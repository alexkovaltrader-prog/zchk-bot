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
                funnel_version TEXT,
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
        conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS funnel_events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                telegram_id INTEGER NOT NULL,
                event TEXT NOT NULL,
                step_id TEXT,
                step_index INTEGER,
                button_id TEXT,
                created_at TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS funnel_followups (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                telegram_id INTEGER NOT NULL,
                branch TEXT NOT NULL,
                touch INTEGER NOT NULL,
                created_at TEXT NOT NULL
            );
            """
        )
        cols = {row[1] for row in conn.execute("PRAGMA table_info(bot_users)")}
        extra = {
            "funnel_version": "TEXT",
            "last_step_at": "TEXT",
            "onboarding_completed": "INTEGER NOT NULL DEFAULT 0",
            "funnel_branch": "TEXT",
            "purchase_kind": "TEXT",
            "funnel_followup_done": "INTEGER NOT NULL DEFAULT 0",
            "funnel_objection": "TEXT",
            "asked_manager": "INTEGER NOT NULL DEFAULT 0",
        }
        for name, decl in extra.items():
            if name not in cols:
                conn.execute(f"ALTER TABLE bot_users ADD COLUMN {name} {decl}")
        conn.execute(
            """
            UPDATE bot_users
            SET funnel_version = 'v1'
            WHERE (funnel_version IS NULL OR TRIM(funnel_version) = '')
              AND onboarding_started = 1
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


def delete_user(telegram_id: int):
    init_db()
    with connect() as conn:
        conn.execute("DELETE FROM funnel_events WHERE telegram_id = ?", (telegram_id,))
        conn.execute("DELETE FROM funnel_followups WHERE telegram_id = ?", (telegram_id,))
        conn.execute("DELETE FROM push_events WHERE telegram_id = ?", (telegram_id,))
        conn.execute("DELETE FROM bot_users WHERE telegram_id = ?", (telegram_id,))


def log_funnel_event(
    telegram_id: int,
    event: str,
    step_id: str | None = None,
    step_index: int | None = None,
    button_id: str | None = None,
):
    init_db()
    with connect() as conn:
        conn.execute(
            """
            INSERT INTO funnel_events (
                telegram_id, event, step_id, step_index, button_id, created_at
            ) VALUES (?, ?, ?, ?, ?, ?)
            """,
            (telegram_id, event, step_id, step_index, button_id, _now()),
        )


def log_funnel_followup(telegram_id: int, branch: str, touch: int):
    init_db()
    with connect() as conn:
        conn.execute(
            """
            INSERT INTO funnel_followups (telegram_id, branch, touch, created_at)
            VALUES (?, ?, ?, ?)
            """,
            (telegram_id, branch, touch, _now()),
        )


def followup_touches(telegram_id: int, branch: str) -> set[int]:
    init_db()
    with connect() as conn:
        rows = conn.execute(
            """
            SELECT touch FROM funnel_followups
            WHERE telegram_id = ? AND branch = ?
            """,
            (telegram_id, branch),
        ).fetchall()
        return {int(r["touch"]) for r in rows}


def due_funnel_followup_users() -> list[dict]:
    init_db()
    with connect() as conn:
        rows = conn.execute(
            """
            SELECT * FROM bot_users
            WHERE funnel_version = 'v2'
              AND onboarding_started = 1
              AND funnel_followup_done = 0
              AND blocked = 0
            """
        ).fetchall()
        return [dict(r) for r in rows]


def funnel_metrics() -> dict:
    init_db()
    with connect() as conn:
        views = conn.execute(
            """
            SELECT step_index, step_id, COUNT(DISTINCT telegram_id) AS users
            FROM funnel_events
            WHERE event = 'step_view'
            GROUP BY step_index, step_id
            ORDER BY step_index
            """
        ).fetchall()
        clicks = conn.execute(
            """
            SELECT button_id, COUNT(*) AS n
            FROM funnel_events
            WHERE event = 'link_click'
            GROUP BY button_id
            """
        ).fetchall()
        impressions = conn.execute(
            """
            SELECT button_id, COUNT(*) AS n
            FROM funnel_events
            WHERE event = 'link_impression'
            GROUP BY button_id
            """
        ).fetchall()
        reached = conn.execute(
            """
            SELECT COUNT(*) AS n FROM bot_users
            WHERE funnel_version = 'v2' AND onboarding_completed = 1
            """
        ).fetchone()
        started = conn.execute(
            """
            SELECT COUNT(*) AS n FROM bot_users
            WHERE funnel_version = 'v2' AND onboarding_started = 1
            """
        ).fetchone()
        purchases = conn.execute(
            """
            SELECT purchase_kind, COUNT(*) AS n FROM bot_users
            WHERE funnel_version = 'v2' AND purchase_kind IS NOT NULL AND purchase_kind != ''
            GROUP BY purchase_kind
            """
        ).fetchall()
        return {
            "step_users": [dict(r) for r in views],
            "link_clicks": [dict(r) for r in clicks],
            "link_impressions": [dict(r) for r in impressions],
            "v2_started": int(started["n"] if started else 0),
            "v2_reached_9": int(reached["n"] if reached else 0),
            "purchases": [dict(r) for r in purchases],
        }


def hours_since_iso(value: str | None) -> float | None:
    if not value:
        return None
    started = datetime.fromisoformat(value)
    if started.tzinfo is None:
        started = started.replace(tzinfo=timezone.utc)
    return (datetime.now(timezone.utc) - started.astimezone(timezone.utc)).total_seconds() / 3600


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
