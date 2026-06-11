"""
ZCHK Academy Bot — @zchkacademy_bot
Токен: 8883835887:AAFzMh_1AhW8E8ggwFnFhAANLZSbDCsdaXw
Группа лидов: -5154204408
"""

import logging
import asyncio
from datetime import datetime, timedelta
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application, CommandHandler, CallbackQueryHandler,
    ContextTypes, MessageHandler, filters
)

# ── КОНФИГ ──────────────────────────────────────────────────────────────────
TOKEN          = "8883835887:AAFzMh_1AhW8E8ggwFnFhAANLZSbDCsdaXw"
LEADS_CHAT_ID  = -5154204408
MANAGER_URL    = "https://t.me/zchkcapitalmanager"
PLATFORM_URL   = "https://zchkcapital.com/login.html"
CALENDLY_URL   = "https://calendly.com/zaichikturit/founder-call"

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)

# ── ИСТОРИЯ ЯРОСЛАВА ─────────────────────────────────────────────────────────
STORY_TEXT = """👤 *Меня зовут Ярослав Зайцев

С детства до 15 лет я занимался хоккеем профессионально. В 16 начал программировать и впервые заработал сам. Это изменило мышление навсегда.

Дальше были попытки строить бизнес. С другом открыли химчистку авто — пришла налоговая, закрыли. Попробовал производство 3D-панелей не вышло. Работал поваром в пиццерии, строил фудтрак. Снова неудача.

Это был тяжёлый путь. Я не буду говорить иначе.

2020 год. Ковид. Все закрываются Я открылся. Осознанное решение идти против течения. И впервые всё получилось. Именно тогда я начал изучать трейдинг.

Я не пошёл на курсы с обещаниями золотых гор. Читал книги, смотрел семинары западных университетов, изучал как реально устроены рынки. Это заняло годы. Но именно это дало понимание которого нет у большинства трейдеров.

Весь опыт сложил в свою платформу и сделал максимально доступную цену — чтобы каждый получил не очередной набор паттернов, а реальную стабильную профессию.*"""

WHY_US_TEXT = """⚡️ *Почему ZCHK Capital, а не другие*

→ Без паттернов. Учим читать рынок через базовые принципы — спрос, предложение, нарратив. То что работает всегда.

→ Проп-трейдинг. Торгуешь не своими деньгами — до $200,000 чужого капитала. 80% прибыли — твоя.

→ Реальные результаты. Показываем и убытки, не только профиты. Прозрачность — наш принцип.

→ Под новичков и опытных. Полная система с нуля. Те кто уже торговал — находят ответы почему нет стабильности.

→ Методичка + 24 видеоурока + разборы сделок. Не теория ради теории — конкретный алгоритм действий.

📅 *До 30 июня — триал бесплатно. Без карты.*"""

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
            "archetype": "Чистый лист — главное преимущество",
            "desc": "У тебя нет вредных привычек и ложных паттернов. Большинство приходят в трейдинг через серию дорогостоящих ошибок. Ты можешь построить систему сразу правильно.",
            "pain": "Единственное что тебе сейчас нужно — правильный фундамент. Без него первые же сделки будут хаотичными, а рынок быстро покажет цену неподготовленности.",
            "offer": "Методичка ZCHK + бесплатный триал платформы — старт для тех кто хочет войти в профессию правильно. Без слива первого депозита."
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
            "pain": "Пока нет системы — каждый следующий депозит закончится так же как предыдущий. Опыт без правильного фундамента только закрепляет ошибки.",
            "offer": "ZCHK даёт то чего не хватает — систему. Риск-менеджмент, чтение рынка через нарратив, психология под давлением. Один слитый депозит стоит дороже курса."
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
            "offer": "ZCHK — целостная система от структуры рынка до психологии решений. Не с нуля, а поверх твоего опыта. Плюс адаптация под проп-фирмы."
        }
    }
}

# ── ПРОГРЕВ ──────────────────────────────────────────────────────────────────
WARMUP = {
    "novice": [
        "💡 *День 1. Почему 95% новичков теряют деньги*\n\nОни торгуют без системы. Видят паттерн → входят. Видят движение → входят. Никакой логики — только ощущения.\n\nРезультат предсказуем: рынок забирает деньги у тех кто не понимает почему он двигается.\n\nЕсть один вопрос который меняет всё: *«Кто стоит по другую сторону моей сделки?»*\n\nКогда начнёшь думать об этом — ты начнёшь понимать рынок.",
        "📊 *День 2. История одного студента*\n\nАртём пришёл в ZCHK три месяца назад. Никогда не торговал. Боялся потерять деньги.\n\nСейчас у него: понимание структуры рынка, первые сделки в плюс, план на первый проп-аккаунт.\n\n«Первые 3 урока дали больше понимания чем год самостоятельного изучения» — его слова.\n\nТриал бесплатно до 30 июня 👇",
        "🎯 *День 3. Последнее сообщение*\n\nЯрослав лично созванивается с каждым новым участником на 10 минут. Без продаж — просто чтобы понять твою ситуацию и показать как работает система.\n\nЭто бесплатно. Это занимает 10 минут. И это меняет понимание того куда двигаться.\n\nЗапись на звонок или триал — решение за тобой."
    ],
    "beginner": [
        "💡 *День 1. Почему твоя стратегия не работает*\n\nПаттерны — это следствие. Не причина движения цены.\n\nКогда ты торгуешь по паттернам — ты угадываешь. Угадывание даёт нестабильный результат даже при хорошем винрейте.\n\nСистема ZCHK основана на другом: *понимать почему рынок двигается* — через нарратив, ликвидность, структуру. Тогда паттерны становятся подтверждением, а не сигналом.",
        "📊 *День 2. Один слитый депозит стоит дороже*\n\nСредний трейдер теряет $2,000–$8,000 на пути к стабильности.\n\nМетодичка ZCHK стоит $24.99. Полный курс — $199.\n\nМатематика простая. Вопрос только в том — ты готов учиться на чужих ошибках или продолжаешь платить за свои?",
        "🎯 *День 3. Твой следующий шаг*\n\nЕсли ты читал наши сообщения и что-то резонирует — это не случайно.\n\nЯрослав лично созванивается на 10 минут с теми кто хочет разобраться. Покажет систему изнутри, ответит на главный вопрос.\n\nЭто последнее сообщение от нас. Решение за тобой."
    ],
    "experienced": [
        "💡 *День 1. Проблема опытных трейдеров*\n\nТы торгуешь несколько лет. У тебя есть навыки. Но нет стабильности.\n\nЭто не проблема стратегии. Это проблема фундамента — понимания *почему* рынок делает то что делает.\n\nБез этого даже правильные сделки превращаются в угадывание. Хороший месяц, плохой месяц. Без системы.",
        "📊 *День 2. Проп-трейдинг — следующий уровень*\n\nЗачем торговать на $5,000 своих когда можно торговать на $100,000–$200,000 чужих?\n\nПроп-фирмы дают капитал тем кто умеет управлять риском. 80% прибыли — твоя.\n\nВ ZCHK есть отдельный блок по адаптации под правила проп-фирм: как выстроить риск-менеджмент, как торговать в условиях дродауна, как системно пройти оценку.",
        "🎯 *День 3. 10 минут с Ярославом*\n\nЕсли ты с опытом и хочешь разобрать конкретные вопросы — Ярослав созванивается лично.\n\n10 минут. Твоя ситуация. Конкретный следующий шаг.\n\nЗапись бесплатная. Это последнее сообщение от нас."
    ]
}

# ── ХРАНИЛИЩЕ СОСТОЯНИЙ ──────────────────────────────────────────────────────
user_states = {}

def get_state(user_id):
    return user_states.get(user_id, {})

def set_state(user_id, state):
    user_states[user_id] = state

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
        f"Привет, {user.first_name}! 👋\n\n"
        f"Я бот ZCHK Capital платформы по трейдингу. Готовим к проп-трейдингу и торговле личным капиталом.\n\n"
        f"5 вопросов и ты получишь персональный разбор своей ситуации.\n\n"
        f"*Сколько ты уже в трейдинге?*",
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup(kb)
    )

async def button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user = update.effective_user
    data = query.data
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
            # state потерян — просим начать заново
            await query.edit_message_text(
                "Что-то пошло не так. Напиши /start чтобы начать заново.",
                parse_mode="Markdown"
            )
            return
        state["answers"].append(ans_idx)
        state["step"] += 1
        set_state(user.id, state)

        track = TRACKS[state["track"]]
        if state["step"] < len(track["questions"]):
            await send_question(query, context, state)
        else:
            await send_result(query, context, state, user)

    # История Ярослава
    elif data == "show_story":
        kb = [
            [InlineKeyboardButton("⚡️ Почему ZCHK →", callback_data="show_why")],
        ]
        await query.edit_message_text(STORY_TEXT, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(kb))

    # Почему мы
    elif data == "show_why":
        kb = [
            [InlineKeyboardButton("📞 Записаться на звонок с Ярославом", url=CALENDLY_URL)],
            [InlineKeyboardButton("🚀 Разобраться самостоятельно на платформе", url=PLATFORM_URL)],
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
    YAROSLAV_PHOTO = "https://zchkcapital.com/hero-photo.webp"
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
        [InlineKeyboardButton("👤 История Ярослава →", callback_data="show_story")],
    ]
    await context.bot.send_message(
        chat_id=chat_id,
        text=(
            f"✅ *{r['archetype']}*\n\n"
            f"{r['desc']}\n\n"
            f"_{r['pain']}_\n\n"
            f"━━━━━━━━━━━━━━\n"
            f"*Рекомендация:*\n{r['offer']}\n\n"
            f"📅 До 30 июня — триал *бесплатно*\n"
            f"Без карты · Регистрация за 30 секунд"
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
        [InlineKeyboardButton("🚀 Протестировать платформу", url=PLATFORM_URL)],
        [InlineKeyboardButton("📞 Записаться на звонок с Ярославом", url=CALENDLY_URL)],
        [InlineKeyboardButton("💬 Написать менеджеру", url=MANAGER_URL)],
    ]
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
