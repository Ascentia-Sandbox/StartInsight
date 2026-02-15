"""Market Pulse API — real-time pipeline health and trending data.

Public endpoint (no auth) designed to drive organic SEO traffic.
"""

import logging
from datetime import UTC, datetime, timedelta

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy import func, select, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.models.insight import Insight
from app.models.raw_signal import RawSignal

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/pulse", tags=["pulse"])


class TrendingKeyword(BaseModel):
    keyword: str
    volume: str | None = None
    growth: str | None = None


class PulseResponse(BaseModel):
    signals_24h: int
    insights_24h: int
    total_insights: int
    trending_keywords: list[TrendingKeyword]
    hottest_markets: list[str]
    top_sources: dict[str, int]
    last_updated: str


@router.get("", response_model=PulseResponse)
async def get_market_pulse(db: AsyncSession = Depends(get_db)) -> PulseResponse:
    """
    Get real-time market pulse data.

    Public endpoint — no authentication required. Designed for:
    - `/pulse` landing page with auto-refresh
    - SEO traffic from "startup trends today" queries
    - Demonstrating pipeline activity to visitors
    """
    now = datetime.now(UTC)
    day_ago = now - timedelta(hours=24)

    # Signals collected in last 24h
    signals_result = await db.execute(
        select(func.count()).where(RawSignal.created_at >= day_ago)
    )
    signals_24h = signals_result.scalar() or 0

    # Insights generated in last 24h
    insights_24h_result = await db.execute(
        select(func.count()).where(Insight.created_at >= day_ago)
    )
    insights_24h = insights_24h_result.scalar() or 0

    # Total insights
    total_result = await db.execute(select(func.count()).select_from(Insight))
    total_insights = total_result.scalar() or 0

    # Top sources in last 24h
    sources_result = await db.execute(
        select(RawSignal.source, func.count().label("cnt"))
        .where(RawSignal.created_at >= day_ago)
        .group_by(RawSignal.source)
        .order_by(text("cnt DESC"))
        .limit(6)
    )
    top_sources = {row.source: row.cnt for row in sources_result.fetchall()}

    # Trending keywords from recent insights (JSONB extraction)
    trending_keywords: list[TrendingKeyword] = []
    try:
        kw_result = await db.execute(
            select(Insight.trend_keywords)
            .where(Insight.trend_keywords.isnot(None))
            .order_by(Insight.created_at.desc())
            .limit(10)
        )
        seen = set()
        for row in kw_result.fetchall():
            if not row[0]:
                continue
            for kw in row[0]:
                keyword = kw.get("keyword", "") if isinstance(kw, dict) else ""
                if keyword and keyword not in seen:
                    seen.add(keyword)
                    trending_keywords.append(TrendingKeyword(
                        keyword=keyword,
                        volume=kw.get("volume"),
                        growth=kw.get("growth"),
                    ))
                if len(trending_keywords) >= 10:
                    break
            if len(trending_keywords) >= 10:
                break
    except Exception as e:
        logger.debug(f"Could not extract trending keywords: {e}")

    # Hottest markets from recent insight market_size_estimate
    hottest_markets: list[str] = []
    try:
        markets_result = await db.execute(
            select(Insight.market_size_estimate, func.count().label("cnt"))
            .where(Insight.created_at >= now - timedelta(days=7))
            .where(Insight.market_size_estimate.isnot(None))
            .group_by(Insight.market_size_estimate)
            .order_by(text("cnt DESC"))
            .limit(5)
        )
        hottest_markets = [row.market_size_estimate for row in markets_result.fetchall()]
    except Exception as e:
        logger.debug(f"Could not extract hottest markets: {e}")

    return PulseResponse(
        signals_24h=signals_24h,
        insights_24h=insights_24h,
        total_insights=total_insights,
        trending_keywords=trending_keywords,
        hottest_markets=hottest_markets,
        top_sources=top_sources,
        last_updated=now.isoformat(),
    )
