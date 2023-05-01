import asyncio
import datetime
from aiogram import Router, types, F
from aiogram.filters import Text
from aiogram.filters.command import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

from utils.calendar import Calendar
from utils.notification import Notification
from utils.timepicker import TimePicker
from db import db


class BotState(StatesGroup):
    text = State()
    date = State()
    time = State()
    attachment = State()


create_router = Router()


async def run_at(dt, coro):
    now = datetime.datetime.now()
    await asyncio.sleep((dt - now).total_seconds())
    return await coro


@create_router.message(Command("create_notification"))
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
    command = query.data.removeprefix(TimePicker.prefix)
    if command == TimePicker.command_back:
        nt.time = None

    elif command == TimePicker.command_confirm:
        nt.time = tp.time
        kb = [
            [
                types.InlineKeyboardButton(text="No", callback_data="-ATTACHMENTS-NO-"),
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


@create_router.callback_query(Text("-ATTACHMENTS-NO-"))
async def handle_attachments_no(query: types.CallbackQuery, state: FSMContext):
    data = await state.get_data()
    nt: Notification = data["notification"]

    if nt.date == None or nt.time == None:
        query.answer("Error while creating notification")
        raise Exception("date or time is null")

    loop = asyncio.get_event_loop()
    nt.task = loop.create_task(
        run_at(
            datetime.datetime.combine(nt.date, nt.time),
            query.message.answer(f"Notification!\n{nt.text}"),
        )
    )

    await query.message.edit_text(
        text=(
            f"Notification created!\nText: {nt.text}\nDate: {nt.date}\nTime:"
            f" {nt.time}\n"
        ),
        reply_markup=None,
        parse_mode="Markdown",
    )

    db.insert_notification(nt)
    await state.clear()


@create_router.callback_query(Text("-ATTACHMENTS-YES-"))
async def handle_attachments_yes(query: types.CallbackQuery, state: FSMContext):
    data = await state.get_data()
    nt: Notification = data["notification"]
    await query.message.edit_text(
        text=f"*Text:* {nt.text}\n*Date:* {nt.date}\n*Time:* {nt.time}\n",
        reply_markup=None,
        parse_mode="Markdown",
    )

    await state.set_state(BotState.attachment)
    await query.message.answer(text="Send attachments:")
    query.answer()


@create_router.message(BotState.attachment, F.content_type.in_({"document", "photo"}))
async def handle_attachment(
    message: types.Message,
    state: FSMContext,
):
    try:
        data = await state.get_data()
        await message.answer(
            text=(
                f"Notification created!\n\n*Text*: {data['text']}\n*Date*:"
                f" {data['date']}\n*Time* {data['hour']}:{data['minute']}\n"
            ),
            reply_markup=None,
            parse_mode="Markdown",
        )
        print(message.document.file_id)
        await message.answer_document(document=message.document.file_id)
        await state.clear()
    except Exception as e:
        print(e)
