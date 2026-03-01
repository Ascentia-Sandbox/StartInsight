"""Backfill trend_data for all trends using PyTrends.

Fetches real Google Trends interest-over-time data for each trend's keyword
and stores it in trend.trend_data as {"dates": [...], "values": [...]}.

Usage:
    cd backend && python -m scripts.backfill_trends_table
"""

import asyncio
import logging
import time

from pytrends.request import TrendReq
from sqlalchemy import select

from app.db.session import AsyncSessionLocal
from app.models.trend import Trend

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)

BATCH_SIZE = 5
REQUEST_DELAY = 2.0  # seconds between Google Trends requests


def fetch_trend_data(keyword: str, timeframe: str = "today 1-m") -> dict | None:
    """Fetch Google Trends interest_over_time for a keyword.

    Returns {"dates": [...], "values": [...]} or None on failure.
    """
    try:
        pytrends = TrendReq(hl="en-US", tz=360, timeout=(10, 30), retries=0)
        pytrends.build_payload(kw_list=[keyword], timeframe=timeframe)
        df = pytrends.interest_over_time()

        if df.empty or keyword not in df.columns:
            logger.warning(f"No data for keyword: {keyword}")
            return None

        dates = [idx.strftime("%Y-%m-%d") for idx in df.index]
        values = [int(v) for v in df[keyword].values]

        return {"dates": dates, "values": values, "source": "google_trends"}

    except Exception as e:
        logger.error(f"PyTrends error for '{keyword}': {type(e).__name__}: {e}")
        return None


async def backfill():
    """Main backfill routine."""
    async with AsyncSessionLocal() as session:
        # Get all trends where trend_data is empty or null
        query = select(Trend).order_by(Trend.created_at.desc())
        result = await session.execute(query)
        trends = list(result.scalars().all())

        logger.info(f"Found {len(trends)} trends to process")

        updated = 0
        skipped = 0
        failed = 0

        for i, trend in enumerate(trends):
            # Skip if trend data already exists with real dates
            existing_data = trend.trend_data or {}
            if existing_data.get("dates") and len(existing_data["dates"]) >= 7:
                logger.info(f"[{i+1}/{len(trends)}] Already has trend data: {trend.keyword}")
                skipped += 1
                continue

            logger.info(f"[{i+1}/{len(trends)}] Fetching trends for '{trend.keyword}'")

            # Rate limit
            time.sleep(REQUEST_DELAY)

            trend_data = fetch_trend_data(trend.keyword)
            if not trend_data:
                failed += 1
                continue

            # Update trend.trend_data
            trend.trend_data = trend_data
            updated += 1

            # Commit in batches
            if updated % BATCH_SIZE == 0:
                await session.commit()
                logger.info(f"Committed batch ({updated} updated so far)")

        # Final commit
        await session.commit()
        logger.info(
            f"Backfill complete: {updated} updated, {skipped} skipped, {failed} failed "
            f"out of {len(trends)} total"
        )


if __name__ == "__main__":
    asyncio.run(backfill())
