import os

import aio_pika
from dotenv import load_dotenv
from redis import asyncio as aioredis

load_dotenv()

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
if not TELEGRAM_BOT_TOKEN:
    raise ValueError("TELEGRAM_BOT_TOKEN not found in environment variables")

RABBITMQ_USER = os.getenv("RABBITMQ_DEFAULT_USER")
if not RABBITMQ_USER:
    raise ValueError("RABBITMQ_DEFAULT_USER not found in environment variables")

RABBITMQ_PASS = os.getenv("RABBITMQ_DEFAULT_PASS")
if not RABBITMQ_PASS:
    raise ValueError("RABBITMQ_DEFAULT_PASS not found in environment variables")

RABBITMQ_HOST = os.getenv("RABBITMQ_HOST")
if not RABBITMQ_HOST:
    raise ValueError("RABBITMQ_HOST not found in environment variables")

RABBITMQ_PORT = os.getenv("RABBITMQ_PORT")
if not RABBITMQ_PORT:
    raise ValueError("RABBITMQ_PORT not found in environment variables")

REDIS_URL = os.getenv("REDIS_URL")
if not REDIS_URL:
    raise ValueError("REDIS_URL not found in environment variables")


async def get_rabbit_connection():
    """Устанавливает соединение с RabbitMQ"""
    return await aio_pika.connect_robust(
        host=RABBITMQ_HOST,
        port=int(RABBITMQ_PORT),
        login=RABBITMQ_USER,  # Указываем имя пользователя
        password=RABBITMQ_PASS,  # Указываем пароль
    )


redis = aioredis.from_url(REDIS_URL)

ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD")
if not ADMIN_PASSWORD:
    raise ValueError("ADMIN_PASSWORD not found in environment variables")

ADMIN_USERNAME = os.getenv("ADMIN_USERNAME")
if not ADMIN_USERNAME:
    raise ValueError("ADMIN_USERNAME not found in environment variables")