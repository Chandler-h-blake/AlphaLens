"""add dashboard snapshots and daily reviews

Revision ID: 0004_add_workspace_snapshots
Revises: 0003_add_market_data_tables
"""

from alembic import op
import sqlalchemy as sa

revision = "0004_add_workspace_snapshots"
down_revision = "0003_add_market_data_tables"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table("workspace_snapshots", sa.Column("key", sa.String(32), primary_key=True), sa.Column("payload", sa.JSON(), nullable=False), sa.Column("source", sa.String(128), nullable=False), sa.Column("as_of", sa.DateTime(), nullable=False), sa.Column("fetched_at", sa.DateTime(), nullable=False))
    op.create_index("ix_workspace_snapshots_as_of", "workspace_snapshots", ["as_of"])
    op.create_index("ix_workspace_snapshots_fetched_at", "workspace_snapshots", ["fetched_at"])
    op.create_table("daily_reviews", sa.Column("id", sa.Integer(), primary_key=True), sa.Column("content_markdown", sa.Text(), nullable=False), sa.Column("generated_at", sa.DateTime(), nullable=False), sa.Column("source_summary", sa.JSON(), nullable=False))
    op.create_index("ix_daily_reviews_generated_at", "daily_reviews", ["generated_at"])
    op.add_column("research_tasks", sa.Column("kind", sa.String(32), nullable=False, server_default="research_report"))
    op.add_column("research_tasks", sa.Column("review_id", sa.Integer(), nullable=True))


def downgrade() -> None:
    op.drop_column("research_tasks", "review_id")
    op.drop_column("research_tasks", "kind")
    op.drop_table("daily_reviews")
    op.drop_table("workspace_snapshots")
