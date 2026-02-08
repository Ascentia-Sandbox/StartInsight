"""Tests for competitor URL validation service.

Tests the URLValidator class which validates that competitor
URLs are reachable and resolve correctly.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from app.services.url_validator import (
    URLValidator,
    URLValidationResult,
    CompetitorData,
    get_url_validator,
)


class TestURLNormalization:
    """Test URL normalization."""

    def test_add_https_scheme(self):
        """Should add https:// scheme when missing."""
        validator = URLValidator()
        result = validator._normalize_url("example.com")
        assert result == "https://example.com"

    def test_preserve_http_scheme(self):
        """Should preserve existing http:// scheme."""
        validator = URLValidator()
        result = validator._normalize_url("http://example.com")
        assert result == "http://example.com"

    def test_preserve_https_scheme(self):
        """Should preserve existing https:// scheme."""
        validator = URLValidator()
        result = validator._normalize_url("https://example.com")
        assert result == "https://example.com"

    def test_strip_whitespace(self):
        """Should strip whitespace."""
        validator = URLValidator()
        result = validator._normalize_url("  https://example.com  ")
        assert result == "https://example.com"

    def test_normalize_path(self):
        """Should normalize path slashes."""
        validator = URLValidator()
        result = validator._normalize_url("https://example.com/path/")
        assert result == "https://example.com/path"

    def test_invalid_url_raises(self):
        """Should raise ValueError for invalid URL."""
        validator = URLValidator()
        with pytest.raises(ValueError):
            validator._normalize_url("")


class TestURLFormatValidation:
    """Test URL format validation."""

    def test_valid_https_url(self):
        """Should accept valid https URL."""
        validator = URLValidator()
        is_valid, error = validator._is_valid_url_format("https://example.com")
        assert is_valid is True
        assert error is None

    def test_valid_http_url(self):
        """Should accept valid http URL."""
        validator = URLValidator()
        is_valid, error = validator._is_valid_url_format("http://example.com")
        assert is_valid is True
        assert error is None

    def test_missing_scheme(self):
        """Should reject URL without scheme."""
        validator = URLValidator()
        is_valid, error = validator._is_valid_url_format("example.com")
        assert is_valid is False
        assert "scheme" in error.lower()

    def test_invalid_scheme(self):
        """Should reject invalid scheme."""
        validator = URLValidator()
        is_valid, error = validator._is_valid_url_format("ftp://example.com")
        assert is_valid is False
        assert "invalid scheme" in error.lower()

    def test_missing_netloc(self):
        """Should reject URL without domain."""
        validator = URLValidator()
        is_valid, error = validator._is_valid_url_format("https://")
        assert is_valid is False
        assert "netloc" in error.lower()


class TestURLValidatorInit:
    """Test URLValidator initialization."""

    def test_default_initialization(self):
        """Should initialize with default settings."""
        validator = URLValidator()

        assert validator._timeout == 10.0
        assert validator._max_redirects == 5
        assert validator._verify_ssl is True
        assert validator._cache == {}

    def test_custom_initialization(self):
        """Should accept custom settings."""
        validator = URLValidator(timeout=5.0, max_redirects=3, verify_ssl=False)

        assert validator._timeout == 5.0
        assert validator._max_redirects == 3
        assert validator._verify_ssl is False


class TestValidateCompetitors:
    """Test competitor URL validation."""

    @pytest.mark.asyncio
    async def test_validate_empty_list(self):
        """Should handle empty competitor list."""
        validator = URLValidator()

        valid, valid_count, invalid_count = await validator.validate_competitors([])

        assert valid == []
        assert valid_count == 0
        assert invalid_count == 0

    @pytest.mark.asyncio
    async def test_skip_missing_url(self):
        """Should skip competitors without URL."""
        validator = URLValidator()

        competitors = [{"name": "Test", "url": "", "description": "Test"}]
        valid, valid_count, invalid_count = await validator.validate_competitors(competitors)

        assert valid == []
        assert valid_count == 0
        assert invalid_count == 1


class TestCacheOperations:
    """Test cache operations."""

    def test_clear_cache(self):
        """Should clear the cache."""
        validator = URLValidator()
        validator._cache["test"] = URLValidationResult(
            url="test",
            valid=True,
            final_url="test",
            status_code=200,
            redirect_count=0,
            response_time_ms=100.0,
        )

        validator.clear_cache()

        assert validator._cache == {}

    def test_get_cache_stats(self):
        """Should return cache statistics."""
        validator = URLValidator()
        validator._cache["valid"] = URLValidationResult(
            url="valid",
            valid=True,
            final_url="valid",
            status_code=200,
            redirect_count=0,
            response_time_ms=100.0,
        )
        validator._cache["invalid"] = URLValidationResult(
            url="invalid",
            valid=False,
            final_url=None,
            status_code=404,
            redirect_count=0,
            response_time_ms=100.0,
            error="HTTP 404",
        )

        stats = validator.get_cache_stats()

        assert stats["cached_urls"] == 2
        assert stats["valid_cached"] == 1
        assert stats["invalid_cached"] == 1


class TestGetURLValidator:
    """Test singleton getter."""

    def test_returns_validator_instance(self):
        """Should return a URLValidator instance."""
        validator = get_url_validator()
        assert isinstance(validator, URLValidator)

    def test_returns_same_instance(self):
        """Should return the same instance on subsequent calls."""
        validator1 = get_url_validator()
        validator2 = get_url_validator()
        assert validator1 is validator2
