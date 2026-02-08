"""Per-source rate limiting service.

This module provides rate limiting to prevent API quota exhaustion
for external services like Reddit, Firecrawl, Google Trends, and Twitter.

Features:
- Per-source configurable limits
- Sliding window rate limiting
- Async-safe with asyncio locks
- Request tracking and statistics
- Graceful waiting when at limit

Default limits (conservative):
- Reddit: 60 requests/minute (PRAW limit)
- Firecrawl: 10 requests/minute
- Google Trends: 30 requests/minute
- Twitter: 450 requests/15 minutes
"""

import asyncio
import logging
from collections import defaultdict
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from typing import Any

logger = logging.getLogger(__name__)


@dataclass
class RateLimitConfig:
    """Configuration for a rate limit."""

    requests: int  # Number of requests allowed
    window_seconds: int  # Time window in seconds
    name: str = ""  # Human-readable name


@dataclass
class RateLimitStatus:
    """Current status of a rate limiter."""

    source: str
    remaining: int
    limit: int
    window_seconds: int
    reset_in_seconds: float
    is_limited: bool


class RateLimiter:
    """
    Per-source rate limiting to prevent API quota exhaustion.

    Uses sliding window algorithm: tracks individual request timestamps
    and counts requests within the window.

    Thread-safe using asyncio locks.

    Example:
        >>> limiter = RateLimiter()
        >>> await limiter.acquire("reddit")  # Wait if needed
        >>> # Make Reddit API call
    """

    # Default rate limits for each source
    DEFAULT_LIMITS: dict[str, RateLimitConfig] = {
        "reddit": RateLimitConfig(
            requests=60,
            window_seconds=60,
            name="Reddit (PRAW)",
        ),
        "firecrawl": RateLimitConfig(
            requests=10,
            window_seconds=60,
            name="Firecrawl API",
        ),
        "google_trends": RateLimitConfig(
            requests=30,
            window_seconds=60,
            name="Google Trends (pytrends)",
        ),
        "twitter": RateLimitConfig(
            requests=450,
            window_seconds=900,  # 15 minutes
            name="Twitter/X API",
        ),
        "product_hunt": RateLimitConfig(
            requests=30,
            window_seconds=60,
            name="Product Hunt (Firecrawl)",
        ),
    }

    def __init__(
        self,
        custom_limits: dict[str, RateLimitConfig] | None = None,
    ):
        """
        Initialize rate limiter.

        Args:
            custom_limits: Optional custom limits to override defaults
        """
        self._limits = {**self.DEFAULT_LIMITS}
        if custom_limits:
            self._limits.update(custom_limits)

        # Request timestamps by source
        self._request_times: dict[str, list[datetime]] = defaultdict(list)

        # Async locks by source (one lock per source)
        self._locks: dict[str, asyncio.Lock] = defaultdict(asyncio.Lock)

        # Statistics
        self._stats: dict[str, dict[str, int]] = defaultdict(
            lambda: {"requests": 0, "waits": 0, "total_wait_ms": 0}
        )

        logger.info(
            f"Rate limiter initialized with {len(self._limits)} source limits"
        )

    def configure_limit(
        self,
        source: str,
        requests: int,
        window_seconds: int,
        name: str = "",
    ) -> None:
        """
        Configure or update rate limit for a source.

        Args:
            source: Source identifier
            requests: Maximum requests per window
            window_seconds: Window duration in seconds
            name: Human-readable name
        """
        self._limits[source] = RateLimitConfig(
            requests=requests,
            window_seconds=window_seconds,
            name=name or source,
        )
        logger.info(
            f"Configured rate limit for {source}: "
            f"{requests} requests / {window_seconds}s"
        )

    async def acquire(self, source: str) -> float:
        """
        Acquire permission to make a request, waiting if necessary.

        This method should be called before each API request to the source.
        It will block (await) if the rate limit has been reached.

        Args:
            source: Data source name (reddit, firecrawl, etc.)

        Returns:
            Wait time in seconds (0 if no wait was needed)

        Example:
            >>> limiter = RateLimiter()
            >>> wait_time = await limiter.acquire("reddit")
            >>> # Now safe to make Reddit API call
        """
        if source not in self._limits:
            # No limit defined for this source
            return 0.0

        limit = self._limits[source]

        async with self._locks[source]:
            now = datetime.now(UTC)
            window_start = now - timedelta(seconds=limit.window_seconds)

            # Clean old requests outside the window
            self._request_times[source] = [
                t for t in self._request_times[source]
                if t > window_start
            ]

            current_count = len(self._request_times[source])

            # Check if at limit
            if current_count >= limit.requests:
                # Calculate wait time until oldest request expires
                oldest = self._request_times[source][0]
                wait_until = oldest + timedelta(seconds=limit.window_seconds)
                wait_seconds = (wait_until - now).total_seconds()

                if wait_seconds > 0:
                    logger.info(
                        f"Rate limit reached for {source} "
                        f"({current_count}/{limit.requests}), "
                        f"waiting {wait_seconds:.1f}s"
                    )

                    # Track statistics
                    self._stats[source]["waits"] += 1
                    self._stats[source]["total_wait_ms"] += int(wait_seconds * 1000)

                    await asyncio.sleep(wait_seconds)

                    # Clean again after waiting
                    now = datetime.now(UTC)
                    window_start = now - timedelta(seconds=limit.window_seconds)
                    self._request_times[source] = [
                        t for t in self._request_times[source]
                        if t > window_start
                    ]
                else:
                    wait_seconds = 0.0
            else:
                wait_seconds = 0.0

            # Record this request
            self._request_times[source].append(datetime.now(UTC))
            self._stats[source]["requests"] += 1

            return wait_seconds

    def get_remaining(self, source: str) -> int:
        """
        Get remaining requests available in current window.

        Args:
            source: Data source name

        Returns:
            Number of remaining requests (-1 if unlimited)
        """
        if source not in self._limits:
            return -1  # Unlimited

        limit = self._limits[source]
        now = datetime.now(UTC)
        window_start = now - timedelta(seconds=limit.window_seconds)

        # Count recent requests
        recent = [
            t for t in self._request_times.get(source, [])
            if t > window_start
        ]

        return max(0, limit.requests - len(recent))

    def get_status(self, source: str) -> RateLimitStatus | None:
        """
        Get detailed rate limit status for a source.

        Args:
            source: Data source name

        Returns:
            RateLimitStatus or None if source has no limit
        """
        if source not in self._limits:
            return None

        limit = self._limits[source]
        now = datetime.now(UTC)
        window_start = now - timedelta(seconds=limit.window_seconds)

        # Count recent requests
        recent = [
            t for t in self._request_times.get(source, [])
            if t > window_start
        ]
        current_count = len(recent)
        remaining = max(0, limit.requests - current_count)

        # Calculate reset time
        if recent:
            oldest = min(recent)
            reset_in = (oldest + timedelta(seconds=limit.window_seconds) - now).total_seconds()
            reset_in = max(0, reset_in)
        else:
            reset_in = 0.0

        return RateLimitStatus(
            source=source,
            remaining=remaining,
            limit=limit.requests,
            window_seconds=limit.window_seconds,
            reset_in_seconds=reset_in,
            is_limited=(remaining == 0),
        )

    def get_all_statuses(self) -> dict[str, RateLimitStatus]:
        """
        Get status for all configured sources.

        Returns:
            Dictionary of source name to RateLimitStatus
        """
        return {
            source: status
            for source in self._limits
            if (status := self.get_status(source)) is not None
        }

    def get_statistics(self) -> dict[str, dict[str, Any]]:
        """
        Get rate limiter statistics.

        Returns:
            Dictionary with statistics per source
        """
        stats = {}
        for source, data in self._stats.items():
            avg_wait_ms = (
                data["total_wait_ms"] / data["waits"]
                if data["waits"] > 0
                else 0
            )
            stats[source] = {
                "total_requests": data["requests"],
                "total_waits": data["waits"],
                "total_wait_ms": data["total_wait_ms"],
                "average_wait_ms": round(avg_wait_ms, 2),
                "wait_percentage": round(
                    (data["waits"] / data["requests"] * 100)
                    if data["requests"] > 0
                    else 0,
                    2,
                ),
            }

        # Add current status
        for source, status in self.get_all_statuses().items():
            if source not in stats:
                stats[source] = {
                    "total_requests": 0,
                    "total_waits": 0,
                    "total_wait_ms": 0,
                    "average_wait_ms": 0,
                    "wait_percentage": 0,
                }
            stats[source]["current_remaining"] = status.remaining
            stats[source]["is_limited"] = status.is_limited

        return stats

    def reset(self, source: str | None = None) -> None:
        """
        Reset rate limiter state.

        Args:
            source: Specific source to reset, or None for all sources
        """
        if source:
            self._request_times[source] = []
            self._stats[source] = {"requests": 0, "waits": 0, "total_wait_ms": 0}
            logger.info(f"Rate limiter reset for source: {source}")
        else:
            self._request_times.clear()
            self._stats.clear()
            logger.info("Rate limiter reset for all sources")


# Global rate limiter instance
_rate_limiter: RateLimiter | None = None


def get_rate_limiter() -> RateLimiter:
    """
    Get or create global rate limiter instance.

    Returns:
        RateLimiter: Singleton rate limiter instance
    """
    global _rate_limiter
    if _rate_limiter is None:
        _rate_limiter = RateLimiter()
    return _rate_limiter


async def rate_limited(source: str):
    """
    Decorator context manager for rate limiting.

    Example:
        >>> async with rate_limited("reddit"):
        ...     await reddit_api_call()
    """
    limiter = get_rate_limiter()
    await limiter.acquire(source)


# =============================================================================
# Subscription Tier Rate Limiting (Phase 6.3)
# =============================================================================

@dataclass
class TierRateLimitConfig:
    """Rate limit configuration for a subscription tier."""

    tier: str
    requests_per_minute: int
    requests_per_hour: int
    requests_per_day: int
    research_requests_per_month: int
    api_calls_per_month: int


# Default tier limits
TIER_LIMITS: dict[str, TierRateLimitConfig] = {
    "free": TierRateLimitConfig(
        tier="free",
        requests_per_minute=10,
        requests_per_hour=100,
        requests_per_day=500,
        research_requests_per_month=3,
        api_calls_per_month=1000,
    ),
    "starter": TierRateLimitConfig(
        tier="starter",
        requests_per_minute=30,
        requests_per_hour=500,
        requests_per_day=2000,
        research_requests_per_month=10,
        api_calls_per_month=10000,
    ),
    "pro": TierRateLimitConfig(
        tier="pro",
        requests_per_minute=60,
        requests_per_hour=1000,
        requests_per_day=5000,
        research_requests_per_month=50,
        api_calls_per_month=50000,
    ),
    "enterprise": TierRateLimitConfig(
        tier="enterprise",
        requests_per_minute=120,
        requests_per_hour=5000,
        requests_per_day=20000,
        research_requests_per_month=200,
        api_calls_per_month=200000,
    ),
}


class InMemoryRateLimiter:
    """
    In-memory rate limiter for subscription tier limiting.

    Used as fallback when Redis is not available.
    Uses sliding window algorithm.
    """

    def __init__(self):
        self._request_times: dict[str, list[datetime]] = defaultdict(list)
        self._locks: dict[str, asyncio.Lock] = defaultdict(asyncio.Lock)

    def check_rate_limit(
        self,
        identifier: str,
        limit: int,
        window_seconds: int,
    ) -> tuple[bool, int, datetime]:
        """
        Check if a request is allowed under rate limit.

        Args:
            identifier: User ID or API key
            limit: Maximum requests allowed in window
            window_seconds: Window duration in seconds

        Returns:
            Tuple of (allowed, remaining, reset_at)
        """
        now = datetime.now(UTC)
        window_start = now - timedelta(seconds=window_seconds)

        # Clean old requests
        self._request_times[identifier] = [
            t for t in self._request_times[identifier]
            if t > window_start
        ]

        current_count = len(self._request_times[identifier])

        if current_count >= limit:
            # Rate limited
            oldest = self._request_times[identifier][0] if self._request_times[identifier] else now
            reset_at = oldest + timedelta(seconds=window_seconds)
            return (False, 0, reset_at)

        # Record request
        self._request_times[identifier].append(now)
        remaining = limit - current_count - 1
        reset_at = now + timedelta(seconds=window_seconds)

        return (True, remaining, reset_at)

    def get_usage_count(self, identifier: str, window_seconds: int) -> int:
        """Get current usage count in window."""
        now = datetime.now(UTC)
        window_start = now - timedelta(seconds=window_seconds)

        recent = [
            t for t in self._request_times.get(identifier, [])
            if t > window_start
        ]
        return len(recent)

    def reset(self, identifier: str) -> None:
        """Reset rate limit for an identifier."""
        self._request_times[identifier] = []


# Global in-memory limiter instance
_tier_limiter: InMemoryRateLimiter | None = None


def get_tier_limiter() -> InMemoryRateLimiter:
    """Get or create global tier rate limiter instance."""
    global _tier_limiter
    if _tier_limiter is None:
        _tier_limiter = InMemoryRateLimiter()
    return _tier_limiter


async def check_rate_limit(
    identifier: str,
    tier: str = "free",
    limit_type: str = "requests_per_minute",
) -> dict[str, Any]:
    """
    Check rate limit for a user/API key.

    Args:
        identifier: User ID or API key
        tier: Subscription tier (free, starter, pro, enterprise)
        limit_type: Type of limit to check

    Returns:
        Dict with allowed, remaining, reset_at, limit
    """
    tier_config = TIER_LIMITS.get(tier, TIER_LIMITS["free"])

    # Get limit based on type
    limit = getattr(tier_config, limit_type, 10)

    # Determine window based on limit type
    window_seconds = 60  # Default: per minute
    if "hour" in limit_type:
        window_seconds = 3600
    elif "day" in limit_type:
        window_seconds = 86400
    elif "month" in limit_type:
        window_seconds = 2592000  # 30 days

    limiter = get_tier_limiter()
    allowed, remaining, reset_at = limiter.check_rate_limit(
        identifier=f"{identifier}:{limit_type}",
        limit=limit,
        window_seconds=window_seconds,
    )

    return {
        "allowed": allowed,
        "remaining": remaining,
        "reset_at": reset_at.isoformat(),
        "limit": limit,
        "limit_type": limit_type,
        "tier": tier,
    }


async def get_usage_stats(identifier: str, tier: str = "free") -> dict[str, Any]:
    """
    Get usage statistics for an identifier.

    Args:
        identifier: User ID or API key
        tier: Subscription tier

    Returns:
        Dict with usage stats by limit type
    """
    tier_config = TIER_LIMITS.get(tier, TIER_LIMITS["free"])
    limiter = get_tier_limiter()

    stats = {
        "identifier": identifier,
        "tier": tier,
        "usage": {},
    }

    # Check each limit type
    for limit_type in ["requests_per_minute", "requests_per_hour", "requests_per_day"]:
        limit = getattr(tier_config, limit_type, 10)

        window_seconds = 60
        if "hour" in limit_type:
            window_seconds = 3600
        elif "day" in limit_type:
            window_seconds = 86400

        used = limiter.get_usage_count(
            f"{identifier}:{limit_type}",
            window_seconds,
        )

        stats["usage"][limit_type] = {
            "used": used,
            "limit": limit,
            "remaining": max(0, limit - used),
        }

    return stats


async def increment_usage(
    identifier: str,
    usage_type: str = "requests_per_minute",
    tier: str = "free",
) -> int:
    """
    Increment usage counter for an identifier.

    Args:
        identifier: User ID or API key
        usage_type: Type of usage to track
        tier: Subscription tier

    Returns:
        New usage count
    """
    tier_config = TIER_LIMITS.get(tier, TIER_LIMITS["free"])
    limit = getattr(tier_config, usage_type, 10)

    window_seconds = 60
    if "hour" in usage_type:
        window_seconds = 3600
    elif "day" in usage_type:
        window_seconds = 86400
    elif "month" in usage_type:
        window_seconds = 2592000

    limiter = get_tier_limiter()
    key = f"{identifier}:{usage_type}"

    # Check and increment
    allowed, remaining, reset_at = limiter.check_rate_limit(
        identifier=key,
        limit=limit,
        window_seconds=window_seconds,
    )

    # Return new count
    return limiter.get_usage_count(key, window_seconds)
