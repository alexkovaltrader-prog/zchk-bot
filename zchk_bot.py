"""
ZCHK Academy Bot — @zchkacademy_bot
Токен и chat_id хранятся в переменных окружения Railway:
  BOT_TOKEN      — токен бота
  LEADS_CHAT_ID  — chat_id группы лидов (отрицательное число)
"""

import os
import logging
import asyncio
from datetime import datetime, timedelta
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application, CommandHandler, CallbackQueryHandler,
    ContextTypes, MessageHandler, filters
)

# ── КОНФИГ ──────────────────────────────────────────────────────────────────
TOKEN          = os.environ["BOT_TOKEN"]
LEADS_CHAT_ID  = int(os.environ["LEADS_CHAT_ID"])
MANAGER_URL    = "https://t.me/zchkcapitalmanager"
PLATFORM_URL   = "https://zchkcapital.com/login.html"
CALENDLY_URL   = "https://calendly.com/zaichikturit/founder-call"

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)

# ── ИСТОРИЯ ЯРОСЛАВА ─────────────────────────────────────────────────────────
STORY_TEXT = """*Меня зовут Ярослав Зайцев*

С детства до 15 лет я занимался хоккеем профессионально. В 16 начал программировать — и впервые заработал сам. Это изменило мышление навсегда.

Дальше были попытки строить бизнес. С другом открыли химчистку авто — пришла налоговая, закрыли. Попробовал производство 3D-панелей — не вышло. Работал поваром в пиццерии, строил фудтрак. Снова неудача.

Это был тяжёлый путь. Я не буду говорить иначе.

2020 год. Ковид. Все закрываются — я открылся. Осознанное решение идти против течения. И впервые всё получилось. Именно тогда я начал изучать трейдинг.

Я не пошёл на курсы с обещаниями золотых гор. Читал книги, смотрел семинары западных университетов, изучал как реально устроены рынки. Это заняло годы. Но именно это дало понимание которого нет у большинства трейдеров.

Весь опыт сложил в свою платформу и сделал максимально доступную цену — чтобы каждый получил не очередной набор паттернов, а реальную стабильную профессию.

$9,300 — первая крупная выплата от проп-фирмы
$10,396 — следующая выплата месяц спустя
$420,000+ — общая прибыль на реальном счёте"""

WHY_US_TEXT = """*Почему ZCHK, а не другие*

Мы не учим паттернам. Учим читать рынок через базовые принципы — спрос, предложение, нарратив. То что работает всегда, а не только в определённых условиях.

Ты можешь торговать не своими деньгами — до $200,000 чужого капитала и забирать 80% прибыли. Или торговать собственный капитал без сливов — с механизмами управления которые используют крупные финансовые организации.

Мы показываем и убытки, не только профиты. Прозрачность — наш принцип.

Система подходит как новичку, так и тому кто уже торгует. Те кто с опытом — находят здесь ответ почему нет стабильности.

Методичка, 24 видеоурока, разборы сделок. Не теория ради теории — конкретный алгоритм действий.

До 30 июня триал бесплатно. Без карты."""

# ── ТРЕКИ И ВОПРОСЫ ──────────────────────────────────────────────────────────
TRACKS = {
    "novice": {
        "label": "Никогда не торговал",
        "questions": [
            {
                "q": "Почему тебя интересует трейдинг?",
                "opts": [
                    "Хочу дополнительный доход",
                    "Хочу уйти с работы",
                    "Хочу управлять капиталом профессионально",
                    "Пока просто изучаю тему"
                ]
            },
            {
                "q": "Что останавливает от старта?",
                "opts": [
                    "Боюсь потерять деньги",
                    "Не знаю с чего начать",
                    "Не понимаю как это работает",
                    "Нет времени разбираться самому"
                ]
            },
            {
                "q": "Смотрел обучения по трейдингу?",
                "opts": [
                    "Да, но так и не начал торговать",
                    "Нет, начинаю с нуля",
                    "Смотрел YouTube — каша в голове"
                ]
            },
            {
                "q": "Как обычно учишься новому?",
                "opts": [
                    "Читаю и изучаю теорию",
                    "Сразу иду на практику",
                    "Нужна чёткая структура и система",
                    "Нужен наставник который объяснит"
                ]
            }
        ],
        "result": {
            "archetype": "Чистый лист — это твоё главное преимущество",
            "desc": "У тебя нет вредных привычек и ложных паттернов. Большинство приходят в трейдинг через серию дорогостоящих ошибок. Ты можешь построить систему сразу правильно.",
            "pain": "Единственное что тебе нужно сейчас — правильный фундамент. Без него первые же сделки будут хаотичными, а рынок быстро покажет цену неподготовленности.",
            "offer": "Методичка ZCHK плюс бесплатный триал платформы — старт для тех кто хочет войти в профессию правильно. Без слива первого депозита.\n\nДо 30 июня триал бесплатно. Регистрация за 30 секунд."
        }
    },
    "beginner": {
        "label": "До года в трейдинге",
        "questions": [
            {
                "q": "Ты уже сливал депозит?",
                "opts": [
                    "Да, один раз",
                    "Да, несколько раз",
                    "Пока нет, но близко к этому",
                    "Торгую около нуля"
                ]
            },
            {
                "q": "Что обычно происходит в сделках?",
                "opts": [
                    "Режу профит рано, держу убыток долго",
                    "Вхожу на эмоциях после пропущенной сделки",
                    "Стратегия меняется каждые 2 недели",
                    "Всё перечисленное одновременно"
                ]
            },
            {
                "q": "Покупал обучение по трейдингу?",
                "opts": [
                    "Да, деньги потрачены — результата нет",
                    "Смотрел бесплатное — каша в голове",
                    "Нет, учился полностью самостоятельно"
                ]
            },
            {
                "q": "Что делаешь после серии стопов?",
                "opts": [
                    "Ищу новую стратегию",
                    "Пытаюсь отыграться сразу",
                    "Не понимаю что делаю не так",
                    "Останавливаюсь и анализирую"
                ]
            }
        ],
        "result": {
            "archetype": "Трейдер без системы",
            "desc": "Ты уже в рынке, уже чувствовал как теряются деньги. Проблема не в тебе — проблема в том что тебе дали набор паттернов вместо системы мышления.",
            "pain": "Пока нет системы — каждый следующий депозит закончится так же как предыдущий. Каждый аккаунт сливается, а если и получаешь мимолётные результаты — стабильности всё равно нет. Опыт без правильного фундамента только закрепляет ошибки.",
            "offer": "ZCHK даёт то чего не хватает — систему. Риск-менеджмент, чтение рынка через нарратив, психология под давлением. Один слитый депозит стоит дороже курса.\n\nДо 30 июня триал бесплатно, чтобы ознакомиться с платформой."
        }
    },
    "experienced": {
        "label": "1-5 лет в трейдинге",
        "questions": [
            {
                "q": "Есть стабильная прибыльная система?",
                "opts": [
                    "Нет, результат непостоянный",
                    "Частично — бывают хорошие месяцы",
                    "Да, но хочу масштабировать",
                    "Торгую в плюс но хочу в проп"
                ]
            },
            {
                "q": "Пробовал проп-фирмы?",
                "opts": [
                    "Да, не прошёл оценку",
                    "Да, прошёл но слил финансируемый счёт",
                    "Нет, хочу попробовать",
                    "Торгую в проп, хочу улучшить результат"
                ]
            },
            {
                "q": "Главная проблема сейчас?",
                "opts": [
                    "Психология — эмоции мешают торговать",
                    "Нет чёткого алгоритма входа",
                    "Не понимаю как читать нарратив",
                    "Всё вместе"
                ]
            },
            {
                "q": "Сколько торгуешь в месяц?",
                "opts": [
                    "Несколько сделок",
                    "10-30 сделок",
                    "30+ сделок",
                    "Нерегулярно"
                ]
            }
        ],
        "result": {
            "archetype": "Опытный трейдер ищет стабильность",
            "desc": "У тебя есть опыт — и это ловушка. Ты думаешь что уже много знаешь, но результат нестабилен. Это признак одного: системы нет, есть набор навыков без фундамента.",
            "pain": "Годы без стабильного результата — это не невезение. Это системная проблема. Чем дольше торгуешь без исправления фундамента, тем дороже обходится каждый месяц.",
            "offer": "ZCHK — целостная система от структуры рынка до психологии решений. Не с нуля, а поверх твоего опыта. Плюс адаптация под проп-фирмы.\n\nДо 30 июня триал бесплатно. Регистрация за 30 секунд."
        }
    }
}

# ── ПРОГРЕВ ──────────────────────────────────────────────────────────────────
WARMUP = {
    "novice": [
        "Почему 95% новичков теряют деньги\n\nОни торгуют без системы. Видят паттерн — входят. Видят движение — входят. Никакой логики, только ощущения.\n\nРезультат предсказуем. Рынок забирает деньги у тех кто не понимает почему он двигается.\n\nНаша система выстроена не на паттернах из интернета, а на реальной логике — законах спроса и предложения и фундаментальных экономических принципах. Именно это даёт стабильность на дистанции.",
        "История одного студента\n\nДарина пришла в ZCHK чуть больше месяца назад. Никогда не торговала. Боялась потерять деньги.\n\nСейчас у неё понимание структуры рынка, первый проп-аккаунт и уже первая выплата на нём.\n\nПервые 3 урока дали больше понимания чем год самостоятельного изучения — её слова.",
        "Последнее сообщение\n\nЯрослав лично созванивается с каждым новым участником на 10 минут. Без продаж — просто чтобы понять твою ситуацию и показать как работает система.\n\nЭто бесплатно, занимает 10 минут и меняет понимание того куда двигаться.\n\nЗапись на звонок или триал — решение за тобой."
    ],
    "beginner": [
        "Почему твоя стратегия не работает\n\nПаттерны — это следствие, не причина движения цены.\n\nКогда торгуешь по паттернам — угадываешь. Угадывание даёт нестабильный результат даже при хорошем винрейте.\n\nСистема ZCHK основана на другом. Понимать почему рынок двигается — через нарратив, логику ценообразования, структуру. Тогда паттерны становятся не инструментом и не сигналом, а лишь отображением логики в данный момент на рынке.",
        "Один слитый депозит стоит дороже\n\nСредний трейдер теряет от $2,000 до $8,000 на пути к стабильности. Большинство думают что смогут торговать по паттернам из интернета — но трейдинг не про паттерны. Так ты только побуждаешь лудомана в себе.\n\nС нами ты получишь профессию и стабильность.\n\nМетодичка ZCHK — $24.99. Полный курс — $199.\n\nВопрос только в том — ты готов учиться на чужих ошибках или продолжаешь платить за свои?",
        "Твой следующий шаг\n\nЕсли ты читал наши сообщения и что-то резонирует — это не случайно.\n\nЯрослав лично созванивается на 10 минут с теми кто хочет разобраться. Покажет систему изнутри, ответит на главный вопрос.\n\nЭто последнее сообщение от нас. Решение за тобой."
    ],
    "experienced": [
        "Проблема опытных трейдеров\n\nТы торгуешь несколько лет. Есть навыки. Но нет стабильности.\n\nЭто не проблема стратегии. Это проблема фундамента — понимания почему рынок делает то что делает.\n\nБез этого даже правильные сделки превращаются в угадывание. Хороший месяц, плохой месяц. Без системы.",
        "Следующий уровень\n\nЗачем торговать на $5,000 своих когда можно торговать на $100,000–$200,000 чужих?\n\nПроп-фирмы дают капитал тем кто умеет управлять риском. 80% прибыли твоя.\n\nВ ZCHK есть отдельный блок по адаптации под правила проп-фирм. Как выстроить риск-менеджмент, как торговать в условиях дродауна, как системно пройти оценку.",
        "10 минут с Ярославом\n\nЕсли ты с опытом и хочешь разобрать конкретные вопросы — Ярослав созванивается лично.\n\n10 минут. Твоя ситуация. Конкретный следующий шаг.\n\nЗапись бесплатная. Это последнее сообщение от нас."
    ]
}

# ── ХРАНИЛИЩЕ СОСТОЯНИЙ ──────────────────────────────────────────────────────
user_states = {}
user_locks = {}  # лок на юзера — защита от двойных нажатий

def get_state(user_id):
    return user_states.get(user_id, {})

def set_state(user_id, state):
    user_states[user_id] = state

def get_lock(user_id):
    if user_id not in user_locks:
        user_locks[user_id] = asyncio.Lock()
    return user_locks[user_id]

# ── ХЭНДЛЕРЫ ────────────────────────────────────────────────────────────────
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    set_state(user.id, {})

    kb = [
        [InlineKeyboardButton("Никогда не торговал", callback_data="track_novice")],
        [InlineKeyboardButton("До года в трейдинге", callback_data="track_beginner")],
        [InlineKeyboardButton("1-5 лет опыта", callback_data="track_experienced")],
    ]
    await update.message.reply_text(
        f"Привет, {user.first_name}\n\n"
        f"Я бот ZCHK Academy — платформы по трейдингу. Готовим к проп-трейдингу и торговле личным капиталом.\n\n"
        f"Пять вопросов — и ты получишь персональный разбор своей ситуации.\n\n"
        f"*Сколько ты уже в трейдинге?*",
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup(kb)
    )

async def button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user = update.effective_user
    data = query.data

    # Для ответов на вопросы используем лок — защита от двойных нажатий
    if data.startswith("ans_") or data.startswith("track_"):
        lock = get_lock(user.id)
        if lock.locked():
            # Уже обрабатывается — игнорируем повторное нажатие
            return
        async with lock:
            await _handle_quiz_button(query, context, user, data)
    else:
        await _handle_menu_button(query, context, user, data)

async def _handle_quiz_button(query, context, user, data):
    state = get_state(user.id)

    # Выбор трека
    if data.startswith("track_"):
        track_key = data.replace("track_", "")
        set_state(user.id, {"track": track_key, "step": 0, "answers": []})
        await send_question(query, context, get_state(user.id))

    # Ответ на вопрос
    elif data.startswith("ans_"):
        ans_idx = int(data.replace("ans_", ""))
        if not state or "track" not in state:
            await query.edit_message_text(
                "Что-то пошло не так. Напиши /start чтобы начать заново.",
                parse_mode="Markdown"
            )
            return

        expected_step = state["step"]
        # Защита от повторного нажатия на уже пройденный вопрос
        if len(state["answers"]) != expected_step:
            return

        state["answers"].append(ans_idx)
        state["step"] += 1
        set_state(user.id, state)

        track = TRACKS[state["track"]]
        if state["step"] < len(track["questions"]):
            await send_question(query, context, state)
        else:
            await send_result(query, context, state, user)

async def _handle_menu_button(query, context, user, data):

    # История Ярослава
    if data == "show_story":
        kb = [
            [InlineKeyboardButton("Почему ZCHK", callback_data="show_why")],
        ]
        # Сначала отправляем фото торгового счёта как доказательство цифр
        chat_id = query.message.chat_id
        try:
            await context.bot.send_photo(
                chat_id=chat_id,
                photo="https://raw.githubusercontent.com/alexkovaltrader-prog/zchk-bot/main/Frame_138.png",
                caption="📊 Реальный торговый счёт — прибыль $420,000+"
            )
        except Exception as e:
            logging.error(f"Story photo 1 failed: {e}")
        try:
            await context.bot.send_photo(
                chat_id=chat_id,
                photo="https://raw.githubusercontent.com/alexkovaltrader-prog/zchk-bot/main/%D0%91%D0%B5%D0%B7%20%D0%BD%D0%B0%D0%B7%D0%B2%D0%B0%D0%BD%D0%B8%D1%8F.png",
                caption="💰 Сертификат выплаты Crypto Fund Trader — $9,300"
            )
        except Exception as e:
            logging.error(f"Story photo 2 failed: {e}")
        await context.bot.send_message(
            chat_id=chat_id,
            text=STORY_TEXT,
            parse_mode="Markdown",
            reply_markup=InlineKeyboardMarkup(kb)
        )

    # Почему мы
    elif data == "show_why":
        kb = [
            [InlineKeyboardButton("Записаться на звонок с Ярославом", url=CALENDLY_URL)],
            [InlineKeyboardButton("Разобраться самостоятельно на платформе", url=PLATFORM_URL)],
        ]
        await query.edit_message_text(WHY_US_TEXT, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(kb))

    # Рестарт
    elif data == "restart":
        set_state(user.id, {})
        kb = [
            [InlineKeyboardButton("Никогда не торговал", callback_data="track_novice")],
            [InlineKeyboardButton("До года в трейдинге", callback_data="track_beginner")],
            [InlineKeyboardButton("1-5 лет опыта", callback_data="track_experienced")],
        ]
        await query.edit_message_text(
            "*Сколько ты уже в трейдинге?*",
            parse_mode="Markdown",
            reply_markup=InlineKeyboardMarkup(kb)
        )

async def send_question(query, context, state):
    track = TRACKS[state["track"]]
    q_data = track["questions"][state["step"]]
    step_num = state["step"] + 1
    total = len(track["questions"])
    progress = "▓" * step_num + "░" * (total - step_num)

    kb = [[InlineKeyboardButton(opt, callback_data=f"ans_{i}")] for i, opt in enumerate(q_data["opts"])]
    await query.edit_message_text(
        f"`{progress}` Вопрос {step_num}/{total}\n\n*{q_data['q']}*",
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup(kb)
    )

async def send_result(query, context, state, user):
    track_key = state["track"]
    track = TRACKS[track_key]
    r = track["result"]

    # Уведомление в группу лидов
    track_labels = {"novice": "Никогда не торговал", "beginner": "До года", "experienced": "1-5 лет"}
    answers_text = "\n".join([
        f"  {i+1}. {track['questions'][i]['opts'][state['answers'][i]]}"
        for i in range(len(state["answers"]))
    ])
    lead_msg = (
        f"🔥 *Новый лид из бота*\n\n"
        f"👤 {user.full_name} (@{user.username or 'нет username'})\n"
        f"🎯 Трек: {track_labels[track_key]}\n\n"
        f"*Ответы:*\n{answers_text}"
    )
    try:
        await context.bot.send_message(LEADS_CHAT_ID, lead_msg, parse_mode="Markdown")
    except Exception as e:
        logging.error(f"Lead notification failed: {e}")

    # Планируем прогрев
    chat_id = query.message.chat_id
    warmup_msgs = WARMUP.get(track_key, [])
    try:
        for i, msg in enumerate(warmup_msgs):
            delay = (i + 1) * 86400
            context.job_queue.run_once(
                send_warmup,
                delay,
                data={"chat_id": chat_id, "text": msg, "step": i},
                name=f"warmup_{chat_id}_{i}"
            )
    except Exception as e:
        logging.error(f"Warmup scheduling failed: {e}")

    # Отправляем фото Ярослава
    YAROSLAV_PHOTO = "https://raw.githubusercontent.com/alexkovaltrader-prog/zchk-bot/main/IMG_0101.JPG"
    try:
        await context.bot.send_photo(
            chat_id=chat_id,
            photo=YAROSLAV_PHOTO,
            caption="*Ярослав Зайцев* — основатель ZCHK Capital",
            parse_mode="Markdown"
        )
    except Exception as e:
        logging.error(f"Photo send failed: {e}")

    kb = [
        [InlineKeyboardButton("История Ярослава", callback_data="show_story")],
    ]
    await context.bot.send_message(
        chat_id=chat_id,
        text=(
            f"*{r['archetype']}*\n\n"
            f"{r['desc']}\n\n"
            f"{r['pain']}\n\n"
            f"{r['offer']}"
        ),
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup(kb)
    )

async def send_warmup(context: ContextTypes.DEFAULT_TYPE):
    job = context.job
    data = job.data
    step = data["step"]
    text = data["text"]

    kb = [
        [InlineKeyboardButton("Протестировать платформу бесплатно", url=PLATFORM_URL)],
        [InlineKeyboardButton("Записаться на звонок с Ярославом", url=CALENDLY_URL)],
    ]

    # День 2 (step=1) — добавляем фото отзыва студента
    if step == 1:
        try:
            await context.bot.send_photo(
                data["chat_id"],
                photo="https://raw.githubusercontent.com/alexkovaltrader-prog/zchk-bot/main/%D0%A1%D0%BD%D0%B8%D0%BC%D0%BE%D0%BA%20%D1%8D%D0%BA%D1%80%D0%B0%D0%BD%D0%B0%202026-06-05%20150556.png",
                caption="💬 Студентка Дарина — взяла платформу 2 недели назад, уже зарабатывает"
            )
        except Exception as e:
            logging.error(f"Warmup photo step 1 failed: {e}")

    try:
        await context.bot.send_message(
            data["chat_id"],
            text,
            parse_mode="Markdown",
            reply_markup=InlineKeyboardMarkup(kb)
        )
    except Exception as e:
        logging.error(f"Warmup {step} failed: {e}")

# ── ЗАПУСК ───────────────────────────────────────────────────────────────────
def main():
    app = (
        Application.builder()
        .token(TOKEN)
        .build()
    )
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(button))
    print("✅ ZCHK Academy бот запущен")
    app.run_polling(drop_pending_updates=True)

if __name__ == "__main__":
    main()
