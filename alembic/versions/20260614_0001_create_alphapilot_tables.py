"""create alphapilot tables

Revision ID: 20260614_0001
Revises:
Create Date: 2026-06-14
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql


revision: str = "20260614_0001"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def _json_type():
    return sa.JSON().with_variant(postgresql.JSONB, "postgresql")


def upgrade() -> None:
    op.create_table(
        "users",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("email", sa.String(length=255), nullable=False),
        sa.Column("password_hash", sa.Text(), nullable=False),
        sa.Column("display_name", sa.String(length=120), nullable=False),
        sa.Column("role", sa.String(length=32), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("email"),
    )
    op.create_index(op.f("ix_users_email"), "users", ["email"], unique=False)

    op.create_table(
        "user_tokens",
        sa.Column("token", sa.String(length=255), nullable=False),
        sa.Column("user_id", sa.String(length=36), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("token"),
    )
    op.create_index(op.f("ix_user_tokens_user_id"), "user_tokens", ["user_id"], unique=False)

    op.create_table(
        "user_quotas",
        sa.Column("user_id", sa.String(length=36), nullable=False),
        sa.Column("daily_limit", sa.Integer(), nullable=False),
        sa.Column("used_today", sa.Integer(), nullable=False),
        sa.Column("usage_date", sa.Date(), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("user_id"),
    )

    op.create_table(
        "analysis_jobs",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("user_id", sa.String(length=36), nullable=False),
        sa.Column("ticker", sa.String(length=32), nullable=False),
        sa.Column("trade_date", sa.String(length=10), nullable=False),
        sa.Column("mode", sa.String(length=16), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("selected_analysts", _json_type(), nullable=False),
        sa.Column("result_id", sa.String(length=36), nullable=True),
        sa.Column("error", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_analysis_jobs_ticker"), "analysis_jobs", ["ticker"], unique=False)
    op.create_index(op.f("ix_analysis_jobs_user_id"), "analysis_jobs", ["user_id"], unique=False)

    op.create_table(
        "analysis_results",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("job_id", sa.String(length=36), nullable=False),
        sa.Column("normalized", _json_type(), nullable=False),
        sa.Column("raw_state", _json_type(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["job_id"], ["analysis_jobs.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("job_id", name="uq_analysis_results_job_id"),
    )
    op.create_index(op.f("ix_analysis_results_job_id"), "analysis_results", ["job_id"], unique=False)

    op.create_table(
        "api_usage_logs",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("user_id", sa.String(length=36), nullable=True),
        sa.Column("endpoint", sa.String(length=120), nullable=False),
        sa.Column("provider", sa.String(length=64), nullable=True),
        sa.Column("model", sa.String(length=120), nullable=True),
        sa.Column("input_tokens", sa.Integer(), nullable=True),
        sa.Column("output_tokens", sa.Integer(), nullable=True),
        sa.Column("estimated_cost_usd", sa.Numeric(12, 6), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_api_usage_logs_user_id"), "api_usage_logs", ["user_id"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_api_usage_logs_user_id"), table_name="api_usage_logs")
    op.drop_table("api_usage_logs")
    op.drop_index(op.f("ix_analysis_results_job_id"), table_name="analysis_results")
    op.drop_table("analysis_results")
    op.drop_index(op.f("ix_analysis_jobs_user_id"), table_name="analysis_jobs")
    op.drop_index(op.f("ix_analysis_jobs_ticker"), table_name="analysis_jobs")
    op.drop_table("analysis_jobs")
    op.drop_table("user_quotas")
    op.drop_index(op.f("ix_user_tokens_user_id"), table_name="user_tokens")
    op.drop_table("user_tokens")
    op.drop_index(op.f("ix_users_email"), table_name="users")
    op.drop_table("users")
