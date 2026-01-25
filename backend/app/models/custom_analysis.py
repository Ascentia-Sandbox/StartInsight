"""CustomAnalysis model - Phase 5.1 AI Research Agent.

Stores user-requested deep analyses using the 40-step research process.
Includes market sizing, competitor landscape, value equation, and execution roadmap.

See architecture.md Section "Research Agent Architecture" for specification.
"""

from datetime import datetime
from uuid import UUID, uuid4

from sqlalchemy import DateTime, ForeignKey, Numeric, String, Text, func
from sqlalchemy.dialects.postgresql import JSONB, UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class CustomAnalysis(Base):
    """
    CustomAnalysis model - Stores deep research analyses requested by users.

    Analysis includes 40-step research process:
    - Market analysis (TAM/SAM/SOM, growth rate, maturity)
    - Competitor landscape (top 10 with scores)
    - Value equation (Hormozi framework)
    - Market matrix (2x2 positioning)
    - A-C-P framework (Awareness, Consideration, Purchase)
    - Validation signals (Reddit, Product Hunt, trends)
    - Execution roadmap (phases with milestones)
    - Risk assessment (technical, market, team)
    """

    __tablename__ = "custom_analyses"

    # Primary key
    id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        primary_key=True,
        default=uuid4,
        doc="Unique identifier for this analysis",
    )

    # Foreign key to user
    user_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("users.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
        doc="User who requested this analysis (RESTRICT prevents deletion if analyses exist)",
    )

    # ============================================
    # User Input
    # ============================================

    idea_description: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        doc="User's startup idea description (50-2000 chars)",
    )

    target_market: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        doc="Target market description",
    )

    budget_range: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="unknown",
        doc="Budget range: bootstrap, 10k-50k, 50k-200k, 200k+",
    )

    # ============================================
    # Analysis Status
    # ============================================

    status: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="pending",
        index=True,
        doc="Status: pending, processing, completed, failed",
    )

    progress_percent: Mapped[int] = mapped_column(
        nullable=False,
        default=0,
        doc="Analysis progress (0-100)",
    )

    current_step: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
        doc="Current step description for UI progress",
    )

    # ============================================
    # Analysis Results (40-step research)
    # ============================================

    # Market Analysis
    market_analysis: Mapped[dict] = mapped_column(
        JSONB,
        nullable=False,
        default=dict,
        doc="Market size, growth rate, TAM/SAM/SOM",
    )

    # Competitor Landscape
    competitor_landscape: Mapped[dict] = mapped_column(
        JSONB,
        nullable=False,
        default=list,
        doc="Top 10 competitors with scores",
    )

    # Value Equation (Hormozi framework)
    value_equation: Mapped[dict] = mapped_column(
        JSONB,
        nullable=False,
        default=dict,
        doc="Dream Outcome, Perceived Likelihood, Time Delay, Effort/Sacrifice",
    )

    # Market Matrix (2x2 positioning)
    market_matrix: Mapped[dict] = mapped_column(
        JSONB,
        nullable=False,
        default=dict,
        doc="Position on Demand vs Difficulty matrix",
    )

    # A-C-P Framework
    acp_framework: Mapped[dict] = mapped_column(
        JSONB,
        nullable=False,
        default=dict,
        doc="Awareness, Consideration, Purchase scoring",
    )

    # Validation Signals
    validation_signals: Mapped[dict] = mapped_column(
        JSONB,
        nullable=False,
        default=list,
        doc="Reddit threads, Product Hunt launches, trends",
    )

    # Execution Roadmap
    execution_roadmap: Mapped[dict] = mapped_column(
        JSONB,
        nullable=False,
        default=list,
        doc="Phases with milestones and timelines",
    )

    # Risk Assessment
    risk_assessment: Mapped[dict] = mapped_column(
        JSONB,
        nullable=False,
        default=dict,
        doc="Technical, market, and team risks",
    )

    # ============================================
    # Summary Scores
    # ============================================

    opportunity_score: Mapped[float | None] = mapped_column(
        Numeric(4, 2),
        nullable=True,
        doc="Overall opportunity score (0-1)",
    )

    market_fit_score: Mapped[float | None] = mapped_column(
        Numeric(4, 2),
        nullable=True,
        doc="Product-market fit score (0-1)",
    )

    execution_readiness: Mapped[float | None] = mapped_column(
        Numeric(4, 2),
        nullable=True,
        doc="Execution readiness score (0-1)",
    )

    # ============================================
    # Metadata
    # ============================================

    tokens_used: Mapped[int] = mapped_column(
        nullable=False,
        default=0,
        doc="Total tokens used for analysis",
    )

    analysis_cost_usd: Mapped[float] = mapped_column(
        Numeric(6, 4),
        nullable=False,
        default=0.0,
        doc="Analysis cost in USD",
    )

    error_message: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
        doc="Error message if analysis failed",
    )

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
        index=True,
        doc="When analysis was requested",
    )

    started_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        doc="When analysis processing started",
    )

    completed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        doc="When analysis completed",
    )

    # Relationships
    user: Mapped["User"] = relationship(
        "User",
        back_populates="custom_analyses",
        lazy="selectin",
        doc="User who requested this analysis",
    )

    def __repr__(self) -> str:
        """String representation of CustomAnalysis."""
        return (
            f"<CustomAnalysis(id={self.id}, "
            f"status={self.status}, "
            f"score={self.opportunity_score})>"
        )

    def __str__(self) -> str:
        """Human-readable string representation."""
        return f"Analysis: {self.idea_description[:50]}..."
