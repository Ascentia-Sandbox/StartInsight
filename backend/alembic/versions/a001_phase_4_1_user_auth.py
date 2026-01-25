"""Phase 4.1: User authentication and workspace tables

Revision ID: a001_phase_4_1
Revises: 3d17254743b8
Create Date: 2026-01-25 12:00:00.000000

Creates:
- users table (Supabase Auth integration)
- saved_insights table (user workspace)
- user_ratings table (insight feedback)
- admin_users table (role-based access)

RLS Policies (Supabase):
- Users can only read/update their own record
- Saved insights scoped to user
- Ratings scoped to user
- Admin users table restricted to admins

See architecture.md Section "Database Schema Extensions" for full specification.
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "a001_phase_4_1"
down_revision: Union[str, Sequence[str], None] = "3d17254743b8"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create Phase 4.1 tables with RLS policies."""

    # ============================================
    # 1. USERS TABLE
    # ============================================
    op.create_table(
        "users",
        sa.Column("id", sa.UUID(), nullable=False, server_default=sa.text("gen_random_uuid()")),
        sa.Column("supabase_user_id", sa.String(length=255), nullable=False),
        sa.Column("email", sa.String(length=255), nullable=False),
        sa.Column("display_name", sa.String(length=255), nullable=True),
        sa.Column("avatar_url", sa.Text(), nullable=True),
        sa.Column("subscription_tier", sa.String(length=20), nullable=False, server_default="free"),
        sa.Column("preferences", postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default="{}"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("last_login_at", sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("supabase_user_id", name="uq_users_supabase_id"),
        sa.UniqueConstraint("email", name="uq_users_email"),
    )

    op.create_index("idx_users_supabase_id", "users", ["supabase_user_id"])
    op.create_index("idx_users_email", "users", ["email"])
    op.create_index("idx_users_tier", "users", ["subscription_tier"])
    op.create_index("idx_users_created", "users", ["created_at"])

    # ============================================
    # 2. SAVED_INSIGHTS TABLE
    # ============================================
    op.create_table(
        "saved_insights",
        sa.Column("id", sa.UUID(), nullable=False, server_default=sa.text("gen_random_uuid()")),
        sa.Column("user_id", sa.UUID(), nullable=False),
        sa.Column("insight_id", sa.UUID(), nullable=False),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("tags", postgresql.ARRAY(sa.String(50)), nullable=True),
        sa.Column("status", sa.String(length=20), nullable=False, server_default="saved"),
        sa.Column("claimed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("saved_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("shared_count", sa.Integer(), nullable=False, server_default="0"),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["insight_id"], ["insights.id"], ondelete="CASCADE"),
        sa.UniqueConstraint("user_id", "insight_id", name="uq_user_insight"),
    )

    op.create_index("idx_saved_insights_user_saved", "saved_insights", ["user_id", "saved_at"])
    op.create_index("idx_saved_insights_user_status", "saved_insights", ["user_id", "status"])
    op.create_index("idx_saved_insights_insight", "saved_insights", ["insight_id"])

    # ============================================
    # 3. USER_RATINGS TABLE
    # ============================================
    op.create_table(
        "user_ratings",
        sa.Column("id", sa.UUID(), nullable=False, server_default=sa.text("gen_random_uuid()")),
        sa.Column("user_id", sa.UUID(), nullable=False),
        sa.Column("insight_id", sa.UUID(), nullable=False),
        sa.Column("rating", sa.Integer(), nullable=False),
        sa.Column("feedback", sa.Text(), nullable=True),
        sa.Column("rated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["insight_id"], ["insights.id"], ondelete="CASCADE"),
        sa.UniqueConstraint("user_id", "insight_id", name="uq_user_insight_rating"),
        sa.CheckConstraint("rating >= 1 AND rating <= 5", name="ck_rating_range"),
    )

    op.create_index("idx_user_ratings_user", "user_ratings", ["user_id"])
    op.create_index("idx_user_ratings_insight", "user_ratings", ["insight_id"])
    op.create_index("idx_user_ratings_rated", "user_ratings", ["rated_at"])

    # ============================================
    # 4. ADMIN_USERS TABLE
    # ============================================
    op.create_table(
        "admin_users",
        sa.Column("id", sa.UUID(), nullable=False, server_default=sa.text("gen_random_uuid()")),
        sa.Column("user_id", sa.UUID(), nullable=False),
        sa.Column("role", sa.String(length=20), nullable=False),
        sa.Column("permissions", postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default="{}"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.UniqueConstraint("user_id", name="uq_admin_user"),
    )

    op.create_index("idx_admin_users_user", "admin_users", ["user_id"])
    op.create_index("idx_admin_users_role", "admin_users", ["role"])

    # ============================================
    # 5. RLS POLICIES (Supabase)
    # ============================================
    # Note: These are raw SQL for Supabase RLS. They require the Supabase
    # auth.uid() function to work. In local PostgreSQL (without Supabase),
    # these policies won't be created but tables will still be usable.

    # RLS policies - only execute on Supabase (where auth schema exists)
    # Using DO block to conditionally execute only if auth schema is available
    op.execute("""
        DO $$
        BEGIN
            -- Check if auth schema exists (Supabase)
            IF EXISTS (SELECT 1 FROM information_schema.schemata WHERE schema_name = 'auth') THEN
                -- Enable RLS on tables
                ALTER TABLE users ENABLE ROW LEVEL SECURITY;
                ALTER TABLE saved_insights ENABLE ROW LEVEL SECURITY;
                ALTER TABLE user_ratings ENABLE ROW LEVEL SECURITY;
                ALTER TABLE admin_users ENABLE ROW LEVEL SECURITY;

                -- Users table RLS
                CREATE POLICY "Users can view own profile"
                ON users FOR SELECT
                USING (supabase_user_id = auth.uid()::text);

                CREATE POLICY "Users can update own profile"
                ON users FOR UPDATE
                USING (supabase_user_id = auth.uid()::text)
                WITH CHECK (supabase_user_id = auth.uid()::text);

                -- Saved insights RLS
                CREATE POLICY "Users can view own saved insights"
                ON saved_insights FOR SELECT
                USING (user_id IN (SELECT id FROM users WHERE supabase_user_id = auth.uid()::text));

                CREATE POLICY "Users can insert own saved insights"
                ON saved_insights FOR INSERT
                WITH CHECK (user_id IN (SELECT id FROM users WHERE supabase_user_id = auth.uid()::text));

                CREATE POLICY "Users can update own saved insights"
                ON saved_insights FOR UPDATE
                USING (user_id IN (SELECT id FROM users WHERE supabase_user_id = auth.uid()::text))
                WITH CHECK (user_id IN (SELECT id FROM users WHERE supabase_user_id = auth.uid()::text));

                CREATE POLICY "Users can delete own saved insights"
                ON saved_insights FOR DELETE
                USING (user_id IN (SELECT id FROM users WHERE supabase_user_id = auth.uid()::text));

                -- User ratings RLS
                CREATE POLICY "Users can view own ratings"
                ON user_ratings FOR SELECT
                USING (user_id IN (SELECT id FROM users WHERE supabase_user_id = auth.uid()::text));

                CREATE POLICY "Users can insert own ratings"
                ON user_ratings FOR INSERT
                WITH CHECK (user_id IN (SELECT id FROM users WHERE supabase_user_id = auth.uid()::text));

                CREATE POLICY "Users can update own ratings"
                ON user_ratings FOR UPDATE
                USING (user_id IN (SELECT id FROM users WHERE supabase_user_id = auth.uid()::text))
                WITH CHECK (user_id IN (SELECT id FROM users WHERE supabase_user_id = auth.uid()::text));

                CREATE POLICY "Users can delete own ratings"
                ON user_ratings FOR DELETE
                USING (user_id IN (SELECT id FROM users WHERE supabase_user_id = auth.uid()::text));

                -- Admin users RLS (admins only)
                CREATE POLICY "Only admins can view admin_users"
                ON admin_users FOR SELECT
                USING (
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
    """Remove Phase 4.1 tables and RLS policies."""

    # Drop RLS policies (ignore errors if policies don't exist)
    policies = [
        ("users", "Users can view own profile"),
        ("users", "Users can update own profile"),
        ("saved_insights", "Users can view own saved insights"),
        ("saved_insights", "Users can insert own saved insights"),
        ("saved_insights", "Users can update own saved insights"),
        ("saved_insights", "Users can delete own saved insights"),
        ("user_ratings", "Users can view own ratings"),
        ("user_ratings", "Users can insert own ratings"),
        ("user_ratings", "Users can update own ratings"),
        ("user_ratings", "Users can delete own ratings"),
        ("admin_users", "Only admins can view admin_users"),
    ]

    for table, policy_name in policies:
        op.execute(f'DROP POLICY IF EXISTS "{policy_name}" ON {table};')

    # Disable RLS
    op.execute("ALTER TABLE admin_users DISABLE ROW LEVEL SECURITY;")
    op.execute("ALTER TABLE user_ratings DISABLE ROW LEVEL SECURITY;")
    op.execute("ALTER TABLE saved_insights DISABLE ROW LEVEL SECURITY;")
    op.execute("ALTER TABLE users DISABLE ROW LEVEL SECURITY;")

    # Drop tables in reverse dependency order
    op.drop_table("admin_users")
    op.drop_table("user_ratings")
    op.drop_table("saved_insights")
    op.drop_table("users")
