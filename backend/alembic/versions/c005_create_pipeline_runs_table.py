"""create_pipeline_runs_table

Revision ID: c005
Revises: c004
Create Date: 2026-02-15 11:46:57.059162

"""
from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

# revision identifiers, used by Alembic.
revision: str = 'c005'
down_revision: str | Sequence[str] | None = 'c004'
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Create pipeline_runs table for content automation pipeline tracking."""
    op.create_table('pipeline_runs',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('status', sa.String(length=20), nullable=False),
        sa.Column('stages_completed', sa.Integer(), nullable=False),
        sa.Column('total_stages', sa.Integer(), nullable=False),
        sa.Column('cost_usd', sa.Numeric(precision=10, scale=4), nullable=False),
        sa.Column('details', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('error_message', sa.String(length=500), nullable=True),
        sa.Column('started_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('completed_at', sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )


def downgrade() -> None:
    """Drop pipeline_runs table."""
    op.drop_table('pipeline_runs')
