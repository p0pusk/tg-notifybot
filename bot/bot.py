from aiogram.types import BotCommand

from bot import bot, dp, db, scheduler
from bot.routers import edit_router, create_router, file_router, return_router
from bot.utils.scheduler import schedule_notification


async def setup_bot_commands():
    bot_commands = [
        BotCommand(command="/create", description="Create new notification"),
        BotCommand(command="/show_current", description="Show current notifications"),
        BotCommand(command="/show_done", description="Show done notifications"),
        BotCommand(command="/help", description="Show help"),
    ]
    await bot.set_my_commands(bot_commands)


async def awake():
    await setup_bot_commands()
    notifications = db.get_pending()
    if notifications is None:
        return

    for nt in notifications:
        schedule_notification(nt)

    scheduler.start()


async def start():
    await awake()
    dp.include_router(edit_router)
    dp.include_router(create_router)
    dp.include_router(file_router)
    dp.include_router(return_router)
    await dp.start_polling(bot)
