"""Health check endpoints for production monitoring.

Phase 6.2A: Source health dashboard endpoint.
"""

import logging
from datetime import UTC, datetime, timedelta

from fastapi import APIRouter, Depends, status
from fastapi.responses import JSONResponse
from sqlalchemy import func, select, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.cache import get_redis
from app.db.session import get_db
from app.models.raw_signal import RawSignal

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("/health")
async def health_check():
    """
    Basic health check - returns 200 if app is running.
    Used by load balancer for routing decisions.
    """
    return {"status": "healthy", "service": "startinsight-api"}


@router.get("/health/ready")
async def readiness_check(db: AsyncSession = Depends(get_db)):
    """
    Readiness check - verifies database AND Redis connectivity.
    Used by Railway/Kubernetes for pod readiness.

    Returns 503 if any dependency is unhealthy.
    """
    checks = {"database": "unknown", "redis": "unknown"}

    # Check database
    try:
        result = await db.execute(text("SELECT 1"))
        checks["database"] = "healthy" if result else "unhealthy"
    except Exception as e:
        logger.error(f"Database health check failed: {e}")
        checks["database"] = f"unhealthy: {type(e).__name__}"

    # Check Redis
    try:
        redis_client = await get_redis()
        await redis_client.ping()
        checks["redis"] = "healthy"
    except Exception as e:
        logger.error(f"Redis health check failed: {e}")
        checks["redis"] = f"unhealthy: {type(e).__name__}"

    # Determine overall status
    all_healthy = all(status == "healthy" for status in checks.values())

    response_status = status.HTTP_200_OK if all_healthy else status.HTTP_503_SERVICE_UNAVAILABLE

    return JSONResponse(
        status_code=response_status,
        content={"status": "ready" if all_healthy else "not_ready", "checks": checks},
    )


@router.get("/health/live")
async def liveness_check():
    """
    Liveness check - app is alive and not in deadlock.
    Used by Railway/Kubernetes for pod restart decisions.
    """
    return {"status": "alive"}


@router.get("/health/scraping")
async def scraper_health_check(
    db: AsyncSession = Depends(get_db),
):
    """
    Scraper health check - monitor data collection pipeline.

    Returns:
        - Last run time per source
        - Signals pending processing
        - Error counts (last 24 hours)
        - Queue depth
        - Overall scraping status

    Used for production monitoring and alerting.
    """
    now = datetime.now(UTC).replace(tzinfo=None)
    twenty_four_hours_ago = now - timedelta(hours=24)

    # Check last successful run per source
    last_runs_query = await db.execute(
        select(RawSignal.source, func.max(RawSignal.created_at).label("last_run"))
        .where(RawSignal.created_at >= twenty_four_hours_ago)
        .group_by(RawSignal.source)
    )
    last_runs = {row.source: row.last_run for row in last_runs_query.all()}

    # Check pending signals (unprocessed)
    pending_count_query = await db.execute(
        select(func.count(RawSignal.id)).where(RawSignal.processed.is_(False))
    )
    pending_count = pending_count_query.scalar() or 0

    # Calculate signals collected in last 24 hours
    signals_24h_query = await db.execute(
        select(func.count(RawSignal.id)).where(RawSignal.created_at >= twenty_four_hours_ago)
    )
    signals_24h = signals_24h_query.scalar() or 0

    # Check Redis queue depth (Arq queue)
    try:
        redis_client = await get_redis()
        queue_depth = await redis_client.llen("arq:queue:default")
    except Exception as e:
        logger.warning(f"Failed to check Redis queue: {e}")
        queue_depth = None

    # Determine overall status
    # Healthy if all sources ran in last 7 hours (allowing 1 hour buffer)
    from app.core.constants import EXPECTED_SOURCES

    expected_sources = EXPECTED_SOURCES
    all_sources_recent = all(
        last_runs.get(source) and (now - last_runs[source]) < timedelta(hours=7)
        for source in expected_sources
    )

    # Calculate actual collection rate (signals/day)
    actual_rate = signals_24h  # Already daily count

    # Calculate error rate (signals with no content or failed processing)
    error_count_query = await db.execute(
        select(func.count(RawSignal.id)).where(
            RawSignal.created_at >= twenty_four_hours_ago, RawSignal.content.is_(None)
        )
    )
    error_count = error_count_query.scalar() or 0

    return {
        "status": "healthy" if all_sources_recent else "degraded",
        "last_runs": {
            source: last_run.isoformat() if last_run else None
            for source, last_run in last_runs.items()
        },
        "pending_signals": pending_count,
        "queue_depth": queue_depth,
        "signals_collected_24h": signals_24h,
        "target_rate": "360/day",
        "actual_rate": f"{actual_rate}/day",
        "errors_24h": error_count,
        "error_rate": f"{(error_count / signals_24h * 100):.1f}%" if signals_24h > 0 else "0%",
        "checked_at": now.isoformat(),
    }


@router.get("/health/sources")
async def source_health_check(db: AsyncSession = Depends(get_db)):
    """
    Phase 6.2A: Source health dashboard.

    Returns real-time health status for all data sources from the source_health table.
    No auth required — used by monitoring dashboards.
    """
    try:
        result = await db.execute(
            text(
                "SELECT source_name, status, last_success_at, last_failure_at, "
                "last_error_message, consecutive_failures, avg_latency_ms, "
                "avg_signals_per_run, total_runs, total_failures, circuit_state, "
                "baseline_mean, baseline_variance, baseline_count, updated_at "
                "FROM source_health ORDER BY source_name"
            )
        )
        rows = result.mappings().all()

        sources = []
        for row in rows:
            sources.append(
                {
                    "name": row["source_name"],
                    "status": row["status"],
                    "last_success": row["last_success_at"].isoformat()
                    if row["last_success_at"]
                    else None,
                    "last_failure": row["last_failure_at"].isoformat()
                    if row["last_failure_at"]
                    else None,
                    "error": row["last_error_message"],
                    "consecutive_failures": row["consecutive_failures"],
                    "avg_latency_ms": round(row["avg_latency_ms"], 1),
                    "signals_per_run": round(row["avg_signals_per_run"], 1),
                    "total_runs": row["total_runs"],
                    "total_failures": row["total_failures"],
                    "circuit": row["circuit_state"],
                    "baseline": {
                        "mean": round(row["baseline_mean"], 2),
                        "variance": round(row["baseline_variance"], 2),
                        "count": row["baseline_count"],
                    },
                    "updated_at": row["updated_at"].isoformat() if row["updated_at"] else None,
                }
            )

        return {"sources": sources}

    except Exception as e:
        # Table may not exist yet (migration not applied)
        logger.debug(f"Source health query failed: {e}")
        return {"sources": [], "note": "source_health table not yet available"}
