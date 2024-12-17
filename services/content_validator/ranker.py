import json
from datetime import datetime, timedelta, timezone

import aio_pika
from aiolimiter import AsyncLimiter
from langchain_core.output_parsers import JsonOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_together import ChatTogether
from pydantic import BaseModel, Field

from logger_setup import setup_logger
from services.content_validator.config import (
    TOGETHER_AI_KEY,
    async_session_factory,
    get_rabbit_connection,
)
from services.content_validator.database.models import User
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
            temperature=0.1,
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
        async with async_session_factory() as session:
            user = await session.get(User, user_id)
            return user.preferences

    async def user_keywords(self, user_id: int) -> list[str]:
        async with async_session_factory() as session:
            user = await session.get(User, user_id)
            return user.keywords

    async def rank_post(
        self, title: str, preferences: str, keywords: str, content: str
    ) -> Evaluation:
        return await self.chain.ainvoke(
            {
                "title": title,
                "preferences": preferences,
                "keywords": keywords,
                "content": content,
                "format_instructions": self.parser.get_format_instructions(),
            }
        )

    async def handle_new_posts(self, message: aio_pika.IncomingMessage):
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
        
        # Проверяем, что пост не старше 3 часов
        if (current_time - published_at) > timedelta(hours=3):
            logger.info(
                f"Пост '{data['post_title']}' не релевантен, так как он был опубликован более 3 часов назад",
                correlation_id=correlation_id,
            )
            return
            
        users_id = list(data["feed_subscribers"])
        for user_id in users_id:
            # Гарантируем, что не превысим лимит запросов
            async with self.limiter:
                preferences = await self.user_preferences(int(user_id))
                keywords = await self.user_keywords(int(user_id))
                rank = await self.rank_post(
                    data["post_title"], preferences, keywords, data["post_content"]
                )
                logger.info(
                    f"Пост '{data['post_title']}' оценён рейтингом {rank['rank']}%",
                    correlation_id=correlation_id,
                )
                if rank["rank"] > 65:
                    connection = await get_rabbit_connection()
                    channel = await connection.channel()
                    queue = await channel.declare_queue("rss.relevant_posts")
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
