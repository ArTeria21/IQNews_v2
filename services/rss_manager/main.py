import asyncio

from services.rss_manager.config import init_db, get_rabbit_connection
from services.rss_manager.managers import RssFeedManager
from services.rss_manager.rss_listener import RSSListener
from logger_setup import setup_logger, generate_correlation_id

logger = setup_logger(__name__)
async def run_listener(listener: RSSListener):
    correlation_id = generate_correlation_id()
    logger.info("Запуск слушателя", correlation_id=correlation_id)
    while True:
        await listener.check_feeds()
        logger.info("Проверка RSS-каналов", correlation_id=correlation_id)
        await asyncio.sleep(60)

async def main():
    correlation_id = generate_correlation_id()
    await init_db()
    # Установка соединения с RabbitMQ
    connection = await get_rabbit_connection()
    channel = await connection.channel()
    
    # Объявление очередей
    feed_queue = await channel.declare_queue('rss.feed.subscribe', durable=True)
    subscriptions_queue = await channel.declare_queue('user.rss.subscriptions', durable=True)
    delete_queue = await channel.declare_queue('rss.feed.unsubscribe', durable=True)
    
    # Объявление менеджеров
    feed_manager = RssFeedManager()
    listener = RSSListener()
    # Подписка на очереди
    await feed_queue.consume(feed_manager.handle_add_message)
    await subscriptions_queue.consume(feed_manager.handle_get_subscriptions)
    await delete_queue.consume(feed_manager.handle_delete_message)
    
    logger.info("Запуск менеджера RSS потоков", correlation_id=correlation_id)
    
    # Запуск слушателя
    asyncio.create_task(run_listener(listener))
    
    try:
        # Бесконечный цикл для поддержания работы приложения
        await asyncio.Future()
    finally:
        await connection.close()
        logger.info("Завершение работы менеджера RSS потоков", correlation_id=correlation_id)

if __name__ == '__main__':
    asyncio.run(main())