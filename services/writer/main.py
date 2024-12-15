import asyncio

from services.writer.config import get_rabbit_connection
from services.writer.ai_writer import Writer

async def main():
    # Установка соединения с RabbitMQ
    connection = await get_rabbit_connection()
    channel = await connection.channel()
    
    # Объявление очередей
    ready_posts_queue = await channel.declare_queue('rss.relevant_posts')
    
    writer = Writer()
    # Подписка на очереди
    await ready_posts_queue.consume(writer.handle_new_posts)
    
    print(" [*] Ожидание сообщений. Для выхода нажмите CTRL+C")
    try:
        await asyncio.Future()
    finally:
        await connection.close()
    
if __name__ == '__main__':
    asyncio.run(main())