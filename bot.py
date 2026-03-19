import os
import json
import sqlite3
import random
from datetime import datetime
from typing import Dict, List, Tuple, Optional

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler, ContextTypes
from telegram.error import BadRequest


# =========================
# ENV
# =========================
BOT_TOKEN = os.getenv("BOT_TOKEN")
if not BOT_TOKEN:
    raise ValueError("Не найдена переменная окружения BOT_TOKEN")

ADMIN_CHAT_ID_RAW = os.getenv("ADMIN_CHAT_ID", "").strip()
ADMIN_CHAT_ID: Optional[int] = None
if ADMIN_CHAT_ID_RAW:
    try:
        ADMIN_CHAT_ID = int(ADMIN_CHAT_ID_RAW)
    except ValueError:
        raise ValueError("ADMIN_CHAT_ID должен быть числом, например 123456789 или -1001234567890")

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
    "Отвечайте честно и интуитивно. В тесте нет «правильных» и «неправильных» ответов — цель понять, какая роль вам действительно ближе."
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
    {
        "question": "1. В новой команде вы быстрее всего проявляете себя через…",
        "options": [
            ("A", "умение расположить к себе людей и наладить атмосферу"),
            ("B", "идеи, как сделать продукт заметнее и интереснее"),
            ("C", "понимание, кто на что влияет и где есть полезные связи"),
        ],
    },
    {
        "question": "2. Что чаще всего вызывает у вас внутренний интерес?",
        "options": [
            ("A", "поведение людей и их мотивация"),
            ("B", "почему одни идеи «цепляют», а другие нет"),
            ("C", "как устроены договорённости и чья выгода в них сильнее"),
        ],
    },
    {
        "question": "3. Когда у людей вокруг стресс, вы обычно…",
        "options": [
            ("A", "стараетесь стабилизировать общение и снизить напряжение"),
            ("B", "думаете, как правильно подать ситуацию и сохранить восприятие"),
            ("C", "ищете кратчайший путь к практическому решению"),
        ],
    },
    {
        "question": "4. Что для вас выглядит как действительно классный рабочий день?",
        "options": [
            ("A", "много живой коммуникации и понятная обратная связь от людей"),
            ("B", "проверка гипотез, идеи, контент и ростовые инсайты"),
            ("C", "полезные созвоны, новые контакты и продвижение переговоров"),
        ],
    },
    {
        "question": "5. Какая роль даётся вам естественнее всего?",
        "options": [
            ("A", "тот, к кому приходят с вопросами и за поддержкой"),
            ("B", "тот, кто подсказывает, как сделать сильнее и заметнее"),
            ("C", "тот, кто двигает вопрос через договорённости и ресурсы"),
        ],
    },
    {
        "question": "6. Что вам приятнее слышать о себе?",
        "options": [
            ("A", "с тобой легко и спокойно"),
            ("B", "у тебя классное чувство идеи и подачи"),
            ("C", "ты умеешь договариваться и открывать двери"),
        ],
    },
    {
        "question": "7. Что вас больше утомляет?",
        "options": [
            ("A", "холодное отношение и плохая коммуникация внутри сообщества"),
            ("B", "слабая упаковка и скучная подача сильного продукта"),
            ("C", "упущенные возможности и отсутствие нужных контактов"),
        ],
    },
    {
        "question": "8. Когда вы видите новый проект, вы интуитивно оцениваете прежде всего…",
        "options": [
            ("A", "какие там люди и какая атмосфера вокруг"),
            ("B", "как он выглядит, звучит и насколько он понятен рынку"),
            ("C", "кто за ним стоит и какие у него рычаги роста"),
        ],
    },
    {
        "question": "9. Что для вас ценнее в долгую?",
        "options": [
            ("A", "лояльные люди и сильное комьюнити"),
            ("B", "узнаваемость и сильный бренд"),
            ("C", "сеть отношений, которая открывает возможности"),
        ],
    },
    {
        "question": "10. В условиях неопределённости вы чаще опираетесь на…",
        "options": [
            ("A", "чувство людей и реакцию аудитории"),
            ("B", "чувство рынка, трендов и подачи"),
            ("C", "практический расчёт и leverage"),
        ],
    },
    {
        "question": "11. Что вас больше заряжает эмоционально?",
        "options": [
            ("A", "видеть, как люди включаются и становятся активнее"),
            ("B", "видеть, как идея начинает вируситься и расти"),
            ("C", "видеть, как диалог превращается в реальную возможность"),
        ],
    },
    {
        "question": "12. В споре вам ближе…",
        "options": [
            ("A", "понять позицию сторон и вернуть контакт"),
            ("B", "найти формулировку, которая изменит восприятие"),
            ("C", "найти формат, при котором все стороны что-то выигрывают"),
        ],
    },
    {
        "question": "13. Какая рабочая среда вам ближе?",
        "options": [
            ("A", "где много взаимодействия с людьми и постоянный диалог"),
            ("B", "где ценятся идеи, гипотезы и экспериментирование"),
            ("C", "где ценятся инициативность, связи и результат через переговоры"),
        ],
    },
    {
        "question": "14. Что у вас чаще получается лучше других?",
        "options": [
            ("A", "чувствовать настроение людей и не терять контакт"),
            ("B", "видеть, как улучшить подачу и сделать сильнее интерес"),
            ("C", "замечать, с кем и как можно создать полезное сотрудничество"),
        ],
    },
    {
        "question": "15. Какой комплимент кажется вам самым «про вас»?",
        "options": [
            ("A", "ты умеешь удерживать людей рядом"),
            ("B", "ты умеешь запускать интерес к идее"),
            ("C", "ты умеешь соединять нужных людей и возможности"),
        ],
    },
    {
        "question": "16. Когда вы думаете о будущем росте, вас больше привлекает…",
        "options": [
            ("A", "влияние через отношения и сообщество"),
            ("B", "влияние через идеи, бренд и внимание"),
            ("C", "влияние через переговоры и стратегические связи"),
        ],
    },
    {
        "question": "17. Что для вас особенно важно в работе?",
        "options": [
            ("A", "чувствовать, что вы реально полезны людям"),
            ("B", "видеть измеримый рост интереса и охвата"),
            ("C", "видеть, что вы открываете новые возможности"),
        ],
    },
    {
        "question": "18. Если вам нужно быстро освоиться в новом пространстве, вы скорее…",
        "options": [
            ("A", "начнёте знакомиться и понимать локальную динамику людей"),
            ("B", "поймёте, как там всё устроено с точки зрения внимания и подачи"),
            ("C", "поймёте, кто ключевые игроки и как выйти на них"),
        ],
    },
    {
        "question": "19. Что больше всего мешает сильному проекту, по вашему ощущению?",
        "options": [
            ("A", "когда аудиторию не слышат и с ней не выстраивают отношения"),
            ("B", "когда продукт не умеют правильно показать рынку"),
            ("C", "когда проект не использует внешние связи и возможности"),
        ],
    },
    {
        "question": "20. Какая роль ощущается для вас наиболее естественной?",
        "options": [
            ("A", "быть мостом между проектом и людьми"),
            ("B", "быть драйвером интереса, роста и позиционирования"),
            ("C", "быть человеком, который открывает проекту новые двери"),
        ],
    },
]

THINKING_QUESTIONS = [
    {
        "question": "21. Если проект не растёт, вы в первую очередь подумаете о…",
        "options": [
            ("A", "качестве обратной связи, удержании и атмосфере"),
            ("B", "воронке, позиционировании и каналах привлечения"),
            ("C", "партнёрах, дистрибуции и внешних точках роста"),
        ],
    },
    {
        "question": "22. Какой KPI вам интуитивно понятнее?",
        "options": [
            ("A", "engagement, retention, active community"),
            ("B", "CTR, CAC, registrations, reach"),
            ("C", "количество партнёрств, integrations, deal flow"),
        ],
    },
    {
        "question": "23. Что вам проще структурировать?",
        "options": [
            ("A", "сценарии общения, FAQ и логику работы с аудиторией"),
            ("B", "контент-план, воронку и growth-гипотезы"),
            ("C", "список приоритетных партнёров и шаги по переговорам"),
        ],
    },
    {
        "question": "24. Если бы вам дали ограниченный ресурс времени, вы бы поставили акцент на…",
        "options": [
            ("A", "качество взаимодействия с текущей аудиторией"),
            ("B", "действия, которые усиливают видимость и спрос"),
            ("C", "действия, которые дают внешний рычаг роста"),
        ],
    },
    {
        "question": "25. Какой тип задач вам кажется наиболее интеллектуально интересным?",
        "options": [
            ("A", "понять причины поведения людей и удержать вовлечение"),
            ("B", "найти сильный угол подачи и масштабировать внимание"),
            ("C", "найти оптимальный путь к нужному решению через переговоры"),
        ],
    },
    {
        "question": "26. Вы скорее сильнее в…",
        "options": [
            ("A", "эмпатии, тоне и управлении коммуникацией"),
            ("B", "смыслах, гипотезах и понимании внимания аудитории"),
            ("C", "приоритизации возможностей и выходе на нужных людей"),
        ],
    },
    {
        "question": "27. Если нужно быстро улучшить результат, вы предпочтёте…",
        "options": [
            ("A", "выявить боли текущей аудитории и наладить диалог"),
            ("B", "протестировать новую подачу и новые каналы"),
            ("C", "подключить стратегических людей и внешние ресурсы"),
        ],
    },
    {
        "question": "28. Что кажется вам наиболее полезным навыком в хаотичной среде?",
        "options": [
            ("A", "не терять контакт с людьми и поддерживать ясность"),
            ("B", "быстро упаковывать идеи в понятные смыслы"),
            ("C", "быстро видеть leverage и принимать деловые решения"),
        ],
    },
    {
        "question": "29. Какой способ решения проблемы вам ближе?",
        "options": [
            ("A", "разобраться с первопричиной через диалог и фидбек"),
            ("B", "пересобрать подход, сообщение или механику"),
            ("C", "изменить конфигурацию взаимодействий и найти сильный альянс"),
        ],
    },
    {
        "question": "30. Когда вы смотрите на рынок, вы чаще замечаете…",
        "options": [
            ("A", "что люди любят, что их раздражает и на что они реагируют"),
            ("B", "какие смыслы, форматы и бренды выигрывают внимание"),
            ("C", "кто с кем связан и где есть незакрытые возможности"),
        ],
    },
    {
        "question": "31. Вам проще принять решение, когда вы видите…",
        "options": [
            ("A", "реакции людей и обратную связь сообщества"),
            ("B", "данные по росту и понимание, что сработает в подаче"),
            ("C", "карту влияния и возможные исходы переговоров"),
        ],
    },
    {
        "question": "32. В идеале ваша работа должна измеряться через…",
        "options": [
            ("A", "качество отношений и активность аудитории"),
            ("B", "привлечение внимания и рост интереса"),
            ("C", "новые возможности, сделки и деловой результат"),
        ],
    },
    {
        "question": "33. Когда вы строите план, вам естественнее начать с…",
        "options": [
            ("A", "карты сегментов аудитории и сценариев общения"),
            ("B", "основной идеи, оффера и каналов продвижения"),
            ("C", "списка приоритетных контактов и партнёрского pipeline"),
        ],
    },
    {
        "question": "34. Что вам легче всего улучшать системно?",
        "options": [
            ("A", "коммуникационные процессы и качество взаимодействия"),
            ("B", "ростовые механики, упаковку и маркетинговую воронку"),
            ("C", "деловые процессы вокруг партнёрств и выхода на рынок"),
        ],
    },
    {
        "question": "35. Какой тип информации для вас особенно полезен?",
        "options": [
            ("A", "реальные отзывы, реакции и поведение сообщества"),
            ("B", "данные о спросе, конверсии и работе креативов"),
            ("C", "информация о ключевых людях, компаниях и их интересах"),
        ],
    },
    {
        "question": "36. Если нужно быстро понять, где проект теряет потенциал, вы проверите…",
        "options": [
            ("A", "где рвётся связь с текущей аудиторией"),
            ("B", "где слабая упаковка и неработающая воронка"),
            ("C", "где отсутствуют сильные внешние связи и интеграции"),
        ],
    },
    {
        "question": "37. Ваша сильная сторона в команде — это чаще…",
        "options": [
            ("A", "стабилизировать коммуникацию и быть голосом аудитории"),
            ("B", "видеть возможности роста и усиливать позиционирование"),
            ("C", "создавать полезные входы, коллаборации и деловые ходы"),
        ],
    },
    {
        "question": "38. Что вам приятнее строить?",
        "options": [
            ("A", "долгосрочное доверие"),
            ("B", "сильный спрос"),
            ("C", "сильную сеть возможностей"),
        ],
    },
    {
        "question": "39. Что из этого больше похоже на ваш стиль мышления?",
        "options": [
            ("A", "люди сначала"),
            ("B", "внимание и рост сначала"),
            ("C", "рычаги влияния и результат сначала"),
        ],
    },
    {
        "question": "40. Если бы вы выбирали между тремя типами задач, какая была бы вам ближе всего?",
        "options": [
            ("A", "удержать и вовлечь текущую аудиторию"),
            ("B", "придумать, как резко усилить интерес к продукту"),
            ("C", "найти того, кто ускорит рост через сотрудничество"),
        ],
    },
]

WEB3_PRACTICE_QUESTIONS = [
    {
        "question": "41. В Telegram-чате проекта резко начался негатив. Что вам ближе сделать первым?",
        "options": [
            ("A", "успокоить тон диалога, ответить людям и вернуть доверие"),
            ("B", "подумать, как грамотно подать ситуацию публично"),
            ("C", "быстро собрать ответственных и закрыть вопрос решением"),
        ],
    },
    {
        "question": "42. У проекта нормальный продукт, но мало новых пользователей. Ваш первый фокус?",
        "options": [
            ("A", "оживить текущую аудиторию и понять, что ей не хватает"),
            ("B", "усилить оффер, маркетинг и acquisition-каналы"),
            ("C", "найти партнёров, которые дадут доступ к новой аудитории"),
        ],
    },
    {
        "question": "43. Вам дали задачу принести результат за 30 дней. Что вам ближе?",
        "options": [
            ("A", "повысить активность и лояльность комьюнити"),
            ("B", "запустить рост через контент и гипотезы"),
            ("C", "собрать pipeline партнёров и выйти на ключевых игроков"),
        ],
    },
    {
        "question": "44. В Web3-проекте упал engagement в соцсетях. Ваш первый ход?",
        "options": [
            ("A", "разобраться, чего не хватает текущему комьюнити"),
            ("B", "пересобрать контент-стратегию и форматы"),
            ("C", "задействовать внешние коллаборации и новых медиапартнёров"),
        ],
    },
    {
        "question": "45. Биржа или проект хочет выйти на новый регион. Что вам ближе взять на себя?",
        "options": [
            ("A", "адаптировать коммуникацию и работать с локальным комьюнити"),
            ("B", "адаптировать маркетинговые смыслы и каналы продвижения"),
            ("C", "выстроить локальные партнёрства, KOL-связи и экосистемные контакты"),
        ],
    },
    {
        "question": "46. После AMA активность не выросла. Какую гипотезу вы проверите первой?",
        "options": [
            ("A", "людям не хватило вовлечения и понятного продолжения общения"),
            ("B", "формат и упаковка ивента были слабыми"),
            ("C", "на ивент пришла не та аудитория и не было сильной дистрибуции"),
        ],
    },
    {
        "question": "47. Проект хочет укрепить репутацию. Куда вам ближе направить усилие?",
        "options": [
            ("A", "на прозрачную коммуникацию и работу с текущим сообществом"),
            ("B", "на сильный бренд-нарратив и качественную подачу"),
            ("C", "на ассоциацию с сильными партнёрами и экосистемой"),
        ],
    },
    {
        "question": "48. Вам нужно подготовить недельный план. Что в нём вам ближе всего?",
        "options": [
            ("A", "модерация, комьюнити-активности, ответы и обратная связь"),
            ("B", "контент, креативы, ростовые тесты и аналитика по каналам"),
            ("C", "созвоны, follow-up, outreach и подготовка партнёрских предложений"),
        ],
    },
    {
        "question": "49. На рынке появился сильный конкурент. Ваша первая мысль?",
        "options": [
            ("A", "важно сохранить лояльность текущих людей"),
            ("B", "нужно сильнее показать ценность и отличия продукта"),
            ("C", "нужно ускорить стратегические связи и усилить позиции через союзников"),
        ],
    },
    {
        "question": "50. Если проект запускает реферальную программу, вам интереснее всего…",
        "options": [
            ("A", "понять, как сделать её понятной и приятной для сообщества"),
            ("B", "продумать механику роста и как её красиво упаковать"),
            ("C", "понять, с кем объединить запуск, чтобы усилить охват и ценность"),
        ],
    },
    {
        "question": "51. Внутри проекта не хватает ясности по обратной связи от аудитории. Ваш фокус?",
        "options": [
            ("A", "собрать системный фидбек и структурировать проблемы людей"),
            ("B", "оценить, что мешает людям захотеть продукт сильнее"),
            ("C", "оценить, где внешние партнёры могут закрыть этот разрыв быстрее"),
        ],
    },
    {
        "question": "52. Проект хочет сделать коллаборацию с KOL. Что вам ближе?",
        "options": [
            ("A", "подумать, как аудитория воспримет это и как удержать диалог"),
            ("B", "подумать, как это встроить в маркетинговую кампанию"),
            ("C", "вести переговоры и добиваться выгодных условий сотрудничества"),
        ],
    },
    {
        "question": "53. После запуска продукта в чате много одинаковых вопросов. Что делать первым?",
        "options": [
            ("A", "улучшить поддержку, FAQ и тон коммуникации"),
            ("B", "улучшить onboarding и подачу продукта"),
            ("C", "подключить партнёров, которые помогут с дистрибуцией и обучением"),
        ],
    },
    {
        "question": "54. Если токен-проект готовит важный анонс, вам интереснее отвечать за…",
        "options": [
            ("A", "качественную работу с реакцией сообщества до и после анонса"),
            ("B", "упаковку анонса и его маркетинговый эффект"),
            ("C", "внешние связи, ко-маркетинг и стратегические касания"),
        ],
    },
    {
        "question": "55. Если вы работаете на CEX, какой блок задач ближе вам больше всего?",
        "options": [
            ("A", "комьюнити, локальные чаты, удержание и пользовательский фидбек"),
            ("B", "рекламные кампании, growth, медиа и KOL-активации"),
            ("C", "листинговые и экосистемные партнёрства, affiliate и business outreach"),
        ],
    },
    {
        "question": "56. Что для вас выглядит как самый сильный результат в Web3?",
        "options": [
            ("A", "сообщество, которое верит проекту и остаётся с ним"),
            ("B", "рынок, который замечает и обсуждает проект"),
            ("C", "экосистема, в которой проект стал нужным игроком"),
        ],
    },
    {
        "question": "57. Команда хочет поднять конверсию с контента в действие. Что вам ближе сделать?",
        "options": [
            ("A", "убрать непонимание и усилить контакт с текущей аудиторией"),
            ("B", "пересобрать контент, CTA и воронку"),
            ("C", "подключить правильных партнёров и совместные размещения"),
        ],
    },
    {
        "question": "58. В проекте начинается подготовка к офлайн-ивенту. Чем вам интереснее заняться?",
        "options": [
            ("A", "работой с участниками, атмосферой и коммуникацией до/во время/после"),
            ("B", "упаковкой события, промо и охватом"),
            ("C", "поиском спонсоров, партнёров и VIP-контактов"),
        ],
    },
    {
        "question": "59. Проект хочет усилить присутствие в экосистеме. Вы бы начали с…",
        "options": [
            ("A", "понимания, как текущее комьюнити может усилить этот рост"),
            ("B", "понимания, как правильно рассказать рынку новую историю"),
            ("C", "карты экосистемных игроков и планов по выходу на них"),
        ],
    },
    {
        "question": "60. Если вам нужно выбрать одну роль в запуске нового Web3-продукта, что ближе всего?",
        "options": [
            ("A", "сделать так, чтобы пользователи чувствовали связь с проектом"),
            ("B", "сделать так, чтобы о проекте узнали и захотели его попробовать"),
            ("C", "сделать так, чтобы проект быстро получил сильные внешние рычаги роста"),
        ],
    },
]


# =========================
# DB
# =========================
def now_str() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def get_conn():
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
def shuffle_question(question: dict) -> dict:
    options = list(question["options"])
    random.shuffle(options)
    return {
        "question": question["question"],
        "options": options,
    }


def build_question_set() -> List[dict]:
    selected = []
    selected.extend(random.sample(PSYCHOLOGY_QUESTIONS, 5))
    selected.extend(random.sample(THINKING_QUESTIONS, 5))
    selected.extend(random.sample(WEB3_PRACTICE_QUESTIONS, 5))
    random.shuffle(selected)
    return [shuffle_question(q) for q in selected]


def calculate_result(scores: Dict[str, int]) -> Tuple[str, str, str]:
    sorted_scores = sorted(scores.items(), key=lambda item: item[1], reverse=True)
    return sorted_scores[0][0], sorted_scores[1][0], sorted_scores[2][0]


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
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton("A", callback_data=f"answer:{index}:{question_data['options'][0][0]}"),
            InlineKeyboardButton("B", callback_data=f"answer:{index}:{question_data['options'][1][0]}"),
            InlineKeyboardButton("C", callback_data=f"answer:{index}:{question_data['options'][2][0]}"),
        ],
        [InlineKeyboardButton("Начать заново", callback_data="restart_test")],
    ])


def get_result_keyboard(primary_code: str, secondary_code: str, third_code: str) -> InlineKeyboardMarkup:
    rows = []
    for code in [primary_code, secondary_code, third_code]:
        rows.append([
            InlineKeyboardButton(f"Выбрать {ROLE_NAMES[code]}", url=ROLE_PAYMENT_URLS[code])
        ])
    rows.append([InlineKeyboardButton("Нужна помощь менеджера", url=MANAGER_URL)])
    rows.append([InlineKeyboardButton("Пройти тест заново", callback_data="restart_test")])
    return InlineKeyboardMarkup(rows)


def format_result(scores: Dict[str, int]) -> Tuple[str, str, str, str]:
    primary_code, secondary_code, third_code = calculate_result(scores)
    sorted_scores = sorted(scores.items(), key=lambda item: item[1], reverse=True)
    mixed_profile = (sorted_scores[0][1] - sorted_scores[1][1]) <= 1

    lines = [
        f"Ваш результат: {ROLE_NAMES[primary_code]} 🚀",
        "",
        "Почему это направление подходит вам лучше всего:",
        ROLE_WHY[primary_code],
        "",
    ]

    if mixed_profile:
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
    await safe_edit_message(
        query.message,
        build_question_text(session, index),
        reply_markup=build_question_keyboard(session, index),
    )


async def handle_restart_test(query) -> None:
    delete_session(query.from_user.id)
    await safe_edit_message(query.message, WELCOME_TEXT, reply_markup=get_entry_keyboard())


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

    scores[answer_code] += 1
    history.append(answer_code)
    next_index = current_index + 1

    if next_index >= len(question_set):
        primary_code, secondary_code, third_code, result_text = format_result(scores)
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
        except Exception as e:
            print(f"Не удалось отправить результат в админ-чат: {e}")
        return

    save_session(query.from_user.id, next_index, scores, history, question_set)
    updated_session = get_session(query.from_user.id)
    await safe_edit_message(
        query.message,
        build_question_text(updated_session, next_index),
        reply_markup=build_question_keyboard(updated_session, next_index),
    )


async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()
    data = query.data

    if data == "start_test":
        await handle_start_test(query)
        return

    if data == "resume_test":
        await handle_resume_test(query)
        return

    if data == "restart_test":
        await handle_restart_test(query)
        return

    if data.startswith("answer:"):
        _, question_index, answer_code = data.split(":")
        await handle_answer(query, context, int(question_index), answer_code)
        return


def main() -> None:
    init_db()

    if ADMIN_CHAT_ID is None:
        print(NO_ADMIN_WARNING)

    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(button_handler))

    print("2026UP career test bot started...")
    app.run_polling()


if __name__ == "__main__":
    main()



if __name__ == "__main__":
    main()
