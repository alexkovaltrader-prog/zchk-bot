"""Гейт подписки на @ZAICHIKFx."""

from __future__ import annotations

import asyncio
import logging
import time

from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from telegram.error import Forbidden, TelegramError

import db
from config import (
    BTN_CHECK,
    BTN_SUBSCRIBE,
    CHANNEL_URL,
    CHANNEL_USERNAME,
    CHECK_SUB_COOLDOWN_SEC,
    GATE_ALERT_NOT_SUB,
    GATE_IMAGE,
    GATE_TEXT,
)

log = logging.getLogger(__name__)

SUBSCRIBED_STATUSES = {"creator", "administrator", "member"}


def gate_keyboard():
    return InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton(BTN_SUBSCRIBE, url=CHANNEL_URL),
                InlineKeyboardButton(BTN_CHECK, callback_data="check_sub"),
            ]
        ]
    )


async def send_gate(bot, chat_id: int):
    from media import send_photo

    return await send_photo(bot, chat_id, GATE_IMAGE, GATE_TEXT, gate_keyboard())


async def is_channel_member(bot, user_id: int) -> bool | None:
    """True / False / None (ошибка прав или API — пропускаем дальше)."""
    try:
        member = await asyncio.wait_for(
            bot.get_chat_member(CHANNEL_USERNAME, user_id),
            timeout=8,
        )
        status = getattr(member, "status", None)
        if hasattr(status, "value"):
            status = status.value
        status = str(status or "")
        return status in SUBSCRIBED_STATUSES
    except asyncio.TimeoutError:
        log.error("getChatMember timeout user=%s", user_id)
        return None
    except Forbidden as e:
        log.error("getChatMember forbidden (bot not admin?): %s", e)
        return None
    except TelegramError as e:
        log.error("getChatMember telegram error: %s", e)
        return None
    except Exception as e:
        log.error("getChatMember failed: %s", e)
        return None


def check_cooldown_ok(user_row: dict) -> bool:
    last = float(user_row.get("last_sub_check_at") or 0)
    return (time.time() - last) >= CHECK_SUB_COOLDOWN_SEC
