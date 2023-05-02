from typing import Union
from aiogram.fsm.context import FSMContext
from aiogram.filters import Text, Filter
from aiogram import Bot, Router, types, F

from db import DataBase
from utils.states import BotState
from utils.notification import Notification
from middlewares.album_middleware import AlbumMidleware
from config import bot_token, dbconfig

file_router = Router()
file_router.message.middleware(AlbumMidleware())

bot = Bot(bot_token)
db = DataBase(
    user=dbconfig["USERNAME"],
    password=dbconfig["PASSWORD"],
    dbname=dbconfig["DB"],
    host=dbconfig["HOST"],
)


class MediagroupFilter(Filter):
    async def __call__(self, message: types.Message) -> bool:
        return message.media_group_id is not None


@file_router.callback_query(Text("-ATTACHMENTS-YES-"))
async def handle_attachments_yes(query: types.CallbackQuery, state: FSMContext):
    data = await state.get_data()
    nt: Notification = data["notification"]
    await query.message.edit_text(
        text=f"*Text:* {nt.text}\n*Date:* {nt.date}\n*Time:* {nt.time}\n",
        reply_markup=None,
        parse_mode="Markdown",
    )

    await state.set_state(BotState.attachment)
    await query.message.answer(text="Send attachments:")
    query.answer()


@file_router.message(
    MediagroupFilter(),
    BotState.attachment,
    F.content_type.in_({"document", "photo", "audio", "video"}),
)
async def handle_mediagroup(
    message: types.Message, state: FSMContext, album: list[types.Message]
):
    data = await state.get_data()
    nt: Notification = data["notification"]
    media_group: list[
        Union[
            types.InputMediaAudio,
            types.InputMediaDocument,
            types.InputMediaPhoto,
            types.InputMediaVideo,
        ]
    ] = []
    for obj in album:
        if obj.photo:
            file_id = obj.photo[-1].file_id
            media_group.append(types.InputMediaPhoto(type="photo", media=file_id))
        elif obj.document:
            file_id = obj.document.file_id
            media_group.append(types.InputMediaDocument(type="document", media=file_id))
        elif obj.audio:
            file_id = obj.audio.file_id
            media_group.append(types.InputMediaAudio(type="audio", media=file_id))
        else:
            return await message.answer(
                "This type of album is not supported by aiogram."
            )

        nt.attachments_id.append(file_id)

    await message.answer_media_group(media_group)


@file_router.message(
    BotState.attachment, F.content_type.in_({"document", "photo", "audio", "video"})
)
async def handle_attachment(message: types.Message, state: FSMContext):
    data = await state.get_data()
    nt: Notification = data["notification"]
    try:
        if message.photo:
            file_id = message.photo[-1].file_id
        elif message.document:
            file_id = message.document.file_id
        elif message.audio:
            file_id = message.audio.file_id
        elif message.video:
            file_id = message.video.file_id
        else:
            return await message.answer("This type is not supported.")
        nt.attachments_id.append(file_id)
        return await message.answer(
            text="Attach more?",
            reply_markup=types.InlineKeyboardMarkup(
                inline_keyboard=[
                    [
                        types.InlineKeyboardButton(
                            text="No", callback_data="-NOTIFICATION_DONE-"
                        ),
                        types.InlineKeyboardButton(
                            text="Yes", callback_data="-ATTACH_MORE-"
                        ),
                    ]
                ]
            ),
        )
    except Exception as e:
        print(e)
        await message.answer("Error occured while getting your file")


@file_router.callback_query(Text("-ATTACH_MORE-"))
async def attach_more(query: types.CallbackQuery):
    await query.message.edit_reply_markup(reply_markup=None)
    return await query.answer()
