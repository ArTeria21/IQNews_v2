import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

def get_edit_profile_keyboard():
    edit_preferences_keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="Интересы", callback_data="edit_preferences"),
            InlineKeyboardButton(text="Ключевые слова", callback_data="edit_keywords")]
        ]
    )
    return edit_preferences_keyboard
