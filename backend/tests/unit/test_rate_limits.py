"""Tests for tier-based rate limiting configuration."""

from unittest.mock import MagicMock

from app.core.rate_limits import (
    DEFAULT_RATE_LIMIT,
    TIER_RATE_LIMITS,
    get_identifier,
    get_tier_rate_limit,
)


class TestTierRateLimits:
    """Test tier-based rate limit configuration."""

    def test_all_tiers_defined(self):
        """All subscription tiers should have rate limits."""
        expected_tiers = ["anonymous", "free", "starter", "pro", "enterprise"]
        for tier in expected_tiers:
            assert tier in TIER_RATE_LIMITS

    def test_tiers_increase_with_plan(self):
        """Higher tiers should have higher rate limits."""
        tier_order = ["anonymous", "free", "starter", "pro", "enterprise"]
        limits = []
        for tier in tier_order:
            rate = TIER_RATE_LIMITS[tier]
            # Parse "X/minute" to int
            limit_num = int(rate.split("/")[0])
            limits.append(limit_num)

        # Each tier should be >= previous
        for i in range(1, len(limits)):
            assert limits[i] >= limits[i - 1], (
                f"{tier_order[i]} ({limits[i]}) should be >= {tier_order[i-1]} ({limits[i-1]})"
            )

    def test_anonymous_rate_limit(self):
        """Anonymous users should get lowest rate."""
        assert TIER_RATE_LIMITS["anonymous"] == "20/minute"

    def test_free_rate_limit(self):
        """Free tier users should get 30/minute."""
        assert TIER_RATE_LIMITS["free"] == "30/minute"

    def test_pro_rate_limit(self):
        """Pro tier users should get 120/minute."""
        assert TIER_RATE_LIMITS["pro"] == "120/minute"

    def test_enterprise_rate_limit(self):
        """Enterprise tier should have highest limit."""
        assert TIER_RATE_LIMITS["enterprise"] == "300/minute"


class TestGetTierRateLimit:
    """Test dynamic rate limit based on user tier."""

    def test_anonymous_user(self):
        """Request without user should get anonymous rate."""
        request = MagicMock()
        request.state = MagicMock(spec=[])  # No 'user' attribute

        result = get_tier_rate_limit(request)
        assert result == TIER_RATE_LIMITS["anonymous"]

    def test_free_user(self):
        """Free tier user should get free rate limit."""
        request = MagicMock()
        request.state.user = MagicMock()
        request.state.user.subscription_tier = "free"

        result = get_tier_rate_limit(request)
        assert result == TIER_RATE_LIMITS["free"]

    def test_pro_user(self):
        """Pro tier user should get pro rate limit."""
        request = MagicMock()
        request.state.user = MagicMock()
        request.state.user.subscription_tier = "pro"

        result = get_tier_rate_limit(request)
        assert result == TIER_RATE_LIMITS["pro"]

    def test_enterprise_user(self):
        """Enterprise tier user should get enterprise rate limit."""
        request = MagicMock()
        request.state.user = MagicMock()
        request.state.user.subscription_tier = "enterprise"

        result = get_tier_rate_limit(request)
        assert result == TIER_RATE_LIMITS["enterprise"]

    def test_unknown_tier_falls_back(self):
        """Unknown tier should fall back to default."""
        request = MagicMock()
        request.state.user = MagicMock()
        request.state.user.subscription_tier = "unknown_tier"

        result = get_tier_rate_limit(request)
        assert result == DEFAULT_RATE_LIMIT

    def test_null_user(self):
        """Null user on state should get anonymous rate."""
        request = MagicMock()
        request.state.user = None

        result = get_tier_rate_limit(request)
        assert result == TIER_RATE_LIMITS["anonymous"]


class TestGetIdentifier:
    """Test rate limit key generation."""

    def test_authenticated_user(self):
        """Authenticated user should use user ID as key."""
        request = MagicMock()
        request.state.user = MagicMock()
        request.state.user.id = "user-123"

        result = get_identifier(request)
        assert result == "user:user-123"

    def test_anonymous_user_uses_ip(self):
        """Anonymous user should fall back to IP address."""
        request = MagicMock()
        request.state = MagicMock(spec=[])  # No 'user' attribute
        request.client = MagicMock()
        request.client.host = "192.168.1.1"

        result = get_identifier(request)
        assert result == "192.168.1.1"

    def test_null_user_uses_ip(self):
        """Null user should fall back to IP address."""
        request = MagicMock()
        request.state.user = None
        request.client = MagicMock()
        request.client.host = "10.0.0.1"

        result = get_identifier(request)
        assert result == "10.0.0.1"
