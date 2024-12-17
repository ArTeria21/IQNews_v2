from aiogram.fsm.state import State, StatesGroup


class Administrator(StatesGroup):
    password = State()
    set_as_pro = State()
    set_as_free = State()
    panel = State()