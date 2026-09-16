"""Тексты, ссылки и шаги онбординга. Правки контента — только здесь."""

from pathlib import Path

ROOT = Path(__file__).resolve().parent
IMAGES_DIR = ROOT / "assets" / "images"

CHANNEL_USERNAME = "@ZAICHIKFx"
CHANNEL_URL = "https://t.me/ZAICHIKFx"
REVIEWS_URL = "https://t.me/ZAICHIKFx/1009"
PLATFORM_URL = "https://zchkcapital.com/login.html"

# Картинки только в assets/images, имена латиницей без пробелов.
GATE_IMAGE = "gate.jpg"
GATE_TEXT = (
    "Чтобы открыть доступ, нужна подписка на канал — там основное: "
    "разборы рынка, позиции и то, что я не выкладываю больше нигде.\n\n"
    "Подпишись и нажми «Я подписался»."
)
GATE_ALERT_NOT_SUB = "Подписка не найдена. Проверь, что подписался на канал"

CHECK_SUB_COOLDOWN_SEC = 3
PUSH_MAX_PER_SEC = 20
PUSH_HOUR_START_MSK = 10
PUSH_HOUR_END_MSK = 21

BTN_SUBSCRIBE = "Подписаться"
BTN_CHECK = "Я подписался"
BTN_REVIEWS = "Отзывы"
BTN_NEXT = "Дальше →"
BTN_BACK = "← Назад"
BTN_PLATFORM = "Перейти на платформу"
MENU_REVIEWS = "Отзывы"

# Добавление шага — только новая строка в этом списке.
STEPS = [
    {
        "id": "register",
        "image": "register.jpg",
        "title": "01 — Регистрация",
        "text": (
            "Создаёшь аккаунт — email, пароль, можно Google. "
            "Сразу бесплатный trial. Никаких лишних шагов."
        ),
    },
    {
        "id": "intro",
        "image": "intro.jpg",
        "title": "02 — Перед стартом",
        "text": (
            "После регистрации — короткое видео на 11 минут. "
            "Досмотри до конца — после этого открывается доступ к платформе."
        ),
    },
    {
        "id": "dashboard",
        "image": "dashboard.jpg",
        "title": "03 — Личный кабинет",
        "text": (
            "На главной виден прогресс и следующие шаги: регистрация, приложение на телефон, "
            "канал, первый раздел. Всё на одном экране."
        ),
    },
    {
        "id": "positions",
        "image": "positions.jpg",
        "title": "04 — Позиции и математика",
        "text": (
            "Открытые позиции и калькулятор: размер проп-аккаунта, доходность, "
            "твоя доля. Считаешь цифры до входа в рынок, не в моменте."
        ),
    },
    {
        "id": "videos",
        "image": "videos.jpg",
        "title": "05 — Видеоуроки",
        "text": (
            "Библиотека: 24 урока Price Action. На trial доступна первая часть методички "
            "и вводные уроки, дальше — полный доступ."
        ),
    },
    {
        "id": "methodichka",
        "image": "methodichka.jpg",
        "title": "06 — Методичка",
        "text": (
            "7 частей с нуля до системы: основы, структура тренда, Price Action, "
            "AMT, Live Trading. Идёшь по порядку, текущая часть открыта."
        ),
    },
    {
        "id": "articles",
        "image": "articles.jpg",
        "title": "07 — Статьи и разборы",
        "text": (
            "Выжимки из практики: журнал сделок, ошибки мышления, статистика. "
            "Не вода и не мотивация."
        ),
    },
    {
        "id": "live",
        "image": "live.jpg",
        "title": "08 — Сделки в рынке",
        "text": (
            "Позиции публикуются до результата — со стопом, тейком и разбором логики входа. "
            "На полном доступе — уровни, история и все сделки."
        ),
    },
]

PUSHES = [
    {
        "touch": 1,
        "delay_hours": 24,
        "image": "gate.jpg",
        "text": (
            "Ты остановился на первом шаге.\n\n"
            "Чтобы открыть доступ, нужна подписка на канал — там основное: "
            "разборы рынка, позиции и то, что я не выкладываю больше нигде.\n\n"
            "Подпишись и возвращайся, продолжим с того же места."
        ),
    },
    {
        "touch": 2,
        "delay_hours": 72,
        "image": "story.jpg",
        "text": (
            "Пока ты не дошёл, коротко о главном.\n\n"
            "Большинство сливает не потому, что не знает паттернов. "
            "А потому что принимает решения в моменте, когда цена летит и деньги настоящие.\n\n"
            "Я торгую иначе: все решения приняты заранее, днём я на графики не смотрю. "
            "Как это устроено — разбираю в канале и внутри бота.\n\n"
            "Вход всё ещё открыт."
        ),
    },
    {
        "touch": 3,
        "delay_hours": 24 * 7,
        "image": "reviews.jpg",
        "text": (
            "Последнее сообщение, дальше не пишу.\n\n"
            "Доступ к боту остаётся, он никуда не денется. "
            "Захочешь вернуться — просто подпишись на канал и нажми «Я подписался».\n\n"
            "Отзывы тех, кто уже внутри: https://t.me/ZAICHIKFx/1009"
        ),
        "show_reviews": True,
    },
]


def configured_images() -> list[str]:
    names = [GATE_IMAGE]
    names.extend(step["image"] for step in STEPS)
    names.extend(item["image"] for item in PUSHES)
    return names


def log_image_assets():
    import logging

    log = logging.getLogger(__name__)
    IMAGES_DIR.mkdir(parents=True, exist_ok=True)
    for name in configured_images():
        path = (IMAGES_DIR / name).resolve()
        if path.is_file():
            log.info("image ok %s -> %s", name, path)
        else:
            log.error("image MISSING %s -> %s", name, path)
