"""Quality Review Agents - Ensure market insights and startup insights meet quality standards.

Two agents:
1. MarketInsightQualityReviewer - Reviews draft articles before publishing
2. InsightQualityReviewer - Audits startup insights for data completeness and accuracy

Superadmin-only access via Agent Management page.
"""

import asyncio
import logging
from datetime import UTC, datetime

from pydantic import BaseModel, Field
from pydantic_ai import Agent
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.db.session import AsyncSessionLocal
from app.models.agent_control import AgentConfiguration
from app.models.insight import Insight
from app.models.market_insight import MarketInsight

logger = logging.getLogger(__name__)


# ============================================================================
# SCHEMAS
# ============================================================================


class ArticleReview(BaseModel):
    """Quality review result for a market insight article."""

    quality_score: int = Field(
        ge=1, le=10,
        description="Overall quality score (1-10). 7+ is publishable."
    )
    data_accuracy: int = Field(
        ge=1, le=10,
        description="Are data points specific and realistic? (1-10)"
    )
    actionability: int = Field(
        ge=1, le=10,
        description="Does it provide concrete takeaways for founders? (1-10)"
    )
    readability: int = Field(
        ge=1, le=10,
        description="Is the article well-structured and easy to scan? (1-10)"
    )
    issues: list[str] = Field(
        default_factory=list,
        description="Specific issues found (empty if none). Max 5."
    )
    publish_recommendation: bool = Field(
        description="True if article meets quality bar for publishing"
    )
    improved_title: str | None = Field(
        default=None,
        description="Suggested improved title if original is weak, else null"
    )
    improved_summary: str | None = Field(
        default=None,
        description="Suggested improved summary if original is weak, else null"
    )


class InsightAuditResult(BaseModel):
    """Quality audit result for a startup insight."""

    completeness_score: int = Field(
        ge=1, le=10,
        description="How complete is the insight data? (1-10)"
    )
    missing_fields: list[str] = Field(
        default_factory=list,
        description="Fields that are null/empty but should have data"
    )
    score_consistency: bool = Field(
        description="Are the 8 dimension scores internally consistent?"
    )
    title_quality: int = Field(
        ge=1, le=10,
        description="Is proposed_solution a concise product name? (1-10)"
    )
    needs_reanalysis: bool = Field(
        description="True if insight should be re-analyzed by enhanced analyzer"
    )


# ============================================================================
# AGENT DEFINITIONS
# ============================================================================

MARKET_REVIEWER_NAME = "market_insight_quality_reviewer"
INSIGHT_REVIEWER_NAME = "insight_quality_reviewer"

market_review_agent = Agent(
    model=settings.default_llm_model,
    output_type=ArticleReview,
    system_prompt="""You are a senior editorial quality reviewer for StartInsight.

Your job is to review market insight articles before they are published.

Quality criteria:
1. DATA ACCURACY (weight: 30%): Every claim must have specific numbers. Reject vague claims
   like "growing market" without figures. Numbers should be realistic and sourced.
2. ACTIONABILITY (weight: 25%): Article must include concrete next steps founders can take.
   Not "do market research" but "target the $2.3B SMB analytics segment via Product Hunt launch."
3. READABILITY (weight: 25%): Clear headers, bullet points, tables. No walls of text.
   Maximum 3-4 sentences per paragraph.
4. ORIGINALITY (weight: 20%): Not rehashing common startup advice. Must provide novel
   data-driven perspectives.

Score 7+ = Publishable. Below 7 = needs revision.

Be strict but fair. Most articles should score 6-8.
""",
)

insight_review_agent = Agent(
    model=settings.default_llm_model,
    output_type=InsightAuditResult,
    system_prompt="""You are a data quality auditor for StartInsight's startup insight database.

Your job is to audit individual startup insights for completeness and quality.

Check:
1. COMPLETENESS: Are all 8 score dimensions filled? Is value_ladder, why_now_analysis,
   market_gap_analysis, proof_signals, execution_plan populated?
2. TITLE QUALITY: Is proposed_solution a concise product name (under 50 chars)?
   Bad: "Develop an AI-powered tool for..." Good: "AI Code Review with Pattern Learning"
3. SCORE CONSISTENCY: Do scores make sense together? (e.g., high opportunity + low feasibility
   is fine, but high everything is suspicious)
4. DATA QUALITY: Are competitor_analysis entries real companies? Are market_size_estimates
   specific dollar amounts, not just "Large"?

Flag insights that need re-analysis.
""",
)


# ============================================================================
# MARKET INSIGHT QUALITY REVIEW
# ============================================================================


async def _is_agent_enabled(session: AsyncSession, agent_name: str) -> bool:
    """Check if an agent is enabled in AgentConfiguration."""
    result = await session.execute(
        select(AgentConfiguration).where(
            AgentConfiguration.agent_name == agent_name
        )
    )
    config = result.scalar_one_or_none()
    if config is None:
        return True
    return config.is_enabled


async def review_draft_articles(session: AsyncSession) -> list[dict]:
    """Review all unpublished market insight articles and auto-publish good ones."""
    if not await _is_agent_enabled(session, MARKET_REVIEWER_NAME):
        logger.info(f"Agent '{MARKET_REVIEWER_NAME}' is disabled, skipping")
        return []

    # Get unpublished articles
    result = await session.execute(
        select(MarketInsight)
        .where(MarketInsight.is_published.is_(False))
        .order_by(MarketInsight.created_at.desc())
        .limit(10)
    )
    drafts = result.scalars().all()

    if not drafts:
        logger.info("No draft articles to review")
        return []

    results = []
    for article in drafts:
        try:
            review_prompt = (
                f"Review this market insight article:\n\n"
                f"Title: {article.title}\n"
                f"Summary: {article.summary}\n"
                f"Category: {article.category}\n\n"
                f"Content:\n{article.content[:3000]}"
            )

            review_result = await asyncio.wait_for(
                market_review_agent.run(review_prompt), timeout=settings.llm_call_timeout
            )
            review = review_result.output

            # Apply improvements if suggested
            if review.improved_title:
                article.title = review.improved_title
            if review.improved_summary:
                article.summary = review.improved_summary

            # Auto-publish if quality score >= 7
            if review.publish_recommendation and review.quality_score >= 7:
                article.is_published = True
                article.published_at = datetime.now(UTC)
                logger.info(
                    f"Auto-published article '{article.title}' "
                    f"(score: {review.quality_score}/10)"
                )
            else:
                logger.info(
                    f"Article '{article.title}' needs revision "
                    f"(score: {review.quality_score}/10, issues: {review.issues})"
                )

            await session.commit()

            results.append({
                "article_id": str(article.id),
                "title": article.title,
                "quality_score": review.quality_score,
                "published": article.is_published,
                "issues": review.issues,
            })

        except Exception as e:
            logger.error(f"Failed to review article {article.id}: {e}")
            results.append({
                "article_id": str(article.id),
                "error": str(e),
            })

    return results


# ============================================================================
# INSIGHT QUALITY AUDIT
# ============================================================================


async def audit_insights(session: AsyncSession, batch_size: int = 20) -> list[dict]:
    """Audit startup insights for data quality and completeness."""
    if not await _is_agent_enabled(session, INSIGHT_REVIEWER_NAME):
        logger.info(f"Agent '{INSIGHT_REVIEWER_NAME}' is disabled, skipping")
        return []

    # Find insights with potential quality issues:
    # - Missing key fields (no value_ladder, no why_now_analysis, etc.)
    # - Low score variety (all scores identical = suspicious)
    # - Vague market sizes
    result = await session.execute(
        select(Insight)
        .where(
            (Insight.value_ladder.is_(None)) |
            (Insight.why_now_analysis.is_(None)) |
            (Insight.proof_signals.is_(None)) |
            (Insight.market_size_estimate.in_(["Large", "Medium", "Small", "Unknown"]))
        )
        .order_by(Insight.created_at.desc())
        .limit(batch_size)
    )
    insights = result.scalars().all()

    if not insights:
        logger.info("All insights pass basic quality checks")
        return []

    logger.info(f"Auditing {len(insights)} insights with potential quality issues")

    results = []
    for insight in insights:
        try:
            # Build context for review
            fields_summary = {
                "proposed_solution": insight.proposed_solution,
                "market_size_estimate": insight.market_size_estimate,
                "opportunity_score": insight.opportunity_score,
                "problem_score": insight.problem_score,
                "feasibility_score": insight.feasibility_score,
                "why_now_score": insight.why_now_score,
                "go_to_market_score": insight.go_to_market_score,
                "founder_fit_score": insight.founder_fit_score,
                "execution_difficulty": insight.execution_difficulty,
                "revenue_potential": insight.revenue_potential,
                "has_value_ladder": insight.value_ladder is not None,
                "has_why_now_analysis": insight.why_now_analysis is not None,
                "has_proof_signals": insight.proof_signals is not None,
                "has_execution_plan": insight.execution_plan is not None,
                "has_market_gap": insight.market_gap_analysis is not None,
                "competitor_count": len(insight.competitor_analysis) if insight.competitor_analysis else 0,
            }

            audit_prompt = (
                f"Audit this startup insight for quality:\n\n"
                f"Fields: {fields_summary}\n\n"
                f"Problem (first 500 chars): {insight.problem_statement[:500]}"
            )

            audit_result = await asyncio.wait_for(
                insight_review_agent.run(audit_prompt), timeout=settings.llm_call_timeout
            )
            audit = audit_result.output

            results.append({
                "insight_id": str(insight.id),
                "title": insight.proposed_solution,
                "completeness_score": audit.completeness_score,
                "title_quality": audit.title_quality,
                "missing_fields": audit.missing_fields,
                "needs_reanalysis": audit.needs_reanalysis,
            })

        except Exception as e:
            logger.error(f"Failed to audit insight {insight.id}: {e}")
            results.append({
                "insight_id": str(insight.id),
                "error": str(e),
            })

    flagged = sum(1 for r in results if r.get("needs_reanalysis"))
    logger.info(
        f"Insight audit complete: {len(results)} reviewed, "
        f"{flagged} flagged for re-analysis"
    )
    return results


# ============================================================================
# ENTRY POINTS (for scheduler)
# ============================================================================


async def run_market_insight_quality_review() -> dict:
    """Entry point for market insight quality review task."""
    async with AsyncSessionLocal() as session:
        try:
            results = await review_draft_articles(session)
            published = sum(1 for r in results if r.get("published"))
            return {
                "status": "success",
                "reviewed": len(results),
                "published": published,
                "results": results,
            }
        except Exception as e:
            logger.error(f"Market insight quality review failed: {e}", exc_info=True)
            return {"status": "error", "error": str(e)}


async def run_insight_quality_audit() -> dict:
    """Entry point for insight quality audit task."""
    async with AsyncSessionLocal() as session:
        try:
            results = await audit_insights(session)
            flagged = sum(1 for r in results if r.get("needs_reanalysis"))
            return {
                "status": "success",
                "audited": len(results),
                "flagged_for_reanalysis": flagged,
                "results": results,
            }
        except Exception as e:
            logger.error(f"Insight quality audit failed: {e}", exc_info=True)
            return {"status": "error", "error": str(e)}
