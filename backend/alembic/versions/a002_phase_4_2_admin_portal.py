"""Phase 4.2: Admin portal tables and insight extensions

Revision ID: a002_phase_4_2
Revises: a001_phase_4_1
Create Date: 2026-01-25 13:00:00.000000

Creates:
- agent_execution_logs table (execution tracking)
- system_metrics table (LLM costs, latencies)
- ALTER insights table (add admin control columns)

RLS Policies (Supabase):
- Admin-only access to agent logs and metrics

See architecture.md Section "Admin Portal Architecture" for full specification.
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "a002_phase_4_2"
down_revision: Union[str, Sequence[str], None] = "a001_phase_4_1"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create Phase 4.2 tables and extend insights."""

    # ============================================
    # 1. AGENT_EXECUTION_LOGS TABLE
    # ============================================
    op.create_table(
        "agent_execution_logs",
        sa.Column("id", sa.UUID(), nullable=False, server_default=sa.text("gen_random_uuid()")),
        sa.Column("agent_type", sa.String(length=50), nullable=False),
        sa.Column("source", sa.String(length=50), nullable=True),
        sa.Column("status", sa.String(length=20), nullable=False),
        sa.Column("started_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("duration_ms", sa.Integer(), nullable=True),
        sa.Column("items_processed", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("items_failed", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("extra_metadata", postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default="{}"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_index("idx_agent_logs_type_status", "agent_execution_logs", ["agent_type", "status"])
    op.create_index("idx_agent_logs_created", "agent_execution_logs", ["created_at"])
    op.create_index("idx_agent_logs_source", "agent_execution_logs", ["source"])

    # ============================================
    # 2. SYSTEM_METRICS TABLE
    # ============================================
    op.create_table(
        "system_metrics",
        sa.Column("id", sa.UUID(), nullable=False, server_default=sa.text("gen_random_uuid()")),
        sa.Column("metric_type", sa.String(length=50), nullable=False),
        sa.Column("metric_value", sa.Numeric(10, 4), nullable=False),
        sa.Column("dimensions", postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default="{}"),
        sa.Column("recorded_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_index("idx_metrics_type_recorded", "system_metrics", ["metric_type", "recorded_at"])
    op.create_index("idx_metrics_type", "system_metrics", ["metric_type"])

    # ============================================
    # 3. EXTEND INSIGHTS TABLE FOR ADMIN CONTROL
    # ============================================
    op.add_column(
        "insights",
        sa.Column("admin_status", sa.String(length=20), nullable=True, server_default="approved"),
    )
    op.add_column(
        "insights",
        sa.Column("admin_notes", sa.Text(), nullable=True),
    )
    op.add_column(
        "insights",
        sa.Column("admin_override_score", sa.Float(), nullable=True),
    )
    op.add_column(
        "insights",
        sa.Column("edited_by", sa.UUID(), nullable=True),
    )
    op.add_column(
        "insights",
        sa.Column("edited_at", sa.DateTime(timezone=True), nullable=True),
    )

    # Add foreign key constraint for edited_by
    op.create_foreign_key(
        "fk_insights_edited_by_admin",
        "insights",
        "admin_users",
        ["edited_by"],
        ["id"],
        ondelete="SET NULL",
    )

    op.create_index("idx_insights_admin_status", "insights", ["admin_status"])
    op.create_index("idx_insights_edited_by", "insights", ["edited_by"])

    # ============================================
    # 4. RLS POLICIES (Supabase)
    # ============================================
    # RLS policies - only execute on Supabase (where auth schema exists)
    op.execute("""
        DO $$
        BEGIN
            -- Check if auth schema exists (Supabase)
            IF EXISTS (SELECT 1 FROM information_schema.schemata WHERE schema_name = 'auth') THEN
                -- Enable RLS on new tables
                ALTER TABLE agent_execution_logs ENABLE ROW LEVEL SECURITY;
                ALTER TABLE system_metrics ENABLE ROW LEVEL SECURITY;

                -- Agent execution logs RLS (admins only)
                CREATE POLICY "Only admins can view agent logs"
                ON agent_execution_logs FOR SELECT
                USING (
                    EXISTS (
                        SELECT 1 FROM admin_users au
                        JOIN users u ON au.user_id = u.id
                        WHERE u.supabase_user_id = auth.uid()::text
                    )
                );

                CREATE POLICY "Only admins can insert agent logs"
                ON agent_execution_logs FOR INSERT
                WITH CHECK (
                    EXISTS (
                        SELECT 1 FROM admin_users au
                        JOIN users u ON au.user_id = u.id
                        WHERE u.supabase_user_id = auth.uid()::text
                    )
                );

                -- System metrics RLS (admins only)
                CREATE POLICY "Only admins can view system metrics"
                ON system_metrics FOR SELECT
                USING (
                    EXISTS (
                        SELECT 1 FROM admin_users au
                        JOIN users u ON au.user_id = u.id
                        WHERE u.supabase_user_id = auth.uid()::text
                    )
                );

                CREATE POLICY "Only admins can insert system metrics"
                ON system_metrics FOR INSERT
                WITH CHECK (
                    EXISTS (
                        SELECT 1 FROM admin_users au
                        JOIN users u ON au.user_id = u.id
                        WHERE u.supabase_user_id = auth.uid()::text
                    )
                );
            END IF;
        END $$;
    """)


def downgrade() -> None:
    """Remove Phase 4.2 tables and extensions."""

    # Drop RLS policies
    policies = [
        ("agent_execution_logs", "Only admins can view agent logs"),
        ("agent_execution_logs", "Only admins can insert agent logs"),
        ("system_metrics", "Only admins can view system metrics"),
        ("system_metrics", "Only admins can insert system metrics"),
    ]

    for table, policy_name in policies:
        op.execute(f'DROP POLICY IF EXISTS "{policy_name}" ON {table};')

    # Disable RLS
    op.execute("ALTER TABLE system_metrics DISABLE ROW LEVEL SECURITY;")
    op.execute("ALTER TABLE agent_execution_logs DISABLE ROW LEVEL SECURITY;")

    # Remove insights extensions
    op.drop_index("idx_insights_edited_by", table_name="insights")
    op.drop_index("idx_insights_admin_status", table_name="insights")
    op.drop_constraint("fk_insights_edited_by_admin", "insights", type_="foreignkey")
    op.drop_column("insights", "edited_at")
    op.drop_column("insights", "edited_by")
    op.drop_column("insights", "admin_override_score")
    op.drop_column("insights", "admin_notes")
    op.drop_column("insights", "admin_status")

    # Drop tables
    op.drop_table("system_metrics")
    op.drop_table("agent_execution_logs")
