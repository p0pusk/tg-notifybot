import json
import asyncio
import logging
from aiogram import Bot, Dispatcher, types
from aiogram.filters.command import Command

from routes.create_route import create_router
from db import db


config = json.load(open("./config.json"))
bot = Bot(token=config["TOKEN"])
logging.basicConfig(level=logging.INFO)
dp = Dispatcher()


@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    await message.answer("Hello!")
    db.insert_user(id=message.from_user.id, username=message.from_user.username)


async def main():
    dp.include_router(create_router)
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
