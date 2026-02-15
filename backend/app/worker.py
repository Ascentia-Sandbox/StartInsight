"""Arq worker configuration and background tasks."""

import logging
import os
from pathlib import Path
from typing import Any

# Load .env into os.environ so PydanticAI agents can read GOOGLE_API_KEY etc.
# Pydantic Settings loads into the settings object but NOT into os.environ.
from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parent.parent / ".env")

from arq import cron
from arq.connections import RedisSettings

from app.core.config import settings
from app.db.session import AsyncSessionLocal
from app.scrapers.base_scraper import BaseScraper
from app.scrapers.sources import (
    GoogleTrendsScraper,
    HackerNewsScraper,
    ProductHuntScraper,
    RedditScraper,
    TwitterScraper,
)
from app.tasks.daily_digest import send_daily_digests_task
from app.tasks.daily_insight_agent import fetch_daily_insight_task
from app.tasks.success_stories_agent import update_success_stories_task

logger = logging.getLogger(__name__)


# ============================================
# TASK WRAPPERS FOR AGENTS (Phase 16.1)
# These wrap agent entry points as Arq-compatible task functions.
# ============================================


async def market_insight_publisher_task(ctx: dict[str, Any]) -> dict[str, Any]:
    """Arq task wrapper for market insight publisher agent."""
    from app.agents.market_insight_publisher import run_market_insight_publisher

    logger.info("Starting market_insight_publisher_task")
    try:
        result = await run_market_insight_publisher()
        logger.info(f"market_insight_publisher_task complete: {result.get('status')}")
        return result
    except Exception as e:
        logger.error(f"market_insight_publisher_task failed: {e}")
        return {"status": "error", "error": str(e)}


async def market_insight_quality_review_task(ctx: dict[str, Any]) -> dict[str, Any]:
    """Arq task wrapper for market insight quality review agent."""
    from app.agents.quality_reviewer import run_market_insight_quality_review

    logger.info("Starting market_insight_quality_review_task")
    try:
        result = await run_market_insight_quality_review()
        logger.info(f"market_insight_quality_review_task complete: {result.get('status')}")
        return result
    except Exception as e:
        logger.error(f"market_insight_quality_review_task failed: {e}")
        return {"status": "error", "error": str(e)}


async def insight_quality_audit_task(ctx: dict[str, Any]) -> dict[str, Any]:
    """Arq task wrapper for insight quality audit agent."""
    from app.agents.quality_reviewer import run_insight_quality_audit

    logger.info("Starting insight_quality_audit_task")
    try:
        result = await run_insight_quality_audit()
        logger.info(f"insight_quality_audit_task complete: {result.get('status')}")
        return result
    except Exception as e:
        logger.error(f"insight_quality_audit_task failed: {e}")
        return {"status": "error", "error": str(e)}


async def run_content_pipeline_task(ctx: dict[str, Any]) -> dict[str, Any]:
    """Arq task wrapper for content automation pipeline (Phase 17)."""
    from app.services.pipeline_orchestrator import run_content_pipeline

    logger.info("Starting run_content_pipeline_task")
    try:
        result = await run_content_pipeline()
        logger.info(f"run_content_pipeline_task complete: {result.get('status')}")
        return result
    except Exception as e:
        logger.error(f"run_content_pipeline_task failed: {e}")
        return {"status": "error", "error": str(e)}


async def run_research_agent_auto_task(ctx: dict[str, Any]) -> dict[str, Any]:
    """Auto-run research agent on top unresearched insights (Phase 17.2)."""
    from sqlalchemy import select

    from app.db.session import AsyncSessionLocal
    from app.models.custom_analysis import CustomAnalysis
    from app.models.insight import Insight

    logger.info("Starting run_research_agent_auto_task")
    try:
        async with AsyncSessionLocal() as session:
            # Find insights without custom analyses
            analyzed_ids_query = select(CustomAnalysis.insight_id).distinct()
            result = await session.execute(
                select(Insight)
                .where(Insight.relevance_score >= 0.7)
                .where(~Insight.id.in_(analyzed_ids_query))
                .order_by(Insight.relevance_score.desc())
                .limit(5)
            )
            insights = result.scalars().all()

            if not insights:
                return {"status": "completed", "items": 0, "reason": "no_unresearched_insights"}

            # Import and run research agent on each
            from app.agents.research_agent import analyze_idea_with_retry

            processed = 0
            for insight in insights:
                try:
                    await analyze_idea_with_retry(
                        idea_description=insight.problem_statement,
                        target_market=insight.market_size_estimate,
                    )
                    processed += 1
                except Exception as e:
                    logger.error(f"Research agent failed for insight {insight.id}: {e}")

            await session.commit()

        return {"status": "completed", "items": processed, "total": len(insights)}
    except Exception as e:
        logger.error(f"run_research_agent_auto_task failed: {e}")
        return {"status": "error", "error": str(e)}


# ============================================
# PHASE D: Content Volume & Quality Automation
# ============================================


async def run_content_generator_auto_task(ctx: dict[str, Any]) -> dict[str, Any]:
    """Auto-generate blog/social content for top insights without content (Phase D)."""
    from sqlalchemy import select

    from app.agents.content_generator_agent import generate_all_content
    from app.models.insight import Insight

    logger.info("Starting run_content_generator_auto_task")
    try:
        async with AsyncSessionLocal() as session:
            # Find top insights by score that haven't had content generated
            result = await session.execute(
                select(Insight)
                .where(Insight.relevance_score >= 0.7)
                .order_by(Insight.relevance_score.desc())
                .limit(5)
            )
            insights = result.scalars().all()

            if not insights:
                return {"status": "completed", "items": 0, "reason": "no_eligible_insights"}

            processed = 0
            for insight in insights:
                try:
                    await generate_all_content(insight.id, session)
                    processed += 1
                except Exception as e:
                    logger.error(f"Content generation failed for insight {insight.id}: {e}")

        return {"status": "completed", "items": processed, "total": len(insights)}
    except Exception as e:
        logger.error(f"run_content_generator_auto_task failed: {e}")
        return {"status": "error", "error": str(e)}


async def run_competitive_intel_auto_task(ctx: dict[str, Any]) -> dict[str, Any]:
    """Auto-analyze competitors for insights with stale data (Phase D)."""
    from datetime import UTC, datetime, timedelta

    from sqlalchemy import or_, select

    from app.agents.competitive_intel_agent import analyze_competitors_with_retry
    from app.models.insight import Insight

    logger.info("Starting run_competitive_intel_auto_task")
    try:
        async with AsyncSessionLocal() as session:
            stale_cutoff = datetime.now(UTC) - timedelta(days=30)
            # Find insights that need competitor refresh
            result = await session.execute(
                select(Insight)
                .where(Insight.relevance_score >= 0.7)
                .where(
                    or_(
                        Insight.updated_at < stale_cutoff,
                        Insight.updated_at.is_(None),
                    )
                )
                .order_by(Insight.relevance_score.desc())
                .limit(5)
            )
            insights = result.scalars().all()

            if not insights:
                return {"status": "completed", "items": 0, "reason": "no_stale_insights"}

            processed = 0
            for insight in insights:
                try:
                    await analyze_competitors_with_retry(insight.id, session)
                    processed += 1
                except Exception as e:
                    logger.error(f"Competitive intel failed for insight {insight.id}: {e}")

            await session.commit()

        return {"status": "completed", "items": processed, "total": len(insights)}
    except Exception as e:
        logger.error(f"run_competitive_intel_auto_task failed: {e}")
        return {"status": "error", "error": str(e)}


async def run_market_intel_auto_task(ctx: dict[str, Any]) -> dict[str, Any]:
    """Auto-generate market reports for trending insights (Phase D)."""
    from sqlalchemy import select

    from app.agents.market_intel_agent import generate_market_report
    from app.models.insight import Insight

    logger.info("Starting run_market_intel_auto_task")
    try:
        async with AsyncSessionLocal() as session:
            # Pick top 3 insights by score for market analysis
            result = await session.execute(
                select(Insight)
                .where(Insight.relevance_score >= 0.8)
                .order_by(Insight.relevance_score.desc())
                .limit(3)
            )
            insights = result.scalars().all()

            if not insights:
                return {"status": "completed", "items": 0, "reason": "no_high_score_insights"}

            processed = 0
            for insight in insights:
                try:
                    await generate_market_report(insight.id, session)
                    processed += 1
                except Exception as e:
                    logger.error(f"Market intel failed for insight {insight.id}: {e}")

            await session.commit()

        return {"status": "completed", "items": processed, "total": len(insights)}
    except Exception as e:
        logger.error(f"run_market_intel_auto_task failed: {e}")
        return {"status": "error", "error": str(e)}


async def send_weekly_digest_task(ctx: dict[str, Any]) -> dict[str, Any]:
    """Send weekly digest of top insights to opted-in users via Resend."""
    import hashlib
    from datetime import UTC, date, datetime, timedelta

    from sqlalchemy import desc, select

    from app.models.insight import Insight
    from app.models.user import User
    from app.models.user_preferences import EmailPreferences, EmailSend
    from app.services.email_service import send_weekly_digest

    logger.info("Starting weekly digest task")
    try:
        async with AsyncSessionLocal() as session:
            # Get top 10 insights from past week
            one_week_ago = datetime.now(UTC) - timedelta(days=7)
            result = await session.execute(
                select(Insight)
                .where(Insight.created_at >= one_week_ago)
                .order_by(desc(Insight.relevance_score))
                .limit(10)
            )
            insights = result.scalars().all()

            if not insights:
                return {"status": "completed", "sent": 0, "reason": "no_insights_this_week"}

            # Format insights for email template
            insight_list = [
                {
                    "title": i.title or i.proposed_solution[:80],
                    "problem_statement": i.problem_statement[:150],
                    "relevance_score": f"{(i.relevance_score or 0) * 100:.0f}%",
                    "market_size": i.market_size_estimate or "Unknown",
                }
                for i in insights
            ]

            # Get users opted in to weekly digest
            subscribers_result = await session.execute(
                select(EmailPreferences, User)
                .join(User, EmailPreferences.user_id == User.id)
                .where(EmailPreferences.weekly_digest.is_(True))
                .where(EmailPreferences.unsubscribed_at.is_(None))
                .where(User.deleted_at.is_(None))
            )
            subscribers = subscribers_result.all()

            if not subscribers:
                logger.info("No subscribers for weekly digest")
                return {"status": "completed", "sent": 0, "reason": "no_subscribers"}

            sent = 0
            skipped = 0
            for prefs, user in subscribers:
                # Dedup: one weekly digest per user per week
                content_hash = hashlib.sha256(
                    f"weekly_{date.today().isocalendar()[1]}_{user.id}".encode()
                ).hexdigest()

                existing = await session.execute(
                    select(EmailSend).where(
                        EmailSend.user_id == user.id,
                        EmailSend.content_hash == content_hash,
                    )
                )
                if existing.scalar_one_or_none():
                    skipped += 1
                    continue

                try:
                    from itsdangerous import URLSafeTimedSerializer

                    serializer = URLSafeTimedSerializer(settings.jwt_secret or "dev-secret")
                    unsub_token = serializer.dumps(str(user.id), salt="email-unsubscribe")

                    await send_weekly_digest(
                        email=user.email,
                        name=user.display_name or "there",
                        insights=insight_list,
                        dashboard_url=f"{settings.app_url}/insights",
                        unsubscribe_url=f"{settings.app_url}/api/email/unsubscribe?token={unsub_token}",
                    )

                    session.add(EmailSend(
                        user_id=user.id,
                        email_type="weekly_digest",
                        content_hash=content_hash,
                    ))
                    sent += 1
                except Exception:
                    logger.exception(f"Failed to send weekly digest to user {user.id}")

            await session.commit()

        logger.info(f"Weekly digest: sent={sent}, skipped={skipped}")
        return {"status": "completed", "sent": sent, "skipped": skipped, "insights": len(insights)}
    except Exception as e:
        logger.error(f"Weekly digest failed: {e}")
        return {"status": "error", "error": str(e)}


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

    # Check if scraper is paused via Redis flag
    try:
        import redis.asyncio as aioredis

        r = aioredis.from_url(settings.redis_url)
        paused = await r.get(f"scraper:paused:{source_name}")
        await r.aclose()
        if paused:
            logger.info(f"{source_name} scraper is paused, skipping")
            return {
                "status": "skipped",
                "source": source_name,
                "reason": "paused",
            }
    except Exception as e:
        logger.debug(f"Could not check pause flag for {source_name}: {e}")

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
        RedditScraper(subreddits=["startups", "SaaS"], limit=50, time_filter="day"),
    )


async def scrape_product_hunt_task(ctx: dict[str, Any]) -> dict[str, Any]:
    """Background task to scrape Product Hunt for daily launches."""
    return await _run_scraper(
        "product_hunt",
        ProductHuntScraper(days_back=1, limit=30),
    )


async def scrape_trends_task(ctx: dict[str, Any]) -> dict[str, Any]:
    """Background task to scrape Google Trends for multiple regions."""
    regions = [
        ("US", "United States"),
        ("GB", "United Kingdom"),
        ("DE", "Germany"),
        ("JP", "Japan"),
        ("SG", "Singapore"),
        ("AU", "Australia"),
    ]
    all_results = []
    for geo, name in regions:
        result = await _run_scraper(
            f"google_trends_{geo}",
            GoogleTrendsScraper(keywords=None, timeframe="now 7-d", geo=geo),
        )
        all_results.append(result)

    total_signals = sum(
        r.get("signals_saved", 0) for r in all_results if r.get("status") == "success"
    )
    return {
        "status": "success",
        "source": "google_trends_multi_region",
        "signals_saved": total_signals,
        "regions": len(regions),
        "details": all_results,
    }


async def scrape_twitter_task(ctx: dict[str, Any]) -> dict[str, Any]:
    """Background task to scrape Twitter/X for startup discussions."""
    return await _run_scraper(
        "twitter",
        TwitterScraper(),
    )


async def scrape_hackernews_task(ctx: dict[str, Any]) -> dict[str, Any]:
    """Background task to scrape Hacker News for top stories and Show HN posts."""
    return await _run_scraper(
        "hacker_news",
        HackerNewsScraper(min_score=50, max_results=30),
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
    from datetime import UTC, datetime, timedelta

    from sqlalchemy import desc, select

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
                    now = datetime.now(UTC)
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
        "twitter": await scrape_twitter_task(ctx),
        "hacker_news": await scrape_hackernews_task(ctx),
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
    # CRITICAL: Every task enqueued by scheduler.py MUST be listed here,
    # otherwise Arq silently drops the job.
    functions = [
        # Scraping tasks
        scrape_reddit_task,
        scrape_product_hunt_task,
        scrape_trends_task,
        scrape_twitter_task,
        scrape_hackernews_task,
        scrape_all_sources_task,
        # Analysis
        analyze_signals_task,
        hourly_trends_update_task,
        # Agent tasks (Phase 16.1 - previously missing, scheduler enqueued but never ran)
        market_insight_publisher_task,
        market_insight_quality_review_task,
        insight_quality_audit_task,
        # Task modules (Phase 16.1 - previously missing)
        fetch_daily_insight_task,
        send_daily_digests_task,
        update_success_stories_task,
        # Phase 17: Content automation pipeline
        run_content_pipeline_task,
        run_research_agent_auto_task,
        # Phase D: Content volume & quality automation
        run_content_generator_auto_task,
        run_competitive_intel_auto_task,
        run_market_intel_auto_task,
        # Phase L: Weekly digest
        send_weekly_digest_task,
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
        # Analyze signals 30min after each scrape cycle
        cron(
            analyze_signals_task,
            hour={0, 6, 12, 18},
            minute=30,
            run_at_startup=False,
        ),
        # Daily insight selection at 08:00 UTC
        cron(
            fetch_daily_insight_task,
            hour=8,
            minute=0,
            run_at_startup=False,
        ),
        # Daily digest at 09:00 UTC
        cron(
            send_daily_digests_task,
            hour=9,
            minute=0,
            run_at_startup=False,
        ),
        # Weekly digest every Monday at 09:00
        cron(
            send_weekly_digest_task,
            weekday="mon",
            hour=9,
            minute=0,
            run_at_startup=False,
        ),
        # Weekly market report every Wednesday at 06:00 UTC
        cron(
            market_insight_publisher_task,
            weekday="wed",
            hour=6,
            minute=0,
            run_at_startup=False,
        ),
        # Weekly success stories every Sunday at 10:00 UTC
        cron(
            update_success_stories_task,
            weekday="sun",
            hour=10,
            minute=0,
            run_at_startup=False,
        ),
        # Quality audit after analysis (1h after scrape cycle)
        cron(
            insight_quality_audit_task,
            hour={1, 7, 13, 19},
            minute=0,
            run_at_startup=False,
        ),
    ]

    # Startup and shutdown hooks
    on_startup = startup
    on_shutdown = shutdown

    # Worker settings
    max_jobs = 10  # Max concurrent jobs
    job_timeout = 600  # 10 minutes timeout per job
    keep_result = 3600  # Keep job results for 1 hour
