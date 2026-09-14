"""Пошаговый онбординг: одно сообщение, editMessageMedia."""

from __future__ import annotations

import logging

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup
from telegram.error import BadRequest

import db
from config import (
    BTN_BACK,
    BTN_NEXT,
    BTN_PLATFORM,
    BTN_REVIEWS,
    MENU_REVIEWS,
    PLATFORM_URL,
    REVIEWS_URL,
    STEPS,
)

log = logging.getLogger(__name__)


def progress_caption(index: int) -> str:
    step = STEPS[index]
    parts = [f"Шаг {index + 1} из {len(STEPS)}"]
    if step.get("title"):
        parts.append(step["title"])
    if step.get("text"):
        parts.append(step["text"])
    return "\n\n".join(parts)


def step_keyboard(index: int):
    last = index == len(STEPS) - 1
    row = []
    if index > 0:
        row.append(InlineKeyboardButton(BTN_BACK, callback_data="onb:prev"))
    if last:
        row.append(InlineKeyboardButton(BTN_PLATFORM, url=PLATFORM_URL))
    else:
        row.append(InlineKeyboardButton(BTN_NEXT, callback_data="onb:next"))
    rows = [row]
    if last:
        rows.append([InlineKeyboardButton(BTN_REVIEWS, url=REVIEWS_URL)])
    return InlineKeyboardMarkup(rows)


def main_menu_keyboard():
    return ReplyKeyboardMarkup([[MENU_REVIEWS]], resize_keyboard=True)


async def show_step(bot, chat_id: int, user_id: int, index: int, message_id: int | None):
    from media import edit_photo, send_photo

    index = max(0, min(index, len(STEPS) - 1))
    step = STEPS[index]
    caption = progress_caption(index)
    kb = step_keyboard(index)

    db.update_user(
        user_id,
        onboarding_started=1,
        onboarding_step=index,
        onboarding_chat_id=chat_id,
    )

    if message_id:
        try:
            await edit_photo(bot, chat_id, message_id, step["image"], caption, kb)
            db.update_user(user_id, onboarding_message_id=message_id)
            return message_id
        except BadRequest as e:
            if "not modified" in str(e).lower():
                return message_id
            log.error("edit onboarding failed: %s", e)
        except Exception as e:
            log.error("edit onboarding failed: %s", e)

    msg = await send_photo(bot, chat_id, step["image"], caption, kb)
    if msg:
        db.update_user(user_id, onboarding_message_id=msg.message_id)
        return msg.message_id
    return message_id


async def resume_or_start(bot, chat_id: int, user_id: int):
    row = db.get_user(user_id) or {}
    index = int(row.get("onboarding_step") or 0)
    await show_step(bot, chat_id, user_id, index, None)
    await bot.send_message(
        chat_id=chat_id,
        text="Навигация по платформе. Листай шаги кнопками ниже.",
        reply_markup=main_menu_keyboard(),
    )
