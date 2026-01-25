"""Phase 4.4: Insight interactions table for analytics tracking

Revision ID: a004_phase_4_4
Revises: a003_phase_4_3
Create Date: 2026-01-25 15:00:00.000000

Creates:
- insight_interactions table (view, interested, claim, share, export tracking)

RLS Policies (Supabase):
- Users can view their own interactions
- Users can create their own interactions

See architecture.md Section 5 for schema specification.
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "a004_phase_4_4"
down_revision: Union[str, Sequence[str], None] = "a003_phase_4_3"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create Phase 4.4 insight_interactions table."""

    # ============================================
    # 1. INSIGHT_INTERACTIONS TABLE
    # ============================================
    op.create_table(
        "insight_interactions",
        sa.Column(
            "id",
            sa.UUID(),
            nullable=False,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column("user_id", sa.UUID(), nullable=False),
        sa.Column("insight_id", sa.UUID(), nullable=False),
        sa.Column("interaction_type", sa.String(length=20), nullable=False),
        sa.Column(
            "extra_metadata",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
            server_default="{}",
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["users.id"],
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["insight_id"],
            ["insights.id"],
            ondelete="CASCADE",
        ),
    )

    # ============================================
    # 2. INDEXES FOR QUERY PERFORMANCE
    # ============================================
    op.create_index("idx_interactions_user", "insight_interactions", ["user_id"])
    op.create_index("idx_interactions_insight", "insight_interactions", ["insight_id"])
    op.create_index(
        "idx_interactions_type", "insight_interactions", ["interaction_type"]
    )
    op.create_index(
        "idx_interactions_created",
        "insight_interactions",
        [sa.text("created_at DESC")],
    )

    # Composite index for user-insight queries
    op.create_index(
        "idx_interactions_user_insight",
        "insight_interactions",
        ["user_id", "insight_id"],
    )

    # Composite index for type + time analytics
    op.create_index(
        "idx_interactions_type_created",
        "insight_interactions",
        ["interaction_type", "created_at"],
    )

    # ============================================
    # 3. CHECK CONSTRAINT FOR INTERACTION TYPE
    # ============================================
    op.execute("""
        ALTER TABLE insight_interactions
        ADD CONSTRAINT chk_interaction_type
        CHECK (interaction_type IN ('view', 'interested', 'claim', 'share', 'export'));
    """)

    # ============================================
    # 4. RLS POLICIES (Supabase)
    # ============================================
    # RLS policies - only execute on Supabase (where auth schema exists)
    op.execute("""
        DO $$
        BEGIN
            -- Check if auth schema exists (Supabase)
            IF EXISTS (SELECT 1 FROM information_schema.schemata WHERE schema_name = 'auth') THEN
                ALTER TABLE insight_interactions ENABLE ROW LEVEL SECURITY;

                -- Users can view their own interactions
                CREATE POLICY "Users can view own interactions"
                ON insight_interactions FOR SELECT
                USING (
                    user_id IN (
                        SELECT id FROM users
                        WHERE supabase_user_id = auth.uid()::text
                    )
                );

                -- Users can create their own interactions
                CREATE POLICY "Users can create own interactions"
                ON insight_interactions FOR INSERT
                WITH CHECK (
                    user_id IN (
                        SELECT id FROM users
                        WHERE supabase_user_id = auth.uid()::text
                    )
                );

                -- Admins can view all interactions (for analytics)
                CREATE POLICY "Admins can view all interactions"
                ON insight_interactions FOR SELECT
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
    """Remove Phase 4.4 insight_interactions table."""

    # Drop RLS policies
    policies = [
        "Users can view own interactions",
        "Users can create own interactions",
        "Admins can view all interactions",
    ]

    for policy_name in policies:
        op.execute(
            f'DROP POLICY IF EXISTS "{policy_name}" ON insight_interactions;'
        )

    # Disable RLS
    op.execute("ALTER TABLE insight_interactions DISABLE ROW LEVEL SECURITY;")

    # Drop check constraint
    op.execute(
        "ALTER TABLE insight_interactions DROP CONSTRAINT IF EXISTS chk_interaction_type;"
    )

    # Drop indexes
    op.drop_index("idx_interactions_type_created", table_name="insight_interactions")
    op.drop_index("idx_interactions_user_insight", table_name="insight_interactions")
    op.drop_index("idx_interactions_created", table_name="insight_interactions")
    op.drop_index("idx_interactions_type", table_name="insight_interactions")
    op.drop_index("idx_interactions_insight", table_name="insight_interactions")
    op.drop_index("idx_interactions_user", table_name="insight_interactions")

    # Drop table
    op.drop_table("insight_interactions")
