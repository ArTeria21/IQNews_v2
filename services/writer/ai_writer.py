import json

import aio_pika
from aiolimiter import AsyncLimiter
from langchain_core.exceptions import OutputParserException
from langchain_core.output_parsers import JsonOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_together import ChatTogether
from pydantic import BaseModel, Field

from logger_setup import setup_logger
from services.writer.config import TOGETHER_AI_KEY, get_rabbit_connection
from services.writer.metrics import (
    AMOUNT_OF_SUMMARIES,
    ERROR_COUNTER,
    SUMMARY_LENGTH,
    TIME_OF_OPERATION,
)
from services.writer.prompts import SYSTEM_PROMPT, WRITE_PROMPT

logger = setup_logger(__name__)


class News(BaseModel):
    content: str = Field(description="Your news item prepared for the reader")


class Writer:
    def __init__(self):
        self.llm = ChatTogether(
            api_key=TOGETHER_AI_KEY,
            model="meta-llama/Llama-3.3-70B-Instruct-Turbo",
            temperature=0.6,
            max_tokens=1000,
        )

        self.parser = JsonOutputParser(pydantic_object=News)
        self.prompt = ChatPromptTemplate(
            [("system", SYSTEM_PROMPT), ("human", WRITE_PROMPT)]
        )
        self.chain = self.prompt | self.llm | self.parser

        # Лимитер: не более 5 запросов в секунду
        self.limiter = AsyncLimiter(max_rate=3, time_period=1)

    async def write_news(self, topic: str, preferences: str, content: str) -> News:
        async with self.limiter:
            with TIME_OF_OPERATION.labels(request_type="write_news").time():
                return await self.chain.ainvoke(
                    {
                        "topic": topic,
                        "preferences": preferences,
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
        try:
            logger.info(
                f"Генерация статьи для пользователя {data['user_id']}",
                correlation_id=correlation_id
            )
            news = await self.write_news(
                data["post_title"], data["preferences"], data["post_content"]
            )
        except OutputParserException:
            ERROR_COUNTER.labels(error_type="parser_error").inc()
            logger.error(
                "Ошибка при парсинге ответа от LLM", correlation_id=correlation_id
            )
            return

        try:
            content = news["content"]
            AMOUNT_OF_SUMMARIES.inc()
            SUMMARY_LENGTH.observe(len(content))
        except KeyError:
            ERROR_COUNTER.labels(error_type="content_error").inc()
            logger.error(
                "Ошибка при получении содержимого статьи", correlation_id=correlation_id
            )
            return

        connection = await get_rabbit_connection()
        channel = await connection.channel()
        await channel.declare_queue("rss.ready_posts", durable=True)
        await channel.default_exchange.publish(
            aio_pika.Message(
                body=json.dumps(
                    {
                        "user_id": data["user_id"],
                        "news": content,
                        "post_url": data["post_link"],
                        "feed_url": data["feed_url"],
                        "rank": data["rank"],
                        "correlation_id": correlation_id,
                    }
                ).encode()
            ),
            routing_key="rss.ready_posts",
        )
        await connection.close()
        logger.info(
            f"Статья для пользователя {data['user_id']} отправлена в очередь готовых статей",
            correlation_id=correlation_id,
        )
