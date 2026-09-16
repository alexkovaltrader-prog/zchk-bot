"""Архив рабочей воронки. Тексты, картинки и порядок не менять."""

VERSION = "v1"

STEPS = [
    {
        "id": "register",
        "image": "screen_login.jpg",
        "title": "01 — Регистрация за 30 секунд",
        "text": (
            "Заходишь на платформу, вводишь email и пароль — и сразу получаешь доступ. "
            "Можно войти через Google. Никаких лишних шагов."
        ),
    },
    {
        "id": "dashboard",
        "image": "screen_dasbord.jpg",
        "title": "02 — Главная панель",
        "text": (
            "После входа попадаешь на дашборд. Здесь виден твой прогресс, "
            "доступные разделы и следующий шаг. Всё на одном экране."
        ),
    },
    {
        "id": "library",
        "image": "screen_library.jpg",
        "title": "03 — Библиотека видеоуроков — 24 лекции",
        "text": (
            "Это ядро обучения. 24 урока разбиты на 5 блоков — от основ до проп-стратегий. "
            "Каждый урок: сначала теория, затем практика на реальном графике."
        ),
    },
    {
        "id": "lesson",
        "image": "screen_lesson.jpg",
        "title": "",
        "text": "",
    },
    {
        "id": "lesson2",
        "image": "screen_lesson2.jpg",
        "title": "",
        "text": "",
    },
    {
        "id": "checklist",
        "image": "screen_checklist.jpg",
        "title": "04 — Алгоритм анализа перед входом",
        "text": (
            "Интерактивный чеклист — пошаговый алгоритм который ты проходишь "
            "перед каждой сделкой. Убирает эмоции из принятия решений."
        ),
    },
    {
        "id": "articles",
        "image": "screen_articles.jpg",
        "title": "05 — Статьи и разборы от Ярослава",
        "text": (
            "Ярослав сам пишет статьи с выжимками из практики. Не вода, не мотивация. "
            "Разборы реальных ситуаций, психология трейдера, типичные ошибки."
        ),
    },
    {
        "id": "metodichka",
        "image": "screen_metodichka.jpg",
        "title": "06 — Методичка — 6 частей с нуля до системы",
        "text": (
            "Текстовая база знаний. 6 частей от полного нуля до рабочей торговой системы. "
            "Институциональный анализ, TDA, риск-менеджмент, психология — всё структурировано и по порядку."
        ),
    },
]


def caption(index: int) -> str:
    step = STEPS[index]
    parts = [f"Шаг {index + 1} из {len(STEPS)}"]
    if step.get("title"):
        parts.append(step["title"])
    if step.get("text"):
        parts.append(step["text"])
    return "\n\n".join(parts)


def keyboard(index: int):
    from telegram import InlineKeyboardButton, InlineKeyboardMarkup
    from config import BTN_BACK, BTN_NEXT, BTN_PLATFORM, BTN_REVIEWS, PLATFORM_URL, REVIEWS_URL

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
