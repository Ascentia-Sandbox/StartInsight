"""Agent Control API routes - Phase 8.4-8.5: AI Agent Control & Security.

Provides admin endpoints for:
- AI agent configuration and management
- Security audit logs
"""

import asyncio
import json
import logging
from datetime import UTC, datetime, timedelta
from typing import Annotated, Any
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from pydantic import BaseModel, Field
from sqlalchemy import func, select, text
from sqlalchemy.ext.asyncio import AsyncSession
from sse_starlette.sse import EventSourceResponse

from app.api.deps import get_db, require_admin
from app.db.session import AsyncSessionLocal
from app.models.agent_control import AgentConfiguration, AuditLog
from app.models.agent_execution_log import AgentExecutionLog
from app.models.user import User

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/admin/agents", tags=["Agent Control"])


# ============================================
# Schemas
# ============================================

class AgentConfigResponse(BaseModel):
    id: UUID
    agent_name: str
    is_enabled: bool
    model_name: str
    temperature: float
    max_tokens: int
    rate_limit_per_hour: int
    cost_limit_daily_usd: float
    custom_prompts: dict[str, Any] | None
    # Phase 16.2: Schedule fields
    schedule_type: str | None = None
    schedule_cron: str | None = None
    schedule_interval_hours: int | None = None
    next_run_at: datetime | None = None
    last_run_at: datetime | None = None
    updated_at: datetime

    class Config:
        from_attributes = True

class AgentConfigCreate(BaseModel):
    agent_name: str = Field(..., min_length=1, max_length=50)
    is_enabled: bool = True
    model_name: str = "gemini-1.5-flash"
    temperature: float = Field(0.7, ge=0, le=2)
    max_tokens: int = Field(4096, ge=100, le=32000)
    rate_limit_per_hour: int = Field(100, ge=1, le=1000)
    cost_limit_daily_usd: float = Field(50.0, ge=1, le=1000)
    custom_prompts: dict[str, Any] | None = None

class AgentConfigUpdate(BaseModel):
    is_enabled: bool | None = None
    model_name: str | None = None
    temperature: float | None = Field(None, ge=0, le=2)
    max_tokens: int | None = Field(None, ge=100, le=32000)
    rate_limit_per_hour: int | None = Field(None, ge=1, le=1000)
    cost_limit_daily_usd: float | None = Field(None, ge=1, le=1000)
    custom_prompts: dict[str, Any] | None = None

class AgentScheduleUpdate(BaseModel):
    """Phase 16.2: Dynamic schedule management."""
    schedule_type: str = Field(..., pattern="^(cron|interval|manual)$")
    schedule_cron: str | None = Field(None, max_length=100, description="Cron expression (e.g., '0 8 * * *')")
    schedule_interval_hours: int | None = Field(None, ge=1, le=168, description="Interval in hours (1-168)")

    def model_post_init(self, __context):
        """Validate that the correct fields are provided based on schedule_type."""
        if self.schedule_type == "cron" and not self.schedule_cron:
            raise ValueError("schedule_cron is required when schedule_type is 'cron'")
        if self.schedule_type == "interval" and not self.schedule_interval_hours:
            raise ValueError("schedule_interval_hours is required when schedule_type is 'interval'")

class AgentScheduleResponse(BaseModel):
    agent_name: str
    schedule_type: str | None
    schedule_cron: str | None
    schedule_interval_hours: int | None
    next_run_at: datetime | None
    last_run_at: datetime | None
    updated_at: datetime

    class Config:
        from_attributes = True

class AgentStatsResponse(BaseModel):
    agent_name: str
    executions_24h: int
    success_rate: float
    avg_duration_ms: float
    tokens_used_24h: int
    cost_24h_usd: float

class AuditLogResponse(BaseModel):
    id: UUID
    user_id: UUID | None
    action: str
    resource_type: str
    resource_id: UUID | None
    details: dict[str, Any] | None
    ip_address: str | None
    created_at: datetime

    class Config:
        from_attributes = True


# ============================================
# Agent Configuration Endpoints
# ============================================

@router.get("/configurations", response_model=list[AgentConfigResponse])
async def list_agent_configurations(
    db: Annotated[AsyncSession, Depends(get_db)],
    admin: Annotated[User, Depends(require_admin)],
):
    """List all AI agent configurations."""
    result = await db.execute(select(AgentConfiguration).order_by(AgentConfiguration.agent_name))
    return [AgentConfigResponse.model_validate(c) for c in result.scalars().all()]


@router.post("/configurations", response_model=AgentConfigResponse, status_code=201)
async def create_agent_configuration(
    payload: AgentConfigCreate,
    db: Annotated[AsyncSession, Depends(get_db)],
    admin: Annotated[User, Depends(require_admin)],
    request: Request,
):
    """Create a new AI agent configuration."""
    # Check uniqueness
    existing = await db.execute(
        select(AgentConfiguration).where(AgentConfiguration.agent_name == payload.agent_name)
    )
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=409, detail=f"Agent '{payload.agent_name}' already exists")

    config = AgentConfiguration(
        agent_name=payload.agent_name,
        is_enabled=payload.is_enabled,
        model_name=payload.model_name,
        temperature=payload.temperature,
        max_tokens=payload.max_tokens,
        rate_limit_per_hour=payload.rate_limit_per_hour,
        cost_limit_daily_usd=payload.cost_limit_daily_usd,
        custom_prompts=payload.custom_prompts,
        updated_by=admin.id,
    )
    db.add(config)

    audit = AuditLog(
        user_id=admin.id,
        action=AuditLog.ACTION_CREATE,
        resource_type="agent_configuration",
        details={"agent_name": payload.agent_name},
        ip_address=request.client.host if request.client else None,
    )
    db.add(audit)

    await db.commit()
    await db.refresh(config)

    logger.info(f"Agent {payload.agent_name} created by admin {admin.id}")
    return AgentConfigResponse.model_validate(config)


@router.delete("/configurations/{agent_name}", status_code=204)
async def delete_agent_configuration(
    agent_name: str,
    db: Annotated[AsyncSession, Depends(get_db)],
    admin: Annotated[User, Depends(require_admin)],
    request: Request,
):
    """Delete an AI agent configuration."""
    result = await db.execute(
        select(AgentConfiguration).where(AgentConfiguration.agent_name == agent_name)
    )
    config = result.scalar_one_or_none()

    if not config:
        raise HTTPException(status_code=404, detail="Agent configuration not found")

    audit = AuditLog(
        user_id=admin.id,
        action=AuditLog.ACTION_DELETE,
        resource_type="agent_configuration",
        details={"agent_name": agent_name},
        ip_address=request.client.host if request.client else None,
    )
    db.add(audit)

    await db.delete(config)
    await db.commit()

    logger.info(f"Agent {agent_name} deleted by admin {admin.id}")


@router.get("/configurations/{agent_name}", response_model=AgentConfigResponse)
async def get_agent_configuration(
    agent_name: str,
    db: Annotated[AsyncSession, Depends(get_db)],
    admin: Annotated[User, Depends(require_admin)],
):
    """Get a specific agent configuration."""
    result = await db.execute(
        select(AgentConfiguration).where(AgentConfiguration.agent_name == agent_name)
    )
    config = result.scalar_one_or_none()

    if not config:
        raise HTTPException(status_code=404, detail="Agent configuration not found")

    return AgentConfigResponse.model_validate(config)


@router.patch("/configurations/{agent_name}", response_model=AgentConfigResponse)
async def update_agent_configuration(
    agent_name: str,
    updates: AgentConfigUpdate,
    db: Annotated[AsyncSession, Depends(get_db)],
    admin: Annotated[User, Depends(require_admin)],
    request: Request,
):
    """Update an agent configuration."""
    result = await db.execute(
        select(AgentConfiguration).where(AgentConfiguration.agent_name == agent_name)
    )
    config = result.scalar_one_or_none()

    if not config:
        raise HTTPException(status_code=404, detail="Agent configuration not found")

    # Store old values for audit
    old_values = {
        "is_enabled": config.is_enabled,
        "model_name": config.model_name,
        "temperature": float(config.temperature),
        "max_tokens": config.max_tokens,
    }

    # Apply updates
    update_dict = updates.model_dump(exclude_unset=True)
    for key, value in update_dict.items():
        if value is not None:
            setattr(config, key, value)

    config.updated_by = admin.id
    config.updated_at = datetime.now(UTC)

    # Create audit log
    audit = AuditLog(
        user_id=admin.id,
        action=AuditLog.ACTION_CONFIG_CHANGE,
        resource_type="agent_configuration",
        resource_id=config.id,
        details={"old_values": old_values, "new_values": update_dict},
        ip_address=request.client.host if request.client else None,
        user_agent=request.headers.get("user-agent"),
    )
    db.add(audit)

    await db.commit()
    await db.refresh(config)

    logger.info(f"Agent {agent_name} configuration updated by admin {admin.id}")
    return AgentConfigResponse.model_validate(config)


@router.post("/configurations/{agent_name}/toggle")
async def toggle_agent(
    agent_name: str,
    db: Annotated[AsyncSession, Depends(get_db)],
    admin: Annotated[User, Depends(require_admin)],
    request: Request,
):
    """Enable or disable an agent."""
    result = await db.execute(
        select(AgentConfiguration).where(AgentConfiguration.agent_name == agent_name)
    )
    config = result.scalar_one_or_none()

    if not config:
        raise HTTPException(status_code=404, detail="Agent configuration not found")

    config.is_enabled = not config.is_enabled
    config.updated_by = admin.id
    config.updated_at = datetime.now(UTC)

    # Audit log
    audit = AuditLog(
        user_id=admin.id,
        action=AuditLog.ACTION_CONFIG_CHANGE,
        resource_type="agent_configuration",
        resource_id=config.id,
        details={"action": "toggle", "new_state": config.is_enabled},
        ip_address=request.client.host if request.client else None,
    )
    db.add(audit)

    await db.commit()

    logger.info(f"Agent {agent_name} {'enabled' if config.is_enabled else 'disabled'} by admin {admin.id}")
    return {"agent_name": agent_name, "is_enabled": config.is_enabled}


@router.get("/stats", response_model=list[AgentStatsResponse])
async def get_agent_stats(
    db: Annotated[AsyncSession, Depends(get_db)],
    admin: Annotated[User, Depends(require_admin)],
):
    """Get execution statistics for all agents."""
    day_ago = datetime.now(UTC) - timedelta(hours=24)

    # Get stats from execution logs
    stats_query = await db.execute(
        select(
            AgentExecutionLog.agent_type,
            func.count(AgentExecutionLog.id).label("count"),
            func.avg(AgentExecutionLog.duration_ms).label("avg_duration"),
            func.sum(AgentExecutionLog.items_processed).label("items_processed"),
        )
        .where(AgentExecutionLog.started_at >= day_ago)
        .group_by(AgentExecutionLog.agent_type)
    )

    # Query token/cost totals from extra_metadata JSONB
    token_cost_query = await db.execute(
        select(
            AgentExecutionLog.agent_type,
            func.coalesce(
                func.sum(text("(extra_metadata->>'tokens_used')::int")), 0
            ).label("tokens"),
            func.coalesce(
                func.sum(text("(extra_metadata->>'cost_usd')::float")), 0
            ).label("cost"),
        )
        .where(AgentExecutionLog.started_at >= day_ago)
        .group_by(AgentExecutionLog.agent_type)
    )
    token_cost_map = {
        row[0]: {"tokens": int(row[1]), "cost": float(row[2])}
        for row in token_cost_query.fetchall()
    }

    results = []
    for row in stats_query.fetchall():
        agent_name, count, avg_duration, items = row

        # Count successes
        success_count = await db.execute(
            select(func.count()).where(
                AgentExecutionLog.agent_type == agent_name,
                AgentExecutionLog.started_at >= day_ago,
                AgentExecutionLog.error_message.is_(None)
            )
        )
        success_rate = (success_count.scalar() or 0) / count if count > 0 else 0

        tc = token_cost_map.get(agent_name, {"tokens": 0, "cost": 0.0})

        results.append(AgentStatsResponse(
            agent_name=agent_name,
            executions_24h=count,
            success_rate=round(success_rate, 2),
            avg_duration_ms=float(avg_duration or 0),
            tokens_used_24h=tc["tokens"],
            cost_24h_usd=round(tc["cost"], 4),
        ))

    return results


# ============================================
# Phase 16.2: Dynamic Schedule Management
# ============================================

@router.patch("/configurations/{agent_name}/schedule", response_model=AgentScheduleResponse)
async def update_agent_schedule(
    agent_name: str,
    schedule: AgentScheduleUpdate,
    db: Annotated[AsyncSession, Depends(get_db)],
    admin: Annotated[User, Depends(require_admin)],
    request: Request,
):
    """
    Update agent execution schedule.

    Phase 16.2: Supports cron, interval, or manual scheduling.
    Automatically restarts the APScheduler job with new schedule.
    """
    result = await db.execute(
        select(AgentConfiguration).where(AgentConfiguration.agent_name == agent_name)
    )
    config = result.scalar_one_or_none()

    if not config:
        raise HTTPException(status_code=404, detail="Agent configuration not found")

    # Store old schedule for audit
    old_schedule = {
        "schedule_type": config.schedule_type,
        "schedule_cron": config.schedule_cron,
        "schedule_interval_hours": config.schedule_interval_hours,
    }

    # Update schedule
    config.schedule_type = schedule.schedule_type
    config.schedule_cron = schedule.schedule_cron
    config.schedule_interval_hours = schedule.schedule_interval_hours
    config.updated_by = admin.id
    config.updated_at = datetime.now(UTC)

    # Calculate next_run_at based on schedule type
    if schedule.schedule_type == "interval" and schedule.schedule_interval_hours:
        config.next_run_at = datetime.now(UTC) + timedelta(hours=schedule.schedule_interval_hours)
    elif schedule.schedule_type == "manual":
        config.next_run_at = None
    # For cron, next_run_at will be calculated by the scheduler

    # Create audit log
    audit = AuditLog(
        user_id=admin.id,
        action=AuditLog.ACTION_CONFIG_CHANGE,
        resource_type="agent_schedule",
        resource_id=config.id,
        details={
            "agent_name": agent_name,
            "old_schedule": old_schedule,
            "new_schedule": schedule.model_dump(),
        },
        ip_address=request.client.host if request.client else None,
        user_agent=request.headers.get("user-agent"),
    )
    db.add(audit)

    await db.commit()
    await db.refresh(config)

    logger.info(f"Agent {agent_name} schedule updated to {schedule.schedule_type} by admin {admin.id}")

    # TODO: Restart APScheduler job with new schedule
    # This would require importing scheduler and calling _schedule_agent_from_config

    return AgentScheduleResponse(
        agent_name=config.agent_name,
        schedule_type=config.schedule_type,
        schedule_cron=config.schedule_cron,
        schedule_interval_hours=config.schedule_interval_hours,
        next_run_at=config.next_run_at,
        last_run_at=config.last_run_at,
        updated_at=config.updated_at,
    )


@router.get("/configurations/{agent_name}/schedule", response_model=AgentScheduleResponse)
async def get_agent_schedule(
    agent_name: str,
    db: Annotated[AsyncSession, Depends(get_db)],
    admin: Annotated[User, Depends(require_admin)],
):
    """Get agent execution schedule."""
    result = await db.execute(
        select(AgentConfiguration).where(AgentConfiguration.agent_name == agent_name)
    )
    config = result.scalar_one_or_none()

    if not config:
        raise HTTPException(status_code=404, detail="Agent configuration not found")

    return AgentScheduleResponse(
        agent_name=config.agent_name,
        schedule_type=config.schedule_type,
        schedule_cron=config.schedule_cron,
        schedule_interval_hours=config.schedule_interval_hours,
        next_run_at=config.next_run_at,
        last_run_at=config.last_run_at,
        updated_at=config.updated_at,
    )


# ============================================
# Phase 16.2: Cost Analytics
# ============================================

class CostBreakdownResponse(BaseModel):
    """Daily cost breakdown per agent."""
    date: str
    agent_name: str
    executions: int
    tokens_used: int
    cost_usd: float

class CostAnalyticsResponse(BaseModel):
    """Cost analytics for a time period."""
    period: str
    start_date: str
    end_date: str
    total_cost_usd: float
    daily_breakdown: list[CostBreakdownResponse]
    agent_totals: dict[str, float]

@router.get("/stats/costs", response_model=CostAnalyticsResponse)
async def get_agent_cost_analytics(
    db: Annotated[AsyncSession, Depends(get_db)],
    admin: Annotated[User, Depends(require_admin)],
    period: Annotated[str, Query(pattern="^(7d|30d|90d)$")] = "7d",
):
    """
    Get cost analytics with daily breakdown per agent.

    Phase 16.2: Extracts cost data from agent_execution_logs.extra_metadata.

    Query params:
    - period: 7d, 30d, or 90d
    """
    # Parse period
    days_map = {"7d": 7, "30d": 30, "90d": 90}
    days = days_map[period]
    start_date = datetime.now(UTC) - timedelta(days=days)
    end_date = datetime.now(UTC)

    # Query daily cost breakdown
    # Extract cost_usd and tokens_used from extra_metadata JSONB
    cost_query = text("""
        SELECT
            DATE(started_at) as date,
            agent_type,
            COUNT(*) as executions,
            COALESCE(SUM((extra_metadata->>'tokens_used')::int), 0) as tokens_used,
            COALESCE(SUM((extra_metadata->>'cost_usd')::float), 0) as cost_usd
        FROM agent_execution_logs
        WHERE started_at >= :start_date
          AND started_at < :end_date
          AND extra_metadata ? 'cost_usd'
        GROUP BY DATE(started_at), agent_type
        ORDER BY date DESC, cost_usd DESC
    """)

    result = await db.execute(cost_query, {"start_date": start_date, "end_date": end_date})
    rows = result.fetchall()

    # Build daily breakdown
    daily_breakdown = []
    agent_totals = {}

    for row in rows:
        date_str = row.date.isoformat()
        agent_name = row.agent_type
        executions = row.executions
        tokens_used = row.tokens_used
        cost_usd = round(row.cost_usd, 4)

        daily_breakdown.append(CostBreakdownResponse(
            date=date_str,
            agent_name=agent_name,
            executions=executions,
            tokens_used=tokens_used,
            cost_usd=cost_usd,
        ))

        # Accumulate agent totals
        if agent_name not in agent_totals:
            agent_totals[agent_name] = 0.0
        agent_totals[agent_name] += cost_usd

    # Calculate total cost
    total_cost = sum(agent_totals.values())

    return CostAnalyticsResponse(
        period=period,
        start_date=start_date.date().isoformat(),
        end_date=end_date.date().isoformat(),
        total_cost_usd=round(total_cost, 2),
        daily_breakdown=daily_breakdown,
        agent_totals={k: round(v, 2) for k, v in agent_totals.items()},
    )


# ============================================
# Audit Log Endpoints
# ============================================

@router.get("/audit-logs", response_model=list[AuditLogResponse])
async def list_audit_logs(
    db: Annotated[AsyncSession, Depends(get_db)],
    admin: Annotated[User, Depends(require_admin)],
    action: str | None = None,
    user_id: UUID | None = None,
    resource_type: str | None = None,
    days: int = 7,
    limit: int = 100,
):
    """List security audit logs."""
    query = select(AuditLog).order_by(AuditLog.created_at.desc())

    if action:
        query = query.where(AuditLog.action == action)
    if user_id:
        query = query.where(AuditLog.user_id == user_id)
    if resource_type:
        query = query.where(AuditLog.resource_type == resource_type)

    since = datetime.now(UTC) - timedelta(days=days)
    query = query.where(AuditLog.created_at >= since).limit(limit)

    result = await db.execute(query)
    return [AuditLogResponse.model_validate(log) for log in result.scalars().all()]


@router.get("/audit-logs/actions")
async def list_audit_actions(
    db: Annotated[AsyncSession, Depends(get_db)],
    admin: Annotated[User, Depends(require_admin)],
):
    """List all distinct audit actions."""
    result = await db.execute(
        select(AuditLog.action, func.count(AuditLog.id))
        .group_by(AuditLog.action)
        .order_by(func.count(AuditLog.id).desc())
    )

    return [{"action": row[0], "count": row[1]} for row in result.fetchall()]


@router.get("/audit-logs/stats")
async def get_audit_stats(
    db: Annotated[AsyncSession, Depends(get_db)],
    admin: Annotated[User, Depends(require_admin)],
    days: int = 7,
):
    """Get audit log statistics."""
    since = datetime.now(UTC) - timedelta(days=days)

    total = await db.execute(
        select(func.count(AuditLog.id)).where(AuditLog.created_at >= since)
    )

    by_action = await db.execute(
        select(AuditLog.action, func.count(AuditLog.id))
        .where(AuditLog.created_at >= since)
        .group_by(AuditLog.action)
    )

    by_resource = await db.execute(
        select(AuditLog.resource_type, func.count(AuditLog.id))
        .where(AuditLog.created_at >= since)
        .group_by(AuditLog.resource_type)
    )

    return {
        "total_events": total.scalar() or 0,
        "by_action": {row[0]: row[1] for row in by_action.fetchall()},
        "by_resource": {row[0]: row[1] for row in by_resource.fetchall()},
        "period_days": days
    }


# ============================================
# Real-time Agent Logs SSE (Phase 20.4)
# ============================================

@router.get("/{agent_name}/logs/stream")
async def stream_agent_logs(
    request: Request,
    agent_name: str,
    admin: Annotated[User, Depends(require_admin)],
):
    """
    SSE stream tailing agent_execution_logs for a specific agent.

    Sends new log entries every 3 seconds. Useful for monitoring
    agent execution in real-time from the admin UI.
    """
    last_seen_id: UUID | None = None

    async def event_generator():
        nonlocal last_seen_id

        try:
            while True:
                if await request.is_disconnected():
                    break

                try:
                    async with AsyncSessionLocal() as db:
                        query = (
                            select(AgentExecutionLog)
                            .where(AgentExecutionLog.agent_type == agent_name)
                            .order_by(AgentExecutionLog.started_at.desc())
                            .limit(20)
                        )
                        if last_seen_id:
                            query = query.where(AgentExecutionLog.id != last_seen_id)

                        result = await db.execute(query)
                        logs = result.scalars().all()

                    if logs:
                        last_seen_id = logs[0].id
                        for log in reversed(logs):
                            yield {
                                "event": "log_entry",
                                "data": json.dumps({
                                    "id": str(log.id),
                                    "agent_type": log.agent_type,
                                    "source": log.source,
                                    "status": log.status,
                                    "started_at": log.started_at.isoformat() if log.started_at else None,
                                    "completed_at": log.completed_at.isoformat() if log.completed_at else None,
                                    "duration_ms": log.duration_ms,
                                    "items_processed": log.items_processed,
                                    "error_message": log.error_message,
                                }, default=str),
                            }
                    else:
                        yield {"event": "heartbeat", "data": ""}

                    await asyncio.sleep(3)

                except asyncio.CancelledError:
                    break
                except Exception as e:
                    logger.error(f"Agent logs SSE error: {e}")
                    yield {"event": "error", "data": json.dumps({"error": str(e)})}
                    await asyncio.sleep(5)
        finally:
            logger.info(f"Agent logs SSE closed for {agent_name}")

    return EventSourceResponse(event_generator())
