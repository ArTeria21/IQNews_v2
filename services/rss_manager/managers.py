import json
from uuid import UUID

from aio_pika import IncomingMessage, Message
from sqlalchemy import delete, func
from sqlalchemy.future import select

from logger_setup import setup_logger
from services.rss_manager.config import async_session_factory, get_rabbit_connection
from services.rss_manager.database.models import RssFeed, Subscription
from services.rss_manager.metrics import AMOUNT_OF_ADDED_RSS_FEEDS, TIME_OF_OPERATION, ERROR_COUNTER


logger = setup_logger(__name__)


class RssFeedManager:
    async def add_feed(self, feed_url: str, correlation_id: str) -> RssFeed:
        with TIME_OF_OPERATION.labels(request_type="add_feed").time():
            async with async_session_factory() as session:
                result = await session.execute(
                    select(RssFeed).where(RssFeed.url == feed_url)
                )
                feed = result.scalar_one_or_none()
                if not feed:
                    new_feed = RssFeed(url=feed_url)
                    session.add(new_feed)
                    await session.commit()
                    AMOUNT_OF_ADDED_RSS_FEEDS.inc()
                    logger.info(
                        f"RSS-поток {feed_url} добавлен.", correlation_id=correlation_id
                    )
                else:
                    logger.info(
                        f"RSS-поток {feed_url} уже существует.",
                        correlation_id=correlation_id,
                    )

                result = await session.execute(
                    select(RssFeed).where(RssFeed.url == feed_url)
                )
                feed = result.scalar_one_or_none()
                return feed

    async def add_subscription(self, user_id: int, feed_id: int, correlation_id: str):
        with TIME_OF_OPERATION.labels(request_type="add_subscription").time():
            async with async_session_factory() as session:
                result = await session.execute(
                    select(Subscription).where(
                        Subscription.user_id == user_id, Subscription.feed_id == feed_id
                    )
                )
                subscription = result.scalar_one_or_none()
                if not subscription:
                    new_subscription = Subscription(user_id=user_id, feed_id=feed_id)
                    session.add(new_subscription)
                    await session.commit()
                    logger.info(
                        f"Подписка на RSS-поток {feed_id} для пользователя {user_id} добавлена.",
                        correlation_id=correlation_id,
                    )
                else:
                    logger.info(
                        f"Подписка на RSS-поток {feed_id} для пользователя {user_id} уже существует.",
                        correlation_id=correlation_id,
                    )

    async def handle_add_message(self, message: IncomingMessage):
        with TIME_OF_OPERATION.labels(request_type="handle_add_message").time():
            try:
                data = json.loads(message.body.decode())
                correlation_id = data["correlation_id"]
                feed_url = data["feed_url"]
                logger.info(
                    f"Получено сообщение о добавлении RSS-потока: {feed_url}",
                    correlation_id=correlation_id,
                )
                feed = await self.add_feed(feed_url, correlation_id)
                await self.add_subscription(data["user_id"], feed.feed_id, correlation_id)
                await message.ack()
            except Exception as e:
                ERROR_COUNTER.labels(error_type="handle_add_message").inc()
                raise

    async def get_subscription_urls(self, user_id: int) -> list[str]:
        with TIME_OF_OPERATION.labels(request_type="get_subscription_urls").time():
            async with async_session_factory() as session:
                result = await session.execute(
                    select(RssFeed.url)
                    .join(Subscription, Subscription.feed_id == RssFeed.feed_id)
                    .where(Subscription.user_id == user_id)
                )
                urls = result.scalars().all()
                return urls

    async def handle_get_subscriptions(self, message: IncomingMessage):
        with TIME_OF_OPERATION.labels(request_type="handle_get_subscriptions").time():
            try:
                connection = await get_rabbit_connection()
                channel = await connection.channel()

                data = json.loads(message.body.decode())
                user_id = data["user_id"]
                urls = await self.get_subscription_urls(user_id)
                reply_to = message.reply_to
                correlation_id = message.correlation_id

                logger.info(
                    f"Получен запрос на получение списка подписок для пользователя {user_id}",
                    correlation_id=correlation_id,
                )
                await channel.default_exchange.publish(
                    Message(
                        body=json.dumps({"urls": urls}).encode(), correlation_id=correlation_id
                    ),
                    routing_key=reply_to,
                )
                logger.info(
                    f"Отправлен ответ на запрос подписок пользователя с ID {user_id}.",
                    correlation_id=correlation_id,
                )
                await message.ack()
            except Exception as e:
                ERROR_COUNTER.labels(error_type="handle_get_subscriptions").inc()
                raise

    async def get_feed_by_url(self, feed_url: str) -> RssFeed:
        with TIME_OF_OPERATION.labels(request_type="get_feed_by_url").time():
            async with async_session_factory() as session:
                result = await session.execute(
                    select(RssFeed).where(RssFeed.url == feed_url)
                )
                feed = result.scalar_one_or_none()
                return feed

    async def delete_feed(self, feed_url: str, correlation_id: str):
        with TIME_OF_OPERATION.labels(request_type="delete_feed").time():
            async with async_session_factory() as session:
                await session.execute(delete(RssFeed).where(RssFeed.url == feed_url))
                await session.commit()
                logger.info(f"RSS-поток {feed_url} удален.", correlation_id=correlation_id)

    async def get_amount_of_subscriptions(self, feed_id: UUID) -> int:
        with TIME_OF_OPERATION.labels(request_type="get_amount_of_subscriptions").time():
            async with async_session_factory() as session:
                result = await session.execute(
                    select(func.count(Subscription.subscription_id)).where(
                        Subscription.feed_id == feed_id
                    )
                )
                amount = result.scalar_one_or_none()
                return amount

    async def delete_subscription(
        self, user_id: int, feed_url: str, correlation_id: str
    ):
        with TIME_OF_OPERATION.labels(request_type="delete_subscription").time():
            async with async_session_factory() as session:
                feed = await self.get_feed_by_url(feed_url)
                if not feed:
                    ERROR_COUNTER.labels(error_type="feed_not_found").inc()
                    logger.error(
                        f"RSS-поток с URL {feed_url} не найден.",
                        correlation_id=correlation_id,
                    )
                    return  # Выход из метода, так как поток не существует

                subscription = await session.execute(
                    select(Subscription).where(
                        Subscription.user_id == user_id,
                        Subscription.feed_id == feed.feed_id,
                    )
                )
                if subscription.scalar_one_or_none():
                    await session.execute(
                        delete(Subscription).where(
                            Subscription.user_id == user_id,
                            Subscription.feed_id == feed.feed_id,
                        )
                    )
                    await session.commit()
                    logger.info(
                        f"Подписка на RSS-поток {feed_url} для пользователя {user_id} удалена.",
                        correlation_id=correlation_id,
                    )
                else:
                    logger.info(
                        f"Подписка на RSS-поток {feed_url} для пользователя {user_id} не найдена.",
                        correlation_id=correlation_id,
                    )

                # Проверка, остались ли подписки на поток
                if await self.get_amount_of_subscriptions(feed.feed_id) == 0:
                    await self.delete_feed(feed_url, correlation_id)

    async def handle_delete_message(self, message: IncomingMessage):
        with TIME_OF_OPERATION.labels(request_type="handle_delete_message").time():
            try:
                data = json.loads(message.body.decode())
                feed_url = data["feed_url"]
                user_id = data["user_id"]
                correlation_id = data["correlation_id"]
                await self.delete_subscription(user_id, feed_url, correlation_id)
                logger.info(
                    f"Подписка на RSS-поток {feed_url} для пользователя {user_id} удалена.",
                    correlation_id=correlation_id,
                )
                await message.ack()
            except Exception as e:
                ERROR_COUNTER.labels(error_type="handle_delete_message").inc()
                raise