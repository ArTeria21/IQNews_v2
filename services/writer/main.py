import asyncio

from services.writer.config import get_rabbit_connection
from services.writer.ai_writer import Writer
from logger_setup import setup_logger, generate_correlation_id

logger = setup_logger(__name__)

async def main():
    correlation_id = generate_correlation_id()
    logger.info("Запуск сервиса генератора статей", correlation_id=correlation_id)
    # Установка соединения с RabbitMQ
    connection = await get_rabbit_connection()
    channel = await connection.channel()
    
    # Объявление очередей
    ready_posts_queue = await channel.declare_queue('rss.relevant_posts', durable=True)
    
    writer = Writer()
    # Подписка на очереди
    await ready_posts_queue.consume(writer.handle_new_posts)
    
    try:
        await asyncio.Future()
    finally:
        await connection.close()
        logger.info("Завершение работы сервиса генератора статей", correlation_id=correlation_id)

if __name__ == '__main__':
    asyncio.run(main())