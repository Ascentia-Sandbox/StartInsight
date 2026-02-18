"""add visualization columns to insights

Revision ID: b003_viz
Revises: b002
Create Date: 2026-01-25

Phase 5+: Enhanced Visualizations
- Add community_signals_chart JSONB column
- Add enhanced_scores JSONB column
"""
from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB

from alembic import op

# revision identifiers, used by Alembic.
revision: str = 'b003_viz'
down_revision: str | None = 'b002'
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Add visualization columns to insights table."""
    # Add community_signals_chart column
    op.add_column(
        'insights',
        sa.Column(
            'community_signals_chart',
            JSONB,
            nullable=True,
            comment='Community engagement visualization data (platform, score, members, engagement_rate)'
        )
    )

    # Add enhanced_scores column
    op.add_column(
        'insights',
        sa.Column(
            'enhanced_scores',
            JSONB,
            nullable=True,
            comment='8-dimension scoring breakdown (dimension, value, label)'
        )
    )

    # Set default empty arrays for existing rows
    op.execute("UPDATE insights SET community_signals_chart = '[]'::jsonb WHERE community_signals_chart IS NULL")
    op.execute("UPDATE insights SET enhanced_scores = '[]'::jsonb WHERE enhanced_scores IS NULL")


def downgrade() -> None:
    """Remove visualization columns from insights table."""
    op.drop_column('insights', 'enhanced_scores')
    op.drop_column('insights', 'community_signals_chart')
