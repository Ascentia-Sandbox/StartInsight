"""Insight database model - AI-analyzed structured insights.

Phase 1-3: Basic insight analysis
Phase 4.3: Enhanced 8-dimension scoring (IdeaBrowser parity)
"""

from datetime import datetime
from uuid import UUID, uuid4

from sqlalchemy import DateTime, Float, ForeignKey, Integer, String, Text, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class Insight(Base):
    """
    Insight model - Stores AI-analyzed, structured insights from raw signals.

    An Insight represents the structured analysis of a RawSignal, containing:
    - Identified market problem
    - Proposed solution
    - Market size estimate
    - Relevance score (0.0 - 1.0)
    - Competitor analysis (up to 3 competitors)

    Phase 4.3 Enhanced Scoring (8 dimensions):
    - opportunity_score: Market size (1-10)
    - problem_score: Pain severity (1-10)
    - feasibility_score: Technical difficulty (1-10)
    - why_now_score: Market timing (1-10)
    - revenue_potential: $, $$, $$$, $$$$
    - execution_difficulty: Complexity (1-10)
    - go_to_market_score: Distribution ease (1-10)
    - founder_fit_score: Skill requirements (1-10)

    Advanced Frameworks:
    - value_ladder: 4-tier pricing model
    - market_gap_analysis: 200-500 word competitor gap analysis
    - why_now_analysis: 200-500 word timing analysis
    - proof_signals: 3-5 validation evidence pieces
    - execution_plan: 5-7 actionable launch steps
    """

    __tablename__ = "insights"

    # Primary key
    id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        primary_key=True,
        default=uuid4,
        doc="Unique identifier for this insight",
    )

    # Foreign key to source raw signal
    raw_signal_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("raw_signals.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        doc="Reference to the source raw signal",
    )

    # Core insight data
    problem_statement: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        doc="Identified market problem from the signal",
    )

    proposed_solution: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        doc="Suggested solution approach or opportunity",
    )

    market_size_estimate: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        doc="Market size: 'Small' (<$100M), 'Medium' ($100M-$1B), 'Large' (>$1B)",
    )

    relevance_score: Mapped[float] = mapped_column(
        Float,
        nullable=False,
        index=True,
        doc="Signal relevance (0.0=weak, 1.0=strong)",
    )

    # Competitor analysis (stored as JSON array of competitor objects)
    competitor_analysis: Mapped[dict] = mapped_column(
        JSONB,
        nullable=True,
        default=list,
        doc="List of up to 3 competitors with name, URL, description, market position",
    )

    # ============================================
    # Phase 4.3: Enhanced 8-Dimension Scoring
    # ============================================

    # Optional title for display
    title: Mapped[str | None] = mapped_column(
        String(200),
        nullable=True,
        doc="Optional display title for this insight",
    )

    # Core Opportunity Metrics (1-10 scale)
    opportunity_score: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
        index=True,
        doc="Market size: 1=tiny, 10=massive",
    )

    problem_score: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
        index=True,
        doc="Pain severity: 1=nice-to-have, 10=existential",
    )

    feasibility_score: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
        index=True,
        doc="Technical ease: 1=breakthrough needed, 10=weekend project",
    )

    why_now_score: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
        index=True,
        doc="Market timing: 1=too early/late, 10=perfect inflection",
    )

    # Business Fit Metrics
    revenue_potential: Mapped[str | None] = mapped_column(
        String(4),
        nullable=True,
        index=True,
        doc="$=low, $$=medium, $$$=high, $$$$=very high",
    )

    execution_difficulty: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
        index=True,
        doc="Complexity: 1=weekend, 10=multi-year enterprise",
    )

    go_to_market_score: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
        index=True,
        doc="Distribution: 1=enterprise sales, 10=viral PLG",
    )

    founder_fit_score: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
        index=True,
        doc="Skills: 1=PhD + 10 years, 10=anyone can learn",
    )

    # ============================================
    # Advanced Frameworks (IdeaBrowser Parity)
    # ============================================

    # Value Ladder: 4-tier pricing model
    value_ladder: Mapped[dict | None] = mapped_column(
        JSONB,
        nullable=True,
        doc="4-tier value ladder: lead_magnet, frontend, core, backend",
    )

    # Market Gap Analysis: 200-500 word competitor gap analysis
    market_gap_analysis: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
        doc="200-500 word analysis of competitor gaps",
    )

    # Why Now Analysis: 200-500 word timing analysis
    why_now_analysis: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
        doc="200-500 word analysis of market timing",
    )

    # Proof Signals: 3-5 validation evidence pieces
    proof_signals: Mapped[dict | None] = mapped_column(
        JSONB,
        nullable=True,
        doc="3-5 validation evidence pieces",
    )

    # Execution Plan: 5-7 actionable launch steps
    execution_plan: Mapped[dict | None] = mapped_column(
        JSONB,
        nullable=True,
        doc="5-7 actionable launch steps",
    )

    # ============================================
    # Phase 5+: Enhanced Visualizations
    # ============================================

    # Community Signals Chart: Array of platform engagement data
    community_signals_chart: Mapped[dict | None] = mapped_column(
        JSONB,
        nullable=True,
        default=list,
        doc="Community engagement visualization data (platform, score, members, engagement_rate)",
    )

    # Enhanced Scores: 8-dimension scoring breakdown
    enhanced_scores: Mapped[dict | None] = mapped_column(
        JSONB,
        nullable=True,
        default=list,
        doc="8-dimension scoring breakdown (dimension, value, label)",
    )

    # Trend Keywords: Search volume and growth data
    trend_keywords: Mapped[dict | None] = mapped_column(
        JSONB,
        nullable=True,
        default=list,
        doc="Trending keywords with search volume and growth percentage",
    )

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
        index=True,
        doc="When this insight was created",
    )

    # Relationships
    raw_signal: Mapped["RawSignal"] = relationship(
        "RawSignal",
        back_populates="insights",
        lazy="selectin",
        doc="The source raw signal for this insight",
    )

    interactions: Mapped[list["InsightInteraction"]] = relationship(
        "InsightInteraction",
        back_populates="insight",
        lazy="selectin",
        cascade="all, delete-orphan",
        doc="User interactions with this insight (Phase 4.4)",
    )

    # Phase 6.4: Team shares relationship
    team_shares: Mapped[list["SharedInsight"]] = relationship(
        "SharedInsight",
        back_populates="insight",
        lazy="selectin",
        cascade="all, delete-orphan",
        doc="Teams this insight is shared with (Phase 6.4)",
    )

    def __repr__(self) -> str:
        """String representation of Insight."""
        return (
            f"<Insight(id={self.id}, "
            f"problem='{self.problem_statement[:50]}...', "
            f"score={self.relevance_score})>"
        )

    def __str__(self) -> str:
        """Human-readable string representation."""
        return f"Insight: {self.problem_statement[:100]}"
