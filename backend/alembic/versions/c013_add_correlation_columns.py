"""add correlation columns to insights (Phase 6.4B)

Revision ID: c013
Revises: c012
Create Date: 2026-03-20
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "c013"
down_revision: str | Sequence[str] | None = "c012"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("insights", sa.Column("correlation_group_id", sa.UUID(), nullable=True))
    op.add_column(
        "insights", sa.Column("correlation_score", sa.Float(), nullable=True, server_default="0")
    )
    op.add_column(
        "insights", sa.Column("source_count", sa.Integer(), nullable=True, server_default="1")
    )
    op.create_index("ix_insights_correlation_group_id", "insights", ["correlation_group_id"])


def downgrade() -> None:
    op.drop_index("ix_insights_correlation_group_id", table_name="insights")
    op.drop_column("insights", "source_count")
    op.drop_column("insights", "correlation_score")
    op.drop_column("insights", "correlation_group_id")
