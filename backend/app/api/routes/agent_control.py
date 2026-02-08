"""Agent Control API routes - Phase 8.4-8.5: AI Agent Control & Security.

Provides admin endpoints for:
- AI agent configuration and management
- Security audit logs
"""

import logging
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from typing import Annotated, Any
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from pydantic import BaseModel, Field
from sqlalchemy import func, select, text, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import require_admin, get_db
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
