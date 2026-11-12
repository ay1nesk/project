"""Модели данных HabitBot (схема БД — задача #14, модели — #15).

Таблицы:
- users    — пользователи бота;
- habits   — привычки пользователя;
- checkins — отметки выполнения привычки по дням.
"""

from __future__ import annotations

import datetime as dt

from sqlalchemy import (
    BigInteger,
    CheckConstraint,
    Date,
    DateTime,
    ForeignKey,
    Index,
    MetaData,
    SmallInteger,
    String,
    Time,
    UniqueConstraint,
    false,
    func,
    true,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship

# Единые правила именования индексов и ограничений — чтобы миграции
# одинаково работали в SQLite (разработка, тесты) и PostgreSQL (сервер).
NAMING_CONVENTION = {
    "ix": "ix_%(table_name)s_%(column_0_name)s",
    "uq": "uq_%(table_name)s_%(column_0_name)s",
    "ck": "ck_%(table_name)s_%(constraint_name)s",
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
    "pk": "pk_%(table_name)s",
}

# Расписание привычки хранится битовой маской: Пн = 1, Вт = 2, Ср = 4 … Вс = 64.
EVERY_DAY = 0b1111111  # 127 — каждый день

DEFAULT_UTC_OFFSET_MINUTES = 180  # UTC+3 по умолчанию (FR-1.3)
FREE_HABITS_LIMIT = 5  # лимит активных привычек на тарифе Free (FR-2.2)


class Base(DeclarativeBase):
    metadata = MetaData(naming_convention=NAMING_CONVENTION)


class User(Base):
    __tablename__ = "users"
    __table_args__ = (
        CheckConstraint("plan IN ('free', 'pro')", name="plan"),
        CheckConstraint("utc_offset_minutes BETWEEN -720 AND 840", name="utc_offset"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    telegram_id: Mapped[int] = mapped_column(BigInteger, unique=True)
    first_name: Mapped[str] = mapped_column(String(64))
    language_code: Mapped[str | None] = mapped_column(String(8))
    utc_offset_minutes: Mapped[int] = mapped_column(
        SmallInteger, default=DEFAULT_UTC_OFFSET_MINUTES, server_default=str(DEFAULT_UTC_OFFSET_MINUTES)
    )
    reminders_enabled: Mapped[bool] = mapped_column(default=True, server_default=true())
    plan: Mapped[str] = mapped_column(String(8), default="free", server_default="free")
    pro_until: Mapped[dt.datetime | None] = mapped_column(DateTime(timezone=True))
    # False, если пользователь заблокировал бота (FR-3.6)
    is_active: Mapped[bool] = mapped_column(default=True, server_default=true())
    created_at: Mapped[dt.datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    habits: Mapped[list[Habit]] = relationship(
        back_populates="user", cascade="all, delete-orphan", passive_deletes=True
    )

    def __repr__(self) -> str:
        return f"User(id={self.id}, telegram_id={self.telegram_id}, plan={self.plan!r})"


class Habit(Base):
    __tablename__ = "habits"
    __table_args__ = (
        CheckConstraint("schedule_days BETWEEN 1 AND 127", name="schedule_days"),
        CheckConstraint("length(title) BETWEEN 1 AND 50", name="title_length"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    title: Mapped[str] = mapped_column(String(50))
    schedule_days: Mapped[int] = mapped_column(SmallInteger, default=EVERY_DAY, server_default=str(EVERY_DAY))
    remind_at: Mapped[dt.time | None] = mapped_column(Time)  # None — без напоминания
    reminders_enabled: Mapped[bool] = mapped_column(default=True, server_default=true())
    # Удаление — это архивация: история отметок остаётся в статистике (FR-2.6)
    is_archived: Mapped[bool] = mapped_column(default=False, server_default=false())
    created_at: Mapped[dt.datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    archived_at: Mapped[dt.datetime | None] = mapped_column(DateTime(timezone=True))

    user: Mapped[User] = relationship(back_populates="habits")
    checkins: Mapped[list[Checkin]] = relationship(
        back_populates="habit", cascade="all, delete-orphan", passive_deletes=True
    )

    def runs_on(self, day: dt.date) -> bool:
        """Входит ли день в расписание привычки."""
        return bool(self.schedule_days & (1 << day.weekday()))

    def __repr__(self) -> str:
        return f"Habit(id={self.id}, title={self.title!r})"


class Checkin(Base):
    __tablename__ = "checkins"
    __table_args__ = (
        # Одна отметка на привычку в день (FR-4.2)
        UniqueConstraint("habit_id", "date", name="uq_checkins_habit_id_date"),
        CheckConstraint("status IN ('done', 'skipped')", name="status"),
        Index("ix_checkins_date", "date"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    habit_id: Mapped[int] = mapped_column(ForeignKey("habits.id", ondelete="CASCADE"))
    date: Mapped[dt.date] = mapped_column(Date)
    status: Mapped[str] = mapped_column(String(8), default="done", server_default="done")
    created_at: Mapped[dt.datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    habit: Mapped[Habit] = relationship(back_populates="checkins")

    def __repr__(self) -> str:
        return f"Checkin(habit_id={self.habit_id}, date={self.date}, status={self.status!r})"
