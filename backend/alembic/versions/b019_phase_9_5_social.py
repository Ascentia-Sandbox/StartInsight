"""Phase 9.5: Social & Community Features

Create tables for:
- founder_profiles: Public founder profiles
- founder_connections: Connection requests
- idea_clubs: Topic-based communities
- club_members: Club membership
- club_posts: Club discussion posts

Revision ID: b019
Revises: b018
Create Date: 2026-02-04
"""

import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB, UUID

from alembic import op

revision = "b019"
down_revision = "b018"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Founder profiles table
    op.create_table(
        "founder_profiles",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("user_id", UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), unique=True, nullable=False),
        sa.Column("username", sa.String(50), unique=True, nullable=False),
        sa.Column("display_name", sa.String(100), nullable=True),
        sa.Column("bio", sa.Text(), nullable=True),
        sa.Column("avatar_url", sa.String(500), nullable=True),
        sa.Column("location", sa.String(100), nullable=True),
        sa.Column("skills", JSONB, nullable=True),  # ["python", "marketing"]
        sa.Column("interests", JSONB, nullable=True),  # ["ai", "fintech"]
        sa.Column("social_links", JSONB, nullable=True),  # {twitter, linkedin, github}
        sa.Column("is_public", sa.Boolean(), server_default=sa.text("false"), nullable=False),
        sa.Column("accepting_connections", sa.Boolean(), server_default=sa.text("true"), nullable=False),
        sa.Column("connection_count", sa.Integer(), server_default="0", nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("idx_founder_profiles_username", "founder_profiles", ["username"])
    op.create_index("idx_founder_profiles_public", "founder_profiles", ["is_public"])

    # Founder connections table
    op.create_table(
        "founder_connections",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("requester_id", UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("recipient_id", UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("status", sa.String(20), server_default="pending", nullable=False),  # pending, accepted, rejected
        sa.Column("message", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("responded_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_unique_constraint("uq_founder_connections", "founder_connections", ["requester_id", "recipient_id"])
    op.create_index("idx_founder_connections_recipient", "founder_connections", ["recipient_id", "status"])

    # Idea clubs table
    op.create_table(
        "idea_clubs",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("name", sa.String(100), unique=True, nullable=False),
        sa.Column("slug", sa.String(100), unique=True, nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("category", sa.String(50), nullable=True),
        sa.Column("cover_image_url", sa.String(500), nullable=True),
        sa.Column("member_count", sa.Integer(), server_default="0", nullable=False),
        sa.Column("post_count", sa.Integer(), server_default="0", nullable=False),
        sa.Column("is_public", sa.Boolean(), server_default=sa.text("true"), nullable=False),
        sa.Column("is_official", sa.Boolean(), server_default=sa.text("false"), nullable=False),
        sa.Column("created_by", UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("idx_idea_clubs_slug", "idea_clubs", ["slug"])
    op.create_index("idx_idea_clubs_category", "idea_clubs", ["category"])

    # Club members table
    op.create_table(
        "club_members",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("club_id", UUID(as_uuid=True), sa.ForeignKey("idea_clubs.id", ondelete="CASCADE"), nullable=False),
        sa.Column("user_id", UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("role", sa.String(20), server_default="member", nullable=False),  # admin, moderator, member
        sa.Column("joined_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_unique_constraint("uq_club_members", "club_members", ["club_id", "user_id"])
    op.create_index("idx_club_members_user", "club_members", ["user_id"])

    # Club posts table
    op.create_table(
        "club_posts",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("club_id", UUID(as_uuid=True), sa.ForeignKey("idea_clubs.id", ondelete="CASCADE"), nullable=False),
        sa.Column("user_id", UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("title", sa.String(255), nullable=True),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("post_type", sa.String(20), server_default="discussion", nullable=False),  # discussion, idea_share, question
        sa.Column("insight_id", UUID(as_uuid=True), sa.ForeignKey("insights.id", ondelete="SET NULL"), nullable=True),
        sa.Column("upvotes", sa.Integer(), server_default="0", nullable=False),
        sa.Column("comment_count", sa.Integer(), server_default="0", nullable=False),
        sa.Column("is_pinned", sa.Boolean(), server_default=sa.text("false"), nullable=False),
        sa.Column("is_deleted", sa.Boolean(), server_default=sa.text("false"), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("idx_club_posts_club", "club_posts", ["club_id", sa.text("created_at DESC")])
    op.create_index("idx_club_posts_user", "club_posts", ["user_id"])

    # Enable RLS
    op.execute("ALTER TABLE founder_profiles ENABLE ROW LEVEL SECURITY")
    op.execute("ALTER TABLE founder_connections ENABLE ROW LEVEL SECURITY")
    op.execute("ALTER TABLE idea_clubs ENABLE ROW LEVEL SECURITY")
    op.execute("ALTER TABLE club_members ENABLE ROW LEVEL SECURITY")
    op.execute("ALTER TABLE club_posts ENABLE ROW LEVEL SECURITY")

    # Founder profiles: public can read public profiles, user can manage own
    op.execute("""
        CREATE POLICY read_public_profiles_policy ON founder_profiles
        FOR SELECT USING (is_public = true OR user_id = auth.uid())
    """)
    op.execute("""
        CREATE POLICY manage_own_profile_policy ON founder_profiles
        FOR ALL USING (user_id = auth.uid())
    """)

    # Connections: user can see own, manage own
    op.execute("""
        CREATE POLICY user_connections_policy ON founder_connections
        FOR ALL USING (requester_id = auth.uid() OR recipient_id = auth.uid())
    """)

    # Clubs: public clubs are readable by all
    op.execute("""
        CREATE POLICY read_public_clubs_policy ON idea_clubs
        FOR SELECT USING (is_public = true)
    """)
    op.execute("""
        CREATE POLICY manage_clubs_policy ON idea_clubs
        FOR ALL USING (
            created_by = auth.uid() OR
            EXISTS (SELECT 1 FROM admin_users WHERE admin_users.user_id = auth.uid())
        )
    """)

    # Club members: readable if member or public club
    op.execute("""
        CREATE POLICY read_club_members_policy ON club_members
        FOR SELECT USING (
            user_id = auth.uid() OR
            EXISTS (SELECT 1 FROM idea_clubs WHERE idea_clubs.id = club_members.club_id AND idea_clubs.is_public = true)
        )
    """)
    op.execute("""
        CREATE POLICY manage_membership_policy ON club_members
        FOR ALL USING (user_id = auth.uid())
    """)

    # Club posts: readable if member or public club
    op.execute("""
        CREATE POLICY read_club_posts_policy ON club_posts
        FOR SELECT USING (
            EXISTS (SELECT 1 FROM idea_clubs WHERE idea_clubs.id = club_posts.club_id AND idea_clubs.is_public = true) OR
            EXISTS (SELECT 1 FROM club_members WHERE club_members.club_id = club_posts.club_id AND club_members.user_id = auth.uid())
        )
    """)
    op.execute("""
        CREATE POLICY manage_own_posts_policy ON club_posts
        FOR ALL USING (user_id = auth.uid())
    """)


def downgrade() -> None:
    op.execute("DROP POLICY IF EXISTS manage_own_posts_policy ON club_posts")
    op.execute("DROP POLICY IF EXISTS read_club_posts_policy ON club_posts")
    op.execute("DROP POLICY IF EXISTS manage_membership_policy ON club_members")
    op.execute("DROP POLICY IF EXISTS read_club_members_policy ON club_members")
    op.execute("DROP POLICY IF EXISTS manage_clubs_policy ON idea_clubs")
    op.execute("DROP POLICY IF EXISTS read_public_clubs_policy ON idea_clubs")
    op.execute("DROP POLICY IF EXISTS user_connections_policy ON founder_connections")
    op.execute("DROP POLICY IF EXISTS manage_own_profile_policy ON founder_profiles")
    op.execute("DROP POLICY IF EXISTS read_public_profiles_policy ON founder_profiles")
    op.drop_table("club_posts")
    op.drop_table("club_members")
    op.drop_table("idea_clubs")
    op.drop_table("founder_connections")
    op.drop_table("founder_profiles")
