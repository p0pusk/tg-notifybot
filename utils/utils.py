from aiogram import Bot
import asyncio
import datetime

from utils.notification import Notification
from db import DataBase
from config import dbconfig


async def send_async_notification(nt: Notification, bot: Bot):
    if nt.date and nt.time:
        dt = datetime.datetime.combine(nt.date, nt.time)
        now = datetime.datetime.now()
        await asyncio.sleep((dt - now).total_seconds())
        await bot.send_message(chat_id=nt.uid, text=nt.text)
        db = DataBase(
            user=dbconfig["USERNAME"],
            password=dbconfig["PASSWORD"],
            dbname=dbconfig["DB"],
            host=dbconfig["HOST"],
        )
        db.delete_notification(nt)
    else:
        raise Exception("Exception: Notifications is not fully initialized")
