"""Обработчики команд и кнопок, по одному модулю на функцию бота."""

from aiogram import Router

from bot.handlers import common, habits, reminders, start, stats, subscription


def get_routers() -> list[Router]:
    """Роутеры в порядке подключения.

    common подключается последним: он ловит всё, что не обработали остальные
    (неизвестные команды и произвольный текст).
    """
    return [
        start.router,
        habits.router,
        reminders.router,
        stats.router,
        subscription.router,
        common.router,
    ]
