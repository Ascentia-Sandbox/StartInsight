"""add referral columns to users

Revision ID: c011
Revises: c010
Create Date: 2026-02-22
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "c011"
down_revision: str | Sequence[str] | None = "c010"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("users", sa.Column("referral_code", sa.String(12), nullable=True))
    op.add_column("users", sa.Column("referred_by", sa.String(12), nullable=True))
    op.create_unique_constraint("uq_users_referral_code", "users", ["referral_code"])
    op.create_index("ix_users_referral_code", "users", ["referral_code"])


def downgrade() -> None:
    op.drop_index("ix_users_referral_code", table_name="users")
    op.drop_constraint("uq_users_referral_code", "users", type_="unique")
    op.drop_column("users", "referred_by")
    op.drop_column("users", "referral_code")
