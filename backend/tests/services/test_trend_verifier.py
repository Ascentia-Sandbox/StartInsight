"""Tests for trend keyword verification service.

Tests the TrendVerifier class which validates LLM-generated
trend keywords against Google Trends data.
"""

from unittest.mock import MagicMock, patch

import pytest

from app.services.trend_verification import (
    TrendKeywordData,
    TrendVerificationResult,
    TrendVerifier,
    compare_growth_claims,
    get_trend_verifier,
)


class TestVolumeFormatting:
    """Test volume formatting."""

    def test_format_high_volume(self):
        """Should format high volume correctly."""
        result = TrendVerifier._format_volume(75)
        assert result == "High"

    def test_format_medium_volume(self):
        """Should format medium volume correctly."""
        result = TrendVerifier._format_volume(50)
        assert result == "Medium"

    def test_format_low_volume(self):
        """Should format low volume correctly."""
        result = TrendVerifier._format_volume(25)
        assert result == "Low"

    def test_format_very_low_volume(self):
        """Should format very low volume correctly."""
        result = TrendVerifier._format_volume(10)
        assert result == "Very Low"


class TestGrowthFormatting:
    """Test growth percentage formatting."""

    def test_format_positive_growth(self):
        """Should format positive growth with + sign."""
        result = TrendVerifier._format_growth(45.2)
        assert result == "+45.2%"

    def test_format_negative_growth(self):
        """Should format negative growth without + sign."""
        result = TrendVerifier._format_growth(-12.3)
        assert result == "-12.3%"

    def test_format_zero_growth(self):
        """Should format zero growth with + sign."""
        result = TrendVerifier._format_growth(0.0)
        assert result == "+0.0%"

    def test_format_none_growth(self):
        """Should format None as N/A."""
        result = TrendVerifier._format_growth(None)
        assert result == "N/A"


class TestTrendVerifierInit:
    """Test TrendVerifier initialization."""

    def test_default_initialization(self):
        """Should initialize with default settings."""
        verifier = TrendVerifier()

        assert verifier._hl == "en-US"
        assert verifier._tz == 360
        assert verifier._retries == 3
        assert verifier._pytrends is None
        assert verifier._cache == {}

    def test_custom_initialization(self):
        """Should accept custom settings."""
        verifier = TrendVerifier(hl="de-DE", tz=60, retries=5)

        assert verifier._hl == "de-DE"
        assert verifier._tz == 60
        assert verifier._retries == 5


class TestVerifyTrendKeywords:
    """Test trend keyword verification."""

    @pytest.mark.asyncio
    async def test_verify_empty_list(self):
        """Should handle empty keyword list."""
        verifier = TrendVerifier()

        verified, verified_count, unverified_count = await verifier.verify_trend_keywords([])

        assert verified == []
        assert verified_count == 0
        assert unverified_count == 0

    @pytest.mark.asyncio
    async def test_skip_empty_keywords(self):
        """Should skip keywords with empty strings."""
        verifier = TrendVerifier()

        keywords = [{"keyword": "", "volume": "1K", "growth": "+10%"}]
        verified, verified_count, unverified_count = await verifier.verify_trend_keywords(keywords)

        assert verified == []
        assert verified_count == 0
        assert unverified_count == 1


class TestCompareGrowthClaims:
    """Test growth claim comparison."""

    def test_accurate_claim_within_tolerance(self):
        """Should accept claims within tolerance."""
        is_accurate, message = compare_growth_claims("+50%", 45.0, tolerance_percent=50.0)
        assert is_accurate is True
        assert "accurate" in message.lower()

    def test_inaccurate_claim_outside_tolerance(self):
        """Should reject claims outside tolerance."""
        is_accurate, message = compare_growth_claims("+1900%", 10.0, tolerance_percent=50.0)
        assert is_accurate is False
        assert "inaccurate" in message.lower()

    def test_missing_data(self):
        """Should handle missing data."""
        is_accurate, message = compare_growth_claims(None, 10.0)
        assert is_accurate is False
        assert "missing data" in message.lower()

    def test_invalid_claim_format(self):
        """Should handle invalid claim format."""
        is_accurate, message = compare_growth_claims("invalid", 10.0)
        assert is_accurate is False
        assert "cannot parse" in message.lower()


class TestGetTrendVerifier:
    """Test singleton getter."""

    def test_returns_verifier_instance(self):
        """Should return a TrendVerifier instance."""
        verifier = get_trend_verifier()
        assert isinstance(verifier, TrendVerifier)

    def test_returns_same_instance(self):
        """Should return the same instance on subsequent calls."""
        verifier1 = get_trend_verifier()
        verifier2 = get_trend_verifier()
        assert verifier1 is verifier2
