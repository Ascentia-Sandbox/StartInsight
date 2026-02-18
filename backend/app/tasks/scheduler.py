"""Task scheduler using APScheduler to enqueue Arq jobs."""

import logging
from datetime import UTC, datetime, timedelta
from urllib.parse import urlparse

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.interval import IntervalTrigger
from arq import create_pool
from arq.connections import RedisSettings
from sqlalchemy import select

from app.core.config import settings
from app.db.session import AsyncSessionLocal
from app.models.agent_control import AgentConfiguration

logger = logging.getLogger(__name__)


def _get_redis_settings() -> RedisSettings:
    """Parse settings.redis_url into an Arq RedisSettings instance."""
    parsed = urlparse(settings.redis_url)
    return RedisSettings(
        host=parsed.hostname or "localhost",
        port=parsed.port or 6379,
        password=parsed.password,
        database=int(parsed.path.lstrip("/") or "0"),
        conn_timeout=3,
        conn_retries=0,
    )

# Global scheduler instance
scheduler = AsyncIOScheduler()


async def schedule_scraping_tasks() -> None:
    """
    Schedule all scraping tasks to run every 6 hours.

    Creates an Arq Redis pool and schedules jobs to be enqueued
    at regular intervals.

    This function should be called on FastAPI startup.
    Phase 16.2: Reads agent schedules from database.
    """
    logger.info("Initializing task scheduler with dynamic schedule management")

    # Create Arq Redis pool
    redis = await create_pool(_get_redis_settings())

    # Phase 16.2: Load agent schedules from database
    async with AsyncSessionLocal() as db:
        result = await db.execute(
            select(AgentConfiguration).where(AgentConfiguration.is_enabled)
        )
        agent_configs = result.scalars().all()

        # Schedule agents based on their configuration
        for config in agent_configs:
            await _schedule_agent_from_config(redis, config, db)

    # Fallback: Schedule legacy scraping tasks if no DB config exists
    if not scheduler.get_job("scrape_all_sources"):
        scheduler.add_job(
            func=redis.enqueue_job,
            args=("scrape_all_sources_task",),
            trigger=IntervalTrigger(hours=settings.scrape_interval_hours),
            id="scrape_all_sources",
            replace_existing=True,
            name="Scrape All Sources (Reddit, Product Hunt, Google Trends, Twitter, Hacker News)",
        )

    # Schedule Twitter scraping every 6 hours (offset by 1h from scrape_all)
    if not scheduler.get_job("scrape_twitter"):
        scheduler.add_job(
            func=redis.enqueue_job,
            args=("scrape_twitter_task",),
            trigger=CronTrigger(hour="1,7,13,19", minute=0),
            id="scrape_twitter",
            replace_existing=True,
            name="Scrape Twitter/X (Startup Discussions)",
        )

    # Schedule Hacker News scraping every 6 hours (offset by 1h from scrape_all)
    if not scheduler.get_job("scrape_hackernews"):
        scheduler.add_job(
            func=redis.enqueue_job,
            args=("scrape_hackernews_task",),
            trigger=CronTrigger(hour="1,7,13,19", minute=15),
            id="scrape_hackernews",
            replace_existing=True,
            name="Scrape Hacker News (Top Stories + Show HN)",
        )

    # Fallback: Schedule analysis tasks if no DB config
    if not scheduler.get_job("analyze_signals"):
        scheduler.add_job(
            func=redis.enqueue_job,
            args=("analyze_signals_task",),
            trigger=IntervalTrigger(hours=settings.scrape_interval_hours),
            id="analyze_signals",
            replace_existing=True,
            name="Analyze Raw Signals (PydanticAI)",
        )

    # Schedule daily digest emails at 09:00 UTC (PMF: disabled by default)
    if settings.enable_daily_digest:
        scheduler.add_job(
            func=redis.enqueue_job,
            args=("send_daily_digests_task",),
            trigger=CronTrigger(hour=9, minute=0),
            id="send_daily_digests",
            replace_existing=True,
            name="Send Daily Digest Emails",
        )
        logger.info("Daily digest emails enabled (09:00 UTC)")
    else:
        logger.info("Daily digest emails disabled (PMF optimization - save email quota)")

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

    # Phase 17: Content automation pipeline
    # Runs 15 min after analysis (which runs at top of scrape interval)
    scheduler.add_job(
        func=redis.enqueue_job,
        args=("run_content_pipeline_task",),
        trigger=IntervalTrigger(hours=settings.scrape_interval_hours),
        id="content_pipeline",
        replace_existing=True,
        name="Content Automation Pipeline (after analysis)",
    )

    # Phase 17.2: Auto-run research agent weekly on Wednesdays
    scheduler.add_job(
        func=redis.enqueue_job,
        args=("run_research_agent_auto_task",),
        trigger=CronTrigger(day_of_week="wed", hour=4, minute=0),
        id="research_agent_auto",
        replace_existing=True,
        name="Auto Research Agent (weekly, Wed 4am UTC)",
    )

    # Phase D: Content generator auto (every 3 days, Tue/Fri at 07:00 UTC)
    scheduler.add_job(
        func=redis.enqueue_job,
        args=("run_content_generator_auto_task",),
        trigger=CronTrigger(day="*/3", hour=7, minute=0),
        id="content_generator_auto",
        replace_existing=True,
        name="Auto Content Generator (every 3 days, 7am UTC)",
    )

    # Phase D: Competitive intel auto (weekly Thursdays at 04:00 UTC)
    scheduler.add_job(
        func=redis.enqueue_job,
        args=("run_competitive_intel_auto_task",),
        trigger=CronTrigger(day_of_week="thu", hour=4, minute=0),
        id="competitive_intel_auto",
        replace_existing=True,
        name="Auto Competitive Intel (weekly, Thu 4am UTC)",
    )

    # Phase D: Market intel auto (weekly Fridays at 05:00 UTC)
    scheduler.add_job(
        func=redis.enqueue_job,
        args=("run_market_intel_auto_task",),
        trigger=CronTrigger(day_of_week="fri", hour=5, minute=0),
        id="market_intel_auto",
        replace_existing=True,
        name="Auto Market Intel (weekly, Fri 5am UTC)",
    )

    # Phase L: Weekly digest every Monday at 09:00 UTC
    scheduler.add_job(
        func=redis.enqueue_job,
        args=("send_weekly_digest_task",),
        trigger=CronTrigger(day_of_week="mon", hour=9, minute=0),
        id="weekly_digest",
        replace_existing=True,
        name="Weekly Insight Digest (Mon 9am UTC)",
    )

    # Start the scheduler
    scheduler.start()

    logger.info(
        f"Task scheduler started. Scraping every {settings.scrape_interval_hours}h, "
        f"Twitter+HN every 6h (offset), "
        f"daily insight at 08:00 UTC, daily digest at 09:00 UTC, "
        f"market insight publisher every 3 days, quality reviews scheduled, "
        f"success stories agent weekly on Sundays, "
        f"content/competitive/market intel auto-scheduled, "
        f"weekly insight digest Mon 9am UTC."
    )


async def _schedule_agent_from_config(redis, config: AgentConfiguration, db) -> None:
    """
    Schedule an agent based on its database configuration.

    Phase 16.2: Dynamic scheduling from AgentConfiguration.
    """
    job_id = f"agent_{config.agent_name}"

    # Map agent names to task functions
    task_map = {
        "enhanced_analyzer": "analyze_signals_task",
        "research_agent": "fetch_daily_insight_task",
        "competitive_intel": "update_success_stories_task",
        "market_intel": "market_insight_publisher_task",
    }

    task_name = task_map.get(config.agent_name)
    if not task_name:
        logger.warning(f"No task mapping found for agent: {config.agent_name}")
        return

    # Remove existing job if present
    if scheduler.get_job(job_id):
        scheduler.remove_job(job_id)

    # Schedule based on type
    if config.schedule_type == "cron" and config.schedule_cron:
        # Parse cron expression
        cron_parts = config.schedule_cron.split()
        if len(cron_parts) == 5:
            minute, hour, day, month, day_of_week = cron_parts
            scheduler.add_job(
                func=redis.enqueue_job,
                args=(task_name,),
                trigger=CronTrigger(
                    minute=minute,
                    hour=hour,
                    day=day,
                    month=month,
                    day_of_week=day_of_week
                ),
                id=job_id,
                replace_existing=True,
                name=f"{config.agent_name} (cron: {config.schedule_cron})",
            )

            # Calculate next run time
            next_run = scheduler.get_job(job_id).next_run_time
            config.next_run_at = next_run
            await db.commit()

            logger.info(f"Scheduled {config.agent_name} with cron: {config.schedule_cron} (next: {next_run})")

    elif config.schedule_type == "interval" and config.schedule_interval_hours:
        scheduler.add_job(
            func=redis.enqueue_job,
            args=(task_name,),
            trigger=IntervalTrigger(hours=config.schedule_interval_hours),
            id=job_id,
            replace_existing=True,
            name=f"{config.agent_name} (every {config.schedule_interval_hours}h)",
        )

        # Calculate next run time
        next_run = datetime.now(UTC) + timedelta(hours=config.schedule_interval_hours)
        config.next_run_at = next_run
        await db.commit()

        logger.info(f"Scheduled {config.agent_name} with interval: {config.schedule_interval_hours}h (next: {next_run})")

    elif config.schedule_type == "manual":
        logger.info(f"Agent {config.agent_name} is set to manual execution only")
    else:
        logger.warning(f"Agent {config.agent_name} has invalid schedule configuration")


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
