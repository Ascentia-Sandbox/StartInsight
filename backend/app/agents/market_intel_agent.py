"""Market Intelligence AI Agent - Generate market reports and industry analysis.

Sprint 3.3: Provides AI-powered market intelligence including:
- TAM/SAM/SOM market sizing calculations
- Industry benchmark analysis
- Weekly market digest generation
- Trend-to-opportunity mapping
"""

import asyncio
import logging
from datetime import UTC, datetime

from app.agents.sentry_tracing import trace_agent_run
from typing import Any
from uuid import UUID

from pydantic import BaseModel, Field
from pydantic_ai import Agent, RunContext
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.models.insight import Insight
from app.models.trend import Trend

logger = logging.getLogger(__name__)


# ============================================================================
# PYDANTIC SCHEMAS
# ============================================================================

class MarketSizing(BaseModel):
    """TAM/SAM/SOM market sizing analysis"""

    tam: dict[str, Any] = Field(
        ...,
        description="Total Addressable Market (global market size)",
    )
    sam: dict[str, Any] = Field(
        ...,
        description="Serviceable Addressable Market (target segment)",
    )
    som: dict[str, Any] = Field(
        ...,
        description="Serviceable Obtainable Market (realistic capture)",
    )
    methodology: str = Field(
        ...,
        description="How these numbers were calculated (bottom-up or top-down)",
    )
    assumptions: list[str] = Field(
        ...,
        min_length=2,
        max_length=5,
        description="Key assumptions in the calculation",
    )
    confidence_level: str = Field(
        ...,
        description="Confidence level: 'high', 'medium', 'low'",
    )


class IndustryBenchmark(BaseModel):
    """Industry benchmark metrics"""

    metric_name: str = Field(..., description="Name of the benchmark metric")
    industry_average: str = Field(..., description="Industry average value")
    top_performer: str = Field(..., description="Top performer value")
    startup_target: str = Field(..., description="Recommended target for startup")
    source: str = Field(default="Industry analysis", description="Data source")


class TrendOpportunity(BaseModel):
    """Mapping of trend to business opportunity"""

    trend_keyword: str = Field(..., description="Trend keyword")
    opportunity_score: int = Field(
        ...,
        ge=1,
        le=100,
        description="Opportunity score 1-100",
    )
    business_implications: str = Field(
        ...,
        description="How this trend creates business opportunity",
    )
    action_items: list[str] = Field(
        ...,
        min_length=1,
        max_length=3,
        description="Specific action items to capitalize on this trend",
    )
    time_sensitivity: str = Field(
        ...,
        description="Time sensitivity: 'urgent', 'near-term', 'long-term'",
    )


class MarketIntelligenceReport(BaseModel):
    """Complete market intelligence report"""

    report_id: str = Field(..., description="Unique report identifier")
    report_type: str = Field(
        ...,
        description="Report type: 'weekly_digest', 'market_sizing', 'competitive_landscape'",
    )
    title: str = Field(..., description="Report title")
    executive_summary: str = Field(
        ...,
        description="Executive summary (3-5 sentences)",
    )

    # Market sizing (optional, for market_sizing reports)
    market_sizing: MarketSizing | None = Field(
        None,
        description="TAM/SAM/SOM analysis",
    )

    # Industry benchmarks
    industry_benchmarks: list[IndustryBenchmark] = Field(
        default_factory=list,
        description="Relevant industry benchmarks",
    )

    # Trend opportunities
    trend_opportunities: list[TrendOpportunity] = Field(
        default_factory=list,
        description="Trends mapped to opportunities",
    )

    # Key insights
    key_insights: list[str] = Field(
        ...,
        min_length=3,
        max_length=10,
        description="Key market insights",
    )

    # Recommendations
    recommendations: list[str] = Field(
        ...,
        min_length=2,
        max_length=5,
        description="Strategic recommendations",
    )

    generated_at: str = Field(
        default_factory=lambda: datetime.now(UTC).isoformat(),
        description="Timestamp when report was generated",
    )

    metadata: dict[str, Any] = Field(
        default_factory=dict,
        description="Additional metadata",
    )


# ============================================================================
# AI AGENT SYSTEM PROMPT
# ============================================================================

MARKET_INTEL_SYSTEM_PROMPT = """You are a market intelligence analyst specializing in startup market analysis and strategic planning.

Your job is to generate comprehensive market intelligence reports that help entrepreneurs make data-driven decisions.

**Analysis Framework:**

1. **Market Sizing (TAM/SAM/SOM)**
   - TAM (Total Addressable Market): Global market size if you captured 100%
   - SAM (Serviceable Addressable Market): Segment you can realistically target
   - SOM (Serviceable Obtainable Market): What you can realistically capture in 3-5 years

   Use both top-down (industry reports) and bottom-up (customer count × price) approaches.

   Example:
   - TAM: $50B (Global API monitoring market)
   - SAM: $5B (SMB SaaS companies in North America)
   - SOM: $50M (1% of SAM in first 3 years)

2. **Industry Benchmarks**
   Provide relevant metrics for the startup's industry:
   - Customer Acquisition Cost (CAC)
   - Lifetime Value (LTV)
   - LTV:CAC ratio
   - Churn rate
   - Net Revenue Retention (NRR)
   - Gross margin

3. **Trend-to-Opportunity Mapping**
   For each relevant trend:
   - Score opportunity (1-100) based on growth rate, market size, competition
   - Explain business implications
   - Provide specific action items
   - Rate time sensitivity (urgent/near-term/long-term)

4. **Weekly Digest Structure**
   - 3-5 key market developments
   - Emerging trends to watch
   - Competitor movements
   - Strategic recommendations

**Output Requirements:**
- Be specific with numbers (use $ amounts, percentages, timeframes)
- Cite data sources when possible
- Provide actionable recommendations
- Focus on insights that drive decisions, not just data

**Tone:** Professional, data-driven, actionable
"""


# ============================================================================
# AI AGENT DEFINITION
# ============================================================================

market_intel_agent = Agent(
    model=settings.default_llm_model,
    output_type=MarketIntelligenceReport,
    system_prompt=MARKET_INTEL_SYSTEM_PROMPT,
)


# ============================================================================
# AGENT DEPENDENCY INJECTION
# ============================================================================

@market_intel_agent.system_prompt
async def add_market_context(ctx: RunContext[dict[str, Any]]) -> str:
    """
    Add market data context to system prompt.

    Provides insight details, trend data, and industry context.
    """
    insight = ctx.deps.get("insight", {})
    trends = ctx.deps.get("trends", [])
    report_type = ctx.deps.get("report_type", "weekly_digest")

    context = f"""
**Report Type:** {report_type}

**Startup Idea:**
- Problem: {insight.get('problem_statement', 'N/A')[:500]}
- Solution: {insight.get('proposed_solution', 'N/A')[:500]}
- Market Size: {insight.get('market_size', 'N/A')[:300]}
- Target Audience: {insight.get('target_audience', 'N/A')[:300]}
- Revenue Model: {insight.get('revenue_model', 'N/A')[:300]}

"""

    if trends:
        context += f"""
**Relevant Trends ({len(trends)} total):**

"""
        for i, trend in enumerate(trends[:10], start=1):
            context += f"""
{i}. **{trend['keyword']}** (Category: {trend['category']})
   - Search Volume: {trend['search_volume']:,}/month
   - Growth: {trend['growth_percentage']}%
   - Business Implications: {trend.get('business_implications', 'N/A')[:200]}

"""

    context += """
**Your Task:**
Generate a comprehensive market intelligence report based on the startup idea and trend data.
Include market sizing (TAM/SAM/SOM), industry benchmarks, and trend-to-opportunity mapping.
"""

    return context


# ============================================================================
# SERVICE FUNCTIONS
# ============================================================================

async def generate_market_report(
    insight_id: UUID,
    session: AsyncSession,
    report_type: str = "market_sizing",
) -> MarketIntelligenceReport:
    """
    Generate market intelligence report for an insight.

    Args:
        insight_id: Insight ID to analyze
        session: Database session
        report_type: Type of report ('weekly_digest', 'market_sizing', 'competitive_landscape')

    Returns:
        MarketIntelligenceReport with market analysis

    Raises:
        ValueError: If insight not found
    """
    logger.info(f"Generating {report_type} report for insight {insight_id}")

    # Fetch insight
    stmt = select(Insight).where(Insight.id == insight_id)
    result = await session.execute(stmt)
    insight = result.scalar_one_or_none()

    if not insight:
        raise ValueError(f"Insight {insight_id} not found")

    # Fetch relevant trends (top 10 by volume)
    trends_stmt = select(Trend).where(
        Trend.is_published == True
    ).order_by(Trend.search_volume.desc()).limit(10)
    trends_result = await session.execute(trends_stmt)
    trends = trends_result.scalars().all()

    # Prepare insight data
    insight_data = {
        "problem_statement": insight.problem_statement,
        "proposed_solution": insight.proposed_solution,
        "market_size": insight.market_size_estimate,
        "target_audience": "startup founders",
        "revenue_model": "SaaS",
    }

    # Prepare trend data
    trend_data = [
        {
            "keyword": t.keyword,
            "category": t.category,
            "search_volume": t.search_volume or 0,
            "growth_percentage": t.growth_percentage or 0,
            "business_implications": t.business_implications,
        }
        for t in trends
    ]

    # Generate report via AI agent
    try:
        async with trace_agent_run("market_intel_agent"):
            result = await asyncio.wait_for(
                market_intel_agent.run(
                    user_prompt=f"Generate a {report_type} market intelligence report for this startup idea.",
                    deps={
                        "insight": insight_data,
                        "trends": trend_data,
                        "report_type": report_type,
                    },
                ),
                timeout=settings.llm_call_timeout,
            )

        report = result.output
        report.report_id = f"MIR-{insight_id.hex[:8]}-{datetime.now(UTC).strftime('%Y%m%d')}"
        report.metadata = {
            "insight_id": str(insight_id),
            "trends_analyzed": len(trends),
            "model": "gemini-2.0-flash",
        }

        logger.info(f"Generated market report {report.report_id} with {len(report.key_insights)} insights")
        return report

    except Exception as e:
        logger.error(f"Market report generation failed: {type(e).__name__} - {e}")
        raise ValueError(f"Report generation failed: {str(e)}")


async def generate_weekly_digest(
    session: AsyncSession,
) -> MarketIntelligenceReport:
    """
    Generate weekly market digest across all trends.

    This is a general market report not tied to a specific insight.

    Args:
        session: Database session

    Returns:
        MarketIntelligenceReport with weekly market digest
    """
    logger.info("Generating weekly market digest")

    # Get trending keywords (top 20 by growth)
    trends_stmt = select(Trend).where(
        Trend.is_published == True
    ).order_by(Trend.growth_percentage.desc()).limit(20)
    result = await session.execute(trends_stmt)
    trends = result.scalars().all()

    if not trends:
        raise ValueError("No trends available for digest generation")

    # Get recent insights count
    insights_count_stmt = select(func.count(Insight.id))
    insights_count = await session.scalar(insights_count_stmt) or 0

    # Prepare trend data
    trend_data = [
        {
            "keyword": t.keyword,
            "category": t.category,
            "search_volume": t.search_volume or 0,
            "growth_percentage": t.growth_percentage or 0,
            "business_implications": t.business_implications,
        }
        for t in trends
    ]

    # Generate digest via AI agent
    try:
        result = await asyncio.wait_for(market_intel_agent.run(
            user_prompt=f"""Generate a weekly market digest summarizing the top {len(trends)} trending topics.

This is a general market overview for entrepreneurs, not specific to any single startup idea.
Focus on:
1. Key market developments this week
2. Emerging trends to watch
3. Industry benchmarks for SaaS/tech startups
4. Strategic recommendations for entrepreneurs

Total insights in database: {insights_count}
""",
            deps={
                "insight": {
                    "problem_statement": "General market analysis for entrepreneurs",
                    "proposed_solution": "Market intelligence digest",
                    "market_size": "Global startup ecosystem",
                    "target_audience": "Entrepreneurs and startup founders",
                    "revenue_model": "N/A - general digest",
                },
                "trends": trend_data,
                "report_type": "weekly_digest",
            },
        ), timeout=settings.llm_call_timeout)

        report = result.output
        report.report_id = f"WD-{datetime.now(UTC).strftime('%Y%m%d-%H%M')}"
        report.report_type = "weekly_digest"
        report.metadata = {
            "trends_analyzed": len(trends),
            "insights_in_database": insights_count,
            "model": "gemini-2.0-flash",
        }

        logger.info(f"Generated weekly digest {report.report_id}")
        return report

    except Exception as e:
        logger.error(f"Weekly digest generation failed: {type(e).__name__} - {e}")
        raise ValueError(f"Digest generation failed: {str(e)}")


async def calculate_tam_sam_som(
    insight_id: UUID,
    session: AsyncSession,
) -> MarketSizing:
    """
    Calculate TAM/SAM/SOM for a specific insight.

    This is a focused market sizing calculation without the full report.

    Args:
        insight_id: Insight ID
        session: Database session

    Returns:
        MarketSizing with TAM/SAM/SOM calculations
    """
    logger.info(f"Calculating TAM/SAM/SOM for insight {insight_id}")

    report = await generate_market_report(
        insight_id=insight_id,
        session=session,
        report_type="market_sizing",
    )

    if not report.market_sizing:
        raise ValueError("Market sizing calculation failed")

    return report.market_sizing
