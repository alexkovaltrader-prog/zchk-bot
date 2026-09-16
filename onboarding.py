"""Пошаговый онбординг: одно сообщение, воронка берётся из funnels.*."""

from __future__ import annotations

import logging

from telegram.error import BadRequest

import db
import funnels

log = logging.getLogger(__name__)


def _funnel_for(user_id: int):
    return funnels.funnel_for_user(user_id)


async def show_step(bot, chat_id: int, user_id: int, index: int, message_id: int | None):
    from media import edit_photo, send_photo

    funnel = _funnel_for(user_id)
    steps = funnel.STEPS
    index = max(0, min(index, len(steps) - 1))
    step = steps[index]
    caption = funnel.caption(index)
    kb = funnel.keyboard(index)

    last = index == len(steps) - 1
    row = db.get_user(user_id) or {}
    completed = 1 if last else int(row.get("onboarding_completed") or 0)
    db.update_user(
        user_id,
        onboarding_started=1,
        onboarding_step=index,
        onboarding_chat_id=chat_id,
        last_step_at=db._now(),
        onboarding_completed=completed,
    )
    db.log_funnel_event(
        user_id,
        "step_view",
        step_id=step.get("id"),
        step_index=index,
    )
    layout = step.get("layout") or "nav"
    shown = {"prop": ["cft"], "result": ["reviews"], "future": ["register", "full", "quick", "manager"]}
    for button_id in shown.get(layout, []):
        db.log_funnel_event(
            user_id,
            "link_impression",
            step_id=step.get("id"),
            step_index=index,
            button_id=button_id,
        )

    if message_id:
        try:
            await edit_photo(bot, chat_id, message_id, step["image"], caption, kb)
            db.update_user(user_id, onboarding_message_id=message_id)
            return message_id
        except BadRequest as e:
            if "not modified" in str(e).lower():
                return message_id
            log.error("edit onboarding failed, fallback delete+send: %s", e)
        except Exception as e:
            log.error("edit onboarding failed, fallback delete+send: %s", e)
        try:
            await bot.delete_message(chat_id=chat_id, message_id=message_id)
        except Exception as e:
            log.error("delete onboarding failed: %s", e)

    msg = await send_photo(bot, chat_id, step["image"], caption, kb)
    if msg:
        db.update_user(user_id, onboarding_message_id=msg.message_id)
        return msg.message_id
    return message_id


async def resume_or_start(bot, chat_id: int, user_id: int):
    funnels.lock_funnel_version(user_id)
    row = db.get_user(user_id) or {}
    index = int(row.get("onboarding_step") or 0)
    message_id = row.get("onboarding_message_id")
    await show_step(bot, chat_id, user_id, index, message_id)
