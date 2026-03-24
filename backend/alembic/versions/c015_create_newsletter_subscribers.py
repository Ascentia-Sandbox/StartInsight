"""create newsletter_subscribers table for double opt-in newsletter

Revision ID: c015
Revises: c014
Create Date: 2026-03-23
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "c015"
down_revision: str | Sequence[str] | None = "c014"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "newsletter_subscribers",
        sa.Column("id", sa.dialects.postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("email", sa.String(255), nullable=False, unique=True),
        sa.Column("confirmed", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("confirmation_token", sa.String(128), nullable=True, unique=True),
        sa.Column("token_expires_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("confirmed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("unsubscribed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("source", sa.String(50), nullable=False, server_default="footer"),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
    )
    op.create_index("ix_newsletter_subscribers_email", "newsletter_subscribers", ["email"])
    op.create_index(
        "ix_newsletter_subscribers_token",
        "newsletter_subscribers",
        ["confirmation_token"],
    )


def downgrade() -> None:
    op.drop_index("ix_newsletter_subscribers_token", table_name="newsletter_subscribers")
    op.drop_index("ix_newsletter_subscribers_email", table_name="newsletter_subscribers")
    op.drop_table("newsletter_subscribers")
