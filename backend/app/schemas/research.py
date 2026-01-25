"""Pydantic schemas for AI Research Agent - Phase 5.1.

Includes schemas for:
- Custom analysis requests
- Market analysis results
- Competitor profiles
- Value equation (Hormozi framework)
- Execution roadmaps

See architecture.md Section "Research Agent Architecture" for specification.
"""

from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, Field


# ============================================
# Analysis Input Schemas
# ============================================


class ResearchRequestCreate(BaseModel):
    """Schema for creating a custom analysis request."""

    idea_description: str = Field(
        min_length=50,
        max_length=2000,
        description="Detailed description of your startup idea",
    )
    target_market: str = Field(
        min_length=10,
        max_length=500,
        description="Target market description",
    )
    budget_range: Literal["bootstrap", "10k-50k", "50k-200k", "200k+", "unknown"] = Field(
        default="unknown",
        description="Initial budget range for the startup",
    )


# ============================================
# Analysis Result Components
# ============================================


class MarketAnalysis(BaseModel):
    """Market sizing and analysis."""

    tam: str = Field(description="Total Addressable Market (e.g., '$50B')")
    sam: str = Field(description="Serviceable Addressable Market (e.g., '$5B')")
    som: str = Field(description="Serviceable Obtainable Market (e.g., '$50M')")
    growth_rate: float = Field(description="Annual growth rate (e.g., 0.15 for 15%)")
    market_maturity: Literal["nascent", "growing", "mature", "declining"] = Field(
        description="Market lifecycle stage"
    )
    key_trends: list[str] = Field(
        default_factory=list,
        description="Top 3-5 market trends",
    )


class CompetitorProfile(BaseModel):
    """Individual competitor analysis."""

    name: str = Field(description="Competitor name")
    url: str = Field(description="Competitor website")
    funding: str = Field(description="Funding stage (e.g., '$5M Series A')")
    unique_value_prop: str = Field(description="Their unique value proposition")
    weakness: str = Field(description="Key weakness or gap")
    market_share_estimate: float = Field(
        ge=0, le=100, description="Estimated market share %"
    )
    threat_level: Literal["low", "medium", "high"] = Field(
        description="Competitive threat level"
    )


class ValueEquation(BaseModel):
    """Alex Hormozi's Value Equation framework."""

    dream_outcome_score: int = Field(
        ge=1, le=10, description="How desirable is the outcome? (1-10)"
    )
    perceived_likelihood_score: int = Field(
        ge=1, le=10, description="How likely does customer believe it will work? (1-10)"
    )
    time_delay_score: int = Field(
        ge=1, le=10, description="How fast do they get results? Lower is better (1-10)"
    )
    effort_sacrifice_score: int = Field(
        ge=1, le=10, description="How much effort required? Lower is better (1-10)"
    )
    value_score: float = Field(
        description="Calculated: (Dream * Likelihood) / (Time * Effort)"
    )
    analysis: str = Field(description="200-word value proposition analysis")


class MarketMatrix(BaseModel):
    """2x2 Market positioning matrix."""

    demand_score: int = Field(ge=1, le=10, description="Market demand (1-10)")
    difficulty_score: int = Field(ge=1, le=10, description="Execution difficulty (1-10)")
    quadrant: Literal["star", "cash_cow", "question_mark", "dog"] = Field(
        description="Matrix quadrant based on scores"
    )
    positioning_strategy: str = Field(description="Recommended positioning strategy")


class ACPFramework(BaseModel):
    """Awareness, Consideration, Purchase framework."""

    awareness_score: int = Field(ge=1, le=10, description="Target awareness level (1-10)")
    consideration_score: int = Field(ge=1, le=10, description="Consideration likelihood (1-10)")
    purchase_score: int = Field(ge=1, le=10, description="Purchase readiness (1-10)")
    funnel_bottleneck: str = Field(description="Primary funnel bottleneck")
    recommended_channels: list[str] = Field(description="Top 3 acquisition channels")


class ValidationSignal(BaseModel):
    """Market validation signal."""

    source: str = Field(description="Source platform (Reddit, Product Hunt, etc.)")
    signal_type: str = Field(description="Type: discussion, launch, trend, review")
    description: str = Field(description="Signal description")
    url: str | None = Field(None, description="Source URL if available")
    sentiment: Literal["positive", "neutral", "negative"] = Field(
        description="Overall sentiment"
    )
    strength: Literal["weak", "moderate", "strong"] = Field(
        description="Signal strength"
    )


class ExecutionPhase(BaseModel):
    """Execution roadmap phase."""

    phase_number: int = Field(ge=1, le=5, description="Phase number (1-5)")
    name: str = Field(description="Phase name (e.g., 'MVP', 'Launch')")
    duration: str = Field(description="Duration (e.g., '2-4 weeks')")
    milestones: list[str] = Field(description="Key milestones for this phase")
    budget_estimate: str = Field(description="Budget estimate (e.g., '$5K-$10K')")
    key_risks: list[str] = Field(description="Phase-specific risks")


class RiskAssessment(BaseModel):
    """Risk assessment across categories."""

    technical_risk: int = Field(ge=1, le=10, description="Technical risk score (1-10)")
    market_risk: int = Field(ge=1, le=10, description="Market risk score (1-10)")
    team_risk: int = Field(ge=1, le=10, description="Team/execution risk (1-10)")
    financial_risk: int = Field(ge=1, le=10, description="Financial risk score (1-10)")
    overall_risk: float = Field(description="Weighted overall risk (0-1)")
    mitigation_strategies: list[str] = Field(
        description="Top 3 risk mitigation strategies"
    )


# ============================================
# Full Analysis Response
# ============================================


class ResearchAnalysisResponse(BaseModel):
    """Complete research analysis response."""

    id: UUID
    user_id: UUID
    status: Literal["pending", "processing", "completed", "failed"]
    progress_percent: int = Field(ge=0, le=100)
    current_step: str | None = None

    # Input
    idea_description: str
    target_market: str
    budget_range: str

    # Results (None until completed)
    market_analysis: MarketAnalysis | None = None
    competitor_landscape: list[CompetitorProfile] = Field(default_factory=list)
    value_equation: ValueEquation | None = None
    market_matrix: MarketMatrix | None = None
    acp_framework: ACPFramework | None = None
    validation_signals: list[ValidationSignal] = Field(default_factory=list)
    execution_roadmap: list[ExecutionPhase] = Field(default_factory=list)
    risk_assessment: RiskAssessment | None = None

    # Summary scores (None until completed)
    opportunity_score: float | None = Field(None, ge=0, le=1)
    market_fit_score: float | None = Field(None, ge=0, le=1)
    execution_readiness: float | None = Field(None, ge=0, le=1)

    # Metadata
    tokens_used: int = 0
    analysis_cost_usd: float = 0.0
    error_message: str | None = None

    # Timestamps
    created_at: datetime
    started_at: datetime | None = None
    completed_at: datetime | None = None

    class Config:
        from_attributes = True


class ResearchAnalysisSummary(BaseModel):
    """Summary view of research analysis (for lists)."""

    id: UUID
    status: str
    progress_percent: int
    idea_description: str
    target_market: str
    opportunity_score: float | None = None
    created_at: datetime
    completed_at: datetime | None = None

    class Config:
        from_attributes = True


class ResearchAnalysisListResponse(BaseModel):
    """Paginated list of research analyses."""

    items: list[ResearchAnalysisSummary]
    total: int


# ============================================
# Progress Update (for SSE)
# ============================================


class ResearchProgressUpdate(BaseModel):
    """Progress update for SSE streaming."""

    analysis_id: UUID
    status: str
    progress_percent: int
    current_step: str
    message: str | None = None


# ============================================
# Research Request Schemas (Phase 5.2: Admin Queue)
# ============================================


class ResearchRequestResponse(BaseModel):
    """Research request entity with admin review details."""

    id: UUID
    user_id: UUID
    admin_id: UUID | None = None
    status: Literal["pending", "approved", "rejected", "completed"]
    idea_description: str
    target_market: str | None = None
    budget_range: str | None = None
    admin_notes: str | None = None
    analysis_id: UUID | None = None
    created_at: datetime
    reviewed_at: datetime | None = None
    completed_at: datetime | None = None

    # Optional: include user email for admin queue display
    user_email: str | None = None

    class Config:
        from_attributes = True


class ResearchRequestSummary(BaseModel):
    """Summary view of research request (for admin queue)."""

    id: UUID
    user_id: UUID
    user_email: str | None = None
    status: Literal["pending", "approved", "rejected", "completed"]
    idea_description: str
    target_market: str | None = None
    created_at: datetime
    reviewed_at: datetime | None = None

    class Config:
        from_attributes = True


class ResearchRequestListResponse(BaseModel):
    """Paginated list of research requests."""

    items: list[ResearchRequestSummary]
    total: int


class ResearchRequestAction(BaseModel):
    """Admin action on research request (approve/reject)."""

    action: Literal["approve", "reject"]
    notes: str | None = Field(
        default=None,
        max_length=1000,
        description="Optional notes explaining the decision",
    )


# ============================================
# Quota Response
# ============================================


class ResearchQuotaResponse(BaseModel):
    """User's research quota status."""

    analyses_used: int
    analyses_limit: int
    analyses_remaining: int
    tier: str
    resets_at: datetime | None = None
