"""Phase 8.3: User & Revenue Intelligence

Create tables for:
- user_activity_events: User behavior tracking
- user_sessions: Session analytics

Revision ID: b014
Revises: b013
Create Date: 2026-02-04
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID, JSONB

revision = "b014"
down_revision = "b013"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # User activity events table
    op.create_table(
        "user_activity_events",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("user_id", UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("event_type", sa.String(50), nullable=False, comment="page_view, feature_use, insight_save, etc."),
        sa.Column("event_data", JSONB, nullable=True),
        sa.Column("session_id", sa.String(100), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("idx_activity_events_user_time", "user_activity_events", ["user_id", sa.text("created_at DESC")])
    op.create_index("idx_activity_events_type_time", "user_activity_events", ["event_type", sa.text("created_at DESC")])
    op.create_index("idx_activity_events_session", "user_activity_events", ["session_id"])

    # User sessions table
    op.create_table(
        "user_sessions",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("user_id", UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("session_id", sa.String(100), unique=True, nullable=False),
        sa.Column("started_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("ended_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("duration_seconds", sa.Integer(), nullable=True),
        sa.Column("page_views", sa.Integer(), server_default="0", nullable=False),
        sa.Column("events_count", sa.Integer(), server_default="0", nullable=False),
        sa.Column("device_type", sa.String(20), nullable=True),
        sa.Column("referrer", sa.String(500), nullable=True),
    )
    op.create_index("idx_sessions_user_time", "user_sessions", ["user_id", sa.text("started_at DESC")])

    # Enable RLS
    for table in ["user_activity_events", "user_sessions"]:
        op.execute(f"ALTER TABLE {table} ENABLE ROW LEVEL SECURITY")
        # Users can see their own data, admins can see all
        op.execute(f"""
            CREATE POLICY user_{table}_policy ON {table}
            FOR ALL USING (
                user_id = auth.uid() OR
                EXISTS (SELECT 1 FROM admin_users WHERE admin_users.user_id = auth.uid())
            )
        """)


def downgrade() -> None:
    for table in ["user_sessions", "user_activity_events"]:
        op.execute(f"DROP POLICY IF EXISTS user_{table}_policy ON {table}")
        op.drop_table(table)
