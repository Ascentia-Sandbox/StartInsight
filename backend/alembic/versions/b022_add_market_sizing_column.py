"""Add market_sizing JSONB column to insights table.

Revision ID: b022
Revises: c22518f05cbf
Create Date: 2026-02-08
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB

# revision identifiers, used by Alembic.
revision = "b022"
down_revision = "c22518f05cbf"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("insights", sa.Column("market_sizing", JSONB, nullable=True))


def downgrade() -> None:
    op.drop_column("insights", "market_sizing")
