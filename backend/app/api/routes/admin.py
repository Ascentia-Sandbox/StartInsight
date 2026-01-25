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
import json
import logging
from datetime import datetime, timedelta
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from redis import asyncio as aioredis
from sqlalchemy import func, select, text
from sqlalchemy.ext.asyncio import AsyncSession
from sse_starlette.sse import EventSourceResponse

from app.api.deps import AdminUser
from app.core.config import settings
from app.core.rate_limits import limiter
from app.db.query_helpers import count_by_field
from app.db.session import get_db, AsyncSessionLocal
from app.models.agent_execution_log import AgentExecutionLog
from app.models.insight import Insight
from app.models.system_metric import SystemMetric
from app.schemas.admin import (
    AgentControlResponse,
    AgentStatusResponse,
    AgentType,
    DashboardMetricsResponse,
    ErrorSummaryResponse,
    ExecutionLogListResponse,
    ExecutionLogResponse,
    InsightAdminUpdate,
    InsightReviewResponse,
    MetricQueryRequest,
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
                        "data": json.dumps({"error": str(e)}),
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
    today_start = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)

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
        "timestamp": datetime.utcnow().isoformat(),
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
    today_start = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
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
    agent_type: AgentType,
    admin: AdminUser,
    db: AsyncSession = Depends(get_db),
) -> AgentControlResponse:
    """
    Pause agent execution.

    Agent will skip next scheduled run until resumed.
    """
    # Log admin action
    log = AgentExecutionLog(
        agent_type=agent_type.value,
        status="skipped",
        error_message=f"Paused by admin {admin.email}",
        extra_metadata={"action": "pause", "admin_id": str(admin.id)},
    )
    db.add(log)
    await db.commit()

    logger.info(f"Agent {agent_type} paused by admin {admin.email}")

    return AgentControlResponse(
        status="paused",
        agent_type=agent_type.value,
        triggered_by=admin.email,
        timestamp=datetime.utcnow(),
    )


@router.post("/agents/{agent_type}/resume", response_model=AgentControlResponse)
@limiter.limit("20/minute")  # Phase 2: SlowAPI rate limiting
async def resume_agent(
    agent_type: AgentType,
    admin: AdminUser,
    db: AsyncSession = Depends(get_db),
) -> AgentControlResponse:
    """
    Resume paused agent execution.
    """
    # Log admin action
    log = AgentExecutionLog(
        agent_type=agent_type.value,
        status="running",
        error_message=f"Resumed by admin {admin.email}",
        extra_metadata={"action": "resume", "admin_id": str(admin.id)},
    )
    db.add(log)
    await db.commit()

    logger.info(f"Agent {agent_type} resumed by admin {admin.email}")

    return AgentControlResponse(
        status="running",
        agent_type=agent_type.value,
        triggered_by=admin.email,
        timestamp=datetime.utcnow(),
    )


@router.post("/agents/{agent_type}/trigger", response_model=AgentControlResponse)
@limiter.limit("20/minute")  # Phase 2: SlowAPI rate limiting
async def trigger_agent(
    agent_type: AgentType,
    admin: AdminUser,
    db: AsyncSession = Depends(get_db),
) -> AgentControlResponse:
    """
    Manually trigger agent execution (out of schedule).
    """
    # Create execution log
    log = AgentExecutionLog(
        agent_type=agent_type.value,
        status="running",
        extra_metadata={"action": "manual_trigger", "admin_id": str(admin.id)},
    )
    db.add(log)
    await db.commit()
    await db.refresh(log)

    # TODO: Actually enqueue the task with Arq
    # from app.worker import arq_redis
    # job = await arq_redis.enqueue_job(task_map[agent_type])

    logger.info(f"Agent {agent_type} triggered by admin {admin.email}")

    return AgentControlResponse(
        status="triggered",
        agent_type=agent_type.value,
        triggered_by=admin.email,
        job_id=str(log.id),
        timestamp=datetime.utcnow(),
    )


# ============================================
# INSIGHT MODERATION ENDPOINTS
# ============================================


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
    pending_count = await count_by_field(db, Insight, "admin_status", "pending")
    approved_count = await count_by_field(db, Insight, "admin_status", "approved")
    rejected_count = await count_by_field(db, Insight, "admin_status", "rejected")

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
                admin_status=i.admin_status or "approved",
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


@router.patch("/insights/{insight_id}", response_model=InsightReviewResponse)
async def update_insight_status(
    insight_id: UUID,
    update_data: InsightAdminUpdate,
    admin: AdminUser,
    db: AsyncSession = Depends(get_db),
) -> InsightReviewResponse:
    """
    Update insight admin status (approve/reject).
    """
    # Get insight
    insight = await db.get(Insight, insight_id)
    if not insight:
        raise HTTPException(status_code=404, detail="Insight not found")

    # Get admin_users record for edited_by FK
    from app.models.admin_user import AdminUser as AdminUserModel

    admin_record_result = await db.execute(
        select(AdminUserModel).where(AdminUserModel.user_id == admin.id)
    )
    admin_record = admin_record_result.scalar_one_or_none()

    # Update fields
    if update_data.admin_status is not None:
        insight.admin_status = update_data.admin_status
    if update_data.admin_notes is not None:
        insight.admin_notes = update_data.admin_notes
    if update_data.admin_override_score is not None:
        insight.admin_override_score = update_data.admin_override_score

    # Track who edited
    if admin_record:
        insight.edited_by = admin_record.id
    insight.edited_at = datetime.utcnow()

    await db.commit()
    await db.refresh(insight)

    logger.info(f"Admin {admin.email} updated insight {insight_id}")

    return InsightReviewResponse(
        id=insight.id,
        problem_statement=insight.problem_statement,
        proposed_solution=insight.proposed_solution,
        relevance_score=insight.relevance_score,
        admin_status=insight.admin_status or "approved",
        admin_notes=insight.admin_notes,
        source=insight.raw_signal.source if insight.raw_signal else "unknown",
        created_at=insight.created_at,
    )


@router.delete("/insights/{insight_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_insight(
    insight_id: UUID,
    admin: AdminUser,
    db: AsyncSession = Depends(get_db),
) -> None:
    """
    Delete an insight (admin only).
    """
    insight = await db.get(Insight, insight_id)
    if not insight:
        raise HTTPException(status_code=404, detail="Insight not found")

    await db.delete(insight)
    await db.commit()

    logger.info(f"Admin {admin.email} deleted insight {insight_id}")


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
    start_time = datetime.utcnow() - timedelta(hours=hours)

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
        period_end=datetime.utcnow(),
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
    start_time = datetime.utcnow() - timedelta(hours=hours)

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
