from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup


def get_edit_profile_keyboard():
    edit_preferences_keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="Интересы", callback_data="edit_preferences"),
                InlineKeyboardButton(
                    text="Антипатии", callback_data="edit_antipathy"
                ),
            ]
        ]
    )
    return edit_preferences_keyboard
