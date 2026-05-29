import os
import json
import random
import hashlib
from datetime import datetime
from zoneinfo import ZoneInfo

from dotenv import load_dotenv

load_dotenv()
from fastapi import FastAPI, Request
from aiogram import Bot, Dispatcher
from aiogram.filters import Command
from aiogram.types import Message, Update
from supabase import create_client



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

supabase = create_client(SUPABASE_URL, SUPABASE_SERVICE_KEY)


TAROT_CARDS = [
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


def today_str() -> str:
    return datetime.now(TZ).date().isoformat()


def make_seed(*parts: str) -> int:
    raw = "|".join(str(part) for part in parts)
    digest = hashlib.sha256(raw.encode("utf-8")).hexdigest()
    return int(digest, 16)


def draw_cards(seed: int, count: int) -> list[str]:
    rng = random.Random(seed)
    deck = TAROT_CARDS.copy()
    rng.shuffle(deck)
    return deck[:count]


def format_cards(cards: list[str]) -> str:
    lines = []
    for i, card in enumerate(cards, start=1):
        meaning = CARD_MEANINGS.get(card, "")
        lines.append(f"{i}. **{card}** — {meaning}")
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


def save_reading(user_id: int, reading_type: str, cards: list[str], question_text: str | None = None):
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

    text = (
        "Привет. Я Tarot-бот 🔮\n\n"
        "Что я умею:\n"
        "/birth 2000-05-17 14:30 — сохранить дату и время рождения\n"
        "/birth_cards — личный набор карт по дате рождения\n"
        "/day — карта дня\n"
        "/three — прошлое / настоящее / будущее\n"
        "/situation твой вопрос — расклад на ситуацию\n\n"
        "Пока это развлекательный MVP, не воспринимай расклады как финансовый, медицинский или юридический совет."
    )

    await message.answer(text, parse_mode="Markdown")


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
            parse_mode="Markdown"
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
            parse_mode="Markdown"
        )
        return

    seed = make_seed("birth", full_user["birth_datetime"])
    cards = draw_cards(seed, 5)

    text = (
        "Твой личный набор карт по дате и времени рождения:\n\n"
        "1 — архетип личности\n"
        "2 — внутренний ресурс\n"
        "3 — главный урок\n"
        "4 — скрытая энергия\n"
        "5 — направление пути\n\n"
        f"{format_cards(cards)}"
    )

    await message.answer(text, parse_mode="Markdown")


@dp.message(Command("day"))
async def daily_card_handler(message: Message):
    user = get_or_create_user(message)

    existing = get_daily_reading(user["id"], "daily_card")

    if existing:
        cards = existing["cards"]
    else:
        seed = make_seed("daily_card", user["telegram_id"], today_str())
        cards = draw_cards(seed, 1)
        save_reading(user["id"], "daily_card", cards)

    card = cards[0]

    text = (
        f"Карта дня на сегодня: **{card}**\n\n"
        f"Смысл карты: {CARD_MEANINGS.get(card)}.\n\n"
        "Эта карта закреплена за тобой до конца текущего дня."
    )

    await message.answer(text, parse_mode="Markdown")


@dp.message(Command("three"))
async def three_cards_handler(message: Message):
    user = get_or_create_user(message)

    existing = get_daily_reading(user["id"], "three_cards")

    if existing:
        cards = existing["cards"]
    else:
        seed = make_seed("three_cards", user["telegram_id"], today_str())
        cards = draw_cards(seed, 3)
        save_reading(user["id"], "three_cards", cards)

    text = (
        "Расклад на сегодня: **прошлое / настоящее / будущее**\n\n"
        f"**Прошлое:** {cards[0]} — {CARD_MEANINGS.get(cards[0])}\n\n"
        f"**Настоящее:** {cards[1]} — {CARD_MEANINGS.get(cards[1])}\n\n"
        f"**Будущее:** {cards[2]} — {CARD_MEANINGS.get(cards[2])}\n\n"
        "Этот расклад закреплён за тобой до конца текущего дня."
    )

    await message.answer(text, parse_mode="Markdown")


@dp.message(Command("situation"))
async def situation_handler(message: Message):
    user = get_or_create_user(message)

    question = message.text.replace("/situation", "").strip()

    if not question:
        await message.answer(
            "Напиши вопрос после команды, например:\n\n"
            "`/situation стоит ли мне менять работу?`",
            parse_mode="Markdown"
        )
        return

    seed = make_seed("situation", user["telegram_id"], today_str(), question)
    cards = draw_cards(seed, 3)

    save_reading(
        user_id=user["id"],
        reading_type="situation",
        cards=cards,
        question_text=question,
    )

    text = (
        f"Вопрос: **{question}**\n\n"
        "Расклад на ситуацию:\n\n"
        f"**1. Суть ситуации:** {cards[0]} — {CARD_MEANINGS.get(cards[0])}\n\n"
        f"**2. Что влияет скрыто:** {cards[1]} — {CARD_MEANINGS.get(cards[1])}\n\n"
        f"**3. Возможное направление:** {cards[2]} — {CARD_MEANINGS.get(cards[2])}\n\n"
        "Совет: воспринимай расклад как способ посмотреть на ситуацию под другим углом, а не как окончательное решение."
    )

    await message.answer(text, parse_mode="Markdown")


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