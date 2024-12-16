from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup


def get_edit_profile_keyboard():
    edit_preferences_keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="Интересы", callback_data="edit_preferences"),
                InlineKeyboardButton(
                    text="Ключевые слова", callback_data="edit_keywords"
                ),
            ]
        ]
    )
    return edit_preferences_keyboard
