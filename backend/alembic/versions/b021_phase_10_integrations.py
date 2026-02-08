"""Phase 10: Integration Ecosystem

Create tables for:
- external_integrations: Connected services (Notion, Airtable, Slack)
- integration_webhooks: Webhook endpoints for external services
- integration_syncs: Sync status tracking
- browser_extension_tokens: Chrome extension authentication

Revision ID: b021
Revises: b020
Create Date: 2026-02-04
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID, JSONB

revision = "b021"
down_revision = "b020"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # External integrations table
    op.create_table(
        "external_integrations",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("user_id", UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("service_type", sa.String(50), nullable=False),  # notion, airtable, slack, discord, linear, jira
        sa.Column("service_name", sa.String(100), nullable=True),  # User's name for this integration
        sa.Column("access_token", sa.Text(), nullable=True),  # Encrypted OAuth token
        sa.Column("refresh_token", sa.Text(), nullable=True),
        sa.Column("token_expires_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("workspace_id", sa.String(255), nullable=True),  # External workspace/team ID
        sa.Column("workspace_name", sa.String(255), nullable=True),
        sa.Column("config", JSONB, nullable=True),  # Service-specific config
        sa.Column("is_active", sa.Boolean(), server_default=sa.text("true"), nullable=False),
        sa.Column("last_sync_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("sync_error", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("idx_external_integrations_user", "external_integrations", ["user_id"])
    op.create_index("idx_external_integrations_service", "external_integrations", ["service_type", "is_active"])

    # Integration webhooks table
    op.create_table(
        "integration_webhooks",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("integration_id", UUID(as_uuid=True), sa.ForeignKey("external_integrations.id", ondelete="CASCADE"), nullable=False),
        sa.Column("webhook_type", sa.String(50), nullable=False),  # new_insight, insight_update, research_complete
        sa.Column("webhook_url", sa.String(500), nullable=False),
        sa.Column("secret", sa.String(255), nullable=True),  # For signature verification
        sa.Column("is_active", sa.Boolean(), server_default=sa.text("true"), nullable=False),
        sa.Column("last_triggered_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("failure_count", sa.Integer(), server_default="0", nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("idx_webhooks_integration", "integration_webhooks", ["integration_id"])
    op.create_index("idx_webhooks_type", "integration_webhooks", ["webhook_type", "is_active"])

    # Integration sync log table
    op.create_table(
        "integration_syncs",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("integration_id", UUID(as_uuid=True), sa.ForeignKey("external_integrations.id", ondelete="CASCADE"), nullable=False),
        sa.Column("sync_type", sa.String(50), nullable=False),  # full, incremental, webhook
        sa.Column("status", sa.String(20), nullable=False),  # started, completed, failed
        sa.Column("items_synced", sa.Integer(), server_default="0", nullable=False),
        sa.Column("items_failed", sa.Integer(), server_default="0", nullable=False),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("started_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index("idx_syncs_integration", "integration_syncs", ["integration_id", sa.text("started_at DESC")])

    # Browser extension tokens table
    op.create_table(
        "browser_extension_tokens",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("user_id", UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("token_hash", sa.String(64), unique=True, nullable=False),  # SHA-256 hash
        sa.Column("device_name", sa.String(100), nullable=True),
        sa.Column("browser", sa.String(50), nullable=True),  # chrome, firefox, edge
        sa.Column("last_used_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("last_ip", sa.String(45), nullable=True),
        sa.Column("is_active", sa.Boolean(), server_default=sa.text("true"), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index("idx_ext_tokens_user", "browser_extension_tokens", ["user_id"])
    op.create_index("idx_ext_tokens_hash", "browser_extension_tokens", ["token_hash"])

    # Slack/Discord subscriptions table
    op.create_table(
        "bot_subscriptions",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("integration_id", UUID(as_uuid=True), sa.ForeignKey("external_integrations.id", ondelete="CASCADE"), nullable=False),
        sa.Column("channel_id", sa.String(100), nullable=False),  # Slack/Discord channel ID
        sa.Column("channel_name", sa.String(100), nullable=True),
        sa.Column("subscription_type", sa.String(50), nullable=False),  # keyword, trending, new_insights
        sa.Column("keywords", JSONB, nullable=True),  # For keyword subscriptions
        sa.Column("min_score", sa.Numeric(3, 2), nullable=True),  # Minimum relevance score
        sa.Column("frequency", sa.String(20), server_default="instant", nullable=False),  # instant, daily, weekly
        sa.Column("is_active", sa.Boolean(), server_default=sa.text("true"), nullable=False),
        sa.Column("last_notified_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("idx_bot_subscriptions_integration", "bot_subscriptions", ["integration_id"])
    op.create_index("idx_bot_subscriptions_type", "bot_subscriptions", ["subscription_type", "is_active"])

    # Enable RLS
    op.execute("ALTER TABLE external_integrations ENABLE ROW LEVEL SECURITY")
    op.execute("ALTER TABLE integration_webhooks ENABLE ROW LEVEL SECURITY")
    op.execute("ALTER TABLE integration_syncs ENABLE ROW LEVEL SECURITY")
    op.execute("ALTER TABLE browser_extension_tokens ENABLE ROW LEVEL SECURITY")
    op.execute("ALTER TABLE bot_subscriptions ENABLE ROW LEVEL SECURITY")

    # User can access own integrations
    op.execute("""
        CREATE POLICY user_integrations_policy ON external_integrations
        FOR ALL USING (user_id = auth.uid())
    """)

    op.execute("""
        CREATE POLICY user_webhooks_policy ON integration_webhooks
        FOR ALL USING (
            EXISTS (SELECT 1 FROM external_integrations WHERE external_integrations.id = integration_webhooks.integration_id AND external_integrations.user_id = auth.uid())
        )
    """)

    op.execute("""
        CREATE POLICY user_syncs_policy ON integration_syncs
        FOR SELECT USING (
            EXISTS (SELECT 1 FROM external_integrations WHERE external_integrations.id = integration_syncs.integration_id AND external_integrations.user_id = auth.uid())
        )
    """)

    op.execute("""
        CREATE POLICY user_ext_tokens_policy ON browser_extension_tokens
        FOR ALL USING (user_id = auth.uid())
    """)

    op.execute("""
        CREATE POLICY user_bot_subs_policy ON bot_subscriptions
        FOR ALL USING (
            EXISTS (SELECT 1 FROM external_integrations WHERE external_integrations.id = bot_subscriptions.integration_id AND external_integrations.user_id = auth.uid())
        )
    """)

    # Admin policies
    op.execute("""
        CREATE POLICY admin_integrations_policy ON external_integrations
        FOR ALL USING (
            EXISTS (SELECT 1 FROM admin_users WHERE admin_users.user_id = auth.uid())
        )
    """)


def downgrade() -> None:
    op.execute("DROP POLICY IF EXISTS admin_integrations_policy ON external_integrations")
    op.execute("DROP POLICY IF EXISTS user_bot_subs_policy ON bot_subscriptions")
    op.execute("DROP POLICY IF EXISTS user_ext_tokens_policy ON browser_extension_tokens")
    op.execute("DROP POLICY IF EXISTS user_syncs_policy ON integration_syncs")
    op.execute("DROP POLICY IF EXISTS user_webhooks_policy ON integration_webhooks")
    op.execute("DROP POLICY IF EXISTS user_integrations_policy ON external_integrations")
    op.drop_table("bot_subscriptions")
    op.drop_table("browser_extension_tokens")
    op.drop_table("integration_syncs")
    op.drop_table("integration_webhooks")
    op.drop_table("external_integrations")
