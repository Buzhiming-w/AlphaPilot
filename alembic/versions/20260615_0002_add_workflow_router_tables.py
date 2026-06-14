"""add workflow router tables

Revision ID: 20260615_0002
Revises: 20260614_0001
Create Date: 2026-06-15
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op


revision: str = "20260615_0002"
down_revision: str | None = "20260614_0001"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "watchlist_items",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("user_id", sa.String(length=36), nullable=False),
        sa.Column("ticker", sa.String(length=32), nullable=False),
        sa.Column("company_name", sa.String(length=255), nullable=False),
        sa.Column("market", sa.String(length=32), nullable=False),
        sa.Column("exchange", sa.String(length=64), nullable=False),
        sa.Column("currency", sa.String(length=16), nullable=False),
        sa.Column("note", sa.Text(), nullable=True),
        sa.Column("source", sa.String(length=32), nullable=False),
        sa.Column("last_analysis_job_id", sa.String(length=36), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["last_analysis_job_id"], ["analysis_jobs.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_watchlist_items_ticker"), "watchlist_items", ["ticker"], unique=False)
    op.create_index(op.f("ix_watchlist_items_user_id"), "watchlist_items", ["user_id"], unique=False)

    op.create_table(
        "compare_workflows",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("user_id", sa.String(length=36), nullable=False),
        sa.Column("start_date", sa.String(length=10), nullable=True),
        sa.Column("end_date", sa.String(length=10), nullable=True),
        sa.Column("analysis_anchor", sa.String(length=10), nullable=True),
        sa.Column("source", sa.String(length=32), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_compare_workflows_user_id"), "compare_workflows", ["user_id"], unique=False)

    op.create_table(
        "compare_workflow_symbols",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("compare_workflow_id", sa.String(length=36), nullable=False),
        sa.Column("ticker", sa.String(length=32), nullable=False),
        sa.Column("company_name", sa.String(length=255), nullable=False),
        sa.Column("market", sa.String(length=32), nullable=False),
        sa.Column("exchange", sa.String(length=64), nullable=False),
        sa.Column("currency", sa.String(length=16), nullable=False),
        sa.Column("analysis_job_id", sa.String(length=36), nullable=True),
        sa.Column("order_index", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(["analysis_job_id"], ["analysis_jobs.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["compare_workflow_id"], ["compare_workflows.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_compare_workflow_symbols_compare_workflow_id"),
        "compare_workflow_symbols",
        ["compare_workflow_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_compare_workflow_symbols_ticker"),
        "compare_workflow_symbols",
        ["ticker"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(op.f("ix_compare_workflow_symbols_ticker"), table_name="compare_workflow_symbols")
    op.drop_index(
        op.f("ix_compare_workflow_symbols_compare_workflow_id"),
        table_name="compare_workflow_symbols",
    )
    op.drop_table("compare_workflow_symbols")
    op.drop_index(op.f("ix_compare_workflows_user_id"), table_name="compare_workflows")
    op.drop_table("compare_workflows")
    op.drop_index(op.f("ix_watchlist_items_user_id"), table_name="watchlist_items")
    op.drop_index(op.f("ix_watchlist_items_ticker"), table_name="watchlist_items")
    op.drop_table("watchlist_items")
