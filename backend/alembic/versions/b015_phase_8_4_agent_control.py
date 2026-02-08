"""Phase 8.4-8.5: AI Agent Control & Security Audit

Create tables for:
- agent_configurations: AI agent settings
- audit_logs: Security audit trail

Revision ID: b015
Revises: b014
Create Date: 2026-02-04
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID, JSONB

revision = "b015"
down_revision = "b014"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Agent configurations table
    op.create_table(
        "agent_configurations",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("agent_name", sa.String(50), unique=True, nullable=False),
        sa.Column("is_enabled", sa.Boolean(), server_default=sa.text("true"), nullable=False),
        sa.Column("model_name", sa.String(100), server_default="gemini-1.5-flash", nullable=False),
        sa.Column("temperature", sa.Numeric(3, 2), server_default="0.7", nullable=False),
        sa.Column("max_tokens", sa.Integer(), server_default="4096", nullable=False),
        sa.Column("rate_limit_per_hour", sa.Integer(), server_default="100", nullable=False),
        sa.Column("cost_limit_daily_usd", sa.Numeric(10, 2), server_default="50.00", nullable=False),
        sa.Column("custom_prompts", JSONB, nullable=True),
        sa.Column("updated_by", UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )

    # Audit logs table
    op.create_table(
        "audit_logs",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("user_id", UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("action", sa.String(100), nullable=False),
        sa.Column("resource_type", sa.String(50), nullable=False),
        sa.Column("resource_id", UUID(as_uuid=True), nullable=True),
        sa.Column("details", JSONB, nullable=True),
        sa.Column("ip_address", sa.String(45), nullable=True),
        sa.Column("user_agent", sa.String(500), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("idx_audit_logs_user_time", "audit_logs", ["user_id", sa.text("created_at DESC")])
    op.create_index("idx_audit_logs_action", "audit_logs", ["action", sa.text("created_at DESC")])
    op.create_index("idx_audit_logs_resource", "audit_logs", ["resource_type", "resource_id"])

    # Enable RLS
    op.execute("ALTER TABLE agent_configurations ENABLE ROW LEVEL SECURITY")
    op.execute("ALTER TABLE audit_logs ENABLE ROW LEVEL SECURITY")

    op.execute("""
        CREATE POLICY admin_agent_config_policy ON agent_configurations
        FOR ALL USING (
            EXISTS (SELECT 1 FROM admin_users WHERE admin_users.user_id = auth.uid())
        )
    """)

    op.execute("""
        CREATE POLICY admin_audit_logs_policy ON audit_logs
        FOR ALL USING (
            EXISTS (SELECT 1 FROM admin_users WHERE admin_users.user_id = auth.uid())
        )
    """)

    # Insert default agent configurations
    op.execute("""
        INSERT INTO agent_configurations (agent_name, model_name, temperature, max_tokens, rate_limit_per_hour)
        VALUES
            ('enhanced_analyzer', 'gemini-1.5-flash', 0.7, 4096, 100),
            ('research_agent', 'gemini-1.5-pro', 0.3, 8192, 20),
            ('competitive_intel', 'gemini-1.5-flash', 0.5, 4096, 50)
    """)


def downgrade() -> None:
    op.execute("DROP POLICY IF EXISTS admin_agent_config_policy ON agent_configurations")
    op.execute("DROP POLICY IF EXISTS admin_audit_logs_policy ON audit_logs")
    op.drop_table("audit_logs")
    op.drop_table("agent_configurations")
