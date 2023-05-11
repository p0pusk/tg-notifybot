import asyncio
from aiogram.types import BotCommand

from bot import bot, dp, db, scheduler
from bot.routers import main_router, create_router, file_router
from bot.utils.scheduler import schedule_notification, schedule_periodic


async def setup_bot_commands():
    bot_commands = [
        BotCommand(command="/help", description="Show help"),
        BotCommand(command="/create", description="Create new notification"),
        BotCommand(command="/show_current", description="Show current notifications"),
        BotCommand(command="/show_done", description="Show done notifications"),
    ]
    await bot.set_my_commands(bot_commands)


async def awake():
    await setup_bot_commands()
    notifications = db.get_pending()
    if notifications is None:
        return

    for nt in notifications:
        if nt.is_periodic:
            schedule_periodic(nt)
        else:
            schedule_notification(nt)

    scheduler.start()


async def start():
    await awake()
    dp.include_router(main_router)
    dp.include_router(create_router)
    dp.include_router(file_router)
    await dp.start_polling(bot)
