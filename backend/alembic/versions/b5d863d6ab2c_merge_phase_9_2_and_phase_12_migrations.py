"""merge phase 9.2 and phase 12 migrations

Revision ID: b5d863d6ab2c
Revises: b008_market_insights, b94254847a13
Create Date: 2026-01-29 01:10:55.994356

"""
from typing import Sequence, Union

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = 'b5d863d6ab2c'
down_revision: Union[str, Sequence[str], None] = ('b008_market_insights', 'b94254847a13')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
