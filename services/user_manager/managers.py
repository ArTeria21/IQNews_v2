# managers.py
import json
from sqlalchemy.future import select
from sqlalchemy.exc import NoResultFound
from database.models import User
from config import async_session_factory

from aio_pika import IncomingMessage, Channel, Message

class UserDBManager:
    async def create_user(self, user_id: int, username: str):
        async with async_session_factory() as session:
            user = await self.get_user(user_id, session)
            if not user:
                new_user = User(user_id=user_id, username=username)
                session.add(new_user)
                await session.commit()
                print(f"Пользователь {username} создан с ID {user_id}.")
            else:
                print(f"Пользователь с ID {user_id} уже существует.")

    async def get_user(self, user_id: int, session=None):
        if session is None:
            async with async_session_factory() as session:
                result = await session.execute(select(User).where(User.user_id == user_id))
                return result.scalar_one_or_none()
        else:
            result = await session.execute(select(User).where(User.user_id == user_id))
            return result.scalar_one_or_none()

    async def update_user(self, user_id: int, **kwargs):
        async with async_session_factory() as session:
            try:
                result = await session.execute(select(User).where(User.user_id == user_id))
                user = result.scalar_one()
                for key, value in kwargs.items():
                    if hasattr(user, key):
                        setattr(user, key, value)
                    else:
                        raise AttributeError(f"У пользователя нет атрибута '{key}'")
                await session.commit()
                print(f"Пользователь с ID {user_id} обновлен.")
            except NoResultFound:
                print(f"Пользователь с ID {user_id} не найден.")
            except Exception as e:
                await session.rollback()
                print(f"Ошибка при обновлении пользователя: {e}")

class UserQueueManager:
    def __init__(self, channel: Channel):
        self.user_db_manager = UserDBManager()
        self.channel = channel

    async def handle_create_user(self, message: IncomingMessage):
        async with message.process():
            try:
                body = json.loads(message.body.decode())
                user_id = body['user_id']
                username = body['username']
                await self.user_db_manager.create_user(user_id=user_id, username=username)
                print(f"Обработано создание пользователя с ID {user_id}.")
            except (KeyError, json.JSONDecodeError) as e:
                print(f"Неверный формат сообщения: {e}")

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
                        response = {
                            "status": "success",
                            "data": profile.to_dict()
                        }
                    else:
                        response = {"status": "error", "message": "Профиль не найден"}

                if reply_to:
                    await self.channel.default_exchange.publish(
                        Message(
                            body=json.dumps(response).encode(),
                            correlation_id=correlation_id
                        ),
                        routing_key=reply_to
                    )
                    print(f"Отправлен ответ на запрос профиля пользователя с ID {user_id}.")
            except (KeyError, json.JSONDecodeError) as e:
                print(f"Неверный формат запроса: {e}")
                
    async def handle_update_preferences(self, message: IncomingMessage):
        async with message.process():
            try:
                body = json.loads(message.body.decode())
                user_id = body['user_id']
                preferences = body['preferences']
                await self.user_db_manager.update_user(user_id=user_id, preferences=preferences)
                print(f"Обработано обновление интересов пользователя с ID {user_id}.")
            except (KeyError, json.JSONDecodeError) as e:
                print(f"Неверный формат сообщения: {e}")
                
    async def handle_update_keywords(self, message: IncomingMessage):
        async with message.process():
            try:
                body = json.loads(message.body.decode())
                user_id = body['user_id']
                keywords = body['keywords']
                await self.user_db_manager.update_user(user_id=user_id, keywords=keywords)
                print(f"Обработано обновление ключевых слов пользователя с ID {user_id}.")
            except (KeyError, json.JSONDecodeError) as e:
                print(f"Неверный формат сообщения: {e}")