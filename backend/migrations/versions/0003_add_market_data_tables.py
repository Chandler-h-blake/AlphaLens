"""add persisted online market data

Revision ID: 0003_add_market_data_tables
Revises: 0002_persist_generated_reports
Create Date: 2026-07-11
"""

from alembic import op
import sqlalchemy as sa


revision = "0003_add_market_data_tables"
down_revision = "0002_persist_generated_reports"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "market_snapshots",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("symbol", sa.String(length=6), sa.ForeignKey("stocks.symbol"), nullable=False, unique=True),
        sa.Column("name", sa.String(length=64), nullable=False),
        sa.Column("latest_price", sa.Float(), nullable=False),
        sa.Column("change_amount", sa.Float(), nullable=True),
        sa.Column("change_percent", sa.Float(), nullable=True),
        sa.Column("open_price", sa.Float(), nullable=True),
        sa.Column("high_price", sa.Float(), nullable=True),
        sa.Column("low_price", sa.Float(), nullable=True),
        sa.Column("volume", sa.Float(), nullable=True),
        sa.Column("amount", sa.Float(), nullable=True),
        sa.Column("total_market_cap", sa.Float(), nullable=True),
        sa.Column("main_net_inflow", sa.Float(), nullable=True),
        sa.Column("source", sa.String(length=128), nullable=False),
        sa.Column("as_of", sa.DateTime(), nullable=False),
        sa.Column("fetched_at", sa.DateTime(), nullable=False),
    )
    op.create_index("ix_market_snapshots_symbol", "market_snapshots", ["symbol"])
    op.create_index("ix_market_snapshots_as_of", "market_snapshots", ["as_of"])
    op.create_index("ix_market_snapshots_fetched_at", "market_snapshots", ["fetched_at"])
    op.create_table(
        "market_announcements",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("symbol", sa.String(length=6), sa.ForeignKey("stocks.symbol"), nullable=False),
        sa.Column("article_id", sa.String(length=64), nullable=False),
        sa.Column("title", sa.String(length=512), nullable=False),
        sa.Column("category", sa.String(length=128), nullable=True),
        sa.Column("published_at", sa.DateTime(), nullable=True),
        sa.Column("url", sa.String(length=1024), nullable=True),
        sa.Column("source", sa.String(length=128), nullable=False),
        sa.Column("fetched_at", sa.DateTime(), nullable=False),
        sa.UniqueConstraint("symbol", "article_id", name="uq_market_announcement_symbol_article"),
    )
    op.create_index("ix_market_announcements_symbol", "market_announcements", ["symbol"])
    op.create_index("ix_market_announcements_published_at", "market_announcements", ["published_at"])


def downgrade() -> None:
    op.drop_table("market_announcements")
    op.drop_table("market_snapshots")
