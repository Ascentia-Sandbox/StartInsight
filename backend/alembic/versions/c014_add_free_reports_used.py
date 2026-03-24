"""add free_reports_used and free_reports_reset_at to users (PLG freemium paywall)

Revision ID: c014
Revises: c013
Create Date: 2026-03-23
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "c014"
down_revision: str | Sequence[str] | None = "c013"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "users",
        sa.Column("free_reports_used", sa.Integer(), nullable=False, server_default="0"),
    )
    op.add_column(
        "users",
        sa.Column("free_reports_reset_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index(
        "ix_users_tier_reports",
        "users",
        ["subscription_tier", "free_reports_used"],
    )


def downgrade() -> None:
    op.drop_index("ix_users_tier_reports", table_name="users")
    op.drop_column("users", "free_reports_reset_at")
    op.drop_column("users", "free_reports_used")
