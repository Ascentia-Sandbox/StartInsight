"""add nurture_stage to newsletter_subscribers for email drip sequence

Revision ID: c019
Revises: c018
Create Date: 2026-05-09
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "c019"
down_revision: str | Sequence[str] | None = "c018"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "newsletter_subscribers",
        sa.Column(
            "nurture_stage",
            sa.Integer(),
            nullable=False,
            server_default="0",
        ),
    )


def downgrade() -> None:
    op.drop_column("newsletter_subscribers", "nurture_stage")
