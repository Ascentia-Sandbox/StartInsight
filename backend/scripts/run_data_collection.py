#!/usr/bin/env python3
"""
Run data collection pipeline directly (without Arq worker).

This script:
1. Scrapes data from Google Trends (7 days of data)
2. Stores signals in the database
3. Runs enhanced analyzer to generate insights

Usage:
    python scripts/run_data_collection.py

Note: Requires GOOGLE_API_KEY environment variable.
Reddit and Firecrawl scrapers are skipped if API keys are not configured.
"""

import asyncio
import logging
import sys
from datetime import UTC, datetime

# Setup path
sys.path.insert(0, "/home/wysetime-pcc/Nero/StartInsight/backend")

from app.core.config import settings
from app.db.session import AsyncSessionLocal
from app.scrapers.sources import GoogleTrendsScraper

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


async def run_google_trends_scraper() -> int:
    """Run Google Trends scraper for last 7 days."""
    logger.info("=" * 60)
    logger.info("Starting Google Trends Data Collection")
    logger.info("=" * 60)

    # Extended keywords for more comprehensive coverage
    keywords = [
        # SaaS & Startup
        "AI startup",
        "SaaS product",
        "no code",
        "startup idea",
        "side hustle",
        # Tech trends
        "API integration",
        "automation tool",
        "project management software",
        "CRM software",
        "email marketing",
        # AI & ML
        "AI assistant",
        "machine learning tool",
        "chatbot platform",
        "AI analytics",
        "generative AI",
        # Developer tools
        "developer productivity",
        "code review tool",
        "DevOps platform",
        "cloud infrastructure",
        "CI CD pipeline",
        # Business
        "business intelligence",
        "data analytics",
        "workflow automation",
        "team collaboration",
        "remote work tools",
    ]

    scraper = GoogleTrendsScraper(
        keywords=keywords,
        timeframe="now 7-d",  # Last 7 days
        geo="",  # Worldwide
    )

    signals_count = 0
    async with AsyncSessionLocal() as session:
        try:
            # Run scraper
            results = await scraper.scrape()
            logger.info(f"Scraped {len(results)} trend signals")

            # Save to database (correct method name)
            signals = await scraper.save_to_database(session, results)
            await session.commit()

            signals_count = len(signals)
            logger.info(f"Saved {signals_count} signals to database")

        except Exception as e:
            logger.error(f"Error in Google Trends scraper: {e}")
            await session.rollback()

    return signals_count


async def run_analysis() -> int:
    """Run enhanced analyzer on unprocessed signals.

    Uses per-signal sessions to avoid DB connection timeouts during
    long-running Gemini API calls (~14s each).
    """
    from sqlalchemy import select, update

    from app.agents.enhanced_analyzer import analyze_signal_enhanced_with_retry
    from app.models.raw_signal import RawSignal

    logger.info("=" * 60)
    logger.info("Starting Signal Analysis")
    logger.info("=" * 60)

    analyzed_count = 0
    failed_count = 0

    # Fetch signal IDs first (short-lived session)
    async with AsyncSessionLocal() as session:
        result = await session.execute(
            select(RawSignal.id)
            .where(RawSignal.processed == False)
            .order_by(RawSignal.created_at.asc())
            .limit(20)
        )
        signal_ids = [row[0] for row in result.all()]

    if not signal_ids:
        logger.info("No unprocessed signals to analyze")
        return 0

    logger.info(f"Found {len(signal_ids)} unprocessed signals")

    # Process each signal with a fresh session to avoid connection timeouts
    for i, signal_id in enumerate(signal_ids, 1):
        try:
            async with AsyncSessionLocal() as session:
                signal = await session.get(RawSignal, signal_id)
                if not signal:
                    continue

                content_preview = (signal.content or "")[:50]
                logger.info(f"Processing signal {i}/{len(signal_ids)}: {signal.source} - {content_preview}...")

                insight = await analyze_signal_enhanced_with_retry(signal)
                session.add(insight)
                await session.commit()

                # Mark signal as processed
                async with AsyncSessionLocal() as update_session:
                    await update_session.execute(
                        update(RawSignal)
                        .where(RawSignal.id == signal_id)
                        .values(processed=True)
                    )
                    await update_session.commit()

                analyzed_count += 1
                problem_preview = (insight.problem_statement or "")[:50]
                logger.info(f"  ✓ Generated insight: {problem_preview}...")

        except Exception as e:
            failed_count += 1
            logger.error(f"  ✗ Failed: {type(e).__name__} - {e}")

    logger.info(f"Analysis complete: {analyzed_count} analyzed, {failed_count} failed")
    return analyzed_count


async def check_reddit_scraper() -> int:
    """Check if Reddit scraper can be used."""
    if (
        not settings.reddit_client_id
        or settings.reddit_client_id == "your_reddit_client_id_here"
    ):
        logger.warning("Reddit API not configured - skipping Reddit scraper")
        return 0

    logger.info("Reddit API configured - running Reddit scraper")
    from app.scrapers.sources import RedditScraper

    scraper = RedditScraper(
        subreddits=["startups", "SaaS", "Entrepreneur", "smallbusiness"],
        limit=25,
        time_filter="week",  # Last week for 7-day data
    )

    signals_count = 0
    async with AsyncSessionLocal() as session:
        try:
            results = await scraper.scrape()
            logger.info(f"Scraped {len(results)} Reddit posts")

            signals = await scraper.save_to_database(session, results)
            await session.commit()

            signals_count = len(signals)
            logger.info(f"Saved {signals_count} Reddit signals to database")

        except Exception as e:
            logger.error(f"Error in Reddit scraper: {e}")
            await session.rollback()

    return signals_count


async def main():
    """Main entry point for data collection."""
    logger.info("=" * 70)
    logger.info("StartInsight Data Collection Pipeline")
    logger.info(f"Started at: {datetime.now(UTC).isoformat()}")
    logger.info("=" * 70)

    total_signals = 0
    total_insights = 0

    # Step 1: Google Trends
    try:
        signals = await run_google_trends_scraper()
        total_signals += signals
    except Exception as e:
        logger.error(f"Google Trends scraper failed: {e}")

    # Step 2: Reddit (if configured)
    try:
        signals = await check_reddit_scraper()
        total_signals += signals
    except Exception as e:
        logger.error(f"Reddit scraper failed: {e}")

    # Step 3: Analyze signals
    if total_signals > 0 or True:  # Always try to analyze any unprocessed
        try:
            insights = await run_analysis()
            total_insights += insights

            # Run analysis again if there are more signals
            while insights > 0:
                insights = await run_analysis()
                total_insights += insights

        except Exception as e:
            logger.error(f"Analysis failed: {e}")

    # Summary
    logger.info("=" * 70)
    logger.info("Data Collection Summary")
    logger.info("=" * 70)
    logger.info(f"Total signals collected: {total_signals}")
    logger.info(f"Total insights generated: {total_insights}")
    logger.info(f"Completed at: {datetime.now(UTC).isoformat()}")
    logger.info("=" * 70)

    return total_signals, total_insights


if __name__ == "__main__":
    asyncio.run(main())
