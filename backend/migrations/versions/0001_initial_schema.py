"""create core research tables

Revision ID: 0001_initial_schema
Revises:
Create Date: 2026-07-10
"""

from alembic import op
import sqlalchemy as sa


revision = "0001_initial_schema"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table("stocks", sa.Column("symbol", sa.String(length=6), primary_key=True), sa.Column("name", sa.String(length=64), nullable=False), sa.Column("industry", sa.String(length=64), nullable=True))
    op.create_table("factor_scores", sa.Column("id", sa.Integer(), primary_key=True), sa.Column("symbol", sa.String(length=6), sa.ForeignKey("stocks.symbol"), nullable=False), sa.Column("data_date", sa.Date(), nullable=False), sa.Column("rank", sa.Integer(), nullable=False), sa.Column("composite_score", sa.Float(), nullable=False), sa.Column("factor_values", sa.JSON(), nullable=False), sa.UniqueConstraint("symbol", "data_date", name="uq_factor_score_symbol_date"))
    op.create_index("ix_factor_scores_symbol", "factor_scores", ["symbol"]); op.create_index("ix_factor_scores_data_date", "factor_scores", ["data_date"]); op.create_index("ix_factor_scores_rank", "factor_scores", ["rank"])
    op.create_table("factor_overviews", sa.Column("id", sa.Integer(), primary_key=True), sa.Column("factor", sa.String(length=64), nullable=False), sa.Column("data_date", sa.Date(), nullable=False), sa.Column("name", sa.String(length=64), nullable=False), sa.Column("category", sa.String(length=32), nullable=False), sa.Column("direction", sa.Integer(), nullable=False), sa.Column("direction_text", sa.String(length=32), nullable=False), sa.Column("weight", sa.Float(), nullable=False), sa.Column("data_source", sa.String(length=128), nullable=False), sa.Column("description", sa.Text(), nullable=False), sa.Column("metrics", sa.JSON(), nullable=False), sa.UniqueConstraint("factor", "data_date", name="uq_factor_overview_factor_date"))
    op.create_index("ix_factor_overviews_factor", "factor_overviews", ["factor"]); op.create_index("ix_factor_overviews_data_date", "factor_overviews", ["data_date"])
    op.create_table("research_reports", sa.Column("id", sa.Integer(), primary_key=True), sa.Column("symbol", sa.String(length=6), sa.ForeignKey("stocks.symbol"), nullable=False), sa.Column("name", sa.String(length=64), nullable=False), sa.Column("title", sa.String(length=256), nullable=False), sa.Column("industry", sa.String(length=64), nullable=True), sa.Column("generated_at", sa.DateTime(), nullable=True), sa.Column("content_markdown", sa.Text(), nullable=False), sa.Column("sources", sa.JSON(), nullable=False), sa.Column("source_file", sa.String(length=256), nullable=True))
    op.create_index("ix_research_reports_symbol", "research_reports", ["symbol"]); op.create_index("ix_research_reports_generated_at", "research_reports", ["generated_at"])
    op.create_table("industry_rotations", sa.Column("id", sa.Integer(), primary_key=True), sa.Column("industry_code", sa.String(length=32), nullable=False), sa.Column("data_date", sa.Date(), nullable=False), sa.Column("industry_name", sa.String(length=64), nullable=False), sa.Column("latest_close", sa.Float(), nullable=True), sa.Column("return_1m", sa.Float(), nullable=False), sa.Column("return_3m", sa.Float(), nullable=False), sa.Column("rank_1m", sa.Integer(), nullable=False), sa.Column("rank_3m", sa.Integer(), nullable=False), sa.Column("rotation_type", sa.String(length=32), nullable=False), sa.Column("generated_at", sa.DateTime(), nullable=True), sa.UniqueConstraint("industry_code", "data_date", name="uq_industry_rotation_code_date"))
    op.create_index("ix_industry_rotations_industry_code", "industry_rotations", ["industry_code"]); op.create_index("ix_industry_rotations_data_date", "industry_rotations", ["data_date"])
    op.create_table("research_tasks", sa.Column("id", sa.String(length=36), primary_key=True), sa.Column("symbol", sa.String(length=6), nullable=False), sa.Column("status", sa.String(length=16), nullable=False), sa.Column("error_message", sa.Text(), nullable=True), sa.Column("created_at", sa.DateTime(), nullable=False), sa.Column("finished_at", sa.DateTime(), nullable=True))
    op.create_index("ix_research_tasks_symbol", "research_tasks", ["symbol"]); op.create_index("ix_research_tasks_status", "research_tasks", ["status"])
    op.create_table("source_documents", sa.Column("id", sa.Integer(), primary_key=True), sa.Column("source_type", sa.String(length=64), nullable=False), sa.Column("title", sa.String(length=256), nullable=False), sa.Column("content", sa.Text(), nullable=False), sa.Column("as_of", sa.Date(), nullable=True))


def downgrade() -> None:
    op.drop_table("source_documents"); op.drop_table("research_tasks"); op.drop_table("industry_rotations"); op.drop_table("research_reports"); op.drop_table("factor_overviews"); op.drop_table("factor_scores"); op.drop_table("stocks")
