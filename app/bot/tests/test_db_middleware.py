"""Middleware сессии БД (задача #13)."""

from types import SimpleNamespace

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from bot.database.db import create_sessionmaker
from bot.middlewares.db import DbSessionMiddleware


async def test_handler_gets_working_session(engine):
    seen = {}

    async def handler(event, data):
        session = data["session"]
        seen["session"] = session
        return (await session.execute(text("SELECT 1"))).scalar()

    result = await DbSessionMiddleware(create_sessionmaker(engine))(handler, SimpleNamespace(), {})

    assert result == 1
    assert isinstance(seen["session"], AsyncSession)


async def test_session_is_closed_after_handler(engine):
    seen = {}

    async def handler(event, data):
        seen["session"] = data["session"]
        await data["session"].execute(text("SELECT 1"))

    await DbSessionMiddleware(create_sessionmaker(engine))(handler, SimpleNamespace(), {})

    assert not seen["session"].in_transaction()


async def test_dispatcher_passes_session_to_handlers(dp):
    from bot.middlewares.db import DbSessionMiddleware as Middleware

    assert any(isinstance(m, Middleware) for m in dp.update.middleware)
