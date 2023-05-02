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
    nt.text = message.text
    await state.update_data(notification=nt, cal=cal)
    await message.answer(
        f"Text: {message.text}\nChoose date:", reply_markup=cal.get_keyboard()
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
            text=f"Text: {nt.text}\nDate: {nt.date}\nChoose time:",
            reply_markup=tp.keyboard(),
        )
        await state.set_state(BotState.time)
    elif keyboard:
        await query.message.edit_reply_markup(reply_markup=keyboard)

    await query.answer()


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
            f"Text: {nt.text}\nChoose date:", reply_markup=cal.get_keyboard()
        )

    elif command == TimePicker.command_confirm:
        nt.time = tp.time
        nt.time.replace(second=datetime.now().second)
        await state.set_state(BotState.attachment)
        kb = [
            [
                types.InlineKeyboardButton(
                    text="No", callback_data="-NOTIFICATION_DONE--"
                ),
                types.InlineKeyboardButton(
                    text="Yes", callback_data="-ATTACHMENTS-YES-"
                ),
            ],
        ]

        await query.message.edit_text(
            text=(
                f"*Text*: {nt.text}\n*Date*: {nt.date}\n*Time: {nt.time}*\nAdd"
                " attachments?"
            ),
            reply_markup=types.InlineKeyboardMarkup(inline_keyboard=kb),
            parse_mode="Markdown",
        )
    else:
        await tp.handle_command(query, command)
        await query.message.edit_text(
            text=f"*Text:* {nt.text}\n*Date:* {nt.date}\n*Choose time:*",
            reply_markup=tp.keyboard(),
            parse_mode="Markdown",
        )


@create_router.callback_query(Text("-NOTIFICATION_DONE-"), BotState.attachment)
async def handle_attachments_no(query: types.CallbackQuery, state: FSMContext):
    try:
        data = await state.get_data()
        nt: Notification = data["notification"]

        if nt.date == None or nt.time == None:
            query.answer("Error while creating notification")
            raise Exception("date or time is null")

        asyncio.get_event_loop().create_task(send_async_notification(nt, bot))

        db.insert_notification(nt)
        await query.message.edit_text(
            text=(
                f"Notification created!\nText: {nt.text}\nDate: {nt.date}\nTime:"
                f" {nt.time}\n"
            ),
            reply_markup=None,
            parse_mode="Markdown",
        )

    except Exception as e:
        print(e)
        await query.answer("Error occured when creating notification")

    await state.clear()