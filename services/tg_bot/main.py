import asyncio
from aiogram import Bot, Dispatcher
from aiohttp import web
from config import TELEGRAM_BOT_TOKEN

from handlers import command_router, text_router

bot = Bot(token=TELEGRAM_BOT_TOKEN)
dp = Dispatcher()

async def main():
    """Временная функция для запуска бота в режиме polling"""
    dp.include_routers(command_router, text_router)
    await dp.start_polling(bot)

if __name__ == '__main__':
    asyncio.run(main())