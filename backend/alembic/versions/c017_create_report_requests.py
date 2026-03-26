"""create report_requests table for conviction funnel

Revision ID: c017
Revises: c016
Create Date: 2026-03-26
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "c017"
down_revision: str | Sequence[str] | None = "c016"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "report_requests",
        sa.Column("id", sa.dialects.postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "stripe_payment_intent_id",
            sa.String(255),
            nullable=False,
            unique=True,
        ),
        sa.Column("source", sa.String(50), nullable=False, server_default="direct"),
        sa.Column("category", sa.String(100), nullable=False),
        sa.Column("email", sa.String(255), nullable=False),
        sa.Column("teaser_viewed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("checkout_started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("paid_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("report_delivered_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("status", sa.String(20), nullable=False, server_default="pending"),
        sa.Column("failed_step", sa.String(50), nullable=True),
        sa.Column("report_html", sa.Text(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
        ),
    )
    # Composite index for per-channel kill criteria
    op.create_index(
        "ix_report_requests_category_source",
        "report_requests",
        ["category", "source"],
    )
    # Index on payment intent for fast idempotency lookup
    op.create_index(
        "ix_report_requests_stripe_payment_intent_id",
        "report_requests",
        ["stripe_payment_intent_id"],
        unique=True,
    )


def downgrade() -> None:
    op.drop_index(
        "ix_report_requests_stripe_payment_intent_id",
        table_name="report_requests",
    )
    op.drop_index(
        "ix_report_requests_category_source",
        table_name="report_requests",
    )
    op.drop_table("report_requests")
