"""Phase 9.2: AI Idea Chat Assistant

Create tables for:
- idea_chats: Chat sessions per user/insight
- idea_chat_messages: Individual chat messages

Revision ID: b017
Revises: b016
Create Date: 2026-02-04
"""

import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID

from alembic import op

revision = "b017"
down_revision = "b016"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Idea chat sessions table
    op.create_table(
        "idea_chats",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("user_id", UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("insight_id", UUID(as_uuid=True), sa.ForeignKey("insights.id", ondelete="CASCADE"), nullable=False),
        sa.Column("title", sa.String(255), nullable=True),
        sa.Column("message_count", sa.Integer(), server_default="0", nullable=False),
        sa.Column("total_tokens", sa.Integer(), server_default="0", nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("idx_idea_chats_user", "idea_chats", ["user_id"])
    op.create_index("idx_idea_chats_insight", "idea_chats", ["insight_id"])
    op.create_index("idx_idea_chats_user_insight", "idea_chats", ["user_id", "insight_id"])

    # Chat messages table
    op.create_table(
        "idea_chat_messages",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("chat_id", UUID(as_uuid=True), sa.ForeignKey("idea_chats.id", ondelete="CASCADE"), nullable=False),
        sa.Column("role", sa.String(20), nullable=False),  # user, assistant
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("tokens_used", sa.Integer(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("idx_chat_messages_chat", "idea_chat_messages", ["chat_id", sa.text("created_at ASC")])

    # Enable RLS
    op.execute("ALTER TABLE idea_chats ENABLE ROW LEVEL SECURITY")
    op.execute("ALTER TABLE idea_chat_messages ENABLE ROW LEVEL SECURITY")

    # User can access own chats
    op.execute("""
        CREATE POLICY user_idea_chats_policy ON idea_chats
        FOR ALL USING (user_id = auth.uid())
    """)

    op.execute("""
        CREATE POLICY user_chat_messages_policy ON idea_chat_messages
        FOR ALL USING (
            EXISTS (SELECT 1 FROM idea_chats WHERE idea_chats.id = idea_chat_messages.chat_id AND idea_chats.user_id = auth.uid())
        )
    """)

    # Admin can access all
    op.execute("""
        CREATE POLICY admin_idea_chats_policy ON idea_chats
        FOR ALL USING (
            EXISTS (SELECT 1 FROM admin_users WHERE admin_users.user_id = auth.uid())
        )
    """)

    op.execute("""
        CREATE POLICY admin_chat_messages_policy ON idea_chat_messages
        FOR ALL USING (
            EXISTS (SELECT 1 FROM admin_users WHERE admin_users.user_id = auth.uid())
        )
    """)


def downgrade() -> None:
    op.execute("DROP POLICY IF EXISTS admin_chat_messages_policy ON idea_chat_messages")
    op.execute("DROP POLICY IF EXISTS admin_idea_chats_policy ON idea_chats")
    op.execute("DROP POLICY IF EXISTS user_chat_messages_policy ON idea_chat_messages")
    op.execute("DROP POLICY IF EXISTS user_idea_chats_policy ON idea_chats")
    op.drop_table("idea_chat_messages")
    op.drop_table("idea_chats")
