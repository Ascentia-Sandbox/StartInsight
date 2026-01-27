"""Pydantic schemas for Insight API responses."""

from datetime import datetime
from typing import Any, Literal
from uuid import UUID

from pydantic import BaseModel, Field, HttpUrl


class CompetitorResponse(BaseModel):
    """Competitor data in API response."""

    name: str
    url: str
    description: str
    market_position: str | None = None


class CommunitySignal(BaseModel):
    """Community signal data for visualization."""

    platform: Literal["Reddit", "Facebook", "YouTube", "Other"]
    score: int = Field(ge=1, le=10, description="Engagement score from 1-10")
    members: int = Field(ge=0, description="Total community members")
    engagement_rate: float = Field(ge=0.0, le=1.0, description="Engagement rate as decimal (0-1)")
    top_url: HttpUrl | None = Field(default=None, description="URL to top post/discussion")


class EnhancedScore(BaseModel):
    """Enhanced 8-dimension scoring data."""

    dimension: str = Field(description="Scoring dimension name")
    value: int = Field(ge=1, le=10, description="Score from 1-10")
    label: str = Field(description="Human-readable label (e.g., 'Excellent', 'Strong', 'Moderate')")


class TrendKeyword(BaseModel):
    """Trending keyword with search volume and growth data."""

    keyword: str = Field(description="Search keyword")
    volume: str = Field(description="Search volume (e.g., '1.0K', '27.1K', '74.0K')")
    growth: str = Field(description="Growth percentage (e.g., '+1900%', '+86%', '+514%')")


class RawSignalSummary(BaseModel):
    """Summary of raw signal in insight response."""

    id: UUID
    source: str
    url: str
    created_at: datetime

    class Config:
        from_attributes = True


class InsightResponse(BaseModel):
    """Single insight response."""

    id: UUID
    raw_signal_id: UUID
    problem_statement: str
    proposed_solution: str
    market_size_estimate: str
    relevance_score: float = Field(ge=0.0, le=1.0)
    competitor_analysis: list[dict[str, Any]]
    created_at: datetime

    # Optional: include raw signal summary
    raw_signal: RawSignalSummary | None = None

    # Enhanced visualizations (Phase 5+)
    community_signals_chart: list[CommunitySignal] | None = Field(
        default=None,
        description="Community engagement visualization data"
    )
    enhanced_scores: list[EnhancedScore] | None = Field(
        default=None,
        description="8-dimension scoring breakdown"
    )
    trend_keywords: list[TrendKeyword] | None = Field(
        default=None,
        description="Trending keywords with search volume and growth percentage"
    )

    # Individual score fields for frontend compatibility
    opportunity_score: int | None = Field(default=None, ge=1, le=10)
    problem_score: int | None = Field(default=None, ge=1, le=10)
    feasibility_score: int | None = Field(default=None, ge=1, le=10)
    why_now_score: int | None = Field(default=None, ge=1, le=10)
    go_to_market_score: int | None = Field(default=None, ge=1, le=10)
    founder_fit_score: int | None = Field(default=None, ge=1, le=10)
    execution_difficulty_score: int | None = Field(default=None, ge=1, le=10)
    revenue_potential_score: int | None = Field(default=None, ge=1, le=10)

    class Config:
        from_attributes = True


class InsightListResponse(BaseModel):
    """Paginated insights response."""

    insights: list[InsightResponse]
    total: int
    limit: int
    offset: int
