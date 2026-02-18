"""Add missing insight columns (admin_status, trend_keywords)

Revision ID: c009
Revises: c008
Create Date: 2026-02-18

admin_status was dropped by 68bc7f9b5a31 and not re-added by c004.
trend_keywords was added to the model but never migrated.
"""
from collections.abc import Sequence

from alembic import op

revision: str = "c009"
down_revision: str | Sequence[str] | None = "c008"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.execute(
        "ALTER TABLE insights ADD COLUMN IF NOT EXISTS admin_status VARCHAR(20) DEFAULT 'approved'"
    )
    op.execute(
        "CREATE INDEX IF NOT EXISTS ix_insights_admin_status ON insights (admin_status)"
    )
    op.execute(
        "ALTER TABLE insights ADD COLUMN IF NOT EXISTS trend_keywords JSONB"
    )


def downgrade() -> None:
    op.drop_column("insights", "trend_keywords")
    op.drop_index("ix_insights_admin_status", table_name="insights")
    op.drop_column("insights", "admin_status")
