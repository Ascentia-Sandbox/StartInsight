"""Phase 16.2: Add schedule columns to agent_configurations

Add dynamic scheduling columns for agent execution control:
- schedule_type: 'cron', 'interval', or 'manual'
- schedule_cron: cron expression (e.g., '0 8 * * *')
- schedule_interval_hours: interval in hours
- next_run_at: next scheduled run time
- last_run_at: last execution time

Revision ID: c001
Revises: c22518f05cbf
Create Date: 2026-02-14
"""

import sqlalchemy as sa

from alembic import op

revision = "c001"
down_revision = "b023"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add schedule management columns to agent_configurations
    op.add_column(
        "agent_configurations",
        sa.Column("schedule_type", sa.String(20), nullable=True, comment="cron | interval | manual")
    )
    op.add_column(
        "agent_configurations",
        sa.Column("schedule_cron", sa.String(100), nullable=True, comment="cron expression (e.g., '0 8 * * *')")
    )
    op.add_column(
        "agent_configurations",
        sa.Column("schedule_interval_hours", sa.Integer(), nullable=True, comment="interval in hours")
    )
    op.add_column(
        "agent_configurations",
        sa.Column("next_run_at", sa.DateTime(timezone=True), nullable=True, comment="next scheduled run time")
    )
    op.add_column(
        "agent_configurations",
        sa.Column("last_run_at", sa.DateTime(timezone=True), nullable=True, comment="last execution time")
    )

    # Add index for scheduling queries
    op.create_index(
        "idx_agent_config_next_run",
        "agent_configurations",
        ["is_enabled", "next_run_at"],
        postgresql_where=sa.text("next_run_at IS NOT NULL")
    )

    # Set default schedules for existing agents
    # Enhanced analyzer: every 6 hours
    op.execute("""
        UPDATE agent_configurations
        SET schedule_type = 'interval',
            schedule_interval_hours = 6
        WHERE agent_name = 'enhanced_analyzer'
    """)

    # Research agent: daily at 8am UTC
    op.execute("""
        UPDATE agent_configurations
        SET schedule_type = 'cron',
            schedule_cron = '0 8 * * *'
        WHERE agent_name = 'research_agent'
    """)

    # Competitive intel: every 12 hours
    op.execute("""
        UPDATE agent_configurations
        SET schedule_type = 'interval',
            schedule_interval_hours = 12
        WHERE agent_name = 'competitive_intel'
    """)


def downgrade() -> None:
    op.drop_index("idx_agent_config_next_run", "agent_configurations")
    op.drop_column("agent_configurations", "last_run_at")
    op.drop_column("agent_configurations", "next_run_at")
    op.drop_column("agent_configurations", "schedule_interval_hours")
    op.drop_column("agent_configurations", "schedule_cron")
    op.drop_column("agent_configurations", "schedule_type")
