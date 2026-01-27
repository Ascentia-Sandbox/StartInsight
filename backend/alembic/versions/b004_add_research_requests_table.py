"""add research_requests table and update custom_analyses

Revision ID: b004_research_requests
Revises: b003_viz
Create Date: 2026-01-25

Phase 5.2: Super Admin Sovereignty
- Create research_requests table for admin approval queue
- Add admin_id and request_id to custom_analyses
- Make custom_analyses.user_id nullable (admin can trigger without user)
"""
from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID

from alembic import op

# revision identifiers, used by Alembic.
revision: str = 'b004_research_requests'
down_revision: str | None = 'b003_viz'
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Add research_requests table and update custom_analyses."""

    # Create research_requests table
    op.create_table(
        'research_requests',
        sa.Column('id', UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()'), nullable=False),
        sa.Column('user_id', UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False, index=True),
        sa.Column('admin_id', UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='SET NULL'), nullable=True, index=True),
        sa.Column('status', sa.String(20), nullable=False, server_default='pending', index=True),
        sa.Column('idea_description', sa.Text, nullable=False),
        sa.Column('target_market', sa.String(255), nullable=True),
        sa.Column('budget_range', sa.String(100), nullable=True),
        sa.Column('admin_notes', sa.Text, nullable=True),
        sa.Column('analysis_id', UUID(as_uuid=True), sa.ForeignKey('custom_analyses.id', ondelete='SET NULL'), nullable=True, index=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False, index=True),
        sa.Column('reviewed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('completed_at', sa.DateTime(timezone=True), nullable=True),
        comment='Research requests submitted by users, pending admin approval'
    )

    # Add admin_id column to custom_analyses
    op.add_column(
        'custom_analyses',
        sa.Column('admin_id', UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='SET NULL'), nullable=True, index=True)
    )

    # Add request_id column to custom_analyses
    op.add_column(
        'custom_analyses',
        sa.Column('request_id', UUID(as_uuid=True), sa.ForeignKey('research_requests.id', ondelete='SET NULL'), nullable=True, index=True)
    )

    # Make user_id nullable in custom_analyses (admin can trigger without user)
    op.alter_column('custom_analyses', 'user_id', nullable=True)

    # Add indexes for performance
    op.create_index('idx_research_requests_user_id', 'research_requests', ['user_id'])
    op.create_index('idx_research_requests_status', 'research_requests', ['status'])
    op.create_index('idx_research_requests_created_at', 'research_requests', ['created_at'], postgresql_using='btree', postgresql_ops={'created_at': 'DESC'})


def downgrade() -> None:
    """Remove research_requests table and revert custom_analyses changes."""

    # Drop indexes
    op.drop_index('idx_research_requests_created_at', 'research_requests')
    op.drop_index('idx_research_requests_status', 'research_requests')
    op.drop_index('idx_research_requests_user_id', 'research_requests')

    # Revert custom_analyses changes
    op.alter_column('custom_analyses', 'user_id', nullable=False)
    op.drop_column('custom_analyses', 'request_id')
    op.drop_column('custom_analyses', 'admin_id')

    # Drop research_requests table
    op.drop_table('research_requests')
