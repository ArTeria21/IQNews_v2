from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup


def get_admin_panel_keyboard():
    admin_panel_keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="Установить PRO", callback_data="set_as_pro"),
                InlineKeyboardButton(text="Установить FREE", callback_data="set_as_free"),
            ]
        ]
    )
    return admin_panel_keyboard