from aiogram.fsm.state import StatesGroup, State

class SubscribeRss(StatesGroup):
    feed_url = State()