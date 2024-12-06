"""Модуль с handlers для обработки команд"""
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from aiogram import Router, types
from aiogram.filters import Command
from tg_bot.texts import START_TEXT, HELP_TEXT

router = Router()

@router.message(Command('start'))
async def start_command(message: types.Message):
    """Обрабатывает команду /start и отправляет приветственное сообщение"""
    await message.answer(START_TEXT)

@router.message(Command('help'))
async def help_command(message: types.Message):
    """Обрабатывает команду /help и отправляет справку по командам"""
    await message.answer(HELP_TEXT)