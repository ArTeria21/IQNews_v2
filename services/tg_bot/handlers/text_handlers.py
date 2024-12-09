"""Модуль с handlers для обработки текстовых сообщений"""
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from aiogram import Router, types
from tg_bot.texts import DONT_UNDERSTAND_TEXT

router = Router()

@router.message()
async def dont_understand_text(message: types.Message):
    """Обрабатывает текстовые сообщения, которые не являются командами"""
    await message.answer(DONT_UNDERSTAND_TEXT.format(command=message.text))