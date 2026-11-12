"""Подключение к базе данных.

На сервере — PostgreSQL (asyncpg), при разработке и в тестах — файл SQLite
(aiosqlite). Адрес задаётся переменной DATABASE_URL в app/.env.
"""

from sqlalchemy import event, text
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, async_sessionmaker, create_async_engine


def _enable_sqlite_foreign_keys(dbapi_connection, _record) -> None:
    # SQLite по умолчанию не проверяет внешние ключи и не делает ON DELETE CASCADE
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA foreign_keys=ON")
    cursor.close()


def create_engine(database_url: str, echo: bool = False) -> AsyncEngine:
    engine = create_async_engine(database_url, echo=echo)
    if engine.dialect.name == "sqlite":
        event.listen(engine.sync_engine, "connect", _enable_sqlite_foreign_keys)
    return engine


def create_sessionmaker(engine: AsyncEngine) -> async_sessionmaker[AsyncSession]:
    # expire_on_commit=False — объекты остаются доступны после commit()
    return async_sessionmaker(engine, expire_on_commit=False)


async def check_connection(engine: AsyncEngine) -> None:
    """Проверяет, что база доступна. Бросает исключение, если нет."""
    async with engine.connect() as connection:
        await connection.execute(text("SELECT 1"))
