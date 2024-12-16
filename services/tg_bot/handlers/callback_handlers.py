"""Модуль с handlers для обработки нажатий на кнопку клавиатуры"""

from aiogram import F, Router, types
from aiogram.fsm.context import FSMContext

from logger_setup import generate_correlation_id, setup_logger
from services.tg_bot.states.edit_profile import EditProfile
from services.tg_bot.texts import EDIT_KEYWORDS_TEXT, EDIT_PREFERENCES_TEXT

logger = setup_logger(__name__)

router = Router()


@router.callback_query(F.data == "edit_preferences")
async def edit_preferences_callback(callback: types.CallbackQuery, state: FSMContext):
    """Обработка нажатия на кнопку Изменить интересы"""
    correlation_id = generate_correlation_id()
    logger.info(
        "Обработка нажатия на кнопку Изменить интересы", correlation_id=correlation_id
    )
    await callback.message.answer(EDIT_PREFERENCES_TEXT)
    await state.set_state(EditProfile.preferences)
    await state.update_data(correlation_id=correlation_id)


@router.callback_query(F.data == "edit_keywords")
async def edit_keywords_callback(callback: types.CallbackQuery, state: FSMContext):
    """Обработка нажатия на кнопку Изменить ключевые слова"""
    correlation_id = generate_correlation_id()
    logger.info(
        "Обработка нажатия на кнопку Изменить ключевые слова",
        correlation_id=correlation_id,
    )
    await callback.message.answer(EDIT_KEYWORDS_TEXT)
    await state.set_state(EditProfile.keywords)
    await state.update_data(correlation_id=correlation_id)
