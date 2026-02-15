"""Admin API endpoints - Phase 4.2 admin portal.

Endpoints:
- /api/admin/dashboard - Overview metrics
- /api/admin/events - SSE stream for real-time updates
- /api/admin/agents/* - Agent control (pause/resume/trigger)
- /api/admin/insights/* - Insight moderation
- /api/admin/metrics - System metrics query

See architecture.md "Admin Portal Architecture" for full specification.
"""

import asyncio
import csv
import hashlib
import io
import json
import logging
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, File, HTTPException, Query, Request, UploadFile, status
from sqlalchemy import func, select, text
from sqlalchemy.ext.asyncio import AsyncSession
from sse_starlette.sse import EventSourceResponse
from starlette.responses import StreamingResponse

from app.api.deps import AdminUser
from app.core.config import settings
from app.core.constants import InsightStatus
from app.core.rate_limits import limiter
from app.db.query_helpers import count_by_field
from app.db.session import AsyncSessionLocal, get_db
from app.models.admin_user import AdminUser as AdminUserModel
from app.models.agent_control import AgentConfiguration, AuditLog
from app.models.agent_execution_log import AgentExecutionLog
from app.models.insight import Insight
from app.models.market_insight import MarketInsight
from app.models.raw_signal import RawSignal
from app.models.success_story import SuccessStory
from app.models.system_metric import SystemMetric
from app.models.tool import Tool
from app.models.trend import Trend
from app.models.user import User as UserModel
from app.schemas.admin import (
    AdminUserListResponse,
    AdminUserPromoteRequest,
    AdminUserResponse,
    AdminUserUpdateRequest,
    AgentControlResponse,
    AgentStatusResponse,
    DashboardMetricsResponse,
    ErrorSummaryResponse,
    ExecutionLogListResponse,
    ExecutionLogResponse,
    InsightAdminCreate,
    InsightAdminListResponse,
    InsightAdminResponse,
    InsightAdminUpdate,
    InsightReviewResponse,
    MetricResponse,
    MetricSummaryResponse,
    ReviewQueueResponse,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/admin", tags=["admin"])

# SSE connection tracking (prevent connection exhaustion)
_active_sse_connections = set()
_MAX_SSE_CONNECTIONS = 10  # Limit concurrent admin SSE streams


# ============================================
# DASHBOARD ENDPOINTS
# ============================================


@router.get("/dashboard", response_model=DashboardMetricsResponse)
@limiter.limit("20/minute")  # Phase 2: SlowAPI rate limiting
async def get_dashboard_metrics(
    request: Request,
    admin: AdminUser,
    db: AsyncSession = Depends(get_db),
) -> DashboardMetricsResponse:
    """
    Get admin dashboard overview metrics.

    Returns:
    - Agent states (running/paused)
    - Recent execution logs
    - LLM cost today
    - Pending insights count
    """
    metrics = await _gather_admin_metrics(db)
    logger.info(f"Admin dashboard accessed by {admin.email}")
    return DashboardMetricsResponse(**metrics)


@router.get("/events")
async def admin_event_stream(
    request: Request,
    admin: AdminUser,
):
    """
    Server-Sent Events stream for real-time admin dashboard updates.

    Sends metrics_update events every 5 seconds with heartbeat.

    Security:
    - Limited to 10 concurrent connections (prevents DB pool exhaustion)
    - Creates fresh DB session per query (prevents session leak)
    - Heartbeat detects client disconnects
    - Auto-cleanup on disconnect
    """
    connection_id = id(request)

    # ✅ CONNECTION LIMIT - Prevent DB pool exhaustion
    if len(_active_sse_connections) >= _MAX_SSE_CONNECTIONS:
        logger.warning(f"SSE connection limit reached ({_MAX_SSE_CONNECTIONS})")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Too many active admin connections. Please try again later.",
        )

    async def event_generator():
        # Track this connection
        _active_sse_connections.add(connection_id)
        logger.info(f"Admin SSE connected: {admin.email} (total: {len(_active_sse_connections)})")

        try:
            while True:
                # ✅ CHECK CLIENT DISCONNECT - Heartbeat mechanism
                if await request.is_disconnected():
                    logger.info(f"Admin SSE client disconnected: {admin.email}")
                    break

                try:
                    # ✅ FRESH DB SESSION - Prevents connection leak
                    async with AsyncSessionLocal() as db:
                        metrics = await _gather_admin_metrics(db)

                    # Send metrics update
                    yield {
                        "event": "metrics_update",
                        "data": json.dumps(metrics, default=str),
                        "retry": 5000,
                    }

                    # Wait 5 seconds
                    await asyncio.sleep(5)

                except asyncio.CancelledError:
                    logger.info(f"Admin SSE cancelled: {admin.email}")
                    break
                except Exception as e:
                    logger.error(f"SSE metrics error: {e}", exc_info=True)
                    # Send error event but keep connection alive
                    yield {
                        "event": "error",
                        "data": json.dumps({"error": "Internal metrics error"}),
                    }
                    await asyncio.sleep(5)

        finally:
            # ✅ CLEANUP - Always remove from active connections
            _active_sse_connections.discard(connection_id)
            logger.info(f"Admin SSE cleanup: {admin.email} (remaining: {len(_active_sse_connections)})")

    return EventSourceResponse(event_generator())


async def _gather_admin_metrics(db: AsyncSession) -> dict:
    """
    Gather all metrics for admin dashboard with optimized queries.

    Optimizations:
    - Single query for agent states using DISTINCT ON (PostgreSQL)
    - Combined insight/metric queries
    - Reduced from 9 queries to 3 queries
    """
    today_start = datetime.now(UTC).replace(hour=0, minute=0, second=0, microsecond=0)

    # ✅ OPTIMIZATION #1: Get agent states in single query (was 4 queries)
    # Uses PostgreSQL DISTINCT ON to get most recent log per agent type
    agent_states_query = text("""
        SELECT DISTINCT ON (agent_type) agent_type, status
        FROM agent_execution_logs
        WHERE agent_type IN ('reddit_scraper', 'product_hunt_scraper', 'trends_scraper', 'analyzer')
        ORDER BY agent_type, created_at DESC
    """)
    agent_states_result = await db.execute(agent_states_query)
    agent_states = {
        row.agent_type: row.status
        for row in agent_states_result.fetchall()
    }

    # Ensure all agents have a state (even if no logs)
    for agent in ["reddit_scraper", "product_hunt_scraper", "trends_scraper", "analyzer"]:
        if agent not in agent_states:
            agent_states[agent] = "unknown"

    # ✅ OPTIMIZATION #2: Get recent logs (unchanged - already optimized)
    logs_result = await db.execute(
        select(AgentExecutionLog)
        .order_by(AgentExecutionLog.created_at.desc())
        .limit(10)
    )
    recent_logs = [
        ExecutionLogResponse.model_validate(log).model_dump()
        for log in logs_result.scalars().all()
    ]

    # ✅ OPTIMIZATION #3: Combined metrics query (was 4 separate queries)
    # Single query with multiple aggregations
    metrics_query = text("""
        SELECT
            (SELECT COALESCE(SUM(metric_value), 0)
             FROM system_metrics
             WHERE metric_type = 'llm_cost' AND recorded_at >= :today_start) AS llm_cost_today,
            (SELECT COUNT(*)
             FROM insights
             WHERE admin_status = 'pending') AS pending_insights,
            (SELECT COUNT(*)
             FROM insights
             WHERE created_at >= :today_start) AS total_insights_today,
            (SELECT COUNT(*)
             FROM system_metrics
             WHERE metric_type = 'error_rate' AND recorded_at >= :today_start) AS errors_today
    """)
    metrics_result = await db.execute(metrics_query, {"today_start": today_start})
    metrics_row = metrics_result.fetchone()

    return {
        "agent_states": agent_states,
        "recent_logs": recent_logs,
        "llm_cost_today": float(metrics_row.llm_cost_today),
        "pending_insights": int(metrics_row.pending_insights),
        "total_insights_today": int(metrics_row.total_insights_today),
        "errors_today": int(metrics_row.errors_today),
        "timestamp": datetime.now(UTC).isoformat(),
    }


# ============================================
# AGENT CONTROL ENDPOINTS
# ============================================


@router.get("/agents", response_model=list[AgentStatusResponse])
async def list_agents(
    admin: AdminUser,
    db: AsyncSession = Depends(get_db),
) -> list[AgentStatusResponse]:
    """
    List all agents with their current status.
    """
    agents = ["reddit_scraper", "product_hunt_scraper", "trends_scraper", "analyzer"]
    today_start = datetime.now(UTC).replace(hour=0, minute=0, second=0, microsecond=0)
    results = []

    for agent_type in agents:
        # Get last run
        last_result = await db.execute(
            select(AgentExecutionLog)
            .where(AgentExecutionLog.agent_type == agent_type)
            .order_by(AgentExecutionLog.created_at.desc())
            .limit(1)
        )
        last_log = last_result.scalar_one_or_none()

        # Count items processed today (SUM not supported by count_by_field, keep manual)
        processed_result = await db.execute(
            select(func.sum(AgentExecutionLog.items_processed)).where(
                AgentExecutionLog.agent_type == agent_type,
                AgentExecutionLog.created_at >= today_start,
            )
        )
        items_today = processed_result.scalar_one() or 0

        # Count errors today (multiple WHERE conditions, keep manual)
        errors_result = await db.execute(
            select(func.count()).select_from(AgentExecutionLog).where(
                AgentExecutionLog.agent_type == agent_type,
                AgentExecutionLog.status == "failed",
                AgentExecutionLog.created_at >= today_start,
            )
        )
        errors_today = errors_result.scalar_one() or 0

        results.append(
            AgentStatusResponse(
                agent_type=agent_type,
                state="running",  # Default state
                last_run=last_log.completed_at if last_log else None,
                last_status=last_log.status if last_log else None,
                items_processed_today=items_today,
                errors_today=errors_today,
            )
        )

    return results


@router.get("/agents/{agent_type}/logs", response_model=ExecutionLogListResponse)
async def get_agent_logs(
    agent_type: str,
    admin: AdminUser,
    limit: Annotated[int, Query(ge=1, le=100)] = 20,
    offset: Annotated[int, Query(ge=0)] = 0,
    db: AsyncSession = Depends(get_db),
) -> ExecutionLogListResponse:
    """
    Get execution logs for a specific agent.
    """
    # Get total count (uses count_by_field helper)
    total = await count_by_field(db, AgentExecutionLog, "agent_type", agent_type)

    # Get logs
    logs_result = await db.execute(
        select(AgentExecutionLog)
        .where(AgentExecutionLog.agent_type == agent_type)
        .order_by(AgentExecutionLog.created_at.desc())
        .limit(limit)
        .offset(offset)
    )
    logs = logs_result.scalars().all()

    return ExecutionLogListResponse(
        items=[ExecutionLogResponse.model_validate(log) for log in logs],
        total=total,
        limit=limit,
        offset=offset,
    )


@router.post("/agents/{agent_type}/pause", response_model=AgentControlResponse)
@limiter.limit("20/minute")  # Phase 2: SlowAPI rate limiting
async def pause_agent(
    request: Request,
    agent_type: str,
    admin: AdminUser,
    db: AsyncSession = Depends(get_db),
) -> AgentControlResponse:
    """
    Pause agent execution.

    Agent will skip next scheduled run until resumed.
    Accepts any configured agent name (e.g., competitive_intel, enhanced_analyzer).
    """
    # Validate agent exists in configurations
    config = await db.execute(
        select(AgentConfiguration).where(AgentConfiguration.agent_name == agent_type)
    )
    if not config.scalar_one_or_none():
        raise HTTPException(status_code=404, detail=f"Agent '{agent_type}' not found")

    # Log admin action
    log = AgentExecutionLog(
        agent_type=agent_type,
        status="skipped",
        error_message=f"Paused by admin {admin.email}",
        extra_metadata={"action": "pause", "admin_id": str(admin.id)},
    )
    db.add(log)
    await db.commit()

    logger.info(f"Agent {agent_type} paused by admin {admin.email}")

    return AgentControlResponse(
        status="paused",
        agent_type=agent_type,
        triggered_by=admin.email,
        timestamp=datetime.now(UTC),
    )


@router.post("/agents/{agent_type}/resume", response_model=AgentControlResponse)
@limiter.limit("20/minute")  # Phase 2: SlowAPI rate limiting
async def resume_agent(
    request: Request,
    agent_type: str,
    admin: AdminUser,
    db: AsyncSession = Depends(get_db),
) -> AgentControlResponse:
    """
    Resume paused agent execution.
    Accepts any configured agent name.
    """
    # Validate agent exists
    config = await db.execute(
        select(AgentConfiguration).where(AgentConfiguration.agent_name == agent_type)
    )
    if not config.scalar_one_or_none():
        raise HTTPException(status_code=404, detail=f"Agent '{agent_type}' not found")

    # Log admin action
    log = AgentExecutionLog(
        agent_type=agent_type,
        status="running",
        error_message=f"Resumed by admin {admin.email}",
        extra_metadata={"action": "resume", "admin_id": str(admin.id)},
    )
    db.add(log)
    await db.commit()

    logger.info(f"Agent {agent_type} resumed by admin {admin.email}")

    return AgentControlResponse(
        status="running",
        agent_type=agent_type,
        triggered_by=admin.email,
        timestamp=datetime.now(UTC),
    )


@router.post("/agents/{agent_type}/trigger", response_model=AgentControlResponse)
@limiter.limit("20/minute")  # Phase 2: SlowAPI rate limiting
async def trigger_agent(
    request: Request,
    agent_type: str,
    admin: AdminUser,
    db: AsyncSession = Depends(get_db),
) -> AgentControlResponse:
    """
    Manually trigger agent execution (out of schedule).
    Accepts any configured agent name.
    """
    # Validate agent exists
    config = await db.execute(
        select(AgentConfiguration).where(AgentConfiguration.agent_name == agent_type)
    )
    if not config.scalar_one_or_none():
        raise HTTPException(status_code=404, detail=f"Agent '{agent_type}' not found")

    # Create execution log
    log = AgentExecutionLog(
        agent_type=agent_type,
        status="running",
        extra_metadata={"action": "manual_trigger", "admin_id": str(admin.id)},
    )
    db.add(log)
    await db.commit()
    await db.refresh(log)

    # Enqueue the Arq job for this agent type
    agent_task_map = {
        "reddit_scraper": "scrape_reddit_task",
        "product_hunt_scraper": "scrape_product_hunt_task",
        "trends_scraper": "scrape_trends_task",
        "twitter_scraper": "scrape_twitter_task",
        "hackernews_scraper": "scrape_hackernews_task",
        "analyzer": "analyze_signals_task",
        "enhanced_analyzer": "analyze_signals_task",
        "quality_reviewer": "insight_quality_audit_task",
        "market_insight_publisher": "market_insight_publisher_task",
        "market_insight_quality_review": "market_insight_quality_review_task",
        "content_pipeline": "run_content_pipeline_task",
        "research_agent": "run_research_agent_auto_task",
        "content_generator": "run_content_generator_auto_task",
        "competitive_intel": "run_competitive_intel_auto_task",
        "market_intel": "run_market_intel_auto_task",
        "daily_insight": "fetch_daily_insight_task",
        "daily_digest": "send_daily_digests_task",
        "success_stories": "update_success_stories_task",
        "scrape_all": "scrape_all_sources_task",
    }

    task_name = agent_task_map.get(agent_type)
    if task_name:
        try:
            from arq.connections import ArqRedis, create_pool
            from arq.connections import RedisSettings as ArqRedisSettings

            pool: ArqRedis = await create_pool(ArqRedisSettings(
                host=settings.redis_host,
                port=settings.redis_port,
            ))
            job = await pool.enqueue_job(task_name)
            await pool.aclose()
            logger.info(f"Enqueued Arq job '{task_name}' (job_id={job.job_id}) for agent {agent_type}")
        except Exception as e:
            logger.warning(f"Failed to enqueue Arq job for {agent_type}: {e}")
    else:
        logger.warning(f"No task mapping found for agent_type '{agent_type}', log created but job not enqueued")

    logger.info(f"Agent {agent_type} triggered by admin {admin.email}")

    return AgentControlResponse(
        status="triggered",
        agent_type=agent_type,
        triggered_by=admin.email,
        job_id=str(log.id),
        timestamp=datetime.now(UTC),
    )


# ============================================
# INSIGHT MODERATION ENDPOINTS
# ============================================


@router.post("/insights", response_model=InsightAdminResponse, status_code=status.HTTP_201_CREATED)
async def create_insight_admin(
    create_data: InsightAdminCreate,
    admin: AdminUser,
    db: AsyncSession = Depends(get_db),
) -> InsightAdminResponse:
    """
    Manually create a new insight (Phase A1).

    Creates a synthetic RawSignal with source='admin_manual' to satisfy the FK constraint.
    """
    # Create synthetic raw signal
    content = f"# {create_data.title}\n\n{create_data.problem_statement}"
    raw_signal = RawSignal(
        source="admin_manual",
        url=f"admin://manual/{admin.email}",
        content=content,
        content_hash=hashlib.sha256(content.encode()).hexdigest(),
        extra_metadata={"created_by": admin.email, "manual": True},
        processed=True,
    )
    db.add(raw_signal)
    await db.flush()

    # Create insight
    insight = Insight(
        raw_signal_id=raw_signal.id,
        title=create_data.title,
        problem_statement=create_data.problem_statement,
        proposed_solution=create_data.proposed_solution,
        market_size_estimate=create_data.market_size_estimate,
        relevance_score=create_data.relevance_score,
        admin_status=create_data.admin_status,
        opportunity_score=create_data.opportunity_score,
        problem_score=create_data.problem_score,
        feasibility_score=create_data.feasibility_score,
        why_now_score=create_data.why_now_score,
        execution_difficulty=create_data.execution_difficulty,
        go_to_market_score=create_data.go_to_market_score,
        founder_fit_score=create_data.founder_fit_score,
        revenue_potential=create_data.revenue_potential,
        market_gap_analysis=create_data.market_gap_analysis,
        why_now_analysis=create_data.why_now_analysis,
    )
    db.add(insight)

    # Audit log
    audit = AuditLog(
        user_id=admin.id,
        action=AuditLog.ACTION_CREATE,
        resource_type="insight",
        resource_id=insight.id,
        details={"title": create_data.title, "admin_email": admin.email},
    )
    db.add(audit)

    await db.commit()
    await db.refresh(insight)

    logger.info(f"Admin {admin.email} created insight {insight.id}: {create_data.title}")

    return InsightAdminResponse(
        id=insight.id,
        title=insight.title,
        problem_statement=insight.problem_statement,
        proposed_solution=insight.proposed_solution,
        market_size_estimate=insight.market_size_estimate,
        relevance_score=insight.relevance_score,
        admin_status=insight.admin_status or "approved",
        admin_notes=insight.admin_notes,
        admin_override_score=insight.admin_override_score,
        source="admin_manual",
        created_at=insight.created_at,
        edited_at=insight.edited_at,
        opportunity_score=insight.opportunity_score,
        problem_score=insight.problem_score,
        feasibility_score=insight.feasibility_score,
        why_now_score=insight.why_now_score,
        execution_difficulty=insight.execution_difficulty,
        go_to_market_score=insight.go_to_market_score,
        founder_fit_score=insight.founder_fit_score,
        revenue_potential=insight.revenue_potential,
        market_gap_analysis=insight.market_gap_analysis,
        why_now_analysis=insight.why_now_analysis,
        value_ladder=insight.value_ladder,
        proof_signals=insight.proof_signals,
        execution_plan=insight.execution_plan,
        competitor_analysis=insight.competitor_analysis,
    )


@router.get("/insights", response_model=ReviewQueueResponse)
async def get_review_queue(
    admin: AdminUser,
    status_filter: Annotated[str | None, Query(alias="status")] = None,
    limit: Annotated[int, Query(ge=1, le=100)] = 20,
    offset: Annotated[int, Query(ge=0)] = 0,
    db: AsyncSession = Depends(get_db),
) -> ReviewQueueResponse:
    """
    Get insights review queue.

    - **status**: Filter by admin_status (pending, approved, rejected)
    """
    # Build query
    query = select(Insight).order_by(Insight.created_at.desc())
    if status_filter:
        query = query.where(Insight.admin_status == status_filter)

    # Get total count (simplified with count_by_field for single field case)
    if not status_filter:
        # Simple case: count all insights
        total = await count_by_field(db, Insight)
    else:
        # Filtered case: use count_by_field with admin_status
        total = await count_by_field(db, Insight, "admin_status", status_filter)

    # Get status counts (uses count_by_field helper)
    pending_count = await count_by_field(db, Insight, "admin_status", InsightStatus.PENDING)
    approved_count = await count_by_field(db, Insight, "admin_status", InsightStatus.APPROVED)
    rejected_count = await count_by_field(db, Insight, "admin_status", InsightStatus.REJECTED)

    # Get insights
    result = await db.execute(query.limit(limit).offset(offset))
    insights = result.scalars().all()

    return ReviewQueueResponse(
        items=[
            InsightReviewResponse(
                id=i.id,
                problem_statement=i.problem_statement,
                proposed_solution=i.proposed_solution,
                relevance_score=i.relevance_score,
                admin_status=i.admin_status or InsightStatus.APPROVED,
                admin_notes=i.admin_notes,
                source=i.raw_signal.source if i.raw_signal else "unknown",
                created_at=i.created_at,
            )
            for i in insights
        ],
        total=total,
        pending_count=pending_count,
        approved_count=approved_count,
        rejected_count=rejected_count,
    )


@router.get("/insights/list", response_model=InsightAdminListResponse)
async def list_insights_admin(
    admin: AdminUser,
    search: Annotated[str | None, Query()] = None,
    status_filter: Annotated[str | None, Query(alias="status")] = None,
    min_score: Annotated[float | None, Query(ge=0.0, le=1.0)] = None,
    max_score: Annotated[float | None, Query(ge=0.0, le=1.0)] = None,
    limit: Annotated[int, Query(ge=1, le=100)] = 20,
    offset: Annotated[int, Query(ge=0)] = 0,
    db: AsyncSession = Depends(get_db),
) -> InsightAdminListResponse:
    """
    Full paginated insights list for admin with search and filters (Phase 15.1).
    """
    query = select(Insight).order_by(Insight.created_at.desc())

    if status_filter:
        query = query.where(Insight.admin_status == status_filter)
    if min_score is not None:
        query = query.where(Insight.relevance_score >= min_score)
    if max_score is not None:
        query = query.where(Insight.relevance_score <= max_score)
    if search:
        search_term = f"%{search}%"
        query = query.where(
            Insight.problem_statement.ilike(search_term)
            | Insight.proposed_solution.ilike(search_term)
            | Insight.title.ilike(search_term)
        )

    # Count queries
    count_query = select(func.count()).select_from(query.subquery())
    total = (await db.execute(count_query)).scalar_one()

    pending_count = await count_by_field(db, Insight, "admin_status", InsightStatus.PENDING)
    approved_count = await count_by_field(db, Insight, "admin_status", InsightStatus.APPROVED)
    rejected_count = await count_by_field(db, Insight, "admin_status", InsightStatus.REJECTED)

    result = await db.execute(query.limit(limit).offset(offset))
    insights = result.scalars().all()

    return InsightAdminListResponse(
        items=[
            InsightAdminResponse(
                id=i.id,
                title=i.title,
                problem_statement=i.problem_statement,
                proposed_solution=i.proposed_solution,
                market_size_estimate=i.market_size_estimate,
                relevance_score=i.relevance_score,
                admin_status=i.admin_status or InsightStatus.APPROVED,
                admin_notes=i.admin_notes,
                admin_override_score=i.admin_override_score,
                source=i.raw_signal.source if i.raw_signal else "unknown",
                created_at=i.created_at,
                edited_at=i.edited_at,
                opportunity_score=i.opportunity_score,
                problem_score=i.problem_score,
                feasibility_score=i.feasibility_score,
                why_now_score=i.why_now_score,
                execution_difficulty=i.execution_difficulty,
                go_to_market_score=i.go_to_market_score,
                founder_fit_score=i.founder_fit_score,
                revenue_potential=i.revenue_potential,
                market_gap_analysis=i.market_gap_analysis,
                why_now_analysis=i.why_now_analysis,
                value_ladder=i.value_ladder,
                proof_signals=i.proof_signals,
                execution_plan=i.execution_plan,
                competitor_analysis=i.competitor_analysis,
            )
            for i in insights
        ],
        total=total,
        pending_count=pending_count,
        approved_count=approved_count,
        rejected_count=rejected_count,
    )


@router.patch("/insights/{insight_id}", response_model=InsightAdminResponse)
async def update_insight_admin(
    insight_id: UUID,
    update_data: InsightAdminUpdate,
    admin: AdminUser,
    db: AsyncSession = Depends(get_db),
) -> InsightAdminResponse:
    """
    Full insight editing for admin (Phase 15.1).

    Supports all insight fields: content, scores, analysis, JSONB data.
    All changes are audit-logged.
    """
    insight = await db.get(Insight, insight_id)
    if not insight:
        raise HTTPException(status_code=404, detail="Insight not found")

    # Get admin_users record for edited_by FK
    admin_record_result = await db.execute(
        select(AdminUserModel).where(AdminUserModel.user_id == admin.id)
    )
    admin_record = admin_record_result.scalar_one_or_none()

    # Track changes for audit log
    changes = {}
    update_dict = update_data.model_dump(exclude_unset=True)
    for field, value in update_dict.items():
        old_value = getattr(insight, field, None)
        if old_value != value:
            changes[field] = {"old": str(old_value)[:200], "new": str(value)[:200]}
            setattr(insight, field, value)

    # Track who edited
    if admin_record:
        insight.edited_by = admin_record.id
    insight.edited_at = datetime.now(UTC)

    # Create audit log entry
    if changes:
        audit = AuditLog(
            user_id=admin.id,
            action=AuditLog.ACTION_UPDATE,
            resource_type="insight",
            resource_id=insight_id,
            details={"changes": changes, "admin_email": admin.email},
        )
        db.add(audit)

    await db.commit()
    await db.refresh(insight)

    logger.info(f"Admin {admin.email} updated insight {insight_id}: {list(changes.keys())}")

    return InsightAdminResponse(
        id=insight.id,
        title=insight.title,
        problem_statement=insight.problem_statement,
        proposed_solution=insight.proposed_solution,
        market_size_estimate=insight.market_size_estimate,
        relevance_score=insight.relevance_score,
        admin_status=insight.admin_status or InsightStatus.APPROVED,
        admin_notes=insight.admin_notes,
        admin_override_score=insight.admin_override_score,
        source=insight.raw_signal.source if insight.raw_signal else "unknown",
        created_at=insight.created_at,
        edited_at=insight.edited_at,
        opportunity_score=insight.opportunity_score,
        problem_score=insight.problem_score,
        feasibility_score=insight.feasibility_score,
        why_now_score=insight.why_now_score,
        execution_difficulty=insight.execution_difficulty,
        go_to_market_score=insight.go_to_market_score,
        founder_fit_score=insight.founder_fit_score,
        revenue_potential=insight.revenue_potential,
        market_gap_analysis=insight.market_gap_analysis,
        why_now_analysis=insight.why_now_analysis,
        value_ladder=insight.value_ladder,
        proof_signals=insight.proof_signals,
        execution_plan=insight.execution_plan,
        competitor_analysis=insight.competitor_analysis,
    )


@router.delete("/insights/{insight_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_insight(
    insight_id: UUID,
    admin: AdminUser,
    db: AsyncSession = Depends(get_db),
) -> None:
    """
    Soft-delete an insight with audit logging (Phase 15.1).
    """
    insight = await db.get(Insight, insight_id)
    if not insight:
        raise HTTPException(status_code=404, detail="Insight not found")

    # Audit log
    audit = AuditLog(
        user_id=admin.id,
        action=AuditLog.ACTION_DELETE,
        resource_type="insight",
        resource_id=insight_id,
        details={"title": insight.title, "admin_email": admin.email},
    )
    db.add(audit)

    # Set status to rejected as soft delete
    insight.admin_status = "rejected"
    insight.admin_notes = f"Deleted by admin {admin.email}"
    insight.edited_at = datetime.now(UTC)

    await db.commit()

    logger.info(f"Admin {admin.email} soft-deleted insight {insight_id}")


# ============================================
# INSIGHT EXPORT & BULK OPERATIONS (Phase I.3/I.5)
# ============================================


@router.get("/insights/export")
async def export_insights(
    admin: AdminUser,
    format: Annotated[str, Query()] = "csv",
    status_filter: Annotated[str | None, Query(alias="status")] = None,
    search: Annotated[str | None, Query()] = None,
    ids: Annotated[str | None, Query()] = None,
    db: AsyncSession = Depends(get_db),
):
    """
    Export insights as CSV or JSON (Phase I.3).

    Supports optional filters:
    - status: Filter by admin_status (pending, approved, rejected)
    - search: Search by title/problem/solution
    - ids: Comma-separated list of insight IDs to export specific items
    - format: csv or json (default: csv)
    """
    if format not in ["csv", "json"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid format. Must be 'csv' or 'json'",
        )

    query = select(Insight).order_by(Insight.created_at.desc())

    if status_filter:
        query = query.where(Insight.admin_status == status_filter)
    if search:
        search_term = f"%{search}%"
        query = query.where(
            Insight.problem_statement.ilike(search_term)
            | Insight.proposed_solution.ilike(search_term)
            | Insight.title.ilike(search_term)
        )
    if ids:
        id_list = [id_str.strip() for id_str in ids.split(",") if id_str.strip()]
        if id_list:
            query = query.where(Insight.id.in_(id_list))

    result = await db.execute(query)
    insights = result.scalars().all()

    logger.info(f"Admin {admin.email} exporting {len(insights)} insights as {format}")

    # Define export columns
    export_columns = [
        "id", "title", "problem_statement", "proposed_solution",
        "market_size_estimate", "relevance_score", "admin_status",
        "opportunity_score", "problem_score", "feasibility_score",
        "why_now_score", "execution_difficulty", "go_to_market_score",
        "founder_fit_score", "revenue_potential", "language", "created_at",
    ]

    if format == "json":
        data = []
        for i in insights:
            item = {}
            for col in export_columns:
                value = getattr(i, col, None)
                if isinstance(value, datetime):
                    item[col] = value.isoformat()
                elif isinstance(value, UUID):
                    item[col] = str(value)
                else:
                    item[col] = value
            # Include text analysis fields
            item["market_gap_analysis"] = i.market_gap_analysis
            item["why_now_analysis"] = i.why_now_analysis
            data.append(item)

        return {
            "content_type": "insights",
            "count": len(data),
            "data": data,
        }

    # CSV export
    output = io.StringIO()

    if len(insights) == 0:
        writer = csv.writer(output)
        writer.writerow(["No insights found"])
        output.seek(0)
        return StreamingResponse(
            iter([output.getvalue()]),
            media_type="text/csv",
            headers={
                "Content-Disposition": f"attachment; filename=insights-export-{datetime.now(UTC).strftime('%Y%m%d')}.csv"
            },
        )

    all_columns = export_columns + ["market_gap_analysis", "why_now_analysis"]
    writer = csv.DictWriter(output, fieldnames=all_columns)
    writer.writeheader()

    for i in insights:
        row = {}
        for col in all_columns:
            value = getattr(i, col, None)
            if isinstance(value, datetime):
                row[col] = value.isoformat()
            elif isinstance(value, UUID):
                row[col] = str(value)
            elif isinstance(value, (dict, list)):
                row[col] = json.dumps(value)
            else:
                row[col] = value
        writer.writerow(row)

    output.seek(0)

    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={
            "Content-Disposition": f"attachment; filename=insights-export-{datetime.now(UTC).strftime('%Y%m%d')}.csv"
        },
    )


@router.post("/insights/bulk-delete")
async def bulk_delete_insights(
    admin: AdminUser,
    payload: dict,
    db: AsyncSession = Depends(get_db),
):
    """
    Bulk soft-delete insights by setting status to rejected (Phase I.5).

    Expects: {"ids": ["uuid1", "uuid2", ...]}
    """
    ids = payload.get("ids", [])
    if not ids:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No insight IDs provided",
        )

    if len(ids) > 100:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Maximum 100 insights per bulk operation",
        )

    result = await db.execute(
        select(Insight).where(Insight.id.in_(ids))
    )
    insights = result.scalars().all()

    deleted_count = 0
    for insight in insights:
        insight.admin_status = "rejected"
        insight.admin_notes = f"Bulk deleted by admin {admin.email}"
        insight.edited_at = datetime.now(UTC)
        deleted_count += 1

    # Audit log for bulk operation
    audit = AuditLog(
        user_id=admin.id,
        action=AuditLog.ACTION_DELETE,
        resource_type="insight",
        details={
            "action": "bulk_delete",
            "count": deleted_count,
            "ids": [str(i) for i in ids[:10]],
            "admin_email": admin.email,
        },
    )
    db.add(audit)

    await db.commit()

    logger.info(f"Admin {admin.email} bulk-deleted {deleted_count} insights")

    return {
        "status": "success",
        "deleted_count": deleted_count,
        "total_requested": len(ids),
    }


# ============================================
# METRICS ENDPOINTS
# ============================================


@router.get("/metrics", response_model=list[MetricResponse])
async def query_metrics(
    admin: AdminUser,
    metric_type: Annotated[str | None, Query()] = None,
    start_date: Annotated[datetime | None, Query()] = None,
    end_date: Annotated[datetime | None, Query()] = None,
    limit: Annotated[int, Query(ge=1, le=1000)] = 100,
    db: AsyncSession = Depends(get_db),
) -> list[MetricResponse]:
    """
    Query system metrics with filters.
    """
    query = select(SystemMetric).order_by(SystemMetric.recorded_at.desc())

    if metric_type:
        query = query.where(SystemMetric.metric_type == metric_type)
    if start_date:
        query = query.where(SystemMetric.recorded_at >= start_date)
    if end_date:
        query = query.where(SystemMetric.recorded_at <= end_date)

    result = await db.execute(query.limit(limit))
    metrics = result.scalars().all()

    return [MetricResponse.model_validate(m) for m in metrics]


@router.get("/metrics/summary", response_model=MetricSummaryResponse)
async def get_metrics_summary(
    metric_type: str,
    admin: AdminUser,
    hours: Annotated[int, Query(ge=1, le=168)] = 24,
    db: AsyncSession = Depends(get_db),
) -> MetricSummaryResponse:
    """
    Get aggregated summary for a metric type.
    """
    start_time = datetime.now(UTC) - timedelta(hours=hours)

    # Aggregate metrics
    result = await db.execute(
        select(
            func.count().label("count"),
            func.sum(SystemMetric.metric_value).label("total"),
            func.avg(SystemMetric.metric_value).label("average"),
            func.min(SystemMetric.metric_value).label("min_value"),
            func.max(SystemMetric.metric_value).label("max_value"),
        ).where(
            SystemMetric.metric_type == metric_type,
            SystemMetric.recorded_at >= start_time,
        )
    )
    row = result.one()

    return MetricSummaryResponse(
        metric_type=metric_type,
        count=row.count or 0,
        total=float(row.total or 0),
        average=float(row.average or 0),
        min_value=float(row.min_value or 0),
        max_value=float(row.max_value or 0),
        period_start=start_time,
        period_end=datetime.now(UTC),
    )


@router.get("/errors", response_model=ErrorSummaryResponse)
async def get_error_summary(
    admin: AdminUser,
    hours: Annotated[int, Query(ge=1, le=168)] = 24,
    db: AsyncSession = Depends(get_db),
) -> ErrorSummaryResponse:
    """
    Get error summary for the specified time period.
    """
    start_time = datetime.now(UTC) - timedelta(hours=hours)

    # Get total errors (multiple WHERE conditions, keep manual)
    total_result = await db.execute(
        select(func.count()).select_from(SystemMetric).where(
            SystemMetric.metric_type == "error_rate",
            SystemMetric.recorded_at >= start_time,
        )
    )
    total_errors = total_result.scalar_one() or 0

    # Get errors by type (from dimensions)
    errors_result = await db.execute(
        select(SystemMetric).where(
            SystemMetric.metric_type == "error_rate",
            SystemMetric.recorded_at >= start_time,
        ).order_by(SystemMetric.recorded_at.desc()).limit(50)
    )
    errors = errors_result.scalars().all()

    # Aggregate by type and source
    errors_by_type: dict[str, int] = {}
    errors_by_source: dict[str, int] = {}

    for error in errors:
        error_type = error.dimensions.get("error_type", "unknown")
        source = error.dimensions.get("source", "unknown")

        errors_by_type[error_type] = errors_by_type.get(error_type, 0) + 1
        if source:
            errors_by_source[source] = errors_by_source.get(source, 0) + 1

    return ErrorSummaryResponse(
        total_errors_today=total_errors,
        errors_by_type=errors_by_type,
        errors_by_source=errors_by_source,
        recent_errors=[],  # TODO: Convert to ErrorEntry list
    )


# ============================================
# BULK EXPORT/IMPORT ENDPOINTS (Phase 15.4)
# ============================================


@router.get("/export/{content_type}")
async def export_content(
    content_type: str,
    admin: AdminUser,
    format: Annotated[str, Query()] = "csv",
    db: AsyncSession = Depends(get_db),
):
    """
    Bulk export content as CSV or JSON (Phase 15.4).

    Content types: tools, trends, market-insights, success-stories
    Formats: csv, json
    """
    # Map content type to model
    model_map = {
        "tools": Tool,
        "trends": Trend,
        "market-insights": MarketInsight,
        "success-stories": SuccessStory,
    }

    if content_type not in model_map:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid content type. Must be one of: {', '.join(model_map.keys())}",
        )

    if format not in ["csv", "json"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid format. Must be 'csv' or 'json'",
        )

    model = model_map[content_type]

    # Fetch all records
    result = await db.execute(select(model).order_by(model.created_at.desc()))
    records = result.scalars().all()

    logger.info(f"Admin {admin.email} exporting {len(records)} {content_type} records as {format}")

    if format == "json":
        # JSON export: return list of records as dicts
        data = []
        for record in records:
            item = {}
            for column in record.__table__.columns:
                value = getattr(record, column.name)
                # Convert datetime to ISO string, UUID to string
                if isinstance(value, datetime):
                    item[column.name] = value.isoformat()
                elif isinstance(value, UUID):
                    item[column.name] = str(value)
                else:
                    item[column.name] = value
            data.append(item)

        return {"content_type": content_type, "count": len(data), "data": data}

    # CSV export
    output = io.StringIO()

    if len(records) == 0:
        # Empty export
        writer = csv.writer(output)
        writer.writerow(["No records found"])
        output.seek(0)
        return StreamingResponse(
            iter([output.getvalue()]),
            media_type="text/csv",
            headers={
                "Content-Disposition": f"attachment; filename={content_type}-export-{datetime.now(UTC).strftime('%Y%m%d')}.csv"
            },
        )

    # Get column names from first record
    first_record = records[0]
    fieldnames = [col.name for col in first_record.__table__.columns]

    writer = csv.DictWriter(output, fieldnames=fieldnames)
    writer.writeheader()

    for record in records:
        row = {}
        for column in record.__table__.columns:
            value = getattr(record, column.name)
            # Convert datetime to ISO string, UUID to string, JSONB to JSON string
            if isinstance(value, datetime):
                row[column.name] = value.isoformat()
            elif isinstance(value, UUID):
                row[column.name] = str(value)
            elif isinstance(value, (dict, list)):
                row[column.name] = json.dumps(value)
            else:
                row[column.name] = value
        writer.writerow(row)

    output.seek(0)

    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={
            "Content-Disposition": f"attachment; filename={content_type}-export-{datetime.now(UTC).strftime('%Y%m%d')}.csv"
        },
    )


@router.post("/import/{content_type}")
async def import_content(
    content_type: str,
    admin: AdminUser,
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
):
    """
    Bulk import content from CSV or JSON file (Phase 15.4).

    Content types: tools, trends, market-insights, success-stories
    File formats: .csv, .json
    """
    # Map content type to model
    model_map = {
        "tools": Tool,
        "trends": Trend,
        "market-insights": MarketInsight,
        "success-stories": SuccessStory,
    }

    if content_type not in model_map:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid content type. Must be one of: {', '.join(model_map.keys())}",
        )

    model = model_map[content_type]

    # Read file content
    content = await file.read()

    imported_count = 0
    failed_count = 0
    errors = []

    try:
        # Detect format from filename or content
        if file.filename and file.filename.endswith(".json"):
            # JSON import
            data = json.loads(content.decode("utf-8"))

            # Handle both [{...}, {...}] and {data: [{...}]} formats
            if isinstance(data, dict) and "data" in data:
                records_data = data["data"]
            elif isinstance(data, list):
                records_data = data
            else:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="JSON must be an array or object with 'data' key",
                )

            for idx, record_data in enumerate(records_data):
                try:
                    # Remove id and timestamps to allow fresh creation
                    record_data.pop("id", None)
                    record_data.pop("created_at", None)
                    record_data.pop("updated_at", None)

                    # Parse datetime fields if present
                    for field in ["published_at"]:
                        if field in record_data and record_data[field]:
                            record_data[field] = datetime.fromisoformat(record_data[field].replace("Z", "+00:00"))

                    # Parse JSONB fields if they're strings
                    for field in ["translations", "metrics", "timeline", "trend_data"]:
                        if field in record_data and isinstance(record_data[field], str):
                            record_data[field] = json.loads(record_data[field])

                    # Create new record
                    new_record = model(**record_data)
                    db.add(new_record)
                    imported_count += 1

                except Exception as e:
                    failed_count += 1
                    errors.append(f"Row {idx + 1}: {str(e)[:100]}")

        else:
            # CSV import
            csv_content = io.StringIO(content.decode("utf-8"))
            reader = csv.DictReader(csv_content)

            for idx, row in enumerate(reader):
                try:
                    # Remove empty string values
                    record_data = {k: v for k, v in row.items() if v}

                    # Remove id and timestamps
                    record_data.pop("id", None)
                    record_data.pop("created_at", None)
                    record_data.pop("updated_at", None)

                    # Parse datetime fields
                    for field in ["published_at"]:
                        if field in record_data and record_data[field]:
                            record_data[field] = datetime.fromisoformat(record_data[field].replace("Z", "+00:00"))

                    # Parse JSONB fields from JSON strings
                    for field in ["translations", "metrics", "timeline", "trend_data"]:
                        if field in record_data and record_data[field]:
                            record_data[field] = json.loads(record_data[field])

                    # Parse boolean fields
                    for field in ["is_featured", "is_published"]:
                        if field in record_data:
                            record_data[field] = record_data[field].lower() in ["true", "1", "yes"]

                    # Parse numeric fields
                    for field in ["reading_time_minutes", "view_count", "search_volume", "sort_order"]:
                        if field in record_data and record_data[field]:
                            record_data[field] = int(record_data[field])

                    for field in ["growth_percentage"]:
                        if field in record_data and record_data[field]:
                            record_data[field] = float(record_data[field])

                    # Create new record
                    new_record = model(**record_data)
                    db.add(new_record)
                    imported_count += 1

                except Exception as e:
                    failed_count += 1
                    errors.append(f"Row {idx + 2}: {str(e)[:100]}")  # +2 because of header row

        # Commit all successful imports
        if imported_count > 0:
            await db.commit()

        logger.info(
            f"Admin {admin.email} imported {imported_count} {content_type} records "
            f"({failed_count} failed)"
        )

        return {
            "content_type": content_type,
            "imported_count": imported_count,
            "failed_count": failed_count,
            "errors": errors[:10],  # Return first 10 errors
        }

    except json.JSONDecodeError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid JSON format: {str(e)}",
        )
    except Exception as e:
        logger.error(f"Import error: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Import failed: {str(e)}",
        )


# ============================================
# ADMIN USER MANAGEMENT ENDPOINTS
# ============================================


@router.get("/admin-users", response_model=AdminUserListResponse)
async def list_admin_users(
    admin: AdminUser,
    db: AsyncSession = Depends(get_db),
) -> AdminUserListResponse:
    """
    List all admin users with joined user info.

    Returns admin records with email, display_name, role, and created_at.
    """
    result = await db.execute(
        select(AdminUserModel).order_by(AdminUserModel.created_at.desc())
    )
    admin_users = result.scalars().all()

    items = []
    for au in admin_users:
        items.append(
            AdminUserResponse(
                id=au.id,
                user_id=au.user_id,
                role=au.role,
                permissions=au.permissions,
                created_at=au.created_at,
                user_email=au.user.email if au.user else None,
                user_display_name=au.user.display_name if au.user else None,
            )
        )

    logger.info(f"Admin {admin.email} listed {len(items)} admin users")

    return AdminUserListResponse(items=items, total=len(items))


@router.post("/admin-users", response_model=AdminUserResponse, status_code=status.HTTP_201_CREATED)
async def promote_user_to_admin(
    payload: AdminUserPromoteRequest,
    admin: AdminUser,
    db: AsyncSession = Depends(get_db),
) -> AdminUserResponse:
    """
    Promote a user to admin by email.

    Looks up the user by email, then creates an admin_users record
    with the specified role (superadmin, admin, moderator, or viewer).
    """
    # Find user by email
    user_result = await db.execute(
        select(UserModel).where(UserModel.email == payload.email)
    )
    target_user = user_result.scalar_one_or_none()

    if not target_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No user found with email: {payload.email}",
        )

    # Check if user is already an admin
    existing_result = await db.execute(
        select(AdminUserModel).where(AdminUserModel.user_id == target_user.id)
    )
    if existing_result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"User {payload.email} is already an admin",
        )

    # Create admin user record
    new_admin = AdminUserModel(
        user_id=target_user.id,
        role=payload.role.value,
        permissions={},
    )
    db.add(new_admin)

    # Audit log
    audit = AuditLog(
        user_id=admin.id,
        action=AuditLog.ACTION_CREATE,
        resource_type="admin_user",
        resource_id=new_admin.id,
        details={
            "promoted_email": payload.email,
            "promoted_user_id": str(target_user.id),
            "role": payload.role.value,
            "admin_email": admin.email,
        },
    )
    db.add(audit)

    await db.commit()
    await db.refresh(new_admin)

    logger.info(
        f"Admin {admin.email} promoted {payload.email} to {payload.role.value}"
    )

    return AdminUserResponse(
        id=new_admin.id,
        user_id=new_admin.user_id,
        role=new_admin.role,
        permissions=new_admin.permissions,
        created_at=new_admin.created_at,
        user_email=target_user.email,
        user_display_name=target_user.display_name,
    )


@router.patch("/admin-users/{admin_user_id}", response_model=AdminUserResponse)
async def update_admin_role(
    admin_user_id: UUID,
    payload: AdminUserUpdateRequest,
    admin: AdminUser,
    db: AsyncSession = Depends(get_db),
) -> AdminUserResponse:
    """
    Update an admin user's role.

    Changes the role of an existing admin user record.
    """
    admin_record = await db.get(AdminUserModel, admin_user_id)
    if not admin_record:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Admin user record not found",
        )

    old_role = admin_record.role
    admin_record.role = payload.role.value

    # Audit log
    audit = AuditLog(
        user_id=admin.id,
        action=AuditLog.ACTION_UPDATE,
        resource_type="admin_user",
        resource_id=admin_user_id,
        details={
            "old_role": old_role,
            "new_role": payload.role.value,
            "target_user_id": str(admin_record.user_id),
            "admin_email": admin.email,
        },
    )
    db.add(audit)

    await db.commit()
    await db.refresh(admin_record)

    # Invalidate Redis cache for the affected user
    cache_key = f"admin_role:{admin_record.user_id}"
    try:
        from app.api.deps import get_redis
        redis = await get_redis()
        await redis.delete(cache_key)
    except Exception as e:
        logger.warning(f"Failed to invalidate admin cache for {admin_record.user_id}: {e}")

    logger.info(
        f"Admin {admin.email} changed admin_user {admin_user_id} role: "
        f"{old_role} -> {payload.role.value}"
    )

    return AdminUserResponse(
        id=admin_record.id,
        user_id=admin_record.user_id,
        role=admin_record.role,
        permissions=admin_record.permissions,
        created_at=admin_record.created_at,
        user_email=admin_record.user.email if admin_record.user else None,
        user_display_name=admin_record.user.display_name if admin_record.user else None,
    )


@router.delete("/admin-users/{admin_user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_admin_access(
    admin_user_id: UUID,
    admin: AdminUser,
    db: AsyncSession = Depends(get_db),
) -> None:
    """
    Remove admin access from a user.

    Deletes the admin_users record but keeps the user account intact.
    An admin cannot remove their own admin access.
    """
    admin_record = await db.get(AdminUserModel, admin_user_id)
    if not admin_record:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Admin user record not found",
        )

    # Prevent self-removal
    if admin_record.user_id == admin.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot remove your own admin access",
        )

    target_email = admin_record.user.email if admin_record.user else "unknown"
    target_user_id = admin_record.user_id

    # Audit log
    audit = AuditLog(
        user_id=admin.id,
        action=AuditLog.ACTION_DELETE,
        resource_type="admin_user",
        resource_id=admin_user_id,
        details={
            "removed_email": target_email,
            "removed_user_id": str(target_user_id),
            "removed_role": admin_record.role,
            "admin_email": admin.email,
        },
    )
    db.add(audit)

    await db.delete(admin_record)
    await db.commit()

    # Invalidate Redis cache for the removed user
    cache_key = f"admin_role:{target_user_id}"
    try:
        from app.api.deps import get_redis
        redis = await get_redis()
        await redis.delete(cache_key)
    except Exception as e:
        logger.warning(f"Failed to invalidate admin cache for {target_user_id}: {e}")

    logger.info(
        f"Admin {admin.email} removed admin access for {target_email} "
        f"(admin_user_id={admin_user_id})"
    )


# ============================================
# IMAGE UPLOAD (Phase 20.1)
# ============================================

UPLOAD_DIR = Path("uploads/images")
ALLOWED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".gif", ".webp", ".svg"}
MAX_FILE_SIZE = 5 * 1024 * 1024  # 5MB


@router.post("/upload")
async def upload_image(
    request: Request,
    admin: AdminUser,
    file: UploadFile = File(...),
):
    """
    Upload an image for use in admin content (market insights, tools, etc.).

    Returns a public URL for the uploaded image.
    Max size: 5MB. Formats: jpg, png, gif, webp, svg.
    """
    # Validate file extension
    ext = Path(file.filename or "").suffix.lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"File type {ext} not allowed. Use: {', '.join(ALLOWED_EXTENSIONS)}",
        )

    # Read and validate size
    contents = await file.read()
    if len(contents) > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"File too large. Max size: {MAX_FILE_SIZE // (1024*1024)}MB",
        )

    # Generate unique filename from content hash
    content_hash = hashlib.sha256(contents).hexdigest()[:16]
    filename = f"{content_hash}{ext}"

    # Save file
    UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
    filepath = UPLOAD_DIR / filename
    filepath.write_bytes(contents)

    # Return URL (assumes static file serving is configured)
    public_url = f"/uploads/images/{filename}"

    logger.info(f"Admin {admin.email} uploaded image: {filename} ({len(contents)} bytes)")

    return {
        "url": public_url,
        "filename": filename,
        "size": len(contents),
        "content_type": file.content_type,
    }
