"""Миграции Alembic (задача #15): создают схему с нуля и совпадают с моделями."""

from pathlib import Path

from alembic import command
from alembic.config import Config
from sqlalchemy import create_engine, inspect

APP_DIR = Path(__file__).resolve().parents[2]


def alembic_config(db_file: Path) -> Config:
    config = Config(APP_DIR / "alembic.ini")
    config.set_main_option("script_location", str(APP_DIR / "migrations"))
    config.set_main_option("sqlalchemy.url", f"sqlite+aiosqlite:///{db_file}")
    config.attributes["configure_logger"] = False
    return config


def test_upgrade_creates_schema_and_downgrade_removes_it(tmp_path):
    db_file = tmp_path / "migrations.db"
    config = alembic_config(db_file)

    command.upgrade(config, "head")

    inspector = inspect(create_engine(f"sqlite:///{db_file}"))
    assert {"users", "habits", "checkins"} <= set(inspector.get_table_names())
    assert "ix_habits_user_id" in {i["name"] for i in inspector.get_indexes("habits")}
    assert "ix_checkins_date" in {i["name"] for i in inspector.get_indexes("checkins")}
    unique = {tuple(u["column_names"]) for u in inspector.get_unique_constraints("checkins")}
    assert ("habit_id", "date") in unique

    command.downgrade(config, "base")
    inspector = inspect(create_engine(f"sqlite:///{db_file}"))
    assert not {"users", "habits", "checkins"} & set(inspector.get_table_names())


def test_migrations_match_models(tmp_path):
    config = alembic_config(tmp_path / "check.db")
    command.upgrade(config, "head")
    # alembic check падает, если модели и миграции расходятся
    command.check(config)
