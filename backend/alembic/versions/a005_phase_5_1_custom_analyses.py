"""Phase 5.1: Custom analyses table for AI Research Agent

Revision ID: a005_phase_5_1
Revises: a004_phase_4_4
Create Date: 2026-01-25 16:00:00.000000

Creates:
- custom_analyses table (40-step research analysis storage)

RLS Policies (Supabase):
- Users can view their own analyses
- Users can create their own analyses
- Admins can view all analyses

See architecture.md "Research Agent Architecture" for specification.
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "a005_phase_5_1"
down_revision: Union[str, Sequence[str], None] = "a004_phase_4_4"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create Phase 5.1 custom_analyses table."""

    # ============================================
    # 1. CUSTOM_ANALYSES TABLE
    # ============================================
    op.create_table(
        "custom_analyses",
        sa.Column(
            "id",
            sa.UUID(),
            nullable=False,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column("user_id", sa.UUID(), nullable=False),
        # User Input
        sa.Column("idea_description", sa.Text(), nullable=False),
        sa.Column("target_market", sa.Text(), nullable=False),
        sa.Column("budget_range", sa.String(length=20), nullable=False, server_default="unknown"),
        # Status
        sa.Column("status", sa.String(length=20), nullable=False, server_default="pending"),
        sa.Column("progress_percent", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("current_step", sa.String(length=100), nullable=True),
        # Analysis Results (JSONB)
        sa.Column(
            "market_analysis",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
            server_default="{}",
        ),
        sa.Column(
            "competitor_landscape",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
            server_default="[]",
        ),
        sa.Column(
            "value_equation",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
            server_default="{}",
        ),
        sa.Column(
            "market_matrix",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
            server_default="{}",
        ),
        sa.Column(
            "acp_framework",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
            server_default="{}",
        ),
        sa.Column(
            "validation_signals",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
            server_default="[]",
        ),
        sa.Column(
            "execution_roadmap",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
            server_default="[]",
        ),
        sa.Column(
            "risk_assessment",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
            server_default="{}",
        ),
        # Summary Scores
        sa.Column("opportunity_score", sa.Numeric(4, 2), nullable=True),
        sa.Column("market_fit_score", sa.Numeric(4, 2), nullable=True),
        sa.Column("execution_readiness", sa.Numeric(4, 2), nullable=True),
        # Metadata
        sa.Column("tokens_used", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("analysis_cost_usd", sa.Numeric(6, 4), nullable=False, server_default="0"),
        sa.Column("error_message", sa.Text(), nullable=True),
        # Timestamps
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        # Constraints
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["users.id"],
            ondelete="CASCADE",
        ),
    )

    # ============================================
    # 2. INDEXES
    # ============================================
    op.create_index("idx_analyses_user", "custom_analyses", ["user_id"])
    op.create_index("idx_analyses_status", "custom_analyses", ["status"])
    op.create_index(
        "idx_analyses_created",
        "custom_analyses",
        [sa.text("created_at DESC")],
    )
    op.create_index(
        "idx_analyses_user_status",
        "custom_analyses",
        ["user_id", "status"],
    )

    # ============================================
    # 3. CHECK CONSTRAINTS
    # ============================================

    # Status must be valid
    op.execute("""
        ALTER TABLE custom_analyses
        ADD CONSTRAINT chk_analysis_status
        CHECK (status IN ('pending', 'processing', 'completed', 'failed'));
    """)

    # Budget range must be valid
    op.execute("""
        ALTER TABLE custom_analyses
        ADD CONSTRAINT chk_budget_range
        CHECK (budget_range IN ('bootstrap', '10k-50k', '50k-200k', '200k+', 'unknown'));
    """)

    # Progress must be 0-100
    op.execute("""
        ALTER TABLE custom_analyses
        ADD CONSTRAINT chk_progress_range
        CHECK (progress_percent >= 0 AND progress_percent <= 100);
    """)

    # Score ranges (0-1)
    op.execute("""
        ALTER TABLE custom_analyses
        ADD CONSTRAINT chk_opportunity_score
        CHECK (opportunity_score IS NULL OR (opportunity_score >= 0 AND opportunity_score <= 1));
    """)

    op.execute("""
        ALTER TABLE custom_analyses
        ADD CONSTRAINT chk_market_fit_score
        CHECK (market_fit_score IS NULL OR (market_fit_score >= 0 AND market_fit_score <= 1));
    """)

    op.execute("""
        ALTER TABLE custom_analyses
        ADD CONSTRAINT chk_execution_readiness
        CHECK (execution_readiness IS NULL OR (execution_readiness >= 0 AND execution_readiness <= 1));
    """)

    # Idea description minimum length
    op.execute("""
        ALTER TABLE custom_analyses
        ADD CONSTRAINT chk_idea_min_length
        CHECK (length(idea_description) >= 50);
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
                ALTER TABLE custom_analyses ENABLE ROW LEVEL SECURITY;

                -- Users can view their own analyses
                CREATE POLICY "Users can view own analyses"
                ON custom_analyses FOR SELECT
                USING (
                    user_id IN (
                        SELECT id FROM users
                        WHERE supabase_user_id = auth.uid()::text
                    )
                );

                -- Users can create their own analyses
                CREATE POLICY "Users can create own analyses"
                ON custom_analyses FOR INSERT
                WITH CHECK (
                    user_id IN (
                        SELECT id FROM users
                        WHERE supabase_user_id = auth.uid()::text
                    )
                );

                -- Admins can view all analyses
                CREATE POLICY "Admins can view all analyses"
                ON custom_analyses FOR SELECT
                USING (
                    EXISTS (
                        SELECT 1 FROM admin_users au
                        JOIN users u ON au.user_id = u.id
                        WHERE u.supabase_user_id = auth.uid()::text
                    )
                );

                -- Admins can update all analyses
                CREATE POLICY "Admins can update all analyses"
                ON custom_analyses FOR UPDATE
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
    """Remove Phase 5.1 custom_analyses table."""

    # Drop RLS policies
    policies = [
        "Users can view own analyses",
        "Users can create own analyses",
        "Admins can view all analyses",
        "Admins can update all analyses",
    ]

    for policy_name in policies:
        op.execute(f'DROP POLICY IF EXISTS "{policy_name}" ON custom_analyses;')

    # Disable RLS
    op.execute("ALTER TABLE custom_analyses DISABLE ROW LEVEL SECURITY;")

    # Drop check constraints
    constraints = [
        "chk_analysis_status",
        "chk_budget_range",
        "chk_progress_range",
        "chk_opportunity_score",
        "chk_market_fit_score",
        "chk_execution_readiness",
        "chk_idea_min_length",
    ]

    for constraint in constraints:
        op.execute(f"ALTER TABLE custom_analyses DROP CONSTRAINT IF EXISTS {constraint};")

    # Drop indexes
    op.drop_index("idx_analyses_user_status", table_name="custom_analyses")
    op.drop_index("idx_analyses_created", table_name="custom_analyses")
    op.drop_index("idx_analyses_status", table_name="custom_analyses")
    op.drop_index("idx_analyses_user", table_name="custom_analyses")

    # Drop table
    op.drop_table("custom_analyses")
