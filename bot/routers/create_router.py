import asyncio
from datetime import datetime
from aiogram import Router, types
from aiogram.filters import Text
from aiogram.filters.command import Command
from aiogram.fsm.context import FSMContext

from bot import bot, scheduler, db
from bot.utils.states import CreateState
from bot.utils.calendar import Calendar
from bot.utils.notification import Notification
from bot.utils.timepicker import TimePicker
from bot.utils.scheduler import schedule_notification

create_router = Router()


@create_router.message(Command("create"))
async def create_notification(message: types.Message, state: FSMContext):
    await state.set_state(CreateState.text)
    await message.answer(text="Input notification text:")


@create_router.message(CreateState.text)
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
    await state.set_state(CreateState.date)


@create_router.callback_query(Text(startswith=Calendar.prefix), CreateState.date)
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
        await state.set_state(CreateState.time)
    elif keyboard:
        await query.message.edit_reply_markup(reply_markup=keyboard)


@create_router.callback_query(Text(startswith=TimePicker.prefix), CreateState.time)
async def time_handler(query: types.CallbackQuery, state: FSMContext):
    data = await state.get_data()
    nt: Notification = data["notification"]
    tp: TimePicker = data["timepicker"]
    cal: Calendar = data["cal"]

    command = query.data.removeprefix(TimePicker.prefix)
    if command == TimePicker.command_back:
        nt.time = None
        await state.set_state(CreateState.date)
        await query.message.edit_text(
            f"{nt.text()}\nChoose date:",
            reply_markup=cal.get_keyboard(),
            parse_mode="Markdown",
        )

    elif command == TimePicker.command_confirm:
        nt.time = tp.time
        nt.time.replace(second=datetime.now().second)
        await state.set_state(CreateState.attachment)
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
    await state.set_state(CreateState.periodic)
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


@create_router.callback_query(Text("-PERIODIC-"), CreateState.periodic)
async def periodic_handler(query: types.CallbackQuery, state: FSMContext):
    data = await state.get_data()
    nt: Notification = data["notification"]
    nt.is_periodic = True
    await state.update_data(notification=nt)

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
                    text="Monthly", callback_data="-REPEAT_MONTHLY-"
                ),
            ]
        ]
    )
    await query.message.edit_text(
        text=f"{nt.text()}Choose repeat interval:",
        reply_markup=kb,
        parse_mode="Markdown",
    )


@create_router.callback_query(Text(startswith="-REPEAT"), CreateState.periodic)
async def handle_repeat_value(query: types.CallbackQuery, state: FSMContext):
    data = await state.get_data()
    nt: Notification = data["notification"]

    period = query.data[8:-1]
    if period == "DAILY":
        nt.period = "daily"
    elif period == "WEEKLY":
        nt.period = "weekly"
    elif period == "MONTHLY":
        nt.period = "monthly"
    else:
        raise Exception("[Notification period handler]: Unknown period")

    await state.update_data(notification=nt)
    await query.message.edit_text(
        text=f"{nt.text()}",
        reply_markup=None,
    )
    await notifications_done(query, state)


@create_router.callback_query(Text("-NOTIFICATION_DONE-"), CreateState.periodic)
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

        db.insert_notification(nt)
        schedule_notification(nt)

        await query.message.edit_text(
            text=f"Notification created!\n{nt.text()}",
            reply_markup=None,
            parse_mode="Markdown",
        )

    except Exception as e:
        print(e)
        await query.answer("Error occured when creating notification")

    await state.clear()
