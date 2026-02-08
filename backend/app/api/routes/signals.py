"""API routes for raw signals.

Includes:
- Public signal listing and retrieval
- Admin-only scraping trigger
- Signal statistics

Phase 5: Authentication added to sensitive endpoints.
"""

import logging
from datetime import UTC, datetime, timedelta
from typing import Literal
from uuid import UUID

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Query
from pydantic import BaseModel, field_validator
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import AdminUser, require_admin
from app.db.session import get_db
from app.models.raw_signal import RawSignal
from app.models.user import User
from app.schemas.signals import (
    RawSignalListResponse,
    RawSignalResponse,
    SignalStatsResponse,
)
from app.tasks import trigger_scraping_now

logger = logging.getLogger(__name__)

router = APIRouter()


# ============================================================
# Input Validation Schemas
# ============================================================


class ScraperConfig(BaseModel):
    """Validated configuration for manual scraping trigger."""

    sources: list[str] = ["reddit", "product_hunt", "trends"]
    limit_per_source: int = 25
    days_back: int = 1

    @field_validator("sources")
    @classmethod
    def validate_sources(cls, v: list[str]) -> list[str]:
        """Ensure only valid sources are requested."""
        valid_sources = {"reddit", "product_hunt", "trends", "twitter", "google_trends"}
        invalid = set(v) - valid_sources
        if invalid:
            raise ValueError(f"Invalid sources: {invalid}. Valid: {valid_sources}")
        return v

    @field_validator("limit_per_source")
    @classmethod
    def validate_limit(cls, v: int) -> int:
        """Ensure limit is within acceptable range."""
        if not 1 <= v <= 100:
            raise ValueError("limit_per_source must be 1-100")
        return v

    @field_validator("days_back")
    @classmethod
    def validate_days(cls, v: int) -> int:
        """Ensure days_back is within acceptable range."""
        if not 1 <= v <= 7:
            raise ValueError("days_back must be 1-7")
        return v


class TriggerScrapingResponse(BaseModel):
    """Response for scraping trigger endpoint."""

    status: Literal["queued", "rate_limited", "error"]
    message: str
    job_id: str | None = None
    triggered_by: str | None = None
    sources: list[str] | None = None
    next_allowed_at: datetime | None = None


# Rate limiting state (in production, use Redis)
_last_trigger_time: datetime | None = None
_trigger_cooldown_minutes = 5


@router.get("/signals", response_model=RawSignalListResponse)
async def list_signals(
    source: str | None = Query(None, description="Filter by source (reddit, product_hunt, google_trends)"),
    processed: bool | None = Query(None, description="Filter by processed status"),
    limit: int = Query(20, ge=1, le=100, description="Number of signals to return"),
    offset: int = Query(0, ge=0, description="Number of signals to skip"),
    db: AsyncSession = Depends(get_db),
):
    """
    List raw signals with optional filtering and pagination.

    Args:
        source: Optional source filter
        processed: Optional processed status filter
        limit: Number of signals to return (max 100)
        offset: Number of signals to skip
        db: Database session

    Returns:
        Paginated list of raw signals
    """
    try:
        # Build query
        query = select(RawSignal)

        # Apply filters
        if source:
            query = query.where(RawSignal.source == source)
        if processed is not None:
            query = query.where(RawSignal.processed == processed)

        # Order by created_at descending (newest first)
        query = query.order_by(RawSignal.created_at.desc())

        # Get total count (direct count with same filters, avoids subquery)
        count_query = select(func.count(RawSignal.id))
        if source:
            count_query = count_query.where(RawSignal.source == source)
        if processed is not None:
            count_query = count_query.where(RawSignal.processed == processed)
        total_result = await db.execute(count_query)
        total = total_result.scalar() or 0

        # Apply pagination
        query = query.limit(limit).offset(offset)

        # Execute query
        result = await db.execute(query)
        signals = result.scalars().all()

        # Convert to response models
        signal_responses = [
            RawSignalResponse.model_validate(signal) for signal in signals
        ]

        return RawSignalListResponse(
            signals=signal_responses,
            total=total,
            limit=limit,
            offset=offset,
            has_more=(offset + limit) < total,
        )

    except Exception as e:
        logger.error(f"Error listing signals: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="An internal error occurred. Please try again.")


@router.get("/signals/{signal_id}", response_model=RawSignalResponse)
async def get_signal(
    signal_id: UUID,
    db: AsyncSession = Depends(get_db),
):
    """
    Get a single raw signal by ID.

    Args:
        signal_id: Signal UUID
        db: Database session

    Returns:
        Raw signal details
    """
    query = select(RawSignal).where(RawSignal.id == signal_id)
    result = await db.execute(query)
    signal = result.scalars().first()

    if not signal:
        raise HTTPException(status_code=404, detail="Signal not found")

    return RawSignalResponse.model_validate(signal)


@router.get("/signals/stats/summary", response_model=SignalStatsResponse)
async def get_signal_stats(
    db: AsyncSession = Depends(get_db),
):
    """
    Get statistics about raw signals.

    Args:
        db: Database session

    Returns:
        Signal statistics including counts by source and processed status
    """
    try:
        # Get total count
        total_query = select(func.count()).select_from(RawSignal)
        total_result = await db.execute(total_query)
        total_signals = total_result.scalar() or 0

        # Get counts by source
        source_query = select(
            RawSignal.source, func.count(RawSignal.id).label("count")
        ).group_by(RawSignal.source)
        source_result = await db.execute(source_query)
        signals_by_source = {row[0]: row[1] for row in source_result.all()}

        # Get processed counts
        processed_query = select(func.count()).select_from(RawSignal).where(
            RawSignal.processed == True  # noqa: E712
        )
        processed_result = await db.execute(processed_query)
        processed_count = processed_result.scalar() or 0

        unprocessed_count = total_signals - processed_count

        # Get latest signal time
        latest_query = select(func.max(RawSignal.created_at))
        latest_result = await db.execute(latest_query)
        latest_signal_time = latest_result.scalar()

        return SignalStatsResponse(
            total_signals=total_signals,
            signals_by_source=signals_by_source,
            processed_count=processed_count,
            unprocessed_count=unprocessed_count,
            latest_signal_time=latest_signal_time,
        )

    except Exception as e:
        logger.error(f"Error getting signal stats: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="An internal error occurred. Please try again.")


@router.post("/signals/trigger-scraping", response_model=TriggerScrapingResponse)
async def trigger_scraping(
    config: ScraperConfig | None = None,
    current_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    """
    Manually trigger scraping tasks immediately.

    **Requires admin authentication.**

    Rate limited to once every 5 minutes to prevent abuse.

    Args:
        config: Optional scraper configuration
        current_user: Authenticated admin user
        db: Database session

    Returns:
        Status with job ID and trigger info

    Raises:
        HTTPException: 429 if rate limited, 403 if not admin
    """
    global _last_trigger_time

    # Rate limiting check
    if _last_trigger_time:
        cooldown_end = _last_trigger_time + timedelta(minutes=_trigger_cooldown_minutes)
        if datetime.now(UTC) < cooldown_end:
            logger.warning(
                f"Scraping trigger rate limited. User: {current_user.email}"
            )
            return TriggerScrapingResponse(
                status="rate_limited",
                message=f"Rate limit: Can only trigger scraping once every {_trigger_cooldown_minutes} minutes",
                triggered_by=current_user.email,
                next_allowed_at=cooldown_end,
            )

    # Use default config if not provided
    config = config or ScraperConfig()

    try:
        # Log the trigger event
        logger.info(
            f"Scraping triggered by admin {current_user.email}. "
            f"Sources: {config.sources}, Limit: {config.limit_per_source}"
        )

        # Trigger the scraping job
        result = await trigger_scraping_now()

        # Update rate limit timestamp
        _last_trigger_time = datetime.now(UTC)

        return TriggerScrapingResponse(
            status="queued",
            message="Scraping job queued successfully",
            job_id=result.get("job_id"),
            triggered_by=current_user.email,
            sources=config.sources,
        )

    except Exception as e:
        logger.error(f"Error triggering scraping: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail="Failed to queue scraping job. Please try again.",
        )


@router.get("/signals/trigger-status")
async def get_trigger_status(
    current_user: User = Depends(require_admin),
):
    """
    Get current scraping trigger status (rate limit info).

    **Requires admin authentication.**

    Returns:
        Current rate limit status
    """
    global _last_trigger_time

    if _last_trigger_time:
        cooldown_end = _last_trigger_time + timedelta(minutes=_trigger_cooldown_minutes)
        can_trigger = datetime.now(UTC) >= cooldown_end
        next_allowed = cooldown_end if not can_trigger else None
    else:
        can_trigger = True
        next_allowed = None

    return {
        "can_trigger": can_trigger,
        "last_triggered_at": _last_trigger_time.isoformat() if _last_trigger_time else None,
        "next_allowed_at": next_allowed.isoformat() if next_allowed else None,
        "cooldown_minutes": _trigger_cooldown_minutes,
    }
