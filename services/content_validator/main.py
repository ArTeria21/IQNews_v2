import asyncio

from services.content_validator.config import init_db, get_rabbit_connection
from services.content_validator.ranker import Ranker

async def main():
    await init_db()
    # Установка соединения с RabbitMQ
    connection = await get_rabbit_connection()
    channel = await connection.channel()
    
    # Объявление очередей
    new_posts_queue = await channel.declare_queue('rss.new_posts')
    
    ranker = Ranker()
    # Подписка на очереди
    await new_posts_queue.consume(ranker.handle_new_posts)
    
    print(" [*] Ожидание сообщений. Для выхода нажмите CTRL+C")
    try:
        # Бесконечный цикл для поддержания работы приложения
        await asyncio.Future()
    finally:
        await connection.close()

if __name__ == '__main__':
    asyncio.run(main())