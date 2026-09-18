"""Переключение воронки онбординга через FUNNEL_VERSION (v1 | v2)."""

from __future__ import annotations

import os

from . import v1_classic, v2_path

REGISTRY = {
    "v1": v1_classic,
    "v2": v2_path,
}


def default_version() -> str:
    raw = (os.getenv("FUNNEL_VERSION") or "v2").strip().lower()
    if raw in ("v1", "v1_classic"):
        return "v1"
    return "v2"


def get_funnel(version: str | None):
    key = (version or "").strip().lower()
    if key in ("v2", "v2_path"):
        return REGISTRY["v2"]
    return REGISTRY["v1"]


def lock_funnel_version(telegram_id: int) -> str:
    """Фиксирует версию при первом входе в онбординг. Дальше не меняется."""
    import db

    db.init_db()
    db.upsert_on_start(telegram_id, "direct")
    row = db.get_user(telegram_id) or {}
    existing = (row.get("funnel_version") or "").strip()
    if existing in REGISTRY:
        return existing
    if row.get("onboarding_started"):
        version = "v1"
    else:
        version = default_version()
    db.update_user(telegram_id, funnel_version=version)
    return version


def funnel_for_user(telegram_id: int):
    return get_funnel(lock_funnel_version(telegram_id))


CAPTION_LIMIT = 1024


def log_funnel_runtime_config():
    import logging

    from config import PROP_VIDEO_ENABLED, SCREEN_S5_TWO_WEEKS_ENABLED, WORK_ACCOUNT_URL
    from funnels.v2_path import STEPS

    log = logging.getLogger(__name__)
    log.info(
        "funnel config FUNNEL_VERSION=%s PROP_VIDEO_ENABLED=%s WORK_ACCOUNT_URL=%s SCREEN_S5_TWO_WEEKS_ENABLED=%s steps=%s",
        default_version(),
        PROP_VIDEO_ENABLED,
        "set" if (WORK_ACCOUNT_URL or "").strip() else "empty",
        SCREEN_S5_TWO_WEEKS_ENABLED,
        len(STEPS),
    )


def log_caption_lengths():
    import logging

    log = logging.getLogger(__name__)
    version = default_version()
    funnel = get_funnel(version)
    log.info("caption check funnel=%s steps=%s", version, len(funnel.STEPS))
    for index, step in enumerate(funnel.STEPS):
        n = len(funnel.caption(index))
        log.info("caption step %s = %s chars", step.get("id"), n)
        if n > CAPTION_LIMIT:
            log.warning("caption too long: step %s = %s chars (limit %s)", step.get("id"), n, CAPTION_LIMIT)


def log_referenced_screen_keys():
    import logging

    from funnel_followups import D_BRANCH_STEP_IDS
    from funnels.v2_path import ALL_STEPS

    log = logging.getLogger(__name__)
    known = {step["id"] for step in ALL_STEPS}
    missing = sorted(key for key in D_BRANCH_STEP_IDS if key not in known)
    extra_old = sorted({"s6_capital"} - known)
    log.info("v2 screen keys: %s", sorted(known))
    if missing:
        log.warning("followup screen_key missing in v2_path: %s", missing)
    else:
        log.info("followup screen keys ok: %s", sorted(D_BRANCH_STEP_IDS))
    if extra_old:
        log.info("legacy keys not in STEPS (expected after split): %s", extra_old)
