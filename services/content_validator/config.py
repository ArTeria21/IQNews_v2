# config.py
import os

from aio_pika import connect_robust
from dotenv import load_dotenv
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import declarative_base, sessionmaker

load_dotenv()

# Конфигурация базы данных
POSTGRES_USER = os.getenv("POSTGRES_USER")
POSTGRES_PASSWORD = os.getenv("POSTGRES_PASSWORD")
POSTGRES_HOST = os.getenv("POSTGRES_HOST")
POSTGRES_PORT = os.getenv("POSTGRES_PORT")

if not all([POSTGRES_USER, POSTGRES_PASSWORD, POSTGRES_HOST, POSTGRES_PORT]):
    raise ValueError("Переменные окружения для базы данных установлены некорректно.")

DATABASE_URL = f"postgresql+asyncpg://{POSTGRES_USER}:{POSTGRES_PASSWORD}@{POSTGRES_HOST}:{POSTGRES_PORT}/user_manager"

engine = create_async_engine(DATABASE_URL)
Base = declarative_base()
async_session_factory = sessionmaker(
    engine, class_=AsyncSession, expire_on_commit=False
)


async def init_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


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
        login=RABBITMQ_USER,  # Указываем имя пользователя
        password=RABBITMQ_PASS,  # Указываем пароль
    )


TOGETHER_AI_KEY = os.getenv("TOGETHER_AI_KEY")
if not TOGETHER_AI_KEY:
    raise ValueError("Переменные окружения для Together AI установлены некорректно.")
