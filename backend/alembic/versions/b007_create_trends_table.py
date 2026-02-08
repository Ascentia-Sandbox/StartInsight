"""create trends table

Revision ID: b007
Revises: b006
Create Date: 2026-01-29 10:10:00.000000

Phase 12.2: IdeaBrowser Feature Replication - 180+ trending keywords with volume/growth metrics
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "b007_trends"
down_revision: Union[str, None] = "b006_success_stories"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create trends table for trending keywords database."""

    # Create trends table
    op.create_table(
        "trends",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("keyword", sa.String(length=200), nullable=False, unique=True, index=True),
        sa.Column("category", sa.String(length=100), nullable=False, index=True),
        sa.Column("search_volume", sa.Integer(), nullable=False, index=True),
        sa.Column("growth_percentage", sa.Float(), nullable=False, index=True),
        sa.Column("business_implications", sa.Text(), nullable=False),
        sa.Column("trend_data", postgresql.JSONB(astext_type=sa.Text()), nullable=True, server_default=sa.text("'{}'::jsonb")),
        sa.Column("source", sa.String(length=100), nullable=False, server_default=sa.text("'Google Trends'")),
        sa.Column("is_featured", sa.Boolean(), nullable=False, server_default=sa.text("false"), index=True),
        sa.Column("is_published", sa.Boolean(), nullable=False, server_default=sa.text("true"), index=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()"), index=True),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
    )

    # Create indexes for sorting
    op.create_index("ix_trends_search_volume_desc", "trends", [sa.text("search_volume DESC")])
    op.create_index("ix_trends_growth_percentage_desc", "trends", [sa.text("growth_percentage DESC")])
    op.create_index("ix_trends_created_at_desc", "trends", [sa.text("created_at DESC")])

    # Enable RLS
    op.execute("ALTER TABLE trends ENABLE ROW LEVEL SECURITY;")

    # RLS Policy: Public read for published trends
    op.execute("""
        CREATE POLICY trends_public_read ON trends
        FOR SELECT
        USING (is_published = true);
    """)

    # RLS Policy: Admin write access (simplified for local development)
    op.execute("""
        CREATE POLICY trends_admin_write ON trends
        FOR ALL
        USING (true)
        WITH CHECK (true);
    """)


def downgrade() -> None:
    """Drop trends table."""
    op.drop_table("trends")
