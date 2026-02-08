"""Tests for rate limiter service.

Tests per-source rate limiting:
1. Basic acquire behavior
2. Rate limit enforcement
3. Multiple sources
4. Statistics tracking
"""

import asyncio
from datetime import datetime, timedelta

import pytest

from app.services.rate_limiter import (
    RateLimiter,
    RateLimitConfig,
    RateLimitStatus,
    get_rate_limiter,
)


class TestRateLimiter:
    """Test RateLimiter class."""

    @pytest.fixture
    def limiter(self):
        """Create rate limiter with test configuration."""
        return RateLimiter(
            custom_limits={
                "test_source": RateLimitConfig(
                    requests=5,
                    window_seconds=60,
                    name="Test Source",
                ),
                "fast_source": RateLimitConfig(
                    requests=10,
                    window_seconds=10,
                    name="Fast Source",
                ),
            }
        )

    @pytest.mark.asyncio
    async def test_acquire_succeeds_under_limit(self, limiter):
        """Test that acquire succeeds when under rate limit."""
        wait_time = await limiter.acquire("test_source")
        assert wait_time == 0.0

    @pytest.mark.asyncio
    async def test_acquire_returns_zero_for_unknown_source(self, limiter):
        """Test that unknown sources have no rate limit."""
        wait_time = await limiter.acquire("unknown_source")
        assert wait_time == 0.0

    @pytest.mark.asyncio
    async def test_remaining_decreases_after_acquire(self, limiter):
        """Test that remaining count decreases after acquire."""
        initial = limiter.get_remaining("test_source")

        await limiter.acquire("test_source")

        after = limiter.get_remaining("test_source")
        assert after == initial - 1

    @pytest.mark.asyncio
    async def test_remaining_returns_minus_one_for_unlimited(self, limiter):
        """Test that unlimited sources return -1 for remaining."""
        remaining = limiter.get_remaining("unknown_source")
        assert remaining == -1

    def test_get_status_returns_none_for_unknown(self, limiter):
        """Test that get_status returns None for unknown sources."""
        status = limiter.get_status("unknown_source")
        assert status is None

    def test_get_status_returns_status(self, limiter):
        """Test that get_status returns RateLimitStatus."""
        status = limiter.get_status("test_source")

        assert isinstance(status, RateLimitStatus)
        assert status.source == "test_source"
        assert status.limit == 5
        assert status.window_seconds == 60

    @pytest.mark.asyncio
    async def test_statistics_tracking(self, limiter):
        """Test that statistics are tracked."""
        await limiter.acquire("test_source")
        await limiter.acquire("test_source")

        stats = limiter.get_statistics()

        assert "test_source" in stats
        assert stats["test_source"]["total_requests"] == 2

    @pytest.mark.asyncio
    async def test_reset_clears_source(self, limiter):
        """Test that reset clears a specific source."""
        await limiter.acquire("test_source")
        assert limiter.get_remaining("test_source") < 5

        limiter.reset("test_source")

        assert limiter.get_remaining("test_source") == 5

    @pytest.mark.asyncio
    async def test_reset_all_clears_everything(self, limiter):
        """Test that reset without source clears everything."""
        await limiter.acquire("test_source")
        await limiter.acquire("fast_source")

        limiter.reset()

        assert limiter.get_remaining("test_source") == 5
        assert limiter.get_remaining("fast_source") == 10

    def test_configure_limit_adds_new_source(self, limiter):
        """Test that configure_limit adds a new source."""
        limiter.configure_limit(
            source="new_source",
            requests=20,
            window_seconds=30,
            name="New Source",
        )

        status = limiter.get_status("new_source")
        assert status is not None
        assert status.limit == 20

    def test_configure_limit_updates_existing(self, limiter):
        """Test that configure_limit updates existing source."""
        limiter.configure_limit(
            source="test_source",
            requests=100,
            window_seconds=120,
        )

        status = limiter.get_status("test_source")
        assert status.limit == 100
        assert status.window_seconds == 120

    @pytest.mark.asyncio
    async def test_get_all_statuses(self, limiter):
        """Test that get_all_statuses returns all sources."""
        statuses = limiter.get_all_statuses()

        assert "test_source" in statuses
        assert "fast_source" in statuses
        # Default sources are also included
        assert "reddit" in statuses

    @pytest.mark.asyncio
    async def test_is_limited_when_at_capacity(self, limiter):
        """Test that is_limited is True when at capacity."""
        # Exhaust the limit
        for _ in range(5):
            await limiter.acquire("test_source")

        status = limiter.get_status("test_source")
        assert status.remaining == 0
        assert status.is_limited is True

    @pytest.mark.asyncio
    async def test_concurrent_access_is_safe(self, limiter):
        """Test that concurrent access doesn't cause issues."""
        async def make_requests():
            for _ in range(3):
                await limiter.acquire("test_source")
                await asyncio.sleep(0.01)

        # Run multiple concurrent tasks
        await asyncio.gather(
            make_requests(),
            make_requests(),
        )

        # Should have recorded all requests
        stats = limiter.get_statistics()
        assert stats["test_source"]["total_requests"] == 6


class TestDefaultLimits:
    """Test default rate limit configurations."""

    def test_reddit_limit(self):
        """Test Reddit default limit."""
        limiter = RateLimiter()
        status = limiter.get_status("reddit")

        assert status is not None
        assert status.limit == 60
        assert status.window_seconds == 60

    def test_firecrawl_limit(self):
        """Test Firecrawl default limit."""
        limiter = RateLimiter()
        status = limiter.get_status("firecrawl")

        assert status is not None
        assert status.limit == 10
        assert status.window_seconds == 60

    def test_twitter_limit(self):
        """Test Twitter default limit."""
        limiter = RateLimiter()
        status = limiter.get_status("twitter")

        assert status is not None
        assert status.limit == 450
        assert status.window_seconds == 900  # 15 minutes

    def test_google_trends_limit(self):
        """Test Google Trends default limit."""
        limiter = RateLimiter()
        status = limiter.get_status("google_trends")

        assert status is not None
        assert status.limit == 30
        assert status.window_seconds == 60


class TestGetRateLimiter:
    """Test get_rate_limiter singleton."""

    def test_returns_same_instance(self):
        """Test that get_rate_limiter returns singleton."""
        import app.services.rate_limiter as module

        # Reset global
        module._rate_limiter = None

        limiter1 = get_rate_limiter()
        limiter2 = get_rate_limiter()

        assert limiter1 is limiter2
