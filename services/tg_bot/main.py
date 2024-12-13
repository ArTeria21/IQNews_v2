import asyncio
from aiogram import Bot, Dispatcher
import json
from aiogram.fsm.storage.redis import RedisStorage
from aiohttp import web
from config import TELEGRAM_BOT_TOKEN, redis, get_rabbit_connection
import aio_pika
from handlers import command_router, text_router, callback_router

bot = Bot(token=TELEGRAM_BOT_TOKEN)
storage = RedisStorage(redis=redis)

dp = Dispatcher(storage=storage)

async def handle_ready_posts(message: aio_pika.IncomingMessage):
    data = json.loads(message.body.decode())
    await bot.send_message(chat_id=data['user_id'], text=data['news'])

async def main():
    connection = await get_rabbit_connection()
    channel = await connection.channel()
    queue = await channel.declare_queue('rss.ready_posts')
    await queue.consume(handle_ready_posts)
    """Временная функция для запуска бота в режиме polling"""
    dp.include_routers(command_router, text_router, callback_router)
    await dp.start_polling(bot)
    try:
        await asyncio.Future()
    finally:
        await connection.close()

if __name__ == '__main__':
    asyncio.run(main())