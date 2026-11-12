"""Таблицы users, habits, checkins (задачи #14, #15)

Revision ID: 0001
Revises:
Create Date: 2026-11-12

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0001"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "users",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("telegram_id", sa.BigInteger(), nullable=False),
        sa.Column("first_name", sa.String(length=64), nullable=False),
        sa.Column("language_code", sa.String(length=8), nullable=True),
        sa.Column("utc_offset_minutes", sa.SmallInteger(), server_default="180", nullable=False),
        sa.Column("reminders_enabled", sa.Boolean(), server_default=sa.true(), nullable=False),
        sa.Column("plan", sa.String(length=8), server_default="free", nullable=False),
        sa.Column("pro_until", sa.DateTime(timezone=True), nullable=True),
        sa.Column("is_active", sa.Boolean(), server_default=sa.true(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.CheckConstraint("plan IN ('free', 'pro')", name=op.f("ck_users_plan")),
        sa.CheckConstraint("utc_offset_minutes BETWEEN -720 AND 840", name=op.f("ck_users_utc_offset")),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_users")),
        sa.UniqueConstraint("telegram_id", name=op.f("uq_users_telegram_id")),
    )

    op.create_table(
        "habits",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("title", sa.String(length=50), nullable=False),
        sa.Column("schedule_days", sa.SmallInteger(), server_default="127", nullable=False),
        sa.Column("remind_at", sa.Time(), nullable=True),
        sa.Column("reminders_enabled", sa.Boolean(), server_default=sa.true(), nullable=False),
        sa.Column("is_archived", sa.Boolean(), server_default=sa.false(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("archived_at", sa.DateTime(timezone=True), nullable=True),
        sa.CheckConstraint("length(title) BETWEEN 1 AND 50", name=op.f("ck_habits_title_length")),
        sa.CheckConstraint("schedule_days BETWEEN 1 AND 127", name=op.f("ck_habits_schedule_days")),
        sa.ForeignKeyConstraint(
            ["user_id"], ["users.id"], name=op.f("fk_habits_user_id_users"), ondelete="CASCADE"
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_habits")),
    )
    op.create_index(op.f("ix_habits_user_id"), "habits", ["user_id"], unique=False)

    op.create_table(
        "checkins",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("habit_id", sa.Integer(), nullable=False),
        sa.Column("date", sa.Date(), nullable=False),
        sa.Column("status", sa.String(length=8), server_default="done", nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.CheckConstraint("status IN ('done', 'skipped')", name=op.f("ck_checkins_status")),
        sa.ForeignKeyConstraint(
            ["habit_id"], ["habits.id"], name=op.f("fk_checkins_habit_id_habits"), ondelete="CASCADE"
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_checkins")),
        sa.UniqueConstraint("habit_id", "date", name="uq_checkins_habit_id_date"),
    )
    op.create_index("ix_checkins_date", "checkins", ["date"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_checkins_date", table_name="checkins")
    op.drop_table("checkins")
    op.drop_index(op.f("ix_habits_user_id"), table_name="habits")
    op.drop_table("habits")
    op.drop_table("users")
