"""Task scheduler using APScheduler to enqueue Arq jobs."""

import logging
from urllib.parse import urlparse

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.interval import IntervalTrigger
from arq import create_pool
from arq.connections import RedisSettings

from app.core.config import settings

logger = logging.getLogger(__name__)


def _get_redis_settings() -> RedisSettings:
    """Parse settings.redis_url into an Arq RedisSettings instance."""
    parsed = urlparse(settings.redis_url)
    return RedisSettings(
        host=parsed.hostname or "localhost",
        port=parsed.port or 6379,
        password=parsed.password,
        database=int(parsed.path.lstrip("/") or "0"),
    )

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
    redis = await create_pool(_get_redis_settings())

    # Schedule scraping tasks every 6 hours
    scheduler.add_job(
        func=redis.enqueue_job,
        args=("scrape_all_sources_task",),
        trigger=IntervalTrigger(hours=settings.scrape_interval_hours),
        id="scrape_all_sources",
        replace_existing=True,
        name="Scrape All Sources (Reddit, Product Hunt, Google Trends)",
    )

    # Schedule analysis tasks (run shortly after scraping)
    # Analysis runs 10 minutes after each scraping interval
    scheduler.add_job(
        func=redis.enqueue_job,
        args=("analyze_signals_task",),
        trigger=IntervalTrigger(hours=settings.scrape_interval_hours),
        id="analyze_signals",
        replace_existing=True,
        name="Analyze Raw Signals (PydanticAI)",
    )

    # Schedule daily digest emails at 09:00 UTC
    scheduler.add_job(
        func=redis.enqueue_job,
        args=("send_daily_digests_task",),
        trigger=CronTrigger(hour=9, minute=0),
        id="send_daily_digests",
        replace_existing=True,
        name="Send Daily Digest Emails",
    )

    # Schedule daily insight agent at 08:00 UTC
    scheduler.add_job(
        func=redis.enqueue_job,
        args=("fetch_daily_insight_task",),
        trigger=CronTrigger(hour=8, minute=0),
        id="daily_insight_agent",
        replace_existing=True,
        name="Daily Insight Agent (8am UTC)",
    )

    # Schedule market insight publisher every 3 days at 06:00 UTC
    scheduler.add_job(
        func=redis.enqueue_job,
        args=("market_insight_publisher_task",),
        trigger=CronTrigger(day="*/3", hour=6, minute=0),
        id="market_insight_publisher",
        replace_existing=True,
        name="Market Insight Publisher (every 3 days, 6am UTC)",
    )

    # Schedule market insight quality review 2 hours after publisher
    scheduler.add_job(
        func=redis.enqueue_job,
        args=("market_insight_quality_review_task",),
        trigger=CronTrigger(day="*/3", hour=8, minute=30),
        id="market_insight_quality_reviewer",
        replace_existing=True,
        name="Market Insight Quality Review (every 3 days, 8:30am UTC)",
    )

    # Schedule insight quality audit weekly on Mondays at 03:00 UTC
    scheduler.add_job(
        func=redis.enqueue_job,
        args=("insight_quality_audit_task",),
        trigger=CronTrigger(day_of_week="mon", hour=3, minute=0),
        id="insight_quality_reviewer",
        replace_existing=True,
        name="Insight Quality Audit (weekly, Mon 3am UTC)",
    )

    # Schedule success stories agent every 7 days (Sundays at 05:00 UTC)
    scheduler.add_job(
        func=redis.enqueue_job,
        args=("update_success_stories_task",),
        trigger=CronTrigger(day_of_week="sun", hour=5, minute=0),
        id="success_stories_agent",
        replace_existing=True,
        name="Success Stories Agent (weekly, Sun 5am UTC)",
    )

    # Start the scheduler
    scheduler.start()

    logger.info(
        f"Task scheduler started. Scraping every {settings.scrape_interval_hours}h, "
        f"daily insight at 08:00 UTC, daily digest at 09:00 UTC, "
        f"market insight publisher every 3 days, quality reviews scheduled, "
        f"success stories agent weekly on Sundays."
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

    redis = await create_pool(_get_redis_settings())

    job = await redis.enqueue_job("scrape_all_sources_task")

    return {
        "status": "success",
        "message": "Scraping task enqueued",
        "job_id": job.job_id,
    }
