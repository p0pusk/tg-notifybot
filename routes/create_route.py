import asyncio
from datetime import datetime
from aiogram import Bot, Router, types, F
from aiogram.filters import Text
from aiogram.filters.command import Command
from aiogram.fsm.context import FSMContext

from utils.states import BotState
from utils.calendar import Calendar
from utils.notification import Notification
from utils.timepicker import TimePicker
from utils.utils import send_async_notification
from db import DataBase
from config import bot_token, dbconfig

create_router = Router()

bot = Bot(bot_token)
db = DataBase(
    user=dbconfig["USERNAME"],
    password=dbconfig["PASSWORD"],
    dbname=dbconfig["DB"],
    host=dbconfig["HOST"],
)


@create_router.message(Command("create"))
async def create_notification(message: types.Message, state: FSMContext):
    await state.set_state(BotState.text)
    await message.answer(text="Input notification text:")


@create_router.message(BotState.text)
async def handle_text(message: types.Message, state: FSMContext):
    if not message.from_user:
        raise Exception("Message sender is None")
    nt = Notification(message.from_user.id)
    cal = Calendar()
    nt.description = message.text
    await state.update_data(notification=nt, cal=cal)
    await message.answer(
        f"{nt.text()}\nChoose date:",
        reply_markup=cal.get_keyboard(),
        parse_mode="Markdown",
    )
    await state.set_state(BotState.date)


@create_router.callback_query(Text(startswith=Calendar.prefix), BotState.date)
async def cal_callback(query: types.CallbackQuery, state: FSMContext):
    data = await state.get_data()
    cal: Calendar = data["cal"]
    nt: Notification = data["notification"]
    result, keyboard = cal.parse_query(query.data)

    if result:
        tp = TimePicker()
        nt.date = result
        await state.update_data(notification=nt, timepicker=tp)
        await query.message.edit_text(
            text=f"{nt.text()}\nChoose time:",
            reply_markup=tp.keyboard(),
            parse_mode="Markdown",
        )
        await state.set_state(BotState.time)
    elif keyboard:
        await query.message.edit_reply_markup(reply_markup=keyboard)


@create_router.callback_query(Text(startswith=TimePicker.prefix), BotState.time)
async def time_handler(query: types.CallbackQuery, state: FSMContext):
    data = await state.get_data()
    nt: Notification = data["notification"]
    tp: TimePicker = data["timepicker"]
    cal: Calendar = data["cal"]

    command = query.data.removeprefix(TimePicker.prefix)
    if command == TimePicker.command_back:
        nt.time = None
        await state.set_state(BotState.date)
        await query.message.edit_text(
            f"{nt.text()}\nChoose date:",
            reply_markup=cal.get_keyboard(),
            parse_mode="Markdown",
        )

    elif command == TimePicker.command_confirm:
        nt.time = tp.time
        nt.time.replace(second=datetime.now().second)
        await state.set_state(BotState.attachment)
        kb = [
            [
                types.InlineKeyboardButton(text="No", callback_data="-TO_PERIODIC-"),
                types.InlineKeyboardButton(
                    text="Yes", callback_data="-ATTACHMENTS-YES-"
                ),
            ],
        ]

        await query.message.edit_text(
            text=f"{nt.text()}\nAdd attachments?",
            reply_markup=types.InlineKeyboardMarkup(inline_keyboard=kb),
            parse_mode="Markdown",
        )
    else:
        await tp.handle_command(query, command)
        await query.message.edit_text(
            text=f"{nt.text()}\n*Choose time:*",
            reply_markup=tp.keyboard(),
            parse_mode="Markdown",
        )


@create_router.callback_query(Text("-TO_PERIODIC-"))
async def handle_periodic(query: types.CallbackQuery, state: FSMContext):
    await state.set_state(BotState.periodic)
    data = await state.get_data()
    nt: Notification = data["notification"]

    kb = types.InlineKeyboardMarkup(
        inline_keyboard=[
            [
                types.InlineKeyboardButton(
                    text="No", callback_data="-NOTIFICATION_DONE-"
                ),
                types.InlineKeyboardButton(text="Yes", callback_data="-PERIODIC-"),
            ]
        ]
    )
    await query.message.edit_text(
        text=f"{nt.text()}\nDo you want to make notification periodic?",
        reply_markup=kb,
        parse_mode="Markdown",
    )


@create_router.callback_query(Text("-PERIODIC-"), BotState.periodic)
async def periodic_handler(query: types.CallbackQuery, state: FSMContext):
    data = await state.get_data()
    nt: Notification = data["notification"]
    nt.is_periodic = True

    kb = types.InlineKeyboardMarkup(
        inline_keyboard=[
            [
                types.InlineKeyboardButton(
                    text="Daily", callback_data="-REPEAT_DAILY-"
                ),
                types.InlineKeyboardButton(
                    text="Weekly", callback_data="-REPEAT_WEEKLY-"
                ),
                types.InlineKeyboardButton(
                    text="Yearly", callback_data="-REPEAT_YEARLY-"
                ),
            ]
        ]
    )
    await query.message.edit_text(
        text=f"{nt.text()}Choose repeat interval:",
        reply_markup=kb,
        parse_mode="Markdown",
    )


@create_router.callback_query(Text(startswith="-REPEAT"), BotState.periodic)
async def handle_repeat_value(query: types.CallbackQuery, state: FSMContext):
    data = await state.get_data()
    nt: Notification = data["notification"]

    period = query.data[8:-1]
    if period == "DAILY":
        nt.period = "daily"
    elif period == "MONTHLY":
        nt.period = "monthly"
    elif period == "YEARLY":
        nt.period = "yearly"
    else:
        raise Exception("[Notification period handler]: Unknown period")

    await state.update_data(notification=nt)
    await notifications_done(query, state)


@create_router.callback_query(Text("-NOTIFICATION_DONE-"), BotState.periodic)
async def notifications_done(query: types.CallbackQuery, state: FSMContext):
    try:
        data = await state.get_data()
        nt: Notification = data["notification"]

        now = datetime.now()
        nt.creation_date = now.date()
        nt.creation_time = now.time()

        if nt.date == None or nt.time == None:
            query.answer("Error while creating notification")
            raise Exception("date or time is null")

        asyncio.get_event_loop().create_task(send_async_notification(nt, bot))

        db.insert_notification(nt)
        await query.message.edit_text(
            text=f"Notification created!\n{nt.text()}",
            reply_markup=None,
            parse_mode="Markdown",
        )

    except Exception as e:
        print(e)
        await query.answer("Error occured when creating notification")

    await state.clear()
