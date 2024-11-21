from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.orm import DeclarativeBase
from pydantic_settings import BaseSettings, SettingsConfigDict

# Класс для хранения настроек базы
class DBSettings(BaseSettings):
    POSTGRES_HOST: str
    POSTGRES_PORT: int
    POSTGRES_USER: str
    POSTGRES_PASSWORD: str
    POSTGRES_DB_NAME: str
    
    @property
    def DB_URL(self) -> str:
        return f"postgresql+asyncpg://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}@{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/{self.POSTGRES_DB_NAME}"
    
    model_config = SettingsConfigDict(env_file='.env', extra="ignore")

pg_settings = DBSettings()

# Создание асинхронного движка
async_engine = create_async_engine(
    url=pg_settings.DB_URL,
    pool_size=10,
    max_overflow=20,
)

# Абстрактный класс модели
class Base(DeclarativeBase):
    pass

# Фабрика сессий с использованием AsyncSession
async_session_factory = async_sessionmaker(async_engine, class_=AsyncSession, expire_on_commit=False)