# config.py
from dotenv import load_dotenv
import os
from aio_pika import connect_robust

load_dotenv()

# Конфигурация RabbitMQ
RABBITMQ_USER = os.getenv("RABBITMQ_DEFAULT_USER")
RABBITMQ_PASS = os.getenv("RABBITMQ_DEFAULT_PASS")
RABBITMQ_HOST = os.getenv("RABBITMQ_HOST")
RABBITMQ_PORT = int(os.getenv("RABBITMQ_PORT", 5672))

if not all([RABBITMQ_USER, RABBITMQ_PASS, RABBITMQ_HOST]):
    raise ValueError("Переменные окружения для RabbitMQ установлены некорректно.")

async def get_rabbit_connection():
    """Устанавливает соединение с RabbitMQ"""
    return await connect_robust(
        host=RABBITMQ_HOST,
        port=int(RABBITMQ_PORT),
        login=RABBITMQ_USER,        # Указываем имя пользователя
        password=RABBITMQ_PASS,     # Указываем пароль
    )

# Конфигурация Together AI
TOGETHER_AI_KEY = os.getenv("TOGETHER_AI_KEY")
if not TOGETHER_AI_KEY:
    raise ValueError("Переменные окружения для Together AI установлены некорректно.")