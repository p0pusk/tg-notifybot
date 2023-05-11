import logging
from aiogram import Bot, Dispatcher
from apscheduler.schedulers.asyncio import AsyncIOScheduler

import config
from bot.db import DataBase

config = config
bot = Bot(token=config.bot_token)
logging.basicConfig(level=logging.INFO)
scheduler = AsyncIOScheduler()
dp = Dispatcher()


db = DataBase(
    user=config.dbconfig["USERNAME"],
    password=config.dbconfig["PASSWORD"],
    dbname=config.dbconfig["DB"],
    host=config.dbconfig["HOST"],
)
