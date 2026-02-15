"""Add trend_predictions column to insights

Revision ID: 29b08a2199f2
Revises: b004_research_requests
Create Date: 2026-01-28 08:26:32.267508

"""
from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = '29b08a2199f2'
down_revision: str | Sequence[str] | None = 'b004_research_requests'
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Upgrade schema."""
    # Add trend_predictions JSONB column to insights table
    op.add_column(
        'insights',
        sa.Column(
            'trend_predictions',
            sa.dialects.postgresql.JSONB(),
            nullable=True,
            comment='Time-series forecast predictions for next 7 days (dates, values, confidence intervals)'
        )
    )


def downgrade() -> None:
    """Downgrade schema."""
    # Remove trend_predictions column
    op.drop_column('insights', 'trend_predictions')
