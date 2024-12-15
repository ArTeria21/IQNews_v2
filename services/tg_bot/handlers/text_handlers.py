"""Модуль с handlers для обработки текстовых сообщений"""
import json

from aiogram import Router, types
from aiogram.fsm.context import FSMContext
from aiogram.filters import BaseFilter
from aiogram.types import Message

import aio_pika
from services.tg_bot.config import get_rabbit_connection

from services.tg_bot.texts import (DONT_UNDERSTAND_TEXT, PREFERENCES_SAVED_TEXT, KEYWORDS_SAVED_TEXT, 
                        INVALID_FEED_URL_TEXT, INACTIVE_FEED_TEXT, FEED_SUBSCRIBED_TEXT,
                        UNSUBSCRIBE_FEED_SUCCESS_TEXT)
from services.tg_bot.states.edit_profile import EditProfile
from services.tg_bot.states.subscribe_rss import SubscribeRss
from services.tg_bot.utils.check_rss_link import is_feed_active, is_valid_rss_feed
from services.tg_bot.utils.logging_setup import generate_correlation_id


router = Router()

class NoCommandNoStateFilter(BaseFilter):
    async def __call__(self, message: Message, state: FSMContext) -> bool:
        # Проверяем, что сообщение не является командой
        if message.text and message.text.startswith("/"):
            return False
        # Проверяем, что нет активного состояния FSM
        current_state = await state.get_state()
        if current_state is not None:
            return False
        return True

@router.message(NoCommandNoStateFilter())
async def dont_understand_text(message: types.Message):
    """Обрабатывает текстовые сообщения, которые не являются командами и пользователь не находится в состоянии"""
    await message.answer(DONT_UNDERSTAND_TEXT.format(command=message.text))

@router.message(EditProfile.preferences)
async def edit_preferences(message: types.Message, state: FSMContext):
    """Обрабатывает текстовые сообщения, которые пользователь отправляет в ответном сообщении"""
    preferences = message.text
    connection = await get_rabbit_connection()
    correlation_id = generate_correlation_id()
    async with connection.channel() as channel:
        await channel.declare_queue("user.preferences.update")
        await channel.default_exchange.publish(
            aio_pika.Message(body=json.dumps({"user_id": message.from_user.id, "preferences": preferences, "correlation_id": correlation_id}).encode()),
            routing_key="user.preferences.update"
        )
    await state.clear()
    await message.answer(PREFERENCES_SAVED_TEXT)
    
@router.message(EditProfile.keywords)
async def edit_keywords(message: types.Message, state: FSMContext):
    """Обрабатывает текстовые сообщения, которые пользователь отправляет в ответном сообщении"""
    keywords = message.text
    connection = await get_rabbit_connection()
    correlation_id = generate_correlation_id()
    async with connection.channel() as channel:
        await channel.declare_queue("user.keywords.update")
        await channel.default_exchange.publish(
            aio_pika.Message(body=json.dumps({"user_id": message.from_user.id, "keywords": keywords, "correlation_id": correlation_id}).encode()),
            routing_key="user.keywords.update"
        )
    await state.clear()
    await message.answer(KEYWORDS_SAVED_TEXT)

@router.message(SubscribeRss.feed_url)
async def subscribe_feed(message: types.Message, state: FSMContext):
    """Обрабатывает текстовые сообщения, которые пользователь отправляет в ответном сообщении"""
    feed_url = message.text
    await state.clear()
    if not await is_valid_rss_feed(feed_url):
        await message.reply(INVALID_FEED_URL_TEXT)
        return
    if not await is_feed_active(feed_url):
        await message.reply(INACTIVE_FEED_TEXT)
        return
    
    connection = await get_rabbit_connection()
    correlation_id = generate_correlation_id()
    async with connection.channel() as channel:
        await channel.declare_queue("rss.feed.subscribe")
        await channel.default_exchange.publish(
            aio_pika.Message(body=json.dumps({"user_id": message.from_user.id, "feed_url": feed_url, "correlation_id": correlation_id}).encode()),
            routing_key="rss.feed.subscribe"
        )
    await message.reply(FEED_SUBSCRIBED_TEXT)

@router.message(SubscribeRss.unsubscribe_feed_url)
async def unsubscribe_feed(message: types.Message, state: FSMContext):
    """Обрабатывает текстовые сообщения, которые пользователь отправляет в ответном сообщении"""
    feed_url = message.text
    user_id = message.from_user.id
    
    connection = await get_rabbit_connection()
    correlation_id = generate_correlation_id()
    async with connection.channel() as channel:
        await channel.declare_queue("rss.feed.unsubscribe")
        await channel.default_exchange.publish(
            aio_pika.Message(body=json.dumps({"user_id": user_id, "feed_url": feed_url, "correlation_id": correlation_id}).encode()),
            routing_key="rss.feed.unsubscribe"
        )
    await state.clear()
    await message.reply(UNSUBSCRIBE_FEED_SUCCESS_TEXT)