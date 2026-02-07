"""Arq worker configuration and background tasks."""

import logging
from typing import Any

from arq import cron
from arq.connections import RedisSettings

from app.core.config import settings
from app.db.session import AsyncSessionLocal
from app.scrapers.base_scraper import BaseScraper
from app.scrapers.sources import (
    GoogleTrendsScraper,
    ProductHuntScraper,
    RedditScraper,
)

logger = logging.getLogger(__name__)


async def _run_scraper(source_name: str, scraper: BaseScraper) -> dict[str, Any]:
    """
    Run a scraper and return a standardized result dict.

    Args:
        source_name: Identifier for the data source (e.g., "reddit")
        scraper: Configured scraper instance to execute

    Returns:
        Task result with status and count of signals saved
    """
    logger.info(f"Starting {source_name} scraping task")

    try:
        async with AsyncSessionLocal() as session:
            signals = await scraper.run(session)
            await session.commit()

        logger.info(f"{source_name} scraping complete: {len(signals)} signals saved")
        return {
            "status": "success",
            "source": source_name,
            "signals_saved": len(signals),
        }

    except Exception as e:
        logger.error(f"{source_name} scraping failed: {type(e).__name__} - {e}")
        return {
            "status": "error",
            "source": source_name,
            "error": str(e),
        }


async def scrape_reddit_task(ctx: dict[str, Any]) -> dict[str, Any]:
    """Background task to scrape Reddit for startup discussions."""
    return await _run_scraper(
        "reddit",
        RedditScraper(subreddits=["startups", "SaaS"], limit=25, time_filter="day"),
    )


async def scrape_product_hunt_task(ctx: dict[str, Any]) -> dict[str, Any]:
    """Background task to scrape Product Hunt for daily launches."""
    return await _run_scraper(
        "product_hunt",
        ProductHuntScraper(days_back=1, limit=10),
    )


async def scrape_trends_task(ctx: dict[str, Any]) -> dict[str, Any]:
    """Background task to scrape Google Trends for search volume data."""
    return await _run_scraper(
        "google_trends",
        GoogleTrendsScraper(keywords=None, timeframe="now 7-d", geo="US"),
    )


async def hourly_trends_update_task(ctx: dict[str, Any]) -> dict[str, Any]:
    """
    Hourly background task to update Google Trends real-time data for top insights.

    This task:
    1. Fetches top 100 insights by relevance score
    2. Updates their trend data with latest hourly data point
    3. Stores realtime trend data in extra_metadata.trend_data_realtime
    4. Implements 90-day data retention policy

    Args:
        ctx: Arq context dictionary

    Returns:
        Task result with count of insights updated
    """
    from datetime import datetime, timedelta
    from sqlalchemy import select, desc

    from app.models.insight import Insight
    from app.models.raw_signal import RawSignal

    logger.info("Starting hourly trends update task")

    try:
        updated_count = 0
        failed_count = 0

        async with AsyncSessionLocal() as session:
            # Get top 100 insights by relevance score
            stmt = (
                select(Insight)
                .order_by(desc(Insight.relevance_score))
                .limit(100)
            )
            result = await session.execute(stmt)
            insights = result.scalars().all()

            logger.info(f"Found {len(insights)} insights to update with hourly trends")

            # Process each insight
            for insight in insights:
                try:
                    # Find associated Google Trends signal
                    signal_stmt = (
                        select(RawSignal)
                        .where(RawSignal.id == insight.raw_signal_id)
                        .where(RawSignal.source == "google_trends")
                    )
                    signal_result = await session.execute(signal_stmt)
                    signal = signal_result.scalar_one_or_none()

                    if not signal or not signal.extra_metadata:
                        continue

                    # Extract keyword from signal metadata
                    keyword = signal.extra_metadata.get("keyword")
                    if not keyword:
                        continue

                    # Scrape latest hourly data for this keyword
                    scraper = GoogleTrendsScraper(
                        keywords=[keyword],
                        timeframe="now 1-H",  # Last hour
                        geo=signal.extra_metadata.get("geo", "US"),
                    )

                    # Get latest data point
                    results = await scraper.scrape()
                    if not results:
                        continue

                    latest_result = results[0]
                    current_interest = latest_result.metadata.get("current_interest", 0)

                    # Initialize or update realtime trend data
                    if "trend_data_realtime" not in signal.extra_metadata:
                        signal.extra_metadata["trend_data_realtime"] = {
                            "timestamps": [],
                            "values": []
                        }

                    # Add new data point
                    now = datetime.utcnow()
                    signal.extra_metadata["trend_data_realtime"]["timestamps"].append(
                        now.isoformat()
                    )
                    signal.extra_metadata["trend_data_realtime"]["values"].append(
                        current_interest
                    )

                    # Implement 90-day retention policy
                    cutoff_date = now - timedelta(days=90)
                    timestamps = signal.extra_metadata["trend_data_realtime"]["timestamps"]
                    values = signal.extra_metadata["trend_data_realtime"]["values"]

                    # Filter out data older than 90 days
                    filtered_data = [
                        (ts, val)
                        for ts, val in zip(timestamps, values)
                        if datetime.fromisoformat(ts) >= cutoff_date
                    ]

                    if filtered_data:
                        signal.extra_metadata["trend_data_realtime"]["timestamps"] = [
                            item[0] for item in filtered_data
                        ]
                        signal.extra_metadata["trend_data_realtime"]["values"] = [
                            item[1] for item in filtered_data
                        ]

                    # Mark signal as modified
                    session.add(signal)

                    updated_count += 1
                    logger.debug(
                        f"Updated hourly trend for insight {insight.id} "
                        f"(keyword: {keyword}, value: {current_interest})"
                    )

                except Exception as e:
                    failed_count += 1
                    logger.error(
                        f"Failed to update hourly trend for insight {insight.id}: "
                        f"{type(e).__name__} - {e}"
                    )

            await session.commit()

        logger.info(
            f"Hourly trends update complete: {updated_count} updated, "
            f"{failed_count} failed out of {len(insights)} insights"
        )

        return {
            "status": "success",
            "updated": updated_count,
            "failed": failed_count,
            "total": len(insights),
        }

    except Exception as e:
        logger.error(f"Hourly trends update task failed: {type(e).__name__} - {e}")
        return {
            "status": "error",
            "error": str(e),
        }


async def scrape_all_sources_task(ctx: dict[str, Any]) -> dict[str, Any]:
    """
    Background task to scrape all sources sequentially.

    This is the main scheduled task that runs every 6 hours.

    Args:
        ctx: Arq context dictionary

    Returns:
        Aggregated task results from all sources
    """
    logger.info("Starting scrape_all_sources task")

    results = {
        "reddit": await scrape_reddit_task(ctx),
        "product_hunt": await scrape_product_hunt_task(ctx),
        "google_trends": await scrape_trends_task(ctx),
    }

    total_signals = sum(
        r.get("signals_saved", 0)
        for r in results.values()
        if r.get("status") == "success"
    )

    logger.info(
        f"scrape_all_sources task complete: {total_signals} total signals saved"
    )

    return {
        "status": "success",
        "total_signals": total_signals,
        "details": results,
    }


async def analyze_signals_task(ctx: dict[str, Any]) -> dict[str, Any]:
    """
    Background task to analyze unprocessed raw signals.

    Processes signals in batches using PydanticAI enhanced analyzer.
    Marks signals as processed ONLY AFTER successful commit.

    Uses enhanced analyzer for IdeaBrowser-parity content quality:
    - 450+ word narrative problem statements (exceeds IdeaBrowser's 400+ words)
    - 8-dimension scoring (vs IdeaBrowser's 4 dimensions)
    - Value ladder, market gap analysis, execution plans

    CRITICAL: Signals are marked processed AFTER commit to prevent data loss
    if the transaction fails. This fixes the race condition where signals
    could be marked processed before analysis was actually persisted.

    Args:
        ctx: Arq context dictionary

    Returns:
        Task result with count of analyzed signals
    """
    from sqlalchemy import select, update

    from app.agents.enhanced_analyzer import analyze_signal_enhanced_with_retry
    from app.models.raw_signal import RawSignal

    logger.info("Starting signal analysis task")

    batch_size = settings.analysis_batch_size

    try:
        async with AsyncSessionLocal() as session:
            # Get unprocessed signals with row-level lock to prevent concurrent processing
            result = await session.execute(
                select(RawSignal)
                .where(RawSignal.processed == False)  # noqa: E712
                .order_by(RawSignal.created_at.asc())  # Process oldest first
                .limit(batch_size)
                .with_for_update(skip_locked=True)  # Prevent concurrent processing
            )
            signals = result.scalars().all()

            if not signals:
                logger.info("No unprocessed signals to analyze")
                return {
                    "status": "success",
                    "analyzed": 0,
                    "total": 0,
                }

            analyzed_count = 0
            failed_count = 0
            # Track successfully processed signal IDs for post-commit update
            successfully_processed_ids: list = []

            for signal in signals:
                try:
                    # Analyze signal with enhanced analyzer (450+ word narratives)
                    insight = await analyze_signal_enhanced_with_retry(signal)
                    session.add(insight)

                    # Track success - DO NOT mark processed yet!
                    successfully_processed_ids.append(signal.id)
                    analyzed_count += 1

                    logger.info(
                        f"Analyzed signal {signal.id} from {signal.source}"
                    )

                except Exception as e:
                    failed_count += 1
                    logger.error(
                        f"Failed to analyze signal {signal.id}: {type(e).__name__} - {e}"
                    )
                    # Signal remains unprocessed for retry

            # Commit insights to database
            try:
                await session.commit()
                logger.info(
                    f"Committed {analyzed_count} insights to database"
                )

                # ONLY NOW mark signals as processed (after successful commit)
                if successfully_processed_ids:
                    async with AsyncSessionLocal() as update_session:
                        await update_session.execute(
                            update(RawSignal)
                            .where(RawSignal.id.in_(successfully_processed_ids))
                            .values(processed=True)
                        )
                        await update_session.commit()
                        logger.info(
                            f"Marked {len(successfully_processed_ids)} signals as processed"
                        )

            except Exception as e:
                await session.rollback()
                logger.error(
                    f"Commit failed, no signals marked as processed: "
                    f"{type(e).__name__} - {e}"
                )
                # All signals remain unprocessed for retry
                return {
                    "status": "error",
                    "error": f"Commit failed: {e}",
                    "analyzed": 0,
                    "failed": len(signals),
                    "total": len(signals),
                }

        logger.info(
            f"Analysis task complete: {analyzed_count} analyzed, "
            f"{failed_count} failed out of {len(signals)} signals"
        )

        return {
            "status": "success",
            "analyzed": analyzed_count,
            "failed": failed_count,
            "total": len(signals),
        }

    except Exception as e:
        logger.error(f"Analysis task failed: {type(e).__name__} - {e}")
        return {
            "status": "error",
            "error": str(e),
        }


async def startup(ctx: dict[str, Any]) -> None:
    """
    Startup hook for Arq worker.

    Runs when the worker starts up.
    """
    logger.info("Arq worker starting up")


async def shutdown(ctx: dict[str, Any]) -> None:
    """
    Shutdown hook for Arq worker.

    Runs when the worker shuts down.
    """
    logger.info("Arq worker shutting down")


class WorkerSettings:
    """
    Arq worker configuration.

    Defines Redis connection, tasks, and scheduling.
    """

    # Redis connection settings
    redis_settings = RedisSettings(
        host=settings.redis_host,
        port=settings.redis_port,
        database=0,
    )

    # Task functions to register
    functions = [
        scrape_reddit_task,
        scrape_product_hunt_task,
        scrape_trends_task,
        scrape_all_sources_task,
        analyze_signals_task,
        hourly_trends_update_task,
    ]

    # Cron jobs (scheduled tasks)
    cron_jobs = [
        # Run scrape_all_sources every 6 hours
        cron(
            scrape_all_sources_task,
            hour={0, 6, 12, 18},  # Run at midnight, 6am, noon, 6pm
            minute=0,
            run_at_startup=False,  # Don't run immediately on worker start
        ),
        # Run hourly trends update every hour
        cron(
            hourly_trends_update_task,
            minute=0,  # Run at the top of every hour
            run_at_startup=False,  # Don't run immediately on worker start
        ),
    ]

    # Startup and shutdown hooks
    on_startup = startup
    on_shutdown = shutdown

    # Worker settings
    max_jobs = 10  # Max concurrent jobs
    job_timeout = 600  # 10 minutes timeout per job
    keep_result = 3600  # Keep job results for 1 hour
