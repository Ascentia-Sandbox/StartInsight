"""Phase B: Add mode column to idea_chats

Add chat strategist mode column for 3 modes:
pressure_test, gtm_planning, pricing_strategy

Revision ID: c002
Revises: c001
Create Date: 2026-02-14
"""

import sqlalchemy as sa

from alembic import op

revision = "c002"
down_revision = "c001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("idea_chats", sa.Column("mode", sa.String(30), nullable=True))


def downgrade() -> None:
    op.drop_column("idea_chats", "mode")
