# main.py
import asyncio
from config import init_db, get_rabbit_connection
from managers import UserQueueManager

async def main():
    # Инициализация базы данных
    await init_db()
    
    # Установка соединения с RabbitMQ
    connection = await get_rabbit_connection()
    channel = await connection.channel()
    
    # Объявление очередей
    create_queue = await channel.declare_queue('user.create')
    get_queue = await channel.declare_queue('user.profile.request')
    
    # Инициализация менеджера очередей
    user_queue_manager = UserQueueManager(channel)
    
    # Подписка на очереди
    await create_queue.consume(user_queue_manager.handle_create_user)
    await get_queue.consume(user_queue_manager.handle_get_user)
    
    print(" [*] Ожидание сообщений. Для выхода нажмите CTRL+C")
    
    try:
        # Бесконечный цикл для поддержания работы приложения
        await asyncio.Future()
    finally:
        await connection.close()

if __name__ == '__main__':
    asyncio.run(main())