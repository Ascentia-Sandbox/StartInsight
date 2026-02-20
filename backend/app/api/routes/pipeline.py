"""Pipeline Monitoring API routes - Phase 8.2: Data Pipeline Command Center.

Provides admin endpoints for:
- Pipeline status and health monitoring
- API quota tracking
- Alert configuration and incident management
"""

import logging
from datetime import UTC, datetime, timedelta
from typing import Annotated, Any
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db, require_admin
from app.models.pipeline_monitoring import (
    AdminAlert,
    AdminAlertIncident,
    APIQuotaUsage,
    PipelineHealthCheck,
)
from app.models.user import User

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/admin/pipeline", tags=["Pipeline Monitoring"])

VALID_SCRAPERS = ["reddit", "product_hunt", "hacker_news", "twitter", "google_trends"]


# ============================================
# Schemas
# ============================================

class ScraperStatus(BaseModel):
    name: str
    status: str
    last_check: datetime | None
    response_time_ms: int | None
    items_fetched: int | None
    success_rate_24h: float

class PipelineStatusResponse(BaseModel):
    scrapers: list[ScraperStatus]
    processing_queue: dict[str, int]
    api_quotas: dict[str, dict[str, Any]]

class HealthCheckResponse(BaseModel):
    id: UUID
    scraper_name: str
    status: str
    response_time_ms: int | None
    items_fetched: int | None
    error_message: str | None
    checked_at: datetime

    model_config = ConfigDict(from_attributes=True)

class QuotaUsageResponse(BaseModel):
    id: UUID
    api_name: str
    metric_name: str
    value: float
    period_start: datetime
    period_end: datetime

    model_config = ConfigDict(from_attributes=True)

class AlertCreate(BaseModel):
    alert_name: str = Field(..., max_length=100)
    alert_type: str = Field(..., pattern="^(threshold|anomaly|failure)$")
    metric_name: str = Field(..., max_length=100)
    condition: dict[str, Any]
    severity: str = Field(default="warning", pattern="^(info|warning|critical)$")
    notification_channels: list[str] | None = None

class AlertResponse(BaseModel):
    id: UUID
    alert_name: str
    alert_type: str
    metric_name: str
    condition: dict[str, Any]
    severity: str
    notification_channels: list[str] | None
    is_active: bool
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)

class IncidentResponse(BaseModel):
    id: UUID
    alert_id: UUID
    triggered_value: float | None
    status: str
    created_at: datetime
    resolved_at: datetime | None

    model_config = ConfigDict(from_attributes=True)

class IncidentAction(BaseModel):
    action: str = Field(..., pattern="^(acknowledge|resolve)$")


# ============================================
# Pipeline Status Endpoints
# ============================================

@router.get("/status", response_model=PipelineStatusResponse)
async def get_pipeline_status(
    db: Annotated[AsyncSession, Depends(get_db)],
    admin: Annotated[User, Depends(require_admin)],
):
    """Get real-time pipeline status including all scrapers and quotas."""
    scrapers = ["reddit", "product_hunt", "hacker_news", "twitter", "google_trends"]
    scraper_statuses = []

    for scraper in scrapers:
        # Get latest health check
        result = await db.execute(
            select(PipelineHealthCheck)
            .where(PipelineHealthCheck.scraper_name == scraper)
            .order_by(PipelineHealthCheck.checked_at.desc())
            .limit(1)
        )
        latest = result.scalar_one_or_none()

        # Calculate 24h success rate
        day_ago = datetime.now(UTC) - timedelta(hours=24)
        success_count = await db.execute(
            select(func.count()).where(
                PipelineHealthCheck.scraper_name == scraper,
                PipelineHealthCheck.checked_at >= day_ago,
                PipelineHealthCheck.status == "healthy"
            )
        )
        total_count = await db.execute(
            select(func.count()).where(
                PipelineHealthCheck.scraper_name == scraper,
                PipelineHealthCheck.checked_at >= day_ago
            )
        )
        success = success_count.scalar() or 0
        total = total_count.scalar() or 1
        success_rate = success / total if total > 0 else 0.0

        scraper_statuses.append(ScraperStatus(
            name=scraper,
            status=latest.status if latest else "unknown",
            last_check=latest.checked_at if latest else None,
            response_time_ms=latest.response_time_ms if latest else None,
            items_fetched=latest.items_fetched if latest else None,
            success_rate_24h=round(success_rate, 2)
        ))

    # Get processing queue stats (from raw_signals)
    from app.models.raw_signal import RawSignal
    pending = await db.execute(select(func.count()).where(RawSignal.processed == False))
    processed = await db.execute(select(func.count()).where(RawSignal.processed == True))

    # Get API quotas
    quotas = {}
    for api in ["anthropic", "firecrawl", "reddit"]:
        result = await db.execute(
            select(APIQuotaUsage)
            .where(APIQuotaUsage.api_name == api)
            .order_by(APIQuotaUsage.recorded_at.desc())
            .limit(1)
        )
        usage = result.scalar_one_or_none()
        if usage:
            quotas[api] = {"used": float(usage.value), "metric": usage.metric_name}

    return PipelineStatusResponse(
        scrapers=scraper_statuses,
        processing_queue={"pending": pending.scalar() or 0, "processed": processed.scalar() or 0},
        api_quotas=quotas
    )


@router.get("/health-history", response_model=list[HealthCheckResponse])
async def get_health_history(
    db: Annotated[AsyncSession, Depends(get_db)],
    admin: Annotated[User, Depends(require_admin)],
    scraper: str | None = None,
    hours: int = 24,
    limit: int = 100,
):
    """Get historical health check data."""
    query = select(PipelineHealthCheck).order_by(PipelineHealthCheck.checked_at.desc())

    if scraper:
        query = query.where(PipelineHealthCheck.scraper_name == scraper)

    since = datetime.now(UTC) - timedelta(hours=hours)
    query = query.where(PipelineHealthCheck.checked_at >= since).limit(limit)

    result = await db.execute(query)
    return [HealthCheckResponse.model_validate(h) for h in result.scalars().all()]


@router.post("/scrapers/{name}/trigger")
async def trigger_scraper(
    name: str,
    db: Annotated[AsyncSession, Depends(get_db)],
    admin: Annotated[User, Depends(require_admin)],
):
    """Manually trigger a scraper run."""
    if name not in VALID_SCRAPERS:
        raise HTTPException(status_code=400, detail=f"Invalid scraper: {name}")

    # Enqueue scraper task via Arq
    scraper_task_map = {
        "reddit": "scrape_reddit_task",
        "product_hunt": "scrape_product_hunt_task",
        "hacker_news": "scrape_hackernews_task",
        "twitter": "scrape_twitter_task",
        "google_trends": "scrape_trends_task",
    }
    task_name = scraper_task_map.get(name)
    if task_name:
        try:
            from arq.connections import ArqRedis, create_pool
            from arq.connections import RedisSettings as ArqRedisSettings

            from app.core.config import settings

            pool: ArqRedis = await create_pool(ArqRedisSettings(
                host=settings.redis_host,
                port=settings.redis_port,
            ))
            job = await pool.enqueue_job(task_name)
            await pool.aclose()
            logger.info(f"Enqueued scraper task '{task_name}' (job_id={job.job_id}) by admin {admin.id}")
        except Exception as e:
            logger.warning(f"Failed to enqueue scraper task for {name}: {e}")

    return {"status": "queued", "scraper": name, "triggered_by": str(admin.id)}


@router.post("/scrapers/{name}/pause")
async def pause_scraper(
    name: str,
    db: Annotated[AsyncSession, Depends(get_db)],
    admin: Annotated[User, Depends(require_admin)],
):
    """Pause a scraper by setting a Redis flag."""
    if name not in VALID_SCRAPERS:
        raise HTTPException(status_code=400, detail=f"Invalid scraper: {name}")

    try:
        import redis.asyncio as aioredis

        from app.core.config import settings

        r = aioredis.from_url(settings.redis_url)
        await r.set(f"scraper:paused:{name}", "1")
        await r.aclose()
        logger.info(f"Scraper {name} paused by admin {admin.id}")
    except Exception as e:
        logger.warning(f"Failed to set pause flag for {name}: {e}")

    return {"status": "paused", "scraper": name}


@router.post("/scrapers/{name}/resume")
async def resume_scraper(
    name: str,
    db: Annotated[AsyncSession, Depends(get_db)],
    admin: Annotated[User, Depends(require_admin)],
):
    """Resume a paused scraper by removing the Redis flag."""
    if name not in VALID_SCRAPERS:
        raise HTTPException(status_code=400, detail=f"Invalid scraper: {name}")

    try:
        import redis.asyncio as aioredis

        from app.core.config import settings

        r = aioredis.from_url(settings.redis_url)
        await r.delete(f"scraper:paused:{name}")
        await r.aclose()
        logger.info(f"Scraper {name} resumed by admin {admin.id}")
    except Exception as e:
        logger.warning(f"Failed to remove pause flag for {name}: {e}")

    return {"status": "resumed", "scraper": name}


@router.get("/quotas", response_model=list[QuotaUsageResponse])
async def get_quota_usage(
    db: Annotated[AsyncSession, Depends(get_db)],
    admin: Annotated[User, Depends(require_admin)],
    api_name: str | None = None,
    days: int = 7,
):
    """Get API quota usage history."""
    query = select(APIQuotaUsage).order_by(APIQuotaUsage.recorded_at.desc())

    if api_name:
        query = query.where(APIQuotaUsage.api_name == api_name)

    since = datetime.now(UTC) - timedelta(days=days)
    query = query.where(APIQuotaUsage.recorded_at >= since).limit(100)

    result = await db.execute(query)
    return [QuotaUsageResponse.model_validate(q) for q in result.scalars().all()]


# ============================================
# Alert Management Endpoints
# ============================================

@router.get("/alerts", response_model=list[AlertResponse])
async def list_alerts(
    db: Annotated[AsyncSession, Depends(get_db)],
    admin: Annotated[User, Depends(require_admin)],
    active_only: bool = True,
):
    """List all configured alerts."""
    query = select(AdminAlert).order_by(AdminAlert.created_at.desc())
    if active_only:
        query = query.where(AdminAlert.is_active == True)

    result = await db.execute(query)
    return [AlertResponse.model_validate(a) for a in result.scalars().all()]


@router.post("/alerts", response_model=AlertResponse)
async def create_alert(
    alert: AlertCreate,
    db: Annotated[AsyncSession, Depends(get_db)],
    admin: Annotated[User, Depends(require_admin)],
):
    """Create a new alert configuration."""
    new_alert = AdminAlert(
        alert_name=alert.alert_name,
        alert_type=alert.alert_type,
        metric_name=alert.metric_name,
        condition=alert.condition,
        severity=alert.severity,
        notification_channels=alert.notification_channels,
        created_by=admin.id,
    )
    db.add(new_alert)
    await db.commit()
    await db.refresh(new_alert)

    logger.info(f"Alert '{alert.alert_name}' created by admin {admin.id}")
    return AlertResponse.model_validate(new_alert)


@router.patch("/alerts/{alert_id}")
async def update_alert(
    alert_id: UUID,
    updates: dict[str, Any],
    db: Annotated[AsyncSession, Depends(get_db)],
    admin: Annotated[User, Depends(require_admin)],
):
    """Update an alert configuration."""
    result = await db.execute(select(AdminAlert).where(AdminAlert.id == alert_id))
    alert = result.scalar_one_or_none()

    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found")

    allowed_fields = {"alert_name", "condition", "severity", "notification_channels", "is_active"}
    for key, value in updates.items():
        if key in allowed_fields:
            setattr(alert, key, value)

    await db.commit()
    await db.refresh(alert)

    return AlertResponse.model_validate(alert)


@router.delete("/alerts/{alert_id}")
async def delete_alert(
    alert_id: UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
    admin: Annotated[User, Depends(require_admin)],
):
    """Delete an alert configuration."""
    result = await db.execute(select(AdminAlert).where(AdminAlert.id == alert_id))
    alert = result.scalar_one_or_none()

    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found")

    await db.delete(alert)
    await db.commit()

    return {"status": "deleted", "alert_id": str(alert_id)}


# ============================================
# Incident Management Endpoints
# ============================================

@router.get("/incidents", response_model=list[IncidentResponse])
async def list_incidents(
    db: Annotated[AsyncSession, Depends(get_db)],
    admin: Annotated[User, Depends(require_admin)],
    status_filter: Annotated[str | None, Query(alias="status")] = None,
    limit: int = 50,
):
    """List alert incidents."""
    query = select(AdminAlertIncident).order_by(AdminAlertIncident.created_at.desc())

    if status_filter:
        query = query.where(AdminAlertIncident.status == status_filter)

    query = query.limit(limit)
    result = await db.execute(query)
    return [IncidentResponse.model_validate(i) for i in result.scalars().all()]


@router.patch("/incidents/{incident_id}")
async def update_incident(
    incident_id: UUID,
    action: IncidentAction,
    db: Annotated[AsyncSession, Depends(get_db)],
    admin: Annotated[User, Depends(require_admin)],
):
    """Acknowledge or resolve an incident."""
    result = await db.execute(select(AdminAlertIncident).where(AdminAlertIncident.id == incident_id))
    incident = result.scalar_one_or_none()

    if not incident:
        raise HTTPException(status_code=404, detail="Incident not found")

    if action.action == "acknowledge":
        incident.status = "acknowledged"
        incident.acknowledged_by = admin.id
    elif action.action == "resolve":
        incident.status = "resolved"
        incident.resolved_at = datetime.now(UTC)

    await db.commit()
    await db.refresh(incident)

    logger.info(f"Incident {incident_id} {action.action}d by admin {admin.id}")
    return IncidentResponse.model_validate(incident)
