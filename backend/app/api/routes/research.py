"""API endpoints for AI Research Agent - Phase 5.1.

Endpoints:
- POST /api/research/analyze - Request a custom analysis
- GET /api/research/analysis/{id} - Get analysis by ID
- GET /api/research/analyses - List user's analyses
- GET /api/research/quota - Get user's quota status

See architecture.md "Research Agent Architecture" for full specification.
"""

import logging
from datetime import UTC, datetime
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Query
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.agents.research_agent import (
    analyze_idea_with_retry,
    get_quota_limit,
)
from app.api.deps import AdminUser, CurrentUser
from app.core.constants import AnalysisStatus
from app.core.rate_limits import limiter
from app.db.session import get_db
from app.models.custom_analysis import CustomAnalysis
from app.models.research_request import ResearchRequest
from app.models.user import User
from app.schemas.research import (
    ResearchAnalysisListResponse,
    ResearchAnalysisResponse,
    ResearchAnalysisSummary,
    ResearchQuotaResponse,
    ResearchRequestAction,
    ResearchRequestCreate,
    ResearchRequestListResponse,
    ResearchRequestResponse,
    ResearchRequestSummary,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/research", tags=["research"])


# ============================================
# HELPER FUNCTIONS
# ============================================


async def get_monthly_usage(user_id: UUID, db: AsyncSession) -> int:
    """Get user's research analyses count for current month."""
    first_of_month = datetime.now(UTC).replace(day=1, hour=0, minute=0, second=0, microsecond=0)

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
            analysis.started_at = datetime.now(UTC)
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
            analysis.completed_at = datetime.now(UTC)

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
@limiter.limit("10/hour")  # Phase 2: SlowAPI rate limiting
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

    **Rate Limits (per hour):**
    - 10 requests/hour (enforced by SlowAPI)

    Note: SlowAPI handles hourly rate limiting. Monthly quota is checked separately.
    """
    # Check monthly quota (SlowAPI handles hourly rate limits)
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
        status=AnalysisStatus.PENDING,
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
            ACPFramework,
            CompetitorProfile,
            ExecutionPhase,
            MarketAnalysis,
            MarketMatrix,
            RiskAssessment,
            ValidationSignal,
            ValueEquation,
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
    now = datetime.now(UTC)
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


# ============================================
# RESEARCH REQUEST ENDPOINTS (Phase 5.2: Admin Queue)
# ============================================


@router.post("/request", response_model=ResearchRequestResponse)
@limiter.limit("5/hour")
async def create_research_request(
    request: ResearchRequestCreate,
    current_user: CurrentUser,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
) -> ResearchRequestResponse:
    """
    Submit a research request (queued for admin approval).

    **Workflow:**
    - Free tier: Requires manual admin approval (1 request/month)
    - Starter/Pro/Enterprise: Auto-approved (3/10/100 requests/month)

    **Rate Limits:**
    - 5 requests/hour (enforced by SlowAPI)
    """
    # Check monthly quota
    monthly_usage = await get_monthly_usage(current_user.id, db)
    quota_limit = get_quota_limit(current_user.subscription_tier)

    if monthly_usage >= quota_limit:
        raise HTTPException(
            status_code=429,
            detail=f"Monthly quota exceeded. Limit: {quota_limit} requests. "
                   f"Upgrade to get more requests.",
        )

    # Create research request
    research_request = ResearchRequest(
        user_id=current_user.id,
        idea_description=request.idea_description,
        target_market=request.target_market,
        budget_range=request.budget_range,
        status="pending",
    )
    db.add(research_request)
    await db.commit()
    await db.refresh(research_request)

    # Auto-approve for paid tiers (Starter, Pro, Enterprise)
    if current_user.subscription_tier in ["starter", "pro", "enterprise"]:
        research_request.status = "approved"
        research_request.reviewed_at = datetime.now(UTC)
        research_request.admin_id = None  # System auto-approval
        await db.commit()

        # Trigger analysis in background
        analysis = CustomAnalysis(
            user_id=current_user.id,
            idea_description=request.idea_description,
            target_market=request.target_market,
            budget_range=request.budget_range,
            status=AnalysisStatus.PENDING,
            progress_percent=0,
            current_step="Queued for analysis",
            request_id=research_request.id,
        )
        db.add(analysis)
        await db.commit()
        await db.refresh(analysis)

        research_request.analysis_id = analysis.id
        await db.commit()

        background_tasks.add_task(
            run_analysis_background,
            analysis.id,
            request.idea_description,
            request.target_market,
            request.budget_range,
        )

    logger.info(
        f"User {current_user.email} submitted research request {research_request.id} "
        f"(status: {research_request.status})"
    )

    return ResearchRequestResponse(
        id=research_request.id,
        user_id=research_request.user_id,
        admin_id=research_request.admin_id,
        status=research_request.status,
        idea_description=research_request.idea_description,
        target_market=research_request.target_market,
        budget_range=research_request.budget_range,
        admin_notes=research_request.admin_notes,
        analysis_id=research_request.analysis_id,
        created_at=research_request.created_at,
        reviewed_at=research_request.reviewed_at,
        completed_at=research_request.completed_at,
        user_email=current_user.email,
    )


@router.get("/requests", response_model=ResearchRequestListResponse)
async def list_user_requests(
    current_user: CurrentUser,
    limit: Annotated[int, Query(ge=1, le=50)] = 20,
    offset: Annotated[int, Query(ge=0)] = 0,
    db: AsyncSession = Depends(get_db),
) -> ResearchRequestListResponse:
    """
    List user's research requests.

    Returns a paginated list of research requests with status.
    """
    # Get total count
    count_query = (
        select(func.count())
        .select_from(ResearchRequest)
        .where(ResearchRequest.user_id == current_user.id)
    )
    total = await db.scalar(count_query) or 0

    # Get requests
    query = (
        select(ResearchRequest)
        .where(ResearchRequest.user_id == current_user.id)
        .order_by(ResearchRequest.created_at.desc())
        .limit(limit)
        .offset(offset)
    )
    result = await db.execute(query)
    requests = result.scalars().all()

    return ResearchRequestListResponse(
        items=[
            ResearchRequestSummary(
                id=r.id,
                user_id=r.user_id,
                user_email=current_user.email,
                status=r.status,
                idea_description=r.idea_description,
                target_market=r.target_market,
                created_at=r.created_at,
                reviewed_at=r.reviewed_at,
            )
            for r in requests
        ],
        total=total,
    )


@router.get("/admin/requests", response_model=ResearchRequestListResponse)
async def list_all_requests(
    admin_user: AdminUser,
    status: Annotated[str | None, Query(pattern="^(pending|approved|rejected|completed)$")] = None,
    limit: Annotated[int, Query(ge=1, le=100)] = 20,
    offset: Annotated[int, Query(ge=0)] = 0,
    db: AsyncSession = Depends(get_db),
) -> ResearchRequestListResponse:
    """
    Admin: List all research requests with optional status filter.

    **Admin Only**

    Filter by status: pending, approved, rejected, completed
    """
    # Build query
    query = select(ResearchRequest)
    if status:
        query = query.where(ResearchRequest.status == status)

    # Get total count
    count_query = select(func.count()).select_from(ResearchRequest)
    if status:
        count_query = count_query.where(ResearchRequest.status == status)
    total = await db.scalar(count_query) or 0

    # Get requests with user email
    query = query.order_by(ResearchRequest.created_at.desc()).limit(limit).offset(offset)
    result = await db.execute(query)
    requests = result.scalars().all()

    # Build response items using eagerly-loaded user relationship
    items = [
        ResearchRequestSummary(
            id=r.id,
            user_id=r.user_id,
            user_email=r.user.email if r.user else None,
            status=r.status,
            idea_description=r.idea_description,
            target_market=r.target_market,
            created_at=r.created_at,
            reviewed_at=r.reviewed_at,
        )
        for r in requests
    ]

    return ResearchRequestListResponse(items=items, total=total)


@router.patch("/admin/requests/{request_id}", response_model=ResearchRequestResponse)
async def update_request_status(
    request_id: UUID,
    action: ResearchRequestAction,
    admin_user: AdminUser,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
) -> ResearchRequestResponse:
    """
    Admin: Approve or reject a research request.

    **Admin Only**

    - `approve`: Creates analysis and triggers background processing
    - `reject`: Marks request as rejected with optional notes
    """
    # Get request
    research_request = await db.get(ResearchRequest, request_id)
    if not research_request:
        raise HTTPException(status_code=404, detail="Research request not found")

    if research_request.status != "pending":
        raise HTTPException(
            status_code=400,
            detail=f"Cannot update request with status '{research_request.status}'. "
                   "Only pending requests can be reviewed.",
        )

    # Update request
    research_request.admin_id = admin_user.id
    research_request.reviewed_at = datetime.now(UTC)
    research_request.admin_notes = action.notes

    if action.action == "approve":
        research_request.status = "approved"

        # Create analysis
        analysis = CustomAnalysis(
            user_id=research_request.user_id,
            admin_id=admin_user.id,
            idea_description=research_request.idea_description,
            target_market=research_request.target_market or "",
            budget_range=research_request.budget_range or "unknown",
            status=AnalysisStatus.PENDING,
            progress_percent=0,
            current_step="Queued for analysis",
            request_id=research_request.id,
        )
        db.add(analysis)
        await db.commit()
        await db.refresh(analysis)

        research_request.analysis_id = analysis.id
        await db.commit()

        # Trigger analysis in background
        background_tasks.add_task(
            run_analysis_background,
            analysis.id,
            research_request.idea_description,
            research_request.target_market or "",
            research_request.budget_range or "unknown",
        )

        logger.info(
            f"Admin {admin_user.email} approved request {request_id}, "
            f"created analysis {analysis.id}"
        )

    elif action.action == "reject":
        research_request.status = "rejected"
        logger.info(
            f"Admin {admin_user.email} rejected request {request_id}: "
            f"{action.notes or 'No reason provided'}"
        )

    await db.commit()
    await db.refresh(research_request)

    # Get user email
    user_query = select(User.email).where(User.id == research_request.user_id)
    user_result = await db.execute(user_query)
    user_email = user_result.scalar_one_or_none()

    return ResearchRequestResponse(
        id=research_request.id,
        user_id=research_request.user_id,
        admin_id=research_request.admin_id,
        status=research_request.status,
        idea_description=research_request.idea_description,
        target_market=research_request.target_market,
        budget_range=research_request.budget_range,
        admin_notes=research_request.admin_notes,
        analysis_id=research_request.analysis_id,
        created_at=research_request.created_at,
        reviewed_at=research_request.reviewed_at,
        completed_at=research_request.completed_at,
        user_email=user_email,
    )


@router.post("/admin/analyze", response_model=ResearchAnalysisResponse)
async def admin_trigger_analysis(
    request: ResearchRequestCreate,
    admin_user: AdminUser,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
) -> ResearchAnalysisResponse:
    """
    Admin: Manually trigger research analysis (bypasses request queue).

    **Admin Only**

    Creates analysis directly without user request or quota checks.
    """
    # Create analysis (admin-initiated, no user)
    analysis = CustomAnalysis(
        user_id=None,  # Admin-initiated
        admin_id=admin_user.id,
        idea_description=request.idea_description,
        target_market=request.target_market,
        budget_range=request.budget_range,
        status=AnalysisStatus.PENDING,
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

    logger.info(f"Admin {admin_user.email} manually triggered analysis {analysis.id}")

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


@router.get("/admin/analyses", response_model=ResearchAnalysisListResponse)
async def list_all_analyses(
    admin_user: AdminUser,
    limit: Annotated[int, Query(ge=1, le=100)] = 20,
    offset: Annotated[int, Query(ge=0)] = 0,
    db: AsyncSession = Depends(get_db),
) -> ResearchAnalysisListResponse:
    """
    Admin: List all research analyses (all users).

    **Admin Only**
    """
    # Get total count
    count_query = select(func.count()).select_from(CustomAnalysis)
    total = await db.scalar(count_query) or 0

    # Get analyses
    query = (
        select(CustomAnalysis)
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

