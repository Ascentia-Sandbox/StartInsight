"""purge_seed_data

Revision ID: c008
Revises: c007
Create Date: 2026-02-16 16:00:00.000000

"""
from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = "c008"
down_revision: str | None = "c007"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Delete all seed_data insights and raw_signals.

    Order matters: insights have FK to raw_signals, so delete insights first.
    """
    # 1. Delete insights linked to seed_data raw_signals
    op.execute(
        sa.text("""
            DELETE FROM insights
            WHERE raw_signal_id IN (
                SELECT id FROM raw_signals WHERE source = 'seed_data'
            )
        """)
    )

    # 2. Delete seed_data raw_signals
    op.execute(
        sa.text("DELETE FROM raw_signals WHERE source = 'seed_data'")
    )


def downgrade() -> None:
    """No-op: seed data was synthetic and not recoverable."""
    pass
