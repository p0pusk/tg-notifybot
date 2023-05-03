from aiogram import Bot, types
import asyncio
import datetime
from typing import Union

from utils.notification import Notification
from db import DataBase
from config import dbconfig


async def send_async_notification(nt: Notification, bot: Bot):
    if nt.date and nt.time:
        dt = datetime.datetime.combine(nt.date, nt.time)
        now = datetime.datetime.now()
        await asyncio.sleep((dt - now).total_seconds())

        media_group: list[
            Union[
                types.InputMediaAudio,
                types.InputMediaDocument,
                types.InputMediaPhoto,
                types.InputMediaVideo,
            ]
        ] = []

        for idx, file in enumerate(nt.attachments_id):
            if not file.file_id:
                raise Exception("[Notification sender]: file_id is None")

            if file.file_type == "photo":
                media_group.append(
                    types.InputMediaPhoto(
                        type="photo",
                        media=file.file_id,
                        caption=(
                            f"*Notification!*\n\n{nt.description}" if idx == 0 else None
                        ),
                        parse_mode="Markdown",
                    )
                )
            elif file.file_type == "document":
                media_group.append(
                    types.InputMediaDocument(
                        type="document",
                        media=file.file_id,
                        caption=(
                            f"*Notification!*\n\n{nt.description}" if idx == 0 else None
                        ),
                        parse_mode="Markdown",
                    )
                )
            elif file.file_type == "audio":
                media_group.append(
                    types.InputMediaAudio(
                        type="audio",
                        media=file.file_id,
                        caption=(
                            f"*Notification!*\n\n{nt.description}" if idx == 0 else None
                        ),
                        parse_mode="Markdown",
                    )
                )
            elif file.file_type == "video":
                media_group.append(
                    types.InputMediaVideo(
                        type="video",
                        media=file.file_id,
                        caption=(
                            f"*Notification!*\n\n{nt.description}" if idx == 0 else None
                        ),
                        parse_mode="Markdown",
                    )
                )

        if len(media_group) > 0:
            await bot.send_media_group(chat_id=nt.uid, media=media_group)
        else:
            await bot.send_message(
                chat_id=nt.uid,
                text=f"*Notification!*\n\n{nt.description}",
                parse_mode="Markdown",
            )

        db = DataBase(
            user=dbconfig["USERNAME"],
            password=dbconfig["PASSWORD"],
            dbname=dbconfig["DB"],
            host=dbconfig["HOST"],
        )
        db.mark_done(nt)
    else:
        raise Exception("Exception: Notifications is not fully initialized")
