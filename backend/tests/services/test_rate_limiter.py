"""Tests for rate limiter service - Phase 6.3."""


import pytest
from app.services.rate_limiter import (
    TIER_LIMITS,
    InMemoryRateLimiter,
    check_rate_limit,
    get_usage_stats,
    increment_usage,
)


class TestTierLimits:
    """Tests for tier limits configuration."""

    def test_tier_limits_exist(self):
        """Test that all tier limits are defined."""
        assert "free" in TIER_LIMITS
        assert "starter" in TIER_LIMITS
        assert "pro" in TIER_LIMITS
        assert "enterprise" in TIER_LIMITS

    def test_tier_limits_are_pydantic_models(self):
        """Test that tier limits are valid Pydantic models."""
        for tier_name, config in TIER_LIMITS.items():
            assert hasattr(config, 'requests_per_minute')
            assert hasattr(config, 'requests_per_hour')

    def test_free_tier_has_limits(self):
        """Test free tier has restrictive limits."""
        free_config = TIER_LIMITS["free"]
        assert free_config.requests_per_minute > 0
        assert free_config.requests_per_hour > 0


class TestInMemoryRateLimiter:
    """Tests for in-memory rate limiter fallback."""

    def test_init_creates_limiter(self):
        """Test limiter initializes correctly."""
        limiter = InMemoryRateLimiter()
        assert limiter is not None

    def test_check_rate_limit_first_request(self):
        """Test first request is allowed."""
        limiter = InMemoryRateLimiter()
        allowed, remaining, reset_at = limiter.check_rate_limit("user123", limit=10, window_seconds=60)
        assert allowed is True
        assert remaining == 9

    def test_check_rate_limit_at_limit(self):
        """Test request at limit is rejected."""
        limiter = InMemoryRateLimiter()
        # Make requests up to limit
        for _ in range(10):
            limiter.check_rate_limit("user123", limit=10, window_seconds=60)
        allowed, remaining, reset_at = limiter.check_rate_limit("user123", limit=10, window_seconds=60)
        assert allowed is False
        assert remaining == 0


class TestCheckRateLimit:
    """Tests for check_rate_limit function."""

    @pytest.mark.asyncio
    async def test_check_rate_limit_returns_dict(self):
        """Test rate limit check returns dict."""
        # This uses fallback to in-memory since Redis won't be available
        result = await check_rate_limit(
            identifier="user123",
            tier="free",
        )
        assert isinstance(result, dict)
        assert "allowed" in result
        assert "remaining" in result


class TestGetUsageStats:
    """Tests for get_usage_stats function."""

    @pytest.mark.asyncio
    async def test_get_usage_stats_returns_dict(self):
        """Test usage stats returns dict."""
        result = await get_usage_stats(identifier="user123")
        assert isinstance(result, dict)
        assert "tier" in result


class TestIncrementUsage:
    """Tests for increment_usage function."""

    @pytest.mark.asyncio
    async def test_increment_usage_returns_count(self):
        """Test increment usage returns new count."""
        result = await increment_usage(identifier="user456", usage_type="test")
        assert isinstance(result, int)
        assert result >= 1
