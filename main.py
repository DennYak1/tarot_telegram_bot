import os
import json
import random
import hashlib
from datetime import datetime
from zoneinfo import ZoneInfo

from dotenv import load_dotenv

load_dotenv()
from fastapi import FastAPI, Request
from aiogram import Bot, Dispatcher, F
from aiogram.filters import Command
from aiogram.types import Message, Update, ReplyKeyboardMarkup, KeyboardButton
from supabase import create_client

from fastapi.staticfiles import StaticFiles

BOT_TOKEN = os.getenv("BOT_TOKEN")
BASE_URL = os.getenv("BASE_URL")  # например: https://your-bot.onrender.com
WEBHOOK_SECRET = os.getenv("WEBHOOK_SECRET", "tarot-secret")

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_SERVICE_KEY = os.getenv("SUPABASE_SERVICE_KEY")

TZ = ZoneInfo("Europe/Berlin")

if not BOT_TOKEN:
    raise RuntimeError("BOT_TOKEN is missing")

if not SUPABASE_URL or not SUPABASE_SERVICE_KEY:
    raise RuntimeError("SUPABASE_URL or SUPABASE_SERVICE_KEY is missing")

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()
app = FastAPI()
app.mount("/static", StaticFiles(directory="static"), name="static")

supabase = create_client(SUPABASE_URL, SUPABASE_SERVICE_KEY)

CARD_IMAGES = {
    # Старшие арканы
    "Шут": "00-TheFool.jpg",
    "Маг": "01-TheMagician.jpg",
    "Верховная Жрица": "02-TheHighPriestess.jpg",
    "Императрица": "03-TheEmpress.jpg",
    "Император": "04-TheEmperor.jpg",
    "Иерофант": "05-TheHierophant.jpg",
    "Влюблённые": "06-TheLovers.jpg",
    "Колесница": "07-TheChariot.jpg",
    "Сила": "08-Strength.jpg",
    "Отшельник": "09-TheHermit.jpg",
    "Колесо Фортуны": "10-WheelOfFortune.jpg",
    "Справедливость": "11-Justice.jpg",
    "Повешенный": "12-TheHangedMan.jpg",
    "Смерть": "13-Death.jpg",
    "Умеренность": "14-Temperance.jpg",
    "Дьявол": "15-TheDevil.jpg",
    "Башня": "16-TheTower.jpg",
    "Звезда": "17-TheStar.jpg",
    "Луна": "18-TheMoon.jpg",
    "Солнце": "19-TheSun.jpg",
    "Суд": "20-Judgement.jpg",
    "Мир": "21-TheWorld.jpg",

    # Кубки
    "Туз Кубков": "Cups01.jpg",
    "Двойка Кубков": "Cups02.jpg",
    "Тройка Кубков": "Cups03.jpg",
    "Четвёрка Кубков": "Cups04.jpg",
    "Пятёрка Кубков": "Cups05.jpg",
    "Шестёрка Кубков": "Cups06.jpg",
    "Семёрка Кубков": "Cups07.jpg",
    "Восьмёрка Кубков": "Cups08.jpg",
    "Девятка Кубков": "Cups09.jpg",
    "Десятка Кубков": "Cups10.jpg",
    "Паж Кубков": "Cups11.jpg",
    "Рыцарь Кубков": "Cups12.jpg",
    "Королева Кубков": "Cups13.jpg",
    "Король Кубков": "Cups14.jpg",

    # Пентакли
    "Туз Пентаклей": "Pentacles01.jpg",
    "Двойка Пентаклей": "Pentacles02.jpg",
    "Тройка Пентаклей": "Pentacles03.jpg",
    "Четвёрка Пентаклей": "Pentacles04.jpg",
    "Пятёрка Пентаклей": "Pentacles05.jpg",
    "Шестёрка Пентаклей": "Pentacles06.jpg",
    "Семёрка Пентаклей": "Pentacles07.jpg",
    "Восьмёрка Пентаклей": "Pentacles08.jpg",
    "Девятка Пентаклей": "Pentacles09.jpg",
    "Десятка Пентаклей": "Pentacles10.jpg",
    "Паж Пентаклей": "Pentacles11.jpg",
    "Рыцарь Пентаклей": "Pentacles12.jpg",
    "Королева Пентаклей": "Pentacles13.jpg",
    "Король Пентаклей": "Pentacles14.jpg",

    # Мечи
    "Туз Мечей": "Swords01.jpg",
    "Двойка Мечей": "Swords02.jpg",
    "Тройка Мечей": "Swords03.jpg",
    "Четвёрка Мечей": "Swords04.jpg",
    "Пятёрка Мечей": "Swords05.jpg",
    "Шестёрка Мечей": "Swords06.jpg",
    "Семёрка Мечей": "Swords07.jpg",
    "Восьмёрка Мечей": "Swords08.jpg",
    "Девятка Мечей": "Swords09.jpg",
    "Десятка Мечей": "Swords10.jpg",
    "Паж Мечей": "Swords11.jpg",
    "Рыцарь Мечей": "Swords12.jpg",
    "Королева Мечей": "Swords13.jpg",
    "Король Мечей": "Swords14.jpg",

    # Жезлы
    "Туз Жезлов": "Wands01.jpg",
    "Двойка Жезлов": "Wands02.jpg",
    "Тройка Жезлов": "Wands03.jpg",
    "Четвёрка Жезлов": "Wands04.jpg",
    "Пятёрка Жезлов": "Wands05.jpg",
    "Шестёрка Жезлов": "Wands06.jpg",
    "Семёрка Жезлов": "Wands07.jpg",
    "Восьмёрка Жезлов": "Wands08.jpg",
    "Девятка Жезлов": "Wands09.jpg",
    "Десятка Жезлов": "Wands10.jpg",
    "Паж Жезлов": "Wands11.jpg",
    "Рыцарь Жезлов": "Wands12.jpg",
    "Королева Жезлов": "Wands13.jpg",
    "Король Жезлов": "Wands14.jpg",

    # Рубашка карты
    "Рубашка": "CardBacks.jpg",
}

TAROT_CARDS = [
    # Старшие арканы
    "Шут",
    "Маг",
    "Верховная Жрица",
    "Императрица",
    "Император",
    "Иерофант",
    "Влюблённые",
    "Колесница",
    "Сила",
    "Отшельник",
    "Колесо Фортуны",
    "Справедливость",
    "Повешенный",
    "Смерть",
    "Умеренность",
    "Дьявол",
    "Башня",
    "Звезда",
    "Луна",
    "Солнце",
    "Суд",
    "Мир",

    # Кубки
    "Туз Кубков",
    "Двойка Кубков",
    "Тройка Кубков",
    "Четвёрка Кубков",
    "Пятёрка Кубков",
    "Шестёрка Кубков",
    "Семёрка Кубков",
    "Восьмёрка Кубков",
    "Девятка Кубков",
    "Десятка Кубков",
    "Паж Кубков",
    "Рыцарь Кубков",
    "Королева Кубков",
    "Король Кубков",

    # Пентакли
    "Туз Пентаклей",
    "Двойка Пентаклей",
    "Тройка Пентаклей",
    "Четвёрка Пентаклей",
    "Пятёрка Пентаклей",
    "Шестёрка Пентаклей",
    "Семёрка Пентаклей",
    "Восьмёрка Пентаклей",
    "Девятка Пентаклей",
    "Десятка Пентаклей",
    "Паж Пентаклей",
    "Рыцарь Пентаклей",
    "Королева Пентаклей",
    "Король Пентаклей",

    # Мечи
    "Туз Мечей",
    "Двойка Мечей",
    "Тройка Мечей",
    "Четвёрка Мечей",
    "Пятёрка Мечей",
    "Шестёрка Мечей",
    "Семёрка Мечей",
    "Восьмёрка Мечей",
    "Девятка Мечей",
    "Десятка Мечей",
    "Паж Мечей",
    "Рыцарь Мечей",
    "Королева Мечей",
    "Король Мечей",

    # Жезлы
    "Туз Жезлов",
    "Двойка Жезлов",
    "Тройка Жезлов",
    "Четвёрка Жезлов",
    "Пятёрка Жезлов",
    "Шестёрка Жезлов",
    "Семёрка Жезлов",
    "Восьмёрка Жезлов",
    "Девятка Жезлов",
    "Десятка Жезлов",
    "Паж Жезлов",
    "Рыцарь Жезлов",
    "Королева Жезлов",
    "Король Жезлов",
]

CARD_MEANINGS = {
    "Шут": "новое начало, спонтанность, шаг в неизвестность",
    "Маг": "воля, действие, способность влиять на ситуацию",
    "Верховная Жрица": "интуиция, скрытая информация, внутреннее знание",
    "Императрица": "рост, забота, плодородие, созидание",
    "Император": "структура, контроль, порядок, ответственность",
    "Иерофант": "традиции, обучение, духовный совет",
    "Влюблённые": "выбор, отношения, ценности, притяжение",
    "Колесница": "движение, победа, дисциплина, контроль курса",
    "Сила": "мягкая власть, выдержка, внутренняя устойчивость",
    "Отшельник": "уединение, поиск смысла, глубокий анализ",
    "Колесо Фортуны": "перемены, циклы, шанс, неожиданный поворот",
    "Справедливость": "баланс, честность, последствия решений",
    "Повешенный": "пауза, переоценка, новый взгляд",
    "Смерть": "завершение этапа, трансформация, освобождение",
    "Умеренность": "гармония, терпение, восстановление баланса",
    "Дьявол": "зависимость, искушение, привязки, скрытые ограничения",
    "Башня": "резкие перемены, разрушение старого, правда без прикрас",
    "Звезда": "надежда, вдохновение, исцеление, вера в путь",
    "Луна": "сомнения, иллюзии, тревожность, неясность",
    "Солнце": "ясность, успех, радость, открытость",
    "Суд": "пробуждение, итог, важное осознание",
    "Мир": "завершение, целостность, переход на новый уровень",
}

REVERSED_CARD_MEANINGS = {
    "Шут": "необдуманность, хаос, страх сделать первый шаг",
    "Маг": "сомнение в себе, манипуляции, рассеянная энергия",
    "Верховная Жрица": "игнорирование интуиции, скрытность, путаница",
    "Императрица": "застой, переизбыток контроля, нехватка заботы о себе",
    "Император": "жёсткость, давление, потеря структуры",
    "Иерофант": "конфликт с правилами, устаревшие установки, внутренний протест",
    "Влюблённые": "сложный выбор, сомнения, несогласованность ценностей",
    "Колесница": "потеря направления, спешка, слабый контроль ситуации",
    "Сила": "неуверенность, усталость, подавленная энергия",
    "Отшельник": "изоляция, закрытость, отказ от помощи",
    "Колесо Фортуны": "задержка перемен, сопротивление циклу, нестабильность",
    "Справедливость": "перекос, нечестность, последствия прошлых решений",
    "Повешенный": "застревание, жертвенность, нежелание менять взгляд",
    "Смерть": "страх завершения, сопротивление переменам, затяжной переход",
    "Умеренность": "дисбаланс, нетерпение, внутреннее напряжение",
    "Дьявол": "осознание зависимости, попытка освободиться, скрытые привязки",
    "Башня": "избегание правды, накопленное напряжение, страх разрушения старого",
    "Звезда": "потеря веры, усталость, сомнение в будущем",
    "Луна": "самообман, тревога, неясность, искажённое восприятие",
    "Солнце": "временная потеря радости, неуверенность, задержка успеха",
    "Суд": "отказ признать итог, страх перемен, незавершённый внутренний процесс",
    "Мир": "незавершённость, задержка финала, ощущение, что путь ещё не закрыт",

    "Туз Кубков": "эмоциональная закрытость, сдержанные чувства",
    "Двойка Кубков": "дистанция, недопонимание, хрупкая связь",
    "Тройка Кубков": "поверхностное общение, разлад в окружении",
    "Четвёрка Кубков": "апатия, эмоциональная усталость, отказ видеть возможности",
    "Пятёрка Кубков": "застревание в сожалениях, трудность отпустить прошлое",
    "Шестёрка Кубков": "идеализация прошлого, привязанность к старым сценариям",
    "Семёрка Кубков": "иллюзии, распыление, невозможность выбрать",
    "Восьмёрка Кубков": "страх уйти, затягивание эмоционального решения",
    "Девятка Кубков": "неполное удовлетворение, завышенные ожидания",
    "Десятка Кубков": "напряжение в близких отношениях, нестабильная гармония",
    "Паж Кубков": "эмоциональная незрелость, робость, скрытые чувства",
    "Рыцарь Кубков": "идеализация, красивые слова без действия",
    "Королева Кубков": "эмоциональная перегрузка, зависимость от настроения",
    "Король Кубков": "подавление чувств, эмоциональный контроль, закрытость",

    "Туз Пентаклей": "упущенная возможность, задержка материального старта",
    "Двойка Пентаклей": "перегрузка, хаос в делах, трудность удержать баланс",
    "Тройка Пентаклей": "слабое взаимодействие, недооценка работы",
    "Четвёрка Пентаклей": "жадность, страх потерь, чрезмерный контроль",
    "Пятёрка Пентаклей": "ощущение нехватки, страх просить поддержку",
    "Шестёрка Пентаклей": "неравный обмен, зависимость, скрытая выгода",
    "Семёрка Пентаклей": "нетерпение, сомнения в результате, усталость от ожидания",
    "Восьмёрка Пентаклей": "рутина без вдохновения, ошибки из-за усталости",
    "Девятка Пентаклей": "зависимость, неуверенность в своей ценности",
    "Десятка Пентаклей": "семейные или финансовые напряжения, нестабильность основы",
    "Паж Пентаклей": "недостаток практики, несобранность, слабый старт",
    "Рыцарь Пентаклей": "застой, чрезмерная осторожность, медленное движение",
    "Королева Пентаклей": "перегруз заботой, бытовой контроль, усталость",
    "Король Пентаклей": "жёсткость, материализм, страх потерять статус",

    "Туз Мечей": "путаница, неясная мысль, недостаток честности",
    "Двойка Мечей": "избегание решения, внутренний конфликт",
    "Тройка Мечей": "зажатая боль, обида, трудность прожить ситуацию",
    "Четвёрка Мечей": "выгорание, невозможность восстановиться",
    "Пятёрка Мечей": "конфликтность, победа ценой отношений",
    "Шестёрка Мечей": "сопротивление переходу, страх двигаться дальше",
    "Семёрка Мечей": "скрытые мотивы, самообман, обходной путь",
    "Восьмёрка Мечей": "ощущение ловушки, ограничивающие мысли",
    "Девятка Мечей": "тревожность, накручивание, внутреннее напряжение",
    "Десятка Мечей": "затяжное завершение, болезненный финал",
    "Паж Мечей": "резкость, поспешные выводы, тревожное наблюдение",
    "Рыцарь Мечей": "импульсивность, конфликт, слишком резкое движение",
    "Королева Мечей": "холодность, критичность, эмоциональная закрытость",
    "Король Мечей": "жёсткое мышление, контроль, отсутствие гибкости",

    "Туз Жезлов": "потеря импульса, задержка старта, нехватка энергии",
    "Двойка Жезлов": "страх выбора, сомнения в направлении",
    "Тройка Жезлов": "задержка роста, ожидание без действия",
    "Четвёрка Жезлов": "нестабильность дома, напряжение в основе",
    "Пятёрка Жезлов": "хаос, спорность, борьба без результата",
    "Шестёрка Жезлов": "сомнение в признании, страх провала",
    "Семёрка Жезлов": "усталость от защиты позиции, давление",
    "Восьмёрка Жезлов": "задержки, сбои коммуникации, резкие перемены не вовремя",
    "Девятка Жезлов": "настороженность, защитная позиция, усталость",
    "Десятка Жезлов": "перегрузка, слишком много ответственности",
    "Паж Жезлов": "неуверенный старт, незрелый энтузиазм",
    "Рыцарь Жезлов": "импульсивность, непостоянство, рискованное действие",
    "Королева Жезлов": "ревность, эмоциональная вспыльчивость, неуверенность",
    "Король Жезлов": "давление, авторитарность, чрезмерное стремление контролировать",
}

MAIN_MENU = ReplyKeyboardMarkup(
    keyboard=[
        [
            KeyboardButton(text="🌞 Карта дня"),
            KeyboardButton(text="🔮 3 карты"),
        ],
        [
            KeyboardButton(text="🧬 Карты рождения"),
            KeyboardButton(text="✍️ Расклад на ситуацию"),
        ],
        [
            KeyboardButton(text="📅 Сохранить дату рождения"),
            KeyboardButton(text="ℹ️ Помощь"),
        ],
    ],
    resize_keyboard=True,
    input_field_placeholder="Выберите действие"
)

USER_WAITING_ACTION = {}


def today_str() -> str:
    return datetime.now(TZ).date().isoformat()


def get_card_image_url(card) -> str | None:
    name = card_name(card)
    filename = CARD_IMAGES.get(name)

    if not filename:
        print(f"[CARD_IMAGE] Не найден файл для карты: {name}")
        return None

    public_base_url = BASE_URL or "https://tarot-telegram-bot-0hfs.onrender.com"

    return f"{public_base_url.rstrip('/')}/static/cards/{filename}"


def make_seed(*parts: str) -> int:
    raw = "|".join(str(part) for part in parts)
    digest = hashlib.sha256(raw.encode("utf-8")).hexdigest()
    return int(digest, 16)


def draw_cards(seed: int, count: int, allow_reversed: bool = True) -> list[dict]:
    rng = random.Random(seed)
    deck = TAROT_CARDS.copy()
    rng.shuffle(deck)

    result = []

    for card_name in deck[:count]:
        result.append({
            "name": card_name,
            "reversed": rng.choice([False, True]) if allow_reversed else False
        })

    return result


def card_name(card) -> str:
    if isinstance(card, dict):
        return card.get("name", "")
    return str(card)


def card_is_reversed(card) -> bool:
    if isinstance(card, dict):
        return bool(card.get("reversed", False))
    return False


def card_title(card) -> str:
    name = card_name(card)

    if card_is_reversed(card):
        return f"{name} — перевёрнутая"

    return f"{name} — прямая"


def get_card_meaning(card) -> str:
    name = card_name(card)

    if card_is_reversed(card):
        return REVERSED_CARD_MEANINGS.get(
            name,
            "энергия карты проявляется нестабильно, заблокировано или требует внутренней переоценки"
        )

    return CARD_MEANINGS.get(
        name,
        "толкование пока не добавлено"
    )


def format_cards(cards: list) -> str:
    lines = []

    for i, card in enumerate(cards, start=1):
        lines.append(
            f"{i}. {card_title(card)} — {get_card_meaning(card)}"
        )

    return "\n".join(lines)


def get_or_create_user(message: Message):
    telegram_id = message.from_user.id
    username = message.from_user.username
    first_name = message.from_user.first_name

    existing = (
        supabase.table("users")
        .select("*")
        .eq("telegram_id", telegram_id)
        .execute()
    )

    if existing.data:
        return existing.data[0]

    created = (
        supabase.table("users")
        .insert({
            "telegram_id": telegram_id,
            "username": username,
            "first_name": first_name,
        })
        .execute()
    )

    return created.data[0]


def save_reading(user_id: int, reading_type: str, cards: list, question_text: str | None = None):
    payload = {
        "user_id": user_id,
        "reading_type": reading_type,
        "reading_date": today_str(),
        "question_text": question_text,
        "cards": cards,
    }

    return supabase.table("readings").insert(payload).execute()


def get_daily_reading(user_id: int, reading_type: str):
    result = (
        supabase.table("readings")
        .select("*")
        .eq("user_id", user_id)
        .eq("reading_type", reading_type)
        .eq("reading_date", today_str())
        .execute()
    )

    if result.data:
        return result.data[0]

    return None


@dp.message(Command("start"))
async def start_handler(message: Message):
    get_or_create_user(message)

    text = """Привет. Я Tarot-бот 🔮

Выбери действие на кнопках ниже:

🌞 Карта дня — личная карта до конца дня
🔮 3 карты — прошлое / настоящее / будущее
🧬 Карты рождения — 5 карт по дате и времени рождения
✍️ Расклад на ситуацию — задай свой вопрос

Пока это развлекательный ботик. Не воспринимай расклады как финансовый, медицинский или юридический совет."""

    await message.answer(text, reply_markup=MAIN_MENU)


@dp.message(Command("birth"))
async def birth_handler(message: Message):
    user = get_or_create_user(message)

    raw = message.text.replace("/birth", "").strip()

    try:
        birth_dt = datetime.strptime(raw, "%Y-%m-%d %H:%M")
    except ValueError:
        await message.answer(
            "Напиши дату и время рождения в формате:\n\n"
            "`/birth 2000-05-17 14:30`",

        )
        return

    birth_dt = birth_dt.replace(tzinfo=TZ)

    supabase.table("users").update({
        "birth_datetime": birth_dt.isoformat()
    }).eq("id", user["id"]).execute()

    await message.answer("Дата и время рождения сохранены ✨")


@dp.message(Command("birth_cards"))
async def birth_cards_handler(message: Message):
    user = get_or_create_user(message)

    full_user = (
        supabase.table("users")
        .select("*")
        .eq("id", user["id"])
        .execute()
    ).data[0]

    if not full_user.get("birth_datetime"):
        await message.answer(
            "Сначала сохрани дату рождения:\n\n"
            "`/birth 2000-05-17 14:30`",

        )
        return

    seed = make_seed("birth", full_user["birth_datetime"])
    cards = draw_cards(seed, 5, allow_reversed=False)

    text = (
        "Твой личный набор карт по дате и времени рождения:\n\n"
        "1 — архетип личности\n"
        "2 — внутренний ресурс\n"
        "3 — главный урок\n"
        "4 — скрытая энергия\n"
        "5 — направление пути\n\n"
        f"{format_cards(cards)}"
    )

    await message.answer(text)


@dp.message(Command("day"))
async def daily_card_handler(message: Message):
    user = get_or_create_user(message)

    existing = get_daily_reading(user["id"], "daily_card")

    if existing:
        cards = existing["cards"]
    else:
        seed = make_seed("daily_card", user["telegram_id"], today_str())
        cards = draw_cards(seed, 1, allow_reversed=True)
        save_reading(user["id"], "daily_card", cards)

    card = cards[0]

    text = f"""Карта дня на сегодня: {card_title(card)}

Смысл карты: {get_card_meaning(card)}.

Эта карта закреплена за тобой до конца текущего дня."""

    image_url = get_card_image_url(card)

    if image_url:
        await message.answer_photo(photo=image_url, caption=text)
    else:
        await message.answer(text)


@dp.message(Command("three"))
async def three_cards_handler(message: Message):
    user = get_or_create_user(message)

    existing = get_daily_reading(user["id"], "three_cards")

    if existing:
        cards = existing["cards"]
    else:
        seed = make_seed("three_cards", user["telegram_id"], today_str())
        cards = draw_cards(seed, 3, allow_reversed=True)
        save_reading(user["id"], "three_cards", cards)

    positions = [
        ("Прошлое", cards[0]),
        ("Настоящее", cards[1]),
        ("Будущее", cards[2]),
    ]

    await message.answer("Расклад на сегодня: прошлое / настоящее / будущее")

    for position, card in positions:
        caption = f"""{position}: {card_title(card)}
{get_card_meaning(card)}"""

        image_url = get_card_image_url(card)

        if image_url:
            await message.answer_photo(photo=image_url, caption=caption)
        else:
            await message.answer(caption)

    await message.answer("Этот расклад закреплён за тобой до конца текущего дня.")


@dp.message(Command("situation"))
async def situation_handler(message: Message):
    user = get_or_create_user(message)

    question = message.text.replace("/situation", "").strip()

    if not question:
        await message.answer("""Напиши вопрос после команды, например:

/situation стоит ли мне менять работу?""")
        return

    seed = make_seed("situation", user["telegram_id"], today_str(), question)
    cards = draw_cards(seed, 3, allow_reversed=True)

    save_reading(
        user_id=user["id"],
        reading_type="situation",
        cards=cards,
        question_text=question,
    )

    positions = [
        ("Суть ситуации", cards[0]),
        ("Что влияет скрыто", cards[1]),
        ("Возможное направление", cards[2]),
    ]

    await message.answer(f"""Вопрос: {question}

Расклад на ситуацию:""")

    for position, card in positions:
        caption = f"""{position}: {card_title(card)}
{get_card_meaning(card)}"""

        image_url = get_card_image_url(card)

        if image_url:
            await message.answer_photo(photo=image_url, caption=caption)
        else:
            await message.answer(caption)

    await message.answer(
        "Совет: воспринимай расклад как способ посмотреть на ситуацию под другим углом, а не как окончательное решение.",
        reply_markup=MAIN_MENU,
    )


@dp.message(F.text == "🌞 Карта дня")
async def daily_card_button_handler(message: Message):
    await daily_card_handler(message)


@dp.message(F.text == "🔮 3 карты")
async def three_cards_button_handler(message: Message):
    await three_cards_handler(message)


@dp.message(F.text == "🧬 Карты рождения")
async def birth_cards_button_handler(message: Message):
    await birth_cards_handler(message)


@dp.message(F.text == "📅 Сохранить дату рождения")
async def ask_birth_datetime_handler(message: Message):
    USER_WAITING_ACTION[message.from_user.id] = "birth_datetime"

    await message.answer(
        "Напиши дату и время рождения в формате:\n\n"
        "2000-05-17 14:30"
    )


@dp.message(F.text == "✍️ Расклад на ситуацию")
async def ask_situation_handler(message: Message):
    USER_WAITING_ACTION[message.from_user.id] = "situation"

    await message.answer(
        "Опиши ситуацию или задай вопрос.\n\n"
        "Например:\n"
        "Стоит ли мне менять работу?"
    )


@dp.message(F.text == "ℹ️ Помощь")
async def help_button_handler(message: Message):
    text = (
        "Что умеет бот:\n\n"
        "🌞 Карта дня — одна карта, закреплена за тобой до конца дня.\n\n"
        "🔮 3 карты — расклад прошлое / настоящее / будущее. "
        "Тоже закрепляется до конца текущего дня.\n\n"
        "🧬 Карты рождения — персональный набор из 5 карт по дате и времени рождения.\n\n"
        "✍️ Расклад на ситуацию — ты пишешь вопрос, бот выбирает карты и даёт трактовку.\n\n"
        "📅 Сохранить дату рождения — нужно для персональных карт рождения."
    )

    await message.answer(text, reply_markup=MAIN_MENU)


@dp.message()
async def plain_text_handler(message: Message):
    user_id = message.from_user.id
    action = USER_WAITING_ACTION.get(user_id)

    if action == "birth_datetime":
        raw = message.text.strip()

        try:
            datetime.strptime(raw, "%Y-%m-%d %H:%M")
        except ValueError:
            await message.answer(
                "Не получилось распознать дату.\n\n"
                "Напиши в формате:\n"
                "2000-05-17 14:30"
            )
            return

        USER_WAITING_ACTION.pop(user_id, None)

        message.text = f"/birth {raw}"
        await birth_handler(message)

        await message.answer(
            "Теперь можно открыть карты рождения.",
            reply_markup=MAIN_MENU
        )
        return

    if action == "situation":
        question = message.text.strip()

        if not question:
            await message.answer("Напиши вопрос или коротко опиши ситуацию.")
            return

        USER_WAITING_ACTION.pop(user_id, None)

        message.text = f"/situation {question}"
        await situation_handler(message)

        await message.answer(
            "Можешь выбрать следующий расклад.",
            reply_markup=MAIN_MENU
        )
        return

    await message.answer(
        "Выбери действие на кнопках ниже.",
        reply_markup=MAIN_MENU
    )


@app.get("/")
async def root():
    return {"status": "ok", "service": "tarot-bot"}


@app.get("/health")
async def health():
    return {"ok": True}


@app.on_event("startup")
async def on_startup():
    if BASE_URL:
        webhook_url = f"{BASE_URL}/webhook/{WEBHOOK_SECRET}"
        await bot.set_webhook(webhook_url)


@app.post("/webhook/{secret}")
async def telegram_webhook(secret: str, request: Request):
    if secret != WEBHOOK_SECRET:
        return {"ok": False}

    data = await request.json()
    update = Update.model_validate(data, context={"bot": bot})
    await dp.feed_update(bot, update)

    return {"ok": True}