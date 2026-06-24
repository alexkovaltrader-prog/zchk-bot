"""
broadcast.py — разовый скрипт для массовой рассылки.
Запускать вручную через Railway Terminal: python broadcast.py
"""

import os
import asyncio
import logging
import httpx
from datetime import datetime, timezone

logging.basicConfig(format="%(asctime)s - %(levelname)s - %(message)s", level=logging.INFO)

SUPABASE_URL       = os.environ["SUPABASE_URL"]
SUPABASE_SERVICE_KEY = os.environ["SUPABASE_SERVICE_KEY"]


async def test_broadcast():
    """Тест — отправить только себе перед массовой рассылкой"""
    test_id = 478672630
    now = datetime.now(timezone.utc).replace(tzinfo=None).isoformat()
    async with httpx.AsyncClient(timeout=10) as client:
        resp = await client.post(
            f"{SUPABASE_URL}/rest/v1/scheduled_messages",
            headers={
                "apikey": SUPABASE_SERVICE_KEY,
                "Authorization": f"Bearer {SUPABASE_SERVICE_KEY}",
                "Content-Type": "application/json",
                "Prefer": "return=minimal",
            },
            json={
                "telegram_id": test_id,
                "message_type": "pwa_announcement",
                "payload": {},
                "send_at": now,
                "status": "pending",
            }
        )
        if resp.status_code in (200, 201):
            logging.info(f"✅ Test broadcast inserted for {test_id}")
        else:
            logging.error(f"❌ Failed: {resp.status_code} {resp.text}")


async def broadcast():
    """Массовая рассылка всем уникальным telegram_id из scheduled_messages"""
    now = datetime.now(timezone.utc).replace(tzinfo=None).isoformat()

    # Читаем всех уникальных telegram_id
    async with httpx.AsyncClient(timeout=10) as client:
        resp = await client.get(
            f"{SUPABASE_URL}/rest/v1/scheduled_messages",
            params={
                "select": "telegram_id",
                "limit": "1000",
            },
            headers={
                "apikey": SUPABASE_SERVICE_KEY,
                "Authorization": f"Bearer {SUPABASE_SERVICE_KEY}",
            }
        )
        if resp.status_code != 200:
            logging.error(f"Failed to get telegram_ids: {resp.status_code} {resp.text}")
            return

        rows = resp.json()
        unique_ids = list(set(r["telegram_id"] for r in rows))
        logging.info(f"Found {len(unique_ids)} unique telegram_ids")

    # Вставляем pwa_announcement для каждого
    inserted = 0
    async with httpx.AsyncClient(timeout=10) as client:
        for tid in unique_ids:
            resp = await client.post(
                f"{SUPABASE_URL}/rest/v1/scheduled_messages",
                headers={
                    "apikey": SUPABASE_SERVICE_KEY,
                    "Authorization": f"Bearer {SUPABASE_SERVICE_KEY}",
                    "Content-Type": "application/json",
                    "Prefer": "return=minimal",
                },
                json={
                    "telegram_id": tid,
                    "message_type": "pwa_announcement",
                    "payload": {},
                    "send_at": now,
                    "status": "pending",
                }
            )
            if resp.status_code in (200, 201):
                inserted += 1
            else:
                logging.error(f"Failed for {tid}: {resp.status_code} {resp.text}")

    logging.info(f"✅ Inserted {inserted}/{len(unique_ids)} broadcast messages")


async def main():
    # Для теста — отправить только себе
    await broadcast()
    # Для массовой рассылки — раскомментировать строку ниже и закомментировать строку выше
    # await broadcast()


if __name__ == "__main__":
    asyncio.run(main())
