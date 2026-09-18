"""Догоняющие пуши для непрошедших гейт. Джоба раз в час."""

from __future__ import annotations

import asyncio
import logging
from datetime import datetime, timezone
from zoneinfo import ZoneInfo

from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from telegram.error import Forbidden

import db
from config import (
    BTN_CHECK,
    BTN_REVIEWS,
    BTN_SUBSCRIBE,
    CHANNEL_URL,
    PUSH_HOUR_END_MSK,
    PUSH_HOUR_START_MSK,
    PUSH_MAX_PER_SEC,
    PUSHES,
    REVIEWS_URL,
)
from gate import is_channel_member

log = logging.getLogger(__name__)
MSK = ZoneInfo("Europe/Moscow")


def in_send_window(now: datetime | None = None) -> bool:
    now = now or datetime.now(MSK)
    return PUSH_HOUR_START_MSK <= now.hour < PUSH_HOUR_END_MSK


def hours_since(first_start_at: str) -> float:
    started = datetime.fromisoformat(first_start_at)
    if started.tzinfo is None:
        started = started.replace(tzinfo=timezone.utc)
    return (datetime.now(timezone.utc) - started.astimezone(timezone.utc)).total_seconds() / 3600


def push_keyboard(touch_cfg: dict):
    rows = []
    if touch_cfg.get("show_reviews"):
        rows.append([InlineKeyboardButton(BTN_REVIEWS, url=REVIEWS_URL)])
    rows.append(
        [
            InlineKeyboardButton(BTN_SUBSCRIBE, url=CHANNEL_URL),
            InlineKeyboardButton(BTN_CHECK, callback_data="check_sub"),
        ]
    )
    return InlineKeyboardMarkup(rows)


def next_due_touch(user: dict) -> dict | None:
    last = int(user.get("push_touch") or 0)
    elapsed = hours_since(user["first_start_at"])
    for cfg in PUSHES:
        if cfg["touch"] <= last:
            continue
        if elapsed + 1e-6 >= cfg["delay_hours"]:
            return cfg
        return None
    return None


async def send_touch(bot, user: dict, cfg: dict) -> bool:
    from media import send_photo

    uid = user["telegram_id"]
    member = await is_channel_member(bot, uid)
    if member is True:
        db.mark_subscribed(uid)
        db.update_user(uid, push_sequence_done=1)
        db.log_push(uid, cfg["touch"], "subscribed_before_send")
        log.info("push skip subscribed user=%s touch=%s", uid, cfg["touch"])
        return False
    try:
        await send_photo(
            bot,
            uid,
            cfg["image"],
            cfg["text"],
            push_keyboard(cfg),
        )
    except Forbidden:
        db.mark_blocked(uid)
        db.log_push(uid, cfg["touch"], "blocked")
        log.info("push blocked user=%s", uid)
        return False

    fields = {"push_touch": cfg["touch"]}
    if cfg["touch"] == 3:
        fields["push_sequence_done"] = 1
    db.update_user(uid, **fields)
    db.log_push(uid, cfg["touch"], "sent")
    log.info("push sent user=%s touch=%s", uid, cfg["touch"])
    return True


async def run_push_job(context):
    if not in_send_window():
        log.info("push job skip: outside MSK window")
        return

    bot = context.bot
    delay = 1.0 / PUSH_MAX_PER_SEC
    sent = 0
    for user in db.due_push_users():
        cfg = next_due_touch(user)
        if not cfg:
            continue
        try:
            if await send_touch(bot, user, cfg):
                sent += 1
        except Forbidden:
            db.mark_blocked(user["telegram_id"])
        except Exception as e:
            log.error("push user=%s failed: %s", user["telegram_id"], e)
        await asyncio.sleep(delay)

    stats = db.push_stats()
    log.info("push job done sent=%s stats=%s", sent, stats)
