"""Phase 9.1: User Preferences & Email Digest System

Create tables for:
- user_preferences: Idea matching and personalization
- email_preferences: Digest and alert settings
- email_sends: Email delivery tracking

Revision ID: b016
Revises: b015
Create Date: 2026-02-04
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID, JSONB

revision = "b016"
down_revision = "b015"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # User preferences table for idea matching
    op.create_table(
        "user_preferences",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("user_id", UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), unique=True, nullable=False),
        sa.Column("background", sa.String(50), nullable=True),  # tech, business, creative, other
        sa.Column("budget_range", sa.String(20), nullable=True),  # 0-1k, 1k-10k, 10k+
        sa.Column("time_commitment", sa.String(20), nullable=True),  # nights_weekends, part_time, full_time
        sa.Column("market_preference", sa.String(10), nullable=True),  # b2b, b2c, both
        sa.Column("risk_tolerance", sa.String(10), nullable=True),  # low, medium, high
        sa.Column("skills", JSONB, nullable=True),  # ["python", "marketing", "sales"]
        sa.Column("interests", JSONB, nullable=True),  # ["ai", "fintech", "healthcare"]
        sa.Column("completed_quiz", sa.Boolean(), server_default=sa.text("false"), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("idx_user_preferences_user", "user_preferences", ["user_id"])

    # Email preferences table
    op.create_table(
        "email_preferences",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("user_id", UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), unique=True, nullable=False),
        sa.Column("daily_digest", sa.Boolean(), server_default=sa.text("true"), nullable=False),
        sa.Column("weekly_digest", sa.Boolean(), server_default=sa.text("true"), nullable=False),
        sa.Column("instant_alerts", sa.Boolean(), server_default=sa.text("false"), nullable=False),
        sa.Column("tracked_keywords", JSONB, nullable=True),  # ["ai", "saas", "fintech"]
        sa.Column("min_score_alert", sa.Numeric(3, 2), server_default="0.85", nullable=False),
        sa.Column("digest_time_utc", sa.String(5), server_default="09:00", nullable=False),
        sa.Column("timezone", sa.String(50), server_default="UTC", nullable=False),
        sa.Column("unsubscribed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("idx_email_preferences_user", "email_preferences", ["user_id"])

    # Email sends tracking table
    op.create_table(
        "email_sends",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("user_id", UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("email_type", sa.String(50), nullable=False),  # daily_digest, weekly_digest, instant_alert
        sa.Column("subject", sa.String(255), nullable=True),
        sa.Column("content_hash", sa.String(64), nullable=True),  # Prevent duplicate sends
        sa.Column("sent_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("opened_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("clicked_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index("idx_email_sends_user_type", "email_sends", ["user_id", "email_type"])
    op.create_index("idx_email_sends_content_hash", "email_sends", ["content_hash"])

    # Enable RLS
    op.execute("ALTER TABLE user_preferences ENABLE ROW LEVEL SECURITY")
    op.execute("ALTER TABLE email_preferences ENABLE ROW LEVEL SECURITY")
    op.execute("ALTER TABLE email_sends ENABLE ROW LEVEL SECURITY")

    # User can read/write own preferences
    op.execute("""
        CREATE POLICY user_preferences_policy ON user_preferences
        FOR ALL USING (user_id = auth.uid())
    """)

    op.execute("""
        CREATE POLICY email_preferences_policy ON email_preferences
        FOR ALL USING (user_id = auth.uid())
    """)

    op.execute("""
        CREATE POLICY email_sends_policy ON email_sends
        FOR SELECT USING (user_id = auth.uid())
    """)

    # Admin can access all
    op.execute("""
        CREATE POLICY admin_user_preferences_policy ON user_preferences
        FOR ALL USING (
            EXISTS (SELECT 1 FROM admin_users WHERE admin_users.user_id = auth.uid())
        )
    """)

    op.execute("""
        CREATE POLICY admin_email_preferences_policy ON email_preferences
        FOR ALL USING (
            EXISTS (SELECT 1 FROM admin_users WHERE admin_users.user_id = auth.uid())
        )
    """)

    op.execute("""
        CREATE POLICY admin_email_sends_policy ON email_sends
        FOR ALL USING (
            EXISTS (SELECT 1 FROM admin_users WHERE admin_users.user_id = auth.uid())
        )
    """)


def downgrade() -> None:
    op.execute("DROP POLICY IF EXISTS admin_email_sends_policy ON email_sends")
    op.execute("DROP POLICY IF EXISTS admin_email_preferences_policy ON email_preferences")
    op.execute("DROP POLICY IF EXISTS admin_user_preferences_policy ON user_preferences")
    op.execute("DROP POLICY IF EXISTS email_sends_policy ON email_sends")
    op.execute("DROP POLICY IF EXISTS email_preferences_policy ON email_preferences")
    op.execute("DROP POLICY IF EXISTS user_preferences_policy ON user_preferences")
    op.drop_table("email_sends")
    op.drop_table("email_preferences")
    op.drop_table("user_preferences")
