"""API endpoints for AI Research Agent - Phase 5.1.

Endpoints:
- POST /api/research/analyze - Request a custom analysis
- GET /api/research/analysis/{id} - Get analysis by ID
- GET /api/research/analyses - List user's analyses
- GET /api/research/quota - Get user's quota status

See architecture.md "Research Agent Architecture" for full specification.
"""

import logging
from datetime import datetime, timedelta
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Query
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import CurrentUser
from app.db.session import get_db
from app.models.custom_analysis import CustomAnalysis
from app.agents.research_agent import (
    analyze_idea_with_retry,
    get_quota_limit,
)
from app.schemas.research import (
    ResearchAnalysisListResponse,
    ResearchAnalysisResponse,
    ResearchAnalysisSummary,
    ResearchQuotaResponse,
    ResearchRequestCreate,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/research", tags=["research"])


# ============================================
# HELPER FUNCTIONS
# ============================================


async def get_monthly_usage(user_id: UUID, db: AsyncSession) -> int:
    """Get user's research analyses count for current month."""
    first_of_month = datetime.utcnow().replace(day=1, hour=0, minute=0, second=0, microsecond=0)

    count_query = (
        select(func.count())
        .select_from(CustomAnalysis)
        .where(
            CustomAnalysis.user_id == user_id,
            CustomAnalysis.created_at >= first_of_month,
        )
    )
    return await db.scalar(count_query) or 0


async def run_analysis_background(
    analysis_id: UUID,
    idea_description: str,
    target_market: str,
    budget_range: str,
):
    """Background task to run the research analysis."""
    from app.db.session import async_session_maker

    async with async_session_maker() as db:
        try:
            # Get the analysis record
            analysis = await db.get(CustomAnalysis, analysis_id)
            if not analysis:
                logger.error(f"Analysis {analysis_id} not found")
                return

            # Update status to processing
            analysis.status = "processing"
            analysis.started_at = datetime.utcnow()
            analysis.current_step = "Initializing research agent..."
            analysis.progress_percent = 5
            await db.commit()

            # Run the analysis
            analysis.current_step = "Analyzing market and competitors..."
            analysis.progress_percent = 25
            await db.commit()

            result, tokens_used, cost_usd = await analyze_idea_with_retry(
                idea_description=idea_description,
                target_market=target_market,
                budget_range=budget_range,
            )

            # Update with results
            analysis.status = "completed"
            analysis.progress_percent = 100
            analysis.current_step = "Analysis complete"
            analysis.completed_at = datetime.utcnow()

            # Store analysis results
            analysis.market_analysis = result.market_analysis.model_dump()
            analysis.competitor_landscape = [c.model_dump() for c in result.competitor_landscape]
            analysis.value_equation = result.value_equation.model_dump()
            analysis.market_matrix = result.market_matrix.model_dump()
            analysis.acp_framework = result.acp_framework.model_dump()
            analysis.validation_signals = [v.model_dump() for v in result.validation_signals]
            analysis.execution_roadmap = [e.model_dump() for e in result.execution_roadmap]
            analysis.risk_assessment = result.risk_assessment.model_dump()

            # Store summary scores
            analysis.opportunity_score = result.opportunity_score
            analysis.market_fit_score = result.market_fit_score
            analysis.execution_readiness = result.execution_readiness

            # Store metadata
            analysis.tokens_used = tokens_used
            analysis.analysis_cost_usd = cost_usd

            await db.commit()
            logger.info(f"Analysis {analysis_id} completed successfully")

        except Exception as e:
            # Update status to failed
            analysis = await db.get(CustomAnalysis, analysis_id)
            if analysis:
                analysis.status = "failed"
                analysis.error_message = str(e)
                analysis.current_step = "Analysis failed"
                await db.commit()

            logger.error(f"Analysis {analysis_id} failed: {e}")


# ============================================
# RESEARCH ENDPOINTS
# ============================================


@router.post("/analyze", response_model=ResearchAnalysisResponse)
async def request_analysis(
    request: ResearchRequestCreate,
    background_tasks: BackgroundTasks,
    current_user: CurrentUser,
    db: AsyncSession = Depends(get_db),
) -> ResearchAnalysisResponse:
    """
    Request a custom AI research analysis.

    Starts a background job that performs a comprehensive 40-step analysis
    including market sizing, competitor research, and execution roadmap.

    **Quota Limits (per month):**
    - Free: 1 analysis
    - Starter: 3 analyses
    - Pro: 10 analyses
    - Enterprise: 100 analyses
    """
    # Check quota
    monthly_usage = await get_monthly_usage(current_user.id, db)
    quota_limit = get_quota_limit(current_user.subscription_tier)

    if monthly_usage >= quota_limit:
        raise HTTPException(
            status_code=429,
            detail=f"Monthly quota exceeded. Limit: {quota_limit} analyses. "
                   f"Upgrade to get more analyses.",
        )

    # Create analysis record
    analysis = CustomAnalysis(
        user_id=current_user.id,
        idea_description=request.idea_description,
        target_market=request.target_market,
        budget_range=request.budget_range,
        status="pending",
        progress_percent=0,
        current_step="Queued for analysis",
    )
    db.add(analysis)
    await db.commit()
    await db.refresh(analysis)

    # Start background analysis
    background_tasks.add_task(
        run_analysis_background,
        analysis.id,
        request.idea_description,
        request.target_market,
        request.budget_range,
    )

    logger.info(f"User {current_user.email} requested analysis {analysis.id}")

    return ResearchAnalysisResponse(
        id=analysis.id,
        user_id=analysis.user_id,
        status=analysis.status,
        progress_percent=analysis.progress_percent,
        current_step=analysis.current_step,
        idea_description=analysis.idea_description,
        target_market=analysis.target_market,
        budget_range=analysis.budget_range,
        created_at=analysis.created_at,
    )


@router.get("/analysis/{analysis_id}", response_model=ResearchAnalysisResponse)
async def get_analysis(
    analysis_id: UUID,
    current_user: CurrentUser,
    db: AsyncSession = Depends(get_db),
) -> ResearchAnalysisResponse:
    """
    Get a specific research analysis by ID.

    Returns the full analysis including all frameworks and scores
    once the analysis is complete.
    """
    analysis = await db.get(CustomAnalysis, analysis_id)

    if not analysis:
        raise HTTPException(status_code=404, detail="Analysis not found")

    # Verify ownership (unless admin)
    if analysis.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized to view this analysis")

    # Convert to response
    response = ResearchAnalysisResponse(
        id=analysis.id,
        user_id=analysis.user_id,
        status=analysis.status,
        progress_percent=analysis.progress_percent,
        current_step=analysis.current_step,
        idea_description=analysis.idea_description,
        target_market=analysis.target_market,
        budget_range=analysis.budget_range,
        tokens_used=analysis.tokens_used,
        analysis_cost_usd=float(analysis.analysis_cost_usd) if analysis.analysis_cost_usd else 0.0,
        error_message=analysis.error_message,
        created_at=analysis.created_at,
        started_at=analysis.started_at,
        completed_at=analysis.completed_at,
    )

    # Include results if completed
    if analysis.status == "completed":
        from app.schemas.research import (
            MarketAnalysis,
            CompetitorProfile,
            ValueEquation,
            MarketMatrix,
            ACPFramework,
            ValidationSignal,
            ExecutionPhase,
            RiskAssessment,
        )

        if analysis.market_analysis:
            response.market_analysis = MarketAnalysis(**analysis.market_analysis)
        if analysis.competitor_landscape:
            response.competitor_landscape = [
                CompetitorProfile(**c) for c in analysis.competitor_landscape
            ]
        if analysis.value_equation:
            response.value_equation = ValueEquation(**analysis.value_equation)
        if analysis.market_matrix:
            response.market_matrix = MarketMatrix(**analysis.market_matrix)
        if analysis.acp_framework:
            response.acp_framework = ACPFramework(**analysis.acp_framework)
        if analysis.validation_signals:
            response.validation_signals = [
                ValidationSignal(**v) for v in analysis.validation_signals
            ]
        if analysis.execution_roadmap:
            response.execution_roadmap = [
                ExecutionPhase(**e) for e in analysis.execution_roadmap
            ]
        if analysis.risk_assessment:
            response.risk_assessment = RiskAssessment(**analysis.risk_assessment)

        response.opportunity_score = float(analysis.opportunity_score) if analysis.opportunity_score else None
        response.market_fit_score = float(analysis.market_fit_score) if analysis.market_fit_score else None
        response.execution_readiness = float(analysis.execution_readiness) if analysis.execution_readiness else None

    return response


@router.get("/analyses", response_model=ResearchAnalysisListResponse)
async def list_analyses(
    current_user: CurrentUser,
    limit: Annotated[int, Query(ge=1, le=50)] = 20,
    offset: Annotated[int, Query(ge=0)] = 0,
    db: AsyncSession = Depends(get_db),
) -> ResearchAnalysisListResponse:
    """
    List user's research analyses.

    Returns a paginated list of analyses with summary information.
    """
    # Get total count
    count_query = (
        select(func.count())
        .select_from(CustomAnalysis)
        .where(CustomAnalysis.user_id == current_user.id)
    )
    total = await db.scalar(count_query) or 0

    # Get analyses
    query = (
        select(CustomAnalysis)
        .where(CustomAnalysis.user_id == current_user.id)
        .order_by(CustomAnalysis.created_at.desc())
        .limit(limit)
        .offset(offset)
    )
    result = await db.execute(query)
    analyses = result.scalars().all()

    return ResearchAnalysisListResponse(
        items=[
            ResearchAnalysisSummary(
                id=a.id,
                status=a.status,
                progress_percent=a.progress_percent,
                idea_description=a.idea_description,
                target_market=a.target_market,
                opportunity_score=float(a.opportunity_score) if a.opportunity_score else None,
                created_at=a.created_at,
                completed_at=a.completed_at,
            )
            for a in analyses
        ],
        total=total,
    )


@router.get("/quota", response_model=ResearchQuotaResponse)
async def get_quota(
    current_user: CurrentUser,
    db: AsyncSession = Depends(get_db),
) -> ResearchQuotaResponse:
    """
    Get user's research quota status.

    Returns current usage and limits for the month.
    """
    monthly_usage = await get_monthly_usage(current_user.id, db)
    quota_limit = get_quota_limit(current_user.subscription_tier)

    # Calculate reset date (first of next month)
    now = datetime.utcnow()
    if now.month == 12:
        next_month = now.replace(year=now.year + 1, month=1, day=1)
    else:
        next_month = now.replace(month=now.month + 1, day=1)

    return ResearchQuotaResponse(
        analyses_used=monthly_usage,
        analyses_limit=quota_limit,
        analyses_remaining=max(0, quota_limit - monthly_usage),
        tier=current_user.subscription_tier,
        resets_at=next_month,
    )
