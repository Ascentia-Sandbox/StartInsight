"""Redis caching module for API performance optimization.

Sprint 2.1: Provides simple caching for frequently accessed data:
- Tools directory (cached for 1 hour)
- Trends list (cached for 15 minutes)
- Insights list (cached for 5 minutes)
- Success stories (cached for 1 hour)
- Market insights (cached for 30 minutes)

Uses JSON serialization for simple data structures.
"""

import json
import logging
from collections.abc import Callable
from functools import wraps
from typing import Any, TypeVar

import redis.asyncio as redis
from pydantic import BaseModel

from app.core.config import settings

logger = logging.getLogger(__name__)

T = TypeVar("T")

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
    elif isinstance(data, list):
        # Handle list of Pydantic models
        if data and isinstance(data[0], BaseModel):
            return json.dumps([item.model_dump() for item in data])
        return json.dumps(data)
    elif isinstance(data, dict):
        return json.dumps(data)
    else:
        return json.dumps(data)


def _deserialize(data: str) -> Any:
    """Deserialize JSON string to data."""
    return json.loads(data)


async def cache_get(key: str) -> Any | None:
    """
    Get cached value by key.

    Args:
        key: Cache key

    Returns:
        Cached value or None if not found/expired
    """
    try:
        r = await get_redis()
        value = await r.get(f"cache:{key}")
        if value:
            logger.debug(f"Cache HIT: {key}")
            return _deserialize(value)
        logger.debug(f"Cache MISS: {key}")
        return None
    except Exception as e:
        logger.warning(f"Cache get error for {key}: {e}")
        return None


async def cache_set(key: str, value: Any, ttl: int | None = None) -> bool:
    """
    Set cached value with optional TTL.

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
        logger.debug(f"Cache SET: {key} (TTL: {ttl}s)")
        return True
    except Exception as e:
        logger.warning(f"Cache set error for {key}: {e}")
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
