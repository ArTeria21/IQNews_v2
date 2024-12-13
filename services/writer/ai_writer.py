from langchain_together import ChatTogether
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import JsonOutputParser
from langchain_core.exceptions import OutputParserException
from pydantic import BaseModel, Field

import json
import asyncio
import aio_pika
from config import TOGETHER_AI_KEY, get_rabbit_connection
from aiolimiter import AsyncLimiter

from prompts import WRITE_PROMPT, SYSTEM_PROMPT

class News(BaseModel):
    content: str = Field(description="Your news item prepared for the reader")

class Writer:
    def __init__(self):
        self.llm = ChatTogether(
            api_key=TOGETHER_AI_KEY,
            model='meta-llama/Llama-3.3-70B-Instruct-Turbo',
            temperature=0.6,
            max_tokens=1000,
        )
        
        self.parser = JsonOutputParser(pydantic_object=News)
        self.prompt = ChatPromptTemplate([("system", SYSTEM_PROMPT), ("human", WRITE_PROMPT)])
        self.chain = self.prompt | self.llm | self.parser

        # Лимитер: не более 5 запросов в секунду
        self.limiter = AsyncLimiter(max_rate=3, time_period=1)
        
    async def write_news(self, topic: str, preferences: str, content: str) -> News:
        async with self.limiter:
            return await self.chain.ainvoke({
                "topic": topic,
                "preferences": preferences,
                "content": content,
                "format_instructions": self.parser.get_format_instructions()
            })
            
    async def handle_new_posts(self, message: aio_pika.IncomingMessage):
        data = json.loads(message.body.decode())
        try:
            news = await self.write_news(data['post_title'], data['preferences'], data['post_content'])
        except OutputParserException:
            return
        
        connection = await get_rabbit_connection()
        channel = await connection.channel()
        await channel.declare_queue('rss.ready_posts')
        await channel.default_exchange.publish(aio_pika.Message(body=json.dumps({
            'user_id': data['user_id'],
            'news': news['content'],
            'post_url': data['post_link'],
            'feed_url': data['feed_url'],
            'rank': data['rank']
            }).encode()),
            routing_key='rss.ready_posts')
        await connection.close()