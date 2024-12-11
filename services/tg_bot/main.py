import asyncio
from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.redis import RedisStorage
from aiohttp import web
from config import TELEGRAM_BOT_TOKEN, redis

from handlers import command_router, text_router, callback_router

bot = Bot(token=TELEGRAM_BOT_TOKEN)
storage = RedisStorage(redis=redis)

dp = Dispatcher(storage=storage)

async def main():
    """Временная функция для запуска бота в режиме polling"""
    dp.include_routers(command_router, text_router, callback_router)
    await dp.start_polling(bot)

if __name__ == '__main__':
    asyncio.run(main())