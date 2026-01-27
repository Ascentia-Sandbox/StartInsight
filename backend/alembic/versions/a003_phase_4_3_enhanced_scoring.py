"""Phase 4.3: Enhanced 8-dimension scoring for insights (IdeaBrowser Parity)

Revision ID: a003_phase_4_3
Revises: a002_phase_4_2
Create Date: 2026-01-25 14:00:00.000000

Adds to insights table:
- title: Optional display title
- 8 dimension scores (opportunity, problem, feasibility, why_now, revenue_potential,
  execution_difficulty, go_to_market, founder_fit)
- Advanced frameworks (value_ladder, market_gap_analysis, why_now_analysis,
  proof_signals, execution_plan)

See architecture.md "Enhanced Scoring Architecture" for full specification.
"""

from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "a003_phase_4_3"
down_revision: str | Sequence[str] | None = "a002_phase_4_2"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Add enhanced 8-dimension scoring columns to insights table."""

    # ============================================
    # 1. BASIC INSIGHT ENHANCEMENTS
    # ============================================

    # Optional display title
    op.add_column(
        "insights",
        sa.Column("title", sa.String(length=200), nullable=True),
    )

    # ============================================
    # 2. CORE OPPORTUNITY METRICS (1-10 scale)
    # ============================================

    op.add_column(
        "insights",
        sa.Column("opportunity_score", sa.Integer(), nullable=True),
    )

    op.add_column(
        "insights",
        sa.Column("problem_score", sa.Integer(), nullable=True),
    )

    op.add_column(
        "insights",
        sa.Column("feasibility_score", sa.Integer(), nullable=True),
    )

    op.add_column(
        "insights",
        sa.Column("why_now_score", sa.Integer(), nullable=True),
    )

    # ============================================
    # 3. BUSINESS FIT METRICS
    # ============================================

    op.add_column(
        "insights",
        sa.Column("revenue_potential", sa.String(length=4), nullable=True),
    )

    op.add_column(
        "insights",
        sa.Column("execution_difficulty", sa.Integer(), nullable=True),
    )

    op.add_column(
        "insights",
        sa.Column("go_to_market_score", sa.Integer(), nullable=True),
    )

    op.add_column(
        "insights",
        sa.Column("founder_fit_score", sa.Integer(), nullable=True),
    )

    # ============================================
    # 4. ADVANCED FRAMEWORKS (IdeaBrowser Parity)
    # ============================================

    # Value Ladder: 4-tier pricing model (JSONB array)
    op.add_column(
        "insights",
        sa.Column(
            "value_ladder",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=True,
        ),
    )

    # Market Gap Analysis: 200-500 word competitor gap analysis
    op.add_column(
        "insights",
        sa.Column("market_gap_analysis", sa.Text(), nullable=True),
    )

    # Why Now Analysis: 200-500 word timing analysis
    op.add_column(
        "insights",
        sa.Column("why_now_analysis", sa.Text(), nullable=True),
    )

    # Proof Signals: 3-5 validation evidence pieces (JSONB array)
    op.add_column(
        "insights",
        sa.Column(
            "proof_signals",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=True,
        ),
    )

    # Execution Plan: 5-7 actionable launch steps (JSONB array)
    op.add_column(
        "insights",
        sa.Column(
            "execution_plan",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=True,
        ),
    )

    # ============================================
    # 5. CREATE INDEXES FOR FILTERING & SORTING
    # ============================================

    op.create_index("idx_insights_opportunity", "insights", ["opportunity_score"])
    op.create_index("idx_insights_problem", "insights", ["problem_score"])
    op.create_index("idx_insights_feasibility", "insights", ["feasibility_score"])
    op.create_index("idx_insights_why_now", "insights", ["why_now_score"])
    op.create_index("idx_insights_revenue_potential", "insights", ["revenue_potential"])
    op.create_index("idx_insights_execution", "insights", ["execution_difficulty"])
    op.create_index("idx_insights_go_to_market", "insights", ["go_to_market_score"])
    op.create_index("idx_insights_founder_fit", "insights", ["founder_fit_score"])

    # Composite index for common filter combinations
    op.create_index(
        "idx_insights_enhanced_filter",
        "insights",
        ["opportunity_score", "feasibility_score", "revenue_potential"],
    )

    # ============================================
    # 6. ADD CHECK CONSTRAINTS FOR SCORE VALIDATION
    # ============================================

    # Opportunity score must be 1-10
    op.execute("""
        ALTER TABLE insights
        ADD CONSTRAINT chk_opportunity_score
        CHECK (opportunity_score IS NULL OR (opportunity_score >= 1 AND opportunity_score <= 10));
    """)

    # Problem score must be 1-10
    op.execute("""
        ALTER TABLE insights
        ADD CONSTRAINT chk_problem_score
        CHECK (problem_score IS NULL OR (problem_score >= 1 AND problem_score <= 10));
    """)

    # Feasibility score must be 1-10
    op.execute("""
        ALTER TABLE insights
        ADD CONSTRAINT chk_feasibility_score
        CHECK (feasibility_score IS NULL OR (feasibility_score >= 1 AND feasibility_score <= 10));
    """)

    # Why now score must be 1-10
    op.execute("""
        ALTER TABLE insights
        ADD CONSTRAINT chk_why_now_score
        CHECK (why_now_score IS NULL OR (why_now_score >= 1 AND why_now_score <= 10));
    """)

    # Revenue potential must be $, $$, $$$, or $$$$
    op.execute("""
        ALTER TABLE insights
        ADD CONSTRAINT chk_revenue_potential
        CHECK (revenue_potential IS NULL OR revenue_potential IN ('$', '$$', '$$$', '$$$$'));
    """)

    # Execution difficulty must be 1-10
    op.execute("""
        ALTER TABLE insights
        ADD CONSTRAINT chk_execution_difficulty
        CHECK (execution_difficulty IS NULL OR (execution_difficulty >= 1 AND execution_difficulty <= 10));
    """)

    # Go-to-market score must be 1-10
    op.execute("""
        ALTER TABLE insights
        ADD CONSTRAINT chk_go_to_market_score
        CHECK (go_to_market_score IS NULL OR (go_to_market_score >= 1 AND go_to_market_score <= 10));
    """)

    # Founder fit score must be 1-10
    op.execute("""
        ALTER TABLE insights
        ADD CONSTRAINT chk_founder_fit_score
        CHECK (founder_fit_score IS NULL OR (founder_fit_score >= 1 AND founder_fit_score <= 10));
    """)


def downgrade() -> None:
    """Remove enhanced 8-dimension scoring columns from insights table."""

    # ============================================
    # 1. DROP CHECK CONSTRAINTS
    # ============================================
    constraints = [
        "chk_opportunity_score",
        "chk_problem_score",
        "chk_feasibility_score",
        "chk_why_now_score",
        "chk_revenue_potential",
        "chk_execution_difficulty",
        "chk_go_to_market_score",
        "chk_founder_fit_score",
    ]

    for constraint in constraints:
        op.execute(f"ALTER TABLE insights DROP CONSTRAINT IF EXISTS {constraint};")

    # ============================================
    # 2. DROP INDEXES
    # ============================================
    op.drop_index("idx_insights_enhanced_filter", table_name="insights")
    op.drop_index("idx_insights_founder_fit", table_name="insights")
    op.drop_index("idx_insights_go_to_market", table_name="insights")
    op.drop_index("idx_insights_execution", table_name="insights")
    op.drop_index("idx_insights_revenue_potential", table_name="insights")
    op.drop_index("idx_insights_why_now", table_name="insights")
    op.drop_index("idx_insights_feasibility", table_name="insights")
    op.drop_index("idx_insights_problem", table_name="insights")
    op.drop_index("idx_insights_opportunity", table_name="insights")

    # ============================================
    # 3. DROP ADVANCED FRAMEWORK COLUMNS
    # ============================================
    op.drop_column("insights", "execution_plan")
    op.drop_column("insights", "proof_signals")
    op.drop_column("insights", "why_now_analysis")
    op.drop_column("insights", "market_gap_analysis")
    op.drop_column("insights", "value_ladder")

    # ============================================
    # 4. DROP BUSINESS FIT METRICS
    # ============================================
    op.drop_column("insights", "founder_fit_score")
    op.drop_column("insights", "go_to_market_score")
    op.drop_column("insights", "execution_difficulty")
    op.drop_column("insights", "revenue_potential")

    # ============================================
    # 5. DROP CORE OPPORTUNITY METRICS
    # ============================================
    op.drop_column("insights", "why_now_score")
    op.drop_column("insights", "feasibility_score")
    op.drop_column("insights", "problem_score")
    op.drop_column("insights", "opportunity_score")

    # ============================================
    # 6. DROP BASIC ENHANCEMENTS
    # ============================================
    op.drop_column("insights", "title")
