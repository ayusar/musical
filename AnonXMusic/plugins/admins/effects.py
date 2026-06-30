"""
Audio effects plugin — bass boost, nightcore, vaporwave, 3D audio.

Strategy: pre-process files in the background right after download,
so by the time the user calls /bassboost etc. the file is already ready.
No stutter, no realtime filter lag, works on low-CPU hosts like Render free.
"""

import asyncio
import os

from pyrogram import filters
from pyrogram.types import CallbackQuery, Message
from pytgcalls.types import AudioQuality, VideoQuality, MediaStream

from AnonXMusic import app, LOGGER
from AnonXMusic.core.call import Anony
from AnonXMusic.misc import SUDOERS, db
from AnonXMusic.utils import AdminRightsCheck
from AnonXMusic.utils.database import is_active_chat, is_nonadmin_chat
from AnonXMusic.utils.decorators.language import languageCB
from AnonXMusic.utils.formatters import check_duration, seconds_to_min
from AnonXMusic.utils.inline import close_markup
from config import BANNED_USERS, adminlist

# ──────────────────────────────────────────────────────────────────────────────
# Config
# ──────────────────────────────────────────────────────────────────────────────

EFFECTS_DIR = os.path.join(os.getcwd(), "effects_cache")

EFFECT_FILTERS = {
    "bassboost": "equalizer=f=60:width_type=h:width=50:g=15,equalizer=f=100:width_type=h:width=50:g=10",
    "nightcore": "asetrate=44100*1.25,aresample=44100,atempo=1.06",
    "vaporwave": "asetrate=44100*0.8,aresample=44100,atempo=0.9",
    "3d":        "apulsator=hz=0.08,extrastereo=m=2.5,aecho=0.8:0.88:60:0.4",
}

EFFECT_LABELS = {
    "bassboost": "🔊 Bass Boost",
    "nightcore": "🌸 Nightcore",
    "vaporwave": "🌊 Vaporwave",
    "3d":        "🎧 3D Audio",
}

# track which files are currently being processed so we don't double-process
_processing: set = set()


# ──────────────────────────────────────────────────────────────────────────────
# Pre-processor — call this right after a stream URL / file is known
# ──────────────────────────────────────────────────────────────────────────────

# ffmpeg flags that let it pull a remote (signed/expiring) HTTP(S) stream URL
# reliably instead of just bailing out on a hiccup.
_NETWORK_INPUT_FLAGS = (
    '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5 '
    '-rw_timeout 15000000'
)


def _is_remote(source: str) -> bool:
    return source.startswith("http://") or source.startswith("https://")


def _ffmpeg_cmd(source: str, af: str, out: str) -> str:
    pre = _NETWORK_INPUT_FLAGS + " " if _is_remote(source) else ""
    return f'ffmpeg {pre}-i "{source}" -af "{af}" -vn "{out}" -y'


async def preprocess_effects(vidid: str, source: str):
    """
    Kick off background ffmpeg jobs for all effects, keyed by video id.
    `source` can be a local downloaded file OR a remote stream URL — both work,
    since ffmpeg can read straight from an http(s) URL.
    Safe to call and forget — errors are logged and swallowed.
    """
    if not vidid or not source:
        return
    if not _is_remote(source) and not os.path.isfile(source):
        return

    async def _process(effect: str):
        out = _effect_path(vidid, effect)
        if os.path.isfile(out):
            return  # already cached
        key = f"{vidid}:{effect}"
        if key in _processing:
            return
        _processing.add(key)
        try:
            os.makedirs(EFFECTS_DIR, exist_ok=True)
            af = EFFECT_FILTERS[effect]
            proc = await asyncio.create_subprocess_shell(
                _ffmpeg_cmd(source, af, out),
                stdin=asyncio.subprocess.DEVNULL,
                stdout=asyncio.subprocess.DEVNULL,
                stderr=asyncio.subprocess.DEVNULL,
            )
            try:
                await asyncio.wait_for(proc.communicate(), timeout=120)
            except asyncio.TimeoutError:
                proc.kill()
                LOGGER(__name__).warning(f"Effect pre-process timed out [{effect}] for {vidid}")
        except Exception as e:
            LOGGER(__name__).warning(f"Effect pre-process failed [{effect}]: {e}")
        finally:
            _processing.discard(key)

    # run all 4 effects concurrently in background — don't await, fire and forget
    asyncio.gather(*[_process(fx) for fx in EFFECT_FILTERS], return_exceptions=True)


def _effect_path(vidid: str, effect: str) -> str:
    return os.path.join(EFFECTS_DIR, f"{effect}_{vidid}.mp3")


def is_effect_ready(vidid: str, effect: str) -> bool:
    return os.path.isfile(_effect_path(vidid, effect))


# ──────────────────────────────────────────────────────────────────────────────
# Core: swap current stream to an effect file
# ──────────────────────────────────────────────────────────────────────────────

async def stream_with_effect(chat_id: int, effect: str, playing: list):
    assistant = await Anony.group_assistant(Anony, chat_id)

    vidid = playing[0]["vidid"]
    out = _effect_path(vidid, effect)

    if not os.path.isfile(out):
        raise FileNotFoundError("Effect file not ready yet.")

    played   = playing[0]["played"]
    duration = playing[0]["dur"]
    streamtype = playing[0]["streamtype"]

    dur_secs = await asyncio.get_event_loop().run_in_executor(
        None, check_duration, out
    )
    new_duration = seconds_to_min(int(dur_secs))

    stream = (
        MediaStream(
            out,
            audio_parameters=AudioQuality.HIGH,
            video_parameters=VideoQuality.SD_480p,
            ffmpeg_parameters=f"-ss {played} -to {new_duration}",
        )
        if streamtype == "video"
        else MediaStream(
            out,
            audio_parameters=AudioQuality.HIGH,
            ffmpeg_parameters=f"-ss {played} -to {new_duration}",
            video_flags=MediaStream.Flags.IGNORE,
        )
    )

    await assistant.play(chat_id, stream)

    if not playing[0].get("original_file"):
        db[chat_id][0]["original_file"] = playing[0]["file"]
    db[chat_id][0]["file"]          = out
    db[chat_id][0]["dur"]           = new_duration
    db[chat_id][0]["seconds"]       = int(dur_secs)
    db[chat_id][0]["active_effect"] = effect


# ──────────────────────────────────────────────────────────────────────────────
# Shared toggle handler
# ──────────────────────────────────────────────────────────────────────────────

async def _toggle_effect(message: Message, chat_id: int, effect: str, _):
    playing = db.get(chat_id)
    if not playing:
        return await message.reply_text(_["queue_2"])

    original_file  = playing[0].get("original_file", playing[0]["file"])
    vidid          = playing[0]["vidid"]
    duration_secs  = int(playing[0].get("seconds", 0))

    if duration_secs == 0 or "live_" in original_file or "index_" in original_file:
        return await message.reply_text(
            "❌ Effects only work on downloaded tracks, not live streams."
        )

    if playing[0].get("active_effect") == effect:
        return await message.reply_text(
            f"{EFFECT_LABELS[effect]} is already active!\n"
            "Use /speed → 1.0x to restore normal audio.",
            reply_markup=close_markup(_),
        )

    label = EFFECT_LABELS[effect]

    # Check if pre-processed file is ready
    if not is_effect_ready(vidid, effect):
        key = f"{vidid}:{effect}"
        if key in _processing:
            # Still processing — wait for it
            wait_msg = await message.reply_text(
                f"⏳ {label} is being prepared, please wait…"
            )
            for _ in range(30):           # wait up to 30s
                await asyncio.sleep(1)
                if is_effect_ready(vidid, effect):
                    break
            else:
                await wait_msg.delete()
                return await message.reply_text(
                    "❌ Effect processing timed out. Try again in a moment."
                )
            await wait_msg.delete()
        else:
            # Not started yet — process now and wait
            wait_msg = await message.reply_text(f"⏳ Applying {label}…")
            os.makedirs(EFFECTS_DIR, exist_ok=True)
            af  = EFFECT_FILTERS[effect]
            out = _effect_path(vidid, effect)
            _processing.add(key)
            try:
                proc = await asyncio.create_subprocess_shell(
                    _ffmpeg_cmd(original_file, af, out),
                    stdin=asyncio.subprocess.DEVNULL,
                    stdout=asyncio.subprocess.DEVNULL,
                    stderr=asyncio.subprocess.DEVNULL,
                )
                try:
                    await asyncio.wait_for(proc.communicate(), timeout=60)
                except asyncio.TimeoutError:
                    proc.kill()
            finally:
                _processing.discard(key)
            await wait_msg.delete()
            if not os.path.isfile(out):
                return await message.reply_text(
                    "❌ Failed to apply effect. The source stream may be unreachable, try playing the song again."
                )

    try:
        await stream_with_effect(chat_id, effect, playing)
    except Exception as e:
        return await message.reply_text(f"❌ Error: {e}")

    await message.reply_text(
        f"✅ **{label}** applied!\nUse /speed → 1.0x to restore normal audio.",
        reply_markup=close_markup(_),
    )


# ──────────────────────────────────────────────────────────────────────────────
# Commands
# ──────────────────────────────────────────────────────────────────────────────

@app.on_message(
    filters.command(["bassboost", "bass", "cbassboost"]) & filters.group & ~BANNED_USERS
)
@AdminRightsCheck
async def bassboost_cmd(cli, message: Message, _, chat_id):
    await _toggle_effect(message, chat_id, "bassboost", _)


@app.on_message(
    filters.command(["nightcore", "nc", "cnightcore"]) & filters.group & ~BANNED_USERS
)
@AdminRightsCheck
async def nightcore_cmd(cli, message: Message, _, chat_id):
    await _toggle_effect(message, chat_id, "nightcore", _)


@app.on_message(
    filters.command(["vaporwave", "vapor", "cvaporwave"]) & filters.group & ~BANNED_USERS
)
@AdminRightsCheck
async def vaporwave_cmd(cli, message: Message, _, chat_id):
    await _toggle_effect(message, chat_id, "vaporwave", _)


@app.on_message(
    filters.command(["3d", "3daudio", "c3d"]) & filters.group & ~BANNED_USERS
)
@AdminRightsCheck
async def threed_cmd(cli, message: Message, _, chat_id):
    await _toggle_effect(message, chat_id, "3d", _)


# ──────────────────────────────────────────────────────────────────────────────
# Callback: inline effect buttons
# ──────────────────────────────────────────────────────────────────────────────

@app.on_callback_query(filters.regex(r"^ApplyEffect\s") & ~BANNED_USERS)
@languageCB
async def apply_effect_cb(client, CallbackQuery: CallbackQuery, _):
    parts = CallbackQuery.data.strip().split(None, 2)
    if len(parts) < 3:
        return await CallbackQuery.answer("Invalid data.", show_alert=True)

    chat_id = int(parts[1])
    effect  = parts[2]

    if not await is_active_chat(chat_id):
        return await CallbackQuery.answer(_["general_5"], show_alert=True)

    is_non_admin = await is_nonadmin_chat(CallbackQuery.message.chat.id)
    if not is_non_admin:
        if CallbackQuery.from_user.id not in SUDOERS:
            admins = adminlist.get(CallbackQuery.message.chat.id)
            if not admins or CallbackQuery.from_user.id not in admins:
                return await CallbackQuery.answer(_["admin_14"], show_alert=True)

    playing = db.get(chat_id)
    if not playing:
        return await CallbackQuery.answer(_["queue_2"], show_alert=True)

    label = EFFECT_LABELS.get(effect, effect)
    vidid = playing[0]["vidid"]

    if not is_effect_ready(vidid, effect):
        return await CallbackQuery.answer(
            f"⏳ {label} is still being prepared, try again in a moment.",
            show_alert=True,
        )

    await CallbackQuery.answer(f"Applying {label}…")
    try:
        await stream_with_effect(chat_id, effect, playing)
    except Exception as e:
        return await CallbackQuery.edit_message_text(
            f"❌ Failed: {e}", reply_markup=close_markup(_)
        )

    await CallbackQuery.edit_message_text(
        f"✅ **{label}** applied!", reply_markup=close_markup(_)
            )
