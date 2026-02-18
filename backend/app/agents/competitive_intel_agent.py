"""Competitive Intelligence AI Agent - Analyze competitors and generate strategic insights"""

import asyncio
import logging
from datetime import UTC, datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, Field
from pydantic_ai import Agent, RunContext
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.models.competitor_profile import CompetitorProfile
from app.models.insight import Insight

logger = logging.getLogger(__name__)


# ============================================================================
# PYDANTIC SCHEMAS
# ============================================================================

class CompetitorAnalysis(BaseModel):
    """AI-generated analysis of a single competitor"""

    competitor_id: str = Field(..., description="Competitor profile ID")
    strengths: list[str] = Field(
        ...,
        min_length=2,
        max_length=5,
        description="List of 2-5 key strengths",
    )
    weaknesses: list[str] = Field(
        ...,
        min_length=2,
        max_length=5,
        description="List of 2-5 key weaknesses",
    )
    market_position: str = Field(
        ...,
        description="Market position category: 'leader', 'challenger', 'niche', 'startup'",
    )
    positioning_x: int = Field(
        ...,
        ge=1,
        le=10,
        description="X-axis position in 2x2 matrix (price: 1=low, 10=high)",
    )
    positioning_y: int = Field(
        ...,
        ge=1,
        le=10,
        description="Y-axis position in 2x2 matrix (features: 1=few, 10=many)",
    )
    differentiation_strategy: str = Field(
        ...,
        description="How this competitor differentiates itself (1-2 sentences)",
    )


class MarketGapAnalysis(BaseModel):
    """AI-generated analysis of market gaps and opportunities"""

    gaps: list[str] = Field(
        ...,
        min_length=1,
        max_length=5,
        description="List of 1-5 market gaps identified from competitor analysis",
    )
    opportunities: list[str] = Field(
        ...,
        min_length=1,
        max_length=5,
        description="List of 1-5 opportunities for differentiation",
    )
    recommended_positioning: str = Field(
        ...,
        description="Recommended market positioning for the startup idea (2-3 sentences)",
    )


class CompetitiveIntelligenceReport(BaseModel):
    """Complete competitive intelligence report"""

    insight_id: str = Field(..., description="Insight ID this report is for")
    total_competitors: int = Field(..., description="Number of competitors analyzed")

    competitor_analyses: list[CompetitorAnalysis] = Field(
        ...,
        description="Individual competitor analyses",
    )

    market_gap_analysis: MarketGapAnalysis = Field(
        ...,
        description="Market gaps and opportunities",
    )

    positioning_matrix_description: str = Field(
        ...,
        description="Description of the 2x2 positioning matrix (price vs features)",
    )

    executive_summary: str = Field(
        ...,
        description="Executive summary of competitive landscape (3-5 sentences)",
    )

    generated_at: str = Field(
        default_factory=lambda: datetime.now(UTC).isoformat(),
        description="Timestamp when report was generated",
    )


# ============================================================================
# AI AGENT SYSTEM PROMPT
# ============================================================================

COMPETITIVE_INTELLIGENCE_SYSTEM_PROMPT = """You are a competitive intelligence analyst specializing in startup market positioning.

Your job is to analyze competitor data and generate strategic insights about:
1. Competitor strengths and weaknesses
2. Market positioning (price vs features)
3. Market gaps and differentiation opportunities

**Analysis Framework:**

1. **Competitor Strengths** (2-5 per competitor)
   - Look for: brand recognition, feature depth, user base size, pricing advantage, technical capabilities
   - Example: "Strong brand recognition in enterprise market"

2. **Competitor Weaknesses** (2-5 per competitor)
   - Look for: high pricing, limited features, poor UX, lack of API, slow performance
   - Example: "High pricing excludes SMB customers"

3. **Market Position Categories:**
   - **Leader**: Dominant player, high brand recognition, extensive features, highest pricing
   - **Challenger**: Strong competitor, good feature set, competitive pricing
   - **Niche**: Focused on specific use case or vertical, limited scope
   - **Startup**: New entrant, limited features, low pricing, rapid innovation

4. **Positioning Matrix (2x2):**
   - X-axis: Price (1=low, 10=high)
   - Y-axis: Features (1=few features, 10=many features)
   - Position competitors based on pricing tier and feature breadth
   - Examples:
     - Leader: X=8-10, Y=8-10 (high price, many features)
     - Startup: X=1-3, Y=1-3 (low price, few features)
     - Niche: X=5-7, Y=4-6 (mid price, specialized features)

5. **Market Gaps:**
   - Identify underserved price/feature combinations
   - Look for segments competitors ignore
   - Example: "No competitors offer AI-powered insights at SMB pricing ($29/mo)"

6. **Differentiation Opportunities:**
   - Suggest unique positioning based on gaps
   - Consider: pricing, features, target audience, delivery model
   - Example: "Position as 'AI-first' alternative with automated insights"

**Output Requirements:**
- Be specific and actionable
- Use data from competitor profiles (pricing, features, metrics)
- Avoid generic statements like "good product" - quantify when possible
- Focus on strategic insights that help differentiate the startup idea

**Tone:** Professional, strategic, data-driven
"""


# ============================================================================
# AI AGENT DEFINITION
# ============================================================================

competitive_intel_agent = Agent(
    model=settings.default_llm_model,
    output_type=CompetitiveIntelligenceReport,
    system_prompt=COMPETITIVE_INTELLIGENCE_SYSTEM_PROMPT,
)


# ============================================================================
# AGENT DEPENDENCY INJECTION
# ============================================================================

@competitive_intel_agent.system_prompt
async def add_competitor_context(ctx: RunContext[dict[str, Any]]) -> str:
    """
    Add competitor data context to system prompt.

    This dependency is injected into the agent's system prompt,
    providing competitor profiles and startup idea details.
    """
    competitors = ctx.deps.get("competitors", [])
    insight = ctx.deps.get("insight", {})

    if not competitors:
        return "No competitor data available."

    # Format competitor data for LLM context
    competitor_context = f"""
**Startup Idea:**
- Problem: {insight.get('problem_statement', 'N/A')[:300]}
- Solution: {insight.get('proposed_solution', 'N/A')[:300]}
- Market: {insight.get('market_size', 'N/A')[:200]}

**Competitors to Analyze ({len(competitors)} total):**

"""

    for i, comp in enumerate(competitors, start=1):
        competitor_context += f"""
{i}. **{comp['name']}** ({comp['url']})
   - Description: {comp['description'] or 'N/A'}
   - Value Proposition: {comp['value_proposition'] or 'N/A'}
   - Target Audience: {comp['target_audience'] or 'N/A'}
   - Pricing: {comp['metrics'].get('pricing', 'N/A')}
   - Features: {list(comp['features'].keys())[:10] if comp['features'] else 'N/A'}
   - Team Size: {comp['metrics'].get('team_size', 'N/A')}
   - Funding: {comp['metrics'].get('funding', 'N/A')}

"""

    competitor_context += """
**Your Task:**
1. Analyze each competitor's strengths and weaknesses
2. Categorize their market position (leader/challenger/niche/startup)
3. Position them on price vs features matrix (1-10 scale)
4. Identify market gaps and differentiation opportunities
5. Generate executive summary of competitive landscape
"""

    return competitor_context


# ============================================================================
# SERVICE FUNCTIONS
# ============================================================================

async def analyze_competitors_with_retry(
    insight_id: UUID,
    session: AsyncSession,
    max_retries: int = 3,
) -> CompetitiveIntelligenceReport:
    """
    Analyze competitors using AI agent with retry logic.

    Args:
        insight_id: Insight ID to analyze competitors for
        session: Database session
        max_retries: Maximum number of retry attempts

    Returns:
        CompetitiveIntelligenceReport with competitor analysis

    Raises:
        ValueError: If no competitors found or analysis fails
    """
    logger.info(f"Analyzing competitors for insight {insight_id}")

    # Fetch insight
    stmt = select(Insight).where(Insight.id == insight_id)
    result = await session.execute(stmt)
    insight = result.scalar_one_or_none()

    if not insight:
        raise ValueError(f"Insight {insight_id} not found")

    # Fetch competitors
    stmt = select(CompetitorProfile).where(CompetitorProfile.insight_id == insight_id)
    result = await session.execute(stmt)
    competitors = result.scalars().all()

    if not competitors or len(competitors) == 0:
        raise ValueError(f"No competitors found for insight {insight_id}. Please scrape competitors first.")

    logger.info(f"Found {len(competitors)} competitors to analyze")

    # Prepare competitor data for agent
    competitor_data = [
        {
            "id": str(c.id),
            "name": c.name,
            "url": c.url,
            "description": c.description,
            "value_proposition": c.value_proposition,
            "target_audience": c.target_audience,
            "metrics": c.metrics or {},
            "features": c.features or {},
        }
        for c in competitors
    ]

    # Prepare insight data for agent
    insight_data = {
        "problem_statement": insight.problem_statement,
        "proposed_solution": insight.proposed_solution,
        "market_size": insight.market_size_estimate,
    }

    # Run agent with retry logic
    for attempt in range(max_retries):
        try:
            logger.info(f"Running competitive intelligence agent (attempt {attempt + 1}/{max_retries})")

            result = await asyncio.wait_for(
                competitive_intel_agent.run(
                    user_prompt=f"Analyze the {len(competitors)} competitors for this startup idea and generate a competitive intelligence report.",
                    deps={
                        "competitors": competitor_data,
                        "insight": insight_data,
                    },
                ),
                timeout=settings.llm_call_timeout,
            )

            report = result.output

            # Update competitor profiles with analysis results
            await _update_competitor_profiles_with_analysis(
                competitors=competitors,
                analyses=report.competitor_analyses,
                session=session,
            )

            logger.info(
                f"Competitive analysis complete: {len(report.competitor_analyses)} competitors analyzed, "
                f"{len(report.market_gap_analysis.gaps)} gaps identified"
            )

            return report

        except Exception as e:
            logger.warning(
                f"Competitive analysis attempt {attempt + 1} failed: {type(e).__name__} - {e}"
            )
            if attempt == max_retries - 1:
                # Last attempt failed
                raise ValueError(
                    f"Competitive analysis failed after {max_retries} attempts: {str(e)}"
                )
            # Retry with exponential backoff
            await asyncio.sleep(2 ** attempt)


async def _update_competitor_profiles_with_analysis(
    competitors: list[CompetitorProfile],
    analyses: list[CompetitorAnalysis],
    session: AsyncSession,
) -> None:
    """
    Update competitor profiles with AI-generated analysis results.

    Args:
        competitors: List of CompetitorProfile objects
        analyses: List of CompetitorAnalysis from AI agent
        session: Database session
    """
    # Create mapping of competitor_id -> analysis
    analysis_map = {a.competitor_id: a for a in analyses}

    for competitor in competitors:
        competitor_id_str = str(competitor.id)
        if competitor_id_str not in analysis_map:
            logger.warning(f"No analysis found for competitor {competitor_id_str}")
            continue

        analysis = analysis_map[competitor_id_str]

        # Update competitor profile with AI analysis
        competitor.strengths = analysis.strengths
        competitor.weaknesses = analysis.weaknesses
        competitor.market_position = analysis.market_position
        competitor.positioning_x = analysis.positioning_x
        competitor.positioning_y = analysis.positioning_y
        competitor.analysis_generated_at = datetime.now(UTC)
        competitor.analysis_model = "gemini-2.0-flash"

        session.add(competitor)

    await session.commit()
    logger.info(f"Updated {len(competitors)} competitor profiles with AI analysis")
