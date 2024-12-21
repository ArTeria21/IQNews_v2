"""Модуль с handlers для обработки информационных сообщений"""

from aiogram import Router, types
from aiogram.filters import Command
from aiogram.types import FSInputFile

from logger_setup import generate_correlation_id, setup_logger
from services.tg_bot.texts import (
    HOW_SERVICE_WORKS_TEXT,
    WHAT_IS_RSS_TEXT,
    WHO_IS_THE_AUTHOR_TEXT,
)

logger = setup_logger(__name__)

router = Router()

@router.message(Command("what_is_rss"))
async def what_is_rss(message: types.Message):
    correlation_id = generate_correlation_id()
    image = FSInputFile(path="static/rss.jpg")
    logger.info(f"Отправка сообщения о том, что такое RSS пользователю {message.from_user.id}", correlation_id=correlation_id)
    await message.answer_photo(image, caption=WHAT_IS_RSS_TEXT)

@router.message(Command("how_service_works"))
async def how_service_works(message: types.Message):
    correlation_id = generate_correlation_id()
    logger.info(f"Отправка сообщения о том, как работает сервис пользователю {message.from_user.id}", correlation_id=correlation_id)
    await message.answer(HOW_SERVICE_WORKS_TEXT)

@router.message(Command("who_is_the_author"))
async def who_is_the_author(message: types.Message):
    correlation_id = generate_correlation_id()
    logger.info(f"Отправка сообщения о том, кто автор сервиса пользователю {message.from_user.id}", correlation_id=correlation_id)
    await message.answer(WHO_IS_THE_AUTHOR_TEXT)