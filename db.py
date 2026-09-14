"""Локальная SQLite для гейта, онбординга и пушей."""

from __future__ import annotations

import sqlite3
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path

DB_PATH = Path(__file__).resolve().parent / "data" / "bot.db"


def _now() -> str:
    return datetime.now(timezone.utc).replace(tzinfo=None).isoformat(timespec="seconds")


@contextmanager
def connect():
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()


def init_db():
    with connect() as conn:
        conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS bot_users (
                telegram_id INTEGER PRIMARY KEY,
                source TEXT DEFAULT 'direct',
                subscribed INTEGER NOT NULL DEFAULT 0,
                gate_passed INTEGER NOT NULL DEFAULT 0,
                onboarding_started INTEGER NOT NULL DEFAULT 0,
                onboarding_step INTEGER NOT NULL DEFAULT 0,
                onboarding_chat_id INTEGER,
                onboarding_message_id INTEGER,
                first_start_at TEXT NOT NULL,
                last_sub_check_at REAL DEFAULT 0,
                push_touch INTEGER NOT NULL DEFAULT 0,
                push_sequence_done INTEGER NOT NULL DEFAULT 0,
                blocked INTEGER NOT NULL DEFAULT 0,
                created_at TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS media_cache (
                cache_key TEXT PRIMARY KEY,
                file_id TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS push_events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                telegram_id INTEGER NOT NULL,
                touch INTEGER NOT NULL,
                event TEXT NOT NULL,
                created_at TEXT NOT NULL
            );
            """
        )


def upsert_on_start(telegram_id: int, source: str) -> dict:
    init_db()
    now = _now()
    source = source or "direct"
    with connect() as conn:
        row = conn.execute(
            "SELECT * FROM bot_users WHERE telegram_id = ?", (telegram_id,)
        ).fetchone()
        if row is None:
            conn.execute(
                """
                INSERT INTO bot_users (telegram_id, source, first_start_at, created_at)
                VALUES (?, ?, ?, ?)
                """,
                (telegram_id, source, now, now),
            )
        elif source != "direct":
            conn.execute(
                "UPDATE bot_users SET source = ? WHERE telegram_id = ?",
                (source, telegram_id),
            )
        return dict(
            conn.execute(
                "SELECT * FROM bot_users WHERE telegram_id = ?", (telegram_id,)
            ).fetchone()
        )


def get_user(telegram_id: int) -> dict | None:
    init_db()
    with connect() as conn:
        row = conn.execute(
            "SELECT * FROM bot_users WHERE telegram_id = ?", (telegram_id,)
        ).fetchone()
        return dict(row) if row else None


def update_user(telegram_id: int, **fields):
    if not fields:
        return
    keys = ", ".join(f"{k} = ?" for k in fields)
    values = list(fields.values()) + [telegram_id]
    with connect() as conn:
        conn.execute(f"UPDATE bot_users SET {keys} WHERE telegram_id = ?", values)


def mark_subscribed(telegram_id: int):
    update_user(telegram_id, subscribed=1, gate_passed=1)


def mark_blocked(telegram_id: int):
    update_user(telegram_id, blocked=1, push_sequence_done=1)


def log_push(telegram_id: int, touch: int, event: str):
    with connect() as conn:
        conn.execute(
            "INSERT INTO push_events (telegram_id, touch, event, created_at) VALUES (?, ?, ?, ?)",
            (telegram_id, touch, event, _now()),
        )


def push_stats() -> list[dict]:
    with connect() as conn:
        rows = conn.execute(
            """
            SELECT touch, event, COUNT(*) AS n
            FROM push_events
            GROUP BY touch, event
            ORDER BY touch, event
            """
        ).fetchall()
        return [dict(r) for r in rows]


def due_push_users() -> list[dict]:
    init_db()
    with connect() as conn:
        rows = conn.execute(
            """
            SELECT * FROM bot_users
            WHERE subscribed = 0
              AND onboarding_started = 0
              AND push_sequence_done = 0
              AND blocked = 0
            """
        ).fetchall()
        return [dict(r) for r in rows]


def get_file_id(cache_key: str) -> str | None:
    init_db()
    with connect() as conn:
        row = conn.execute(
            "SELECT file_id FROM media_cache WHERE cache_key = ?", (cache_key,)
        ).fetchone()
        return row["file_id"] if row else None


def set_file_id(cache_key: str, file_id: str):
    init_db()
    with connect() as conn:
        conn.execute(
            "INSERT OR REPLACE INTO media_cache (cache_key, file_id) VALUES (?, ?)",
            (cache_key, file_id),
        )


def delete_file_id(cache_key: str):
    with connect() as conn:
        conn.execute("DELETE FROM media_cache WHERE cache_key = ?", (cache_key,))
