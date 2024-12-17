import asyncio
import json

from aio_pika import Message
from aiogram import Router, types, F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext

from logger_setup import generate_correlation_id, setup_logger
from services.tg_bot.config import get_rabbit_connection, ADMIN_PASSWORD
from services.tg_bot.keyboards.admin_panel import get_admin_panel_keyboard
from services.tg_bot.texts import ADMIN_PANEL_TEXT, ADMIN_PANEL_PASSWORD_TEXT, CORRECT_PASSWORD_TEXT, INCORRECT_PASSWORD_TEXT
from services.tg_bot.states.administrator import Administrator

logger = setup_logger(__name__)

router = Router()

async def get_admin_panel_text() -> str:
    # TODO: add service statistics
    return ADMIN_PANEL_TEXT

async def set_status(user_id: int | str, correlation_id: str, status: str = "pro") -> None:
    connection = await get_rabbit_connection()
    channel = await connection.channel()
    if isinstance(user_id, int) or user_id.isdigit():
        queue = await channel.declare_queue("user.set_status.id", durable=True)
        logger.info(f"Отправка сообщения в очередь user.set_status.id: {user_id} {status}", correlation_id=correlation_id)
    elif isinstance(user_id, str):
        if user_id.startswith("@"):
            user_id = user_id[1:]
        queue = await channel.declare_queue("user.set_status.username", durable=True)
        logger.info(f"Отправка сообщения в очередь user.set_status.username: {user_id} {status}", correlation_id=correlation_id)
    await channel.default_exchange.publish(
        Message(body=json.dumps({"user_id": user_id, "status": status, "correlation_id": correlation_id}).encode()),
        routing_key=queue.name,
    )

@router.message(Command("admin_panel"))
async def admin_panel_command(message: types.Message, state: FSMContext):
    """Обработка команды /admin_panel"""
    correlation_id = generate_correlation_id()
    logger.info(f"Пользователь {message.from_user.id} запросил доступ в админ-панель", correlation_id=correlation_id)
    await message.answer(ADMIN_PANEL_PASSWORD_TEXT)
    await state.set_state(Administrator.password)
    await state.update_data(correlation_id = correlation_id)

@router.message(Administrator.password)
async def admin_panel_password_handler(message: types.Message, state: FSMContext):
    """Обработка ввода пароля"""
    password = message.text
    data = await state.get_data()
    if password == ADMIN_PASSWORD:
        temp_message = await message.answer(CORRECT_PASSWORD_TEXT)
        await state.set_state(Administrator.panel)
        logger.info(f"Пользователь {message.from_user.id} ввёл правильный пароль", correlation_id=data["correlation_id"])
        await asyncio.sleep(1) # Для красоты
        await admin_panel_handler(message, state)
        await message.delete()
        await temp_message.delete()
    else:
        await message.answer(INCORRECT_PASSWORD_TEXT)
        logger.info(f"Пользователь {message.from_user.id} ввёл неправильный пароль", correlation_id=data["correlation_id"])
        await state.clear()
        await message.delete()

@router.message(Administrator.panel)
async def admin_panel_handler(message: types.Message, state: FSMContext):
    """Обработка команд в админ-панели"""
    panel_text = await get_admin_panel_text()
    await message.answer(panel_text, reply_markup=get_admin_panel_keyboard())

@router.callback_query(F.data == "set_as_pro")
async def set_as_pro_callback(callback: types.CallbackQuery, state: FSMContext):
    """Обработка нажатия на кнопку Установить PRO"""
    current_state = await state.get_state()
    if current_state != Administrator.panel:
        await callback.answer("Вы не в админ-панели", show_alert=True)
        return
    await callback.message.delete()
    await state.set_state(Administrator.set_as_pro)
    await callback.message.answer(f"Введите ID пользователя, статус которого хотите установить в PRO")

@router.callback_query(F.data == "set_as_free")
async def set_as_free_callback(callback: types.CallbackQuery, state: FSMContext):
    """Обработка нажатия на кнопку Установить FREE"""
    current_state = await state.get_state()
    if current_state != Administrator.panel:
        await callback.answer("Вы не в админ-панели", show_alert=True)
        return
    await callback.message.delete()
    await state.set_state(Administrator.set_as_free)
    await callback.message.answer(f"Введите ID пользователя, статус которого хотите установить в FREE")

@router.message(Administrator.set_as_free)
async def set_as_free_handler(message: types.Message, state: FSMContext):
    """Обработка ввода ID пользователя для установки статуса FREE"""
    user_id = message.text
    data = await state.get_data()
    await set_status(user_id, data["correlation_id"], "free")
    await message.answer(f"Статус пользователя {user_id} установлен в FREE")
    await state.clear()
    
@router.message(Administrator.set_as_pro)
async def set_as_pro_handler(message: types.Message, state: FSMContext):
    """Обработка ввода ID пользователя для установки статуса PRO"""
    user_id = message.text
    data = await state.get_data()
    await set_status(user_id, data["correlation_id"], "pro")
    await message.answer(f"Статус пользователя {user_id} установлен в PRO")
    await state.clear()