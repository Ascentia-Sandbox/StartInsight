"""Market Insight Publisher Agent - Auto-generates professional market insight articles.

Runs every 3 days to produce data-driven market analysis articles
based on current trends, insights, and market data.

Superadmin-only access via Agent Management page.
"""

import asyncio
import logging
import re
from datetime import UTC, datetime
from uuid import uuid4

from pydantic import BaseModel, Field
from pydantic_ai import Agent
from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.db.session import AsyncSessionLocal
from app.models.agent_control import AgentConfiguration
from app.models.insight import Insight
from app.models.market_insight import MarketInsight
from app.models.trend import Trend

logger = logging.getLogger(__name__)

AGENT_NAME = "market_insight_publisher"


# ============================================================================
# PYDANTIC SCHEMAS
# ============================================================================


class MarketInsightArticle(BaseModel):
    """Schema for AI-generated market insight article."""

    title: str = Field(
        description="Compelling article title (50-80 chars). "
        "Data-driven, specific. E.g., 'AI Code Review Market Hits $2.3B: 5 Trends Driving Growth'"
    )
    summary: str = Field(
        description="Article summary (2-3 sentences, 150-200 chars). "
        "Hook the reader with a key insight or statistic."
    )
    content: str = Field(
        description="Full article in Markdown (1500-2500 words). Must include: "
        "## Executive Summary, ## Key Data Points (with specific numbers), "
        "## Market Trends (3-5 trends with evidence), ## Opportunities for Founders, "
        "## What This Means for You. Use tables, bullet points, and bold for readability."
    )
    category: str = Field(
        description="One of: Trends, Analysis, Guides, Case Studies"
    )
    reading_time_minutes: int = Field(
        ge=3, le=15,
        description="Estimated reading time based on content length"
    )


# ============================================================================
# AGENT DEFINITION
# ============================================================================

market_insight_publisher_agent = Agent(
    model=settings.default_llm_model,
    output_type=MarketInsightArticle,
    system_prompt="""You are a senior market analyst at StartInsight, a startup intelligence platform.

Your job is to write professional, data-driven market insight articles that help founders
make informed decisions about emerging opportunities.

Writing guidelines:
- Lead with specific data points and statistics (numbers, percentages, dollar amounts)
- Reference real market trends, search volume data, and growth metrics
- Compare opportunities across sectors (SaaS, AI, FinTech, etc.)
- Include actionable takeaways for solo founders and small teams
- Use professional but accessible tone — not academic, not casual
- Structure with clear headers, bullet points, and tables for scanability
- Every claim should reference data: trend volumes, growth rates, or market sizes
- Include a "What This Means for You" section with concrete next steps

Content quality standards:
- NO generic advice like "do market research" or "build an MVP"
- Every paragraph must contain at least one specific data point
- Trends must be connected to specific startup opportunities
- Market sizes must use real ranges ($1B-$5B), not vague terms
- Include competitor landscape context where relevant
""",
)


# ============================================================================
# CORE FUNCTIONS
# ============================================================================


def _slugify(title: str) -> str:
    """Convert title to URL-friendly slug."""
    slug = title.lower().strip()
    slug = re.sub(r'[^\w\s-]', '', slug)
    slug = re.sub(r'[\s_]+', '-', slug)
    slug = re.sub(r'-+', '-', slug)
    return slug[:200]


async def _is_agent_enabled(session: AsyncSession) -> bool:
    """Check if this agent is enabled in AgentConfiguration."""
    result = await session.execute(
        select(AgentConfiguration).where(
            AgentConfiguration.agent_name == AGENT_NAME
        )
    )
    config = result.scalar_one_or_none()
    if config is None:
        return True  # Default to enabled if not configured
    return config.is_enabled


async def _gather_market_context(session: AsyncSession) -> str:
    """Gather current market data from insights and trends for article generation."""
    # Top trending keywords by growth
    trends_result = await session.execute(
        select(Trend)
        .order_by(Trend.growth_percentage.desc().nulls_last())
        .limit(15)
    )
    trends = trends_result.scalars().all()

    # Recent high-scoring insights
    insights_result = await session.execute(
        select(Insight)
        .where(Insight.relevance_score >= 0.7)
        .where(Insight.opportunity_score >= 7)
        .order_by(Insight.created_at.desc())
        .limit(10)
    )
    insights = insights_result.scalars().all()

    # Insight statistics
    stats_result = await session.execute(
        text("""
            SELECT
                COUNT(*) as total,
                AVG(opportunity_score) as avg_opp,
                AVG(feasibility_score) as avg_feas,
                COUNT(CASE WHEN opportunity_score >= 8 THEN 1 END) as high_opp
            FROM insights
            WHERE created_at > NOW() - INTERVAL '30 days'
        """)
    )
    stats = stats_result.one()

    # Build context string
    context_parts = [
        "## Current Market Data\n",
        f"Total insights analyzed (last 30 days): {stats[0]}",
        f"Average opportunity score: {stats[1]:.1f}/10" if stats[1] else "",
        f"High-opportunity ideas (8+): {stats[3]}",
        "\n## Top Trending Keywords (by growth):\n",
    ]

    for t in trends:
        growth_str = f"+{t.growth_percentage:.0f}%" if t.growth_percentage else "N/A"
        vol_str = f"{t.search_volume:,.0f}" if t.search_volume else "N/A"
        context_parts.append(f"- {t.keyword}: Volume {vol_str}, Growth {growth_str}")

    context_parts.append("\n## Recent High-Scoring Startup Opportunities:\n")
    for i in insights:
        scores = []
        if i.opportunity_score:
            scores.append(f"Opp:{i.opportunity_score}")
        if i.feasibility_score:
            scores.append(f"Feas:{i.feasibility_score}")
        if i.why_now_score:
            scores.append(f"Timing:{i.why_now_score}")
        context_parts.append(
            f"- **{i.proposed_solution}** ({', '.join(scores)}) "
            f"— Market: {i.market_size_estimate}"
        )

    # Recent articles to avoid duplication
    recent_articles = await session.execute(
        select(MarketInsight.title)
        .order_by(MarketInsight.created_at.desc())
        .limit(5)
    )
    recent_titles = [r[0] for r in recent_articles]
    if recent_titles:
        context_parts.append("\n## Recently Published Articles (AVOID similar topics):\n")
        for title in recent_titles:
            context_parts.append(f"- {title}")

    return "\n".join(filter(None, context_parts))


async def generate_market_insight_article(session: AsyncSession) -> MarketInsight | None:
    """Generate and publish a new market insight article.

    Returns the created MarketInsight or None if agent is disabled.
    """
    if not await _is_agent_enabled(session):
        logger.info(f"Agent '{AGENT_NAME}' is disabled, skipping article generation")
        return None

    logger.info("Generating new market insight article...")

    # Gather market context
    context = await _gather_market_context(session)

    # Generate article via LLM
    prompt = (
        f"Write a professional market insight article based on this current data:\n\n"
        f"{context}\n\n"
        f"Today's date: {datetime.now(UTC).strftime('%B %d, %Y')}\n\n"
        f"Create a compelling, data-driven article that synthesizes these trends "
        f"into actionable insights for startup founders. Focus on a specific angle "
        f"or theme that emerges from the data."
    )

    try:
        result = await asyncio.wait_for(
            market_insight_publisher_agent.run(prompt), timeout=settings.llm_call_timeout
        )
        article_data = result.output
    except TimeoutError:
        logger.error("Market insight publisher agent timed out after 120s")
        raise
    except Exception as e:
        logger.error(f"Market insight generation failed: {e}")
        raise

    # Create the article
    slug = _slugify(article_data.title)
    # Ensure unique slug
    existing = await session.execute(
        select(MarketInsight).where(MarketInsight.slug == slug)
    )
    if existing.scalar_one_or_none():
        slug = f"{slug}-{datetime.now(UTC).strftime('%Y%m%d')}"

    now = datetime.now(UTC)
    article = MarketInsight(
        id=uuid4(),
        title=article_data.title,
        slug=slug,
        summary=article_data.summary,
        content=article_data.content,
        category=article_data.category,
        author_name="StartInsight AI",
        reading_time_minutes=article_data.reading_time_minutes,
        is_published=False,  # Draft first, quality reviewer publishes
        is_featured=False,
        created_at=now,
    )

    session.add(article)
    await session.commit()
    await session.refresh(article)

    logger.info(f"Generated market insight article: '{article.title}' (draft, id={article.id})")
    return article


async def run_market_insight_publisher() -> dict:
    """Entry point for scheduled execution."""
    async with AsyncSessionLocal() as session:
        try:
            article = await generate_market_insight_article(session)
            if article:
                return {
                    "status": "success",
                    "article_id": str(article.id),
                    "title": article.title,
                }
            return {"status": "skipped", "reason": "agent_disabled"}
        except Exception as e:
            logger.error(f"Market insight publisher failed: {e}", exc_info=True)
            return {"status": "error", "error": str(e)}
