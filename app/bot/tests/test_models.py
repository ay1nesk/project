"""Модели и схема БД (задачи #14, #15)."""

import datetime as dt

import pytest
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError

from bot.database.models import EVERY_DAY, Checkin, Habit, User

MONDAY = dt.date(2026, 11, 9)


async def make_user(session, telegram_id=555):
    user = User(telegram_id=telegram_id, first_name="Ксения")
    session.add(user)
    await session.flush()
    return user


async def test_defaults(session):
    user = await make_user(session)
    habit = Habit(user=user, title="Пить воду")
    session.add(habit)
    await session.commit()
    await session.refresh(user)
    await session.refresh(habit)

    assert user.plan == "free"
    assert user.utc_offset_minutes == 180  # UTC+3
    assert user.reminders_enabled and user.is_active
    assert user.created_at is not None
    assert habit.schedule_days == EVERY_DAY
    assert habit.is_archived is False
    assert habit.remind_at is None


async def test_telegram_id_is_unique(session):
    await make_user(session, telegram_id=1)
    session.add(User(telegram_id=1, first_name="Дубль"))
    with pytest.raises(IntegrityError):
        await session.flush()


async def test_one_checkin_per_habit_per_day(session):
    user = await make_user(session)
    habit = Habit(user=user, title="Зарядка", remind_at=dt.time(9, 0))
    session.add_all([habit, Checkin(habit=habit, date=MONDAY)])
    await session.flush()

    session.add(Checkin(habit=habit, date=MONDAY))
    with pytest.raises(IntegrityError):
        await session.flush()


async def test_deleting_user_deletes_habits_and_checkins(session):
    user = await make_user(session)
    habit = Habit(user=user, title="Читать")
    session.add_all([habit, Checkin(habit=habit, date=MONDAY, status="skipped")])
    await session.commit()

    await session.delete(user)
    await session.commit()

    assert (await session.scalars(select(Habit))).all() == []
    assert (await session.scalars(select(Checkin))).all() == []


async def test_check_constraints(session):
    user = await make_user(session)
    session.add(Habit(user=user, title="Без расписания", schedule_days=0))
    with pytest.raises(IntegrityError):
        await session.flush()
    await session.rollback()

    user = await make_user(session, telegram_id=2)
    session.add(Habit(user=user, title="Ок"))
    await session.flush()
    session.add(Checkin(habit_id=1, date=MONDAY, status="maybe"))
    with pytest.raises(IntegrityError):
        await session.flush()


def test_runs_on_schedule():
    weekdays_only = Habit(title="Работа", schedule_days=0b0011111)  # Пн–Пт
    assert weekdays_only.runs_on(MONDAY)
    assert weekdays_only.runs_on(MONDAY + dt.timedelta(days=4))  # пятница
    assert not weekdays_only.runs_on(MONDAY + dt.timedelta(days=5))  # суббота
    assert Habit(title="Каждый день", schedule_days=EVERY_DAY).runs_on(MONDAY + dt.timedelta(days=6))
