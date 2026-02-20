"""Pydantic schemas for raw signals API responses."""

from datetime import datetime
from typing import Any, Generic, TypeVar
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

T = TypeVar("T")


class RawSignalResponse(BaseModel):
    """Response schema for a single raw signal."""

    id: UUID = Field(..., description="Unique signal identifier")
    source: str = Field(..., description="Data source (reddit, product_hunt, google_trends)")
    url: str = Field(..., description="Source URL where data was scraped")
    content: str = Field(..., description="Scraped content in markdown format")
    extra_metadata: dict[str, Any] = Field(..., description="Additional metadata (upvotes, comments, etc.)")
    created_at: datetime = Field(..., description="Timestamp when signal was created")
    processed: bool = Field(..., description="Whether signal has been analyzed")

    model_config = ConfigDict(from_attributes=True)


class PaginatedResponse(BaseModel, Generic[T]):
    """Generic paginated response wrapper."""

    items: list[T] = Field(..., description="List of items")
    total: int = Field(..., description="Total number of items")
    limit: int = Field(..., description="Number of items per page")
    offset: int = Field(..., description="Number of items skipped")
    has_more: bool = Field(..., description="Whether there are more items available")


class RawSignalListResponse(BaseModel):
    """Response schema for list of raw signals."""

    signals: list[RawSignalResponse] = Field(..., description="List of raw signals")
    total: int = Field(..., description="Total number of signals")
    limit: int = Field(..., description="Number of signals per page")
    offset: int = Field(..., description="Number of signals skipped")
    has_more: bool = Field(..., description="Whether there are more signals available")


class SignalStatsResponse(BaseModel):
    """Response schema for signal statistics."""

    total_signals: int = Field(..., description="Total number of signals")
    signals_by_source: dict[str, int] = Field(..., description="Signal count per source")
    processed_count: int = Field(..., description="Number of processed signals")
    unprocessed_count: int = Field(..., description="Number of unprocessed signals")
    latest_signal_time: datetime | None = Field(None, description="Timestamp of most recent signal")
