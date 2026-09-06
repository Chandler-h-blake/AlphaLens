"""persist generated report link on research tasks

Revision ID: 0002_persist_generated_reports
Revises: 0001_initial_schema
Create Date: 2026-07-11
"""

from alembic import op
import sqlalchemy as sa


revision = "0002_persist_generated_reports"
down_revision = "0001_initial_schema"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("research_tasks", sa.Column("report_id", sa.Integer(), nullable=True))


def downgrade() -> None:
    op.drop_column("research_tasks", "report_id")
