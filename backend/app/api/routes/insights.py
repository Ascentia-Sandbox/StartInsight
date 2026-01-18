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
