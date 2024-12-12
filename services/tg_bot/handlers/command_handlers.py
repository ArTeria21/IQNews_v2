"""Модуль с handlers для обработки команд"""
import json
import asyncio
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from aiogram import Router, types
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aio_pika import Message

from tg_bot.texts import (
    START_TEXT,
    HELP_TEXT,
    PROFILE_NOT_FOUND_TEXT,
    PROFILE_LOADING_ERROR_TEXT,
    PROFILE_TEXT,
    EDIT_PROFILE_TEXT,
    SUBSCRIBE_FEED_TEXT,
    GET_SUBSCRIPTIONS_TEXT,
    NO_SUBSCRIPTIONS_TEXT,
    UNSUBSCRIBE_FEED_ERROR_TEXT,
    UNSUBSCRIBE_FEED_TEXT,
)
from tg_bot.utils.logging_setup import generate_correlation_id
from tg_bot.keyboards.edit_profile import get_edit_profile_keyboard
from tg_bot.states.subscribe_rss import SubscribeRss
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
                            if profile_data['is_pro']:
                                pro_status = "Вы являетесь Pro пользлвателем сервиса"
                            else:
                                pro_status = "Вы не являетесь Pro пользлвателем сервиса"
                            await message.answer(
                                PROFILE_TEXT.format(**profile_data, pro_status=pro_status),
                                reply_markup=get_edit_profile_keyboard()
                            )
                        else:
                            await message.answer(PROFILE_NOT_FOUND_TEXT)
                        break  # Ответ получен, завершаем цикл
        except asyncio.TimeoutError:
            await message.answer(PROFILE_LOADING_ERROR_TEXT)


@router.message(Command("help"))
async def help_command(message: types.Message):
    """Обрабатывает команду /help и отправляет справку по командам"""
    await message.answer(HELP_TEXT)

@router.message(Command('edit_profile'))
async def edit_profile_command(message: types.Message):
    """Обрабатывает команду /edit_profile и отправляет клавиатуру для редактирования профиля"""
    await message.answer(EDIT_PROFILE_TEXT,
                        reply_markup=get_edit_profile_keyboard())

@router.message(Command('subscribe_feed'))
async def subscribe_feed_command(message: types.Message, state: FSMContext):
    """Обрабатывает команду /subscribe_feed и запрашивает URL RSS-потока"""
    await message.answer(SUBSCRIBE_FEED_TEXT)
    await state.set_state(SubscribeRss.feed_url)
    
@router.message(Command('my_subscriptions'))
async def my_subscriptions_command(message: types.Message):
    """Обрабатывает команду /my_subscriptions и отправляет список подписок пользователя"""
    user_id = message.from_user.id
    correlation_id = generate_correlation_id()

    connection = await get_rabbit_connection()
    async with connection:
        channel = await connection.channel()  # Создаем канал
        reply_queue = await channel.declare_queue(exclusive=True)  # Временная очередь для ответа

        # Отправляем запрос в очередь `user.rss.subscriptions`
        await channel.default_exchange.publish(
            Message(
                body=json.dumps(
                    {"user_id": user_id, "correlation_id": correlation_id}
                ).encode(),
                reply_to=reply_queue.name,
                correlation_id=correlation_id,
            ),
            routing_key="user.rss.subscriptions",
        )
        try:
            async with reply_queue.iterator() as queue_iter:
                async for response_message in queue_iter:
                    if response_message.correlation_id == correlation_id:
                        response = json.loads(response_message.body.decode())
                        if response['urls']:
                            await message.answer(GET_SUBSCRIPTIONS_TEXT(response['urls']))
                        else:
                            await message.answer(NO_SUBSCRIPTIONS_TEXT)
                        break
        except asyncio.TimeoutError:
            await message.answer(PROFILE_LOADING_ERROR_TEXT)

@router.message(Command('unsubscribe'))
async def unsubscribe_command(message: types.Message, state: FSMContext):
    await message.answer(UNSUBSCRIBE_FEED_TEXT)
    await state.set_state(SubscribeRss.unsubscribe_feed_url)