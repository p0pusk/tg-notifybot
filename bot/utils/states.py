from aiogram.fsm.state import State, StatesGroup


class CreateState(StatesGroup):
    text = State()
    date = State()
    time = State()
    attachment = State()
    ask_more_files = State()
    periodic = State()
