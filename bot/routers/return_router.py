from typing import Dict
from aiogram import Router
from aiogram.filters.command import Command
from aiogram.filters import Text
from aiogram.fsm.context import FSMContext
from apscheduler.jobstores.base import JobLookupError
from aiogram.types import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    Message,
    CallbackQuery,
)

from bot import db, scheduler
from bot.utils.calendar import Calendar
from bot.utils.scheduler import schedule_notification
from bot.utils.notification import Notification
from bot.utils.states import ReturnState
from bot.utils.timepicker import TimePicker

return_router = Router()


@return_router.message(Command("show_done"))
async def show_done(message: Message, state: FSMContext):
    await state.clear()
    notifications = db.get_done(uid=message.from_user.id)

    nts: dict[int, Notification] = {}
    calendars: dict[int, Calendar] = {}
    timers: dict[int, TimePicker] = {}

    if len(notifications) == 0:
        return await message.answer("No done notifications")

    for nt in notifications:
        kb = InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(
                        text="Return",
                        callback_data=f"RETURN_DONE_{nt.id}",
                    ),
                ],
            ]
        )
        msg = await message.answer(
            text=f"{nt.text()}",
            parse_mode="Markdown",
            reply_markup=kb,
        )
        nts[msg.message_id] = nt

    await state.set_state(ReturnState.idle)
    return await state.update_data(
        notifications=nts, calendars=calendars, timers=timers
    )


@return_router.callback_query(Text(startswith="RETURN_DONE_"), ReturnState.idle)
async def return_done(query: CallbackQuery, state: FSMContext):
    cal = Calendar()
    calendars = (await state.get_data())["calendars"]
    calendars[query.message.message_id] = cal
    await query.message.edit_reply_markup(reply_markup=cal.get_keyboard())
    await state.update_data(calendars=calendars)
    await state.set_state(ReturnState.date)


@return_router.callback_query(Text(startswith=Calendar.prefix), ReturnState.date)
async def handle_calendar(query: CallbackQuery, state: FSMContext):
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

        if nt is None:
            return query.message.answer("Notifications not found in db")

        timer = TimePicker(time=nt.time)
        timers = data["timers"]
        timers[query.message.message_id] = timer

        await query.message.edit_text(
            text=f"{nt.text()}",
            reply_markup=timer.keyboard(),
            parse_mode="Markdown",
        )
        await state.set_state(ReturnState.time)
    elif keyboard:
        return await query.message.edit_reply_markup(reply_markup=keyboard)


@return_router.callback_query(Text(startswith=TimePicker.prefix), ReturnState.time)
async def handle_time_edit(query: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    tp: TimePicker = data["timers"][query.message.message_id]
    nt: Notification = data["notifications"][query.message.message_id]
    cal: Calendar = data["calendars"][query.message.message_id]

    command = query.data.removeprefix(TimePicker.prefix)
    if command == TimePicker.command_back:
        await query.message.edit_text(
            nt.text(),
            reply_markup=cal.get_keyboard(),
            parse_mode="Markdown",
        )
        await state.set_state(ReturnState.date)

    elif command == TimePicker.command_confirm:
        nt.time = tp.time
        sql = """UPDATE notifications SET time = %s, is_done = FALSE WHERE id = %s"""
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
            "Notification returned to current",
            reply_markup=None,
            parse_mode="Markdown",
        )
        await state.set_state(ReturnState.idle)

    else:
        await tp.handle_command(query, command)
        nt.time = tp.time
        await query.message.edit_text(
            nt.text(),
            reply_markup=tp.keyboard(),
            parse_mode="Markdown",
        )
