import os
import json
import sqlite3
import asyncio
from datetime import datetime

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler, ContextTypes
from telegram.error import BadRequest


# =========================
# ENV
# =========================
BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_CHAT_ID_RAW = os.getenv("ADMIN_CHAT_ID")

if not BOT_TOKEN:
    raise ValueError("Не найдена переменная окружения BOT_TOKEN")

if not ADMIN_CHAT_ID_RAW:
    raise ValueError("Не найдена переменная окружения ADMIN_CHAT_ID")

try:
    ADMIN_CHAT_ID = int(ADMIN_CHAT_ID_RAW)
except ValueError:
    raise ValueError("ADMIN_CHAT_ID должен быть числом, например: 123456789 или -1001234567890")

COURSE_URL = os.getenv("COURSE_URL", "https://t.me/your_course_channel")
COMMUNITY_URL = os.getenv("COMMUNITY_URL", "https://t.me/your_channel_post_community")
MARKETING_URL = os.getenv("MARKETING_URL", "https://t.me/your_channel_post_marketing")
BD_URL = os.getenv("BD_URL", "https://t.me/your_channel_post_bd")
MANAGER_URL = os.getenv("MANAGER_URL", "https://t.me/your_manager_username")

DB_PATH = os.getenv("DB_PATH", "2026up_test_bot.db")
FOLLOWUP_DELAY_SECONDS = int(os.getenv("FOLLOWUP_DELAY_SECONDS", "900"))


# =========================
# TEXTS
# =========================
WELCOME_TEXT = """
Тест 2026UP: какая профессия в Web3 подходит вам больше всего? 🚀

Пройдите 9 коротких вопросов и получите персональную рекомендацию:
• Community Manager
• Web3 Marketing
• Business Development

Тест займет около 2 минут.

Вы уже прошли бесплатный курс «Введение в Web3»?
"""

START_TEST_TEXT = """
Отлично. Начнём.

Отвечайте интуитивно — так результат будет точнее.
"""

RESUME_TEXT = """
У вас есть незавершённый тест.

Нажмите кнопку ниже, чтобы продолжить с того места, где вы остановились.
"""

ANALYSIS_STEPS = [
    "Анализируем ваши ответы…",
    "Сопоставляем ваши сильные стороны с направлениями Web3…",
    "Готовим персональную рекомендацию…",
]

FOLLOWUP_TEXT = """
Вы уже получили результат теста 2026UP.

Если хотите, мы поможем понять, с какого направления лучше начать именно вам.
"""

QUESTIONS = [
    {
        "question": "1. Что вам обычно даётся легче всего?",
        "options": [
            ("B", "Придумывать идеи, как привлечь внимание к проекту"),
            ("C", "Находить возможности, договариваться и продвигать интересы"),
            ("A", "Понимать людей, поддерживать контакт и помогать им"),
        ],
    },
    {
        "question": "2. В команде вы чаще всего оказываетесь человеком, который…",
        "options": [
            ("A", "Следит, чтобы всем было понятно и комфортно"),
            ("B", "Предлагает идеи, как сделать проект заметнее и интереснее"),
            ("C", "Берёт инициативу и двигает вопрос вперёд через связи и договорённости"),
        ],
    },
    {
        "question": "3. Какой результат работы приносит вам больше удовлетворения?",
        "options": [
            ("C", "Появляются новые партнёрства, возможности и реальные договорённости"),
            ("A", "Люди довольны, вовлечены и остаются в контакте"),
            ("B", "Проект растёт, о нём начинают говорить и узнавать"),
        ],
    },
    {
        "question": "4. Если вам дают новый проект, что интереснее сделать в первую очередь?",
        "options": [
            ("B", "Подумать, как лучше упаковать и продвинуть проект"),
            ("A", "Понять аудиторию и как с ней выстроить доверие"),
            ("C", "Понять, с кем можно быстро сделать сильные партнёрства"),
        ],
    },
    {
        "question": "5. Какой формат задач вам ближе?",
        "options": [
            ("C", "Переговоры, партнёры, новые возможности и развитие связей"),
            ("B", "Контент, идеи, продвижение, работа с вниманием аудитории"),
            ("A", "Много общения, поддержка людей, ответы и вовлечение"),
        ],
    },
    {
        "question": "6. Как вы чаще всего принимаете решения в работе?",
        "options": [
            ("A", "Думаю, как это повлияет на людей и отношения"),
            ("C", "Думаю, какой практический результат и новые возможности это даст"),
            ("B", "Думаю, как это поможет росту, образу и продвижению"),
        ],
    },
    {
        "question": "7. Какая обратная связь о вас звучит наиболее правдоподобно?",
        "options": [
            ("B", "У тебя сильное чувство идеи, упаковки и продвижения"),
            ("C", "Ты умеешь договариваться и двигать дела вперёд"),
            ("A", "С тобой легко общаться, ты умеешь слышать людей"),
        ],
    },
    {
        "question": "8. В новой сфере вас больше всего привлекает…",
        "options": [
            ("A", "Люди, комьюнити и атмосфера вокруг проекта"),
            ("B", "Идеи, тренды, рост внимания и образ бренда"),
            ("C", "Возможности, связи, сделки и развитие через партнёрства"),
        ],
    },
    {
        "question": "9. Если представить вашу идеальную роль в Web3, что ближе?",
        "options": [
            ("C", "Открывать проекту новые возможности через связи и сотрудничество"),
            ("A", "Быть лицом общения между проектом и аудиторией"),
            ("B", "Отвечать за рост, маркетинг и интерес к проекту"),
        ],
    },
]

ROLE_NAMES = {
    "A": "Community Manager",
    "B": "Web3 Marketing",
    "C": "Business Development",
}

ROLE_URLS = {
    "A": COMMUNITY_URL,
    "B": MARKETING_URL,
    "C": BD_URL,
}

ROLE_SALARY = {
    "A": "от $1500 до $5000+",
    "B": "от $2000 до $7000+",
    "C": "от $3000 до $8000+",
}

ROLE_WHAT_YOU_DO = {
    "A": "Вести комьюнити, общаться с аудиторией, поддерживать активность и вовлечение.",
    "B": "Продвигать проекты, работать с контентом, маркетинговыми кампаниями и ростом аудитории.",
    "C": "Искать партнёров, запускать коллаборации, выстраивать связи и открывать проекту новые возможности роста.",
}

ROLE_WHY = {
    "A": "Вам ближе работа с людьми, коммуникация и выстраивание доверия.",
    "B": "Вам ближе рост, идеи, упаковка и продвижение проекта.",
    "C": "Вам ближе развитие через возможности, связи и переговоры.",
}


# =========================
# DB
# =========================
def now_str():
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def get_conn():
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_conn()
    cur = conn.cursor()

    cur.execute("""
        CREATE TABLE IF NOT EXISTS user_sessions (
            user_id INTEGER PRIMARY KEY,
            current_index INTEGER NOT NULL,
            scores_json TEXT NOT NULL,
            history_json TEXT NOT NULL,
            primary_code TEXT,
            secondary_code TEXT,
            result_ready INTEGER NOT NULL DEFAULT 0,
            engaged_after_result INTEGER NOT NULL DEFAULT 0,
            followup_sent INTEGER NOT NULL DEFAULT 0,
            updated_at TEXT NOT NULL
        )
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS test_results (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            username TEXT,
            first_name TEXT,
            primary_code TEXT NOT NULL,
            secondary_code TEXT,
            scores_json TEXT NOT NULL,
            created_at TEXT NOT NULL
        )
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS user_actions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            username TEXT,
            first_name TEXT,
            action_text TEXT NOT NULL,
            created_at TEXT NOT NULL
        )
    """)

    conn.commit()
    conn.close()


def save_session(
    user_id,
    current_index,
    scores,
    history,
    primary_code=None,
    secondary_code=None,
    result_ready=0,
    engaged_after_result=0,
    followup_sent=0,
):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO user_sessions (
            user_id, current_index, scores_json, history_json, primary_code, secondary_code,
            result_ready, engaged_after_result, followup_sent, updated_at
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(user_id) DO UPDATE SET
            current_index=excluded.current_index,
            scores_json=excluded.scores_json,
            history_json=excluded.history_json,
            primary_code=excluded.primary_code,
            secondary_code=excluded.secondary_code,
            result_ready=excluded.result_ready,
            engaged_after_result=excluded.engaged_after_result,
            followup_sent=excluded.followup_sent,
            updated_at=excluded.updated_at
    """, (
        user_id,
        current_index,
        json.dumps(scores, ensure_ascii=False),
        json.dumps(history, ensure_ascii=False),
        primary_code,
        secondary_code,
        result_ready,
        engaged_after_result,
        followup_sent,
        now_str(),
    ))
    conn.commit()
    conn.close()


def get_session(user_id):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT * FROM user_sessions WHERE user_id = ?", (user_id,))
    row = cur.fetchone()
    conn.close()

    if not row:
        return None

    return {
        "user_id": row["user_id"],
        "current_index": row["current_index"],
        "scores": json.loads(row["scores_json"]),
        "history": json.loads(row["history_json"]),
        "primary_code": row["primary_code"],
        "secondary_code": row["secondary_code"],
        "result_ready": row["result_ready"],
        "engaged_after_result": row["engaged_after_result"],
        "followup_sent": row["followup_sent"],
        "updated_at": row["updated_at"],
    }


def update_result_engagement(user_id, engaged=None, followup_sent=None):
    conn = get_conn()
    cur = conn.cursor()

    fields = []
    values = []

    if engaged is not None:
        fields.append("engaged_after_result = ?")
        values.append(1 if engaged else 0)

    if followup_sent is not None:
        fields.append("followup_sent = ?")
        values.append(1 if followup_sent else 0)

    fields.append("updated_at = ?")
    values.append(now_str())
    values.append(user_id)

    query = f"UPDATE user_sessions SET {', '.join(fields)} WHERE user_id = ?"
    cur.execute(query, values)
    conn.commit()
    conn.close()


def delete_session(user_id):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("DELETE FROM user_sessions WHERE user_id = ?", (user_id,))
    conn.commit()
    conn.close()


def save_result(user, scores, primary_code, secondary_code):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO test_results (
            user_id, username, first_name, primary_code, secondary_code, scores_json, created_at
        )
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (
        user.id,
        user.username,
        user.first_name,
        primary_code,
        secondary_code,
        json.dumps(scores, ensure_ascii=False),
        now_str(),
    ))
    conn.commit()
    conn.close()


def save_action(user, action_text):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO user_actions (
            user_id, username, first_name, action_text, created_at
        )
        VALUES (?, ?, ?, ?, ?)
    """, (
        user.id,
        user.username,
        user.first_name,
        action_text,
        now_str(),
    ))
    conn.commit()
    conn.close()


# =========================
# UI / FORMAT
# =========================
async def safe_edit_message(message, text, reply_markup=None):
    try:
        await message.edit_text(text, reply_markup=reply_markup)
    except BadRequest as e:
        msg = str(e).lower()
        if "message is not modified" in msg:
            return
        if "message can't be edited" in msg or "message to edit not found" in msg:
            await message.reply_text(text, reply_markup=reply_markup)
            return
        raise


def get_entry_keyboard():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("Да, пройти тест", callback_data="passed_course_yes")],
        [InlineKeyboardButton("Сначала пройти курс", url=COURSE_URL)],
    ])


def get_resume_keyboard():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("Продолжить тест", callback_data="resume_test")],
        [InlineKeyboardButton("Начать заново", callback_data="restart_test")],
    ])


def build_question_text(index):
    question_data = QUESTIONS[index]
    minutes_left = max(1, (len(QUESTIONS) - index + 2) // 3)

    lines = [
        f"Вопрос {index + 1} из {len(QUESTIONS)}",
        f"Примерно {minutes_left} мин. до результата",
        "",
        question_data["question"],
        "",
    ]

    label_map = ["A", "B", "C"]
    for i, (_, text) in enumerate(question_data["options"]):
        lines.append(f"{label_map[i]}. {text}")

    return "\n".join(lines)


def build_question_keyboard(index):
    options = QUESTIONS[index]["options"]

    rows = [[
        InlineKeyboardButton("A", callback_data=f"answer:{index}:{options[0][0]}"),
        InlineKeyboardButton("B", callback_data=f"answer:{index}:{options[1][0]}"),
        InlineKeyboardButton("C", callback_data=f"answer:{index}:{options[2][0]}"),
    ]]

    if index > 0:
        rows.append([InlineKeyboardButton("◀️ Назад", callback_data="go_back")])

    rows.append([InlineKeyboardButton("Начать заново", callback_data="restart_test")])

    return InlineKeyboardMarkup(rows)


def get_result_keyboard(primary_code):
    return InlineKeyboardMarkup([
        [InlineKeyboardButton(f"Посмотреть программу: {ROLE_NAMES[primary_code]}", callback_data=f"open_program:{primary_code}")],
        [InlineKeyboardButton("Посмотреть другие направления", callback_data="choose_other_program")],
        [InlineKeyboardButton("Обсудить, что подойдёт именно вам", callback_data="contact_manager")],
        [InlineKeyboardButton("Пройти тест заново", callback_data="restart_test")],
    ])


def get_other_programs_keyboard(primary_code):
    rows = []
    for code in ["A", "B", "C"]:
        if code != primary_code:
            rows.append([InlineKeyboardButton(ROLE_NAMES[code], callback_data=f"open_program:{code}")])
    rows.append([InlineKeyboardButton("Обсудить, что подойдёт именно вам", callback_data="contact_manager")])
    return InlineKeyboardMarkup(rows)


def get_followup_keyboard(primary_code=None):
    rows = []
    if primary_code:
        rows.append([InlineKeyboardButton(f"Посмотреть программу: {ROLE_NAMES[primary_code]}", callback_data=f"open_program:{primary_code}")])
    rows.append([InlineKeyboardButton("Обсудить, что подойдёт именно вам", callback_data="contact_manager")])
    return InlineKeyboardMarkup(rows)


def calculate_result(scores):
    sorted_scores = sorted(scores.items(), key=lambda item: item[1], reverse=True)
    primary_code = sorted_scores[0][0]
    secondary_code = sorted_scores[1][0]

    if (sorted_scores[0][1] - sorted_scores[1][1]) > 1 or sorted_scores[1][1] == 0:
        secondary_code = None

    return primary_code, secondary_code


def format_result(scores):
    primary_code, secondary_code = calculate_result(scores)

    blocks = [
        f"{ROLE_NAMES[primary_code]}",
        "",
        "Почему подходит:",
        ROLE_WHY[primary_code],
        "",
        "Что вы будете делать:",
        ROLE_WHAT_YOU_DO[primary_code],
        "",
        "Ориентир по доходу:",
        ROLE_SALARY[primary_code],
        "",
        "Следующий шаг:",
        "посмотрите программу или обсудите, с какого направления лучше начать именно вам.",
    ]

    if secondary_code and secondary_code != primary_code:
        blocks.extend([
            "",
            f"Дополнительно вам может подойти: {ROLE_NAMES[secondary_code]}",
        ])

    blocks.extend([
        "",
        "Ваш профиль по результатам теста:",
        f"• Community Manager: {scores['A']}",
        f"• Web3 Marketing: {scores['B']}",
        f"• Business Development: {scores['C']}",
    ])

    return primary_code, "\n".join(blocks), secondary_code


# =========================
# ADMIN
# =========================
async def send_result_to_admin(user, scores, primary_code, secondary_code, context):
    username = f"@{user.username}" if user.username else "без username"

    text = (
        "📊 Новый результат теста 2026UP\n\n"
        f"⏰ Дата: {now_str()}\n"
        f"👤 Имя: {user.first_name or '-'}\n"
        f"🔗 Username: {username}\n"
        f"🆔 Telegram ID: {user.id}\n\n"
        f"🎯 Основной трек: {ROLE_NAMES[primary_code]}\n"
        f"➕ Дополнительный трек: {ROLE_NAMES[secondary_code] if secondary_code else 'нет'}\n\n"
        "Баллы:\n"
        f"• Community Manager: {scores['A']}\n"
        f"• Web3 Marketing: {scores['B']}\n"
        f"• Business Development: {scores['C']}"
    )
    await context.bot.send_message(chat_id=ADMIN_CHAT_ID, text=text)


async def safe_send_result_to_admin(user, scores, primary_code, secondary_code, context):
    try:
        await send_result_to_admin(user, scores, primary_code, secondary_code, context)
    except Exception as e:
        print(f"Failed to send result to admin: {e}")


async def notify_admin_click(user, action_text, context):
    username = f"@{user.username}" if user.username else "без username"

    text = (
        "🟡 Действие после теста\n\n"
        f"⏰ Дата: {now_str()}\n"
        f"👤 Имя: {user.first_name or '-'}\n"
        f"🔗 Username: {username}\n"
        f"🆔 Telegram ID: {user.id}\n\n"
        f"Действие: {action_text}"
    )
    await context.bot.send_message(chat_id=ADMIN_CHAT_ID, text=text)


async def safe_notify_admin_click(user, action_text, context):
    try:
        await notify_admin_click(user, action_text, context)
    except Exception as e:
        print(f"Failed to notify admin: {e}")


# =========================
# FLOW
# =========================
async def animate_analysis(message):
    for step in ANALYSIS_STEPS:
        await safe_edit_message(message, step)
        await asyncio.sleep(1.2)


async def schedule_followup(user_id, context):
    await asyncio.sleep(FOLLOWUP_DELAY_SECONDS)

    session = get_session(user_id)
    if not session:
        return

    if session["result_ready"] != 1:
        return

    if session["engaged_after_result"] == 1 or session["followup_sent"] == 1:
        return

    primary_code = session.get("primary_code")
    try:
        await context.bot.send_message(
            chat_id=user_id,
            text=FOLLOWUP_TEXT,
            reply_markup=get_followup_keyboard(primary_code)
        )
        update_result_engagement(user_id, followup_sent=True)
    except Exception as e:
        print(f"Failed to send followup: {e}")


# =========================
# HANDLERS
# =========================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    session = get_session(update.effective_user.id)

    if session and session["current_index"] < len(QUESTIONS):
        save_action(update.effective_user, f"Вернулся в бот, незавершённый тест на вопросе {session['current_index'] + 1}")
        await update.message.reply_text(RESUME_TEXT, reply_markup=get_resume_keyboard())
        return

    await update.message.reply_text(WELCOME_TEXT, reply_markup=get_entry_keyboard())


async def resume(update: Update, context: ContextTypes.DEFAULT_TYPE):
    session = get_session(update.effective_user.id)

    if not session:
        await update.message.reply_text("У вас нет незавершённого теста. Нажмите /start.")
        return

    index = session["current_index"]

    if index >= len(QUESTIONS):
        await update.message.reply_text("Тест уже завершён. Нажмите /start, чтобы пройти заново.")
        return

    save_action(update.effective_user, f"Продолжил тест с вопроса {index + 1}")

    await update.message.reply_text(
        build_question_text(index),
        reply_markup=build_question_keyboard(index)
    )


async def handle_start_test(query, context):
    user = query.from_user
    scores = {"A": 0, "B": 0, "C": 0}
    history = []

    save_session(user.id, 0, scores, history)
    save_action(user, "Начал тест")

    await safe_edit_message(
        query.message,
        START_TEST_TEXT + "\n\n" + build_question_text(0),
        reply_markup=build_question_keyboard(0)
    )


async def handle_resume_test(query, context):
    user = query.from_user
    session = get_session(user.id)

    if not session:
        await query.message.reply_text("Сессия не найдена. Нажмите /start.")
        return

    index = session["current_index"]

    if index >= len(QUESTIONS):
        await query.message.reply_text("Тест уже завершён. Нажмите /start, чтобы пройти заново.")
        return

    save_action(user, f"Вернулся к тесту на вопросе {index + 1}")

    await safe_edit_message(
        query.message,
        build_question_text(index),
        reply_markup=build_question_keyboard(index)
    )


async def handle_answer(query, context, question_index, answer_code):
    user = query.from_user
    session = get_session(user.id)

    if not session:
        await query.answer("Сессия теста устарела. Нажмите /start, чтобы начать заново.", show_alert=True)
        return

    current_index = session["current_index"]
    scores = session["scores"]
    history = session["history"]

    if question_index != current_index:
        await query.answer("Этот вопрос уже обработан.", show_alert=False)
        return

    scores[answer_code] += 1
    history.append(answer_code)

    next_index = question_index + 1

    if next_index == 3:
        save_action(user, "Дошёл до вопроса 3")

    if next_index == 6:
        save_action(user, "Дошёл до вопроса 6")

    if next_index >= len(QUESTIONS):
        primary_code, result_text, secondary_code = format_result(scores)

        save_session(
            user.id,
            len(QUESTIONS),
            scores,
            history,
            primary_code,
            secondary_code,
            result_ready=1,
            engaged_after_result=0,
            followup_sent=0,
        )
        save_result(user, scores, primary_code, secondary_code)
        save_action(user, "Завершил тест")

        await animate_analysis(query.message)

        # Сначала показываем результат пользователю
        await safe_edit_message(
            query.message,
            result_text,
            reply_markup=get_result_keyboard(primary_code)
        )

        # Потом отправляем админу
        await safe_send_result_to_admin(
            user=user,
            scores=scores,
            primary_code=primary_code,
            secondary_code=secondary_code,
            context=context,
        )

        asyncio.create_task(schedule_followup(user.id, context))
        return

    save_session(
        user.id,
        next_index,
        scores,
        history,
        result_ready=0,
        engaged_after_result=0,
        followup_sent=0,
    )

    await safe_edit_message(
        query.message,
        build_question_text(next_index),
        reply_markup=build_question_keyboard(next_index)
    )


async def handle_go_back(query, context):
    user = query.from_user
    session = get_session(user.id)

    if not session:
        await query.answer("Сессия теста устарела. Нажмите /start, чтобы начать заново.", show_alert=True)
        return

    current_index = session["current_index"]
    scores = session["scores"]
    history = session["history"]

    if current_index <= 0 or not history:
        await query.answer("Назад вернуться нельзя.", show_alert=False)
        return

    last_answer = history.pop()
    scores[last_answer] -= 1
    previous_index = current_index - 1

    save_session(
        user.id,
        previous_index,
        scores,
        history,
        primary_code=session.get("primary_code"),
        secondary_code=session.get("secondary_code"),
        result_ready=0,
        engaged_after_result=0,
        followup_sent=0,
    )
    save_action(user, f"Вернулся назад на вопрос {previous_index + 1}")

    await safe_edit_message(
        query.message,
        build_question_text(previous_index),
        reply_markup=build_question_keyboard(previous_index)
    )


async def handle_open_program(query, context, role_code):
    role_name = ROLE_NAMES[role_code]
    url = ROLE_URLS[role_code]

    update_result_engagement(query.from_user.id, engaged=True)
    save_action(query.from_user, f"Открыл программу: {role_name}")
    await safe_notify_admin_click(query.from_user, f"Открыл программу: {role_name}", context)

    text = (
        f"Вы выбрали направление: {role_name}\n\n"
        "Это направление подходит вам не случайно.\n"
        "Откройте программу и посмотрите, как можно начать путь именно с этого трека."
    )

    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton(f"Перейти к программе: {role_name}", url=url)],
        [InlineKeyboardButton("Обсудить, что подойдёт именно вам", callback_data="contact_manager")]
    ])

    await query.message.reply_text(text, reply_markup=keyboard)


async def handle_choose_other_program(query, context):
    session = get_session(query.from_user.id)

    if not session or not session.get("primary_code"):
        await query.message.reply_text("Сначала пройдите тест.")
        return

    primary_code = session["primary_code"]

    update_result_engagement(query.from_user.id, engaged=True)
    save_action(query.from_user, "Нажал кнопку: Посмотреть другие направления")
    await safe_notify_admin_click(query.from_user, "Нажал кнопку: Посмотреть другие направления", context)

    text = "Если хотите сравнить ваш основной результат с другими треками, выберите направление ниже."
    await query.message.reply_text(text, reply_markup=get_other_programs_keyboard(primary_code))


async def handle_contact_manager(query, context):
    update_result_engagement(query.from_user.id, engaged=True)
    save_action(query.from_user, "Нажал кнопку: Обсудить, что подойдёт именно вам")
    await safe_notify_admin_click(query.from_user, "Нажал кнопку: Обсудить, что подойдёт именно вам", context)

    text = (
        "Если хотите, мы поможем выбрать подходящее направление и ответим на ваши вопросы.\n\n"
        "Нажмите кнопку ниже, чтобы написать менеджеру."
    )

    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("Написать менеджеру", url=MANAGER_URL)]
    ])

    await query.message.reply_text(text, reply_markup=keyboard)


async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    data = query.data

    if data in ("passed_course_yes", "restart_test"):
        if data == "restart_test":
            delete_session(query.from_user.id)
            save_action(query.from_user, "Нажал кнопку: Начать заново")
        await handle_start_test(query, context)
        return

    if data == "resume_test":
        await handle_resume_test(query, context)
        return

    if data == "go_back":
        await handle_go_back(query, context)
        return

    if data.startswith("answer:"):
        _, question_index, answer_code = data.split(":")
        await handle_answer(query, context, int(question_index), answer_code)
        return

    if data.startswith("open_program:"):
        _, role_code = data.split(":")
        await handle_open_program(query, context, role_code)
        return

    if data == "choose_other_program":
        await handle_choose_other_program(query, context)
        return

    if data == "contact_manager":
        await handle_contact_manager(query, context)
        return


def main():
    init_db()

    app = ApplicationBuilder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("resume", resume))
    app.add_handler(CallbackQueryHandler(button_handler))

    print("2026UP test bot started...")
    app.run_polling()


if __name__ == "__main__":
    main()