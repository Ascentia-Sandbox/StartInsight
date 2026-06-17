"""add nurture_stage to newsletter_subscribers for email drip sequence

Revision ID: c019
Revises: c018
Create Date: 2026-05-09
"""

from collections.abc import Sequence

from alembic import op

revision: str = "c019"
down_revision: str | Sequence[str] | None = "c018"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # Use IF NOT EXISTS to handle the case where the column was added manually
    # before this migration was tracked (caused DuplicateColumnError in CI 2026-05-09)
    op.execute(
        "ALTER TABLE newsletter_subscribers ADD COLUMN IF NOT EXISTS nurture_stage INTEGER NOT NULL DEFAULT 0"
    )


def downgrade() -> None:
    op.drop_column("newsletter_subscribers", "nurture_stage")
