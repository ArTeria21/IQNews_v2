from aiogram.fsm.state import StatesGroup, State

class SubscribeRss(StatesGroup):
    feed_url = State()
    unsubscribe_feed_url = State()