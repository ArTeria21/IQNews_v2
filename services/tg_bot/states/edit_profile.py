from aiogram.fsm.state import State, StatesGroup


class EditProfile(StatesGroup):
    preferences = State()
    keywords = State()
