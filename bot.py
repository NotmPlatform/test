import os
import json
import sqlite3
import random
import asyncio
import logging
import hashlib
from datetime import datetime
from typing import Dict, List, Tuple, Optional

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler, ContextTypes
from telegram.error import BadRequest


logging.basicConfig(
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)


# =========================
# ENV
# =========================
BOT_TOKEN = os.getenv("BOT_TOKEN", "").strip()
if not BOT_TOKEN:
    raise ValueError("Не найдена переменная окружения BOT_TOKEN")

ADMIN_CHAT_ID_RAW = os.getenv("ADMIN_CHAT_ID", "").strip()
ADMIN_CHAT_ID: Optional[int] = None
if ADMIN_CHAT_ID_RAW:
    try:
        ADMIN_CHAT_ID = int(ADMIN_CHAT_ID_RAW)
    except ValueError as e:
        raise ValueError("ADMIN_CHAT_ID должен быть числом, например 123456789 или -1001234567890") from e

TRIBUTE_CM_URL = os.getenv("TRIBUTE_CM_URL", "https://t.me/tribute/app?startapp=sQSN")
TRIBUTE_MARKETING_URL = os.getenv("TRIBUTE_MARKETING_URL", "https://t.me/tribute/app?startapp=sQVV")
TRIBUTE_BD_URL = os.getenv("TRIBUTE_BD_URL", "https://t.me/tribute/app?startapp=sQWw")
MANAGER_URL = os.getenv("MANAGER_URL", "https://t.me/BizManag")
DB_PATH = os.getenv("DB_PATH", "2026up_career_test.db")


# =========================
# ROLES
# =========================
ROLE_NAMES = {
    "A": "CM в Web3",
    "B": "Web3 Маркетолог",
    "C": "BD в Web3",
}

ROLE_PAYMENT_URLS = {
    "A": TRIBUTE_CM_URL,
    "B": TRIBUTE_MARKETING_URL,
    "C": TRIBUTE_BD_URL,
}

ROLE_WHY = {
    "A": "Вам ближе коммуникация, поддержка аудитории, чувство атмосферы и выстраивание доверия между проектом и людьми.",
    "B": "Вам ближе рост, упаковка, внимание к смыслам, продвижение и создание интереса к продукту.",
    "C": "Вам ближе развитие через связи, переговоры, партнёрства и поиск возможностей для роста проекта.",
}

ROLE_NEXT_STEP = {
    "A": "Если вам нравится общение, вовлечение, работа с комьюнити и удержание аудитории, вам стоит смотреть трек CM в Web3.",
    "B": "Если вам интересны брендинг, контент, growth, каналы привлечения и упаковка продукта, вам стоит смотреть трек Web3 Маркетолога.",
    "C": "Если вас драйвят партнёрства, выходы на новых людей, экосистемные связи и сделки, вам стоит смотреть трек BD в Web3.",
}


# =========================
# TEXTS
# =========================
WELCOME_TEXT = (
    "Тест 2026UP: какая профессия в Web3 подходит вам больше всего? 🚀\n\n"
    "Ответьте на 15 коротких вопросов и получите персональную рекомендацию по одному из направлений:\n\n"
    "• CM в Web3\n"
    "• Web3 Маркетолог\n"
    "• BD в Web3\n\n"
    "Вопросы подобраны по трём блокам:\n"
    "• психология и особенности личности\n"
    "• мышление и рабочий стиль\n"
    "• реальные ситуации из Web3\n\n"
    "В конце вы увидите основное подходящее направление, две альтернативы и сможете сразу перейти к нужному треку или написать менеджеру."
)

START_TEST_TEXT = (
    "Отлично. Начинаем.\n\n"
    "Отвечайте честно и интуитивно. В тесте нет правильных и неправильных ответов — цель понять, какая роль вам действительно ближе."
)

RESUME_TEXT = (
    "У вас есть незавершённый тест.\n\n"
    "Нажмите кнопку ниже, чтобы продолжить с того места, где вы остановились, или начните заново."
)

NO_ADMIN_WARNING = "ADMIN_CHAT_ID не указан. Результаты не будут отправляться в админ-чат."

ANALYSIS_STEPS = [
    "Ответы получены…",
    "Мы анализируем ваши ответы…",
    "Мы подбираем вам лучшую профессию…",
]


# =========================
# QUESTION BANK (60)
# =========================
PSYCHOLOGY_QUESTIONS = [
    {"question": "В новой команде вы быстрее всего проявляете себя через…", "options": [("A", "умение расположить к себе людей и наладить атмосферу"), ("B", "идеи, как сделать продукт заметнее и интереснее"), ("C", "понимание, кто на что влияет и где есть полезные связи")]},
    {"question": "Что чаще всего вызывает у вас внутренний интерес?", "options": [("A", "поведение людей и их мотивация"), ("B", "почему одни идеи цепляют, а другие нет"), ("C", "как устроены договорённости и чья выгода в них сильнее")]},
    {"question": "Когда у людей вокруг стресс, вы обычно…", "options": [("A", "стараетесь стабилизировать общение и снизить напряжение"), ("B", "думаете, как правильно подать ситуацию и сохранить восприятие"), ("C", "ищете кратчайший путь к практическому решению")]},
    {"question": "Что для вас выглядит как действительно классный рабочий день?", "options": [("A", "много живой коммуникации и понятная обратная связь от людей"), ("B", "проверка гипотез, идеи, контент и ростовые инсайты"), ("C", "полезные созвоны, новые контакты и продвижение переговоров")]},
    {"question": "Какая роль даётся вам естественнее всего?", "options": [("A", "тот, к кому приходят с вопросами и за поддержкой"), ("B", "тот, кто подсказывает, как сделать сильнее и заметнее"), ("C", "тот, кто двигает вопрос через договорённости и ресурсы")]},
    {"question": "Что вам приятнее слышать о себе?", "options": [("A", "с тобой легко и спокойно"), ("B", "у тебя классное чувство идеи и подачи"), ("C", "ты умеешь договариваться и открывать двери")]},
    {"question": "Что вас больше утомляет?", "options": [("A", "холодное отношение и плохая коммуникация внутри сообщества"), ("B", "слабая упаковка и скучная подача сильного продукта"), ("C", "упущенные возможности и отсутствие нужных контактов")]},
    {"question": "Когда вы видите новый проект, вы интуитивно оцениваете прежде всего…", "options": [("A", "какие там люди и какая атмосфера вокруг"), ("B", "как он выглядит, звучит и насколько он понятен рынку"), ("C", "кто за ним стоит и какие у него рычаги роста")]},
    {"question": "Что для вас ценнее в долгую?", "options": [("A", "лояльные люди и сильное комьюнити"), ("B", "узнаваемость и сильный бренд"), ("C", "сеть отношений, которая открывает возможности")]},
    {"question": "В условиях неопределённости вы чаще опираетесь на…", "options": [("A", "чувство людей и реакцию аудитории"), ("B", "чувство рынка, трендов и подачи"), ("C", "практический расчёт и leverage")]},
    {"question": "Что вас больше заряжает эмоционально?", "options": [("A", "видеть, как люди включаются и становятся активнее"), ("B", "видеть, как идея начинает вируситься и расти"), ("C", "видеть, как диалог превращается в реальную возможность")]},
    {"question": "В споре вам ближе…", "options": [("A", "понять позицию сторон и вернуть контакт"), ("B", "найти формулировку, которая изменит восприятие"), ("C", "найти формат, при котором все стороны что-то выигрывают")]},
    {"question": "Какая рабочая среда вам ближе?", "options": [("A", "где много взаимодействия с людьми и постоянный диалог"), ("B", "где ценятся идеи, гипотезы и экспериментирование"), ("C", "где ценятся инициативность, связи и результат через переговоры")]},
    {"question": "Что у вас чаще получается лучше других?", "options": [("A", "чувствовать настроение людей и не терять контакт"), ("B", "видеть, как улучшить подачу и сделать сильнее интерес"), ("C", "замечать, с кем и как можно создать полезное сотрудничество")]},
    {"question": "Какой комплимент кажется вам самым про вас?", "options": [("A", "ты умеешь удерживать людей рядом"), ("B", "ты умеешь запускать интерес к идее"), ("C", "ты умеешь соединять нужных людей и возможности")]},
    {"question": "Когда вы думаете о будущем росте, вас больше привлекает…", "options": [("A", "влияние через отношения и сообщество"), ("B", "влияние через идеи, бренд и внимание"), ("C", "влияние через переговоры и стратегические связи")]},
    {"question": "Что для вас особенно важно в работе?", "options": [("A", "чувствовать, что вы реально полезны людям"), ("B", "видеть измеримый рост интереса и охвата"), ("C", "видеть, что вы открываете новые возможности")]},
    {"question": "Если вам нужно быстро освоиться в новом пространстве, вы скорее…", "options": [("A", "начнёте знакомиться и понимать локальную динамику людей"), ("B", "поймёте, как там всё устроено с точки зрения внимания и подачи"), ("C", "поймёте, кто ключевые игроки и как выйти на них")]},
    {"question": "Что больше всего мешает сильному проекту, по вашему ощущению?", "options": [("A", "когда аудиторию не слышат и с ней не выстраивают отношения"), ("B", "когда продукт не умеют правильно показать рынку"), ("C", "когда проект не использует внешние связи и возможности")]},
    {"question": "Какая роль ощущается для вас наиболее естественной?", "options": [("A", "быть мостом между проектом и людьми"), ("B", "быть драйвером интереса, роста и позиционирования"), ("C", "быть человеком, который открывает проекту новые двери")]}]

THINKING_QUESTIONS = [
    {"question": "Если проект не растёт, вы в первую очередь подумаете о…", "options": [("A", "качестве обратной связи, удержании и атмосфере"), ("B", "воронке, позиционировании и каналах привлечения"), ("C", "партнёрах, дистрибуции и внешних точках роста")]},
    {"question": "Какой KPI вам интуитивно понятнее?", "options": [("A", "engagement, retention, active community"), ("B", "CTR, CAC, registrations, reach"), ("C", "количество партнёрств, integrations, deal flow")]},
    {"question": "Что вам проще структурировать?", "options": [("A", "сценарии общения, FAQ и логику работы с аудиторией"), ("B", "контент-план, воронку и growth-гипотезы"), ("C", "список приоритетных партнёров и шаги по переговорам")]},
    {"question": "Если бы вам дали ограниченный ресурс времени, вы бы поставили акцент на…", "options": [("A", "качество взаимодействия с текущей аудиторией"), ("B", "действия, которые усиливают видимость и спрос"), ("C", "действия, которые дают внешний рычаг роста")]},
    {"question": "Какой тип задач вам кажется наиболее интеллектуально интересным?", "options": [("A", "понять причины поведения людей и удержать вовлечение"), ("B", "найти сильный угол подачи и масштабировать внимание"), ("C", "найти оптимальный путь к нужному решению через переговоры")]},
    {"question": "Вы скорее сильнее в…", "options": [("A", "эмпатии, тоне и управлении коммуникацией"), ("B", "смыслах, гипотезах и понимании внимания аудитории"), ("C", "приоритизации возможностей и выходе на нужных людей")]},
    {"question": "Если нужно быстро улучшить результат, вы предпочтёте…", "options": [("A", "выявить боли текущей аудитории и наладить диалог"), ("B", "протестировать новую подачу и новые каналы"), ("C", "подключить стратегических людей и внешние ресурсы")]},
    {"question": "Что кажется вам наиболее полезным навыком в хаотичной среде?", "options": [("A", "не терять контакт с людьми и поддерживать ясность"), ("B", "быстро упаковывать идеи в понятные смыслы"), ("C", "быстро видеть leverage и принимать деловые решения")]},
    {"question": "Какой способ решения проблемы вам ближе?", "options": [("A", "разобраться с первопричиной через диалог и фидбек"), ("B", "пересобрать подход, сообщение или механику"), ("C", "изменить конфигурацию взаимодействий и найти сильный альянс")]},
    {"question": "Когда вы смотрите на рынок, вы чаще замечаете…", "options": [("A", "что люди любят, что их раздражает и на что они реагируют"), ("B", "какие смыслы, форматы и бренды выигрывают внимание"), ("C", "кто с кем связан и где есть незакрытые возможности")]},
    {"question": "Вам проще принять решение, когда вы видите…", "options": [("A", "реакции людей и обратную связь сообщества"), ("B", "данные по росту и понимание, что сработает в подаче"), ("C", "карту влияния и возможные исходы переговоров")]},
    {"question": "В идеале ваша работа должна измеряться через…", "options": [("A", "качество отношений и активность аудитории"), ("B", "привлечение внимания и рост интереса"), ("C", "новые возможности, сделки и деловой результат")]},
    {"question": "Когда вы строите план, вам естественнее начать с…", "options": [("A", "карты сегментов аудитории и сценариев общения"), ("B", "основной идеи, оффера и каналов продвижения"), ("C", "списка приоритетных контактов и партнёрского pipeline")]},
    {"question": "Что вам легче всего улучшать системно?", "options": [("A", "коммуникационные процессы и качество взаимодействия"), ("B", "ростовые механики, упаковку и маркетинговую воронку"), ("C", "деловые процессы вокруг партнёрств и выхода на рынок")]},
    {"question": "Какой тип информации для вас особенно полезен?", "options": [("A", "реальные отзывы, реакции и поведение сообщества"), ("B", "данные о спросе, конверсии и работе креативов"), ("C", "информация о ключевых людях, компаниях и их интересах")]},
    {"question": "Если нужно быстро понять, где проект теряет потенциал, вы проверите…", "options": [("A", "где рвётся связь с текущей аудиторией"), ("B", "где слабая упаковка и неработающая воронка"), ("C", "где отсутствуют сильные внешние связи и интеграции")]},
    {"question": "Ваша сильная сторона в команде — это чаще…", "options": [("A", "стабилизировать коммуникацию и быть голосом аудитории"), ("B", "видеть возможности роста и усиливать позиционирование"), ("C", "создавать полезные входы, коллаборации и деловые ходы")]},
    {"question": "Что вам приятнее строить?", "options": [("A", "долгосрочное доверие"), ("B", "сильный спрос"), ("C", "сильную сеть возможностей")]},
    {"question": "Что из этого больше похоже на ваш стиль мышления?", "options": [("A", "люди сначала"), ("B", "внимание и рост сначала"), ("C", "рычаги влияния и результат сначала")]},
    {"question": "Если бы вы выбирали между тремя типами задач, какая была бы вам ближе всего?", "options": [("A", "удержать и вовлечь текущую аудиторию"), ("B", "придумать, как резко усилить интерес к продукту"), ("C", "найти того, кто ускорит рост через сотрудничество")]}]

WEB3_PRACTICE_QUESTIONS = [
    {"question": "В Telegram-чате проекта резко начался негатив. Что вам ближе сделать первым?", "options": [("A", "успокоить тон диалога, ответить людям и вернуть доверие"), ("B", "подумать, как грамотно подать ситуацию публично"), ("C", "быстро собрать ответственных и закрыть вопрос решением")]},
    {"question": "У проекта нормальный продукт, но мало новых пользователей. Ваш первый фокус?", "options": [("A", "оживить текущую аудиторию и понять, что ей не хватает"), ("B", "усилить оффер, маркетинг и acquisition-каналы"), ("C", "найти партнёров, которые дадут доступ к новой аудитории")]},
    {"question": "Вам дали задачу принести результат за 30 дней. Что вам ближе?", "options": [("A", "повысить активность и лояльность комьюнити"), ("B", "запустить рост через контент и гипотезы"), ("C", "собрать pipeline партнёров и выйти на ключевых игроков")]},
    {"question": "В Web3-проекте упал engagement в соцсетях. Ваш первый ход?", "options": [("A", "разобраться, чего не хватает текущему комьюнити"), ("B", "пересобрать контент-стратегию и форматы"), ("C", "задействовать внешние коллаборации и новых медиапартнёров")]},
    {"question": "Биржа или проект хочет выйти на новый регион. Что вам ближе взять на себя?", "options": [("A", "адаптировать коммуникацию и работать с локальным комьюнити"), ("B", "адаптировать маркетинговые смыслы и каналы продвижения"), ("C", "выстроить локальные партнёрства, KOL-связи и экосистемные контакты")]},
    {"question": "После AMA активность не выросла. Какую гипотезу вы проверите первой?", "options": [("A", "людям не хватило вовлечения и понятного продолжения общения"), ("B", "формат и упаковка ивента были слабыми"), ("C", "на ивент пришла не та аудитория и не было сильной дистрибуции")]},
    {"question": "Проект хочет укрепить репутацию. Куда вам ближе направить усилие?", "options": [("A", "на прозрачную коммуникацию и работу с текущим сообществом"), ("B", "на сильный бренд-нарратив и качественную подачу"), ("C", "на ассоциацию с сильными партнёрами и экосистемой")]},
    {"question": "Вам нужно подготовить недельный план. Что в нём вам ближе всего?", "options": [("A", "модерация, комьюнити-активности, ответы и обратная связь"), ("B", "контент, креативы, ростовые тесты и аналитика по каналам"), ("C", "созвоны, follow-up, outreach и подготовка партнёрских предложений")]},
    {"question": "На рынке появился сильный конкурент. Ваша первая мысль?", "options": [("A", "важно сохранить лояльность текущих людей"), ("B", "нужно сильнее показать ценность и отличия продукта"), ("C", "нужно ускорить стратегические связи и усилить позиции через союзников")]},
    {"question": "Если проект запускает реферальную программу, вам интереснее всего…", "options": [("A", "понять, как сделать её понятной и приятной для сообщества"), ("B", "продумать механику роста и как её красиво упаковать"), ("C", "понять, с кем объединить запуск, чтобы усилить охват и ценность")]},
    {"question": "Внутри проекта не хватает ясности по обратной связи от аудитории. Ваш фокус?", "options": [("A", "собрать системный фидбек и структурировать проблемы людей"), ("B", "оценить, что мешает людям захотеть продукт сильнее"), ("C", "оценить, где внешние партнёры могут закрыть этот разрыв быстрее")]},
    {"question": "Проект хочет сделать коллаборацию с KOL. Что вам ближе?", "options": [("A", "подумать, как аудитория воспримет это и как удержать диалог"), ("B", "подумать, как это встроить в маркетинговую кампанию"), ("C", "вести переговоры и добиваться выгодных условий сотрудничества")]},
    {"question": "После запуска продукта в чате много одинаковых вопросов. Что делать первым?", "options": [("A", "улучшить поддержку, FAQ и тон коммуникации"), ("B", "улучшить onboarding и подачу продукта"), ("C", "подключить партнёров, которые помогут с дистрибуцией и обучением")]},
    {"question": "Если токен-проект готовит важный анонс, вам интереснее отвечать за…", "options": [("A", "качественную работу с реакцией сообщества до и после анонса"), ("B", "упаковку анонса и его маркетинговый эффект"), ("C", "внешние связи, ко-маркетинг и стратегические касания")]},
    {"question": "Если вы работаете на CEX, какой блок задач ближе вам больше всего?", "options": [("A", "комьюнити, локальные чаты, удержание и пользовательский фидбек"), ("B", "рекламные кампании, growth, медиа и KOL-активации"), ("C", "листинговые и экосистемные партнёрства, affiliate и business outreach")]},
    {"question": "Что для вас выглядит как самый сильный результат в Web3?", "options": [("A", "сообщество, которое верит проекту и остаётся с ним"), ("B", "рынок, который замечает и обсуждает проект"), ("C", "экосистема, в которой проект стал нужным игроком")]},
    {"question": "Команда хочет поднять конверсию с контента в действие. Что вам ближе сделать?", "options": [("A", "убрать непонимание и усилить контакт с текущей аудиторией"), ("B", "пересобрать контент, CTA и воронку"), ("C", "подключить правильных партнёров и совместные размещения")]},
    {"question": "В проекте начинается подготовка к офлайн-ивенту. Чем вам интереснее заняться?", "options": [("A", "работой с участниками, атмосферой и коммуникацией до, во время и после"), ("B", "упаковкой события, промо и охватом"), ("C", "поиском спонсоров, партнёров и VIP-контактов")]},
    {"question": "Проект хочет усилить присутствие в экосистеме. Вы бы начали с…", "options": [("A", "понимания, как текущее комьюнити может усилить этот рост"), ("B", "понимания, как правильно рассказать рынку новую историю"), ("C", "карты экосистемных игроков и планов по выходу на них")]},
    {"question": "Если вам нужно выбрать одну роль в запуске нового Web3-продукта, что ближе всего?", "options": [("A", "сделать так, чтобы пользователи чувствовали связь с проектом"), ("B", "сделать так, чтобы о проекте узнали и захотели его попробовать"), ("C", "сделать так, чтобы проект быстро получил сильные внешние рычаги роста")]}]


# =========================
# DB
# =========================
def now_str() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def get_conn() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn


def init_db() -> None:
    conn = get_conn()
    cur = conn.cursor()

    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS user_sessions (
            user_id INTEGER PRIMARY KEY,
            current_index INTEGER NOT NULL,
            scores_json TEXT NOT NULL,
            history_json TEXT NOT NULL,
            question_set_json TEXT NOT NULL,
            updated_at TEXT NOT NULL
        )
        """
    )

    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS test_results (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            username TEXT,
            first_name TEXT,
            scores_json TEXT NOT NULL,
            primary_code TEXT NOT NULL,
            secondary_code TEXT NOT NULL,
            third_code TEXT NOT NULL,
            created_at TEXT NOT NULL
        )
        """
    )

    conn.commit()
    conn.close()


def save_session(user_id: int, current_index: int, scores: Dict[str, int], history: List[str], question_set: List[dict]) -> None:
    conn = get_conn()
    cur = conn.cursor()
    cur.execute(
        """
        INSERT INTO user_sessions (user_id, current_index, scores_json, history_json, question_set_json, updated_at)
        VALUES (?, ?, ?, ?, ?, ?)
        ON CONFLICT(user_id) DO UPDATE SET
            current_index=excluded.current_index,
            scores_json=excluded.scores_json,
            history_json=excluded.history_json,
            question_set_json=excluded.question_set_json,
            updated_at=excluded.updated_at
        """,
        (
            user_id,
            current_index,
            json.dumps(scores, ensure_ascii=False),
            json.dumps(history, ensure_ascii=False),
            json.dumps(question_set, ensure_ascii=False),
            now_str(),
        ),
    )
    conn.commit()
    conn.close()


def get_session(user_id: int) -> Optional[dict]:
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
        "question_set": json.loads(row["question_set_json"]),
        "updated_at": row["updated_at"],
    }


def delete_session(user_id: int) -> None:
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("DELETE FROM user_sessions WHERE user_id = ?", (user_id,))
    conn.commit()
    conn.close()


def save_result(user, scores: Dict[str, int], primary_code: str, secondary_code: str, third_code: str) -> None:
    conn = get_conn()
    cur = conn.cursor()
    cur.execute(
        """
        INSERT INTO test_results (user_id, username, first_name, scores_json, primary_code, secondary_code, third_code, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            user.id,
            user.username,
            user.first_name,
            json.dumps(scores, ensure_ascii=False),
            primary_code,
            secondary_code,
            third_code,
            now_str(),
        ),
    )
    conn.commit()
    conn.close()


# =========================
# HELPERS
# =========================
def stable_question_id(question_text: str) -> str:
    return hashlib.md5(question_text.encode("utf-8")).hexdigest()


def shuffle_question(question: dict, category: str) -> dict:
    options = list(question["options"])
    random.shuffle(options)
    return {
        "qid": stable_question_id(question["question"]),
        "question": question["question"].strip(),
        "options": options,
        "category": category,
    }


def build_question_set() -> List[dict]:
    selected: List[dict] = []
    selected.extend(shuffle_question(q, "psychology") for q in random.sample(PSYCHOLOGY_QUESTIONS, 5))
    selected.extend(shuffle_question(q, "thinking") for q in random.sample(THINKING_QUESTIONS, 5))
    selected.extend(shuffle_question(q, "practice") for q in random.sample(WEB3_PRACTICE_QUESTIONS, 5))
    random.shuffle(selected)
    return selected


def compute_category_scores(question_set: List[dict], history: List[str]) -> Dict[str, Dict[str, int]]:
    category_scores = {
        "psychology": {"A": 0, "B": 0, "C": 0},
        "thinking": {"A": 0, "B": 0, "C": 0},
        "practice": {"A": 0, "B": 0, "C": 0},
    }

    for idx, answer_code in enumerate(history):
        if idx >= len(question_set):
            break
        category = question_set[idx].get("category", "practice")
        if category not in category_scores:
            category = "practice"
        if answer_code in category_scores[category]:
            category_scores[category][answer_code] += 1

    return category_scores


def deterministic_tie_value(seed: str, role_code: str) -> int:
    digest = hashlib.md5(f"{seed}:{role_code}".encode("utf-8")).hexdigest()
    return int(digest[:8], 16)


def rank_roles(scores: Dict[str, int], question_set: List[dict], history: List[str]) -> List[str]:
    category_scores = compute_category_scores(question_set, history)
    seed_payload = {
        "history": history,
        "questions": [q.get("qid") or q.get("question", "") for q in question_set],
    }
    seed = json.dumps(seed_payload, ensure_ascii=False, sort_keys=True)

    def sort_key(role_code: str) -> Tuple[int, int, int, int, int]:
        return (
            scores.get(role_code, 0),
            category_scores["practice"].get(role_code, 0),
            category_scores["thinking"].get(role_code, 0),
            category_scores["psychology"].get(role_code, 0),
            deterministic_tie_value(seed, role_code),
        )

    return sorted(["A", "B", "C"], key=sort_key, reverse=True)


def calculate_result(scores: Dict[str, int], question_set: List[dict], history: List[str]) -> Tuple[str, str, str]:
    ranked = rank_roles(scores, question_set, history)
    return ranked[0], ranked[1], ranked[2]


def detect_profile_type(scores: Dict[str, int]) -> str:
    values = sorted(scores.values(), reverse=True)
    if values[0] == values[1] == values[2]:
        return "universal"
    if values[0] == values[1]:
        return "dual"
    if values[0] - values[1] <= 1:
        return "mixed"
    return "clear"


def get_entry_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("Пройти тест", callback_data="start_test")],
    ])


def get_resume_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("Продолжить тест", callback_data="resume_test")],
        [InlineKeyboardButton("Начать заново", callback_data="restart_test")],
    ])


def build_question_text(session: dict, index: int) -> str:
    question_data = session["question_set"][index]
    total = len(session["question_set"])
    minutes_left = max(1, (total - index + 2) // 3)

    lines = [
        f"Вопрос {index + 1} из {total}",
        f"Примерно {minutes_left} мин. до результата",
        "",
        question_data["question"],
        "",
        f"A. {question_data['options'][0][1]}",
        f"B. {question_data['options'][1][1]}",
        f"C. {question_data['options'][2][1]}",
    ]
    return "\n".join(lines)


def build_question_keyboard(session: dict, index: int) -> InlineKeyboardMarkup:
    question_data = session["question_set"][index]
    rows = [[
        InlineKeyboardButton("A", callback_data=f"answer:{index}:{question_data['options'][0][0]}"),
        InlineKeyboardButton("B", callback_data=f"answer:{index}:{question_data['options'][1][0]}"),
        InlineKeyboardButton("C", callback_data=f"answer:{index}:{question_data['options'][2][0]}"),
    ]]

    if index > 0:
        rows.append([InlineKeyboardButton("◀️ Назад", callback_data="go_back")])

    rows.append([InlineKeyboardButton("Начать заново", callback_data="restart_test")])
    return InlineKeyboardMarkup(rows)


def get_result_keyboard(primary_code: str, secondary_code: str, third_code: str) -> InlineKeyboardMarkup:
    rows = []
    for code in [primary_code, secondary_code, third_code]:
        rows.append([InlineKeyboardButton(f"Выбрать {ROLE_NAMES[code]}", url=ROLE_PAYMENT_URLS[code])])
    rows.append([InlineKeyboardButton("Нужна помощь менеджера", url=MANAGER_URL)])
    rows.append([InlineKeyboardButton("Пройти тест заново", callback_data="restart_test")])
    return InlineKeyboardMarkup(rows)


def format_result(scores: Dict[str, int], question_set: List[dict], history: List[str]) -> Tuple[str, str, str, str]:
    primary_code, secondary_code, third_code = calculate_result(scores, question_set, history)
    profile_type = detect_profile_type(scores)

    lines: List[str] = []

    if profile_type == "universal":
        lines.extend([
            "Ваш результат: универсальный профиль в Web3 🚀",
            "",
            "У вас практически одинаково выражены качества сразу для трёх направлений: работа с людьми, рост и упаковка, а также партнёрства и переговоры.",
            "",
            f"Если выбирать первый трек для старта, сейчас чаще всего вам будет ближе: {ROLE_NAMES[primary_code]}",
            "",
        ])
    elif profile_type == "dual":
        lines.extend([
            f"Ваш результат: {ROLE_NAMES[primary_code]} 🚀",
            "",
            f"У вас очень близкий профиль между направлениями {ROLE_NAMES[primary_code]} и {ROLE_NAMES[secondary_code]}.",
            f"Если нужно выбрать один основной стартовый трек, сейчас немного ближе выглядит: {ROLE_NAMES[primary_code]}.",
            "",
            "Почему это направление подходит вам лучше всего:",
            ROLE_WHY[primary_code],
            "",
        ])
    else:
        lines.extend([
            f"Ваш результат: {ROLE_NAMES[primary_code]} 🚀",
            "",
            "Почему это направление подходит вам лучше всего:",
            ROLE_WHY[primary_code],
            "",
        ])
        if profile_type == "mixed":
            lines.extend([
                "У вас смешанный профиль.",
                f"Основной фокус — {ROLE_NAMES[primary_code]}, но второе направление тоже выражено довольно сильно: {ROLE_NAMES[secondary_code]}.",
                "",
            ])

    lines.extend([
        "Также вам могут подойти:",
        f"• {ROLE_NAMES[secondary_code]}",
        f"• {ROLE_NAMES[third_code]}",
        "",
        "Что делать дальше:",
        ROLE_NEXT_STEP[primary_code],
        "",
        "Ваши баллы:",
        f"• CM в Web3: {scores['A']}",
        f"• Web3 Маркетолог: {scores['B']}",
        f"• BD в Web3: {scores['C']}",
        "",
        "Ниже вы можете выбрать любой из трёх треков или обратиться к менеджеру за помощью.",
    ])

    return primary_code, secondary_code, third_code, "\n".join(lines)


async def safe_edit_message(message, text: str, reply_markup=None) -> None:
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


async def send_result_to_admin(user, scores: Dict[str, int], primary_code: str, secondary_code: str, third_code: str, context: ContextTypes.DEFAULT_TYPE) -> None:
    if ADMIN_CHAT_ID is None:
        return

    username = f"@{user.username}" if user.username else "без username"
    text = (
        "📊 Новый результат теста 2026UP\n\n"
        f"⏰ Дата: {now_str()}\n"
        f"👤 Имя: {user.first_name or '-'}\n"
        f"🔗 Username: {username}\n"
        f"🆔 Telegram ID: {user.id}\n\n"
        f"🎯 Основной трек: {ROLE_NAMES[primary_code]}\n"
        f"➕ Альтернатива 1: {ROLE_NAMES[secondary_code]}\n"
        f"➕ Альтернатива 2: {ROLE_NAMES[third_code]}\n\n"
        "Баллы:\n"
        f"• CM в Web3: {scores['A']}\n"
        f"• Web3 Маркетолог: {scores['B']}\n"
        f"• BD в Web3: {scores['C']}"
    )
    await context.bot.send_message(chat_id=ADMIN_CHAT_ID, text=text)


# =========================
# HANDLERS
# =========================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if update.message is None or update.effective_user is None:
        return

    session = get_session(update.effective_user.id)
    if session and session["current_index"] < len(session["question_set"]):
        await update.message.reply_text(RESUME_TEXT, reply_markup=get_resume_keyboard())
        return

    await update.message.reply_text(WELCOME_TEXT, reply_markup=get_entry_keyboard())


async def handle_start_test(query) -> None:
    question_set = build_question_set()
    scores = {"A": 0, "B": 0, "C": 0}
    history: List[str] = []
    save_session(query.from_user.id, 0, scores, history, question_set)
    session = get_session(query.from_user.id)
    if session is None:
        await query.message.reply_text("Не удалось запустить тест. Попробуйте снова.")
        return

    await safe_edit_message(
        query.message,
        START_TEST_TEXT + "\n\n" + build_question_text(session, 0),
        reply_markup=build_question_keyboard(session, 0),
    )


async def handle_resume_test(query) -> None:
    session = get_session(query.from_user.id)
    if not session:
        await query.message.reply_text("Незавершённый тест не найден. Нажмите /start.")
        return

    index = session["current_index"]
    if index >= len(session["question_set"]):
        await query.message.reply_text("Тест уже завершён. Нажмите /start, чтобы пройти заново.")
        return

    await safe_edit_message(
        query.message,
        build_question_text(session, index),
        reply_markup=build_question_keyboard(session, index),
    )


async def handle_restart_test(query) -> None:
    delete_session(query.from_user.id)
    await safe_edit_message(query.message, WELCOME_TEXT, reply_markup=get_entry_keyboard())


async def handle_go_back(query) -> None:
    session = get_session(query.from_user.id)
    if not session:
        await query.answer("Сессия теста устарела. Нажмите /start, чтобы начать заново.", show_alert=True)
        return

    current_index = session["current_index"]
    history = session["history"]
    scores = session["scores"]
    question_set = session["question_set"]

    if current_index <= 0 or not history:
        await query.answer("Назад вернуться нельзя.", show_alert=False)
        return

    last_answer = history.pop()
    if last_answer in scores and scores[last_answer] > 0:
        scores[last_answer] -= 1

    previous_index = current_index - 1
    save_session(query.from_user.id, previous_index, scores, history, question_set)
    updated_session = get_session(query.from_user.id)
    if updated_session is None:
        await query.message.reply_text("Не удалось вернуть предыдущий вопрос. Попробуйте /start.")
        return

    await safe_edit_message(
        query.message,
        build_question_text(updated_session, previous_index),
        reply_markup=build_question_keyboard(updated_session, previous_index),
    )


async def animate_analysis(message) -> None:
    for step in ANALYSIS_STEPS:
        await safe_edit_message(message, step)
        await asyncio.sleep(2)


async def handle_answer(query, context: ContextTypes.DEFAULT_TYPE, question_index: int, answer_code: str) -> None:
    session = get_session(query.from_user.id)
    if not session:
        await query.answer("Сессия теста устарела. Нажмите /start, чтобы начать заново.", show_alert=True)
        return

    current_index = session["current_index"]
    if question_index != current_index:
        await query.answer("Этот вопрос уже обработан или порядок устарел.", show_alert=False)
        return

    scores = session["scores"]
    history = session["history"]
    question_set = session["question_set"]

    if answer_code not in scores:
        await query.answer("Некорректный ответ. Попробуйте ещё раз.", show_alert=True)
        return

    scores[answer_code] += 1
    history.append(answer_code)
    next_index = current_index + 1

    if next_index >= len(question_set):
        primary_code, secondary_code, third_code, result_text = format_result(scores, question_set, history)
        save_result(query.from_user, scores, primary_code, secondary_code, third_code)
        delete_session(query.from_user.id)

        await animate_analysis(query.message)
        await safe_edit_message(
            query.message,
            result_text,
            reply_markup=get_result_keyboard(primary_code, secondary_code, third_code),
        )

        try:
            await send_result_to_admin(query.from_user, scores, primary_code, secondary_code, third_code, context)
        except Exception:
            logger.exception("Не удалось отправить результат в админ-чат")
        return

    save_session(query.from_user.id, next_index, scores, history, question_set)
    updated_session = get_session(query.from_user.id)
    if updated_session is None:
        await query.message.reply_text("Не удалось загрузить следующий вопрос. Попробуйте /start.")
        return

    await safe_edit_message(
        query.message,
        build_question_text(updated_session, next_index),
        reply_markup=build_question_keyboard(updated_session, next_index),
    )


async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    if query is None:
        return

    await query.answer()
    data = query.data or ""

    if data == "start_test":
        await handle_start_test(query)
        return

    if data == "resume_test":
        await handle_resume_test(query)
        return

    if data == "restart_test":
        await handle_restart_test(query)
        return

    if data == "go_back":
        await handle_go_back(query)
        return

    if data.startswith("answer:"):
        _, question_index, answer_code = data.split(":", 2)
        await handle_answer(query, context, int(question_index), answer_code)
        return


def main() -> None:
    init_db()

    if ADMIN_CHAT_ID is None:
        logger.warning(NO_ADMIN_WARNING)

    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(button_handler))

    logger.info("2026UP career test bot started...")
    app.run_polling()


if __name__ == "__main__":
    main()
