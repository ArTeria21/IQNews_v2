import json
from sqlalchemy.future import select
from sqlalchemy.exc import NoResultFound
from database.models import RssFeed, RssPost, Subscription
from config import async_session_factory

from aio_pika import IncomingMessage, Channel, Message

class RssFeedManager:
    def __init__(self):
        super().__init__()
        
    async def add_feed(self, feed_url: str):
        async with async_session_factory() as session:
            feed = RssFeed(url=feed_url)
            session.add(feed)
            await session.commit()
            print(f"RSS-поток {feed_url} добавлен.")
            
    async def handle_add_message(self, message: IncomingMessage):
        data = json.loads(message.body)
        feed_url = data['feed_url']
        await self.add_feed(feed_url)