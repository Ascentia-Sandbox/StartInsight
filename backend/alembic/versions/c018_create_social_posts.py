"""create social_posts table + add nurture_stage to newsletter_subscribers

Revision ID: c018
Revises: c017
Create Date: 2026-04-04
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "c018"
down_revision: str | Sequence[str] | None = "c017"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "social_posts",
        sa.Column("id", sa.dialects.postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "insight_id",
            sa.dialects.postgresql.UUID(as_uuid=True),
            sa.ForeignKey("insights.id", ondelete="SET NULL"),
            nullable=True,
            index=True,
        ),
        sa.Column("platform", sa.String(20), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("hashtags", sa.dialects.postgresql.JSONB(), nullable=True),
        sa.Column("link_url", sa.String(512), nullable=True),
        sa.Column("external_post_id", sa.String(255), nullable=True),
        sa.Column("status", sa.String(20), nullable=False, server_default="pending"),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("posted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "engagement_metrics",
            sa.dialects.postgresql.JSONB(),
            nullable=True,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
        ),
    )
    op.create_index(
        "ix_social_posts_status_platform",
        "social_posts",
        ["status", "platform"],
    )

    # Add nurture_stage to newsletter_subscribers for email drip sequence
    op.add_column(
        "newsletter_subscribers",
        sa.Column(
            "nurture_stage",
            sa.Integer(),
            nullable=False,
            server_default="0",
        ),
    )


def downgrade() -> None:
    op.drop_column("newsletter_subscribers", "nurture_stage")
    op.drop_index("ix_social_posts_status_platform", table_name="social_posts")
    op.drop_table("social_posts")
