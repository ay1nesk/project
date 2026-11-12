"""Сквозная проверка: апдейт проходит через Dispatcher, middleware и роутеры.

Вместо настоящего Telegram используется фейковая сессия, которая
запоминает отправленные ботом сообщения.
"""

import datetime

from aiogram import Bot
from aiogram.client.session.base import BaseSession
from aiogram.methods import SendMessage
from aiogram.types import Chat, Message, Update, User

from bot.handlers.common import UNKNOWN_COMMAND_TEXT
from bot.tests.conftest import TEST_TOKEN

USER = User(id=555, is_bot=False, first_name="Ксения")
CHAT = Chat(id=555, type="private")


class FakeSession(BaseSession):
    def __init__(self):
        super().__init__()
        self.sent: list[str] = []

    async def make_request(self, bot, method, timeout=None):
        assert isinstance(method, SendMessage)
        self.sent.append(method.text)
        return Message(message_id=len(self.sent), date=datetime.datetime.now(), chat=CHAT, text=method.text)

    async def stream_content(self, *args, **kwargs):  # pragma: no cover - не используется
        yield b""

    async def close(self):
        pass


def make_update(update_id: int, text: str) -> Update:
    return Update(
        update_id=update_id,
        message=Message(message_id=update_id, date=datetime.datetime.now(), chat=CHAT, from_user=USER, text=text),
    )


async def test_commands_are_routed_through_dispatcher(dp, caplog):
    session = FakeSession()
    bot = Bot(token=TEST_TOKEN, session=session)

    with caplog.at_level("INFO"):
        await dp.feed_update(bot, make_update(1, "/start"))
        await dp.feed_update(bot, make_update(2, "/help"))
        await dp.feed_update(bot, make_update(3, "/unknown"))

    assert "Ксения" in session.sent[0]
    assert "/start" in session.sent[1] and "/help" in session.sent[1]
    assert session.sent[2] == UNKNOWN_COMMAND_TEXT
    assert "update=1 type=message user=555" in caplog.text
