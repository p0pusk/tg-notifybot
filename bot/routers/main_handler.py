from aiogram.filters import Text
from aiogram import Router, types
from aiogram.filters.command import Command
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

from bot import db, bot
from bot.utils.calendar import Calendar

main_router = Router()


@main_router.message(Command("start"))
async def cmd_start(message: types.Message):
    await message.answer("Hello!")
    db.insert_user(id=message.from_user.id, username=message.from_user.username)


@main_router.message(Command("show_current"))
async def current_tasks(message: types.Message):
    notifications = db.get_pending(uid=message.from_user.id)

    for nt in notifications:
        kb = InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(
                        text="Edit description",
                        callback_data=f"EDIT_DESCRIPTION_{nt.id}",
                    ),
                    InlineKeyboardButton(
                        text="Edit date", callback_data=f"EDIT_DATE_{nt.id}"
                    ),
                    InlineKeyboardButton(
                        text="Edit time", callback_data=f"EDIT_TIME_{nt.id}"
                    ),
                ],
                [
                    InlineKeyboardButton(
                        text="Mark done", callback_data=f"EDIT_DONE_{nt.id}"
                    ),
                    InlineKeyboardButton(
                        text="Delete", callback_data=f"EDIT_DELETE_{nt.id}"
                    ),
                ],
            ]
        )
        await message.answer(f"{nt.text()}", parse_mode="Markdown", reply_markup=kb)


@main_router.callback_query(Text(startswith="EDIT"))
async def edit_handler(query: types.CallbackQuery):
    _, command, id = query.data.split("_")

    cal = Calendar()
    if command == "DATE":
        query.message.edit_reply_markup(reply_markup=cal.get_keyboard())


@main_router.message(Command("show_done"))
async def show_done(message: types.Message):
    notifications = db.get_done(uid=message.from_user.id)

    kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="Return", callback_data="-EDIT_DESCRIPTION-"),
            ],
        ]
    )

    for nt in notifications:
        await message.answer(f"{nt.text()}", parse_mode="Markdown", reply_markup=kb)
