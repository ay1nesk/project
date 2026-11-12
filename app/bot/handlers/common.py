"""Ответы на всё, что не обработали другие роутеры.

Подключается последним (см. bot/handlers/__init__.py), поэтому срабатывает,
только если сообщение не подошло ни под одну команду.
"""

from aiogram import F, Router
from aiogram.types import Message

router = Router(name="common")

UNKNOWN_COMMAND_TEXT = "Не знаю такую команду 🤔\nСписок команд — /help"
NOT_A_COMMAND_TEXT = "Я пока понимаю только команды. Список команд — /help"


@router.message(F.text.startswith("/"))
async def unknown_command(message: Message) -> None:
    await message.answer(UNKNOWN_COMMAND_TEXT)


@router.message()
async def any_message(message: Message) -> None:
    await message.answer(NOT_A_COMMAND_TEXT)
