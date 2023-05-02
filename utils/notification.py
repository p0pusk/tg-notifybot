from dataclasses import dataclass
import datetime


@dataclass
class Notification:
    uid: int
    id: int | None = None
    date: datetime.date | None = None
    time: datetime.time | None = None
    text: str = ""
    attachments_id: list[str] | None = None
