import asyncio
import os

from pyrogram import filters
from pyrogram.errors import FloodWait
from pyrogram.types import CallbackQuery, InputMediaPhoto, Message

import config
from AnonXMusic import app
from AnonXMusic.misc import db
from AnonXMusic.utils import AnonyBin, get_channeplayCB, seconds_to_min
from AnonXMusic.utils.database import get_cmode, is_active_chat, is_music_playing
from AnonXMusic.utils.decorators.language import language, languageCB
from AnonXMusic.utils.inline import queue_back_markup, queue_markup
from config import BANNED_USERS

basic = {}


def get_image(videoid):
    if os.path.isfile(f"cache/{videoid}.png"):
        return f"cache/{videoid}.png"
    else:
        return config.YOUTUBE_IMG_URL


def get_duration(playing):
    file_path = playing[0]["file"]
    if "index_" in file_path or "live_" in file_path:
        return "Unknown"
    duration_seconds = int(playing[0]["seconds"])
    if duration_seconds == 0:
        return "Unknown"
    else:
        return "Inline"


@app.on_message(
    filters.command(["queue", "cqueue", "player", "cplayer", "playing", "cplaying"])
    & filters.group
    & ~BANNED_USERS
)
@language
async def get_queue(client, message: Message, _):
    if message.command[0][0] == "c":
        chat_id = await get_cmode(message.chat.id)
        if chat_id is None:
            return await message.reply_text(_["setting_7"])
        try:
            await app.get_chat(chat_id)
        except:
            return await message.reply_text(_["cplay_4"])
        cplay = True
    else:
        chat_id = message.chat.id
        cplay = False
    if not await is_active_chat(chat_id):
        return await message.reply_text(_["general_5"])
    got = db.get(chat_id)
    if not got:
        return await message.reply_text(_["queue_2"])
    file = got[0]["file"]
    videoid = got[0]["vidid"]
    user = got[0]["by"]
    title = (got[0]["title"]).title()
    typo = (got[0]["streamtype"]).title()
    DUR = get_duration(got)
    if "live_" in file:
        IMAGE = get_image(videoid)
    elif "vid_" in file:
        IMAGE = get_image(videoid)
    elif "index_" in file:
        IMAGE = config.STREAM_IMG_URL
    else:
        if videoid == "telegram":
            IMAGE = (
                config.TELEGRAM_AUDIO_URL
                if typo == "Audio"
                else config.TELEGRAM_VIDEO_URL
            )
        elif videoid == "soundcloud":
            IMAGE = config.SOUNCLOUD_IMG_URL
        else:
            IMAGE = get_image(videoid)
    send = _["queue_6"] if DUR == "Unknown" else _["queue_7"]
    cap = _["queue_8"].format(app.mention, title, typo, user, send)
    upl = (
        queue_markup(_, DUR, "c" if cplay else "g", videoid)
        if DUR == "Unknown"
        else queue_markup(
            _,
            DUR,
            "c" if cplay else "g",
            videoid,
            seconds_to_min(got[0]["played"]),
            got[0]["dur"],
        )
    )
    basic[videoid] = True
    mystic = await message.reply_photo(IMAGE, caption=cap, reply_markup=upl)
    if DUR != "Unknown":
        try:
            while db[chat_id][0]["vidid"] == videoid:
                await asyncio.sleep(5)
                if await is_active_chat(chat_id):
                    if basic[videoid]:
                        if await is_music_playing(chat_id):
                            try:
                                buttons = queue_markup(
                                    _,
                                    DUR,
                                    "c" if cplay else "g",
                                    videoid,
                                    seconds_to_min(db[chat_id][0]["played"]),
                                    db[chat_id][0]["dur"],
                                )
                                await mystic.edit_reply_markup(reply_markup=buttons)
                            except FloodWait:
                                pass
                        else:
                            pass
                    else:
                        break
                else:
                    break
        except:
            return


@app.on_callback_query(filters.regex("GetTimer") & ~BANNED_USERS)
async def quite_timer(client, CallbackQuery: CallbackQuery):
    try:
        await CallbackQuery.answer()
    except:
        pass


@app.on_callback_query(filters.regex("GetQueued") & ~BANNED_USERS)
@languageCB
async def queued_tracks(client, CallbackQuery: CallbackQuery, _):
    callback_data = CallbackQuery.data.strip()
    callback_request = callback_data.split(None, 1)[1]
    what, videoid = callback_request.split("|")
    try:
        chat_id, channel = await get_channeplayCB(_, what, CallbackQuery)
    except:
        return
    if not await is_active_chat(chat_id):
        return await CallbackQuery.answer(_["general_5"], show_alert=True)
    got = db.get(chat_id)
    if not got:
        return await CallbackQuery.answer(_["queue_2"], show_alert=True)
    if len(got) == 1:
        return await CallbackQuery.answer(_["queue_5"], show_alert=True)
    await CallbackQuery.answer()
    basic[videoid] = False
    buttons = queue_back_markup(_, what)
    med = InputMediaPhoto(
        media="https://telegra.ph//file/6f7d35131f69951c74ee5.jpg",
        caption=_["queue_1"],
    )
    await CallbackQuery.edit_message_media(media=med)
    j = 0
    msg = ""
    for x in got:
        j += 1
        if j == 1:
            msg += f'Streaming :\n\n✨ Title : {x["title"]}\nDuration : {x["dur"]}\nBy : {x["by"]}\n\n'
        elif j == 2:
            msg += f'Queued :\n\n✨ Title : {x["title"]}\nDuration : {x["dur"]}\nBy : {x["by"]}\n\n'
        else:
            msg += f'✨ Title : {x["title"]}\nDuration : {x["dur"]}\nBy : {x["by"]}\n\n'
    if "Queued" in msg:
        if len(msg) < 700:
            await asyncio.sleep(1)
            return await CallbackQuery.edit_message_text(msg, reply_markup=buttons)
        if "✨" in msg:
            msg = msg.replace("✨", "")
        link = await AnonyBin(msg)
        med = InputMediaPhoto(media=link, caption=_["queue_3"].format(link))
        await CallbackQuery.edit_message_media(media=med, reply_markup=buttons)
    else:
        await asyncio.sleep(1)
        return await CallbackQuery.edit_message_text(msg, reply_markup=buttons)


@app.on_callback_query(filters.regex("queue_back_timer") & ~BANNED_USERS)
@languageCB
async def queue_back(client, CallbackQuery: CallbackQuery, _):
    callback_data = CallbackQuery.data.strip()
    cplay = callback_data.split(None, 1)[1]
    try:
        chat_id, channel = await get_channeplayCB(_, cplay, CallbackQuery)
    except:
        return
    if not await is_active_chat(chat_id):
        return await CallbackQuery.answer(_["general_5"], show_alert=True)
    got = db.get(chat_id)
    if not got:
        return await CallbackQuery.answer(_["queue_2"], show_alert=True)
    await CallbackQuery.answer(_["set_cb_5"], show_alert=True)
    file = got[0]["file"]
    videoid = got[0]["vidid"]
    user = got[0]["by"]
    title = (got[0]["title"]).title()
    typo = (got[0]["streamtype"]).title()
    DUR = get_duration(got)
    if "live_" in file:
        IMAGE = get_image(videoid)
    elif "vid_" in file:
        IMAGE = get_image(videoid)
    elif "index_" in file:
        IMAGE = config.STREAM_IMG_URL
    else:
        if videoid == "telegram":
            IMAGE = (
                config.TELEGRAM_AUDIO_URL
                if typo == "Audio"
                else config.TELEGRAM_VIDEO_URL
            )
        elif videoid == "soundcloud":
            IMAGE = config.SOUNCLOUD_IMG_URL
        else:
            IMAGE = get_image(videoid)
    send = _["queue_6"] if DUR == "Unknown" else _["queue_7"]
    cap = _["queue_8"].format(app.mention, title, typo, user, send)
    upl = (
        queue_markup(_, DUR, cplay, videoid)
        if DUR == "Unknown"
        else queue_markup(
            _,
            DUR,
            cplay,
            videoid,
            seconds_to_min(got[0]["played"]),
            got[0]["dur"],
        )
    )
    basic[videoid] = True

    med = InputMediaPhoto(media=IMAGE, caption=cap)
    mystic = await CallbackQuery.edit_message_media(media=med, reply_markup=upl)
    if DUR != "Unknown":
        try:
            while db[chat_id][0]["vidid"] == videoid:
                await asyncio.sleep(5)
                if await is_active_chat(chat_id):
                    if basic[videoid]:
                        if await is_music_playing(chat_id):
                            try:
                                buttons = queue_markup(
                                    _,
                                    DUR,
                                    cplay,
                                    videoid,
                                    seconds_to_min(db[chat_id][0]["played"]),
                                    db[chat_id][0]["dur"],
                                )
                                await mystic.edit_reply_markup(reply_markup=buttons)
                            except FloodWait:
                                pass
                        else:
                            pass
                    else:
                        break
                else:
                    break
        except:
            return


# ─────────────────────────────────────────────────────────────────────────────
# Enhanced queue list — replaces plain text list with interactive buttons
# ─────────────────────────────────────────────────────────────────────────────

from AnonXMusic.utils.inline.queue import queue_list_markup
from config import autoclean


@app.on_callback_query(filters.regex("GetQueuedList") & ~BANNED_USERS)
@languageCB
async def queued_tracks_interactive(client, CallbackQuery: CallbackQuery, _):
    """Shows the full queue as inline buttons (skip-to / remove)."""
    callback_data = CallbackQuery.data.strip()
    callback_request = callback_data.split(None, 1)[1]
    what, videoid = callback_request.split("|")

    try:
        chat_id, channel = await get_channeplayCB(_, what, CallbackQuery)
    except:
        return

    if not await is_active_chat(chat_id):
        return await CallbackQuery.answer(_["general_5"], show_alert=True)

    got = db.get(chat_id)
    if not got:
        return await CallbackQuery.answer(_["queue_2"], show_alert=True)
    if len(got) == 1:
        return await CallbackQuery.answer(_["queue_5"], show_alert=True)

    await CallbackQuery.answer()
    basic[videoid] = False

    buttons = queue_list_markup(_, what, chat_id, got)
    cap = f"📋 **Queue** — {len(got)} track(s)\n\nTap a track to skip to it, or 🗑 to remove it."
    await CallbackQuery.edit_message_caption(caption=cap, reply_markup=buttons)


# ─────────────────────────────────────────────────────────────────────────────
# Skip to position N in queue
# ─────────────────────────────────────────────────────────────────────────────

@app.on_callback_query(filters.regex(r"^QSkipTo\s") & ~BANNED_USERS)
@languageCB
async def queue_skip_to(client, CallbackQuery: CallbackQuery, _):
    """Drops all tracks before position N and skips to it."""
    parts = CallbackQuery.data.strip().split(None, 1)[1].split("|")
    if len(parts) < 3:
        return await CallbackQuery.answer("Invalid data.", show_alert=True)

    what, chat_id_str, pos_str = parts[0], parts[1], parts[2]
    chat_id = int(chat_id_str)
    pos = int(pos_str)

    try:
        real_chat_id, channel = await get_channeplayCB(_, what, CallbackQuery)
    except:
        return

    if not await is_active_chat(real_chat_id):
        return await CallbackQuery.answer(_["general_5"], show_alert=True)

    got = db.get(real_chat_id)
    if not got or len(got) <= pos:
        return await CallbackQuery.answer("Track not found in queue.", show_alert=True)

    # Pop everything between index 0 (playing) and pos
    for _ in range(pos - 1):
        try:
            popped = got.pop(1)
            if popped:
                try:
                    autoclean.remove(popped["file"])
                except:
                    pass
        except:
            break

    await CallbackQuery.answer(f"⏭ Skipping to track #{pos}…", show_alert=False)
    # Trigger an actual skip using the existing skip mechanism
    from AnonXMusic.core.call import Anony as _Anony
    try:
        got2 = db.get(real_chat_id)
        if got2:
            popped = got2.pop(0)
            if popped:
                try:
                    autoclean.remove(popped["file"])
                except:
                    pass
        if not db.get(real_chat_id):
            await _Anony.stop_stream(real_chat_id)
            return await CallbackQuery.edit_message_caption(
                caption="Queue ended.", reply_markup=None
            )
        # Refresh the queue display
        got3 = db.get(real_chat_id)
        if got3:
            buttons = queue_list_markup(_, what, real_chat_id, got3)
            await CallbackQuery.edit_message_caption(
                caption=f"⏭ Skipped! Now at track **{got3[0]['title']}**\n\n"
                        f"📋 **Queue** — {len(got3)} track(s) remaining.",
                reply_markup=buttons,
            )
    except Exception as e:
        await CallbackQuery.answer(f"Error: {e}", show_alert=True)


# ─────────────────────────────────────────────────────────────────────────────
# Remove a specific track from queue
# ─────────────────────────────────────────────────────────────────────────────

@app.on_callback_query(filters.regex(r"^QRemove\s") & ~BANNED_USERS)
@languageCB
async def queue_remove_track(client, CallbackQuery: CallbackQuery, _):
    """Removes a specific track at position N from queue (cannot remove index 0)."""
    parts = CallbackQuery.data.strip().split(None, 1)[1].split("|")
    if len(parts) < 3:
        return await CallbackQuery.answer("Invalid data.", show_alert=True)

    what, chat_id_str, pos_str = parts[0], parts[1], parts[2]
    chat_id = int(chat_id_str)
    pos = int(pos_str)

    try:
        real_chat_id, channel = await get_channeplayCB(_, what, CallbackQuery)
    except:
        return

    if not await is_active_chat(real_chat_id):
        return await CallbackQuery.answer(_["general_5"], show_alert=True)

    got = db.get(real_chat_id)
    if not got or len(got) <= pos:
        return await CallbackQuery.answer("Track not found.", show_alert=True)
    if pos == 0:
        return await CallbackQuery.answer("Can't remove the currently playing track.", show_alert=True)

    removed = got.pop(pos)
    removed_title = (removed.get("title") or "Unknown")[:30]
    try:
        autoclean.remove(removed["file"])
    except:
        pass

    await CallbackQuery.answer(f"🗑 Removed: {removed_title}", show_alert=False)

    got2 = db.get(real_chat_id)
    if not got2:
        return await CallbackQuery.edit_message_caption(caption="Queue is now empty.", reply_markup=None)

    buttons = queue_list_markup(_, what, real_chat_id, got2)
    await CallbackQuery.edit_message_caption(
        caption=f"🗑 Removed **{removed_title}**\n\n"
                f"📋 **Queue** — {len(got2)} track(s) remaining.",
        reply_markup=buttons,
    )
