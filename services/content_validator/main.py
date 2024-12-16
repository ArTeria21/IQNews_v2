import asyncio

from services.content_validator.config import init_db, get_rabbit_connection
from services.content_validator.ranker import Ranker
from logger_setup import setup_logger, generate_correlation_id

logger = setup_logger(__name__)

async def main():
    correlation_id = generate_correlation_id()
    logger.info("Запуск сервиса контент-валидатора", correlation_id=correlation_id)
    await init_db()
    # Установка соединения с RabbitMQ
    connection = await get_rabbit_connection()
    channel = await connection.channel()
    
    # Объявление очередей
    new_posts_queue = await channel.declare_queue('rss.new_posts', durable=True)
    
    ranker = Ranker()
    # Подписка на очереди
    await new_posts_queue.consume(ranker.handle_new_posts)
    
    try:
        # Бесконечный цикл для поддержания работы приложения
        await asyncio.Future()
    finally:
        await connection.close()
        logger.info("Завершение работы сервиса контент-валидатора", correlation_id=correlation_id)

if __name__ == '__main__':
    asyncio.run(main())