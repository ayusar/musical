"""
/lyrics — fetch lyrics for the current song or a search query.

Usage:
  /lyrics              → lyrics for currently playing song
  /lyrics song name    → search and fetch lyrics for that song

Sources (tried in order):
  1. lyrics.ovh  — free, no key needed
  2. AZLyrics    — scraped as fallback
"""

import asyncio
import html
import re

import aiohttp
from pyrogram import filters
from pyrogram.types import Message

from AnonXMusic import app
from AnonXMusic.misc import db
from AnonXMusic.utils.decorators.language import language
from config import BANNED_USERS

LYRICS_OVH  = "https://api.lyrics.ovh/v1/{artist}/{title}"
AZLYRICS_URL = "https://www.azlyrics.com/lyrics/{artist}/{title}.html"

MAX_MSG_LEN = 4000   # Telegram message cap with some headroom


# ──────────────────────────────────────────────────────────────────────────────
# Helpers
# ──────────────────────────────────────────────────────────────────────────────

def _clean(text: str) -> str:
    """Strip leading/trailing whitespace and normalize blank lines."""
    text = text.strip()
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text


def _split_lyrics(text: str, limit: int = MAX_MSG_LEN) -> list[str]:
    """Split long lyrics into telegram-sized chunks at verse boundaries."""
    if len(text) <= limit:
        return [text]
    parts, buf = [], ""
    for line in text.split("\n"):
        if len(buf) + len(line) + 1 > limit:
            parts.append(buf.strip())
            buf = ""
        buf += line + "\n"
    if buf.strip():
        parts.append(buf.strip())
    return parts


async def _fetch_lyricsovh(query: str) -> str | None:
    """
    lyrics.ovh accepts 'artist/title' — we split on ' - ' if present,
    otherwise treat the whole query as the title with artist 'unknown'.
    """
    if " - " in query:
        artist, title = query.split(" - ", 1)
    else:
        artist, title = query, query   # ovh is lenient with artist field

    url = LYRICS_OVH.format(
        artist=aiohttp.helpers.requote_uri(artist.strip()),
        title=aiohttp.helpers.requote_uri(title.strip()),
    )
    try:
        async with aiohttp.ClientSession() as s:
            async with s.get(url, timeout=aiohttp.ClientTimeout(total=8)) as r:
                if r.status != 200:
                    return None
                data = await r.json(content_type=None)
                return _clean(data.get("lyrics", "")) or None
    except Exception:
        return None


async def _fetch_azlyrics(query: str) -> str | None:
    """Scrape AZLyrics as fallback — strips artist/title from query."""
    if " - " in query:
        artist, title = query.split(" - ", 1)
    else:
        artist, title = "", query

    def _slug(s: str) -> str:
        return re.sub(r"[^a-z0-9]", "", s.lower())

    artist_slug = _slug(artist) if artist else "unknown"
    title_slug  = _slug(title)

    url = AZLYRICS_URL.format(artist=artist_slug, title=title_slug)
    headers = {"User-Agent": "Mozilla/5.0"}

    try:
        async with aiohttp.ClientSession(headers=headers) as s:
            async with s.get(url, timeout=aiohttp.ClientTimeout(total=10)) as r:
                if r.status != 200:
                    return None
                body = await r.text()

        # AZLyrics puts lyrics between two comment markers
        match = re.search(
            r"<!-- Usage of azlyrics.*?-->(.*?)<!-- MxM banner -->",
            body,
            re.DOTALL,
        )
        if not match:
            return None

        raw = match.group(1)
        # Strip HTML tags
        raw = re.sub(r"<br\s*/?>", "\n", raw, flags=re.IGNORECASE)
        raw = re.sub(r"<[^>]+>", "", raw)
        raw = html.unescape(raw)
        return _clean(raw) or None
    except Exception:
        return None


async def _get_lyrics(query: str) -> tuple[str | None, str]:
    """Try sources in order; return (lyrics_text, source_label)."""
    result = await _fetch_lyricsovh(query)
    if result:
        return result, "lyrics.ovh"
    result = await _fetch_azlyrics(query)
    if result:
        return result, "AZLyrics"
    return None, ""


def _now_playing_title(chat_id: int) -> str | None:
    """Return 'Artist - Title' or just 'Title' for the current track."""
    playing = db.get(chat_id)
    if not playing:
        return None
    return playing[0].get("title")


# ──────────────────────────────────────────────────────────────────────────────
# Command handler
# ──────────────────────────────────────────────────────────────────────────────

@app.on_message(
    filters.command(["lyrics", "lyric", "ly"]) & ~BANNED_USERS
)
@language
async def lyrics_cmd(client, message: Message, _):
    query = None

    # Check if user provided a song name after the command
    if len(message.command) > 1:
        query = " ".join(message.command[1:]).strip()
    else:
        # Use currently playing track
        query = _now_playing_title(message.chat.id)
        if not query:
            return await message.reply_text(
                "❌ Nothing is playing right now.\n"
                "Use `/lyrics song name` to search for lyrics."
            )

    searching = await message.reply_text(f"🔍 Searching lyrics for **{query}**…")

    lyrics, source = await _get_lyrics(query)

    if not lyrics:
        return await searching.edit_text(
            f"😕 Couldn't find lyrics for **{query}**.\n\n"
            "Try using the format: `/lyrics Artist - Song Title`"
        )

    await searching.delete()

    parts = _split_lyrics(lyrics)
    header = f"🎵 **{query}**\n`via {source}`\n\n"

    # Send first part with header
    first = header + parts[0]
    sent = await message.reply_text(first)

    # Send remaining parts if lyrics are long
    for part in parts[1:]:
        await asyncio.sleep(0.5)
        await message.reply_text(part)
