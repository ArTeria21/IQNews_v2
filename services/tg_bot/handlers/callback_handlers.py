"""Модуль с handlers для обработки нажатий на кнопку клавиатуры"""
import json

from aiogram import Router, types
from aiogram import F
from aiogram.fsm.context import FSMContext

from services.tg_bot.texts import EDIT_PREFERENCES_TEXT, EDIT_KEYWORDS_TEXT
from services.tg_bot.states.edit_profile import EditProfile

from logger_setup import setup_logger, generate_correlation_id

logger = setup_logger(__name__)

router = Router()

@router.callback_query(F.data == "edit_preferences")
async def edit_preferences_callback(callback: types.CallbackQuery, state: FSMContext):
    """Обработка нажатия на кнопку Изменить интересы"""
    print("edit_preferences_callback")
    correlation_id = generate_correlation_id()
    logger.info("Обработка нажатия на кнопку Изменить интересы", correlation_id=correlation_id)
    await callback.message.answer(EDIT_PREFERENCES_TEXT)
    await state.set_state(EditProfile.preferences)
    await state.update_data(correlation_id=correlation_id)

@router.callback_query(F.data == "edit_keywords")
async def edit_keywords_callback(callback: types.CallbackQuery, state: FSMContext):
    """Обработка нажатия на кнопку Изменить ключевые слова"""
    print("edit_keywords_callback")
    correlation_id = generate_correlation_id()
    logger.info("Обработка нажатия на кнопку Изменить ключевые слова", correlation_id=correlation_id)
    await callback.message.answer(EDIT_KEYWORDS_TEXT)
    await state.set_state(EditProfile.keywords)
    await state.update_data(correlation_id=correlation_id)
