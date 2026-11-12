import pytest
import pytest_asyncio

from bot.config import load_settings
from bot.database.db import create_engine, create_sessionmaker
from bot.database.models import Base
from bot.main import create_dispatcher

TEST_TOKEN = "123456:TEST-token"


@pytest.fixture(scope="session")
def settings(tmp_path_factory):
    db_file = tmp_path_factory.mktemp("db") / "dispatcher.db"
    return load_settings({"BOT_TOKEN": TEST_TOKEN, "DATABASE_URL": f"sqlite+aiosqlite:///{db_file}"})


@pytest.fixture(scope="session")
def dp(settings):
    # Роутер можно подключить только к одному Dispatcher, поэтому он один на все тесты,
    # как и в работающем боте.
    engine = create_engine(settings.database_url)
    return create_dispatcher(settings, create_sessionmaker(engine))


@pytest_asyncio.fixture
async def engine(tmp_path):
    """Пустая БД SQLite с таблицами из моделей — своя для каждого теста."""
    engine = create_engine(f"sqlite+aiosqlite:///{tmp_path / 'test.db'}")
    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)
    yield engine
    await engine.dispose()


@pytest_asyncio.fixture
async def session(engine):
    async with create_sessionmaker(engine)() as session:
        yield session
