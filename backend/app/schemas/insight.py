"""Pydantic schemas for Insight API responses."""

from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, Field


class CompetitorResponse(BaseModel):
    """Competitor data in API response."""

    name: str
    url: str
    description: str
    market_position: str | None = None


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

    class Config:
        from_attributes = True


class InsightListResponse(BaseModel):
    """Paginated insights response."""

    insights: list[InsightResponse]
    total: int
    limit: int
    offset: int
