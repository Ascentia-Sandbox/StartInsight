"""create tools table

Revision ID: b005
Revises: b004
Create Date: 2026-01-29 10:00:00.000000

Phase 12.2: IdeaBrowser Feature Replication - 54-tool directory
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "b005_tools"
down_revision: Union[str, None] = "b004_research_requests"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create tools table for public content directory."""

    # Create tools table
    op.create_table(
        "tools",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("name", sa.String(length=200), nullable=False, index=True),
        sa.Column("tagline", sa.String(length=500), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("category", sa.String(length=100), nullable=False, index=True),
        sa.Column("pricing", sa.String(length=200), nullable=False),
        sa.Column("website_url", sa.String(length=500), nullable=False),
        sa.Column("logo_url", sa.String(length=500), nullable=True),
        sa.Column("is_featured", sa.Boolean(), nullable=False, server_default=sa.text("false"), index=True),
        sa.Column("sort_order", sa.Integer(), nullable=False, server_default=sa.text("0")),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()"), index=True),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
    )

    # Create index for created_at DESC (most recent first)
    op.create_index("ix_tools_created_at_desc", "tools", [sa.text("created_at DESC")])

    # Enable RLS
    op.execute("ALTER TABLE tools ENABLE ROW LEVEL SECURITY;")

    # RLS Policy: Public read access
    op.execute("""
        CREATE POLICY tools_public_read ON tools
        FOR SELECT
        USING (true);
    """)

    # RLS Policy: Admin write access (simplified for local development)
    # In production with Supabase, replace with auth.uid() checks
    op.execute("""
        CREATE POLICY tools_admin_write ON tools
        FOR ALL
        USING (true)
        WITH CHECK (true);
    """)


def downgrade() -> None:
    """Drop tools table."""
    op.drop_table("tools")
