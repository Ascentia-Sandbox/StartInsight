"""Redis caching module for API performance optimization.

Sprint 2.1: Provides simple caching for frequently accessed data:
- Tools directory (cached for 1 hour)
- Trends list (cached for 15 minutes)
- Insights list (cached for 5 minutes)
- Success stories (cached for 1 hour)
- Market insights (cached for 30 minutes)

Phase 6.1B: Stale-on-error cache fallback (dual-key pattern)
Phase 6.1C: Negative caching (sentinel value to prevent thundering herd)
Phase 6.3A: L1 in-memory TTL cache layer (cachetools)

Uses JSON serialization for simple data structures.
"""

import json
import logging
from collections.abc import Callable
from datetime import date, datetime
from decimal import Decimal
from functools import wraps
from typing import Any, TypeVar
from uuid import UUID

import redis.asyncio as redis
from cachetools import TTLCache
from pydantic import BaseModel

from app.core.config import settings

logger = logging.getLogger(__name__)

T = TypeVar("T")

# Phase 6.1C: Sentinel value for negative caching
_NEGATIVE_SENTINEL = "__NEG__"

# Phase 6.3A: L1 in-memory cache (process-local, avoids Redis round-trip for hot keys)
_l1_cache: TTLCache = TTLCache(maxsize=256, ttl=30)


class _Encoder(json.JSONEncoder):
    """Custom JSON encoder that handles types common in SQLAlchemy responses."""

    def default(self, obj: Any) -> Any:
        if isinstance(obj, UUID):
            return str(obj)
        if isinstance(obj, (datetime, date)):
            return obj.isoformat()
        if isinstance(obj, Decimal):
            return float(obj)
        return super().default(obj)


# Cache TTL configuration (in seconds)
CACHE_TTL = {
    "tools": 3600,  # 1 hour
    "tools_featured": 3600,  # 1 hour
    "trends": 900,  # 15 minutes
    "trends_featured": 900,  # 15 minutes
    "insights": 300,  # 5 minutes
    "insights_list": 300,  # 5 minutes
    "success_stories": 3600,  # 1 hour
    "market_insights": 1800,  # 30 minutes
    "idea_of_day": 3600,  # 1 hour (changes daily anyway)
    "default": 300,  # 5 minutes default
}

# Global Redis connection pool
_redis_pool: redis.Redis | None = None


async def get_redis() -> redis.Redis:
    """Get or create Redis connection pool."""
    global _redis_pool

    if _redis_pool is None:
        kwargs = {
            "encoding": "utf-8",
            "decode_responses": True,
            "socket_connect_timeout": settings.redis_socket_connect_timeout,
            "socket_timeout": settings.redis_socket_timeout,
        }
        if settings.redis_ssl:
            kwargs["ssl"] = True
        _redis_pool = redis.from_url(settings.redis_url, **kwargs)

    return _redis_pool


async def close_redis():
    """Close Redis connection pool."""
    global _redis_pool

    if _redis_pool:
        await _redis_pool.close()
        _redis_pool = None


def _serialize(data: Any) -> str:
    """Serialize data to JSON string."""
    if isinstance(data, BaseModel):
        return data.model_dump_json()
    if isinstance(data, list) and data and isinstance(data[0], BaseModel):
        return json.dumps([item.model_dump() for item in data], cls=_Encoder)
    return json.dumps(data, cls=_Encoder)


def _deserialize(data: str) -> Any:
    """Deserialize JSON string to data."""
    return json.loads(data)


async def cache_get(key: str) -> Any | None:
    """
    Get cached value by key. Checks L1 in-memory cache first, then Redis.

    Args:
        key: Cache key

    Returns:
        Cached value or None if not found/expired
    """
    # Phase 6.3A: L1 in-memory check
    l1_value = _l1_cache.get(key)
    if l1_value is not None:
        logger.debug(f"Cache L1 HIT: {key}")
        return l1_value

    try:
        r = await get_redis()
        value = await r.get(f"cache:{key}")
        if value:
            deserialized = _deserialize(value)
            # Promote to L1
            _l1_cache[key] = deserialized
            logger.debug(f"Cache HIT: {key}")
            return deserialized
        logger.debug(f"Cache MISS: {key}")
        return None
    except Exception as e:
        logger.warning(f"Cache get error for {key}: {e}")
        return None


async def cache_set(key: str, value: Any, ttl: int | None = None) -> bool:
    """
    Set cached value with optional TTL. Also updates L1 in-memory cache.

    Args:
        key: Cache key
        value: Value to cache (will be JSON serialized)
        ttl: Time to live in seconds (uses default if not specified)

    Returns:
        True if successful, False otherwise
    """
    try:
        r = await get_redis()
        ttl = ttl or CACHE_TTL.get("default", 300)
        serialized = _serialize(value)
        await r.setex(f"cache:{key}", ttl, serialized)
        # Phase 6.3A: Update L1
        _l1_cache[key] = value
        logger.debug(f"Cache SET: {key} (TTL: {ttl}s)")
        return True
    except Exception as e:
        logger.warning(f"Cache set error for {key}: {e}")
        return False


async def cache_set_with_stale(key: str, value: Any, ttl: int | None = None) -> bool:
    """
    Phase 6.1B: Set cached value with a stale backup copy.

    Writes two Redis keys:
    - cache:{key} with normal TTL
    - cache:stale:{key} with 10× TTL (fallback for stale-on-error)

    Args:
        key: Cache key
        value: Value to cache
        ttl: Time to live in seconds (default from CACHE_TTL)
    """
    try:
        r = await get_redis()
        ttl = ttl or CACHE_TTL.get("default", 300)
        serialized = _serialize(value)
        stale_ttl = ttl * 10  # Stale copy lives 10× longer
        pipe = r.pipeline()
        pipe.setex(f"cache:{key}", ttl, serialized)
        pipe.setex(f"cache:stale:{key}", stale_ttl, serialized)
        await pipe.execute()
        # Update L1
        _l1_cache[key] = value
        logger.debug(f"Cache SET+STALE: {key} (TTL: {ttl}s, stale: {stale_ttl}s)")
        return True
    except Exception as e:
        logger.warning(f"Cache set_with_stale error for {key}: {e}")
        return False


async def cache_get_with_fallback(key: str) -> Any | None:
    """
    Phase 6.1B + 6.1C: Get cached value with stale fallback and negative cache check.

    Lookup order:
    1. L1 in-memory cache
    2. Redis cache:{key} (fresh)
    3. Redis cache:stale:{key} (stale fallback)

    Returns None if negative sentinel is found (6.1C) — prevents thundering herd.
    """
    # L1 check
    l1_value = _l1_cache.get(key)
    if l1_value is not None:
        if l1_value == _NEGATIVE_SENTINEL:
            logger.debug(f"Cache L1 NEG HIT: {key}")
            return None
        return l1_value

    try:
        r = await get_redis()

        # Check fresh key
        value = await r.get(f"cache:{key}")
        if value:
            # Check for negative sentinel
            if value == _NEGATIVE_SENTINEL:
                _l1_cache[key] = _NEGATIVE_SENTINEL
                logger.debug(f"Cache NEG HIT: {key}")
                return None
            deserialized = _deserialize(value)
            _l1_cache[key] = deserialized
            return deserialized

        # Fresh miss — try stale fallback
        stale_value = await r.get(f"cache:stale:{key}")
        if stale_value:
            deserialized = _deserialize(stale_value)
            _l1_cache[key] = deserialized
            logger.info(f"Cache STALE FALLBACK: {key}")
            return deserialized

        return None
    except Exception as e:
        logger.warning(f"Cache get_with_fallback error for {key}: {e}")
        # Last resort: check L1 (may have stale data from previous fetch)
        return _l1_cache.get(key)


async def cache_negative(key: str, ttl: int = 60) -> bool:
    """
    Phase 6.1C: Cache a negative result to prevent thundering herd.

    Stores a sentinel value for `ttl` seconds so repeated lookups for a
    known-failed key don't hit the database or upstream API.

    Args:
        key: Cache key
        ttl: How long to suppress retries (default 60s)
    """
    try:
        r = await get_redis()
        await r.setex(f"cache:{key}", ttl, _NEGATIVE_SENTINEL)
        _l1_cache[key] = _NEGATIVE_SENTINEL
        logger.debug(f"Cache NEG SET: {key} (TTL: {ttl}s)")
        return True
    except Exception as e:
        logger.warning(f"Cache negative set error for {key}: {e}")
        return False


async def cache_delete(key: str) -> bool:
    """
    Delete cached value.

    Args:
        key: Cache key

    Returns:
        True if deleted, False otherwise
    """
    try:
        r = await get_redis()
        await r.delete(f"cache:{key}")
        logger.debug(f"Cache DELETE: {key}")
        return True
    except Exception as e:
        logger.warning(f"Cache delete error for {key}: {e}")
        return False


async def cache_delete_pattern(pattern: str) -> int:
    """
    Delete all keys matching pattern.

    Args:
        pattern: Glob pattern (e.g., "insights:*")

    Returns:
        Number of keys deleted
    """
    try:
        r = await get_redis()
        keys = []
        async for key in r.scan_iter(f"cache:{pattern}"):
            keys.append(key)
        if keys:
            await r.delete(*keys)
            logger.info(f"Cache DELETE pattern {pattern}: {len(keys)} keys")
            return len(keys)
        return 0
    except Exception as e:
        logger.warning(f"Cache delete pattern error for {pattern}: {e}")
        return 0


# Decorator for caching function results
def cached(cache_key: str, ttl_key: str | None = None, ttl: int | None = None):
    """
    Decorator to cache function results.

    Usage:
        @cached("tools:list")
        async def get_tools():
            ...

        @cached("insights:list:{page}:{limit}", ttl=300)
        async def get_insights(page: int, limit: int):
            ...

    Args:
        cache_key: Cache key template (can include {param} placeholders)
        ttl_key: Key for CACHE_TTL lookup (e.g., "tools", "insights")
        ttl: Explicit TTL in seconds (overrides ttl_key)
    """

    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @wraps(func)
        async def wrapper(*args, **kwargs) -> T:
            # Build cache key from template and arguments
            try:
                key = cache_key.format(**kwargs)
            except KeyError:
                key = cache_key

            # Try to get from cache
            cached_value = await cache_get(key)
            if cached_value is not None:
                return cached_value

            # Execute function and cache result
            result = await func(*args, **kwargs)

            # Determine TTL
            cache_ttl = ttl or CACHE_TTL.get(ttl_key or "default", 300)

            # Cache the result
            await cache_set(key, result, cache_ttl)

            return result

        return wrapper

    return decorator


# Cache invalidation helpers
async def invalidate_tools_cache():
    """Invalidate all tools cache."""
    await cache_delete_pattern("tools:*")


async def invalidate_trends_cache():
    """Invalidate all trends cache."""
    await cache_delete_pattern("trends:*")


async def invalidate_insights_cache():
    """Invalidate all insights cache."""
    await cache_delete_pattern("insights:*")


async def invalidate_success_stories_cache():
    """Invalidate all success stories cache."""
    await cache_delete_pattern("success_stories:*")


async def invalidate_market_insights_cache():
    """Invalidate all market insights cache."""
    await cache_delete_pattern("market_insights:*")


async def invalidate_all_cache():
    """Invalidate entire cache (use sparingly)."""
    await cache_delete_pattern("*")


# Health check
async def cache_health_check() -> dict:
    """
    Check Redis cache health.

    Returns:
        Dict with status and latency
    """
    import time

    try:
        r = await get_redis()
        start = time.time()
        await r.ping()
        latency = (time.time() - start) * 1000  # ms

        # Get memory info
        info = await r.info("memory")
        used_memory = info.get("used_memory_human", "unknown")

        return {
            "status": "healthy",
            "latency_ms": round(latency, 2),
            "used_memory": used_memory,
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "error": str(e),
        }


# Phase 6.3B: Bootstrap cache hydration
async def hydrate_cache() -> dict:
    """Pre-warm Redis cache with most-accessed data on worker startup.

    Hydrates: insights page 1, pulse stats, idea of the day.
    Prevents cold-cache misses after Railway deploys (~4x/day).

    Returns:
        Dict with hydration results per key.
    """
    from sqlalchemy import desc, func, select

    from app.db.session import AsyncSessionLocal
    from app.models.insight import Insight

    results = {}
    try:
        async with AsyncSessionLocal() as session:
            # 1. Insights page 1 (most common API call)
            stmt = (
                select(Insight)
                .where(Insight.admin_status == "approved")
                .order_by(desc(Insight.relevance_score))
                .limit(20)
            )
            result = await session.execute(stmt)
            insights = result.scalars().all()
            if insights:
                # Serialize minimal data for cache
                insights_data = [
                    {
                        "id": str(i.id),
                        "title": i.title,
                        "relevance_score": i.relevance_score,
                    }
                    for i in insights
                ]
                await cache_set_with_stale(
                    "insights:list:1:20", insights_data, CACHE_TTL.get("insights", 300)
                )
                results["insights_page_1"] = len(insights_data)

            # 2. Total insights count (used by pulse/stats)
            count_result = await session.execute(select(func.count(Insight.id)))
            total = count_result.scalar() or 0
            await cache_set_with_stale(
                "insights:total_count", total, CACHE_TTL.get("insights", 300)
            )
            results["insights_total"] = total

        logger.info(f"Bootstrap cache hydration complete: {results}")
    except Exception as e:
        logger.warning(f"Bootstrap cache hydration failed: {e}")
        results["error"] = str(e)

    return results
