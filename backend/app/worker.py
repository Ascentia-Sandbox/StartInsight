"""Arq worker configuration and background tasks."""

import logging
from typing import Any

from arq import cron
from arq.connections import RedisSettings

from app.core.config import settings
from app.db.session import AsyncSessionLocal
from app.scrapers.sources import (
    GoogleTrendsScraper,
    ProductHuntScraper,
    RedditScraper,
)

logger = logging.getLogger(__name__)


async def scrape_reddit_task(ctx: dict[str, Any]) -> dict[str, Any]:
    """
    Background task to scrape Reddit for startup discussions.

    Args:
        ctx: Arq context dictionary

    Returns:
        Task result with count of signals saved
    """
    logger.info("Starting Reddit scraping task")

    try:
        scraper = RedditScraper(
            subreddits=["startups", "SaaS"],
            limit=25,
            time_filter="day",
        )

        async with AsyncSessionLocal() as session:
            signals = await scraper.run(session)
            await session.commit()

        logger.info(f"Reddit scraping complete: {len(signals)} signals saved")
        return {
            "status": "success",
            "source": "reddit",
            "signals_saved": len(signals),
        }

    except Exception as e:
        logger.error(f"Reddit scraping failed: {type(e).__name__} - {e}")
        return {
            "status": "error",
            "source": "reddit",
            "error": str(e),
        }


async def scrape_product_hunt_task(ctx: dict[str, Any]) -> dict[str, Any]:
    """
    Background task to scrape Product Hunt for daily launches.

    Args:
        ctx: Arq context dictionary

    Returns:
        Task result with count of signals saved
    """
    logger.info("Starting Product Hunt scraping task")

    try:
        scraper = ProductHuntScraper(
            days_back=1,  # Today's products
            limit=10,
        )

        async with AsyncSessionLocal() as session:
            signals = await scraper.run(session)
            await session.commit()

        logger.info(
            f"Product Hunt scraping complete: {len(signals)} signals saved"
        )
        return {
            "status": "success",
            "source": "product_hunt",
            "signals_saved": len(signals),
        }

    except Exception as e:
        logger.error(
            f"Product Hunt scraping failed: {type(e).__name__} - {e}"
        )
        return {
            "status": "error",
            "source": "product_hunt",
            "error": str(e),
        }


async def scrape_trends_task(ctx: dict[str, Any]) -> dict[str, Any]:
    """
    Background task to scrape Google Trends for search volume data.

    Args:
        ctx: Arq context dictionary

    Returns:
        Task result with count of signals saved
    """
    logger.info("Starting Google Trends scraping task")

    try:
        scraper = GoogleTrendsScraper(
            keywords=None,  # Use default keywords
            timeframe="now 7-d",  # Last 7 days
            geo="US",
        )

        async with AsyncSessionLocal() as session:
            signals = await scraper.run(session)
            await session.commit()

        logger.info(
            f"Google Trends scraping complete: {len(signals)} signals saved"
        )
        return {
            "status": "success",
            "source": "google_trends",
            "signals_saved": len(signals),
        }

    except Exception as e:
        logger.error(f"Google Trends scraping failed: {type(e).__name__} - {e}")
        return {
            "status": "error",
            "source": "google_trends",
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

    Processes signals in batches using PydanticAI analyzer.
    Marks signals as processed after successful analysis.

    Args:
        ctx: Arq context dictionary

    Returns:
        Task result with count of analyzed signals
    """
    from sqlalchemy import select

    from app.agents.analyzer import analyze_signal_with_retry
    from app.models.insight import Insight
    from app.models.raw_signal import RawSignal

    logger.info("Starting signal analysis task")

    batch_size = settings.analysis_batch_size

    try:
        async with AsyncSessionLocal() as session:
            # Get unprocessed signals
            result = await session.execute(
                select(RawSignal)
                .where(RawSignal.processed == False)  # noqa: E712
                .limit(batch_size)
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

            for signal in signals:
                try:
                    # Analyze signal with retry logic
                    insight = await analyze_signal_with_retry(signal)
                    session.add(insight)

                    # Mark signal as processed
                    signal.processed = True

                    analyzed_count += 1
                    logger.info(
                        f"Analyzed signal {signal.id} from {signal.source}"
                    )

                except Exception as e:
                    failed_count += 1
                    logger.error(
                        f"Failed to analyze signal {signal.id}: {type(e).__name__} - {e}"
                    )
                    # Don't mark as processed - will retry later

            await session.commit()

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
    ]

    # Startup and shutdown hooks
    on_startup = startup
    on_shutdown = shutdown

    # Worker settings
    max_jobs = 10  # Max concurrent jobs
    job_timeout = 600  # 10 minutes timeout per job
    keep_result = 3600  # Keep job results for 1 hour
