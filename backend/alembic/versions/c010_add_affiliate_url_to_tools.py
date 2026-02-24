"""Add affiliate_url column to tools table

Revision ID: c010
Revises: c009
Create Date: 2026-02-21

Allows tools to carry an affiliate/referral URL that overrides the
standard website_url in the frontend Visit button.
"""
from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "c010"
down_revision: str | Sequence[str] | None = "c009"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "tools",
        sa.Column("affiliate_url", sa.String(500), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("tools", "affiliate_url")
