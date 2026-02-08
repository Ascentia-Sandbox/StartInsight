"""Phase 9.6: Gamification & Engagement

Create tables for:
- achievements: Achievement definitions
- user_achievements: User earned achievements
- user_points: User points and levels
- user_credits: Credit balance for premium features

Revision ID: b020
Revises: b019
Create Date: 2026-02-04
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID, JSONB

revision = "b020"
down_revision = "b019"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Achievements definition table
    op.create_table(
        "achievements",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("name", sa.String(100), unique=True, nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("badge_icon", sa.String(500), nullable=True),
        sa.Column("points", sa.Integer(), nullable=False),
        sa.Column("criteria", JSONB, nullable=False),  # {"type": "count", "metric": "ideas_saved", "threshold": 10}
        sa.Column("category", sa.String(50), nullable=True),  # explorer, curator, networker, etc.
        sa.Column("is_active", sa.Boolean(), server_default=sa.text("true"), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("idx_achievements_category", "achievements", ["category"])

    # User achievements table
    op.create_table(
        "user_achievements",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("user_id", UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("achievement_id", UUID(as_uuid=True), sa.ForeignKey("achievements.id", ondelete="CASCADE"), nullable=False),
        sa.Column("earned_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_unique_constraint("uq_user_achievements", "user_achievements", ["user_id", "achievement_id"])
    op.create_index("idx_user_achievements_user", "user_achievements", ["user_id"])

    # User points table
    op.create_table(
        "user_points",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("user_id", UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), unique=True, nullable=False),
        sa.Column("total_points", sa.Integer(), server_default="0", nullable=False),
        sa.Column("level", sa.Integer(), server_default="1", nullable=False),
        sa.Column("achievements_count", sa.Integer(), server_default="0", nullable=False),
        sa.Column("current_streak", sa.Integer(), server_default="0", nullable=False),
        sa.Column("longest_streak", sa.Integer(), server_default="0", nullable=False),
        sa.Column("last_activity_date", sa.Date(), nullable=True),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )

    # User credits table (for premium features)
    op.create_table(
        "user_credits",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("user_id", UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), unique=True, nullable=False),
        sa.Column("balance", sa.Integer(), server_default="0", nullable=False),
        sa.Column("lifetime_earned", sa.Integer(), server_default="0", nullable=False),
        sa.Column("lifetime_spent", sa.Integer(), server_default="0", nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )

    # Credit transactions table
    op.create_table(
        "credit_transactions",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("user_id", UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("amount", sa.Integer(), nullable=False),  # positive = earn, negative = spend
        sa.Column("transaction_type", sa.String(50), nullable=False),  # earn_daily_login, spend_chat, etc.
        sa.Column("description", sa.String(255), nullable=True),
        sa.Column("reference_id", UUID(as_uuid=True), nullable=True),  # linked entity ID
        sa.Column("reference_type", sa.String(50), nullable=True),  # insight, chat, research, etc.
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("idx_credit_transactions_user", "credit_transactions", ["user_id", sa.text("created_at DESC")])

    # Enable RLS
    op.execute("ALTER TABLE achievements ENABLE ROW LEVEL SECURITY")
    op.execute("ALTER TABLE user_achievements ENABLE ROW LEVEL SECURITY")
    op.execute("ALTER TABLE user_points ENABLE ROW LEVEL SECURITY")
    op.execute("ALTER TABLE user_credits ENABLE ROW LEVEL SECURITY")
    op.execute("ALTER TABLE credit_transactions ENABLE ROW LEVEL SECURITY")

    # Achievements: everyone can read
    op.execute("""
        CREATE POLICY read_achievements_policy ON achievements
        FOR SELECT USING (true)
    """)
    op.execute("""
        CREATE POLICY admin_achievements_policy ON achievements
        FOR ALL USING (
            EXISTS (SELECT 1 FROM admin_users WHERE admin_users.user_id = auth.uid())
        )
    """)

    # User achievements: user can read own, others can see public
    op.execute("""
        CREATE POLICY user_achievements_policy ON user_achievements
        FOR ALL USING (user_id = auth.uid())
    """)
    op.execute("""
        CREATE POLICY read_user_achievements_policy ON user_achievements
        FOR SELECT USING (true)
    """)

    # User points: user can read own, leaderboard visible
    op.execute("""
        CREATE POLICY user_points_policy ON user_points
        FOR ALL USING (user_id = auth.uid())
    """)
    op.execute("""
        CREATE POLICY read_user_points_policy ON user_points
        FOR SELECT USING (true)
    """)

    # User credits: user can read own only
    op.execute("""
        CREATE POLICY user_credits_policy ON user_credits
        FOR ALL USING (user_id = auth.uid())
    """)

    # Credit transactions: user can read own only
    op.execute("""
        CREATE POLICY credit_transactions_policy ON credit_transactions
        FOR SELECT USING (user_id = auth.uid())
    """)
    op.execute("""
        CREATE POLICY admin_credit_transactions_policy ON credit_transactions
        FOR ALL USING (
            EXISTS (SELECT 1 FROM admin_users WHERE admin_users.user_id = auth.uid())
        )
    """)

    # Insert default achievements
    op.execute("""
        INSERT INTO achievements (name, description, badge_icon, points, criteria, category) VALUES
        ('First Steps', 'Save your first idea', '/badges/first-steps.svg', 10, '{"type": "count", "metric": "ideas_saved", "threshold": 1}', 'explorer'),
        ('Explorer', 'View 10 ideas', '/badges/explorer.svg', 25, '{"type": "count", "metric": "ideas_viewed", "threshold": 10}', 'explorer'),
        ('Curator', 'Save 10 ideas', '/badges/curator.svg', 50, '{"type": "count", "metric": "ideas_saved", "threshold": 10}', 'curator'),
        ('Analyst', 'Request your first research report', '/badges/analyst.svg', 100, '{"type": "count", "metric": "research_requested", "threshold": 1}', 'analyst'),
        ('Builder', 'Export an idea to a builder tool', '/badges/builder.svg', 75, '{"type": "count", "metric": "ideas_exported", "threshold": 1}', 'builder'),
        ('Networker', 'Connect with 5 founders', '/badges/networker.svg', 100, '{"type": "count", "metric": "connections_made", "threshold": 5}', 'social'),
        ('Validator', 'Vote on 20 ideas', '/badges/validator.svg', 50, '{"type": "count", "metric": "votes_cast", "threshold": 20}', 'community'),
        ('Contributor', 'Post 5 comments', '/badges/contributor.svg', 75, '{"type": "count", "metric": "comments_posted", "threshold": 5}', 'community'),
        ('Streak Master', 'Maintain a 7-day login streak', '/badges/streak-master.svg', 150, '{"type": "streak", "metric": "login_streak", "threshold": 7}', 'engagement'),
        ('Thought Leader', 'Get 10 upvotes on a comment', '/badges/thought-leader.svg', 200, '{"type": "max", "metric": "comment_upvotes", "threshold": 10}', 'community')
    """)


def downgrade() -> None:
    op.execute("DROP POLICY IF EXISTS admin_credit_transactions_policy ON credit_transactions")
    op.execute("DROP POLICY IF EXISTS credit_transactions_policy ON credit_transactions")
    op.execute("DROP POLICY IF EXISTS user_credits_policy ON user_credits")
    op.execute("DROP POLICY IF EXISTS read_user_points_policy ON user_points")
    op.execute("DROP POLICY IF EXISTS user_points_policy ON user_points")
    op.execute("DROP POLICY IF EXISTS read_user_achievements_policy ON user_achievements")
    op.execute("DROP POLICY IF EXISTS user_achievements_policy ON user_achievements")
    op.execute("DROP POLICY IF EXISTS admin_achievements_policy ON achievements")
    op.execute("DROP POLICY IF EXISTS read_achievements_policy ON achievements")
    op.drop_table("credit_transactions")
    op.drop_table("user_credits")
    op.drop_table("user_points")
    op.drop_table("user_achievements")
    op.drop_table("achievements")
