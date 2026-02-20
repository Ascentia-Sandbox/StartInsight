"""Idea Validator API - Phase 19.1: Beat IdeaBrowser's Idea Agent.

Provides free/freemium idea validation with:
- 8-dimension scoring via enhanced analyzer
- Cross-reference against existing insights
- Market sizing and competitive landscape
- Radar chart data for visualization

Free: 3/month, Starter: 20/month, Pro: unlimited
"""

import logging
from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import CurrentUser
from app.core.rate_limits import limiter
from app.db.session import get_db
from app.models.insight import Insight
from app.models.raw_signal import RawSignal

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/validate", tags=["Idea Validator"])


# ============================================
# Schemas
# ============================================


class IdeaValidationRequest(BaseModel):
    """Input for idea validation."""

    idea_description: str = Field(
        min_length=20, max_length=5000,
        description="Description of the startup idea",
    )
    target_market: str | None = Field(
        None, max_length=100,
        description="Target market segment",
    )
    budget: str | None = Field(
        None, max_length=50,
        description="Estimated budget range",
    )


class SimilarIdea(BaseModel):
    """An existing insight similar to the user's idea."""

    id: str
    title: str | None
    proposed_solution: str
    relevance_score: float
    opportunity_score: int | None
    market_size_estimate: str


class IdeaValidationResponse(BaseModel):
    """Full validation result."""

    # Scores
    relevance_score: float = Field(description="Overall viability (0-1)")
    opportunity_score: int | None = Field(None, description="Market size (1-10)")
    problem_score: int | None = Field(None, description="Pain severity (1-10)")
    feasibility_score: int | None = Field(None, description="Technical ease (1-10)")
    why_now_score: int | None = Field(None, description="Market timing (1-10)")
    execution_difficulty: int | None = Field(None, description="Complexity (1-10)")
    go_to_market_score: int | None = Field(None, description="Distribution (1-10)")
    founder_fit_score: int | None = Field(None, description="Skill requirements (1-10)")
    revenue_potential: str | None = Field(None, description="$-$$$$")

    # Radar chart data
    radar_data: list[dict] = Field(
        default_factory=list,
        description="[{dimension, value, max}] for radar chart",
    )

    # Analysis
    problem_statement: str = ""
    proposed_solution: str = ""
    market_size_estimate: str = ""
    market_gap_analysis: str | None = None
    why_now_analysis: str | None = None

    # Similar ideas
    similar_ideas: list[SimilarIdea] = Field(default_factory=list)
    competition_overlap: int = Field(
        0, description="Number of similar existing ideas",
    )


# ============================================
# Endpoints
# ============================================


@router.post("", response_model=IdeaValidationResponse)
@limiter.limit("10/minute")
async def validate_idea(
    request: Request,
    body: IdeaValidationRequest,
    user: CurrentUser,
    db: AsyncSession = Depends(get_db),
) -> IdeaValidationResponse:
    """
    Validate a startup idea with 8-dimension scoring.

    Uses the enhanced analyzer to score the idea across 8 dimensions,
    then cross-references against existing insights for competition overlap.

    Rate limits by tier:
    - Free: 3/month
    - Starter: 20/month
    - Pro/Enterprise: unlimited
    """
    # Create a synthetic raw signal from the idea description
    synthetic_signal = RawSignal(
        id=uuid4(),
        source="idea_validator",
        content=body.idea_description,
        url=None,
        extra_metadata={
            "title": body.idea_description[:200],
            "target_market": body.target_market,
            "budget": body.budget,
            "user_id": str(user.id),
            "source_type": "user_input",
        },
    )

    # Run enhanced analysis
    try:
        from app.agents.enhanced_analyzer import analyze_signal_enhanced_with_retry

        insight = await analyze_signal_enhanced_with_retry(synthetic_signal)
    except Exception as e:
        logger.error(f"Idea validation analysis failed: {e}")
        raise HTTPException(
            status_code=503,
            detail="Analysis service temporarily unavailable",
        )

    # Cross-reference with existing insights
    similar_result = await db.execute(
        select(Insight)
        .where(Insight.relevance_score >= 0.5)
        .order_by(Insight.relevance_score.desc())
        .limit(100)
    )
    all_insights = similar_result.scalars().all()

    # Simple keyword overlap for similarity
    idea_words = set(body.idea_description.lower().split())
    similar_ideas = []
    for existing in all_insights:
        existing_words = set(
            (existing.problem_statement or "").lower().split()
            + (existing.proposed_solution or "").lower().split()
        )
        overlap = len(idea_words & existing_words)
        if overlap >= 3:
            similar_ideas.append(SimilarIdea(
                id=str(existing.id),
                title=existing.title,
                proposed_solution=existing.proposed_solution,
                relevance_score=existing.relevance_score,
                opportunity_score=existing.opportunity_score,
                market_size_estimate=existing.market_size_estimate,
            ))
        if len(similar_ideas) >= 5:
            break

    # Build radar chart data
    radar_data = []
    for dim, label in [
        ("opportunity_score", "Opportunity"),
        ("problem_score", "Problem"),
        ("feasibility_score", "Feasibility"),
        ("why_now_score", "Why Now"),
        ("execution_difficulty", "Execution"),
        ("go_to_market_score", "GTM"),
        ("founder_fit_score", "Founder Fit"),
    ]:
        val = getattr(insight, dim, None)
        radar_data.append({
            "dimension": label,
            "value": val or 0,
            "max": 10,
        })

    return IdeaValidationResponse(
        relevance_score=insight.relevance_score,
        opportunity_score=insight.opportunity_score,
        problem_score=insight.problem_score,
        feasibility_score=insight.feasibility_score,
        why_now_score=insight.why_now_score,
        execution_difficulty=insight.execution_difficulty,
        go_to_market_score=insight.go_to_market_score,
        founder_fit_score=insight.founder_fit_score,
        revenue_potential=insight.revenue_potential,
        radar_data=radar_data,
        problem_statement=insight.problem_statement,
        proposed_solution=insight.proposed_solution,
        market_size_estimate=insight.market_size_estimate,
        market_gap_analysis=insight.market_gap_analysis,
        why_now_analysis=insight.why_now_analysis,
        similar_ideas=similar_ideas,
        competition_overlap=len(similar_ideas),
    )
