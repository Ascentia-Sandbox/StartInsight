"""create success_stories table

Revision ID: b006
Revises: b005
Create Date: 2026-01-29 10:05:00.000000

Phase 12.2: IdeaBrowser Feature Replication - Founder case studies with revenue timelines
"""

from typing import Sequence, Union

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "b006_success_stories"
down_revision: Union[str, None] = "b005_tools"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create success_stories table for founder case studies."""

    # Create success_stories table
    op.create_table(
        "success_stories",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("founder_name", sa.String(length=200), nullable=False),
        sa.Column("company_name", sa.String(length=200), nullable=False, index=True),
        sa.Column("tagline", sa.String(length=500), nullable=False),
        sa.Column("idea_summary", sa.Text(), nullable=False),
        sa.Column("journey_narrative", sa.Text(), nullable=False),
        sa.Column("metrics", postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column("timeline", postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default=sa.text("'[]'::jsonb")),
        sa.Column("avatar_url", sa.String(length=500), nullable=True),
        sa.Column("company_logo_url", sa.String(length=500), nullable=True),
        sa.Column("is_featured", sa.Boolean(), nullable=False, server_default=sa.text("false"), index=True),
        sa.Column("is_published", sa.Boolean(), nullable=False, server_default=sa.text("true"), index=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()"), index=True),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
    )

    # Create index for created_at DESC
    op.create_index("ix_success_stories_created_at_desc", "success_stories", [sa.text("created_at DESC")])

    # Enable RLS
    op.execute("ALTER TABLE success_stories ENABLE ROW LEVEL SECURITY;")

    # RLS Policy: Public read for published stories
    op.execute("""
        CREATE POLICY success_stories_public_read ON success_stories
        FOR SELECT
        USING (is_published = true);
    """)

    # RLS Policy: Admin write access (simplified for local development)
    op.execute("""
        CREATE POLICY success_stories_admin_write ON success_stories
        FOR ALL
        USING (true)
        WITH CHECK (true);
    """)


def downgrade() -> None:
    """Drop success_stories table."""
    op.drop_table("success_stories")
