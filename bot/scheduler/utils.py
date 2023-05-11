from aiogram import Bot
import datetime

from bot import db, bot, scheduler
from bot.utils.notification import Notification


async def send_notification(nt: Notification, bot: Bot):
    msg = await bot.send_message(
        chat_id=nt.uid,
        text=f"*Notification!*\n\n{nt.description}",
        parse_mode="Markdown",
    )

    for idx, file in enumerate(nt.attachments_id):
        if not file.file_id:
            raise Exception("[Notification sender]: file_id is None")

        try:
            if file.file_type == "photo":
                await bot.send_photo(
                    chat_id=nt.uid,
                    photo=file.file_id,
                    caption=f"attachment #{idx + 1}",
                    reply_to_message_id=msg.message_id,
                )
            elif file.file_type == "document":
                await bot.send_document(
                    chat_id=nt.uid,
                    document=file.file_id,
                    caption=f"attachment #{idx+1}",
                    reply_to_message_id=msg.message_id,
                )
            elif file.file_type == "audio":
                await bot.send_audio(
                    chat_id=nt.uid,
                    audio=file.file_id,
                    caption=f"attachment #{idx+1}",
                    reply_to_message_id=msg.message_id,
                )
            elif file.file_type == "video":
                await bot.send_video(
                    chat_id=nt.uid,
                    video=file.file_id,
                    caption=f"attachment #{idx+1}",
                    reply_to_message_id=msg.message_id,
                )
        except Exception as e:
            print(e)
            await bot.send_message(
                chat_id=nt.uid,
                text=f"Error sending attachment #{idx+1}",
                reply_to_message_id=msg.message_id,
            )

    db.mark_done(nt)

    if nt.is_periodic:
        schedule_periodic(nt)


def schedule_periodic(nt: Notification):
    if not nt.date or not nt.time:
        raise Exception("Date and/or time not initialized")

    if not nt.is_done:
        schedule_notification(scheduler, nt, bot)
        return

    if nt.period == "daily":
        scheduler.add_job(
            send_notification,
            "cron",
            args=[nt, bot],
            day="*",
            hour=nt.time.hour,
            minute=nt.time.minute,
            id=str(nt.id),
        )
    elif nt.period == "weekly":
        scheduler.add_job(
            send_notification,
            "cron",
            args=[nt, bot],
            day="*/7",
            hour=nt.time.hour,
            minute=nt.time.minute,
            id=str(nt.id),
        )
    elif nt.period == "monthly":
        scheduler.add_job(
            send_notification,
            "cron",
            args=[nt, bot],
            month="*",
            day=nt.date.day,
            hour=nt.time.hour,
            minute=nt.time.minute,
            id=str(nt.id),
        )


def schedule_notification(nt: Notification):
    if nt.date and nt.time:
        dt = datetime.datetime.combine(nt.date, nt.time)
        scheduler.add_job(
            send_notification, "date", run_date=dt, args=[nt, bot], id=nt.id
        )
    else:
        raise Exception("Exception: Notifications is not fully initialized")
