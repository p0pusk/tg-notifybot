import asyncio
from aiogram import types
from aiogram.filters.command import Command

from bot import bot, dp, db, scheduler, config
from bot.routes.create_route import create_router
from bot.routes.attachment_route import file_router
from bot.scheduler.utils import schedule_notification, schedule_periodic


@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    await message.answer("Hello!")
    db.insert_user(id=message.from_user.id, username=message.from_user.username)


async def awake():
    notifications = db.get_pending()
    if notifications is None:
        return

    loop = asyncio.get_event_loop()
    for nt in notifications:
        if nt.is_periodic:
            schedule_periodic(scheduler, nt, bot)
        else:
            schedule_notification(scheduler, nt, bot)

    scheduler.start()


async def start():
    await awake()
    dp.include_router(create_router)
    dp.include_router(file_router)
    await dp.start_polling(bot)
