"""Точка входа HabitBot.

Запуск из папки app:  python -m bot
"""

from __future__ import annotations

import asyncio
import logging
import sys

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.exceptions import TelegramNetworkError, TelegramUnauthorizedError
from aiogram.types import BotCommand
from aiogram.utils.token import TokenValidationError
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from bot.config import ConfigError, Settings, load_settings, setup_logging
from bot.database.db import check_connection, create_engine, create_sessionmaker
from bot.handlers import get_routers
from bot.handlers.errors import on_error
from bot.middlewares.db import DbSessionMiddleware
from bot.middlewares.logging_middleware import LoggingMiddleware

logger = logging.getLogger("habitbot")

# Команды в меню Telegram (кнопка «Меню» рядом с полем ввода).
# Новые команды добавляются сюда по мере реализации задач бэклога.
BOT_COMMANDS = [
    BotCommand(command="start", description="Начать работу с ботом"),
    BotCommand(command="help", description="Список команд"),
]


def create_dispatcher(settings: Settings, sessionmaker: async_sessionmaker[AsyncSession]) -> Dispatcher:
    """Собирает Dispatcher: middleware, обработчики ошибок и роутеры."""
    dp = Dispatcher(settings=settings)
    dp.update.outer_middleware(LoggingMiddleware())
    dp.update.middleware(DbSessionMiddleware(sessionmaker))
    dp.errors.register(on_error)
    dp.include_routers(*get_routers())
    return dp


async def run_bot(settings: Settings) -> None:
    engine = create_engine(settings.database_url)
    try:
        await check_connection(engine)
        logger.info("База данных подключена: %s", engine.url.render_as_string(hide_password=True))
        dp = create_dispatcher(settings, create_sessionmaker(engine))
        # async with закрывает соединение с Telegram при любом завершении
        async with Bot(
            token=settings.bot_token,
            default=DefaultBotProperties(parse_mode=ParseMode.HTML),
        ) as bot:
            me = await bot.get_me()
            await bot.set_my_commands(BOT_COMMANDS)
            logger.info("Бот @%s запущен. Остановка — Ctrl+C", me.username)
            await dp.start_polling(bot)
    finally:
        await engine.dispose()


def main() -> int:
    try:
        settings = load_settings()
    except ConfigError as error:
        print(f"Ошибка настройки: {error}", file=sys.stderr)
        return 1

    setup_logging(settings.log_level)

    try:
        asyncio.run(run_bot(settings))
    except (TokenValidationError, TelegramUnauthorizedError):
        logger.error("Telegram не принял BOT_TOKEN. Проверьте токен в app/.env")
        return 1
    except (SQLAlchemyError, OSError) as error:
        logger.error("Нет подключения к базе данных: %s. Проверьте DATABASE_URL в app/.env", error)
        return 1
    except TelegramNetworkError as error:
        logger.error("Нет связи с Telegram: %s. Проверьте интернет и попробуйте снова", error)
        return 1
    except KeyboardInterrupt:
        pass
    logger.info("Бот остановлен")
    return 0


if __name__ == "__main__":
    sys.exit(main())
