"""merge_all_branches

Revision ID: c22518f05cbf
Revises: b021, b5d863d6ab2c
Create Date: 2026-02-04 16:12:24.304791

"""
from collections.abc import Sequence

# revision identifiers, used by Alembic.
revision: str = 'c22518f05cbf'
down_revision: str | Sequence[str] | None = ('b021', 'b5d863d6ab2c')
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
