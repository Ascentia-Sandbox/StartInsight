"""API routes for raw signals."""

import logging
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.models.raw_signal import RawSignal
from app.schemas.signals import (
    RawSignalListResponse,
    RawSignalResponse,
    SignalStatsResponse,
)
from app.tasks import trigger_scraping_now

logger = logging.getLogger(__name__)

router = APIRouter()


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

        # Get total count
        count_query = select(func.count()).select_from(query.subquery())
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
        logger.error(f"Error listing signals: {e}")
        raise HTTPException(status_code=500, detail=str(e))


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
    try:
        query = select(RawSignal).where(RawSignal.id == signal_id)
        result = await db.execute(query)
        signal = result.scalars().first()

        if not signal:
            raise HTTPException(status_code=404, detail="Signal not found")

        return RawSignalResponse.model_validate(signal)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting signal {signal_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


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
        logger.error(f"Error getting signal stats: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/signals/trigger-scraping")
async def trigger_scraping():
    """
    Manually trigger scraping tasks immediately (for testing/debugging).

    Returns:
        Status message with job ID
    """
    try:
        result = await trigger_scraping_now()
        return result

    except Exception as e:
        logger.error(f"Error triggering scraping: {e}")
        raise HTTPException(status_code=500, detail=str(e))
