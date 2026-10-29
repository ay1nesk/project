"""Проверки каркаса бота по критериям приёмки задачи #12 [2.1.3]."""

import logging
from types import SimpleNamespace
from unittest.mock import AsyncMock

from bot.handlers import common, get_routers, start
from bot.handlers.errors import ERROR_TEXT, on_error
from bot.main import BOT_COMMANDS
from bot.middlewares.logging_middleware import LoggingMiddleware


def fake_message(first_name="Ксения"):
    return SimpleNamespace(from_user=SimpleNamespace(first_name=first_name), answer=AsyncMock())


async def test_start_greets_user_and_points_to_help():
    message = fake_message()
    await start.cmd_start(message)
    text = message.answer.await_args.args[0]
    assert "Ксения" in text
    assert "/help" in text


async def test_start_escapes_html_in_name():
    message = fake_message("<b>Хакер</b>")
    await start.cmd_start(message)
    text = message.answer.await_args.args[0]
    assert "<b>Хакер</b>" not in text
    assert "&lt;b&gt;Хакер&lt;/b&gt;" in text


async def test_help_lists_all_menu_commands():
    message = fake_message()
    await start.cmd_help(message)
    text = message.answer.await_args.args[0]
    for command in BOT_COMMANDS:
        assert f"/{command.command}" in text


async def test_unknown_command_hints_help():
    message = fake_message()
    await common.unknown_command(message)
    assert "/help" in message.answer.await_args.args[0]


async def test_plain_text_hints_help():
    message = fake_message()
    await common.any_message(message)
    assert "/help" in message.answer.await_args.args[0]


def test_fallback_router_is_last():
    routers = get_routers()
    assert routers[-1] is common.router
    assert routers[0] is start.router


def test_dispatcher_is_assembled(dp, settings):
    assert [r.name for r in dp.sub_routers] == [r.name for r in get_routers()]
    assert dp["settings"] is settings


async def test_error_is_logged_and_user_is_notified(caplog):
    message = fake_message()
    event = SimpleNamespace(
        update=SimpleNamespace(update_id=7, message=message),
        exception=RuntimeError("boom"),
    )
    with caplog.at_level(logging.ERROR):
        handled = await on_error(event)
    assert handled is True
    message.answer.assert_awaited_once_with(ERROR_TEXT)
    assert "update=7" in caplog.text


async def test_error_handler_survives_failed_reply():
    message = fake_message()
    message.answer.side_effect = RuntimeError("Telegram недоступен")
    event = SimpleNamespace(update=SimpleNamespace(update_id=8, message=message), exception=ValueError())
    assert await on_error(event) is True


async def test_logging_middleware_logs_update(caplog):
    handler = AsyncMock(return_value="ok")
    event = SimpleNamespace(update_id=42, event_type="message")
    data = {"event_from_user": SimpleNamespace(id=555)}
    with caplog.at_level(logging.INFO):
        result = await LoggingMiddleware()(handler, event, data)
    assert result == "ok"
    assert "update=42 type=message user=555" in caplog.text
