from asyncio import exceptions
from apscheduler.jobstores.base import JobLookupError
import datetime
from aiogram.filters import Text
from aiogram import Router, types
from aiogram.filters.command import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    Message,
    CallbackQuery,
)

from bot import db, scheduler, bot
from bot.utils.calendar import Calendar
from bot.utils.notification import Notification
from bot.utils.scheduler import schedule_notification
from bot.utils.states import EditState
from bot.utils.timepicker import TimePicker

edit_router = Router()

edit_kb = InlineKeyboardMarkup(
    inline_keyboard=[
        [
            InlineKeyboardButton(
                text="Edit description",
                callback_data=f"EDIT_DESCRIPTION",
            ),
            InlineKeyboardButton(
                text="Edit date",
                callback_data=f"EDIT_DATE",
            ),
            InlineKeyboardButton(
                text="Edit time",
                callback_data=f"EDIT_TIME",
            ),
        ],
        [
            InlineKeyboardButton(text="Mark done", callback_data=f"EDIT_DONE"),
            InlineKeyboardButton(text="Delete", callback_data=f"EDIT_DELETE"),
        ],
    ]
)


@edit_router.message(Command("start"))
async def cmd_start(message: Message):
    await message.answer("Hello!")
    db.insert_user(id=message.from_user.id, username=message.from_user.username)


@edit_router.message(Command("help"))
async def cmd_help(message: Message, state: FSMContext):
    await message.answer("Help?")
    data = await state.get_data()
    print(data)


@edit_router.message(Command("show_current"))
async def current_tasks(message: Message, state: FSMContext):
    await state.set_state(EditState.idle)
    notifications = db.get_pending(uid=message.from_user.id)

    if len(notifications) == 0:
        await message.answer("No pending notifications")
        await state.clear()

    nts: dict[int, Notification] = {}
    calendars: dict[int, Calendar] = {}
    timers: dict[int, TimePicker] = {}

    for nt in notifications:
        if not nt.id:
            raise Exception(
                "Exception in current_tasks handler: Notification id is not initialized"
            )
        msg = await message.answer(
            f"{nt.text()}", parse_mode="Markdown", reply_markup=edit_kb
        )

        nts[msg.message_id] = nt
    await state.update_data(notifications=nts, calendars=calendars, timers=timers)


@edit_router.callback_query(Text(startswith="EDIT"), EditState.idle)
async def edit_handler(query: types.CallbackQuery, state: FSMContext):
    command = query.data.removeprefix("EDIT_")
    data = await state.get_data()
    nt: Notification = data["notifications"][query.message.message_id]

    if command == "DESCRIPTION":
        await query.message.edit_reply_markup(reply_markup=None)
        await state.set_state(EditState.description)
        await state.update_data(message_id=query.message.message_id)
        await query.message.answer(
            text="Input new description:",
            reply_to_message_id=query.message.message_id,
        )

    elif command == "DATE":
        cal = Calendar()
        calendars: dict[int, Calendar] = data["calendars"]
        calendars[query.message.message_id] = cal
        await state.update_data(calendars=calendars)
        await state.set_state(EditState.date)
        await query.message.edit_reply_markup(reply_markup=cal.get_keyboard())

    elif command == "TIME":
        timers: dict[int, TimePicker] = data["timers"]
        tp = TimePicker(time=nt.time)
        timers[query.message.message_id] = tp
        await state.update_data(timers=timers)
        await query.message.edit_reply_markup(reply_markup=tp.keyboard())
        await state.set_state(EditState.time)
    elif command == "DONE":
        db.mark_done(nt)
        try:
            scheduler.remove_job(str(nt.id))
        except JobLookupError as e:
            print("Exception: " + str(e))
        await query.message.delete()
    elif command == "DELETE":
        try:
            scheduler.remove_job(str(nt.id))
        except JobLookupError as e:
            print(e)
        db.delete_notification(nt)
        await query.message.delete()


@edit_router.callback_query(Text(startswith=TimePicker.prefix), EditState.time)
async def handle_time_edit(query: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    tp: TimePicker = data["timers"][query.message.message_id]
    nt: Notification = data["notifications"][query.message.message_id]

    command = query.data.removeprefix(TimePicker.prefix)
    if command == TimePicker.command_back:
        await query.message.edit_text(
            nt.text(),
            reply_markup=edit_kb,
            parse_mode="Markdown",
        )
        await state.set_state(EditState.idle)

    elif command == TimePicker.command_confirm:
        nt.time = tp.time
        sql = """UPDATE notifications SET time = %s WHERE id = %s"""
        db.excecute(
            sql,
            (
                nt.time,
                nt.id,
            ),
        )

        try:
            scheduler.remove_job(str(nt.id))
        except JobLookupError as e:
            print(e)

        schedule_notification(nt)
        await query.message.edit_text(
            nt.text(),
            reply_markup=edit_kb,
            parse_mode="Markdown",
        )
        await state.set_state(EditState.idle)

    else:
        await tp.handle_command(query, command)
        nt.time = tp.time
        await query.message.edit_text(
            nt.text(),
            reply_markup=tp.keyboard(),
            parse_mode="Markdown",
        )


@edit_router.message(EditState.description)
async def handle_description_update(message: Message, state: FSMContext):
    data = await state.get_data()
    message_id = data["message_id"]
    nt: Notification = data["notifications"][message_id]
    nt.description = str(message.text)
    sql = """UPDATE notifications SET description = %s WHERE id = %s"""
    db.excecute(
        sql,
        (
            nt.description,
            nt.id,
        ),
    )

    try:
        scheduler.remove_job(str(nt.id))
    except JobLookupError as e:
        print(e)
    schedule_notification(nt)
    await bot.edit_message_text(
        text=f"{nt.text()}",
        chat_id=message.chat.id,
        parse_mode="Markdown",
        message_id=message_id,
        reply_markup=edit_kb,
    )
    await message.answer(text="Description updated", reply_to_message_id=message_id)
    await state.set_state(EditState.idle)


@edit_router.callback_query(Text(startswith=Calendar.prefix), EditState.date)
async def handle_calendar(query: types.CallbackQuery, state: FSMContext):
    data = await state.get_data()
    cal: Calendar = data["calendars"][query.message.message_id]
    nt: Notification = data["notifications"][query.message.message_id]

    result, keyboard = cal.parse_query(query.data)

    if result:
        nt.date = result
        sql = """UPDATE notifications SET date = %s WHERE id = %s"""
        db.excecute(
            sql,
            (
                nt.date,
                nt.id,
            ),
        )

        try:
            scheduler.remove_job(str(nt.id))
        except JobLookupError as e:
            print(e)
        schedule_notification(nt)

        await query.message.edit_text(
            text=f"{nt.text()}",
            reply_markup=edit_kb,
            parse_mode="Markdown",
        )
        return await state.set_state(EditState.idle)
    elif keyboard:
        return await query.message.edit_reply_markup(reply_markup=keyboard)
