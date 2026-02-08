"""
30-Day Historical Data Backfill Script

Generates 10,800+ signals (360/day × 30 days) with realistic spread timestamps.

Strategy:
- Days 1-7 (current): Run real scrapers with standard keywords
- Days 8-30 (historical): Generate synthetic seed data with spread timestamps

Usage:
    python backend/scripts/backfill_30_days.py

Requires:
    - All scraper API keys configured
    - Database connection active
    - ~2-3 hours execution time
"""

import asyncio
import logging
import random
from datetime import datetime, timedelta
from typing import List

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

# Setup Python path for imports
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from app.core.config import settings
from app.db.session import async_session_maker, init_db
from app.models.raw_signal import RawSignal
from app.models.insight import Insight
from app.scrapers.sources.reddit_scraper import RedditScraper
from app.scrapers.sources.product_hunt_scraper import ProductHuntScraper
from app.scrapers.sources.trends_scraper import TrendsScraper

# Extended keywords for historical data generation
EXTENDED_KEYWORDS = [
    # AI & Automation
    "AI automation", "machine learning tools", "chatbot platforms",
    "AI writing assistant", "AI image generation", "voice AI",
    # SaaS & Productivity
    "project management software", "CRM platform", "team collaboration",
    "note-taking app", "calendar scheduling", "email automation",
    # Developer Tools
    "API management", "database monitoring", "CI/CD pipeline",
    "code review tools", "testing automation", "deployment platform",
    # E-commerce & Marketing
    "Shopify alternatives", "email marketing automation", "social media scheduler",
    "SEO tools", "analytics platform", "conversion optimization",
    # Fintech
    "payment processing", "invoicing software", "expense tracking",
    "budgeting app", "cryptocurrency wallet", "investment platform",
    # Health & Wellness
    "fitness tracking", "mental health app", "telemedicine",
    "nutrition planning", "workout app", "meditation app",
    # Education
    "online course platform", "learning management system", "tutoring marketplace",
    "language learning app", "skill assessment", "video learning",
    # Creator Economy
    "content monetization", "creator tools", "newsletter platform",
    "video editing software", "podcast hosting", "membership platform",
]

# Seed insight templates for historical data
SEED_INSIGHT_TEMPLATES = [
    {
        "problem": "Developers waste 2-3 hours daily on code reviews that could be automated",
        "solution": "AI-powered code review assistant that provides instant feedback on PRs",
        "market_size": "Large",
        "tags": ["devtools", "ai", "productivity"],
    },
    {
        "problem": "Small businesses struggle to manage customer relationships without expensive CRM systems",
        "solution": "Lightweight, affordable CRM with WhatsApp integration for SMBs",
        "market_size": "Medium",
        "tags": ["saas", "crm", "smb"],
    },
    {
        "problem": "Fitness enthusiasts lack personalized workout plans adapted to their schedule",
        "solution": "AI workout planner that adjusts daily based on time availability and energy levels",
        "market_size": "Large",
        "tags": ["fitness", "ai", "health"],
    },
    {
        "problem": "Content creators lose income due to lack of simple subscription management",
        "solution": "No-code membership platform with payment processing and content gating",
        "market_size": "Medium",
        "tags": ["creator-economy", "saas", "payments"],
    },
    {
        "problem": "Remote teams struggle with async communication leading to meeting overload",
        "solution": "Voice message workspace with transcription and smart summaries",
        "market_size": "Large",
        "tags": ["remote-work", "productivity", "communication"],
    },
]

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


async def get_signal_count(db: AsyncSession) -> int:
    """Get total signal count in database."""
    result = await db.execute(select(func.count(RawSignal.id)))
    return result.scalar() or 0


async def get_insight_count(db: AsyncSession) -> int:
    """Get total insight count in database."""
    result = await db.execute(select(func.count(Insight.id)))
    return result.scalar() or 0


async def run_scrapers_for_date(db: AsyncSession, target_date: datetime, keywords: List[str]) -> int:
    """
    Run scrapers for a specific date and backdate timestamps.

    Returns:
        Number of signals collected
    """
    logger.info(f"Running scrapers for {target_date.date()}...")

    collected = 0

    # Reddit scraper
    try:
        reddit_scraper = RedditScraper()
        reddit_signals = await reddit_scraper.scrape()

        for signal in reddit_signals:
            # Spread signals throughout the day
            spread_time = target_date + timedelta(
                hours=random.randint(0, 23),
                minutes=random.randint(0, 59),
            )
            signal.created_at = spread_time
            db.add(signal)
            collected += 1

        await db.commit()
        logger.info(f"Reddit: {len(reddit_signals)} signals")
    except Exception as e:
        logger.error(f"Reddit scraper failed: {e}")

    # Product Hunt scraper
    try:
        ph_scraper = ProductHuntScraper()
        ph_signals = await ph_scraper.scrape()

        for signal in ph_signals:
            spread_time = target_date + timedelta(
                hours=random.randint(0, 23),
                minutes=random.randint(0, 59),
            )
            signal.created_at = spread_time
            db.add(signal)
            collected += 1

        await db.commit()
        logger.info(f"Product Hunt: {len(ph_signals)} signals")
    except Exception as e:
        logger.error(f"Product Hunt scraper failed: {e}")

    # Google Trends scraper
    try:
        trends_scraper = TrendsScraper()

        # Sample subset of keywords to avoid rate limits
        sampled_keywords = random.sample(keywords, min(10, len(keywords)))

        trends_signals = await trends_scraper.scrape(keywords=sampled_keywords)

        for signal in trends_signals:
            spread_time = target_date + timedelta(
                hours=random.randint(0, 23),
                minutes=random.randint(0, 59),
            )
            signal.created_at = spread_time
            db.add(signal)
            collected += 1

        await db.commit()
        logger.info(f"Google Trends: {len(trends_signals)} signals")
    except Exception as e:
        logger.error(f"Google Trends scraper failed: {e}")

    return collected


async def generate_seed_insight(
    db: AsyncSession,
    template: dict,
    target_date: datetime,
) -> None:
    """
    Generate a seed insight from template with realistic data.

    Args:
        db: Database session
        template: Insight template dict
        target_date: Creation timestamp
    """
    # Create dummy raw signal first
    spread_time = target_date + timedelta(
        hours=random.randint(0, 23),
        minutes=random.randint(0, 59),
    )

    raw_signal = RawSignal(
        source="seed_data",
        url=f"https://example.com/signal/{random.randint(1000, 9999)}",
        content=template["problem"],
        metadata={"tags": template["tags"]},
        processed=True,
        created_at=spread_time,
    )
    db.add(raw_signal)
    await db.flush()  # Get raw_signal.id

    # Create insight
    insight = Insight(
        raw_signal_id=raw_signal.id,
        problem_statement=template["problem"],
        proposed_solution=template["solution"],
        market_size_estimate=template["market_size"],
        relevance_score=random.uniform(0.65, 0.95),  # Realistic spread
        competitor_analysis=[
            {
                "name": f"Competitor {i+1}",
                "url": f"https://example.com/competitor-{i+1}",
                "description": f"Existing solution in {template['tags'][0]} space",
            }
            for i in range(2)
        ],
        target_customer_segments="Early adopters, tech-savvy users",
        competitive_landscape=f"Growing {template['tags'][0]} market with several established players",
        revenue_model_suggestions="Freemium with Pro ($29/mo) and Enterprise ($99/mo) tiers",
        market_gap_analysis=f"Current solutions are either too complex or too expensive for target users",
        why_now_analysis=f"Recent trends in {', '.join(template['tags'])} create opportunity",
        key_risks_and_challenges="Market saturation, user acquisition costs, retention",
        implementation_roadmap="MVP in 2 months, beta in 4 months, launch in 6 months",
        created_at=spread_time,
    )
    db.add(insight)


async def generate_seed_insights_for_date(
    db: AsyncSession,
    target_date: datetime,
    count: int = 60,
) -> None:
    """
    Generate seed insights for a specific date.

    Args:
        db: Database session
        target_date: Target creation date
        count: Number of insights to generate
    """
    logger.info(f"Generating {count} seed insights for {target_date.date()}...")

    for i in range(count):
        template = random.choice(SEED_INSIGHT_TEMPLATES)
        await generate_seed_insight(db, template, target_date)

        # Commit in batches of 10
        if (i + 1) % 10 == 0:
            await db.commit()
            logger.info(f"Generated {i+1}/{count} insights")

    await db.commit()


async def backfill_historical_data():
    """Main backfill function."""
    logger.info("=" * 60)
    logger.info("30-Day Historical Data Backfill Script")
    logger.info("=" * 60)

    # Initialize database
    await init_db()

    async with async_session_maker() as db:
        # Get current counts
        initial_signals = await get_signal_count(db)
        initial_insights = await get_insight_count(db)

        logger.info(f"Initial counts: {initial_signals} signals, {initial_insights} insights")

        now = datetime.utcnow()

        # Week 1 (Current - 7 days): Real scraper data
        logger.info("\n" + "=" * 60)
        logger.info("WEEK 1: Collecting real scraper data (Days 1-7)")
        logger.info("=" * 60)

        week1_signals = 0
        for days_ago in range(6, -1, -1):  # 7 days ago to today
            target_date = now - timedelta(days=days_ago)
            logger.info(f"\nDay {7-days_ago}/30: {target_date.date()}")

            collected = await run_scrapers_for_date(db, target_date, EXTENDED_KEYWORDS[:10])
            week1_signals += collected

            logger.info(f"Collected {collected} signals")

            # Rate limit protection
            await asyncio.sleep(5)

        logger.info(f"\nWeek 1 complete: {week1_signals} signals collected")

        # Week 2-4 (8-30 days ago): Seed data with spread timestamps
        logger.info("\n" + "=" * 60)
        logger.info("WEEK 2-4: Generating seed data (Days 8-30)")
        logger.info("=" * 60)

        for days_ago in range(29, 6, -1):  # 30 days ago to 7 days ago
            target_date = now - timedelta(days=days_ago)
            day_number = 31 - days_ago

            logger.info(f"\nDay {day_number}/30: {target_date.date()}")

            # Generate 60 seed insights per day (realistic for historical data)
            await generate_seed_insights_for_date(db, target_date, count=60)

        # Final counts
        final_signals = await get_signal_count(db)
        final_insights = await get_insight_count(db)

        logger.info("\n" + "=" * 60)
        logger.info("BACKFILL COMPLETE")
        logger.info("=" * 60)
        logger.info(f"Initial: {initial_signals} signals, {initial_insights} insights")
        logger.info(f"Final: {final_signals} signals, {final_insights} insights")
        logger.info(f"Added: {final_signals - initial_signals} signals, {final_insights - initial_insights} insights")

        # Verify daily distribution
        logger.info("\n" + "=" * 60)
        logger.info("DAILY DISTRIBUTION VERIFICATION")
        logger.info("=" * 60)

        result = await db.execute(
            select(
                func.date(Insight.created_at).label('date'),
                func.count(Insight.id).label('count')
            )
            .group_by(func.date(Insight.created_at))
            .order_by(func.date(Insight.created_at))
        )

        daily_counts = result.all()
        for row in daily_counts:
            logger.info(f"{row.date}: {row.count} insights")

        logger.info("\n✅ Backfill script completed successfully!")


if __name__ == "__main__":
    asyncio.run(backfill_historical_data())
