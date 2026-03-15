import os
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler, ContextTypes

# ===== Переменные окружения =====
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

# ===== Тексты =====
WELCOME_TEXT = """
Тест на профессию 2026UP 🚀

Этот тест лучше проходить после бесплатного курса «Введение в Web3».

Вы уже прошли бесплатный курс?
"""

START_TEST_TEXT = """
Отлично. Тогда давайте определим, какое направление в Web3 подходит вам больше всего.

Тест состоит из 9 коротких вопросов.
Отвечайте интуитивно — так результат будет точнее.
"""

QUESTIONS = [
    {
        "question": "1. Что вам обычно даётся легче всего?",
        "options": [
            ("A", "Понимать людей, поддерживать контакт и помогать им"),
            ("B", "Придумывать идеи, как привлечь внимание к проекту"),
            ("C", "Находить возможности, договариваться и продвигать интересы"),
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
            ("A", "Люди довольны, вовлечены и остаются в контакте"),
            ("B", "Проект растёт, о нём начинают говорить и узнавать"),
            ("C", "Появляются новые партнёрства, возможности и реальные договорённости"),
        ],
    },
    {
        "question": "4. Если вам дают новый проект, что интереснее сделать в первую очередь?",
        "options": [
            ("A", "Понять аудиторию и как с ней выстроить доверие"),
            ("B", "Подумать, как лучше упаковать и продвинуть проект"),
            ("C", "Понять, с кем можно быстро сделать сильные партнёрства"),
        ],
    },
    {
        "question": "5. Какой формат задач вам ближе?",
        "options": [
            ("A", "Много общения, поддержка людей, ответы и вовлечение"),
            ("B", "Контент, идеи, продвижение, работа с вниманием аудитории"),
            ("C", "Переговоры, партнёры, новые возможности и развитие связей"),
        ],
    },
    {
        "question": "6. Как вы чаще всего принимаете решения в работе?",
        "options": [
            ("A", "Думаю, как это повлияет на людей и отношения"),
            ("B", "Думаю, как это поможет росту, образу и продвижению"),
            ("C", "Думаю, какой практический результат и новые возможности это даст"),
        ],
    },
    {
        "question": "7. Какая обратная связь о вас звучит наиболее правдоподобно?",
        "options": [
            ("A", "С тобой легко общаться, ты умеешь слышать людей"),
            ("B", "У тебя сильное чувство идеи, упаковки и продвижения"),
            ("C", "Ты умеешь договариваться и двигать дела вперёд"),
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
            ("A", "Быть лицом общения между проектом и аудиторией"),
            ("B", "Отвечать за рост, маркетинг и интерес к проекту"),
            ("C", "Открывать проекту новые возможности через связи и сотрудничество"),
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

RESULT_TEXTS = {
    "A": {
        "title": "Ваш основной трек — Community Manager",
        "body": (
            "Вам ближе работа с людьми, коммуникация и выстраивание доверия.\n\n"
            "Скорее всего, вы хорошо чувствуете аудиторию, умеете поддерживать контакт "
            "и создавать вовлечённость вокруг проекта."
        ),
    },
    "B": {
        "title": "Ваш основной трек — Web3 Marketing",
        "body": (
            "Вам ближе рост, идеи, упаковка и продвижение проекта.\n\n"
            "Скорее всего, вы мыслите категориями внимания аудитории, интереса к продукту "
            "и того, как сделать проект заметнее."
        ),
    },
    "C": {
        "title": "Ваш основной трек — Business Development",
        "body": (
            "Вам ближе развитие через возможности, связи и переговоры.\n\n"
            "Скорее всего, вы умеете видеть точки роста, быстро ориентируетесь в новых контактах "
            "и чувствуете себя уверенно в коммуникации с партнёрами."
        ),
    },
}

def get_entry_keyboard():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("Да, пройти тест", callback_data="passed_course_yes")],
        [InlineKeyboardButton("Сначала пройти курс", url=COURSE_URL)],
    ])

def build_question_text(index):
    question_data = QUESTIONS[index]
    lines = [f"Вопрос {index + 1} из {len(QUESTIONS)}", "", question_data["question"], ""]
    for code, text in question_data["options"]:
        lines.append(f"{code}. {text}")
    return "\n".join(lines)

def build_question_keyboard(index):
    return InlineKeyboardMarkup([[
        InlineKeyboardButton("A", callback_data=f"answer:{index}:A"),
        InlineKeyboardButton("B", callback_data=f"answer:{index}:B"),
        InlineKeyboardButton("C", callback_data=f"answer:{index}:C"),
    ]])

def get_result_keyboard(primary_code, secondary_code=None):
    rows = [
        [InlineKeyboardButton(f"Открыть программу: {ROLE_NAMES[primary_code]}", callback_data=f"open_program:{primary_code}")]
    ]

    if secondary_code and secondary_code != primary_code:
        rows.append([InlineKeyboardButton(f"Альтернативно: {ROLE_NAMES[secondary_code]}", callback_data=f"open_program:{secondary_code}")])

    rows.append([InlineKeyboardButton("Задать вопрос менеджеру", callback_data="contact_manager")])
    rows.append([InlineKeyboardButton("Пройти тест заново", callback_data="restart_test")])

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

    title = RESULT_TEXTS[primary_code]["title"]
    body = RESULT_TEXTS[primary_code]["body"]

    extra = ""
    if secondary_code and secondary_code != primary_code:
        extra = f"\n\nДополнительно вам может подойти: {ROLE_NAMES[secondary_code]}"

    score_line = (
        f"\n\nВаш профиль по результатам теста:\n"
        f"• Community Manager: {scores['A']}\n"
        f"• Web3 Marketing: {scores['B']}\n"
        f"• Business Development: {scores['C']}"
    )

    final_text = (
        f"{title}\n\n"
        f"{body}"
        f"{extra}"
        f"{score_line}\n\n"
        "Следующий шаг — изучить программу глубже и выбрать направление, с которого вы хотите начать."
    )

    return primary_code, final_text, secondary_code

async def send_result_to_admin(user, scores, primary_code, secondary_code, context):
    username = f"@{user.username}" if user.username else "без username"

    text = (
        "📊 Новый результат теста 2026UP\n\n"
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

async def notify_admin_click(user, action_text, context):
    username = f"@{user.username}" if user.username else "без username"
    text = (
        "🟡 Действие после теста\n\n"
        f"👤 Имя: {user.first_name or '-'}\n"
        f"🔗 Username: {username}\n"
        f"🆔 Telegram ID: {user.id}\n\n"
        f"Действие: {action_text}"
    )
    await context.bot.send_message(chat_id=ADMIN_CHAT_ID, text=text)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data.clear()
    await update.message.reply_text(WELCOME_TEXT, reply_markup=get_entry_keyboard())

async def handle_start_test(query, context):
    context.user_data["scores"] = {"A": 0, "B": 0, "C": 0}
    context.user_data["question_index"] = 0

    await query.message.edit_text(
        START_TEST_TEXT + "\n\n" + build_question_text(0),
        reply_markup=build_question_keyboard(0)
    )

async def handle_answer(query, context, question_index, answer_code):
    current_index = context.user_data.get("question_index")

    if current_index is None or question_index != current_index:
        await query.answer("Этот вопрос уже обработан.", show_alert=False)
        return

    scores = context.user_data.get("scores", {"A": 0, "B": 0, "C": 0})
    scores[answer_code] += 1
    context.user_data["scores"] = scores

    next_index = question_index + 1
    context.user_data["question_index"] = next_index

    if next_index >= len(QUESTIONS):
        primary_code, result_text, secondary_code = format_result(scores)
        context.user_data["primary_code"] = primary_code
        context.user_data["secondary_code"] = secondary_code

        await send_result_to_admin(
            user=query.from_user,
            scores=scores,
            primary_code=primary_code,
            secondary_code=secondary_code,
            context=context,
        )

        await query.message.edit_text(
            result_text,
            reply_markup=get_result_keyboard(primary_code, secondary_code)
        )
        return

    await query.message.edit_text(
        build_question_text(next_index),
        reply_markup=build_question_keyboard(next_index)
    )

async def handle_open_program(query, context, role_code):
    role_name = ROLE_NAMES[role_code]
    url = ROLE_URLS[role_code]

    await notify_admin_click(query.from_user, f"Открыл программу: {role_name}", context)

    text = (
        f"Вы выбрали направление: {role_name}\n\n"
        "Откройте программу по ссылке ниже:"
    )

    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton(f"Перейти к программе: {role_name}", url=url)],
        [InlineKeyboardButton("Задать вопрос менеджеру", callback_data="contact_manager")]
    ])

    await query.message.reply_text(text, reply_markup=keyboard)

async def handle_contact_manager(query, context):
    await notify_admin_click(query.from_user, "Нажал кнопку: Задать вопрос менеджеру", context)

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
        await handle_start_test(query, context)
        return

    if data.startswith("answer:"):
        _, question_index, answer_code = data.split(":")
        await handle_answer(query, context, int(question_index), answer_code)
        return

    if data.startswith("open_program:"):
        _, role_code = data.split(":")
        await handle_open_program(query, context, role_code)
        return

    if data == "contact_manager":
        await handle_contact_manager(query, context)
        return

def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(button_handler))

    print("2026UP test bot started...")
    app.run_polling()

if __name__ == "__main__":
    main()
