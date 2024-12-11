import asyncio

from config import init_db, get_rabbit_connection
from database.models import RssFeed, RssPost, Subscription
from managers import RssFeedManager


async def main():
    await init_db()
    # Установка соединения с RabbitMQ
    connection = await get_rabbit_connection()
    channel = await connection.channel()
    
    # Объявление очередей
    feed_queue = await channel.declare_queue('rss.feed.subscribe')
    
    # Объявление менеджеров
    feed_manager = RssFeedManager()
    
    # Подписка на очереди
    await feed_queue.consume(feed_manager.handle_add_message)
    
    print(" [*] Ожидание сообщений. Для выхода нажмите CTRL+C")
    try:
        # Бесконечный цикл для поддержания работы приложения
        await asyncio.Future()
    finally:
        await connection.close()

if __name__ == '__main__':
    asyncio.run(main())