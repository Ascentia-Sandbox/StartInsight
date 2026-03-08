"""Backfill trend data for all insights using PyTrends.

Fetches real Google Trends data for each insight's primary trend keyword
and stores it in raw_signal.extra_metadata['trend_data'].

Usage:
    cd backend && python -m scripts.backfill_trend_data
"""

import asyncio
import logging
import time

from pytrends.request import TrendReq
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.db.session import AsyncSessionLocal
from app.models.insight import Insight

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)

BATCH_SIZE = 5
REQUEST_DELAY = 2.0  # seconds between Google Trends requests


def fetch_trend_data(keyword: str, timeframe: str = "today 1-m") -> dict | None:
    """Fetch Google Trends interest_over_time for a keyword.

    Returns {"dates": [...], "values": [...]} or None on failure.
    """
    try:
        # retries=0 to avoid pytrends bug with urllib3 2.x (method_whitelist removed)
        pytrends = TrendReq(hl="en-US", tz=360, timeout=(10, 30), retries=0)
        pytrends.build_payload(kw_list=[keyword], timeframe=timeframe)
        df = pytrends.interest_over_time()

        if df.empty or keyword not in df.columns:
            logger.warning(f"No data for keyword: {keyword}")
            return None

        dates = [idx.strftime("%Y-%m-%d") for idx in df.index]
        values = [int(v) for v in df[keyword].values]

        return {"dates": dates, "values": values}

    except Exception as e:
        logger.error(f"PyTrends error for '{keyword}': {type(e).__name__}: {e}")
        return None


async def backfill():
    """Main backfill routine."""
    async with AsyncSessionLocal() as session:
        # Get all insights with their raw signals and trend keywords
        query = (
            select(Insight)
            .options(selectinload(Insight.raw_signal))
            .order_by(Insight.created_at.desc())
        )
        result = await session.execute(query)
        insights = list(result.scalars().all())

        logger.info(f"Found {len(insights)} insights to process")

        updated = 0
        skipped = 0
        failed = 0

        for i, insight in enumerate(insights):
            # Skip if no raw signal
            if not insight.raw_signal:
                logger.warning(f"[{i+1}/{len(insights)}] No raw signal for {insight.id}")
                skipped += 1
                continue

            # Skip if trend data already exists
            extra = insight.raw_signal.extra_metadata or {}
            if extra.get("trend_data") and extra["trend_data"].get("dates"):
                logger.info(f"[{i+1}/{len(insights)}] Already has trend data: {insight.id}")
                skipped += 1
                continue

            # Get keyword from trend_keywords or proposed_solution
            keyword = None
            if insight.trend_keywords and isinstance(insight.trend_keywords, list):
                for kw in insight.trend_keywords:
                    if isinstance(kw, dict) and kw.get("keyword"):
                        keyword = kw["keyword"]
                        break
            if not keyword:
                # Fallback: use first 3 words of proposed_solution
                words = (insight.proposed_solution or "").split()[:4]
                keyword = " ".join(words) if words else None

            if not keyword:
                logger.warning(f"[{i+1}/{len(insights)}] No keyword for {insight.id}")
                skipped += 1
                continue

            logger.info(f"[{i+1}/{len(insights)}] Fetching trends for '{keyword}' (insight {insight.id})")

            # Rate limit
            time.sleep(REQUEST_DELAY)

            trend_data = fetch_trend_data(keyword)
            if not trend_data:
                failed += 1
                continue

            # Update raw_signal.extra_metadata
            new_metadata = dict(extra)
            new_metadata["trend_data"] = trend_data
            insight.raw_signal.extra_metadata = new_metadata

            updated += 1

            # Commit in batches
            if updated % BATCH_SIZE == 0:
                await session.commit()
                logger.info(f"Committed batch ({updated} updated so far)")

        # Final commit
        await session.commit()
        logger.info(
            f"Backfill complete: {updated} updated, {skipped} skipped, {failed} failed "
            f"out of {len(insights)} total"
        )


if __name__ == "__main__":
    asyncio.run(backfill())
