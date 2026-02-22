"""API endpoints for insights.

Phase 15.4: APAC Multi-language Support - Accept-Language header negotiation
"""

import asyncio
import hashlib
import json
import logging
from datetime import UTC, datetime, timedelta
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Header, HTTPException, Query, Request
from fastapi.responses import StreamingResponse
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.api.deps import AdminUser, CurrentUser
from app.core.cache import cache_get, cache_set
from app.core.config import settings
from app.core.rate_limits import limiter
from app.db.session import get_db
from app.models.insight import Insight
from app.models.raw_signal import RawSignal
from app.schemas.insight import (
    CompetitorDetailResponse,
    CompetitorListItemResponse,
    CompetitorSnapshotResponse,
    InsightListResponse,
    InsightResponse,
    MessageResponse,
)
from app.services.trend_prediction import generate_trend_predictions

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/insights", tags=["insights"])


# ============================================================
# Phase 15.4: Language Negotiation Helper
# ============================================================

SUPPORTED_LANGUAGES = ["en", "zh-CN", "id-ID", "vi-VN", "th-TH", "tl-PH"]


def parse_accept_language(accept_language: str | None) -> str:
    """
    Parse Accept-Language header and return best matching supported language.

    Phase 15.4: APAC Multi-language Support

    Examples:
        "zh-CN,zh;q=0.9,en;q=0.8" -> "zh-CN"
        "en-US,en;q=0.9" -> "en"
        "id-ID" -> "id-ID"
        None -> "en"

    Args:
        accept_language: Accept-Language header value

    Returns:
        str: Best matching language code (defaults to "en")
    """
    if not accept_language:
        return "en"

    # Parse weighted language preferences
    # Format: "zh-CN,zh;q=0.9,en;q=0.8"
    languages = []
    for lang_part in accept_language.split(","):
        parts = lang_part.strip().split(";")
        lang_code = parts[0].strip()

        # Extract quality factor (default 1.0)
        quality = 1.0
        if len(parts) > 1 and parts[1].startswith("q="):
            try:
                quality = float(parts[1][2:])
            except ValueError:
                quality = 1.0

        languages.append((lang_code, quality))

    # Sort by quality (highest first)
    languages.sort(key=lambda x: x[1], reverse=True)

    # Find first supported language
    for lang_code, _ in languages:
        # Exact match (zh-CN)
        if lang_code in SUPPORTED_LANGUAGES:
            return lang_code

        # Base language match (zh -> zh-CN)
        base_lang = lang_code.split("-")[0]
        for supported in SUPPORTED_LANGUAGES:
            if supported.startswith(base_lang):
                return supported

    # Default to English
    return "en"


def apply_translation(insight_data: dict, language: str) -> dict:
    """
    Apply translations to insight data based on language.

    Phase 15.4: APAC Multi-language Support

    Args:
        insight_data: Insight data dict
        language: Target language code

    Returns:
        dict: Insight data with translated fields
    """
    if language == "en" or not insight_data.get("translations"):
        return insight_data

    translations = insight_data.get("translations", {})
    lang_translations = translations.get(language, {})

    # Apply translations to translatable fields
    translatable_fields = [
        "title",
        "problem_statement",
        "proposed_solution",
        "market_gap_analysis",
        "why_now_analysis",
    ]

    for field in translatable_fields:
        if field in lang_translations:
            insight_data[field] = lang_translations[field]

    return insight_data


def _serialize_insight(insight: Insight, target_language: str = "en") -> dict:
    """Serialize an insight ORM object to a dict with trend_data injected."""
    insight_dict = InsightResponse.model_validate(insight).model_dump()
    # Inject trend_data from raw_signal.extra_metadata if available
    if insight.raw_signal and insight.raw_signal.extra_metadata:
        td = insight.raw_signal.extra_metadata.get("trend_data")
        if td and td.get("dates"):
            insight_dict["trend_data"] = {
                "dates": td.get("dates", []),
                "values": td.get("values", []),
            }
    return apply_translation(insight_dict, target_language)


@router.get("", response_model=InsightListResponse)
@limiter.limit("100/minute")
async def list_insights(
    request: Request,
    min_score: Annotated[
        float, Query(ge=0.0, le=1.0, description="Minimum relevance score filter")
    ] = 0.0,
    source: Annotated[
        str | None, Query(description="Filter by source (reddit, product_hunt, etc.)")
    ] = None,
    sort: Annotated[
        str, Query(description="Sort by: relevance, founder_fit, opportunity, problem, feasibility, why_now, go_to_market")
    ] = "relevance",
    featured: Annotated[
        bool, Query(description="Filter only featured/high-quality insights (score >= 0.85)")
    ] = False,
    limit: Annotated[int, Query(ge=1, le=100, description="Number of results")] = 20,
    offset: Annotated[int, Query(ge=0, description="Pagination offset")] = 0,
    accept_language: Annotated[str | None, Header()] = None,
    language: Annotated[
        str | None, Query(description="Explicit language override (en, zh-CN, id-ID, vi-VN, th-TH, tl-PH)")
    ] = None,
    db: AsyncSession = Depends(get_db),
) -> InsightListResponse:
    """
    List all insights with filtering and pagination.

    Phase 15.4: APAC Multi-language Support - Returns translated content based on Accept-Language header or explicit language parameter.

    - **min_score**: Minimum relevance score (0.0 - 1.0)
    - **source**: Filter by source (reddit, product_hunt, google_trends)
    - **limit**: Number of results per page (max 100)
    - **offset**: Pagination offset
    - **language**: Explicit language override (en, zh-CN, id-ID, vi-VN, th-TH, tl-PH)
    - **Accept-Language**: HTTP header for automatic language detection

    Returns insights sorted by relevance_score descending with translated fields.
    """
    # Determine target language (explicit parameter takes precedence)
    target_language = language or parse_accept_language(accept_language)

    # --- Cache lookup (TTL: 60s) ---
    # Key encodes all params that affect the result, including language.
    _cache_raw = f"{min_score}:{source}:{sort}:{featured}:{limit}:{offset}:{target_language}"
    cache_key = f"insights:list:{hashlib.md5(_cache_raw.encode()).hexdigest()}"
    cached_response = await cache_get(cache_key)
    if cached_response is not None:
        return InsightListResponse.model_validate(cached_response)

    # Build query
    query = select(Insight).options(selectinload(Insight.raw_signal))

    # Filter by minimum score
    if min_score > 0.0:
        query = query.where(Insight.relevance_score >= min_score)

    # Filter featured (high-quality) insights
    if featured:
        query = query.where(Insight.relevance_score >= 0.85)

    # Filter by source (via raw_signal relationship)
    if source:
        query = query.join(Insight.raw_signal).where(RawSignal.source == source)

    # Dynamic sorting based on sort parameter
    sort_mapping = {
        "relevance": Insight.relevance_score.desc(),
        "founder_fit": Insight.founder_fit_score.desc().nulls_last(),
        "fit": Insight.founder_fit_score.desc().nulls_last(),  # Alias for founder_fit
        "opportunity": Insight.opportunity_score.desc().nulls_last(),
        "problem": Insight.problem_score.desc().nulls_last(),
        "feasibility": Insight.feasibility_score.desc().nulls_last(),
        "easy": Insight.feasibility_score.desc().nulls_last(),  # Alias for feasibility
        "why_now": Insight.why_now_score.desc().nulls_last(),
        "go_to_market": Insight.go_to_market_score.desc().nulls_last(),
        "newest": Insight.created_at.desc(),
        "recent": Insight.created_at.desc(),  # Alias for newest
    }
    sort_column = sort_mapping.get(sort, Insight.relevance_score.desc())
    query = query.order_by(sort_column)

    # Pagination
    query = query.limit(limit).offset(offset)

    # Execute
    result = await db.execute(query)
    insights = result.scalars().all()

    # Get total count (must match all filters applied to main query)
    count_query = select(func.count(Insight.id))
    if min_score > 0.0:
        count_query = count_query.where(Insight.relevance_score >= min_score)
    if featured:
        count_query = count_query.where(Insight.relevance_score >= 0.85)
    if source:
        count_query = count_query.join(Insight.raw_signal).where(
            RawSignal.source == source
        )

    total = await db.scalar(count_query)

    logger.info(
        f"Listed {len(insights)} insights (min_score={min_score}, "
        f"source={source}, language={target_language}, total={total})"
    )

    # Apply translations and inject trend_data
    translated_insights = []
    for insight in insights:
        insight_dict = _serialize_insight(insight, target_language)
        translated_insights.append(InsightResponse.model_validate(insight_dict))

    response = InsightListResponse(
        insights=translated_insights,
        total=total or 0,
        limit=limit,
        offset=offset,
    )

    # Store serialised response in cache (fire-and-forget; failures are swallowed)
    await cache_set(cache_key, response.model_dump(), ttl=60)

    return response


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
    yesterday = datetime.now(UTC) - timedelta(days=1)

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

    return [InsightResponse.model_validate(_serialize_insight(i)) for i in insights]


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
    week_ago = datetime.now(UTC) - timedelta(days=7)

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
    today_str = datetime.now(UTC).strftime("%Y-%m-%d")
    date_hash = int(hashlib.md5(today_str.encode()).hexdigest(), 16)
    selected_index = date_hash % len(candidates)

    selected_insight = candidates[selected_index]

    logger.info(f"Idea of the day: {selected_insight.id} (index {selected_index})")

    return InsightResponse.model_validate(selected_insight)


@router.get("/founder-fit-picks", response_model=list[InsightResponse])
async def get_founder_fit_picks(
    limit: Annotated[
        int, Query(ge=1, le=20, description="Number of top founder-fit insights")
    ] = 10,
    min_fit_score: Annotated[
        int, Query(ge=1, le=10, description="Minimum founder fit score")
    ] = 7,
    db: AsyncSession = Depends(get_db),
) -> list[InsightResponse]:
    """
    Get insights with highest founder fit scores.

    Returns insights optimized for founder accessibility - ideas that don't require
    specialized expertise, PhDs, or years of industry experience.

    Selection criteria:
    - founder_fit_score >= min_fit_score (default 7+)
    - Sorted by founder_fit_score descending
    - Filtered to high-quality insights (relevance >= 0.7)

    - **limit**: Number of insights to return (max 20, default 10)
    - **min_fit_score**: Minimum founder fit score (1-10, default 7)
    """
    # Build query for high founder fit insights
    query = (
        select(Insight)
        .options(selectinload(Insight.raw_signal))
        .where(Insight.founder_fit_score >= min_fit_score)
        .where(Insight.relevance_score >= 0.7)
        .order_by(
            Insight.founder_fit_score.desc().nulls_last(),
            Insight.relevance_score.desc()
        )
        .limit(limit)
    )

    result = await db.execute(query)
    insights = result.scalars().all()

    logger.info(f"Retrieved {len(insights)} founder-fit picks (min_score={min_fit_score})")

    return [InsightResponse.model_validate(_serialize_insight(i)) for i in insights]


@router.get("/featured-picks", response_model=list[InsightResponse])
async def get_featured_picks(
    limit: Annotated[
        int, Query(ge=1, le=20, description="Number of featured insights")
    ] = 6,
    db: AsyncSession = Depends(get_db),
) -> list[InsightResponse]:
    """
    Get curated featured insights for homepage showcase.

    Returns high-quality, diverse insights suitable for homepage display.
    Prioritizes insights with complete data (all scores, competitor analysis, etc.)

    Selection criteria:
    - relevance_score >= 0.85 (premium quality)
    - Has 8-dimension scoring
    - Balanced across different categories/sources
    """
    # Build query for featured insights
    query = (
        select(Insight)
        .options(selectinload(Insight.raw_signal))
        .where(Insight.relevance_score >= 0.85)
        .where(Insight.opportunity_score.isnot(None))  # Has enhanced scoring
        .order_by(Insight.relevance_score.desc())
        .limit(limit)
    )

    result = await db.execute(query)
    insights = result.scalars().all()

    logger.info(f"Retrieved {len(insights)} featured picks")

    return [InsightResponse.model_validate(_serialize_insight(i)) for i in insights]


# ============================================================================
# PHASE K.4: PUBLIC STATISTICS ENDPOINT
# ============================================================================

@router.get("/stats/public")
async def get_public_stats(
    db: AsyncSession = Depends(get_db),
) -> dict:
    """
    Public statistics for homepage counters.

    No authentication required. Returns aggregate platform metrics
    for social proof display on the homepage.
    """
    # Total insights
    insight_count = await db.scalar(
        select(func.count()).select_from(Insight)
    ) or 0

    # Total raw signals
    signal_count = await db.scalar(
        select(func.count()).select_from(RawSignal)
    ) or 0

    # Average relevance score
    avg_score = await db.scalar(
        select(func.avg(Insight.relevance_score)).select_from(Insight)
    )

    # Count distinct sources
    source_count_result = await db.scalar(
        select(func.count(func.distinct(RawSignal.source))).select_from(RawSignal)
    ) or 0

    # Count insights with enhanced scoring (8-dimension)
    scored_count = await db.scalar(
        select(func.count()).select_from(Insight).where(
            Insight.opportunity_score.isnot(None)
        )
    ) or 0

    return {
        "total_insights": insight_count,
        "total_signals": signal_count,
        "avg_quality_score": round(float(avg_score or 0), 2),
        "active_sources": max(int(source_count_result), 6),  # minimum 6 known sources
        "scored_insights": scored_count,
        "scoring_dimensions": 8,
        "evidence_validators": 3,  # Google Trends, Community Signals, Proof Signals
    }


@router.get("/by-slug/{slug}", response_model=InsightResponse)
@limiter.limit("200/minute")
async def get_insight_by_slug(
    request: Request,
    slug: str,
    accept_language: Annotated[str | None, Header()] = None,
    language: Annotated[
        str | None, Query(description="Explicit language override (en, zh-CN, id-ID, vi-VN, th-TH, tl-PH)")
    ] = None,
    db: AsyncSession = Depends(get_db),
) -> InsightResponse:
    """
    Get single insight by slug.

    Returns the insight matching the given URL-friendly slug.

    - **slug**: URL-friendly slug of the insight
    - **language**: Explicit language override
    - **Accept-Language**: HTTP header for automatic language detection
    """
    target_language = language or parse_accept_language(accept_language)

    query = (
        select(Insight)
        .options(selectinload(Insight.raw_signal))
        .where(Insight.slug == slug)
    )

    result = await db.execute(query)
    insight = result.scalar_one_or_none()

    if not insight:
        logger.warning(f"Insight not found by slug: {slug}")
        raise HTTPException(status_code=404, detail="Insight not found")

    logger.info(f"Retrieved insight by slug: {slug} (language={target_language})")

    insight_dict = _serialize_insight(insight, target_language)

    return InsightResponse.model_validate(insight_dict)


@router.get("/{insight_id}", response_model=InsightResponse)
@limiter.limit("200/minute")
async def get_insight(
    request: Request,
    insight_id: UUID,
    accept_language: Annotated[str | None, Header()] = None,
    language: Annotated[
        str | None, Query(description="Explicit language override (en, zh-CN, id-ID, vi-VN, th-TH, tl-PH)")
    ] = None,
    db: AsyncSession = Depends(get_db),
) -> InsightResponse:
    """
    Get single insight by ID.

    Phase 15.4: APAC Multi-language Support - Returns translated content based on Accept-Language header or explicit language parameter.

    Returns the insight with its related raw signal data.

    - **insight_id**: UUID of the insight
    - **language**: Explicit language override (en, zh-CN, id-ID, vi-VN, th-TH, tl-PH)
    - **Accept-Language**: HTTP header for automatic language detection
    """
    # Determine target language (explicit parameter takes precedence)
    target_language = language or parse_accept_language(accept_language)

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

    logger.info(f"Retrieved insight: {insight_id} (language={target_language})")

    insight_dict = _serialize_insight(insight, target_language)

    return InsightResponse.model_validate(insight_dict)


@router.get("/{insight_id}/trend-data")
async def get_insight_trend_data(
    insight_id: UUID,
    db: AsyncSession = Depends(get_db),
) -> dict:
    """
    Get 30-day trend data for an insight.

    Returns timeseries data for Google Trends visualization.

    - **insight_id**: UUID of the insight
    """
    # Build query to get insight
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

    # Extract trend data from raw signal's extra_metadata
    trend_data = None
    if insight.raw_signal and insight.raw_signal.extra_metadata:
        trend_data = insight.raw_signal.extra_metadata.get('trend_data')

    # If trend data is not available, return empty array
    if not trend_data:
        return {
            "dates": [],
            "values": []
        }

    # Return the trend data
    return {
        "dates": trend_data.get("dates", []),
        "values": trend_data.get("values", [])
    }


@router.get("/{insight_id}/trend-stream")
@limiter.limit("5/minute")
async def stream_trend_data(
    request: Request,
    insight_id: UUID,
):
    """
    Stream real-time trend data updates for an insight using Server-Sent Events (SSE).

    This endpoint streams new trend data points as they become available from the
    hourly trends update task. Clients should use EventSource to consume this stream.

    IMPORTANT: Does NOT hold database connection indefinitely. Creates new session per poll.

    - **insight_id**: UUID of the insight to stream trend data for

    Returns:
        StreamingResponse with SSE format:
        event: trend-update
        data: {"timestamp": "2026-01-28T12:00:00", "value": 85}
    """
    import time

    from app.db.session import AsyncSessionLocal

    async def event_generator():
        """
        Generator function that yields Server-Sent Events for real-time trend updates.

        Polls the database every 60 seconds for new trend data points and yields them
        as SSE events. Creates NEW database session per iteration to avoid starving pool.
        """
        # Track last seen timestamp to only send new data
        last_timestamp = None
        max_duration = settings.sse_max_duration
        start_time = time.time()

        try:
            while True:
                # Check if client disconnected
                if await request.is_disconnected():
                    logger.info(f"SSE client disconnected: insight {insight_id}")
                    break

                # Check max duration
                if time.time() - start_time > max_duration:
                    logger.info(f"SSE stream max duration reached: insight {insight_id}")
                    yield "event: close\ndata: {\"message\": \"Maximum stream duration reached. Please reconnect.\"}\n\n"
                    break

                # Create NEW session for each iteration (don't hold connection)
                async with AsyncSessionLocal() as db:
                    # Fetch insight with raw signal
                    query = (
                        select(Insight)
                        .options(selectinload(Insight.raw_signal))
                        .where(Insight.id == insight_id)
                    )

                    result = await db.execute(query)
                    insight = result.scalar_one_or_none()

                    if not insight or not insight.raw_signal:
                        yield "event: error\ndata: {\"error\": \"Insight not found\"}\n\n"
                        break

                    # Extract realtime trend data
                    extra_metadata = insight.raw_signal.extra_metadata or {}
                    realtime_data = extra_metadata.get("trend_data_realtime", {})
                    timestamps = realtime_data.get("timestamps", [])
                    values = realtime_data.get("values", [])

                    if not timestamps or not values:
                        # Send initial message that realtime data is not available yet
                        yield "event: info\ndata: {\"message\": \"Waiting for real-time data...\"}\n\n"
                        await asyncio.sleep(60)
                        continue

                    # Find new data points (timestamps after last_timestamp)
                    new_data_points = []
                    for ts, val in zip(timestamps, values):
                        if last_timestamp is None or ts > last_timestamp:
                            new_data_points.append({"timestamp": ts, "value": val})

                    # Yield new data points as SSE events
                    if new_data_points:
                        for data_point in new_data_points:
                            event_data = json.dumps(data_point)
                            yield f"event: trend-update\ndata: {event_data}\n\n"
                            last_timestamp = data_point["timestamp"]

                            logger.debug(
                                f"Streamed trend update for insight {insight_id}: "
                                f"timestamp={data_point['timestamp']}, value={data_point['value']}"
                            )

                    # Send heartbeat to keep connection alive
                    else:
                        yield f"event: heartbeat\ndata: {{\"timestamp\": \"{datetime.now(UTC).isoformat()}\"}}\n\n"

                # Session auto-closed here (connection returned to pool)

                # Poll every 60 seconds (aligned with hourly task)
                await asyncio.sleep(60)

        except asyncio.CancelledError:
            logger.info(f"SSE stream cancelled for insight {insight_id}")
            yield "event: close\ndata: {\"message\": \"Stream closed\"}\n\n"
        except Exception as e:
            logger.error(f"Error in SSE stream for insight {insight_id}: {e}", exc_info=True)
            yield "event: error\ndata: {\"error\": \"Internal server error\"}\n\n"
        finally:
            logger.info(f"SSE stream ended for insight {insight_id}")

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",  # Disable nginx buffering
        },
    )


@router.get("/{insight_id}/predictions")
async def get_trend_predictions(
    insight_id: UUID,
    periods: Annotated[int, Query(ge=1, le=30, description="Days to forecast ahead")] = 7,
    db: AsyncSession = Depends(get_db),
) -> dict:
    """
    Get AI-powered trend predictions for an insight.

    Uses Facebook Prophet to generate time-series forecasts based on historical
    Google Trends data. Returns 7-day (default) ahead predictions with confidence
    intervals.

    **Prediction Model:**
    - Algorithm: Prophet (Facebook)
    - Training Data: Historical trend data (90+ days recommended)
    - Accuracy: MAPE typically <20% for trends with clear patterns

    **Caching:**
    - Predictions are cached in insights.trend_predictions for 24 hours
    - Regenerated daily during hourly trends update task

    - **insight_id**: UUID of the insight to predict
    - **periods**: Number of days to forecast (default: 7, max: 30)

    Returns:
        Prediction data with dates, values, and confidence intervals
    """
    # Fetch insight with raw signal
    query = (
        select(Insight)
        .options(selectinload(Insight.raw_signal))
        .where(Insight.id == insight_id)
    )

    result = await db.execute(query)
    insight = result.scalar_one_or_none()

    if not insight or not insight.raw_signal:
        logger.warning(f"Insight not found for predictions: {insight_id}")
        raise HTTPException(status_code=404, detail="Insight not found")

    # Check if predictions are cached and recent (< 24 hours old)
    if insight.trend_predictions:
        forecast_date_str = insight.trend_predictions.get("metadata", {}).get("forecast_date")
        if forecast_date_str:
            forecast_date = datetime.fromisoformat(forecast_date_str)
            age_hours = (datetime.now(UTC) - forecast_date).total_seconds() / 3600

            if age_hours < 24:
                logger.info(
                    f"Returning cached predictions for insight {insight_id} "
                    f"(age: {age_hours:.1f} hours)"
                )
                return insight.trend_predictions

    # Extract historical trend data from raw signal
    extra_metadata = insight.raw_signal.extra_metadata or {}

    # Try realtime data first (hourly updates), fallback to standard trend_data
    trend_data = extra_metadata.get("trend_data_realtime") or extra_metadata.get("trend_data")

    if not trend_data or not trend_data.get("dates") or not trend_data.get("values"):
        raise HTTPException(
            status_code=400,
            detail="No historical trend data available for this insight"
        )

    # Convert timestamp format to date format if needed (for realtime data)
    if "timestamps" in trend_data:
        # Realtime data uses timestamps, convert to dates
        trend_data = {
            "dates": [
                datetime.fromisoformat(ts).strftime("%Y-%m-%d")
                for ts in trend_data["timestamps"]
            ],
            "values": trend_data["values"]
        }

    # Generate predictions using Prophet
    try:
        predictions = await generate_trend_predictions(trend_data, periods)

        # Cache predictions in database
        insight.trend_predictions = predictions
        await db.commit()

        logger.info(
            f"Generated {periods}-day predictions for insight {insight_id} "
            f"(MAPE: {predictions['model_accuracy']['mape']:.2%})"
        )

        return predictions

    except ValueError as e:
        logger.warning(f"Prediction failed for insight {insight_id}: {e}")
        raise HTTPException(
            status_code=400,
            detail="Invalid prediction parameters. Please check your input."
        )
    except Exception as e:
        logger.error(f"Unexpected error generating predictions: {type(e).__name__} - {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail="Failed to generate predictions. Please try again later."
        )


# ============================================================================
# PHASE 9.2: COMPETITIVE INTELLIGENCE ENDPOINTS
# ============================================================================

@router.post("/{insight_id}/competitors/scrape")
async def scrape_competitors(
    insight_id: UUID,
    competitor_urls: list[str],
    current_user: CurrentUser,
    db: AsyncSession = Depends(get_db),
) -> dict:
    """
    Scrape competitor websites and create CompetitorProfile records.

    - **insight_id**: Insight ID to associate competitors with
    - **competitor_urls**: List of competitor website URLs to scrape

    Returns count of successfully scraped competitors.

    Example request body:
    ```json
    ["https://notion.com", "https://linear.app", "https://airtable.com"]
    ```
    """
    from app.services.competitor_scraper import scrape_competitor_batch

    # Verify insight exists
    stmt = select(Insight).where(Insight.id == insight_id)
    result = await db.execute(stmt)
    insight = result.scalar_one_or_none()

    if not insight:
        raise HTTPException(status_code=404, detail="Insight not found")

    # Validate URLs
    if not competitor_urls:
        raise HTTPException(status_code=400, detail="At least one competitor URL is required")

    if len(competitor_urls) > 10:
        raise HTTPException(status_code=400, detail="Maximum 10 competitors can be scraped at once")

    # Scrape competitors
    try:
        profiles = await scrape_competitor_batch(
            competitor_urls=competitor_urls,
            insight_id=insight_id,
            session=db,
        )

        success_count = sum(1 for p in profiles if p.scrape_status == "success")
        failed_count = len(profiles) - success_count

        logger.info(
            f"Scraped {len(competitor_urls)} competitors for insight {insight_id}: "
            f"{success_count} success, {failed_count} failed"
        )

        return {
            "total_requested": len(competitor_urls),
            "success_count": success_count,
            "failed_count": failed_count,
            "profiles": [
                {
                    "id": str(p.id),
                    "name": p.name,
                    "url": p.url,
                    "status": p.scrape_status,
                    "error": p.scrape_error,
                }
                for p in profiles
            ],
        }

    except Exception as e:
        logger.error(f"Competitor scraping failed: {type(e).__name__} - {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail="Failed to scrape competitors. Please try again."
        )


@router.get("/{insight_id}/competitors")
async def list_competitors(
    insight_id: UUID,
    current_user: CurrentUser,
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """
    List all competitors for an insight.

    Returns competitor profiles with latest snapshot data.
    """
    from app.models.competitor_profile import CompetitorProfile

    # Verify insight exists
    stmt = select(Insight).where(Insight.id == insight_id)
    result = await db.execute(stmt)
    insight = result.scalar_one_or_none()

    if not insight:
        raise HTTPException(status_code=404, detail="Insight not found")

    # Count total
    total = await db.scalar(
        select(func.count(CompetitorProfile.id)).where(
            CompetitorProfile.insight_id == insight_id
        )
    ) or 0

    # Get competitors with pagination
    stmt = (
        select(CompetitorProfile)
        .where(CompetitorProfile.insight_id == insight_id)
        .order_by(CompetitorProfile.created_at.desc())
        .limit(limit)
        .offset(offset)
    )

    result = await db.execute(stmt)
    competitors = result.scalars().all()

    return {
        "competitors": [
            CompetitorListItemResponse(
                id=c.id,
                name=c.name,
                url=c.url,
                description=c.description,
                value_proposition=c.value_proposition,
                target_audience=c.target_audience,
                market_position=c.market_position,
                metrics=c.metrics,
                features=c.features,
                strengths=c.strengths,
                weaknesses=c.weaknesses,
                positioning_x=c.positioning_x,
                positioning_y=c.positioning_y,
                last_scraped_at=c.last_scraped_at,
                scrape_status=c.scrape_status,
                created_at=c.created_at,
                updated_at=c.updated_at,
            ).model_dump()
            for c in competitors
        ],
        "total": total,
        "limit": limit,
        "offset": offset,
    }


@router.get("/{insight_id}/competitors/{competitor_id}", response_model=CompetitorDetailResponse)
async def get_competitor_detail(
    insight_id: UUID,
    competitor_id: UUID,
    current_user: CurrentUser,
    db: AsyncSession = Depends(get_db),
) -> CompetitorDetailResponse:
    """
    Get detailed competitor profile with snapshot history.

    Returns full competitor data including all historical snapshots.
    """
    from app.models.competitor_profile import CompetitorProfile

    # Get competitor profile
    stmt = (
        select(CompetitorProfile)
        .where(CompetitorProfile.id == competitor_id)
        .where(CompetitorProfile.insight_id == insight_id)
        .options(selectinload(CompetitorProfile.snapshots))
    )

    result = await db.execute(stmt)
    competitor = result.scalar_one_or_none()

    if not competitor:
        raise HTTPException(status_code=404, detail="Competitor not found")

    logger.info(f"Retrieved competitor {competitor_id} for insight {insight_id}")

    snapshots = sorted(competitor.snapshots, key=lambda x: x.scraped_at, reverse=True)[:50]

    return CompetitorDetailResponse(
        id=competitor.id,
        insight_id=competitor.insight_id,
        name=competitor.name,
        url=competitor.url,
        description=competitor.description,
        value_proposition=competitor.value_proposition,
        target_audience=competitor.target_audience,
        market_position=competitor.market_position,
        metrics=competitor.metrics,
        features=competitor.features,
        strengths=competitor.strengths,
        weaknesses=competitor.weaknesses,
        positioning_x=competitor.positioning_x,
        positioning_y=competitor.positioning_y,
        last_scraped_at=competitor.last_scraped_at,
        scrape_status=competitor.scrape_status,
        scrape_error=competitor.scrape_error,
        analysis_generated_at=competitor.analysis_generated_at,
        analysis_model=competitor.analysis_model,
        created_at=competitor.created_at,
        updated_at=competitor.updated_at,
        snapshots=[
            CompetitorSnapshotResponse(
                id=s.id,
                snapshot_data=s.snapshot_data,
                changes_detected=s.changes_detected,
                scraped_at=s.scraped_at,
                scrape_method=s.scrape_method,
            )
            for s in snapshots
        ],
    )


@router.delete("/{insight_id}/competitors/{competitor_id}", response_model=MessageResponse)
async def delete_competitor(
    insight_id: UUID,
    competitor_id: UUID,
    admin: AdminUser,
    db: AsyncSession = Depends(get_db),
) -> MessageResponse:
    """
    Delete a competitor profile.

    This will also delete all associated snapshots (cascade delete).
    """
    from app.models.competitor_profile import CompetitorProfile

    # Get competitor profile
    stmt = (
        select(CompetitorProfile)
        .where(CompetitorProfile.id == competitor_id)
        .where(CompetitorProfile.insight_id == insight_id)
    )

    result = await db.execute(stmt)
    competitor = result.scalar_one_or_none()

    if not competitor:
        raise HTTPException(status_code=404, detail="Competitor not found")

    # Delete competitor (cascades to snapshots)
    await db.delete(competitor)
    await db.commit()

    logger.info(f"Deleted competitor {competitor_id} from insight {insight_id}")

    return MessageResponse(message=f"Competitor '{competitor.name}' deleted successfully")


@router.post("/{insight_id}/competitors/analyze")
async def analyze_competitors_ai(
    insight_id: UUID,
    current_user: CurrentUser,
    db: AsyncSession = Depends(get_db),
) -> dict:
    """
    Run AI competitive intelligence analysis on competitors.

    Generates:
    - Competitor strengths and weaknesses
    - Market positioning (price vs features matrix)
    - Market gap analysis
    - Differentiation opportunities
    - Executive summary

    Updates competitor profiles with analysis results.

    Returns full CompetitiveIntelligenceReport.
    """
    from app.agents.competitive_intel_agent import analyze_competitors_with_retry

    # Verify insight exists
    stmt = select(Insight).where(Insight.id == insight_id)
    result = await db.execute(stmt)
    insight = result.scalar_one_or_none()

    if not insight:
        raise HTTPException(status_code=404, detail="Insight not found")

    # Run AI analysis
    try:
        report = await analyze_competitors_with_retry(
            insight_id=insight_id,
            session=db,
            max_retries=3,
        )

        logger.info(
            f"Competitive analysis generated for insight {insight_id}: "
            f"{report.total_competitors} competitors, "
            f"{len(report.market_gap_analysis.gaps)} gaps identified"
        )

        return report.model_dump()

    except ValueError as e:
        logger.warning(f"Competitive analysis failed: {e}")
        raise HTTPException(status_code=400, detail="Invalid analysis parameters. Please check your input.")

    except Exception as e:
        logger.error(f"Unexpected error during competitive analysis: {type(e).__name__} - {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail="Failed to generate competitive analysis. Please try again later."
        )


# ============================================================================
# PHASE K.2: SOCIAL PROOF / ENGAGEMENT METRICS
# ============================================================================

@router.get("/{insight_id}/engagement")
async def get_insight_engagement(
    insight_id: UUID,
    db: AsyncSession = Depends(get_db),
) -> dict:
    """
    Return engagement metrics for an insight.

    Aggregates interaction data from InsightInteraction and SavedInsight tables
    to provide social proof metrics (view count, save count, chat count, etc.).

    No authentication required -- public endpoint for social proof display.

    - **insight_id**: UUID of the insight
    """
    from app.models.insight_interaction import InsightInteraction
    from app.models.saved_insight import SavedInsight

    # Verify insight exists
    insight = await db.get(Insight, insight_id)
    if not insight:
        raise HTTPException(status_code=404, detail="Insight not found")

    # Count interactions by type
    interaction_counts_query = (
        select(
            InsightInteraction.interaction_type,
            func.count(InsightInteraction.id).label("count"),
        )
        .where(InsightInteraction.insight_id == insight_id)
        .group_by(InsightInteraction.interaction_type)
    )
    result = await db.execute(interaction_counts_query)
    interaction_counts = {row.interaction_type: row.count for row in result.all()}

    # Count saves from SavedInsight table
    save_count = await db.scalar(
        select(func.count(SavedInsight.id)).where(
            SavedInsight.insight_id == insight_id
        )
    ) or 0

    # Count proof signals if available (evidence data points)
    evidence_count = 0
    if insight.proof_signals and isinstance(insight.proof_signals, list):
        evidence_count = len(insight.proof_signals)

    logger.info(f"Engagement metrics for insight {insight_id}: {interaction_counts}")

    return {
        "view_count": interaction_counts.get("view", 0),
        "save_count": save_count,
        "share_count": interaction_counts.get("share", 0),
        "claim_count": interaction_counts.get("claim", 0),
        "export_count": interaction_counts.get("export", 0),
        "interested_count": interaction_counts.get("interested", 0),
        "evidence_count": evidence_count,
    }
