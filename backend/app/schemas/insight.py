"""Pydantic schemas for Insight API responses."""

from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator


class CompetitorResponse(BaseModel):
    """Competitor data in API response."""

    name: str
    url: str
    description: str
    market_position: str | None = None


class CompetitorListItemResponse(BaseModel):
    """Competitor list item in API response."""

    id: UUID
    name: str
    url: str
    description: str | None = None
    value_proposition: str | None = None
    target_audience: str | None = None
    market_position: str | None = None
    metrics: dict[str, Any] | None = None
    features: list[str] | None = None
    strengths: list[str] | None = None
    weaknesses: list[str] | None = None
    positioning_x: float | None = None
    positioning_y: float | None = None
    last_scraped_at: datetime | None = None
    scrape_status: str | None = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class CompetitorSnapshotResponse(BaseModel):
    """Competitor snapshot in API response."""

    id: UUID
    snapshot_data: dict[str, Any] | None = None
    changes_detected: dict[str, Any] | None = None
    scraped_at: datetime
    scrape_method: str | None = None

    model_config = ConfigDict(from_attributes=True)


class CompetitorDetailResponse(CompetitorListItemResponse):
    """Detailed competitor profile with snapshots."""

    insight_id: UUID
    scrape_error: str | None = None
    analysis_generated_at: datetime | None = None
    analysis_model: str | None = None
    snapshots: list[CompetitorSnapshotResponse] = []

    model_config = ConfigDict(from_attributes=True)


class MessageResponse(BaseModel):
    """Simple message response."""

    message: str


class CommunitySignal(BaseModel):
    """Community signal data for visualization.

    Flexible schema: AI agents may produce varying field formats.
    """

    platform: str | None = Field(default=None, description="Platform name (e.g., Reddit, Facebook)")
    community: str | None = Field(default=None, description="Community name (e.g., Sales Hacker)")
    score: int = Field(ge=0, le=10, description="Engagement score from 0-10")
    members: str | int = Field(description="Community members (e.g., '150K+ members' or 5000)")
    engagement_rate: float | None = Field(default=None, ge=0.0, le=1.0, description="Engagement rate as decimal (0-1)")
    top_url: str | None = Field(default=None, description="URL to top post/discussion")


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

    model_config = ConfigDict(from_attributes=True)


class TrendData(BaseModel):
    """Trend timeseries data for line chart visualization."""

    dates: list[str] = Field(default_factory=list, description="Date labels")
    values: list[float] = Field(default_factory=list, description="Search volume values")


class InsightResponse(BaseModel):
    """Single insight response."""

    id: UUID
    raw_signal_id: UUID
    slug: str | None = None
    title: str | None = None
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

    # Trend data for line chart (extracted from raw_signal.extra_metadata)
    trend_data: TrendData | None = Field(
        default=None,
        description="Timeseries trend data (dates + values) for chart visualization"
    )

    # Market sizing (TAM/SAM/SOM)
    market_sizing: dict[str, Any] | None = None

    # Advanced frameworks
    value_ladder: list[dict[str, Any]] | None = None
    market_gap_analysis: str | None = None
    why_now_analysis: str | None = None
    proof_signals: list[dict[str, Any]] | None = None
    execution_plan: list[dict[str, Any]] | None = None

    # Individual score fields for frontend compatibility
    opportunity_score: int | None = Field(default=None, ge=1, le=10)
    problem_score: int | None = Field(default=None, ge=1, le=10)
    feasibility_score: int | None = Field(default=None, ge=1, le=10)
    why_now_score: int | None = Field(default=None, ge=1, le=10)
    go_to_market_score: int | None = Field(default=None, ge=1, le=10)
    founder_fit_score: int | None = Field(default=None, ge=1, le=10)
    execution_difficulty_score: int | None = Field(
        default=None, ge=1, le=10, validation_alias="execution_difficulty"
    )
    revenue_potential_score: str | None = Field(
        default=None, validation_alias="revenue_potential"
    )

    @field_validator("value_ladder", mode="before")
    @classmethod
    def normalize_value_ladder(cls, v: Any) -> list[dict[str, Any]] | None:
        """Normalize value_ladder from various AI output formats to a list of dicts.

        Handles:
        - {'tiers': [...]} → extract tiers list
        - {'core': {...}, 'frontend': {...}, ...} → convert named tiers to list
        - [...] → pass through
        - None → pass through
        """
        if v is None:
            return None
        if isinstance(v, list):
            return v
        if isinstance(v, dict):
            if "tiers" in v:
                return v["tiers"]
            # Named tier format: {'core': {...}, 'frontend': {...}, ...}
            return [{"tier_name": k, **val} if isinstance(val, dict) else {"tier_name": k, "value": val}
                    for k, val in v.items()]
        return v

    model_config = ConfigDict(from_attributes=True, populate_by_name=True)


class InsightListResponse(BaseModel):
    """Paginated insights response."""

    insights: list[InsightResponse]
    total: int
    limit: int
    offset: int
