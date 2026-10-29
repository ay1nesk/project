"""Логирование каждого входящего апдейта (NFR-9.3).

В лог пишутся тип апдейта, Telegram ID пользователя и время обработки
в миллисекундах — по нему проверяется NFR-2.1 (ответ не дольше 1 с).
"""

import logging
import time
from collections.abc import Awaitable, Callable
from typing import Any

from aiogram import BaseMiddleware
from aiogram.types import TelegramObject

logger = logging.getLogger("habitbot.updates")


class LoggingMiddleware(BaseMiddleware):
    async def __call__(
        self,
        handler: Callable[[TelegramObject, dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: dict[str, Any],
    ) -> Any:
        user = data.get("event_from_user")
        started = time.perf_counter()
        try:
            return await handler(event, data)
        finally:
            logger.info(
                "update=%s type=%s user=%s %.0f мс",
                getattr(event, "update_id", None),
                getattr(event, "event_type", type(event).__name__),
                user.id if user else None,
                (time.perf_counter() - started) * 1000,
            )
