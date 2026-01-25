"""API endpoints for insights."""

import logging
from datetime import datetime, timedelta
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.db.session import get_db
from app.models.insight import Insight
from app.models.raw_signal import RawSignal
from app.schemas.insight import InsightListResponse, InsightResponse

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/insights", tags=["insights"])


@router.get("", response_model=InsightListResponse)
async def list_insights(
    min_score: Annotated[
        float, Query(ge=0.0, le=1.0, description="Minimum relevance score filter")
    ] = 0.0,
    source: Annotated[
        str | None, Query(description="Filter by source (reddit, product_hunt, etc.)")
    ] = None,
    limit: Annotated[int, Query(ge=1, le=100, description="Number of results")] = 20,
    offset: Annotated[int, Query(ge=0, description="Pagination offset")] = 0,
    db: AsyncSession = Depends(get_db),
) -> InsightListResponse:
    """
    List all insights with filtering and pagination.

    - **min_score**: Minimum relevance score (0.0 - 1.0)
    - **source**: Filter by source (reddit, product_hunt, google_trends)
    - **limit**: Number of results per page (max 100)
    - **offset**: Pagination offset

    Returns insights sorted by relevance_score descending.
    """
    # Build query
    query = select(Insight).options(selectinload(Insight.raw_signal))

    # Filter by minimum score
    if min_score > 0.0:
        query = query.where(Insight.relevance_score >= min_score)

    # Filter by source (via raw_signal relationship)
    if source:
        query = query.join(Insight.raw_signal).where(RawSignal.source == source)

    # Sort by relevance score descending
    query = query.order_by(Insight.relevance_score.desc())

    # Pagination
    query = query.limit(limit).offset(offset)

    # Execute
    result = await db.execute(query)
    insights = result.scalars().all()

    # Get total count
    count_query = select(func.count(Insight.id))
    if min_score > 0.0:
        count_query = count_query.where(Insight.relevance_score >= min_score)
    if source:
        count_query = count_query.join(Insight.raw_signal).where(
            RawSignal.source == source
        )

    total = await db.scalar(count_query)

    logger.info(
        f"Listed {len(insights)} insights (min_score={min_score}, "
        f"source={source}, total={total})"
    )

    return InsightListResponse(
        insights=[InsightResponse.model_validate(i) for i in insights],
        total=total or 0,
        limit=limit,
        offset=offset,
    )


@router.get("/daily-top", response_model=list[InsightResponse])
async def get_daily_top(
    limit: Annotated[
        int, Query(ge=1, le=20, description="Number of top insights")
    ] = 5,
    db: AsyncSession = Depends(get_db),
) -> list[InsightResponse]:
    """
    Get top insights from last 24 hours.

    Returns the highest-scored insights created in the last 24 hours,
    sorted by relevance_score descending.

    - **limit**: Number of insights to return (max 20, default 5)
    """
    # Calculate 24 hours ago
    yesterday = datetime.utcnow() - timedelta(days=1)

    # Build query
    query = (
        select(Insight)
        .options(selectinload(Insight.raw_signal))
        .where(Insight.created_at >= yesterday)
        .order_by(Insight.relevance_score.desc())
        .limit(limit)
    )

    # Execute
    result = await db.execute(query)
    insights = result.scalars().all()

    logger.info(f"Retrieved {len(insights)} top insights from last 24 hours")

    return [InsightResponse.model_validate(i) for i in insights]


@router.get("/idea-of-the-day", response_model=InsightResponse | None)
async def get_idea_of_the_day(
    db: AsyncSession = Depends(get_db),
) -> InsightResponse | None:
    """
    Get featured "Idea of the Day" insight.

    Returns a high-quality insight deterministically selected for the current day.
    The selection stays consistent throughout the day (uses date as seed).

    Selection criteria:
    - Relevance score >= 0.7 (high quality)
    - Created within last 7 days (fresh)
    - Deterministic selection based on date (same insight all day)
    """
    import hashlib

    # Calculate 7 days ago for freshness filter
    week_ago = datetime.utcnow() - timedelta(days=7)

    # Get qualifying insights (high quality, recent)
    query = (
        select(Insight)
        .options(selectinload(Insight.raw_signal))
        .where(Insight.relevance_score >= 0.7)
        .where(Insight.created_at >= week_ago)
        .order_by(Insight.relevance_score.desc())
        .limit(20)  # Get top 20 candidates
    )

    result = await db.execute(query)
    candidates = list(result.scalars().all())

    if not candidates:
        logger.warning("No qualifying insights for idea of the day")
        return None

    # Deterministic selection based on today's date
    today_str = datetime.utcnow().strftime("%Y-%m-%d")
    date_hash = int(hashlib.md5(today_str.encode()).hexdigest(), 16)
    selected_index = date_hash % len(candidates)

    selected_insight = candidates[selected_index]

    logger.info(f"Idea of the day: {selected_insight.id} (index {selected_index})")

    return InsightResponse.model_validate(selected_insight)


@router.get("/{insight_id}", response_model=InsightResponse)
async def get_insight(
    insight_id: UUID,
    db: AsyncSession = Depends(get_db),
) -> InsightResponse:
    """
    Get single insight by ID.

    Returns the insight with its related raw signal data.

    - **insight_id**: UUID of the insight
    """
    # Build query with eager loading
    query = (
        select(Insight)
        .options(selectinload(Insight.raw_signal))
        .where(Insight.id == insight_id)
    )

    # Execute
    result = await db.execute(query)
    insight = result.scalar_one_or_none()

    if not insight:
        logger.warning(f"Insight not found: {insight_id}")
        raise HTTPException(status_code=404, detail="Insight not found")

    logger.info(f"Retrieved insight: {insight_id}")

    return InsightResponse.model_validate(insight)
