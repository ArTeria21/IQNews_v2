import json
from sqlalchemy.future import select
from sqlalchemy.exc import NoResultFound
from database.models import RssFeed, RssPost, Subscription
from config import async_session_factory

from aio_pika import IncomingMessage, Channel, Message

class RssFeedManager:
    async def add_feed(self, feed_url: str):
        async with async_session_factory() as session:
            result = await session.execute(select(RssFeed).where(RssFeed.url == feed_url))
            feed = result.scalar_one_or_none()
            if not feed:
                new_feed = RssFeed(url=feed_url)
                session.add(new_feed)
                await session.commit()
                print(f"RSS-поток {feed_url} добавлен.")
            else:
                print(f"RSS-поток {feed_url} уже существует.")
            
    async def handle_add_message(self, message: IncomingMessage):
        data = json.loads(message.body.decode())
        feed_url = data['feed_url']
        print(f"Получено сообщение о добавлении RSS-потока: {feed_url}")
        await self.add_feed(feed_url)