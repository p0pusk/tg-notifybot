#!/usr/bin/env python

import calendar
from datetime import date
from aiogram import types


months = {
    1: "JAN",
    2: "FEB",
    3: "MAR",
    4: "APR",
    5: "MAY",
    6: "JUNE",
    7: "JULY",
    8: "AUGUST",
    9: "SEPTEMBER",
    10: "OCTOBER",
    11: "NOVEMBER",
    12: "DECEMBER",
}


class Calendar:
    prefix = "CAL/"

    def __init__(self) -> None:
        self.command_next_month = "NEXT"
        self.command_prev_month = "PREV"
        self.command_confirm_date = "CONFIRM"
        self.command_repeat__date = "REPEAT"
        self.button_next = ">>>"
        self.button_prev = "<<<"
        self.year = date.today().year
        self.month = date.today().month

    def get_keyboard(
        self, year: int = date.today().year, month: int = date.today().month
    ):
        cal = calendar.Calendar()
        kb = [
            [
                types.InlineKeyboardButton(
                    text=f"{months[month]} {year}", callback_data=f"{self.prefix}/"
                )
            ]
        ]
        week = []
        for idx, day in enumerate(cal.itermonthdays(year, month)):
            if idx % 7 == 0 and idx != 0:
                kb.append(week)
                week = []

            week.append(
                types.InlineKeyboardButton(
                    text=day if day != 0 else " ",
                    callback_data=(
                        f"{self.prefix}/{day}-{month}-{year}"
                        if day != 0
                        else f"{self.prefix}/"
                    ),
                )
            )

        if len(week) > 0:
            kb.append(week)

        kb.append(
            [
                types.InlineKeyboardButton(
                    text=self.button_prev,
                    callback_data=f"{self.prefix}{self.command_prev_month}/",
                ),
                types.InlineKeyboardButton(
                    text=self.button_next,
                    callback_data=f"{self.prefix}{self.command_next_month}/",
                ),
            ]
        )

        return types.InlineKeyboardMarkup(inline_keyboard=kb)

    def parse_query(self, data: str | None):
        if data is None:
            return
        data = data.removeprefix(self.prefix)
        command, result = data.split("/")
        keyboard = None

        if command == self.command_next_month:
            if self.month == 12:
                self.year += 1
                self.month = 1
            else:
                self.month += 1
            keyboard = self.get_keyboard(self.year, self.month)

        elif command == self.command_prev_month:
            if self.month == 1:
                self.year -= 1
                self.month = 12
            else:
                self.month -= 1
            keyboard = self.get_keyboard(self.year, self.month)

        day, month, year = result.split("-")

        return date(year=int(year), month=int(month), day=int(day)), keyboard
