"""API endpoints for Trends database (Phase 12.3: IdeaBrowser Replication).

Provides CRUD operations for the 180+ trending keywords with volume/growth metrics.
Sprint 3.1: Adds predictive trend analytics with Prophet forecasting.
"""

import logging
import random
from datetime import UTC, datetime, timedelta
from typing import Annotated, Any, Literal
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import AdminUser
from app.api.utils import escape_like
from app.core.rate_limits import limiter
from app.db.session import get_db
from app.models.trend import Trend
from app.schemas.public_content import (
    TrendCreate,
    TrendListResponse,
    TrendResponse,
    TrendUpdate,
)
from app.services.trend_prediction import generate_trend_predictions

# ============================================================================
# PREDICTION SCHEMAS
# ============================================================================

class TrendPredictionResponse(BaseModel):
    """Response schema for trend predictions"""
    keyword: str = Field(..., description="Trend keyword")
    current_volume: int = Field(..., description="Current search volume")
    predictions: dict[str, Any] = Field(..., description="Prediction data with dates, values, confidence intervals")
    velocity_alert: bool = Field(default=False, description="Whether trend velocity spike detected")
    velocity_change: float = Field(default=0.0, description="7-day velocity change percentage")

    model_config = ConfigDict(from_attributes=True)


class TrendComparisonResponse(BaseModel):
    """Response schema for comparing multiple trends"""
    keywords: list[str] = Field(..., description="Compared keywords")
    comparison_data: list[dict[str, Any]] = Field(..., description="Comparison data for each keyword")
    winner: str | None = Field(None, description="Keyword with highest predicted growth")
    analysis_summary: str = Field(..., description="Brief comparison analysis")

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/trends", tags=["trends"])


@router.get("", response_model=TrendListResponse)
@limiter.limit("30/minute")
async def list_trends(
    request: Request,
    category: Annotated[
        str | None, Query(description="Filter by category")
    ] = None,
    sort: Annotated[
        Literal["recent", "volume", "growth"] | None,
        Query(description="Sort by: recent, volume, or growth"),
    ] = "recent",
    featured: Annotated[
        bool | None, Query(description="Filter by featured status")
    ] = None,
    search: Annotated[
        str | None, Query(description="Search by keyword")
    ] = None,
    limit: Annotated[int, Query(ge=1, le=100, description="Number of results")] = 12,
    offset: Annotated[int, Query(ge=0, description="Pagination offset")] = 0,
    db: AsyncSession = Depends(get_db),
) -> TrendListResponse:
    """
    List all trends with filtering, sorting, and pagination.

    Only returns published trends for public access.

    - **category**: Filter by trend category (e.g., 'AI', 'SaaS')
    - **sort**: Sort by 'recent' (default), 'volume', or 'growth'
    - **featured**: Filter by featured status
    - **search**: Search in keyword
    - **limit**: Number of results per page (default 12, max 100)
    - **offset**: Pagination offset
    """
    # Build query - only published trends
    query = select(Trend).where(Trend.is_published == True)

    # Apply filters
    if category:
        query = query.where(Trend.category == category)
    if featured is not None:
        query = query.where(Trend.is_featured == featured)
    if search:
        query = query.where(Trend.keyword.ilike(f"%{escape_like(search)}%"))

    # Apply sorting
    if sort == "volume":
        query = query.order_by(Trend.search_volume.desc())
    elif sort == "growth":
        query = query.order_by(Trend.growth_percentage.desc())
    else:  # recent (default)
        query = query.order_by(Trend.created_at.desc())

    # Pagination
    query = query.limit(limit).offset(offset)

    # Execute
    result = await db.execute(query)
    trends = result.scalars().all()

    # Get total count
    count_query = select(func.count(Trend.id)).where(Trend.is_published == True)
    if category:
        count_query = count_query.where(Trend.category == category)
    if featured is not None:
        count_query = count_query.where(Trend.is_featured == featured)
    if search:
        count_query = count_query.where(Trend.keyword.ilike(f"%{escape_like(search)}%"))

    total = await db.scalar(count_query)

    logger.info(f"Listed {len(trends)} trends (category={category}, sort={sort}, total={total})")

    return TrendListResponse(
        trends=[TrendResponse.model_validate(t) for t in trends],
        total=total or 0,
        limit=limit,
        offset=offset,
    )


@router.get("/categories", response_model=list[str])
@limiter.limit("30/minute")
async def get_trend_categories(
    request: Request,
    db: AsyncSession = Depends(get_db),
) -> list[str]:
    """
    Get all unique trend categories.

    Useful for building filter dropdowns.
    """
    query = (
        select(Trend.category)
        .where(Trend.is_published == True)
        .distinct()
        .order_by(Trend.category)
    )

    result = await db.execute(query)
    categories = result.scalars().all()

    return list(categories)


@router.get("/{trend_id}", response_model=TrendResponse)
async def get_trend(
    trend_id: UUID,
    db: AsyncSession = Depends(get_db),
) -> TrendResponse:
    """
    Get a single trend by ID.

    Only returns if published (or admin access).
    """
    query = select(Trend).where(Trend.id == trend_id, Trend.is_published == True)
    result = await db.execute(query)
    trend = result.scalar_one_or_none()

    if not trend:
        raise HTTPException(status_code=404, detail="Trend not found")

    return TrendResponse.model_validate(trend)


@router.post("", response_model=TrendResponse, status_code=201)
async def create_trend(
    trend_data: TrendCreate,
    admin: AdminUser,
    db: AsyncSession = Depends(get_db),
) -> TrendResponse:
    """
    Create a new trend (admin only).
    """

    # Check for duplicate keyword
    existing_query = select(Trend).where(Trend.keyword == trend_data.keyword)
    existing = await db.execute(existing_query)
    if existing.scalar_one_or_none():
        raise HTTPException(
            status_code=400, detail=f"Trend with keyword '{trend_data.keyword}' already exists"
        )

    trend = Trend(**trend_data.model_dump())
    db.add(trend)
    await db.commit()
    await db.refresh(trend)

    logger.info(f"Created trend: {trend.keyword} (id={trend.id})")

    return TrendResponse.model_validate(trend)


@router.patch("/{trend_id}", response_model=TrendResponse)
async def update_trend(
    trend_id: UUID,
    trend_data: TrendUpdate,
    admin: AdminUser,
    db: AsyncSession = Depends(get_db),
) -> TrendResponse:
    """
    Update an existing trend (admin only).
    """

    query = select(Trend).where(Trend.id == trend_id)
    result = await db.execute(query)
    trend = result.scalar_one_or_none()

    if not trend:
        raise HTTPException(status_code=404, detail="Trend not found")

    # Check for duplicate keyword if updating
    update_data = trend_data.model_dump(exclude_unset=True)
    if "keyword" in update_data and update_data["keyword"] != trend.keyword:
        existing_query = select(Trend).where(Trend.keyword == update_data["keyword"])
        existing = await db.execute(existing_query)
        if existing.scalar_one_or_none():
            raise HTTPException(
                status_code=400,
                detail=f"Trend with keyword '{update_data['keyword']}' already exists",
            )

    # Update only provided fields
    for field, value in update_data.items():
        setattr(trend, field, value)

    await db.commit()
    await db.refresh(trend)

    logger.info(f"Updated trend: {trend.keyword} (id={trend.id})")

    return TrendResponse.model_validate(trend)


def _get_historical_data(
    trend: Trend, days: int = 30
) -> tuple[list[str], list[int]]:
    """Get historical dates and values from trend, generating synthetic data if needed."""
    trend_data = trend.trend_data or {}
    historical_dates = trend_data.get("dates", [])
    historical_values = trend_data.get("values", [])

    if len(historical_dates) >= 7:
        return historical_dates, historical_values

    base_volume = trend.search_volume or 50
    historical_dates = [
        (datetime.now(UTC) - timedelta(days=i)).strftime("%Y-%m-%d")
        for i in range(days, 0, -1)
    ]
    growth_rate = (trend.growth_percentage or 10) / 100
    historical_values = [
        max(1, int(base_volume * (1 - growth_rate * (days - i) / days) + random.uniform(-5, 5)))
        for i in range(days)
    ]
    return historical_dates, historical_values


def _calculate_velocity(historical_values: list[int], fallback: float) -> tuple[float, bool]:
    """Calculate 7-day velocity change and alert status."""
    if len(historical_values) >= 7:
        week_ago_value = historical_values[-7]
        current_value = historical_values[-1]
        velocity_change = ((current_value - week_ago_value) / max(week_ago_value, 1)) * 100
    else:
        velocity_change = fallback
    return round(velocity_change, 2), abs(velocity_change) > 50


# ============================================================================
# PREDICTION ENDPOINTS (Sprint 3.1)
# ============================================================================

@router.get("/predictions", response_model=list[TrendPredictionResponse])
async def get_trend_predictions(
    limit: Annotated[int, Query(ge=1, le=20, description="Number of trends to predict")] = 10,
    category: Annotated[str | None, Query(description="Filter by category")] = None,
    db: AsyncSession = Depends(get_db),
) -> list[TrendPredictionResponse]:
    """
    Get predictions for top trending keywords.

    Returns 7-day ahead forecasts with confidence intervals for the top N trends
    by search volume. Includes velocity alerts for rapidly accelerating trends.

    - **limit**: Number of trends to generate predictions for (default 10, max 20)
    - **category**: Filter by trend category
    """
    # Get top trends by volume
    query = select(Trend).where(Trend.is_published == True)
    if category:
        query = query.where(Trend.category == category)
    query = query.order_by(Trend.search_volume.desc()).limit(limit)

    result = await db.execute(query)
    trends = result.scalars().all()

    if not trends:
        return []

    predictions = []
    for trend in trends:
        try:
            historical_dates, historical_values = _get_historical_data(trend, days=30)

            prediction_result = await generate_trend_predictions(
                trend_data={"dates": historical_dates, "values": historical_values},
                periods=7,
            )

            velocity_change, velocity_alert = _calculate_velocity(
                historical_values, trend.growth_percentage or 0
            )

            predictions.append(TrendPredictionResponse(
                keyword=trend.keyword,
                current_volume=trend.search_volume or 0,
                predictions=prediction_result,
                velocity_alert=velocity_alert,
                velocity_change=velocity_change,
            ))

        except Exception as e:
            logger.warning(f"Failed to generate prediction for {trend.keyword}: {e}")
            predictions.append(TrendPredictionResponse(
                keyword=trend.keyword,
                current_volume=trend.search_volume or 0,
                predictions={
                    "dates": [],
                    "values": [],
                    "confidence_intervals": {"lower": [], "upper": []},
                    "model_accuracy": {"mape": 0, "rmse": 0},
                    "error": str(e),
                },
                velocity_alert=False,
                velocity_change=0.0,
            ))

    logger.info(f"Generated predictions for {len(predictions)} trends (category={category})")
    return predictions


@router.get("/predictions/{keyword}", response_model=TrendPredictionResponse)
async def get_trend_prediction_by_keyword(
    keyword: str,
    periods: Annotated[int, Query(ge=1, le=30, description="Forecast horizon in days")] = 7,
    db: AsyncSession = Depends(get_db),
) -> TrendPredictionResponse:
    """
    Get prediction for a specific trend keyword.

    Returns N-day ahead forecast with confidence intervals and model accuracy metrics.

    - **keyword**: Trend keyword to predict
    - **periods**: Number of days to forecast (default 7, max 30)
    """
    # Find trend by keyword
    query = select(Trend).where(
        Trend.keyword.ilike(f"%{escape_like(keyword)}%"),
        Trend.is_published == True,
    )
    result = await db.execute(query)
    trend = result.scalar_one_or_none()

    if not trend:
        raise HTTPException(status_code=404, detail=f"Trend '{keyword}' not found")

    historical_dates, historical_values = _get_historical_data(trend, days=90)

    try:
        prediction_result = await generate_trend_predictions(
            trend_data={"dates": historical_dates, "values": historical_values},
            periods=periods,
        )
    except Exception as e:
        logger.error(f"Prediction failed for {keyword}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Prediction failed. Please try again.")

    velocity_change, velocity_alert = _calculate_velocity(
        historical_values, trend.growth_percentage or 0
    )

    logger.info(f"Generated {periods}-day prediction for '{trend.keyword}'")

    return TrendPredictionResponse(
        keyword=trend.keyword,
        current_volume=trend.search_volume or 0,
        predictions=prediction_result,
        velocity_alert=velocity_alert,
        velocity_change=round(velocity_change, 2),
    )


@router.post("/compare", response_model=TrendComparisonResponse)
async def compare_trends(
    keywords: Annotated[list[str], Query(description="Keywords to compare", min_length=2, max_length=5)],
    db: AsyncSession = Depends(get_db),
) -> TrendComparisonResponse:
    """
    Compare multiple trends side-by-side with predictions.

    Compares 2-5 keywords and identifies the fastest growing trend.

    - **keywords**: List of 2-5 keywords to compare
    """
    if len(keywords) < 2:
        raise HTTPException(status_code=400, detail="At least 2 keywords required for comparison")
    if len(keywords) > 5:
        raise HTTPException(status_code=400, detail="Maximum 5 keywords can be compared")

    # Fetch trends for all keywords
    query = select(Trend).where(
        Trend.keyword.in_(keywords),
        Trend.is_published == True,
    )
    result = await db.execute(query)
    trends = result.scalars().all()

    if not trends:
        raise HTTPException(status_code=404, detail="No matching trends found")

    found_keywords = [t.keyword for t in trends]
    missing = set(keywords) - set(found_keywords)
    if missing:
        logger.warning(f"Some keywords not found: {missing}")

    comparison_data = []
    max_growth = -float('inf')
    winner = None

    for trend in trends:
        historical_dates, historical_values = _get_historical_data(trend, days=30)

        try:
            prediction_result = await generate_trend_predictions(
                trend_data={"dates": historical_dates, "values": historical_values},
                periods=7,
            )
            predicted_growth = (
                (prediction_result["values"][-1] - trend.search_volume)
                / max(trend.search_volume, 1) * 100
                if prediction_result["values"]
                else 0
            )
        except Exception as e:
            logger.warning(f"Prediction failed for {trend.keyword}: {e}")
            prediction_result = {}
            predicted_growth = trend.growth_percentage or 0

        if predicted_growth > max_growth:
            max_growth = predicted_growth
            winner = trend.keyword

        comparison_data.append({
            "keyword": trend.keyword,
            "category": trend.category,
            "current_volume": trend.search_volume,
            "growth_percentage": trend.growth_percentage,
            "predicted_growth": round(predicted_growth, 2),
            "predictions": prediction_result,
        })

    # Generate analysis summary
    summary_parts = [f"Compared {len(trends)} trends."]
    if winner:
        summary_parts.append(f"'{winner}' shows highest predicted growth at {max_growth:.1f}%.")
    volumes = [d["current_volume"] for d in comparison_data]
    highest_volume_kw = comparison_data[volumes.index(max(volumes))]["keyword"]
    summary_parts.append(f"'{highest_volume_kw}' has highest current volume.")

    logger.info(f"Compared {len(trends)} trends: {found_keywords}")

    return TrendComparisonResponse(
        keywords=found_keywords,
        comparison_data=comparison_data,
        winner=winner,
        analysis_summary=" ".join(summary_parts),
    )


@router.delete("/{trend_id}", status_code=204)
async def delete_trend(
    trend_id: UUID,
    admin: AdminUser,
    db: AsyncSession = Depends(get_db),
) -> None:
    """
    Delete a trend (admin only).
    """

    query = select(Trend).where(Trend.id == trend_id)
    result = await db.execute(query)
    trend = result.scalar_one_or_none()

    if not trend:
        raise HTTPException(status_code=404, detail="Trend not found")

    await db.delete(trend)
    await db.commit()

    logger.info(f"Deleted trend: {trend.keyword} (id={trend_id})")
