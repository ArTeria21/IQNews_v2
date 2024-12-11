from aiogram.fsm.state import StatesGroup, State

class EditProfile(StatesGroup):
    preferences = State()
    keywords = State()