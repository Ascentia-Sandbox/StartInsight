"""Add missing insight admin columns (admin_notes, admin_override_score, edited_by, edited_at)

Revision ID: c004
Revises: 6b16d01c6cf7
Create Date: 2026-02-15

These columns were defined in model but never migrated to the current DB.
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "c004"
down_revision: str | Sequence[str] | None = "6b16d01c6cf7"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("insights", sa.Column("admin_notes", sa.Text(), nullable=True))
    op.add_column("insights", sa.Column("admin_override_score", sa.Float(), nullable=True))
    op.add_column("insights", sa.Column("edited_by", sa.UUID(), nullable=True))
    op.add_column("insights", sa.Column("edited_at", sa.DateTime(timezone=True), nullable=True))
    op.create_index("idx_insights_edited_by", "insights", ["edited_by"])


def downgrade() -> None:
    op.drop_index("idx_insights_edited_by", table_name="insights")
    op.drop_column("insights", "edited_at")
    op.drop_column("insights", "edited_by")
    op.drop_column("insights", "admin_override_score")
    op.drop_column("insights", "admin_notes")
