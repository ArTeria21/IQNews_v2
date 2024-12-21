import asyncio

from prometheus_client import start_http_server

from logger_setup import generate_correlation_id, setup_logger
from services.user_manager.config import get_rabbit_connection, init_db
from services.user_manager.managers import UserQueueManager
from services.user_manager.metrics import user_manager_registry

logger = setup_logger(__name__)
MONITORING_PORT = 8801 # Порт для мониторинга

async def main():
    correlation_id = generate_correlation_id()
    logger.info("Запуск сервиса менеджера пользователей", correlation_id=correlation_id)
    # Инициализация базы данных
    await init_db()
    start_http_server(MONITORING_PORT, registry=user_manager_registry)

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
    set_status_id_queue = await channel.declare_queue("user.set_status.id", durable=True)
    set_status_username_queue = await channel.declare_queue("user.set_status.username", durable=True)

    # Инициализация менеджера очередей
    user_queue_manager = UserQueueManager(channel)

    # Подписка на очереди
    await create_queue.consume(user_queue_manager.handle_create_user)
    await get_queue.consume(user_queue_manager.handle_get_user)
    await preferences_queue.consume(user_queue_manager.handle_update_preferences)
    await antipathy_queue.consume(user_queue_manager.handle_update_antipathy)
    await set_status_id_queue.consume(user_queue_manager.handle_set_status_id)
    await set_status_username_queue.consume(user_queue_manager.handle_set_status_username)

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
