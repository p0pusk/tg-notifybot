import schedule
import asyncio
import logging
from aiogram import Bot, Dispatcher, types
from aiogram.filters.command import Command

from routes.create_route import create_router
from routes.attachment_route import file_router
from db import DataBase
from config import bot_token, dbconfig
from utils.utils import send_async_notification

bot = Bot(token=bot_token)
logging.basicConfig(level=logging.INFO)
dp = Dispatcher()
db = DataBase(
    user=dbconfig["USERNAME"],
    password=dbconfig["PASSWORD"],
    dbname=dbconfig["DB"],
    host=dbconfig["HOST"],
)


@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    await message.answer("Hello!")
    db.insert_user(id=message.from_user.id, username=message.from_user.username)


async def start():
    notifications = db.get_all_notifications()
    if notifications is None:
        return

    loop = asyncio.get_event_loop()
    for nt in notifications:
        loop.create_task(send_async_notification(nt, bot))


async def main():
    await start()
    dp.include_router(create_router)
    dp.include_router(file_router)
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
