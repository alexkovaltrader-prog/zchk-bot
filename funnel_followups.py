"""Ветки A–D после воронки «Путь». Та же job_queue, что и пуши гейта."""

from __future__ import annotations

import asyncio
import logging
import os
from datetime import datetime, timezone
from zoneinfo import ZoneInfo

import httpx
from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from telegram.error import Forbidden

import db
from config import (
    CFT_URL,
    FULL_ACCESS_URL,
    MANAGER_CONTACT_URL,
    MANAGER_URL,
    PLAN_FULL,
    PLAN_QUICK,
    PLATFORM_URL,
    PUSH_HOUR_END_MSK,
    PUSH_HOUR_START_MSK,
    PUSH_MAX_PER_SEC,
    QUICK_START_URL,
    REVIEWS_URL,
)

log = logging.getLogger(__name__)
MSK = ZoneInfo("Europe/Moscow")

SUPABASE_URL = os.getenv("SUPABASE_URL", "")
SUPABASE_SERVICE_KEY = os.getenv("SUPABASE_SERVICE_KEY", "")

BRANCH_A = "A"
BRANCH_B = "B"
BRANCH_C = "C"
BRANCH_D = "D"
D_BRANCH_STEP_IDS = frozenset({"s3_two_paths", "s6a_capital", "s6b_props"})


def in_send_window(now: datetime | None = None) -> bool:
    now = now or datetime.now(MSK)
    return PUSH_HOUR_START_MSK <= now.hour < PUSH_HOUR_END_MSK


def _hours(value: str | None) -> float:
    return db.hours_since_iso(value) or 0.0


# book = Быстрый старт $59. book_video / video / extended = полный доступ.
# trial / pending / пусто = покупки нет.


def classify_plan(plan) -> str | None:
    if plan is None:
        return None
    value = str(plan).strip().lower()
    if not value:
        return None
    if value in PLAN_QUICK:
        return "quick"
    if value in PLAN_FULL:
        return "full"
    return None


async def fetch_purchase_kind(telegram_id: int) -> str | None:
    if not SUPABASE_URL or not SUPABASE_SERVICE_KEY:
        return None
    headers = {
        "apikey": SUPABASE_SERVICE_KEY,
        "Authorization": f"Bearer {SUPABASE_SERVICE_KEY}",
    }
    url = f"{SUPABASE_URL.rstrip('/')}/rest/v1/profiles"
    lookups = [
        {"telegram": f"eq.{telegram_id}", "select": "plan"},
        {"telegram_id": f"eq.{telegram_id}", "select": "plan"},
    ]
    try:
        async with httpx.AsyncClient(timeout=8) as client:
            for params in lookups:
                resp = await client.get(url, headers=headers, params=params)
                if resp.status_code >= 300:
                    log.warning("profiles plan lookup %s -> %s %s", params, resp.status_code, resp.text[:200])
                    continue
                rows = resp.json()
                if not isinstance(rows, list) or not rows:
                    continue
                kinds = {classify_plan(row.get("plan")) for row in rows}
                kinds.discard(None)
                if len(kinds) == 1:
                    return kinds.pop()
                if len(kinds) > 1:
                    log.warning("profiles plan conflict user=%s values=%s", telegram_id, kinds)
                    return None
                return None
    except Exception as e:
        log.error("fetch_purchase_kind user=%s: %s", telegram_id, e)
    return None


def next_touch(branch: str, sent: set[int], hours: float) -> int | None:
    schedule = {
        BRANCH_A: [(0, 0), (3, 72), (7, 168), (14, 336)],
        BRANCH_B: [(0, 0), (14, 336), (21, 504)],
        BRANCH_C: [(1, 24), (3, 72), (7, 168)],
        BRANCH_D: [(1, 24)],
    }
    for touch, delay in schedule.get(branch, []):
        if touch in sent:
            continue
        if hours + 1e-6 >= delay:
            return touch
        return None
    return None


def _url_kb(label: str, url: str):
    return InlineKeyboardMarkup([[InlineKeyboardButton(label, url=url)]])


def _rows_kb(rows: list) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(rows)


OBJECTION_REPLIES: dict[str, tuple[str, InlineKeyboardMarkup | None]] = {
    "price": (
        "Если полный доступ сейчас тяжело, начни с Быстрого старта за $59. Там база, без неё дальше смысла нет.",
        _url_kb("Быстрый старт, $59", QUICK_START_URL),
    ),
    "doubt": (
        "Это нормально. Посмотри, что пишут те, кто уже внутри, или задай вопрос менеджеру напрямую.",
        _rows_kb(
            [
                [InlineKeyboardButton("Читать отзывы", url=REVIEWS_URL)],
                [InlineKeyboardButton("Написать менеджеру", url=MANAGER_CONTACT_URL)],
            ]
        ),
    ),
    "later": (
        "Ок. Когда будешь готов, вход на том же месте.",
        None,
    ),
}


def objection_reply(key: str) -> tuple[str, InlineKeyboardMarkup | None]:
    return OBJECTION_REPLIES.get(key) or ("Ок, записал.", None)


def _current_step_id(user: dict) -> str:
    from funnels.v2_path import STEPS

    index = int(user.get("onboarding_step") or 0)
    if not STEPS:
        return ""
    index = max(0, min(index, len(STEPS) - 1))
    return STEPS[index].get("id") or ""


def message_for(branch: str, touch: int, user: dict) -> tuple[str, InlineKeyboardMarkup | None]:
    step_id = _current_step_id(user)
    if branch == BRANCH_A:
        if touch == 0:
            return (
                "Доступ открыт. Начни с первого модуля, он занимает около часа.",
                _url_kb("Открыть платформу", PLATFORM_URL),
            )
        if touch == 3:
            return (
                "Как идёт разметка? Кидай скрин графика, посмотрю.",
                _url_kb("Написать", MANAGER_URL),
            )
        if touch == 7:
            return (
                "Базу ты прошёл. Дальше идут остальные 17 лекций Академии и калькулятор рисков под CFT. Без них система не собирается целиком.",
                _url_kb("Полный доступ", FULL_ACCESS_URL),
            )
        return (
            "Многие берут быстрый старт, проходят базу и добирают полный доступ, когда упираются в потолок материала. Открыть можно прямо из личного кабинета.",
            _url_kb("Полный доступ", FULL_ACCESS_URL),
        )
    if branch == BRANCH_B:
        if touch == 0:
            return (
                "Ты внутри. План на первые две недели: разметка, гипотезы, риск. Иди по порядку, не перескакивай.",
                _url_kb("Открыть платформу", PLATFORM_URL),
            )
        if touch == 14:
            return (
                "База пройдена, можно брать челлендж. Помни: первый это тренировка.",
                _url_kb("Забрать условия CFT", CFT_URL),
            )
        return (
            "Как челлендж? Напиши, где ты сейчас: в плюсе, в минусе или слил. Разберём.",
            _url_kb("Написать статус", MANAGER_URL),
        )
    if branch == BRANCH_C:
        if touch == 1:
            kb = InlineKeyboardMarkup(
                [
                    [
                        InlineKeyboardButton("цена", callback_data="funnel:obj:price"),
                        InlineKeyboardButton("сомнения", callback_data="funnel:obj:doubt"),
                        InlineKeyboardButton("не сейчас", callback_data="funnel:obj:later"),
                    ]
                ]
            )
            return (
                "Ты дошёл до конца, но так и не выбрал. Что остановило?",
                kb,
            )
        if touch == 3:
            obj = (user.get("funnel_objection") or "").strip()
            if obj:
                return objection_reply(obj)
            return (
                "Если коротко, вход два: полный доступ или база за $59.",
                _rows_kb(
                    [
                        [InlineKeyboardButton("Полный доступ", url=FULL_ACCESS_URL)],
                        [InlineKeyboardButton("Быстрый старт, $59", url=QUICK_START_URL)],
                    ]
                ),
            )
        return (
            "Последнее сообщение, дальше не пишу. Отзывы тех, кто уже внутри.",
            _url_kb("Читать отзывы", REVIEWS_URL),
        )
    if step_id == "s3_two_paths":
        return (
            "Не решил, что выбрать? Напиши, подскажу, что подойдёт под твою ситуацию.",
            _rows_kb(
                [
                    [InlineKeyboardButton("Написать", url=MANAGER_URL)],
                    [InlineKeyboardButton("Продолжить", callback_data="onb:resume")],
                ]
            ),
        )
    if step_id in {"s6a_capital", "s6b_props"}:
        return (
            "Ты остановился на челлендже. Вопрос в деньгах или в готовности?",
            InlineKeyboardMarkup(
                [[InlineKeyboardButton("Продолжить с этого места", callback_data="onb:resume")]]
            ),
        )
    return (
        "Продолжим с того же места.",
        InlineKeyboardMarkup(
            [[InlineKeyboardButton("Продолжить", callback_data="onb:resume")]]
        ),
    )


async def send_followup(bot, user: dict, branch: str, touch: int) -> bool:
    uid = user["telegram_id"]
    if branch == BRANCH_C and touch == 3 and (user.get("funnel_objection") or "").strip():
        db.log_funnel_followup(uid, branch, touch)
        db.update_user(uid, funnel_branch=branch)
        log.info("funnel followup skip C_72 already answered user=%s", uid)
        return True
    text, kb = message_for(branch, touch, user)
    try:
        await bot.send_message(chat_id=uid, text=text, reply_markup=kb)
    except Forbidden:
        db.mark_blocked(uid)
        return False
    db.log_funnel_followup(uid, branch, touch)
    fields = {"funnel_branch": branch}
    last_by_branch = {BRANCH_A: 14, BRANCH_B: 21, BRANCH_C: 7, BRANCH_D: 1}
    if touch == last_by_branch[branch]:
        fields["funnel_followup_done"] = 1
    db.update_user(uid, **fields)
    log.info("funnel followup user=%s branch=%s touch=%s", uid, branch, touch)
    return True


async def resolve_branch(user: dict) -> tuple[str | None, dict]:
    uid = user["telegram_id"]
    kind = await fetch_purchase_kind(uid)
    fields = {}
    if kind and kind != (user.get("purchase_kind") or ""):
        fields["purchase_kind"] = kind
        user = {**user, **fields}
    if kind == "quick":
        fields["funnel_branch"] = BRANCH_A
        if fields:
            db.update_user(uid, **fields)
        return BRANCH_A, {**user, **fields}
    if kind == "full":
        fields["funnel_branch"] = BRANCH_B
        if fields:
            db.update_user(uid, **fields)
        return BRANCH_B, {**user, **fields}
    hours = _hours(user.get("last_step_at"))
    if hours < 24:
        if fields:
            db.update_user(uid, **fields)
        return None, user
    if int(user.get("onboarding_completed") or 0):
        fields["funnel_branch"] = BRANCH_C
        if fields:
            db.update_user(uid, **fields)
        return BRANCH_C, {**user, **fields}
    fields["funnel_branch"] = BRANCH_D
    if fields:
        db.update_user(uid, **fields)
    return BRANCH_D, {**user, **fields}


def hours_for_branch(branch: str, user: dict) -> float:
    if branch in (BRANCH_A, BRANCH_B):
        return _hours(user.get("last_step_at"))
    return _hours(user.get("last_step_at"))


async def run_funnel_followup_job(context):
    if not in_send_window():
        log.info("funnel followup skip: outside MSK window")
        return
    delay = 1.0 / PUSH_MAX_PER_SEC
    sent = 0
    for user in db.due_funnel_followup_users():
        try:
            branch, user = await resolve_branch(user)
            if not branch:
                continue
            sent_touches = db.followup_touches(user["telegram_id"], branch)
            touch = next_touch(branch, sent_touches, hours_for_branch(branch, user))
            if touch is None:
                continue
            if await send_followup(context.bot, user, branch, touch):
                sent += 1
        except Forbidden:
            db.mark_blocked(user["telegram_id"])
        except Exception as e:
            log.error("funnel followup user=%s failed: %s", user.get("telegram_id"), e)
        await asyncio.sleep(delay)
    log.info("funnel followup done sent=%s metrics=%s", sent, db.funnel_metrics())
