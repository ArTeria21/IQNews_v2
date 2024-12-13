from langchain_together import ChatTogether
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import JsonOutputParser
from pydantic import BaseModel, Field

import json
import asyncio
import aio_pika
from config import TOGETHER_AI_KEY, async_session_factory
from database.models import User
from prompts import RANK_POSTS_PROMPT, SYSTEM_PROMPT
from aiolimiter import AsyncLimiter


class Evaluation(BaseModel):
    explaination: str = Field(description="Briefly (50-80 words) analyze this text and tell us whether it corresponds to the user's interests or not.")
    rank: int = Field(description="digit from 0 to 100")

class Ranker:
    def __init__(self):
        self.llm = ChatTogether(
            api_key=TOGETHER_AI_KEY,
            model='Qwen/Qwen2.5-7B-Instruct-Turbo',
            temperature=0.1,
            max_tokens=300
        )
        self.parser = JsonOutputParser(pydantic_object=Evaluation)
        self.prompt = ChatPromptTemplate([("system", SYSTEM_PROMPT), ("human", RANK_POSTS_PROMPT)])
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

    async def rank_post(self, title: str, preferences: str, keywords: str, content: str) -> Evaluation:
        return await self.chain.ainvoke({
            "title": title,
            "preferences": preferences,
            "keywords": keywords,
            "content": content,
            "format_instructions": self.parser.get_format_instructions()
        })

    async def handle_new_posts(self, message: aio_pika.IncomingMessage):
        data = json.loads(message.body.decode())
        users_id = list(data['feed_subscribers'])
        for user_id in users_id:
            # Гарантируем, что не превысим лимит запросов
            async with self.limiter:
                preferences = await self.user_preferences(int(user_id))
                keywords = await self.user_keywords(int(user_id))
                rank = await self.rank_post(data['post_title'], preferences, keywords, data['post_content'])
                print(rank)