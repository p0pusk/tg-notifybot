from aiogram.fsm.state import State, StatesGroup


class BotState(StatesGroup):
    text = State()
    date = State()
    time = State()
    attachment = State()
