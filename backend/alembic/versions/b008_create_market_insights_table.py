"""create market_insights table

Revision ID: b008
Revises: b007
Create Date: 2026-01-29 10:15:00.000000

Phase 12.2: IdeaBrowser Feature Replication - Blog articles with Markdown content
"""

from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "b008_market_insights"
down_revision: str | None = "b007_trends"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Create market_insights table for blog articles."""

    # Create market_insights table
    op.create_table(
        "market_insights",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("title", sa.String(length=500), nullable=False, index=True),
        sa.Column("slug", sa.String(length=500), nullable=False, unique=True, index=True),
        sa.Column("summary", sa.Text(), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("category", sa.String(length=100), nullable=False, index=True),
        sa.Column("author_name", sa.String(length=200), nullable=False),
        sa.Column("author_avatar_url", sa.String(length=500), nullable=True),
        sa.Column("cover_image_url", sa.String(length=500), nullable=True),
        sa.Column("reading_time_minutes", sa.Integer(), nullable=False, server_default=sa.text("5")),
        sa.Column("view_count", sa.Integer(), nullable=False, server_default=sa.text("0")),
        sa.Column("is_featured", sa.Boolean(), nullable=False, server_default=sa.text("false"), index=True),
        sa.Column("is_published", sa.Boolean(), nullable=False, server_default=sa.text("false"), index=True),
        sa.Column("published_at", sa.DateTime(timezone=True), nullable=True, index=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()"), index=True),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
    )

    # Create indexes for sorting
    op.create_index("ix_market_insights_published_at_desc", "market_insights", [sa.text("published_at DESC")])
    op.create_index("ix_market_insights_created_at_desc", "market_insights", [sa.text("created_at DESC")])

    # Enable RLS
    op.execute("ALTER TABLE market_insights ENABLE ROW LEVEL SECURITY;")

    # RLS Policy: Public read for published articles
    op.execute("""
        CREATE POLICY market_insights_public_read ON market_insights
        FOR SELECT
        USING (is_published = true);
    """)

    # RLS Policy: Admin write access (simplified for local development)
    op.execute("""
        CREATE POLICY market_insights_admin_write ON market_insights
        FOR ALL
        USING (true)
        WITH CHECK (true);
    """)


def downgrade() -> None:
    """Drop market_insights table."""
    op.drop_table("market_insights")
