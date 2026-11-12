"""Настройки бота из переменных окружения (файл app/.env).

Секреты (токен бота, пароли) хранятся только в .env, а не в коде (NFR-4.2).
"""

from __future__ import annotations

import logging
import os
from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv

ENV_FILE = Path(__file__).resolve().parent.parent / ".env"

LOG_LEVELS = ("DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL")


class ConfigError(Exception):
    """Ошибка в настройках: бот не может запуститься."""


@dataclass(frozen=True)
class Settings:
    bot_token: str
    admin_ids: frozenset[int]
    log_level: str
    database_url: str | None
    redis_url: str | None

    def is_admin(self, telegram_id: int) -> bool:
        return telegram_id in self.admin_ids


def _parse_admin_ids(raw: str) -> frozenset[int]:
    ids = set()
    for part in raw.split(","):
        part = part.strip()
        if not part:
            continue
        if not part.isdigit():
            raise ConfigError(
                f"ADMIN_IDS: «{part}» не похоже на Telegram ID. "
                "Укажите числа через запятую, например: 123456789,987654321"
            )
        ids.add(int(part))
    return frozenset(ids)


def load_settings(env: Mapping[str, str] | None = None) -> Settings:
    """Читает настройки из окружения.

    Если env не передан, сначала подгружается файл app/.env.
    Параметр env нужен для тестов.
    """
    if env is None:
        load_dotenv(ENV_FILE)
        env = os.environ

    bot_token = env.get("BOT_TOKEN", "").strip()
    if not bot_token:
        raise ConfigError(
            "Не задан BOT_TOKEN. Скопируйте app/.env.example в app/.env "
            "и впишите токен, который выдал @BotFather."
        )

    log_level = (env.get("LOG_LEVEL") or "INFO").strip().upper()
    if log_level not in LOG_LEVELS:
        raise ConfigError(f"LOG_LEVEL должен быть одним из: {', '.join(LOG_LEVELS)}")

    return Settings(
        bot_token=bot_token,
        admin_ids=_parse_admin_ids(env.get("ADMIN_IDS", "")),
        log_level=log_level,
        database_url=(env.get("DATABASE_URL") or "").strip() or None,
        redis_url=(env.get("REDIS_URL") or "").strip() or None,
    )


def setup_logging(level: str) -> None:
    logging.basicConfig(
        level=level,
        format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
