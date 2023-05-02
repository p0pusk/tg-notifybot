from dataclasses import dataclass, field
import datetime


@dataclass
class Notification:
    uid: int
    id: int | None = None
    date: datetime.date | None = None
    time: datetime.time | None = None
    text: str = ""
    attachments_id: list[str] = field(default_factory=list)
