"""add source_url to success_stories

Revision ID: b023
Revises: c22518f05cbf
Create Date: 2026-02-08

"""
from typing import Sequence, Union

import sqlalchemy as sa

from alembic import op

revision: str = "b023"
down_revision: Union[str, None] = "b022"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "success_stories",
        sa.Column("source_url", sa.String(500), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("success_stories", "source_url")
