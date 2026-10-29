import pytest

from bot.config import ConfigError, load_settings

TOKEN = "123456:TEST-token"


def test_token_is_required():
    with pytest.raises(ConfigError, match="BOT_TOKEN"):
        load_settings({})


def test_blank_token_is_rejected():
    with pytest.raises(ConfigError):
        load_settings({"BOT_TOKEN": "   "})


def test_defaults():
    settings = load_settings({"BOT_TOKEN": TOKEN})
    assert settings.bot_token == TOKEN
    assert settings.log_level == "INFO"
    assert settings.admin_ids == frozenset()
    assert settings.database_url is None
    assert settings.redis_url is None


def test_admin_ids_are_parsed():
    settings = load_settings({"BOT_TOKEN": TOKEN, "ADMIN_IDS": " 111, 222 ,,333"})
    assert settings.admin_ids == {111, 222, 333}
    assert settings.is_admin(222)
    assert not settings.is_admin(999)


def test_bad_admin_id_is_rejected():
    with pytest.raises(ConfigError, match="ADMIN_IDS"):
        load_settings({"BOT_TOKEN": TOKEN, "ADMIN_IDS": "111,abc"})


def test_log_level_is_validated():
    assert load_settings({"BOT_TOKEN": TOKEN, "LOG_LEVEL": "debug"}).log_level == "DEBUG"
    with pytest.raises(ConfigError, match="LOG_LEVEL"):
        load_settings({"BOT_TOKEN": TOKEN, "LOG_LEVEL": "LOUD"})
