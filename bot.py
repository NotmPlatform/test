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
Тест 2026UP: какая профессия в Web3 подходит вам больше всего? 🚀

Пройдите 9 коротких вопросов и получите персональную рекомендацию:
• Community Manager
• Web3 Marketing
• Business Development

Тест займет около 2 минут.

Вы уже прошли бесплатный курс «Введение в Web3»?
"""

START_TEST_TEXT = """
Отлично. Тогда давайте определим, какое направление в Web3 подходит вам больше всего.

Вопросы построены так, чтобы определить ваши сильные стороны и наиболее подходящее направление в Web3.
Отвечайте интуитивно — так результат будет точнее.
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
    "A": "Ориентир по доходу на международном рынке: от $1500 до $5000+",
    "B": "Ориентир по доходу на международном рынке: от $2000 до $7000+",
    "C": "Ориентир по доходу на международном рынке: от $3000 до $8000+",
}

ROLE_WHAT_YOU_DO = {
    "A": "Что вы будете делать: вести комьюнити, общаться с аудиторией, поддерживать активность и вовлечение вокруг проекта.",
    "B": "Что вы будете делать: продвигать проекты, работать с контентом, маркетинговыми кампаниями и ростом аудитории.",
    "C": "Что вы будете делать: искать партнёров, запускать коллаборации, выстраивать связи и открывать проекту новые возможности роста.",
}

RESULT_TEXTS = {
    "A": {
        "title": "Ваш основной трек — Community Manager",
        "body": (
            "Ваши ответы показывают, что вам ближе работа с людьми, коммуникация и выстраивание доверия.\n\n"
            "Скорее всего, именно в этом направлении ваши сильные стороны смогут раскрыться лучше всего."
        ),
    },
    "B": {
        "title": "Ваш основной трек — Web3 Marketing",
        "body": (
            "Ваши ответы показывают, что вам ближе рост, идеи, упаковка и продвижение проекта.\n\n"
            "Скорее всего, именно в этом направлении ваши сильные стороны смогут раскрыться лучше всего."
        ),
    },
    "C": {
        "title": "Ваш основной трек — Business Development",
        "body": (
            "Ваши ответы показывают, что вам ближе развитие через возможности, связи и переговоры.\n\n"
            "Скорее всего, именно в этом направлении ваши сильные стороны смогут раскрыться лучше всего."
        ),
    },
}

def get_entry_keyboard():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("Да, пройти тест", callback_data="passed_course_yes")],
        [InlineKeyboardButton("Сначала пройти курс", url=COURSE_URL)],
    ])

def build_question_text(index: int) -> str:
    question_data = QUESTIONS[index]
    lines = [f"Вопрос {index + 1} из {len(QUESTIONS)}", "", question_data["question"], ""]
    # Показываем A/B/C по фактическому порядку ответов
    label_map = ["A", "B", "C"]
    for i, (_, text) in enumerate(question_data["options"]):
        lines.append(f"{label_map[i]}. {text}")
    return "\n".join(lines)

def build_question_keyboard(index: int):
    options = QUESTIONS[index]["options"]
    return InlineKeyboardMarkup([[
        InlineKeyboardButton("A", callback_data=f"answer:{index}:{options[0][0]}"),
        InlineKeyboardButton("B", callback_data=f"answer:{index}:{options[1][0]}"),
        InlineKeyboardButton("C", callback_data=f"answer:{index}:{options[2][0]}"),
    ]])

def get_result_keyboard(primary_code: str):
    return InlineKeyboardMarkup([
        [InlineKeyboardButton(f"Посмотреть программу: {ROLE_NAMES[primary_code]}", callback_data=f"open_program:{primary_code}")],
        [InlineKeyboardButton("Посмотреть другие направления", callback_data="choose_other_program")],
        [InlineKeyboardButton("Получить помощь с выбором", callback_data="contact_manager")],
        [InlineKeyboardButton("Пройти тест заново", callback_data="restart_test")],
    ])

def get_other_programs_keyboard(primary_code: str):
    rows = []
    for code in ["A", "B", "C"]:
        if code != primary_code:
            rows.append([InlineKeyboardButton(ROLE_NAMES[code], callback_data=f"open_program:{code}")])
    rows.append([InlineKeyboardButton("Получить помощь с выбором", callback_data="contact_manager")])
    return InlineKeyboardMarkup(rows)

def calculate_result(scores):
    sorted_scores = sorted(scores.items(), key=lambda item: item[1], reverse=True)
    primary_code = sorted_scores[0][0]
    secondary_code = sorted_scores[1][0]

    # Дополнительный трек показываем только если он близок к основному
    if (sorted_scores[0][1] - sorted_scores[1][1]) > 1 or sorted_scores[1][1] == 0:
        secondary_code = None

    return primary_code, secondary_code

def format_result(scores):
    primary_code, secondary_code = calculate_result(scores)

    title = RESULT_TEXTS[primary_code]["title"]
    body = RESULT_TEXTS[primary_code]["body"]
    what_you_do = ROLE_WHAT_YOU_DO[primary_code]
    salary = ROLE_SALARY[primary_code]

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
        f"{body}\n\n"
        f"{what_you_do}\n\n"
        f"{salary}\n"
        "Уровень зависит от опыта, навыков, английского языка и типа компании."
        f"{extra}"
        f"{score_line}\n\n"
        "Следующий шаг — выбрать направление и посмотреть программу глубже, пока у вас есть ясность после теста."
    )

    return primary_code, final_text, secondary_code

async def send_result_to_admin(user, scores, primary_code, secondary_code, context: ContextTypes.DEFAULT_TYPE):
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

async def notify_admin_click(user, action_text: str, context: ContextTypes.DEFAULT_TYPE):
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

async def handle_start_test(query, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["scores"] = {"A": 0, "B": 0, "C": 0}
    context.user_data["question_index"] = 0

    await query.message.edit_text(
        START_TEST_TEXT + "\n\n" + build_question_text(0),
        reply_markup=build_question_keyboard(0)
    )

async def handle_answer(query, context: ContextTypes.DEFAULT_TYPE, question_index: int, answer_code: str):
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
            reply_markup=get_result_keyboard(primary_code)
        )
        return

    await query.message.edit_text(
        build_question_text(next_index),
        reply_markup=build_question_keyboard(next_index)
    )

async def handle_open_program(query, context: ContextTypes.DEFAULT_TYPE, role_code: str):
    role_name = ROLE_NAMES[role_code]
    url = ROLE_URLS[role_code]

    await notify_admin_click(query.from_user, f"Открыл программу: {role_name}", context)

    text = (
        f"Вы выбрали направление: {role_name}\n\n"
        "Откройте программу по ссылке ниже:"
    )

    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton(f"Перейти к программе: {role_name}", url=url)],
        [InlineKeyboardButton("Получить помощь с выбором", callback_data="contact_manager")]
    ])

    await query.message.reply_text(text, reply_markup=keyboard)

async def handle_choose_other_program(query, context: ContextTypes.DEFAULT_TYPE):
    primary_code = context.user_data.get("primary_code")
    if not primary_code:
        await query.message.reply_text("Сначала пройдите тест.")
        return

    await notify_admin_click(query.from_user, "Нажал кнопку: Посмотреть другие направления", context)

    text = "Вот другие направления, которые вы тоже можете рассмотреть:"
    await query.message.reply_text(text, reply_markup=get_other_programs_keyboard(primary_code))

async def handle_contact_manager(query, context: ContextTypes.DEFAULT_TYPE):
    await notify_admin_click(query.from_user, "Нажал кнопку: Получить помощь с выбором", context)

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

    if data == "choose_other_program":
        await handle_choose_other_program(query, context)
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