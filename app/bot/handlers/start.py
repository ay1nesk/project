"""Команды /start и /help (F1, FR-1.2, FR-1.5).

Регистрация пользователя в БД при первом /start добавится в задаче
#16 [2.3.1], выбор часового пояса — в #18 [2.3.3].
"""

from html import escape

from aiogram import Router
from aiogram.filters import Command, CommandStart
from aiogram.types import Message

router = Router(name="start")

START_TEXT = (
    "👋 Привет, {name}!\n\n"
    "Я <b>HabitBot</b> — помогаю формировать полезные привычки прямо в Telegram.\n\n"
    "Что я умею:\n"
    "📝 <b>Привычки</b> — создавай привычки и задавай для них расписание\n"
    "⏰ <b>Напоминания</b> — напомню вовремя, а выполнение отметишь одной кнопкой\n"
    "📊 <b>Статистика</b> — серии без пропусков и процент выполнения\n\n"
    "Список команд — /help"
)

HELP_TEXT = (
    "<b>Команды HabitBot</b>\n\n"
    "/start — начать работу с ботом\n"
    "/help — список команд\n\n"
    "Скоро появятся: /new — новая привычка, /habits — мои привычки, "
    "/stats — статистика, /settings — настройки."
)


@router.message(CommandStart())
async def cmd_start(message: Message) -> None:
    name = message.from_user.first_name if message.from_user else "друг"
    await message.answer(START_TEXT.format(name=escape(name)))


@router.message(Command("help"))
async def cmd_help(message: Message) -> None:
    await message.answer(HELP_TEXT)
