"""Модуль с handlers для обработки команд"""

import asyncio
import json

from aio_pika import Message
from aiogram import Router, types
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext

from logger_setup import generate_correlation_id, setup_logger
from services.tg_bot.config import (
    get_rabbit_connection,
)  # Функция для подключения к RabbitMQ
from services.tg_bot.keyboards.edit_profile import get_edit_profile_keyboard
from services.tg_bot.states.subscribe_rss import SubscribeRss
from services.tg_bot.texts import (
    EDIT_PROFILE_TEXT,
    GET_SUBSCRIPTIONS_TEXT,
    HELP_TEXT,
    NO_SUBSCRIPTIONS_TEXT,
    PROFILE_LOADING_ERROR_TEXT,
    PROFILE_NOT_FOUND_TEXT,
    PROFILE_TEXT,
    START_TEXT,
    SUBSCRIBE_FEED_TEXT,
    UNSUBSCRIBE_FEED_TEXT,
)

logger = setup_logger(__name__)

router = Router()


@router.message(Command("start"))
async def start_command(message: types.Message):
    """Обрабатывает команду /start и отправляет приветственное сообщение
    и сообщение в очередь для создания пользователя в БД
    """
    await message.answer(START_TEXT)
    correlation_id = generate_correlation_id()
    logger.info(
        f"Обработка команды /start от пользователя {message.from_user.id}",
        correlation_id=correlation_id,
    )
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
    logger.info(
        f"Обработка команды /profile от пользователя {message.from_user.id}",
        correlation_id=correlation_id,
    )
    connection = await get_rabbit_connection()
    async with connection:
        channel = await connection.channel()  # Создаем канал
        reply_queue = await channel.declare_queue(
            exclusive=True
        )  # Временная очередь для ответа

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
                            if profile_data["is_pro"]:
                                pro_status = "Вы являетесь Pro пользлвателем сервиса"
                            else:
                                pro_status = "Вы не являетесь Pro пользлвателем сервиса"
                            await message.answer(
                                PROFILE_TEXT.format(
                                    **profile_data, pro_status=pro_status
                                ),
                                reply_markup=get_edit_profile_keyboard(),
                            )
                            logger.info(
                                f"Отправлено сообщение с профилем пользователя {message.from_user.id}",
                                correlation_id=correlation_id,
                            )
                        else:
                            await message.answer(PROFILE_NOT_FOUND_TEXT)
                            logger.warning(
                                f"Профиль пользователя {message.from_user.id} не найден",
                                correlation_id=correlation_id,
                            )
                        break  # Ответ получен, завершаем цикл
        except asyncio.TimeoutError:
            await message.answer(PROFILE_LOADING_ERROR_TEXT)
            logger.error(
                f"Ошибка при получении профиля пользователя {message.from_user.id}",
                correlation_id=correlation_id,
            )


@router.message(Command("help"))
async def help_command(message: types.Message):
    """Обрабатывает команду /help и отправляет справку по командам"""
    await message.answer(HELP_TEXT)
    correlation_id = generate_correlation_id()
    logger.info(
        f"Отправлено сообщение с справкой по командам для пользователя {message.from_user.id}",
        correlation_id=correlation_id,
    )


@router.message(Command("edit_profile"))
async def edit_profile_command(message: types.Message):
    """Обрабатывает команду /edit_profile и отправляет клавиатуру для редактирования профиля"""
    correlation_id = generate_correlation_id()
    logger.info(
        f"Обработка команды /edit_profile от пользователя {message.from_user.id}",
        correlation_id=correlation_id,
    )
    await message.answer(EDIT_PROFILE_TEXT, reply_markup=get_edit_profile_keyboard())


@router.message(Command("subscribe"))
async def subscribe_feed_command(message: types.Message, state: FSMContext):
    """Обрабатывает команду /subscribe и запрашивает URL RSS-потока"""
    correlation_id = generate_correlation_id()
    logger.info(
        f"Обработка команды /subscribe от пользователя {message.from_user.id}",
        correlation_id=correlation_id,
    )
    await message.answer(SUBSCRIBE_FEED_TEXT)
    await state.set_state(SubscribeRss.feed_url)
    await state.update_data(correlation_id=correlation_id)


@router.message(Command("subscriptions"))
async def my_subscriptions_command(message: types.Message):
    """Обрабатывает команду /subscriptions и отправляет список подписок пользователя"""
    user_id = message.from_user.id
    correlation_id = generate_correlation_id()
    logger.info(
        f"Обработка команды /subscriptions от пользователя {message.from_user.id}",
        correlation_id=correlation_id,
    )
    connection = await get_rabbit_connection()
    async with connection:
        channel = await connection.channel()  # Создаем канал
        reply_queue = await channel.declare_queue(
            exclusive=True
        )  # Временная очередь для ответа

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
                        if response["urls"]:
                            await message.answer(
                                GET_SUBSCRIPTIONS_TEXT(response["urls"])
                            )
                            logger.info(
                                f"Отправлено сообщение с подписками пользователя {message.from_user.id}",
                                correlation_id=correlation_id,
                            )
                        else:
                            await message.answer(NO_SUBSCRIPTIONS_TEXT)
                            logger.warning(
                                f"У пользователя {message.from_user.id} нет подписок",
                                correlation_id=correlation_id,
                            )
                        break
        except asyncio.TimeoutError:
            await message.answer(PROFILE_LOADING_ERROR_TEXT)
            logger.error(
                f"Ошибка при получении подписок пользователя {message.from_user.id}",
                correlation_id=correlation_id,
            )


@router.message(Command("unsubscribe"))
async def unsubscribe_command(message: types.Message, state: FSMContext):
    correlation_id = generate_correlation_id()
    logger.info(
        f"Обработка команды /unsubscribe от пользователя {message.from_user.id}",
        correlation_id=correlation_id,
    )
    await message.answer(UNSUBSCRIBE_FEED_TEXT)
    await state.set_state(SubscribeRss.unsubscribe_feed_url)
    await state.update_data(correlation_id=correlation_id)
