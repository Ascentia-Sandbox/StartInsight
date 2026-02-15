"""merge_system_settings_heads

Revision ID: 6b16d01c6cf7
Revises: c001_create_system_settings_table, c002
Create Date: 2026-02-15 09:27:16.953375

"""
from collections.abc import Sequence

# revision identifiers, used by Alembic.
revision: str = '6b16d01c6cf7'
down_revision: str | Sequence[str] | None = ('c003', 'c002')
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
