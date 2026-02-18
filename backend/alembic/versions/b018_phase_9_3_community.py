"""Phase 9.3: Community Voting & Comments

Create tables for:
- idea_votes: Upvote/downvote ideas
- idea_comments: Discussion threads on ideas
- idea_polls: Quick polls on ideas
- poll_responses: User poll responses

Revision ID: b018
Revises: b017
Create Date: 2026-02-04
"""

import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB, UUID

from alembic import op

revision = "b018"
down_revision = "b017"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Idea votes table
    op.create_table(
        "idea_votes",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("user_id", UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("insight_id", UUID(as_uuid=True), sa.ForeignKey("insights.id", ondelete="CASCADE"), nullable=False),
        sa.Column("vote_type", sa.String(10), nullable=False),  # up, down
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("idx_idea_votes_insight", "idea_votes", ["insight_id"])
    op.create_unique_constraint("uq_idea_votes_user_insight", "idea_votes", ["user_id", "insight_id"])

    # Idea comments table
    op.create_table(
        "idea_comments",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("user_id", UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("insight_id", UUID(as_uuid=True), sa.ForeignKey("insights.id", ondelete="CASCADE"), nullable=False),
        sa.Column("parent_id", UUID(as_uuid=True), sa.ForeignKey("idea_comments.id", ondelete="CASCADE"), nullable=True),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("upvotes", sa.Integer(), server_default="0", nullable=False),
        sa.Column("is_expert", sa.Boolean(), server_default=sa.text("false"), nullable=False),
        sa.Column("is_pinned", sa.Boolean(), server_default=sa.text("false"), nullable=False),
        sa.Column("is_deleted", sa.Boolean(), server_default=sa.text("false"), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("idx_idea_comments_insight", "idea_comments", ["insight_id"])
    op.create_index("idx_idea_comments_parent", "idea_comments", ["parent_id"])
    op.create_index("idx_idea_comments_user", "idea_comments", ["user_id"])

    # Comment upvotes (separate from idea votes)
    op.create_table(
        "comment_upvotes",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("user_id", UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("comment_id", UUID(as_uuid=True), sa.ForeignKey("idea_comments.id", ondelete="CASCADE"), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_unique_constraint("uq_comment_upvotes_user_comment", "comment_upvotes", ["user_id", "comment_id"])

    # Idea polls table
    op.create_table(
        "idea_polls",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("insight_id", UUID(as_uuid=True), sa.ForeignKey("insights.id", ondelete="CASCADE"), nullable=False),
        sa.Column("created_by", UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("question", sa.String(255), nullable=False),
        sa.Column("poll_type", sa.String(20), server_default="yes_no", nullable=False),  # yes_no, scale, multiple
        sa.Column("options", JSONB, nullable=True),
        sa.Column("is_active", sa.Boolean(), server_default=sa.text("true"), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("idx_idea_polls_insight", "idea_polls", ["insight_id"])

    # Poll responses table
    op.create_table(
        "poll_responses",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("poll_id", UUID(as_uuid=True), sa.ForeignKey("idea_polls.id", ondelete="CASCADE"), nullable=False),
        sa.Column("user_id", UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("response", sa.String(100), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_unique_constraint("uq_poll_responses_user_poll", "poll_responses", ["poll_id", "user_id"])
    op.create_index("idx_poll_responses_poll", "poll_responses", ["poll_id"])

    # Enable RLS
    op.execute("ALTER TABLE idea_votes ENABLE ROW LEVEL SECURITY")
    op.execute("ALTER TABLE idea_comments ENABLE ROW LEVEL SECURITY")
    op.execute("ALTER TABLE comment_upvotes ENABLE ROW LEVEL SECURITY")
    op.execute("ALTER TABLE idea_polls ENABLE ROW LEVEL SECURITY")
    op.execute("ALTER TABLE poll_responses ENABLE ROW LEVEL SECURITY")

    # Votes: user can manage own, read all
    op.execute("""
        CREATE POLICY user_idea_votes_select_policy ON idea_votes
        FOR SELECT USING (true)
    """)
    op.execute("""
        CREATE POLICY user_idea_votes_modify_policy ON idea_votes
        FOR ALL USING (user_id = auth.uid())
    """)

    # Comments: everyone can read, user can manage own
    op.execute("""
        CREATE POLICY user_idea_comments_select_policy ON idea_comments
        FOR SELECT USING (true)
    """)
    op.execute("""
        CREATE POLICY user_idea_comments_modify_policy ON idea_comments
        FOR ALL USING (user_id = auth.uid())
    """)

    # Comment upvotes
    op.execute("""
        CREATE POLICY user_comment_upvotes_policy ON comment_upvotes
        FOR ALL USING (user_id = auth.uid())
    """)

    # Polls: everyone can read, admin/owner can manage
    op.execute("""
        CREATE POLICY user_idea_polls_select_policy ON idea_polls
        FOR SELECT USING (true)
    """)
    op.execute("""
        CREATE POLICY user_idea_polls_modify_policy ON idea_polls
        FOR ALL USING (
            created_by = auth.uid() OR
            EXISTS (SELECT 1 FROM admin_users WHERE admin_users.user_id = auth.uid())
        )
    """)

    # Poll responses: user can manage own
    op.execute("""
        CREATE POLICY user_poll_responses_policy ON poll_responses
        FOR ALL USING (user_id = auth.uid())
    """)
    op.execute("""
        CREATE POLICY read_poll_responses_policy ON poll_responses
        FOR SELECT USING (true)
    """)


def downgrade() -> None:
    op.execute("DROP POLICY IF EXISTS read_poll_responses_policy ON poll_responses")
    op.execute("DROP POLICY IF EXISTS user_poll_responses_policy ON poll_responses")
    op.execute("DROP POLICY IF EXISTS user_idea_polls_modify_policy ON idea_polls")
    op.execute("DROP POLICY IF EXISTS user_idea_polls_select_policy ON idea_polls")
    op.execute("DROP POLICY IF EXISTS user_comment_upvotes_policy ON comment_upvotes")
    op.execute("DROP POLICY IF EXISTS user_idea_comments_modify_policy ON idea_comments")
    op.execute("DROP POLICY IF EXISTS user_idea_comments_select_policy ON idea_comments")
    op.execute("DROP POLICY IF EXISTS user_idea_votes_modify_policy ON idea_votes")
    op.execute("DROP POLICY IF EXISTS user_idea_votes_select_policy ON idea_votes")
    op.drop_table("poll_responses")
    op.drop_table("idea_polls")
    op.drop_table("comment_upvotes")
    op.drop_table("idea_comments")
    op.drop_table("idea_votes")
