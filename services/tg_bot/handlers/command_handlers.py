"""Модуль с handlers для обработки команд"""
import json
import asyncio
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from aiogram import Router, types
from aiogram.filters import Command
from aio_pika import Message

from tg_bot.texts import (
    START_TEXT,
    HELP_TEXT,
    PROFILE_LOADING_TEXT,
    PROFILE_NOT_FOUND_TEXT,
    PROFILE_LOADING_ERROR_TEXT,
)
from tg_bot.utils.logging import generate_correlation_id
from config import get_rabbit_connection  # Функция для подключения к RabbitMQ

router = Router()

@router.message(Command("start"))
async def start_command(message: types.Message):
    """Обрабатывает команду /start и отправляет приветственное сообщение
    и сообщение в очередь для создания пользователя в БД
    """
    await message.answer(START_TEXT)
    correlation_id = generate_correlation_id()

    # Подключение к RabbitMQ
    connection = await get_rabbit_connection()
    async with connection:
        channel = await connection.channel()  # Создаем канал
        await channel.default_exchange.publish(
            Message(
                body=json.dumps(
                    {
                        "user_id": message.from_user.id,
                        "username": message.from_user.username,
                        "correlation_id": correlation_id,
                    }
                ).encode(),
            ),
            routing_key="user.create",  # Очередь создания пользователя
        )


@router.message(Command("profile"))
async def profile_command(message: types.Message):
    """Обрабатывает команду /profile и отправляет запрос на получение профиля пользователя"""
    user_id = message.from_user.id
    status_message = await message.answer(PROFILE_LOADING_TEXT)
    correlation_id = generate_correlation_id()

    connection = await get_rabbit_connection()
    async with connection:
        channel = await connection.channel()  # Создаем канал
        reply_queue = await channel.declare_queue(exclusive=True)  # Временная очередь для ответа

        # Отправляем запрос в очередь `user.profile.request`
        await channel.default_exchange.publish(
            Message(
                body=json.dumps(
                    {"user_id": user_id, "correlation_id": correlation_id}
                ).encode(),
                reply_to=reply_queue.name,
                correlation_id=correlation_id,
            ),
            routing_key="user.profile.request",
        )

        # Ожидаем ответ в временной очереди
        try:
            async with reply_queue.iterator() as queue_iter:
                async for response_message in queue_iter:
                    if response_message.correlation_id == correlation_id:
                        response = json.loads(response_message.body.decode())
                        if response.get("status") == "success":
                            profile_data = response["data"]
                            await status_message.edit_text(
                                f"Ваш профиль:{profile_data}"
                            )
                        else:
                            await status_message.edit_text(PROFILE_NOT_FOUND_TEXT)
                        break  # Ответ получен, завершаем цикл
        except asyncio.TimeoutError:
            await status_message.edit_text(PROFILE_LOADING_ERROR_TEXT)


@router.message(Command("help"))
async def help_command(message: types.Message):
    """Обрабатывает команду /help и отправляет справку по командам"""
    await message.answer(HELP_TEXT)
