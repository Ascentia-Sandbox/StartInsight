"""add source_url to success_stories

Revision ID: b023
Revises: c22518f05cbf
Create Date: 2026-02-08

"""
from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "b023"
down_revision: str | None = "b022"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "success_stories",
        sa.Column("source_url", sa.String(500), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("success_stories", "source_url")
