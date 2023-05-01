from dataclasses import dataclass
import asyncio
import datetime


@dataclass
class Notification:
    uid: int
    date: datetime.date | None = None
    time: datetime.time | None = None
    text: str | None = None
    attachments_id: list[str] | None = None
    task: asyncio.Task | None = None
