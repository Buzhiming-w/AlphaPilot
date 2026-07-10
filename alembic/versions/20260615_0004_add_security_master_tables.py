"""add security master tables

Revision ID: 20260615_0004
Revises: 20260615_0003
Create Date: 2026-06-15
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op


revision: str = "20260615_0004"
down_revision: str | None = "20260615_0003"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "securities",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("symbol", sa.String(length=32), nullable=False),
        sa.Column("normalized_symbol", sa.String(length=64), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("normalized_name", sa.String(length=255), nullable=False),
        sa.Column("exchange", sa.String(length=64), nullable=False),
        sa.Column("market", sa.String(length=32), nullable=False),
        sa.Column("currency", sa.String(length=16), nullable=False),
        sa.Column("asset_type", sa.String(length=32), nullable=False),
        sa.Column("is_etf", sa.Boolean(), nullable=False),
        sa.Column("cik", sa.String(length=32), nullable=True),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("source", sa.String(length=64), nullable=False),
        sa.Column("raw_payload", sa.JSON(), nullable=False),
        sa.Column("first_seen_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("last_seen_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("delisted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("market", "symbol", name="uq_securities_market_symbol"),
    )
    op.create_index(op.f("ix_securities_cik"), "securities", ["cik"], unique=False)
    op.create_index(op.f("ix_securities_normalized_name"), "securities", ["normalized_name"], unique=False)
    op.create_index(op.f("ix_securities_normalized_symbol"), "securities", ["normalized_symbol"], unique=False)
    op.create_index(op.f("ix_securities_status"), "securities", ["status"], unique=False)
    op.create_index(op.f("ix_securities_symbol"), "securities", ["symbol"], unique=False)

    op.create_table(
        "security_aliases",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("security_id", sa.String(length=36), nullable=False),
        sa.Column("alias", sa.String(length=255), nullable=False),
        sa.Column("normalized_alias", sa.String(length=255), nullable=False),
        sa.Column("alias_type", sa.String(length=64), nullable=False),
        sa.Column("confidence", sa.String(length=32), nullable=False),
        sa.Column("source", sa.String(length=64), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["security_id"], ["securities.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("security_id", "normalized_alias", name="uq_security_aliases_security_alias"),
    )
    op.create_index(op.f("ix_security_aliases_normalized_alias"), "security_aliases", ["normalized_alias"], unique=False)
    op.create_index(op.f("ix_security_aliases_security_id"), "security_aliases", ["security_id"], unique=False)

    op.create_table(
        "security_master_sync_runs",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("source", sa.String(length=64), nullable=False),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("finished_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("inserted_count", sa.Integer(), nullable=False),
        sa.Column("updated_count", sa.Integer(), nullable=False),
        sa.Column("deactivated_count", sa.Integer(), nullable=False),
        sa.Column("error", sa.Text(), nullable=True),
        sa.Column("raw_metadata", sa.JSON(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_table(
        "security_resolution_failures",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("user_id", sa.String(length=36), nullable=True),
        sa.Column("query", sa.Text(), nullable=False),
        sa.Column("entities", sa.JSON(), nullable=False),
        sa.Column("reason", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("resolved_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("resolved_by_user_id", sa.String(length=36), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.ForeignKeyConstraint(["resolved_by_user_id"], ["users.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_security_resolution_failures_user_id"), "security_resolution_failures", ["user_id"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_security_resolution_failures_user_id"), table_name="security_resolution_failures")
    op.drop_table("security_resolution_failures")
    op.drop_table("security_master_sync_runs")
    op.drop_index(op.f("ix_security_aliases_security_id"), table_name="security_aliases")
    op.drop_index(op.f("ix_security_aliases_normalized_alias"), table_name="security_aliases")
    op.drop_table("security_aliases")
    op.drop_index(op.f("ix_securities_symbol"), table_name="securities")
    op.drop_index(op.f("ix_securities_status"), table_name="securities")
    op.drop_index(op.f("ix_securities_normalized_symbol"), table_name="securities")
    op.drop_index(op.f("ix_securities_normalized_name"), table_name="securities")
    op.drop_index(op.f("ix_securities_cik"), table_name="securities")
    op.drop_table("securities")
