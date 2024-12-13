import asyncio

from config import init_db, get_rabbit_connection
from managers import RssFeedManager
from rss_listener import RSSListener

async def run_listener(listener: RSSListener):
    while True:
        await listener.check_feeds()
        await asyncio.sleep(60)

async def main():
    await init_db()
    # Установка соединения с RabbitMQ
    connection = await get_rabbit_connection()
    channel = await connection.channel()
    
    # Объявление очередей
    feed_queue = await channel.declare_queue('rss.feed.subscribe')
    subscriptions_queue = await channel.declare_queue('user.rss.subscriptions')
    delete_queue = await channel.declare_queue('rss.feed.unsubscribe')
    
    # Объявление менеджеров
    feed_manager = RssFeedManager()
    listener = RSSListener()
    # Подписка на очереди
    await feed_queue.consume(feed_manager.handle_add_message)
    await subscriptions_queue.consume(feed_manager.handle_get_subscriptions)
    await delete_queue.consume(feed_manager.handle_delete_message)
    
    # Запуск слушателя
    asyncio.create_task(run_listener(listener))
    
    print(" [*] Ожидание сообщений. Для выхода нажмите CTRL+C")
    try:
        # Бесконечный цикл для поддержания работы приложения
        await asyncio.Future()
    finally:
        await connection.close()

if __name__ == '__main__':
    asyncio.run(main())