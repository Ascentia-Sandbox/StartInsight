"""Task scheduler using APScheduler to enqueue Arq jobs."""

import logging

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger
from arq import create_pool
from arq.connections import RedisSettings

from app.core.config import settings

logger = logging.getLogger(__name__)

# Global scheduler instance
scheduler = AsyncIOScheduler()


async def schedule_scraping_tasks() -> None:
    """
    Schedule all scraping tasks to run every 6 hours.

    Creates an Arq Redis pool and schedules jobs to be enqueued
    at regular intervals.

    This function should be called on FastAPI startup.
    """
    logger.info("Initializing task scheduler")

    # Create Arq Redis pool
    redis = await create_pool(
        RedisSettings(
            host=settings.redis_host,
            port=settings.redis_port,
            database=0,
        )
    )

    # Schedule scraping tasks every 6 hours
    scheduler.add_job(
        func=redis.enqueue_job,
        args=("scrape_all_sources_task",),
        trigger=IntervalTrigger(hours=settings.scrape_interval_hours),
        id="scrape_all_sources",
        replace_existing=True,
        name="Scrape All Sources (Reddit, Product Hunt, Google Trends)",
    )

    # Start the scheduler
    scheduler.start()

    logger.info(
        f"Task scheduler started. Scraping will run every "
        f"{settings.scrape_interval_hours} hours"
    )


async def stop_scheduler() -> None:
    """Stop the task scheduler gracefully."""
    if scheduler.running:
        scheduler.shutdown(wait=True)
        logger.info("Task scheduler stopped")


async def trigger_scraping_now() -> dict[str, str]:
    """
    Manually trigger scraping immediately (for testing/debugging).

    Returns:
        Status message
    """
    logger.info("Manually triggering scraping task")

    redis = await create_pool(
        RedisSettings(
            host=settings.redis_host,
            port=settings.redis_port,
            database=0,
        )
    )

    job = await redis.enqueue_job("scrape_all_sources_task")

    return {
        "status": "success",
        "message": "Scraping task enqueued",
        "job_id": job.job_id,
    }
