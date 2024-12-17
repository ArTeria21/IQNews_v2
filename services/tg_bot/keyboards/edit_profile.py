from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup


def get_edit_profile_keyboard():
    edit_preferences_keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="Интересы", callback_data="edit_preferences"),
                InlineKeyboardButton(
                    text="Антипатии", callback_data="edit_antipathy"
                ),
            ],
            [
                InlineKeyboardButton(text="Как стать PRO? 😎", callback_data="How_to_become_pro"),
            ]
        ]
    )
    return edit_preferences_keyboard
