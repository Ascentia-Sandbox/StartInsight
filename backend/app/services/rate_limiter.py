"""Rate Limiter Service - Phase 6.3.

Provides tier-based rate limiting using Redis with fallback to in-memory storage.
"""

import logging
import time
from collections import defaultdict
from datetime import datetime
from typing import Any

from pydantic import BaseModel

from app.core.config import settings

logger = logging.getLogger(__name__)


# ============================================================
# Rate Limit Configuration
# ============================================================


class RateLimitConfig(BaseModel):
    """Rate limit configuration for a tier."""

    requests_per_minute: int
    requests_per_hour: int
    requests_per_day: int
    api_calls_per_hour: int
    analyses_per_hour: int  # ✅ NEW: Hourly limit for AI research analyses
    analyses_per_month: int


TIER_LIMITS: dict[str, RateLimitConfig] = {
    "free": RateLimitConfig(
        requests_per_minute=20,
        requests_per_hour=200,
        requests_per_day=1000,
        api_calls_per_hour=10,
        analyses_per_hour=1,  # ✅ 1 analysis/hour (prevents spam)
        analyses_per_month=1,
    ),
    "starter": RateLimitConfig(
        requests_per_minute=60,
        requests_per_hour=1000,
        requests_per_day=10000,
        api_calls_per_hour=100,
        analyses_per_hour=2,  # ✅ 2 analyses/hour
        analyses_per_month=3,
    ),
    "pro": RateLimitConfig(
        requests_per_minute=120,
        requests_per_hour=3000,
        requests_per_day=50000,
        api_calls_per_hour=500,
        analyses_per_hour=5,  # ✅ 5 analyses/hour
        analyses_per_month=10,
    ),
    "enterprise": RateLimitConfig(
        requests_per_minute=300,
        requests_per_hour=10000,
        requests_per_day=200000,
        api_calls_per_hour=2000,
        analyses_per_hour=-1,  # ✅ Unlimited
        analyses_per_month=-1,  # Unlimited
    ),
}


# ============================================================
# In-Memory Rate Limiter (Fallback)
# ============================================================


class InMemoryRateLimiter:
    """Simple in-memory rate limiter for development/single-instance."""

    def __init__(self):
        # Structure: {key: [(timestamp, count), ...]}
        self._buckets: dict[str, list[tuple[float, int]]] = defaultdict(list)

    def check_rate_limit(
        self,
        key: str,
        limit: int,
        window_seconds: int,
    ) -> tuple[bool, int, int]:
        """
        Check if request is within rate limit.

        Args:
            key: Unique identifier (e.g., "user:123:minute")
            limit: Maximum requests allowed
            window_seconds: Time window in seconds

        Returns:
            tuple: (allowed, remaining, reset_at_timestamp)
        """
        now = time.time()
        window_start = now - window_seconds

        # Clean old entries
        self._buckets[key] = [
            (ts, count) for ts, count in self._buckets[key]
            if ts > window_start
        ]

        # Count requests in window
        total = sum(count for _, count in self._buckets[key])

        if total >= limit:
            # Find earliest entry to calculate reset time
            if self._buckets[key]:
                reset_at = int(self._buckets[key][0][0] + window_seconds)
            else:
                reset_at = int(now + window_seconds)
            return False, 0, reset_at

        # Add new request
        self._buckets[key].append((now, 1))

        remaining = max(0, limit - total - 1)
        reset_at = int(now + window_seconds)

        return True, remaining, reset_at

    def increment(self, key: str, amount: int = 1) -> int:
        """Increment a counter and return new value."""
        now = time.time()
        self._buckets[key].append((now, amount))
        return sum(count for _, count in self._buckets[key])


# Global in-memory limiter
_memory_limiter = InMemoryRateLimiter()


# ============================================================
# Redis Rate Limiter
# ============================================================


async def get_redis_client():
    """Get Redis client instance."""
    try:
        import redis.asyncio as redis
        client = redis.from_url(settings.redis_url)
        # Test connection
        await client.ping()
        return client
    except Exception as e:
        logger.warning(f"Redis not available, using in-memory: {e}")
        return None


async def check_rate_limit(
    identifier: str,
    tier: str = "free",
    limit_type: str = "requests_per_minute",
) -> dict[str, Any]:
    """
    Check rate limit for a user/API key.

    Args:
        identifier: User ID, API key, or IP address
        tier: Subscription tier
        limit_type: Type of limit to check

    Returns:
        dict with allowed, remaining, reset_at, limit
    """
    config = TIER_LIMITS.get(tier, TIER_LIMITS["free"])

    # Get limit value
    limit = getattr(config, limit_type, 60)
    if limit == -1:  # Unlimited
        return {
            "allowed": True,
            "remaining": -1,
            "reset_at": 0,
            "limit": -1,
        }

    # Determine window based on limit type
    window_map = {
        "requests_per_minute": 60,
        "requests_per_hour": 3600,
        "requests_per_day": 86400,
        "api_calls_per_hour": 3600,
        "analyses_per_hour": 3600,  # ✅ 1 hour window for analyses
        "analyses_per_month": 2592000,  # 30 days
    }
    window = window_map.get(limit_type, 60)

    key = f"ratelimit:{identifier}:{limit_type}"

    # Try Redis first
    redis_client = await get_redis_client()
    if redis_client:
        try:
            return await _check_redis_rate_limit(
                redis_client, key, limit, window
            )
        except Exception as e:
            logger.warning(f"Redis rate limit failed, using memory: {e}")

    # Fallback to in-memory
    allowed, remaining, reset_at = _memory_limiter.check_rate_limit(
        key, limit, window
    )

    return {
        "allowed": allowed,
        "remaining": remaining,
        "reset_at": reset_at,
        "limit": limit,
    }


async def _check_redis_rate_limit(
    client,
    key: str,
    limit: int,
    window: int,
) -> dict[str, Any]:
    """Check rate limit using Redis sliding window."""
    import time

    now = time.time()
    window_start = now - window

    # Use Redis sorted set for sliding window
    pipe = client.pipeline()
    pipe.zremrangebyscore(key, 0, window_start)  # Remove old entries
    pipe.zadd(key, {str(now): now})  # Add current request
    pipe.zcard(key)  # Count requests in window
    pipe.expire(key, window + 1)  # Set TTL
    results = await pipe.execute()

    count = results[2]

    if count > limit:
        # Over limit - remove the entry we just added
        await client.zrem(key, str(now))
        # Get oldest entry for reset time
        oldest = await client.zrange(key, 0, 0, withscores=True)
        reset_at = int(oldest[0][1] + window) if oldest else int(now + window)
        return {
            "allowed": False,
            "remaining": 0,
            "reset_at": reset_at,
            "limit": limit,
        }

    reset_at = int(now + window)
    remaining = max(0, limit - count)

    return {
        "allowed": True,
        "remaining": remaining,
        "reset_at": reset_at,
        "limit": limit,
    }


# ============================================================
# Quota Tracking
# ============================================================


async def get_usage_stats(
    identifier: str,
    tier: str = "free",
) -> dict[str, Any]:
    """
    Get current usage statistics for a user.

    Args:
        identifier: User ID
        tier: Subscription tier

    Returns:
        dict with usage stats and limits
    """
    config = TIER_LIMITS.get(tier, TIER_LIMITS["free"])

    # Check each limit type
    stats = {}
    for limit_type in ["requests_per_minute", "requests_per_hour", "api_calls_per_hour", "analyses_per_month"]:
        result = await check_rate_limit(identifier, tier, limit_type)
        limit = getattr(config, limit_type, 0)
        used = limit - result["remaining"] if result["remaining"] >= 0 else 0

        stats[limit_type] = {
            "used": used,
            "limit": limit,
            "remaining": result["remaining"],
        }

    return {
        "tier": tier,
        "stats": stats,
        "timestamp": datetime.now().isoformat(),
    }


async def increment_usage(
    identifier: str,
    usage_type: str,
    amount: int = 1,
) -> int:
    """
    Increment usage counter (e.g., for analyses).

    Args:
        identifier: User ID
        usage_type: Type of usage (e.g., "analyses")
        amount: Amount to increment

    Returns:
        New usage count
    """
    key = f"usage:{identifier}:{usage_type}"

    redis_client = await get_redis_client()
    if redis_client:
        try:
            count = await redis_client.incrby(key, amount)
            # Set TTL for monthly reset
            await redis_client.expire(key, 2592000)
            return count
        except Exception as e:
            logger.warning(f"Redis increment failed: {e}")

    # Fallback to in-memory
    return _memory_limiter.increment(key, amount)


async def reset_monthly_usage(identifier: str) -> None:
    """Reset monthly usage counters for a user."""
    key = f"usage:{identifier}:analyses"

    redis_client = await get_redis_client()
    if redis_client:
        try:
            await redis_client.delete(key)
        except Exception as e:
            logger.warning(f"Redis reset failed: {e}")

    # Also reset in-memory
    _memory_limiter._buckets.pop(key, None)
