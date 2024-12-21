import os

import aio_pika
from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.redis import RedisStorage
from dotenv import load_dotenv
from redis import asyncio as aioredis

load_dotenv()

# Telegram Bot Configuration
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")  # Bot API token from BotFather
if not TELEGRAM_BOT_TOKEN:
    raise ValueError("TELEGRAM_BOT_TOKEN not found in environment variables")

# RabbitMQ Connection Settings
RABBITMQ_USER = os.getenv("RABBITMQ_DEFAULT_USER")  # RabbitMQ username
if not RABBITMQ_USER:
    raise ValueError("RABBITMQ_DEFAULT_USER not found in environment variables")

RABBITMQ_PASS = os.getenv("RABBITMQ_DEFAULT_PASS")  # RabbitMQ password
if not RABBITMQ_PASS:
    raise ValueError("RABBITMQ_DEFAULT_PASS not found in environment variables")

RABBITMQ_HOST = os.getenv("RABBITMQ_HOST")  # RabbitMQ server hostname
if not RABBITMQ_HOST:
    raise ValueError("RABBITMQ_HOST not found in environment variables")

RABBITMQ_PORT = os.getenv("RABBITMQ_PORT")  # RabbitMQ server port
if not RABBITMQ_PORT:
    raise ValueError("RABBITMQ_PORT not found in environment variables")

async def get_rabbit_connection():
    """Устанавливает соединение с RabbitMQ"""
    return await aio_pika.connect_robust(
        host=RABBITMQ_HOST,
        port=int(RABBITMQ_PORT),
        login=RABBITMQ_USER,
        password=RABBITMQ_PASS,
    )

# Redis Configuration
REDIS_URL = os.getenv("REDIS_URL")  # Redis connection URL
if not REDIS_URL:
    raise ValueError("REDIS_URL not found in environment variables")

redis = aioredis.from_url(REDIS_URL)

# Webhook Configuration
USE_WEBHOOK = os.getenv("USE_WEBHOOK", default="False").lower() == "true"  # Flag to enable/disable webhook mode

WEBHOOK_HOST = os.getenv("WEBHOOK_HOST")  # Webhook server hostname
if not WEBHOOK_HOST:
    raise ValueError("WEBHOOK_HOST not found in environment variables")

WEBHOOK_PORT = os.getenv("WEBHOOK_PORT")  # Webhook server port
if not WEBHOOK_PORT:
    raise ValueError("WEBHOOK_PORT not found in environment variables")

BASE_URL = os.getenv("BASE_URL")  # Base URL for webhook endpoints
if not BASE_URL:
    raise ValueError("BASE_URL not found in environment variables")

WEBHOOK_PATH = f"/webhook/{TELEGRAM_BOT_TOKEN}"  # Webhook endpoint path
WEBHOOK_URL = f"{BASE_URL}{WEBHOOK_PATH}"  # Complete webhook URL

# Admin Configuration
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD")  # Password for admin access
if not ADMIN_PASSWORD:
    raise ValueError("ADMIN_PASSWORD not found in environment variables")

ADMIN_USERNAME = os.getenv("ADMIN_USERNAME")  # Admin's Telegram username, starts with @
if not ADMIN_USERNAME:
    raise ValueError("ADMIN_USERNAME not found in environment variables")

# Bot Behavior Settings
MINUTES_BETWEEN_POSTS = float(os.getenv("MINUTES_BETWEEN_POSTS", default=3))  # Delay between posts in minutes
if MINUTES_BETWEEN_POSTS <= 0:
    raise ValueError("MINUTES_BETWEEN_POSTS must be greater than 0")

# Bot and Dispatcher Initialization
bot = Bot(token=TELEGRAM_BOT_TOKEN)
storage = RedisStorage(redis=redis)
dp = Dispatcher(storage=storage)