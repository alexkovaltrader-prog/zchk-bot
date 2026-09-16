"""Переключение воронки онбординга через FUNNEL_VERSION (v1 | v2)."""

from __future__ import annotations

import os

from . import v1_classic, v2_path

REGISTRY = {
    "v1": v1_classic,
    "v2": v2_path,
}


def default_version() -> str:
    raw = (os.getenv("FUNNEL_VERSION") or "v1").strip().lower()
    if raw in ("v2", "v2_path"):
        return "v2"
    return "v1"


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
