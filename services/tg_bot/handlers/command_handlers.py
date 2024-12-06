"""Модуль с handlers для обработки команд"""
import sys
import os
import json
import asyncio

sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from aiogram import Router, types
from aiogram.filters import Command

import pika

from tg_bot.texts import START_TEXT, HELP_TEXT
from tg_bot.utils.logging import generate_correlation_id

from config import CONNECTION

router = Router()

@router.message(Command('start'))
async def start_command(message: types.Message):
    """Обрабатывает команду /start и отправляет приветственное сообщение
    и сообщение в очередь для создания пользователя в БД
    """
    await message.answer(START_TEXT)
    # Генерируем UUID для сквозного логирования
    correlation_id = generate_correlation_id()
    
    # Отправляем сообщение в очередь для создания пользователя в БД
    channel = CONNECTION.channel()
    channel.queue_declare(queue='user.create')
    channel.basic_publish(exchange='', routing_key='user.create', body=json.dumps({'user_id': message.from_user.id,
                                                                                'username': message.from_user.username,
                                                                                'correlation_id': correlation_id}))
    channel.close()

@router.message(Command('profile'))
async def profile_command(message: types.Message):
    """Обрабатывает команду /profile и отправляет профиль пользователя"""
    user_id = message.from_user.id
    status_message = await message.answer(PROFILE_LOADING_TEXT)
    
    # генерируем UUID для сквозного логирования
    correlation_id = generate_correlation_id()
    reply_queue = f"reply_{user_id}"
    
    channel = CONNECTION.channel()
    channel.queue_declare(queue='user.profile.request') # очередь для запроса профиля
    channel.queue_declare(queue=reply_queue, exclusive=True) # одноразовая очередь для ответа
    
    channel.basic_publish(exchange='', 
                        routing_key='user.profile.request',
                        body=json.dumps({'user_id': user_id,
                                        'correlation_id': correlation_id}),
                        properties=pika.BasicProperties(reply_to=reply_queue,
                                                        correlation_id=correlation_id))
    
    def on_response(ch, method, properties, body):
        if properties.correlation_id == correlation_id:
            response = json.loads(body)
            asyncio.get_event_loop().call_soon_threadsafe(asyncio.Future().set_result, response)
    
    channel.basic_consume(queue=reply_queue, on_message_callback=on_response, auto_ack=True)
    
    try:
        response = await asyncio.wait_for(asyncio.Future(), timeout=10)
        if response.get('status') == 'success':
            profile_data = response["data"]
            await status_message.edit_text(f"Ваш профиль:\n{profile_data}")
        else:
            await status_message.edit_text(PROFILE_NOT_FOUND_TEXT)
    except asyncio.TimeoutError:
        await status_message.edit_text(PROFILE_LOADING_ERROR_TEXT)
    finally:
        channel.queue_delete(queue=reply_queue)
        channel.close()
    
@router.message(Command('help'))
async def help_command(message: types.Message):
    """Обрабатывает команду /help и отправляет справку по командам"""
    await message.answer(HELP_TEXT)