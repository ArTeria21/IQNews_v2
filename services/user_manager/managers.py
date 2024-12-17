# managers.py
import json

from aio_pika import Channel, IncomingMessage, Message
from sqlalchemy.exc import NoResultFound
from sqlalchemy.future import select

from logger_setup import setup_logger
from services.user_manager.config import async_session_factory
from services.user_manager.database.models import User

logger = setup_logger(__name__)


class UserDBManager:
    async def create_user(self, user_id: int, username: str, correlation_id: str):
        async with async_session_factory() as session:
            user = await self.get_user(user_id, session)
            if not user:
                new_user = User(user_id=user_id, username=username)
                session.add(new_user)
                await session.commit()
                logger.info(
                    f"Пользователь {username} создан с ID {user_id}.",
                    correlation_id=correlation_id,
                )
            else:
                logger.info(
                    f"Пользователь с ID {user_id} уже существует.",
                    correlation_id=correlation_id,
                )

    async def get_user(self, user_id: int, session=None):
        if session is None:
            async with async_session_factory() as session:
                result = await session.execute(
                    select(User).where(User.user_id == user_id)
                )
                return result.scalar_one_or_none()
        else:
            result = await session.execute(select(User).where(User.user_id == user_id))
            return result.scalar_one_or_none()

    async def update_user(self, user_id: int, correlation_id: str, **kwargs):
        async with async_session_factory() as session:
            try:
                result = await session.execute(
                    select(User).where(User.user_id == user_id)
                )
                user = result.scalar_one()
                for key, value in kwargs.items():
                    if hasattr(user, key):
                        setattr(user, key, value)
                    else:
                        raise AttributeError(f"У пользователя нет атрибута '{key}'")
                await session.commit()
                logger.info(
                    f"Пользователь с ID {user_id} обновлен.",
                    correlation_id=correlation_id,
                )
            except NoResultFound:
                logger.info(
                    f"Пользователь с ID {user_id} не найден.",
                    correlation_id=correlation_id,
                )
            except Exception as e:
                await session.rollback()
                logger.error(
                    f"Ошибка при обновлении пользователя: {e}",
                    correlation_id=correlation_id,
                )


class UserQueueManager:
    def __init__(self, channel: Channel):
        self.user_db_manager = UserDBManager()
        self.channel = channel

    async def handle_create_user(self, message: IncomingMessage):
        async with message.process():
            try:
                body = json.loads(message.body.decode())
                correlation_id = message.correlation_id
                user_id = body["user_id"]
                username = body["username"]
                await self.user_db_manager.create_user(
                    user_id=user_id, username=username, correlation_id=correlation_id
                )
                logger.info(
                    f"Обработано создание пользователя с ID {user_id}.",
                    correlation_id=correlation_id,
                )
            except (KeyError, json.JSONDecodeError) as e:
                logger.error(
                    f"Неверный формат сообщения: {e}", correlation_id=correlation_id
                )

    async def handle_get_user(self, message: IncomingMessage):
        async with message.process():
            try:
                request = json.loads(message.body.decode())
                user_id = request.get("user_id")
                correlation_id = message.correlation_id
                reply_to = message.reply_to

                if not user_id:
                    response = {"status": "error", "message": "user_id не предоставлен"}
                else:
                    profile: User | None = await self.user_db_manager.get_user(user_id)

                    if profile:
                        response = {"status": "success", "data": profile.to_dict()}
                    else:
                        response = {"status": "error", "message": "Профиль не найден"}

                if reply_to:
                    await self.channel.default_exchange.publish(
                        Message(
                            body=json.dumps(response).encode(),
                            correlation_id=correlation_id,
                        ),
                        routing_key=reply_to,
                    )
                    logger.info(
                        f"Отправлен ответ на запрос профиля пользователя с ID {user_id}.",
                        correlation_id=correlation_id,
                    )
            except (KeyError, json.JSONDecodeError) as e:
                logger.error(
                    f"Неверный формат запроса: {e}", correlation_id=correlation_id
                )

    async def handle_update_preferences(self, message: IncomingMessage):
        async with message.process():
            try:
                body = json.loads(message.body.decode())
                user_id = body["user_id"]
                preferences = body["preferences"]
                correlation_id = message.correlation_id
                await self.user_db_manager.update_user(
                    user_id=user_id,
                    preferences=preferences,
                    correlation_id=correlation_id,
                )
                logger.info(
                    f"Обработано обновление интересов пользователя с ID {user_id}.",
                    correlation_id=correlation_id,
                )
            except (KeyError, json.JSONDecodeError) as e:
                logger.error(
                    f"Неверный формат сообщения: {e}", correlation_id=correlation_id
                )

    async def handle_update_antipathy(self, message: IncomingMessage):
        async with message.process():
            try:
                body = json.loads(message.body.decode())
                user_id = body["user_id"]
                antipathy = body["antipathy"]
                correlation_id = message.correlation_id
                await self.user_db_manager.update_user(
                    user_id=user_id, antipathy=antipathy, correlation_id=correlation_id
                )
                logger.info(
                    f"Обработано обновление антипатий пользователя с ID {user_id}.",
                    correlation_id=correlation_id,
                )
            except (KeyError, json.JSONDecodeError) as e:
                logger.error(
                    f"Неверный формат сообщения: {e}", correlation_id=correlation_id
                )
    
    async def is_user_pro(self, user_id: int) -> bool:
        async with async_session_factory() as session:
            result = await session.execute(select(User).where(User.user_id == user_id))
            return result.scalar_one_or_none() is not None
    
    async def handle_is_user_pro(self, message: IncomingMessage):
        async with message.process():
            try:
                body = json.loads(message.body.decode())
                user_id = body["user_id"]
                correlation_id = message.correlation_id
                is_pro = await self.is_user_pro(user_id)
                response = {"status": "success", "is_pro": is_pro}
                await self.channel.default_exchange.publish(
                    Message(
                        body=json.dumps(response).encode(),
                        correlation_id=correlation_id,
                    ),
                    routing_key=message.reply_to,
                )
                logger.info(f"Отправлен ответ на запрос проверки статуса пользователя с ID {user_id}.", correlation_id=correlation_id)
            except (KeyError, json.JSONDecodeError) as e:
                logger.error(f"Неверный формат запроса: {e}", correlation_id=correlation_id)
