"""create source_health table (Phase 6.2A + 6.4A baselines)

Revision ID: c012
Revises: c011
Create Date: 2026-03-20
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "c012"
down_revision: str | Sequence[str] | None = "c011"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "source_health",
        sa.Column("id", sa.UUID(), nullable=False, server_default=sa.text("gen_random_uuid()")),
        sa.Column("source_name", sa.String(50), nullable=False),
        sa.Column("status", sa.String(20), nullable=False, server_default="unknown"),
        sa.Column("last_success_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("last_failure_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("last_error_message", sa.Text(), nullable=True),
        sa.Column("consecutive_failures", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("avg_latency_ms", sa.Float(), nullable=False, server_default="0"),
        sa.Column("avg_signals_per_run", sa.Float(), nullable=False, server_default="0"),
        sa.Column("total_runs", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("total_failures", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("circuit_state", sa.String(20), nullable=False, server_default="closed"),
        # Phase 6.4A: Welford's algorithm baselines
        sa.Column("baseline_mean", sa.Float(), nullable=False, server_default="0"),
        sa.Column("baseline_variance", sa.Float(), nullable=False, server_default="0"),
        sa.Column("baseline_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("source_name"),
    )
    op.create_index("ix_source_health_source_name", "source_health", ["source_name"])


def downgrade() -> None:
    op.drop_index("ix_source_health_source_name", table_name="source_health")
    op.drop_table("source_health")
