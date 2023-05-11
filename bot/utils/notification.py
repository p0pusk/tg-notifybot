from dataclasses import dataclass, field
import datetime


@dataclass
class Attachment:
    file_id: str
    file_type: str
    filename: str | None


@dataclass
class Notification:
    uid: int
    id: int | None = None
    description: str = ""
    is_periodic: bool = False
    period: str | None = None
    date: datetime.date | None = None
    time: datetime.time | None = None
    creation_date: datetime.date | None = None
    creation_time: datetime.time | None = None
    is_done: bool = False
    attachments_id: list[Attachment] = field(default_factory=list[Attachment])

    def text(self):
        text = ""
        if self.description:
            text += f"*Description:* {self.description}\n"
        if self.date:
            text += f"*Date:* {self.date.strftime('%d.%m.%Y')}\n"
        if self.time:
            text += f"*Time:* {self.time.strftime('%H:%M')}\n"
        if self.is_periodic:
            text += f"*Periodic:* {'True' if self.is_periodic else 'False'}\n"
            if self.period:
                text += f"*Period:* {self.period}\n"
        if len(self.attachments_id) > 0:
            text += f"*Attachments:* ({len(self.attachments_id)})"

        return text
