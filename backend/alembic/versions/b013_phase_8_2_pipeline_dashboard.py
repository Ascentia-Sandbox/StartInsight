"""Phase 8.2: Data Pipeline Command Center

Create tables for:
- pipeline_health_checks: Scraper health monitoring
- api_quota_usage: API quota tracking
- admin_alerts: Alert configurations
- admin_alert_incidents: Alert incidents

Revision ID: b013
Revises: b012
Create Date: 2026-02-04
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID, JSONB

revision = "b013"
down_revision = "b012"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Pipeline health checks table
    op.create_table(
        "pipeline_health_checks",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("scraper_name", sa.String(50), nullable=False),
        sa.Column("status", sa.String(20), nullable=False, comment="healthy, degraded, down"),
        sa.Column("response_time_ms", sa.Integer(), nullable=True),
        sa.Column("items_fetched", sa.Integer(), nullable=True),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("checked_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("idx_health_checks_scraper_time", "pipeline_health_checks", ["scraper_name", sa.text("checked_at DESC")])

    # API quota usage table
    op.create_table(
        "api_quota_usage",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("api_name", sa.String(50), nullable=False),
        sa.Column("metric_name", sa.String(50), nullable=False, comment="requests, tokens, cost_usd"),
        sa.Column("value", sa.Numeric(12, 4), nullable=False),
        sa.Column("period_start", sa.DateTime(timezone=True), nullable=False),
        sa.Column("period_end", sa.DateTime(timezone=True), nullable=False),
        sa.Column("recorded_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("idx_quota_usage_api_period", "api_quota_usage", ["api_name", "period_start"])

    # Admin alerts configuration table
    op.create_table(
        "admin_alerts",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("alert_name", sa.String(100), nullable=False),
        sa.Column("alert_type", sa.String(50), nullable=False, comment="threshold, anomaly, failure"),
        sa.Column("metric_name", sa.String(100), nullable=False),
        sa.Column("condition", JSONB, nullable=False, comment='{"operator": "lt", "value": 0.8}'),
        sa.Column("severity", sa.String(20), server_default="warning", nullable=False),
        sa.Column("notification_channels", JSONB, nullable=True),
        sa.Column("is_active", sa.Boolean(), server_default=sa.text("true"), nullable=False),
        sa.Column("created_by", UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("idx_alerts_active", "admin_alerts", ["is_active"])

    # Admin alert incidents table
    op.create_table(
        "admin_alert_incidents",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("alert_id", UUID(as_uuid=True), sa.ForeignKey("admin_alerts.id", ondelete="CASCADE"), nullable=False),
        sa.Column("triggered_value", sa.Numeric(12, 4), nullable=True),
        sa.Column("status", sa.String(20), server_default="open", nullable=False, comment="open, acknowledged, resolved"),
        sa.Column("acknowledged_by", UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("resolved_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("idx_incidents_alert_status", "admin_alert_incidents", ["alert_id", "status"])

    # Enable RLS
    for table in ["pipeline_health_checks", "api_quota_usage", "admin_alerts", "admin_alert_incidents"]:
        op.execute(f"ALTER TABLE {table} ENABLE ROW LEVEL SECURITY")
        op.execute(f"""
            CREATE POLICY admin_{table}_policy ON {table}
            FOR ALL USING (
                EXISTS (SELECT 1 FROM admin_users WHERE admin_users.user_id = auth.uid())
            )
        """)


def downgrade() -> None:
    for table in ["admin_alert_incidents", "admin_alerts", "api_quota_usage", "pipeline_health_checks"]:
        op.execute(f"DROP POLICY IF EXISTS admin_{table}_policy ON {table}")
        op.drop_table(table)
