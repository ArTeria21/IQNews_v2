import json
from sqlalchemy.future import select
from sqlalchemy import delete, func
from sqlalchemy.exc import NoResultFound
from database.models import RssFeed, RssPost, Subscription
from config import async_session_factory, get_rabbit_connection

from aio_pika import IncomingMessage, Channel, Message

class RssFeedManager:
    async def add_feed(self, feed_url: str) -> RssFeed:
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
            
            result = await session.execute(select(RssFeed).where(RssFeed.url == feed_url))
            feed = result.scalar_one_or_none()
            return feed

    async def add_subscription(self, user_id: int, feed_id: int):
        async with async_session_factory() as session:
            result = await session.execute(select(Subscription).where(Subscription.user_id == user_id, Subscription.feed_id == feed_id))
            subscription = result.scalar_one_or_none()
            if not subscription:
                new_subscription = Subscription(user_id=user_id, feed_id=feed_id)
                session.add(new_subscription)
                await session.commit()
                print(f"Подписка на RSS-поток {feed_id} для пользователя {user_id} добавлена.")
            else:
                print(f"Подписка на RSS-поток {feed_id} для пользователя {user_id} уже существует.")

    async def handle_add_message(self, message: IncomingMessage):
        data = json.loads(message.body.decode())
        feed_url = data['feed_url']
        print(f"Получено сообщение о добавлении RSS-потока: {feed_url}")
        feed = await self.add_feed(feed_url)
        await self.add_subscription(data['user_id'], feed.feed_id)

    async def get_subscription_urls(self, user_id: int) -> list[str]:
        async with async_session_factory() as session:
            result = await session.execute(
                select(RssFeed.url)
                .join(Subscription, Subscription.feed_id == RssFeed.feed_id)
                .where(Subscription.user_id == user_id)
            )
            urls = result.scalars().all()
            return urls

    async def handle_get_subscriptions(self, message: IncomingMessage):
        connection = await get_rabbit_connection()
        channel = await connection.channel()
        
        data = json.loads(message.body.decode())
        user_id = data['user_id']
        urls = await self.get_subscription_urls(user_id)
        reply_to = message.reply_to
        correlation_id = message.correlation_id
        
        await channel.default_exchange.publish(
            Message(body=json.dumps({"urls": urls}).encode(), 
            correlation_id=correlation_id),
            routing_key=reply_to
        )
        print(f"Отправлен ответ на запрос подписок пользователя с ID {user_id}.")

    async def get_feed_by_url(self, feed_url: str) -> RssFeed:
        async with async_session_factory() as session:
            result = await session.execute(select(RssFeed).where(RssFeed.url == feed_url))
            feed = result.scalar_one_or_none()
            return feed

    async def delete_feed(self, feed_url: str):
        async with async_session_factory() as session:
            await session.execute(delete(RssFeed).where(RssFeed.url == feed_url))
            await session.commit()
            print(f"RSS-поток {feed_url} удален.")

    async def get_amount_of_subscriptions(self, feed_url: str) -> int:
        async with async_session_factory() as session:
            result = await session.execute(select(func.count(Subscription.subscription_id)).where(Subscription.feed_id == feed_url))
            amount = result.scalar_one_or_none()
            return amount

    async def delete_subscription(self, user_id: int, feed_url: str):
        async with async_session_factory() as session:
            feed = await self.get_feed_by_url(feed_url)
            subscription = await session.execute(select(Subscription).where(Subscription.user_id == user_id, Subscription.feed_id == feed.feed_id))
            if subscription:
                await session.execute(delete(Subscription).where(Subscription.user_id == user_id, Subscription.feed_id == feed.feed_id))
                await session.commit()
                print(f"Подписка на RSS-поток {feed_url} для пользователя {user_id} удалена.")
            else:
                print(f"Подписка на RSS-поток {feed_url} для пользователя {user_id} не найдена.")
        if await self.get_amount_of_subscriptions(feed_url) == 0:
            await self.delete_feed(feed_url)

    async def handle_delete_message(self, message: IncomingMessage):
        data = json.loads(message.body.decode())
        feed_url = data['feed_url']
        user_id = data['user_id']
        await self.delete_subscription(user_id, feed_url)
        print(f"Подписка на RSS-поток {feed_url} для пользователя {user_id} удалена.")