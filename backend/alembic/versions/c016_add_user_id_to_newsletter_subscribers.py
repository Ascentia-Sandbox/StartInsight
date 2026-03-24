"""add user_id to newsletter_subscribers for merge-on-signup

Revision ID: c016
Revises: c015
Create Date: 2026-03-24
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "c016"
down_revision: str | Sequence[str] | None = "c015"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "newsletter_subscribers",
        sa.Column(
            "user_id",
            sa.dialects.postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="SET NULL"),
            nullable=True,
        ),
    )
    op.create_index(
        "ix_newsletter_subscribers_user_id",
        "newsletter_subscribers",
        ["user_id"],
    )


def downgrade() -> None:
    op.drop_index("ix_newsletter_subscribers_user_id", table_name="newsletter_subscribers")
    op.drop_column("newsletter_subscribers", "user_id")
