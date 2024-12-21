"""Модуль с handlers для обработки команд"""

import asyncio
import json

from aio_pika import Message
from aiogram import Router, types
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import FSInputFile

from logger_setup import generate_correlation_id, setup_logger
from services.tg_bot.config import (
    get_rabbit_connection,  # Функция для подключения к RabbitMQ
)
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
    SUBSCRIPTIONS_LIMIT_TEXT,
    UNSUBSCRIBE_FEED_TEXT,
)

logger = setup_logger(__name__)

router = Router()
AMOUNT_OF_FREE_SUBSCRIPTIONS = 3

async def get_user_subscriptions(user_id: int, correlation_id: str) -> list[str]:
    """Получает список подписок пользователя из RabbitMQ"""
    connection = await get_rabbit_connection()
    async with connection:
        channel = await connection.channel()
        reply_queue = await channel.declare_queue(exclusive=True)

        await channel.default_exchange.publish(
            Message(
                body=json.dumps({"user_id": user_id, "correlation_id": correlation_id}).encode(),
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
                        return response["urls"]
        except asyncio.TimeoutError:
            return []
        except Exception as e:
            logger.error(f"Ошибка при получении подписок пользователя {user_id}: {e}", correlation_id=correlation_id)
            return []

async def get_user_profile(user_id: int, correlation_id: str) -> dict:
    """Получает информацию о профиле пользователя через RabbitMQ"""
    connection = await get_rabbit_connection()
    async with connection:
        channel = await connection.channel()
        reply_queue = await channel.declare_queue(exclusive=True)

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

        try:
            async with reply_queue.iterator() as queue_iter:
                async for response_message in queue_iter:
                    if response_message.correlation_id == correlation_id:
                        response = json.loads(response_message.body.decode())
                        return response
        except asyncio.TimeoutError:
            logger.error(
                f"Таймаут при получении профиля пользователя {user_id}",
                correlation_id=correlation_id,
            )
            return {"status": "error", "message": "timeout"}
        except Exception as e:
            logger.error(f"Ошибка при получении профиля пользователя {user_id}: {e}", correlation_id=correlation_id)
            return {"status": "error", "message": "unknown_error"}

@router.message(Command("start"))
async def start_command(message: types.Message):
    """Обрабатывает команду /start и отправляет приветственное сообщение
    и сообщение в очередь для создания пользователя в БД
    """
    photo = FSInputFile(path="static/xy_photo.jpg")
    await message.answer_photo(photo, caption=START_TEXT)
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

    response = await get_user_profile(user_id, correlation_id)
    
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
    elif response.get("message") == "timeout":
        await message.answer(PROFILE_LOADING_ERROR_TEXT)
    else:
        await message.answer(PROFILE_NOT_FOUND_TEXT)
        logger.warning(
            f"Профиль пользователя {message.from_user.id} не найден",
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
    user_profile = await get_user_profile(message.from_user.id, correlation_id)
    is_pro = bool(user_profile['data']['is_pro'])
    current_subscriptions = await get_user_subscriptions(message.from_user.id, correlation_id)
    if not is_pro and len(current_subscriptions) >= AMOUNT_OF_FREE_SUBSCRIPTIONS:
        await message.answer(SUBSCRIPTIONS_LIMIT_TEXT)
        return
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
    subscriptions = await get_user_subscriptions(user_id, correlation_id)
    if not subscriptions:
        await message.answer(NO_SUBSCRIPTIONS_TEXT)
        return
    await message.answer(GET_SUBSCRIPTIONS_TEXT(subscriptions))

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