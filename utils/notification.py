from aiogram import Bot
from dataclasses import dataclass
import asyncio
import datetime


@dataclass
class Notification:
    uid: int
    date: datetime.date | None = None
    time: datetime.time | None = None
    text: str = ""
    attachments_id: list[str] | None = None

    async def send(self, bot):
        if self.date and self.time:
            dt = datetime.datetime.combine(self.date, self.time)
            now = datetime.datetime.now()
            await asyncio.sleep((dt - now).total_seconds())
            await bot.send_message(chat_id=self.uid, text=self.text)
        else:
            raise Exception("Exception: Notifications is not fully initialized")
