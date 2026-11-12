import pytest

from bot.config import load_settings
from bot.main import create_dispatcher

TEST_TOKEN = "123456:TEST-token"


@pytest.fixture(scope="session")
def settings():
    return load_settings({"BOT_TOKEN": TEST_TOKEN})


@pytest.fixture(scope="session")
def dp(settings):
    # Роутер можно подключить только к одному Dispatcher, поэтому он один на все тесты,
    # как и в работающем боте.
    return create_dispatcher(settings)
