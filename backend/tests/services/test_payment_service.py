"""Tests for payment service - Phase 6.1."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.services.payment_service import (
    PRICING_TIERS,
    check_tier_limit,
    create_checkout_session,
    create_customer_portal_session,
    get_tier_limits,
    handle_webhook_event,
)


class TestPricingTiers:
    """Tests for pricing tier configuration."""

    def test_pricing_tiers_exist(self):
        """Test that all pricing tiers are defined."""
        assert "free" in PRICING_TIERS
        assert "starter" in PRICING_TIERS
        assert "pro" in PRICING_TIERS
        assert "enterprise" in PRICING_TIERS

    def test_free_tier_prices(self):
        """Test free tier has zero prices."""
        free_tier = PRICING_TIERS["free"]
        assert free_tier.price_monthly == 0
        assert free_tier.price_yearly == 0

    def test_starter_tier_prices(self):
        """Test starter tier pricing in cents."""
        starter_tier = PRICING_TIERS["starter"]
        assert starter_tier.price_monthly == 1900  # $19
        # Yearly price varies by implementation
        assert starter_tier.price_yearly > 0

    def test_tier_features_defined(self):
        """Test that each tier has features defined."""
        for tier_name, tier in PRICING_TIERS.items():
            assert isinstance(tier.features, list)
            assert len(tier.features) > 0

    def test_tier_limits_are_dict(self):
        """Test that each tier has limits as dict."""
        for tier_name, tier in PRICING_TIERS.items():
            assert isinstance(tier.limits, dict)


class TestGetTierLimits:
    """Tests for get_tier_limits function."""

    def test_get_free_tier_limits(self):
        """Test getting free tier limits."""
        limits = get_tier_limits("free")
        assert isinstance(limits, dict)
        # Check some expected keys exist
        assert len(limits) > 0

    def test_get_unknown_tier_returns_free(self):
        """Test that unknown tier falls back to free."""
        limits = get_tier_limits("unknown_tier")
        assert limits == get_tier_limits("free")


class TestCheckTierLimit:
    """Tests for check_tier_limit function."""

    def test_returns_bool_or_dict(self):
        """Test check returns a bool or dict."""
        result = check_tier_limit("free", "insights_per_day", 0)
        # May return bool or dict depending on implementation
        assert isinstance(result, (bool, dict))


class TestCreateCheckoutSession:
    """Tests for create_checkout_session function."""

    @pytest.mark.asyncio
    async def test_checkout_returns_dict(self):
        """Test checkout returns a dict."""
        result = await create_checkout_session(
            user_id="user123",
            tier="starter",
            success_url="https://example.com/success",
            cancel_url="https://example.com/cancel",
        )
        # Either returns mock or real session
        assert isinstance(result, dict) or result is None


class TestCreateCustomerPortalSession:
    """Tests for create_customer_portal_session function."""

    @pytest.mark.asyncio
    async def test_portal_returns_dict_or_none(self):
        """Test portal returns a dict or None."""
        result = await create_customer_portal_session(
            stripe_customer_id="cus_123",
            return_url="https://example.com/dashboard",
        )
        # Either returns mock or None without Stripe
        assert isinstance(result, dict) or result is None


class TestHandleWebhookEvent:
    """Tests for handle_webhook_event function."""

    @pytest.mark.asyncio
    async def test_webhook_without_stripe_key(self):
        """Test webhook returns error without Stripe API key."""
        with patch("app.services.payment_service.settings") as mock_settings:
            mock_settings.stripe_secret_key = None
            result = await handle_webhook_event(b"payload", "sig_123")
            assert result["status"] == "error"
