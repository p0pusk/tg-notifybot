from aiogram.fsm.context import FSMContext
from aiogram.filters import Text, Filter
from aiogram import Router, types, F

from bot import bot
from bot.utils.states import CreateState
from bot.utils.notification import Attachment, Notification
from bot.middlewares.album_middleware import AlbumMidleware

file_router = Router()
file_router.message.middleware(AlbumMidleware())


class MediagroupFilter(Filter):
    async def __call__(self, message: types.Message) -> bool:
        return message.media_group_id is not None


@file_router.callback_query(Text("-ATTACHMENTS-YES-"))
async def handle_attachments_yes(query: types.CallbackQuery, state: FSMContext):
    data = await state.get_data()
    nt: Notification = data["notification"]
    await query.message.edit_text(
        text=f"*Text:* {nt.description}\n*Date:* {nt.date}\n*Time:* {nt.time}\n",
        reply_markup=None,
        parse_mode="Markdown",
    )

    await state.set_state(CreateState.attachment)
    return await query.message.answer(text="Send attachments:")


@file_router.message(
    MediagroupFilter(),
    CreateState.attachment,
    F.content_type.in_({"document", "photo", "audio", "video"}),
)
async def handle_mediagroup(
    message: types.Message, state: FSMContext, album: list[types.Message]
):
    data = await state.get_data()
    nt: Notification = data["notification"]
    for obj in album:
        if obj.photo:
            file_id = obj.photo[-1].file_id
            file_type = "photo"
        elif obj.document:
            file_id = obj.document.file_id
            file_type = "document"
        elif obj.audio:
            file_id = obj.audio.file_id
            file_type = "audio"
        elif obj.video:
            file_id = obj.video.file_id
            file_type = "video"
        else:
            return await message.answer("This type of file is not supported.")

        file = await bot.get_file(file_id)
        nt.attachments_id.append(Attachment(file_id, file_type, file.file_path))

    await state.update_data(notification=nt)
    await message.answer(
        text="Got your files. Attach more?",
        reply_markup=types.InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    types.InlineKeyboardButton(
                        text="No", callback_data="-TO_PERIODIC-"
                    ),
                    types.InlineKeyboardButton(
                        text="Yes", callback_data="-ATTACH_MORE-"
                    ),
                ]
            ]
        ),
    )

    await state.set_state(CreateState.ask_more_files)


@file_router.message(
    CreateState.attachment, F.content_type.in_({"document", "photo", "audio", "video"})
)
async def handle_attachment(message: types.Message, state: FSMContext):
    data = await state.get_data()
    nt: Notification = data["notification"]
    try:
        if message.photo:
            file_id = message.photo[-1].file_id
            file_type = "photo"
        elif message.document:
            file_id = message.document.file_id
            file_type = "document"
        elif message.audio:
            file_id = message.audio.file_id
            file_type = "audio"
        elif message.video:
            file_id = message.video.file_id
            file_type = "video"
        else:
            await message.answer("This type is not supported.")
            return
        file = await bot.get_file(file_id)
        nt.attachments_id.append(Attachment(file_id, file_type, file.file_path))
        await state.update_data(notification=nt)
        await state.set_state(CreateState.ask_more_files)
        await message.answer(
            text="Got your file. Attach more?",
            reply_markup=types.InlineKeyboardMarkup(
                inline_keyboard=[
                    [
                        types.InlineKeyboardButton(
                            text="No", callback_data="-TO_PERIODIC-"
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


@file_router.callback_query(Text("-ATTACH_MORE-"), CreateState.ask_more_files)
async def attach_more(query: types.CallbackQuery, state: FSMContext):
    await state.set_state(CreateState.attachment)
    await query.message.edit_text(text="Send attachments:", reply_markup=None)
