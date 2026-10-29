"""Общий обработчик ошибок.

Ошибка в любом обработчике попадает в лог, пользователь получает понятное
сообщение, а бот продолжает работать (NFR-9.3).
"""

import logging

from aiogram.types import ErrorEvent

logger = logging.getLogger("habitbot.errors")

ERROR_TEXT = "😔 Что-то пошло не так. Попробуйте ещё раз чуть позже."


async def on_error(event: ErrorEvent) -> bool:
    update = event.update
    logger.error(
        "Ошибка при обработке update=%s: %r",
        getattr(update, "update_id", None),
        event.exception,
        exc_info=event.exception,
    )

    message = getattr(update, "message", None)
    if message is not None:
        try:
            await message.answer(ERROR_TEXT)
        except Exception:  # ответ не должен ронять бота, даже если Telegram недоступен
            logger.exception("Не удалось отправить пользователю сообщение об ошибке")
    return True
