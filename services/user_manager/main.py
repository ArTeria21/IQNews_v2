import asyncio

from logger_setup import generate_correlation_id, setup_logger
from services.user_manager.config import get_rabbit_connection, init_db
from services.user_manager.managers import UserQueueManager

logger = setup_logger(__name__)


async def main():
    correlation_id = generate_correlation_id()
    logger.info("Запуск сервиса менеджера пользователей", correlation_id=correlation_id)
    # Инициализация базы данных
    await init_db()

    # Установка соединения с RabbitMQ
    connection = await get_rabbit_connection()
    channel = await connection.channel()

    # Объявление очередей
    create_queue = await channel.declare_queue("user.create", durable=True)
    get_queue = await channel.declare_queue("user.profile.request", durable=True)
    preferences_queue = await channel.declare_queue(
        "user.preferences.update", durable=True
    )
    antipathy_queue = await channel.declare_queue("user.antipathy.update", durable=True)

    # Инициализация менеджера очередей
    user_queue_manager = UserQueueManager(channel)

    # Подписка на очереди
    await create_queue.consume(user_queue_manager.handle_create_user)
    await get_queue.consume(user_queue_manager.handle_get_user)
    await preferences_queue.consume(user_queue_manager.handle_update_preferences)
    await antipathy_queue.consume(user_queue_manager.handle_update_antipathy)

    try:
        # Бесконечный цикл для поддержания работы приложения
        await asyncio.Future()
    finally:
        await connection.close()
        logger.info(
            "Завершение работы сервиса менеджера пользователей",
            correlation_id=correlation_id,
        )


if __name__ == "__main__":
    asyncio.run(main())
