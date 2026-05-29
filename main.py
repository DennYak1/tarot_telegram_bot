import os
import re
import random
import hashlib
import asyncio
from datetime import datetime, date
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from dotenv import load_dotenv

load_dotenv()

from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from aiogram import Bot, Dispatcher, F
from aiogram.filters import Command
from aiogram.types import Message, Update, ReplyKeyboardMarkup, KeyboardButton
from supabase import create_client


APP_VERSION = "2026-05-29-card-descriptions-v4"

BOT_TOKEN = os.getenv("BOT_TOKEN")
BASE_URL = os.getenv("BASE_URL")
WEBHOOK_SECRET = os.getenv("WEBHOOK_SECRET", "tarot-secret")
CRON_SECRET = os.getenv("CRON_SECRET", WEBHOOK_SECRET)

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_SERVICE_KEY = os.getenv("SUPABASE_SERVICE_KEY")

DEFAULT_TIMEZONE = "Europe/Berlin"
DEFAULT_DAILY_POST_TIME = "08:00"
TZ = ZoneInfo(DEFAULT_TIMEZONE)

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
    # Старшие арканы
    "Шут": "новое начало, свобода, спонтанность, доверие пути",
    "Маг": "воля, действие, инициатива, умение влиять на ситуацию",
    "Верховная Жрица": "интуиция, скрытая информация, внутреннее знание, тишина",
    "Императрица": "рост, забота, изобилие, созидание, телесный комфорт",
    "Император": "структура, контроль, порядок, ответственность, опора",
    "Иерофант": "традиции, наставничество, правила, обучение, духовный совет",
    "Влюблённые": "выбор, отношения, притяжение, ценности, согласие сердца",
    "Колесница": "движение, победа, дисциплина, управление курсом, рывок вперёд",
    "Сила": "выдержка, мягкая власть, смелость, внутренняя устойчивость",
    "Отшельник": "уединение, поиск смысла, пауза, глубокий анализ, мудрость",
    "Колесо Фортуны": "перемены, цикл, шанс, поворот событий, движение судьбы",
    "Справедливость": "баланс, честность, закон причины и следствия, ясное решение",
    "Повешенный": "пауза, переоценка, новый взгляд, отпускание контроля",
    "Смерть": "завершение этапа, трансформация, освобождение, новый цикл",
    "Умеренность": "гармония, терпение, восстановление баланса, мягкое течение",
    "Дьявол": "искушение, зависимость, привязки, страсть, скрытые ограничения",
    "Башня": "резкие перемены, разрушение старого, правда без прикрас, освобождение",
    "Звезда": "надежда, вдохновение, исцеление, вера в путь, мягкий свет",
    "Луна": "сомнения, иллюзии, тревожность, интуитивные сигналы, неясность",
    "Солнце": "ясность, успех, радость, открытость, жизненная энергия",
    "Суд": "пробуждение, итог, важное осознание, переход на новый уровень",
    "Мир": "завершение, целостность, результат, признание, новый горизонт",

    # Кубки
    "Туз Кубков": "новое чувство, эмоциональное открытие, вдохновение, сердечный импульс",
    "Двойка Кубков": "взаимность, союз, симпатия, примирение, эмоциональный контакт",
    "Тройка Кубков": "радость общения, поддержка друзей, праздник, лёгкость, объединение",
    "Четвёрка Кубков": "пауза в чувствах, апатия, переоценка желаний, закрытость к новому",
    "Пятёрка Кубков": "сожаление, разочарование, потеря фокуса, необходимость увидеть оставшееся",
    "Шестёрка Кубков": "память, ностальгия, доброта, прошлое, знакомые эмоции",
    "Семёрка Кубков": "много вариантов, мечты, фантазии, соблазны, сложность выбора",
    "Восьмёрка Кубков": "уход от прежнего, эмоциональное взросление, поиск большего смысла",
    "Девятка Кубков": "удовлетворение, желание, личная радость, эмоциональный комфорт",
    "Десятка Кубков": "гармония, семья, эмоциональная полнота, мир в отношениях",
    "Паж Кубков": "нежное сообщение, робкое чувство, творческий импульс, эмоциональная новизна",
    "Рыцарь Кубков": "романтика, предложение, идеализм, движение за сердцем",
    "Королева Кубков": "эмпатия, забота, тонкая интуиция, эмоциональная глубина",
    "Король Кубков": "эмоциональная зрелость, спокойствие, мудрое управление чувствами",

    # Пентакли
    "Туз Пентаклей": "материальный шанс, новый ресурс, практический старт, возможность роста",
    "Двойка Пентаклей": "баланс дел, гибкость, управление ресурсами, несколько задач сразу",
    "Тройка Пентаклей": "мастерство, сотрудничество, признание навыков, работа в команде",
    "Четвёрка Пентаклей": "сохранение ресурсов, контроль, стабильность, страх потерять достигнутое",
    "Пятёрка Пентаклей": "нехватка, тревога о деньгах или поддержке, период испытаний",
    "Шестёрка Пентаклей": "обмен, помощь, щедрость, поддержка, баланс отдачи и получения",
    "Семёрка Пентаклей": "ожидание результата, терпение, вложения, оценка прогресса",
    "Восьмёрка Пентаклей": "труд, практика, ремесло, улучшение навыков, дисциплина",
    "Девятка Пентаклей": "самодостаточность, комфорт, личные достижения, независимость",
    "Десятка Пентаклей": "устойчивость, семья, наследие, долгосрочный результат, прочная база",
    "Паж Пентаклей": "учёба, практический план, первые шаги, интерес к делу",
    "Рыцарь Пентаклей": "надёжность, медленное движение, ответственность, стабильный труд",
    "Королева Пентаклей": "забота, практичность, уют, ресурсность, земная мудрость",
    "Король Пентаклей": "достаток, управление ресурсами, статус, уверенная материальная опора",

    # Мечи
    "Туз Мечей": "ясная мысль, правда, решение, интеллектуальный прорыв, честность",
    "Двойка Мечей": "выбор, пауза, внутренний конфликт, необходимость принять решение",
    "Тройка Мечей": "боль, разочарование, честное признание сложных чувств",
    "Четвёрка Мечей": "отдых, восстановление, тишина, пауза перед новым этапом",
    "Пятёрка Мечей": "конфликт, спор, победа с потерями, напряжённая коммуникация",
    "Шестёрка Мечей": "переход, движение к спокойствию, дистанция от проблемы",
    "Семёрка Мечей": "стратегия, скрытность, обходной путь, необходимость осторожности",
    "Восьмёрка Мечей": "ограничения, страхи, ловушка мыслей, ощущение невозможности выбора",
    "Девятка Мечей": "тревога, бессонные мысли, переживания, внутреннее давление",
    "Десятка Мечей": "болезненный финал, завершение кризиса, точка невозврата",
    "Паж Мечей": "наблюдение, новости, любопытство, осторожная коммуникация, анализ",
    "Рыцарь Мечей": "резкое движение, напор, скорость, прямота, борьба за идею",
    "Королева Мечей": "ясность, независимость, честность, границы, трезвая оценка",
    "Король Мечей": "разум, стратегия, власть слова, логика, строгая позиция",

    # Жезлы
    "Туз Жезлов": "новый импульс, энергия, вдохновение, страсть, начало действия",
    "Двойка Жезлов": "планирование, выбор направления, взгляд вперёд, личная стратегия",
    "Тройка Жезлов": "расширение, ожидание результата, перспективы, рост горизонтов",
    "Четвёрка Жезлов": "стабильность, радость, дом, праздник, чувство опоры",
    "Пятёрка Жезлов": "конкуренция, спор, столкновение интересов, активная борьба",
    "Шестёрка Жезлов": "победа, признание, уверенность, видимый успех, поддержка окружения",
    "Семёрка Жезлов": "защита позиции, стойкость, давление, необходимость отстоять своё",
    "Восьмёрка Жезлов": "быстрые события, движение, новости, ускорение, импульс",
    "Девятка Жезлов": "выдержка, настороженность, опыт, готовность защищаться",
    "Десятка Жезлов": "нагрузка, ответственность, усталость, необходимость распределить силы",
    "Паж Жезлов": "новая идея, энтузиазм, сообщение, интерес к приключению",
    "Рыцарь Жезлов": "смелое действие, страсть, скорость, риск, желание перемен",
    "Королева Жезлов": "харизма, уверенность, самостоятельность, притяжение, творческая сила",
    "Король Жезлов": "лидерство, масштаб, решительность, предпринимательская энергия, влияние",
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
            KeyboardButton(text="⚙️ Автопостинг"),
        ],
        [
            KeyboardButton(text="ℹ️ Помощь"),
        ],
    ],
    resize_keyboard=True,
    input_field_placeholder="Выберите действие",
)

AUTOPOST_MENU = ReplyKeyboardMarkup(
    keyboard=[
        [
            KeyboardButton(text="✅ Включить автопостинг"),
            KeyboardButton(text="🚫 Выключить автопостинг"),
        ],
        [
            KeyboardButton(text="🕗 Изменить время"),
            KeyboardButton(text="🌍 Изменить часовой пояс"),
        ],
        [
            KeyboardButton(text="📨 Отправить карту сейчас"),
            KeyboardButton(text="⬅️ Главное меню"),
        ],
    ],
    resize_keyboard=True,
    input_field_placeholder="Настройки автопостинга",
)

USER_WAITING_ACTION: dict[int, str] = {}


def safe_timezone(timezone_name: str | None) -> ZoneInfo:
    try:
        return ZoneInfo(timezone_name or DEFAULT_TIMEZONE)
    except ZoneInfoNotFoundError:
        return ZoneInfo(DEFAULT_TIMEZONE)


def today_str(timezone_name: str | None = None) -> str:
    tz = safe_timezone(timezone_name)
    return datetime.now(tz).date().isoformat()


def current_time_hhmm(timezone_name: str | None = None) -> str:
    tz = safe_timezone(timezone_name)
    return datetime.now(tz).strftime("%H:%M")


def normalize_time(value: str) -> str | None:
    raw = value.strip()
    match = re.fullmatch(r"(\d{1,2}):(\d{2})", raw)
    if not match:
        return None

    hour = int(match.group(1))
    minute = int(match.group(2))

    if hour < 0 or hour > 23 or minute < 0 or minute > 59:
        return None

    return f"{hour:02d}:{minute:02d}"


def looks_like_birth_datetime(value: str) -> bool:
    try:
        datetime.strptime(value.strip(), "%Y-%m-%d %H:%M")
        return True
    except ValueError:
        return False


def make_seed(*parts: str) -> int:
    raw = "|".join(str(part) for part in parts)
    digest = hashlib.sha256(raw.encode("utf-8")).hexdigest()
    return int(digest, 16)


def draw_cards(seed: int, count: int, allow_reversed: bool = True) -> list[dict]:
    rng = random.Random(seed)
    deck = TAROT_CARDS.copy()
    rng.shuffle(deck)

    result = []

    for card_name_value in deck[:count]:
        result.append({
            "name": card_name_value,
            "reversed": rng.choice([False, True]) if allow_reversed else False,
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
        return f"{name} — <b>перевёрнутая</b>"

    return name


def get_card_meaning(card) -> str:
    name = card_name(card)

    if card_is_reversed(card):
        return REVERSED_CARD_MEANINGS.get(
            name,
            "энергия карты проявляется нестабильно, заблокировано или требует внутренней переоценки",
        )

    return CARD_MEANINGS.get(name, "толкование пока не добавлено")


def format_cards(cards: list) -> str:
    lines = []

    for index, card in enumerate(cards, start=1):
        lines.append(f"{index}. {card_title(card)} — {get_card_meaning(card)}")

    return "\n".join(lines)


def get_card_image_url(card) -> str | None:
    name = card_name(card)
    filename = CARD_IMAGES.get(name)

    if not filename:
        print(f"[CARD_IMAGE] Не найден файл для карты: {name}")
        return None

    public_base_url = BASE_URL or "https://tarot-telegram-bot-0hfs.onrender.com"
    return f"{public_base_url.rstrip('/')}/static/cards/{filename}"


async def answer_card(message: Message, card, caption: str):
    image_url = get_card_image_url(card)

    if image_url:
        try:
            await message.answer_photo(photo=image_url, caption=caption, parse_mode="HTML")
            return
        except Exception as exc:
            print(f"[TELEGRAM_PHOTO_ERROR] {exc}")

    await message.answer(caption, parse_mode="HTML")


async def send_card_to_chat(chat_id: int, card, caption: str):
    image_url = get_card_image_url(card)

    if image_url:
        try:
            await bot.send_photo(chat_id=chat_id, photo=image_url, caption=caption, parse_mode="HTML")
            return
        except Exception as exc:
            print(f"[TELEGRAM_PHOTO_ERROR] {exc}")

    await bot.send_message(chat_id=chat_id, text=caption, parse_mode="HTML")


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

    payload = {
        "telegram_id": telegram_id,
        "username": username,
        "first_name": first_name,
    }

    try:
        payload.update({
            "timezone": DEFAULT_TIMEZONE,
            "daily_post_enabled": True,
            "daily_post_time": DEFAULT_DAILY_POST_TIME,
        })

        created = supabase.table("users").insert(payload).execute()
        return created.data[0]
    except Exception as exc:
        print(f"[USER_CREATE_EXTENDED_FIELDS_ERROR] {exc}")

        fallback_payload = {
            "telegram_id": telegram_id,
            "username": username,
            "first_name": first_name,
        }
        created = supabase.table("users").insert(fallback_payload).execute()
        return created.data[0]


def get_user_by_telegram_id(telegram_id: int):
    result = (
        supabase.table("users")
        .select("*")
        .eq("telegram_id", telegram_id)
        .execute()
    )

    if result.data:
        return result.data[0]

    return None


def get_user_by_internal_id(user_id: int):
    result = supabase.table("users").select("*").eq("id", user_id).execute()
    if result.data:
        return result.data[0]
    return None


def update_user(user_id: int, payload: dict):
    return supabase.table("users").update(payload).eq("id", user_id).execute()


def user_timezone(user: dict | None) -> str:
    if not user:
        return DEFAULT_TIMEZONE
    return user.get("timezone") or DEFAULT_TIMEZONE


def user_daily_time(user: dict | None) -> str:
    if not user:
        return DEFAULT_DAILY_POST_TIME
    return user.get("daily_post_time") or DEFAULT_DAILY_POST_TIME


def user_daily_enabled(user: dict | None) -> bool:
    if not user:
        return True
    value = user.get("daily_post_enabled")
    if value is None:
        return True
    return bool(value)


def save_reading(
    user_id: int,
    reading_type: str,
    cards: list,
    question_text: str | None = None,
    reading_date: str | None = None,
):
    payload = {
        "user_id": user_id,
        "reading_type": reading_type,
        "reading_date": reading_date or today_str(),
        "question_text": question_text,
        "cards": cards,
    }

    return supabase.table("readings").insert(payload).execute()


def get_daily_reading(user_id: int, reading_type: str, reading_date: str | None = None):
    result = (
        supabase.table("readings")
        .select("*")
        .eq("user_id", user_id)
        .eq("reading_type", reading_type)
        .eq("reading_date", reading_date or today_str())
        .execute()
    )

    if result.data:
        return result.data[0]

    return None


def get_or_create_daily_card_for_user(user: dict):
    tz_name = user_timezone(user)
    local_date = today_str(tz_name)
    existing = get_daily_reading(user["id"], "daily_card", local_date)

    if existing:
        cards = existing["cards"]
    else:
        seed = make_seed("daily_card", user["telegram_id"], local_date)
        cards = draw_cards(seed, 1, allow_reversed=True)
        save_reading(user["id"], "daily_card", cards, reading_date=local_date)

    return cards[0], local_date


async def send_daily_card_for_user(user: dict, chat_id: int | None = None, prefix: str = "Карта дня на сегодня"):
    card, local_date = get_or_create_daily_card_for_user(user)

    text = f"""{prefix}: {card_title(card)}

Смысл карты: {get_card_meaning(card)}.

Дата: {local_date}
Эта карта закреплена за тобой до конца текущего дня."""

    await send_card_to_chat(chat_id or int(user["telegram_id"]), card, text)


async def send_birth_cards_for_message(message: Message, user: dict):
    full_user = get_user_by_internal_id(user["id"])

    if not full_user or not full_user.get("birth_datetime"):
        await message.answer(
            "Сначала сохрани дату рождения. Нажми «📅 Сохранить дату рождения» "
            "или напиши, например: 2000-05-17 14:30",
            reply_markup=MAIN_MENU,
        )
        return

    seed = make_seed("birth", full_user["birth_datetime"])
    cards = draw_cards(seed, 5, allow_reversed=False)

    positions = [
        "Архетип личности",
        "Внутренний ресурс",
        "Главный урок",
        "Скрытая энергия",
        "Направление пути",
    ]

    await message.answer("Твой личный набор карт по дате и времени рождения:")

    for position, card in zip(positions, cards):
        caption = f"""{position}: {card_title(card)}
{get_card_meaning(card)}"""
        await answer_card(message, card, caption)


async def send_three_cards_for_message(message: Message, user: dict):
    local_date = today_str(user_timezone(user))
    existing = get_daily_reading(user["id"], "three_cards", local_date)

    if existing:
        cards = existing["cards"]
    else:
        seed = make_seed("three_cards", user["telegram_id"], local_date)
        cards = draw_cards(seed, 3, allow_reversed=True)
        save_reading(user["id"], "three_cards", cards, reading_date=local_date)

    positions = [
        ("Прошлое", cards[0]),
        ("Настоящее", cards[1]),
        ("Будущее", cards[2]),
    ]

    await message.answer("Расклад на сегодня: прошлое / настоящее / будущее")

    for position, card in positions:
        caption = f"""{position}: {card_title(card)}
{get_card_meaning(card)}"""
        await answer_card(message, card, caption)

    await message.answer("Этот расклад закреплён за тобой до конца текущего дня.")


async def send_situation_reading_for_message(message: Message, user: dict, question: str):
    question = question.strip()

    if not question:
        await message.answer("Напиши вопрос или коротко опиши ситуацию.")
        return

    seed = make_seed("situation", user["telegram_id"], today_str(user_timezone(user)), question)
    cards = draw_cards(seed, 3, allow_reversed=True)

    save_reading(
        user_id=user["id"],
        reading_type="situation",
        cards=cards,
        question_text=question,
        reading_date=today_str(user_timezone(user)),
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
        await answer_card(message, card, caption)

    await message.answer(
        "Совет: воспринимай расклад как способ посмотреть на ситуацию под другим углом, а не как окончательное решение.",
        reply_markup=MAIN_MENU,
    )


async def save_birth_datetime_for_message(message: Message, user: dict, raw: str):
    raw = raw.strip()

    try:
        birth_dt = datetime.strptime(raw, "%Y-%m-%d %H:%M")
    except ValueError:
        await message.answer(
            "Не получилось распознать дату. Напиши в формате:\n\n2000-05-17 14:30",
            reply_markup=MAIN_MENU,
        )
        return

    birth_dt = birth_dt.replace(tzinfo=safe_timezone(user_timezone(user)))

    update_user(user["id"], {"birth_datetime": birth_dt.isoformat()})
    await message.answer("Дата и время рождения сохранены ✨", reply_markup=MAIN_MENU)


def autopost_settings_text(user: dict) -> str:
    status = "включён ✅" if user_daily_enabled(user) else "выключен 🚫"
    return f"""⚙️ Автопостинг карты дня

Статус: {status}
Время: {user_daily_time(user)}
Часовой пояс: {user_timezone(user)}

По умолчанию автопостинг включён и стоит на 08:00 по локальному времени пользователя."""


async def show_autopost_settings(message: Message):
    user = get_or_create_user(message)
    await message.answer(autopost_settings_text(user), reply_markup=AUTOPOST_MENU)


async def process_daily_autoposts():
    processed = 0
    sent = 0
    skipped = 0
    errors = []

    try:
        users_result = (
            supabase.table("users")
            .select("*")
            .execute()
        )
    except Exception as exc:
        return {
            "ok": False,
            "error": f"Не удалось прочитать users. Возможно, не добавлены колонки автопостинга: {exc}",
        }

    for user in users_result.data or []:
        processed += 1

        try:
            if not user_daily_enabled(user):
                skipped += 1
                continue

            tz_name = user_timezone(user)
            local_today = today_str(tz_name)
            target_time = normalize_time(user_daily_time(user)) or DEFAULT_DAILY_POST_TIME
            now_hhmm = current_time_hhmm(tz_name)
            last_sent = user.get("last_daily_card_sent_date")

            if isinstance(last_sent, date):
                last_sent = last_sent.isoformat()

            if last_sent == local_today:
                skipped += 1
                continue

            if now_hhmm < target_time:
                skipped += 1
                continue

            await send_daily_card_for_user(
                user,
                chat_id=int(user["telegram_id"]),
                prefix="Твоя карта дня по расписанию",
            )

            try:
                update_user(user["id"], {"last_daily_card_sent_date": local_today})
            except Exception as update_exc:
                errors.append(f"user {user.get('id')} sent, but update failed: {update_exc}")

            sent += 1
        except Exception as exc:
            errors.append(f"user {user.get('id')}: {exc}")

    return {
        "ok": True,
        "processed": processed,
        "sent": sent,
        "skipped": skipped,
        "errors": errors,
    }


async def autopost_background_loop():
    while True:
        try:
            await process_daily_autoposts()
        except Exception as exc:
            print(f"[AUTOPOST_LOOP_ERROR] {exc}")
        await asyncio.sleep(300)


@dp.message(Command("start"))
async def start_handler(message: Message):
    get_or_create_user(message)

    text = f"""Привет. Я Tarot-бот 🔮

Выбери действие на кнопках ниже:

🌞 Карта дня — личная карта до конца дня
🔮 3 карты — прошлое / настоящее / будущее
🧬 Карты рождения — 5 карт по дате и времени рождения
✍️ Расклад на ситуацию — задай свой вопрос
⚙️ Автопостинг — ежедневная карта дня по расписанию

Версия: {APP_VERSION}

Пока это развлекательный ботик. Не воспринимай расклады как финансовый, медицинский или юридический совет."""

    await message.answer(text, reply_markup=MAIN_MENU)


@dp.message(Command("version"))
async def version_handler(message: Message):
    await message.answer(f"Версия бота: {APP_VERSION}", reply_markup=MAIN_MENU)


@dp.message(Command("birth"))
async def birth_handler(message: Message):
    user = get_or_create_user(message)
    raw = message.text.replace("/birth", "").strip()
    await save_birth_datetime_for_message(message, user, raw)


@dp.message(Command("birth_cards"))
async def birth_cards_handler(message: Message):
    user = get_or_create_user(message)
    await send_birth_cards_for_message(message, user)


@dp.message(Command("day"))
async def daily_card_handler(message: Message):
    user = get_or_create_user(message)
    await send_daily_card_for_user(user, chat_id=message.chat.id)


@dp.message(Command("daily_now"))
async def daily_now_handler(message: Message):
    user = get_or_create_user(message)
    await send_daily_card_for_user(user, chat_id=message.chat.id, prefix="Карта дня по запросу")


@dp.message(Command("three"))
async def three_cards_handler(message: Message):
    user = get_or_create_user(message)
    await send_three_cards_for_message(message, user)


@dp.message(Command("situation"))
async def situation_handler(message: Message):
    user = get_or_create_user(message)
    question = message.text.replace("/situation", "").strip()

    if not question:
        USER_WAITING_ACTION[message.from_user.id] = "situation"
        await message.answer(
            "Опиши ситуацию или задай вопрос. Например:\n\nСтоит ли мне менять работу?",
            reply_markup=MAIN_MENU,
        )
        return

    await send_situation_reading_for_message(message, user, question)


@dp.message(Command("autopost"))
async def autopost_command_handler(message: Message):
    await show_autopost_settings(message)


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
        "Напиши дату и время рождения в формате:\n\n2000-05-17 14:30",
        reply_markup=MAIN_MENU,
    )


@dp.message(F.text == "✍️ Расклад на ситуацию")
async def ask_situation_handler(message: Message):
    USER_WAITING_ACTION[message.from_user.id] = "situation"
    await message.answer(
        "Опиши ситуацию или задай вопрос.\n\nНапример:\nСтоит ли мне менять работу?",
        reply_markup=MAIN_MENU,
    )


@dp.message(F.text == "⚙️ Автопостинг")
async def autopost_button_handler(message: Message):
    await show_autopost_settings(message)


@dp.message(F.text == "✅ Включить автопостинг")
async def enable_autopost_handler(message: Message):
    user = get_or_create_user(message)
    try:
        update_user(user["id"], {"daily_post_enabled": True})
        user["daily_post_enabled"] = True
        await message.answer("Автопостинг включён ✅", reply_markup=AUTOPOST_MENU)
    except Exception as exc:
        await message.answer(
            f"Не удалось включить автопостинг. Проверь, что SQL-колонки добавлены в Supabase.\n\n{exc}",
            reply_markup=AUTOPOST_MENU,
        )


@dp.message(F.text == "🚫 Выключить автопостинг")
async def disable_autopost_handler(message: Message):
    user = get_or_create_user(message)
    try:
        update_user(user["id"], {"daily_post_enabled": False})
        user["daily_post_enabled"] = False
        await message.answer("Автопостинг выключен 🚫", reply_markup=AUTOPOST_MENU)
    except Exception as exc:
        await message.answer(
            f"Не удалось выключить автопостинг. Проверь, что SQL-колонки добавлены в Supabase.\n\n{exc}",
            reply_markup=AUTOPOST_MENU,
        )


@dp.message(F.text == "🕗 Изменить время")
async def change_autopost_time_handler(message: Message):
    USER_WAITING_ACTION[message.from_user.id] = "autopost_time"
    await message.answer("Напиши новое время в формате HH:MM, например: 08:00", reply_markup=AUTOPOST_MENU)


@dp.message(F.text == "🌍 Изменить часовой пояс")
async def change_timezone_handler(message: Message):
    USER_WAITING_ACTION[message.from_user.id] = "timezone"
    await message.answer(
        "Напиши часовой пояс в формате IANA.\n\nНапример:\nEurope/Berlin\nAsia/Tashkent\nEurope/Moscow",
        reply_markup=AUTOPOST_MENU,
    )


@dp.message(F.text == "📨 Отправить карту сейчас")
async def send_daily_now_button_handler(message: Message):
    await daily_now_handler(message)


@dp.message(F.text == "⬅️ Главное меню")
async def back_to_main_menu_handler(message: Message):
    USER_WAITING_ACTION.pop(message.from_user.id, None)
    await message.answer("Главное меню", reply_markup=MAIN_MENU)


@dp.message(F.text == "ℹ️ Помощь")
async def help_button_handler(message: Message):
    text = f"""Что умеет бот:

🌞 Карта дня — одна карта, закреплена за тобой до конца дня.

🔮 3 карты — расклад прошлое / настоящее / будущее. Тоже закрепляется до конца текущего дня.

🧬 Карты рождения — персональный набор из 5 карт по дате и времени рождения.

✍️ Расклад на ситуацию — ты пишешь вопрос, бот выбирает карты и даёт трактовку.

📅 Сохранить дату рождения — нужно для персональных карт рождения.

⚙️ Автопостинг — ежедневная карта дня по расписанию.

Версия: {APP_VERSION}"""

    await message.answer(text, reply_markup=MAIN_MENU)


@dp.message()
async def plain_text_handler(message: Message):
    user = get_or_create_user(message)
    user_id = message.from_user.id
    action = USER_WAITING_ACTION.get(user_id)
    raw = (message.text or "").strip()

    if not raw:
        await message.answer("Выбери действие на кнопках ниже.", reply_markup=MAIN_MENU)
        return

    if action == "birth_datetime" or looks_like_birth_datetime(raw):
        USER_WAITING_ACTION.pop(user_id, None)
        await save_birth_datetime_for_message(message, user, raw)
        return

    normalized_time = normalize_time(raw)

    if action == "autopost_time" or normalized_time:
        if not normalized_time:
            await message.answer("Не получилось распознать время. Напиши в формате HH:MM, например: 08:00")
            return

        USER_WAITING_ACTION.pop(user_id, None)

        try:
            update_user(user["id"], {"daily_post_time": normalized_time})
            await message.answer(f"Время автопостинга сохранено: {normalized_time}", reply_markup=AUTOPOST_MENU)
        except Exception as exc:
            await message.answer(
                f"Не удалось сохранить время. Проверь SQL-колонки в Supabase.\n\n{exc}",
                reply_markup=AUTOPOST_MENU,
            )
        return

    if action == "timezone" or "/" in raw:
        try:
            safe_timezone(raw)
        except Exception:
            await message.answer("Не получилось распознать часовой пояс. Пример: Europe/Berlin")
            return

        USER_WAITING_ACTION.pop(user_id, None)

        try:
            update_user(user["id"], {"timezone": raw})
            await message.answer(f"Часовой пояс сохранён: {raw}", reply_markup=AUTOPOST_MENU)
        except Exception as exc:
            await message.answer(
                f"Не удалось сохранить часовой пояс. Проверь SQL-колонки в Supabase.\n\n{exc}",
                reply_markup=AUTOPOST_MENU,
            )
        return

    if action == "situation" or len(raw) >= 8:
        USER_WAITING_ACTION.pop(user_id, None)
        await send_situation_reading_for_message(message, user, raw)
        return

    await message.answer("Выбери действие на кнопках ниже.", reply_markup=MAIN_MENU)


@app.get("/")
async def root():
    return {
        "status": "ok",
        "service": "tarot-bot",
        "version": APP_VERSION,
        "features": [
            "birth_cards_images",
            "situation_button",
            "daily_autopost",
            "manual_daily_now",
            "version_marker",
        ],
    }


@app.get("/health")
async def health():
    return {"ok": True, "version": APP_VERSION}


@app.get("/cron/daily-cards/{secret}")
async def cron_daily_cards(secret: str):
    if secret != CRON_SECRET:
        return {"ok": False, "error": "bad secret"}

    return await process_daily_autoposts()


@app.on_event("startup")
async def on_startup():
    if BASE_URL:
        webhook_url = f"{BASE_URL.rstrip('/')}/webhook/{WEBHOOK_SECRET}"
        await bot.set_webhook(webhook_url)

    if os.getenv("ENABLE_BACKGROUND_AUTOPOST", "1") == "1":
        asyncio.create_task(autopost_background_loop())


@app.post("/webhook/{secret}")
async def telegram_webhook(secret: str, request: Request):
    if secret != WEBHOOK_SECRET:
        return {"ok": False}

    data = await request.json()
    update = Update.model_validate(data, context={"bot": bot})
    await dp.feed_update(bot, update)

    return {"ok": True}
