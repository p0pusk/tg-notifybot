from datetime import datetime, time
from aiogram import types


class TimePicker:
    prefix = "-TIME-"
    command_back = "-BACK-"
    command_confirm = "-CONFIRM-"
    command_minutes_up = "-MINUTES-UP-"
    command_minutes_down = "-MINUTES-DOWN-"
    command_hours_up = "-HOURS-UP-"
    command_hours_down = "-HOURS-DOWN-"

    def __init__(self) -> None:
        self.time: time = datetime.now().time()

    def keyboard(self):
        kb = [
            [
                types.InlineKeyboardButton(
                    text="up", callback_data=self.prefix + self.command_hours_up
                ),
                types.InlineKeyboardButton(
                    text="up", callback_data=self.prefix + self.command_minutes_up
                ),
            ],
            [
                types.InlineKeyboardButton(
                    text=f"{self.time.hour}", callback_data=self.prefix
                ),
                types.InlineKeyboardButton(
                    text=f"{self.time.minute}", callback_data=self.prefix
                ),
            ],
            [
                types.InlineKeyboardButton(
                    text="down", callback_data=self.prefix + self.command_hours_down
                ),
                types.InlineKeyboardButton(
                    text="down", callback_data=self.prefix + self.command_minutes_down
                ),
            ],
            [
                types.InlineKeyboardButton(
                    text="Confirm", callback_data=self.prefix + self.command_confirm
                )
            ],
            [
                types.InlineKeyboardButton(
                    text="Back", callback_data=self.prefix + self.command_back
                )
            ],
        ]

        return types.InlineKeyboardMarkup(inline_keyboard=kb)

    async def handle_command(self, query: types.CallbackQuery, command: str):
        if command == TimePicker.command_hours_down:
            if self.time.hour == 0:
                self.time = self.time.replace(hour=23)
            self.time = self.time.replace(hour=self.time.hour - 1)
        elif command == TimePicker.command_hours_up:
            if self.time.hour == 23:
                self.time = self.time.replace(hour=0)
            self.time = self.time.replace(hour=self.time.hour + 1)
        elif command == TimePicker.command_minutes_down:
            if self.time.minute == 0:
                self.time = self.time.replace(minute=59)
            self.time = self.time.replace(minute=self.time.minute - 1)
        elif command == TimePicker.command_minutes_up:
            if self.time.minute == 59:
                self.time = self.time.replace(minute=0)
            self.time = self.time.replace(minute=self.time.minute + 1)

        await query.answer()
