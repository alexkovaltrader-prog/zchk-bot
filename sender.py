"""
sender.py — Railway Cron Job
Запускается каждые 10 минут, шлёт запланированные сообщения из Supabase.
Не зависит от состояния бота, не теряется при редеплое.
"""

import os
import asyncio
import logging
import httpx
from datetime import datetime

logging.basicConfig(format="%(asctime)s - %(levelname)s - %(message)s", level=logging.INFO)

BOT_TOKEN          = os.environ["BOT_TOKEN"]
SUPABASE_URL       = os.environ["SUPABASE_URL"]
SUPABASE_SERVICE_KEY = os.environ["SUPABASE_SERVICE_KEY"]
PLATFORM_URL       = "https://zchkcapital.com/login.html"
CALENDLY_URL       = "https://calendly.com/zaichikturit/founder-call"

# ── Тексты прогрева (копия из бота, по result_key) ───────────────────────────
WARMUP = {
    "result_novice_11_hot": [
        "Страх в трейдинге это не слабость. Это нормальная реакция на то чего не понимаешь.\n\nЯ сам когда начинал боялся. Не потерять деньги — боялся потратить годы и ничего не получить. Это другой страх и он более честный.\n\nБольшинство кто теряет, не боялись достаточно. Заходили на эмоциях.",
        "Есть одна вещь которую я понял после нескольких лет в рынке.\n\nТрейдинг не терпит угадывания. Либо ты понимаешь почему цена двигается, либо нет. Паттерны, сигналы, индикаторы — это всё следствия. Когда понимаешь причину, следствия становятся очевидными.\n\nИменно с этого начинается платформа. Зайди и посмотри первые уроки, это бесплатно.",
        "Если остались вопросы — напиши мне. Созвонимся, разберём твою ситуацию. Без продаж, просто поговорим."
    ],
    "result_novice_12_hot": [
        "Желание работать на себя, я это понимаю лучше чем кто-либо.\n\nЯ работал поваром в пиццерии пока искал свой путь. Трейдинг дал мне то что я искал. Но между желанием и результатом есть конкретные шаги.\n\nГлавный из них — не торопиться с первым депозитом.",
        "Самая частая ошибка мотивированных людей — они хотят быстро.\n\nВ трейдинге скорость на старте стоит дорого. Те кто разобрались сначала, потом двигаются намного быстрее.\n\nЗайди на платформу и посмотри как выглядит путь от начала до первого результата. Это бесплатно.",
        "Если хочешь поговорить о том как начать правильно — я на связи. Созвонимся, разберём твою ситуацию конкретно."
    ],
    "result_beginner_21_hot": [
        "Слитый депозит это больно. Не буду говорить что это нормально.\n\nНо вот что я заметил за годы работы. Те кто восстанавливается — не те кто упорнее. Те кто понял где была системная ошибка и не повторил её.",
        "Почти всегда когда человек сливает, он торговал без понимания почему рынок делает то что делает.\n\nВидел движение, входил. Это угадывание а не торговля. Зайди на платформу и посмотри как выглядит торговля с пониманием логики. Это бесплатно.",
        "Если хочешь разобрать что пошло не так — созвонимся. Иногда 10 минут дают больше ясности чем месяц самостоятельного анализа."
    ],
    "result_beginner_22_hot": [
        "Торговать около нуля месяцами это особый вид тупика.\n\nКажется что прогресс есть. Не сливаешь же. Но стабильного плюса нет. И непонятно что менять.",
        "Нестабильность обычно не про стратегию.\n\nСтратегии работают в определённых условиях. Когда условия меняются, они ломаются. Те кто понимает логику рынка адаптируются.\n\nЗайди на платформу и посмотри в чём разница. Бесплатно.",
        "Если хочешь найти где именно проблема — созвонимся. Коротко и конкретно."
    ],
    "result_experienced_32_hot": [
        "Знаешь правила и нарушаешь их. Это не про характер.\n\nПроблема не в силе воли. Проблема в том что решения принимаются во время сделки а не до неё. Когда эмоции уже включились.",
        "Психология в трейдинге не лечится книгами о психологии.\n\nОна лечится когда алгоритм определяет всё заранее и во время сделки нечего решать.\n\nЗайди на платформу и посмотри как это устроено. Бесплатно.",
        "Если хочешь разобрать как убрать эмоциональные решения системно — созвонимся."
    ],
}

# Дефолтный прогрев если result_key не найден
DEFAULT_WARMUP = [
    "Как дела с платформой? Зайди и посмотри первые уроки если ещё не успел. Это бесплатно.",
    "Если остались вопросы по материалу — Ярослав на связи. Можем разобрать твою ситуацию за 10 минут.",
    "Последнее напоминание от меня. Если хочешь двигаться быстрее — запишись на звонок. Без продаж, просто разберём твой следующий шаг."
]

SURVEY_TEXT = (
    "Быстрый вопрос — займёт 30 секунд.\n\n"
    "Ты зашёл на платформу несколько дней назад. Хочу понять как всё идёт.\n\n"
    "*Смотрел уроки на платформе?*"
)


# ── Supabase helpers ─────────────────────────────────────────────────────────

async def get_pending_messages():
    now = datetime.utcnow().isoformat()
    async with httpx.AsyncClient(timeout=10) as client:
        resp = await client.get(
            f"{SUPABASE_URL}/rest/v1/scheduled_messages",
            params={
                "status": "eq.pending",
                "send_at": f"lte.{now}",
                "select": "*",
                "limit": "50",
                "order": "send_at.asc",
            },
            headers={
                "apikey": SUPABASE_SERVICE_KEY,
                "Authorization": f"Bearer {SUPABASE_SERVICE_KEY}",
            }
        )
        if resp.status_code == 200:
            return resp.json()
        logging.error(f"get_pending_messages failed: {resp.status_code} {resp.text}")
        return []


async def mark_sent(message_id: str):
    async with httpx.AsyncClient(timeout=10) as client:
        await client.patch(
            f"{SUPABASE_URL}/rest/v1/scheduled_messages",
            params={"id": f"eq.{message_id}"},
            headers={
                "apikey": SUPABASE_SERVICE_KEY,
                "Authorization": f"Bearer {SUPABASE_SERVICE_KEY}",
                "Content-Type": "application/json",
            },
            json={"status": "sent", "sent_at": datetime.utcnow().isoformat()}
        )


async def mark_failed(message_id: str):
    async with httpx.AsyncClient(timeout=10) as client:
        await client.patch(
            f"{SUPABASE_URL}/rest/v1/scheduled_messages",
            params={"id": f"eq.{message_id}"},
            headers={
                "apikey": SUPABASE_SERVICE_KEY,
                "Authorization": f"Bearer {SUPABASE_SERVICE_KEY}",
                "Content-Type": "application/json",
            },
            json={"status": "failed"}
        )


# ── Telegram sender ──────────────────────────────────────────────────────────

async def send_telegram(telegram_id: int, text: str, keyboard=None):
    body = {
        "chat_id": telegram_id,
        "text": text,
        "parse_mode": "Markdown",
    }
    if keyboard:
        body["reply_markup"] = {"inline_keyboard": keyboard}

    async with httpx.AsyncClient(timeout=15) as client:
        resp = await client.post(
            f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage",
            json=body
        )
        if resp.status_code != 200:
            logging.error(f"Telegram send failed {telegram_id}: {resp.text}")
            return False
        return True


async def send_photo_telegram(telegram_id: int, photo_url: str):
    async with httpx.AsyncClient(timeout=30) as client:
        photo_resp = await client.get(photo_url)
        if photo_resp.status_code != 200:
            return
        files = {"photo": ("photo.jpg", photo_resp.content, "image/jpeg")}
        await client.post(
            f"https://api.telegram.org/bot{BOT_TOKEN}/sendPhoto",
            data={"chat_id": telegram_id},
            files=files
        )


# ── Message processors ───────────────────────────────────────────────────────

async def process_warmup(telegram_id: int, step: int, payload: dict):
    result_key = payload.get("result_key", "")
    texts = WARMUP.get(result_key, DEFAULT_WARMUP)

    if step >= len(texts):
        logging.warning(f"No warmup text for step {step}, result_key={result_key}")
        return True

    text = texts[step]

    kb = [
        [{"text": "Открыть платформу", "url": PLATFORM_URL}],
        [{"text": "Записаться на звонок с Ярославом", "url": CALENDLY_URL}],
    ]

    # На шаге 2 (день 2) шлём скрин результатов как в боте
    if step == 1:
        GITHUB_BASE = "https://raw.githubusercontent.com/alexkovaltrader-prog/zchk-bot/main"
        await send_photo_telegram(
            telegram_id,
            f"{GITHUB_BASE}/%D0%A1%D0%BD%D0%B8%D0%BC%D0%BE%D0%BA%20%D1%8D%D0%BA%D1%80%D0%B0%D0%BD%D0%B0%202026-06-05%20150556.png"
        )

    return await send_telegram(telegram_id, text, kb)


async def process_survey(telegram_id: int, payload: dict):
    kb = [
        [{"text": "Да, несколько уроков", "callback_data": "survey:watched:several"}],
        [{"text": "Один посмотрел", "callback_data": "survey:watched:one"}],
        [{"text": "Ещё не заходил", "callback_data": "survey:watched:none"}],
    ]
    return await send_telegram(telegram_id, SURVEY_TEXT, kb)


async def process_message(msg: dict):
    telegram_id = msg["telegram_id"]
    message_type = msg["message_type"]
    payload = msg.get("payload") or {}

    if message_type == "warmup_1":
        return await process_warmup(telegram_id, 0, payload)
    elif message_type == "warmup_2":
        return await process_warmup(telegram_id, 1, payload)
    elif message_type == "warmup_3":
        return await process_warmup(telegram_id, 2, payload)
    elif message_type == "survey_7":
        return await process_survey(telegram_id, payload)
    else:
        logging.warning(f"Unknown message_type: {message_type}")
        return True


# ── Main ─────────────────────────────────────────────────────────────────────

async def main():
    messages = await get_pending_messages()
    logging.info(f"Pending messages to send: {len(messages)}")

    for msg in messages:
        msg_id = msg["id"]
        try:
            success = await process_message(msg)
            if success:
                await mark_sent(msg_id)
                logging.info(f"✅ Sent {msg['message_type']} to {msg['telegram_id']}")
            else:
                await mark_failed(msg_id)
                logging.error(f"❌ Failed {msg['message_type']} to {msg['telegram_id']}")
        except Exception as e:
            logging.error(f"Exception processing {msg_id}: {e}")
            await mark_failed(msg_id)

    logging.info("sender.py done")


if __name__ == "__main__":
    asyncio.run(main())
