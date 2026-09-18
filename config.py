"""Тексты, ссылки и шаги онбординга. Правки контента — только здесь."""

import os
from pathlib import Path
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

ROOT = Path(__file__).resolve().parent
IMAGES_DIR = ROOT / "assets" / "images"

CHANNEL_USERNAME = "@ZAICHIKFx"
CHANNEL_URL = "https://t.me/ZAICHIKFx"
REVIEWS_URL = "https://t.me/ZAICHIKFx/1009"
PLATFORM_URL = "https://zchkcapital.com/login.html"

CFT_URL = "https://cryptofundtrader.com/?via=zchkcapital"
FULL_ACCESS_URL = "https://app.lava.top/products/8aa52d23-7a67-41d4-a740-a995aeefc504"
QUICK_START_URL = "https://app.lava.top/products/21e9a386-1e50-43af-b1cc-2277b272ad6d"
# Рабочий аккаунт для кнопки «Написать мне» на экране пропов. Подставить боевую ссылку.
WORK_ACCOUNT_URL = os.getenv("WORK_ACCOUNT_URL", "https://t.me/zchkcapitalmanager")
# Ролик «Что такое пропы и как они работают». Подставить боевой URL.
PROP_VIDEO_URL = os.getenv("PROP_VIDEO_URL", "https://t.me/ZAICHIKFx")
# Дубль экрана 5. False = скрыть без правки воронки.
SCREEN_S5_TWO_WEEKS_ENABLED = True


# Продюсер и прочие, кому нужен /reset даже без Railway ADMIN_IDS.
EXTRA_ADMIN_IDS = frozenset({6672319097})


def _admin_ids() -> frozenset[int]:
    ids = set(EXTRA_ADMIN_IDS)
    for part in os.getenv("ADMIN_IDS", "").split(","):
        part = part.strip()
        if not part:
            continue
        try:
            ids.add(int(part))
        except ValueError:
            continue
    return frozenset(ids)


ADMIN_IDS = _admin_ids()
BOT_USERNAME = os.getenv("BOT_USERNAME", "zchkacademy_bot").lstrip("@")
MANAGER_START_PAYLOAD = "manager_future"
MANAGER_HANDLE = "@zchkcapitalmanager"
MANAGER_CONTACT_URL = "https://t.me/zchkcapitalmanager"
BTN_WRITE_MANAGER = "Написать менеджеру"
MANAGER_CONTACT_TEXT = (
    "Напиши менеджеру. Он ответит на любой вопрос по доступу, оплате и подскажет, что подойдёт именно тебе.\n"
    f"{MANAGER_HANDLE}"
)


def manager_deep_link(username: str | None = None) -> str:
    name = (username or BOT_USERNAME).lstrip("@")
    return f"https://t.me/{name}?start={MANAGER_START_PAYLOAD}"


MANAGER_URL = manager_deep_link()


def with_funnel_utm(url: str, step_id: str) -> str:
    """UTM через & если query уже есть, иначе через ?. Deep link t.me/?start= не трогаем."""
    parts = urlsplit(url or "")
    query = dict(parse_qsl(parts.query, keep_blank_values=True))
    if "start" in query and (parts.netloc or "").lower() in {
        "t.me",
        "telegram.me",
        "www.t.me",
    }:
        return url
    query["utm_source"] = "bot"
    query["utm_medium"] = "funnel"
    query["utm_campaign"] = "v2"
    query["utm_content"] = step_id
    encoded = urlencode(query)
    return urlunsplit((parts.scheme, parts.netloc, parts.path, encoded, parts.fragment))


def callback_query_can_open(url: str) -> bool:
    """answerCallbackQuery(url=) открывает только t.me/<bot>?start=…, не произвольный https."""
    parts = urlsplit(url or "")
    host = (parts.netloc or "").lower()
    if host not in {"t.me", "telegram.me", "www.t.me"}:
        return False
    path = parts.path.strip("/")
    if not path or "/" in path:
        return False
    query = dict(parse_qsl(parts.query, keep_blank_values=True))
    return "start" in query


# Картинки только в assets/images, имена латиницей без пробелов.
GATE_IMAGE = "gate.jpg"
GATE_TEXT = (
    "Для продолжения нужно подписаться на канал.\n\n"
    "Дальше ты получишь ссылку на регистрацию и гайд, как проходить проп-фирмы."
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
    from funnels.v1_classic import STEPS as V1_STEPS
    from funnels.v2_path import ALL_STEPS as V2_ALL_STEPS

    names = [GATE_IMAGE]
    names.extend(item["image"] for item in PUSHES)
    names.extend(step["image"] for step in V1_STEPS)
    names.extend(step["image"] for step in V2_ALL_STEPS)
    seen = set()
    unique = []
    for name in names:
        if name not in seen:
            seen.add(name)
            unique.append(name)
    return unique


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
