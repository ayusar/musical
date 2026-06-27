from typing import Union

from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup


def queue_markup(
    _,
    DURATION,
    CPLAY,
    videoid,
    played: Union[bool, int] = None,
    dur: Union[bool, int] = None,
):
    not_dur = [
        [
            InlineKeyboardButton(
                text=_["QU_B_1"],
                callback_data=f"GetQueued {CPLAY}|{videoid}",
            ),
            InlineKeyboardButton(
                text="📋 Manage Queue",
                callback_data=f"GetQueuedList {CPLAY}|{videoid}",
            ),
        ],
        [
            InlineKeyboardButton(
                text=_["CLOSE_BUTTON"],
                callback_data="close",
            ),
        ],
    ]
    dur = [
        [
            InlineKeyboardButton(
                text=_["QU_B_2"].format(played, dur),
                callback_data="GetTimer",
            )
        ],
        [
            InlineKeyboardButton(
                text=_["QU_B_1"],
                callback_data=f"GetQueued {CPLAY}|{videoid}",
            ),
            InlineKeyboardButton(
                text="📋 Manage Queue",
                callback_data=f"GetQueuedList {CPLAY}|{videoid}",
            ),
        ],
        [
            InlineKeyboardButton(
                text=_["CLOSE_BUTTON"],
                callback_data="close",
            ),
        ],
    ]
    upl = InlineKeyboardMarkup(not_dur if DURATION == "Unknown" else dur)
    return upl


def queue_back_markup(_, CPLAY):
    upl = InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton(
                    text=_["BACK_BUTTON"],
                    callback_data=f"queue_back_timer {CPLAY}",
                ),
                InlineKeyboardButton(
                    text=_["CLOSE_BUTTON"],
                    callback_data="close",
                ),
            ]
        ]
    )
    return upl


def aq_markup(_, chat_id):
    buttons = [
        [
            InlineKeyboardButton(text="▷", callback_data=f"ADMIN Resume|{chat_id}"),
            InlineKeyboardButton(text="II", callback_data=f"ADMIN Pause|{chat_id}"),
            InlineKeyboardButton(text="‣‣I", callback_data=f"ADMIN Skip|{chat_id}"),
            InlineKeyboardButton(text="▢", callback_data=f"ADMIN Stop|{chat_id}"),
        ],
    ]
    return buttons


# ─────────────────────────────────────────────────────────────────────────────
# Enhanced queue list markup — skip-to-position + remove buttons per track
# ─────────────────────────────────────────────────────────────────────────────

def queue_list_markup(_, CPLAY, chat_id, queue: list):
    """
    Renders one row per queued track (index 1+) with:
      [▶ Skip to #N  title…]  [🗑 Remove]
    Plus a Back button at the bottom.

    queue  — the full db list for the chat (index 0 = currently playing).
    """
    rows = []

    for i, track in enumerate(queue):
        title = (track.get("title") or "Unknown")[:20]
        if i == 0:
            # Currently playing — show as such, no skip/remove
            rows.append(
                [
                    InlineKeyboardButton(
                        text=f"🎵 {title}…  (playing)",
                        callback_data="GetTimer",
                    )
                ]
            )
        else:
            rows.append(
                [
                    InlineKeyboardButton(
                        text=f"▶ #{i}  {title}…",
                        callback_data=f"QSkipTo {CPLAY}|{chat_id}|{i}",
                    ),
                    InlineKeyboardButton(
                        text="🗑",
                        callback_data=f"QRemove {CPLAY}|{chat_id}|{i}",
                    ),
                ]
            )

    rows.append(
        [
            InlineKeyboardButton(
                text=_["BACK_BUTTON"],
                callback_data=f"queue_back_timer {CPLAY}",
            ),
            InlineKeyboardButton(
                text=_["CLOSE_BUTTON"],
                callback_data="close",
            ),
        ]
    )
    return InlineKeyboardMarkup(rows)
