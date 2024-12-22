import json
from datetime import datetime, timezone

import aio_pika
from aiolimiter import AsyncLimiter
from langchain_core.output_parsers import JsonOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_together import ChatTogether
from pydantic import BaseModel, Field

from logger_setup import setup_logger
from services.content_validator.config import (
    RELEVANCE_THRESHOLD,
    TOGETHER_AI_KEY,
    async_session_factory,
    get_rabbit_connection,
)
from services.content_validator.database.models import User
from services.content_validator.metrics import (
    AMOUNT_OF_VALIDATED_POSTS,
    ERROR_COUNTER,
    MEAN_RATING,
    TIME_OF_OPERATION,
)
from services.content_validator.prompts import RANK_POSTS_PROMPT, SYSTEM_PROMPT

logger = setup_logger(__name__)


class Evaluation(BaseModel):
    explaination: str = Field(
        description="Briefly (50-80 words) analyze this text and tell us whether it corresponds to the user's interests or not."
    )
    rank: int = Field(description="digit from 0 to 100")


class Ranker:
    def __init__(self):
        self.llm = ChatTogether(
            api_key=TOGETHER_AI_KEY,
            model="Qwen/Qwen2.5-7B-Instruct-Turbo",
            temperature=0.2,
            max_tokens=300,
        )
        self.parser = JsonOutputParser(pydantic_object=Evaluation)
        self.prompt = ChatPromptTemplate(
            [("system", SYSTEM_PROMPT), ("human", RANK_POSTS_PROMPT)]
        )
        self.chain = self.prompt | self.llm | self.parser

        # Лимитер: не более 5 запросов в секунду
        self.limiter = AsyncLimiter(max_rate=5, time_period=1)

    async def user_preferences(self, user_id: int) -> dict:
        with TIME_OF_OPERATION.labels(request_type="get_user_preferences").time():
            async with async_session_factory() as session:
                user = await session.get(User, user_id)
                return user.preferences

    async def user_antipathy(self, user_id: int) -> list[str]:
        with TIME_OF_OPERATION.labels(request_type="get_user_antipathy").time():
            async with async_session_factory() as session:
                user = await session.get(User, user_id)
                return user.antipathy

    async def rank_post(
        self, title: str, preferences: str, antipathy: str, content: str
    ) -> Evaluation:
        with TIME_OF_OPERATION.labels(request_type="rank_post").time():
            return await self.chain.ainvoke(
                {
                    "title": title,
                    "preferences": preferences,
                    "antipathy": antipathy,
                    "content": content,
                    "format_instructions": self.parser.get_format_instructions(),
                }
            )

    async def handle_new_posts(self, message: aio_pika.IncomingMessage):
        with TIME_OF_OPERATION.labels(request_type="handle_new_posts").time():
            try:
                data = json.loads(message.body.decode())
                correlation_id = data["correlation_id"]
                logger.info(
                    "Получено новое сообщение о новом посте", correlation_id=correlation_id
                )
                published_at = datetime.fromisoformat(data["published_at"])
                current_time = datetime.now(timezone.utc)
                
                # Make published_at timezone-aware if it isn't already
                if published_at.tzinfo is None:
                    published_at = published_at.replace(tzinfo=timezone.utc)
                
                # Проверяем, что пост вышел в этот день
                if published_at.date() != current_time.date():
                    logger.info(
                        f"Пост '{data['post_title']}' не релевантен, так как он был опубликован в другой день",
                        correlation_id=correlation_id,
                    )
                    return
                    
                users_id = list(data["feed_subscribers"])
                for user_id in users_id:
                    # Гарантируем, что не превысим лимит запросов
                    async with self.limiter:
                        preferences = await self.user_preferences(int(user_id))
                        antipathy = await self.user_antipathy(int(user_id))
                        rank = await self.rank_post(
                            data["post_title"], preferences, antipathy, data["post_content"]
                        )
                        AMOUNT_OF_VALIDATED_POSTS.inc()
                        MEAN_RATING.set(rank["rank"])
                        logger.info(
                            f"Пост '{data['post_title']}' оценён рейтингом {rank['rank']}%",
                            correlation_id=correlation_id,
                        )
                        if rank["rank"] > int(RELEVANCE_THRESHOLD):
                            connection = await get_rabbit_connection()
                            channel = await connection.channel()
                            await channel.default_exchange.publish(
                                aio_pika.Message(
                                    body=json.dumps(
                                        {
                                            "feed_url": data["feed_url"],
                                            "post_title": data["post_title"],
                                            "post_link": data["post_link"],
                                            "post_content": data["post_content"],
                                            "user_id": user_id,
                                            "preferences": preferences,
                                            "rank": rank["rank"],
                                            "correlation_id": correlation_id,
                                        }
                                    ).encode()
                                ),
                                routing_key="rss.relevant_posts",
                            )
                            await connection.close()
                            logger.info(
                                f"Пост '{data['post_title']}' отправлен в очередь релевантных постов для пользователя {user_id}",
                                correlation_id=correlation_id,
                            )
            except Exception:
                ERROR_COUNTER.labels(error_type="handle_new_posts").inc()
                raise
