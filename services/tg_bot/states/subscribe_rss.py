from aiogram.fsm.state import State, StatesGroup


class SubscribeRss(StatesGroup):
    feed_url = State()
    unsubscribe_feed_url = State()
