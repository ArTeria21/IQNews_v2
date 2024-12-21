import asyncio

from prometheus_client import start_http_server

from logger_setup import generate_correlation_id, setup_logger
from services.content_validator.config import get_rabbit_connection, init_db
from services.content_validator.metrics import content_validator_registry
from services.content_validator.ranker import Ranker

logger = setup_logger(__name__)
MONITORING_PORT = 8804


async def main():
    correlation_id = generate_correlation_id()
    logger.info("Запуск сервиса контент-валидатора", correlation_id=correlation_id)
    await init_db()
    start_http_server(MONITORING_PORT, registry=content_validator_registry)
    # Установка соединения с RabbitMQ
    connection = await get_rabbit_connection()
    channel = await connection.channel()

    # Объявление очередей
    new_posts_queue = await channel.declare_queue("rss.new_posts", durable=True)

    ranker = Ranker()
    # Подписка на очереди
    await new_posts_queue.consume(ranker.handle_new_posts, no_ack=True)

    try:
        # Бесконечный цикл для поддержания работы приложения
        await asyncio.Future()
    finally:
        await connection.close()
        logger.info(
            "Завершение работы сервиса контент-валидатора",
            correlation_id=correlation_id,
        )


if __name__ == "__main__":
    asyncio.run(main())
