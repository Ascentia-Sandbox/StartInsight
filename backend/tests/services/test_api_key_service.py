"""Tests for API key service - Phase 7.2."""

from uuid import uuid4

import pytest

from app.services.api_key_service import (
    AVAILABLE_SCOPES,
    check_api_key_rate_limit,
    check_scope,
    create_api_key,
    generate_api_key,
    get_missing_scopes,
    hash_api_key,
    record_api_key_usage,
    revoke_api_key,
    validate_api_key,
)


class TestAvailableScopes:
    """Tests for available scopes configuration."""

    def test_scopes_exist(self):
        """Test that required scopes are defined."""
        assert "insights:read" in AVAILABLE_SCOPES
        assert "insights:write" in AVAILABLE_SCOPES
        assert "research:read" in AVAILABLE_SCOPES
        assert "research:create" in AVAILABLE_SCOPES

    def test_scopes_have_descriptions(self):
        """Test that all scopes have descriptions."""
        for scope, description in AVAILABLE_SCOPES.items():
            assert isinstance(description, str)
            assert len(description) > 0


class TestGenerateApiKey:
    """Tests for generate_api_key function."""

    def test_generate_api_key_format(self):
        """Test generated key has correct format."""
        full_key, key_prefix, key_hash = generate_api_key()
        assert full_key.startswith("si_")
        assert len(full_key) > 10

    def test_generate_api_key_returns_tuple(self):
        """Test generate_api_key returns tuple."""
        result = generate_api_key()
        assert isinstance(result, tuple)
        assert len(result) == 3

    def test_generate_api_key_prefix_correct(self):
        """Test key prefix is correct."""
        full_key, key_prefix, key_hash = generate_api_key()
        assert full_key.startswith(key_prefix)

    def test_generate_api_key_uniqueness(self):
        """Test each generated key is unique."""
        keys = [generate_api_key()[0] for _ in range(100)]
        assert len(set(keys)) == 100


class TestHashApiKey:
    """Tests for hash_api_key function."""

    def test_hash_api_key_returns_string(self):
        """Test hash returns a string."""
        key = "si_test_key_123"
        hashed = hash_api_key(key)
        assert isinstance(hashed, str)

    def test_hash_api_key_deterministic(self):
        """Test same key produces same hash."""
        key = "si_test_key_123"
        hash1 = hash_api_key(key)
        hash2 = hash_api_key(key)
        assert hash1 == hash2

    def test_hash_api_key_different_keys(self):
        """Test different keys produce different hashes."""
        key1 = "si_test_key_123"
        key2 = "si_test_key_456"
        assert hash_api_key(key1) != hash_api_key(key2)


class TestCheckScope:
    """Tests for check_scope function."""

    def test_check_scope_valid(self):
        """Test valid scope check returns True."""
        result = check_scope(
            key_scopes=["insights:read", "insights:write"],
            required_scope="insights:read",
        )
        assert result is True

    def test_check_scope_invalid(self):
        """Test invalid scope check returns False."""
        result = check_scope(
            key_scopes=["insights:read"],
            required_scope="research:create",
        )
        assert result is False

    def test_check_scope_wildcard(self):
        """Test wildcard scope grants access."""
        result = check_scope(
            key_scopes=["insights:*"],
            required_scope="insights:write",
        )
        assert result is True

    def test_check_scope_no_match(self):
        """Test no match returns False."""
        result = check_scope(
            key_scopes=["export:read"],
            required_scope="insights:read",
        )
        assert result is False


class TestGetMissingScopes:
    """Tests for get_missing_scopes function."""

    def test_no_missing_scopes(self):
        """Test no missing scopes when all present."""
        missing = get_missing_scopes(
            key_scopes=["insights:read", "insights:write"],
            required_scopes=["insights:read"],
        )
        assert missing == []

    def test_missing_scopes(self):
        """Test returns missing scopes."""
        missing = get_missing_scopes(
            key_scopes=["insights:read"],
            required_scopes=["insights:read", "research:create"],
        )
        assert "research:create" in missing

    def test_all_missing(self):
        """Test all missing when none present."""
        missing = get_missing_scopes(
            key_scopes=[],
            required_scopes=["insights:read", "insights:write"],
        )
        assert len(missing) == 2


class TestCreateApiKey:
    """Tests for create_api_key function."""

    @pytest.mark.asyncio
    async def test_create_api_key_returns_dict(self):
        """Test create_api_key returns key data dict."""
        result = await create_api_key(
            user_id=uuid4(),
            name="Test Key",
            scopes=["insights:read"],
        )
        assert "key" in result
        assert "key_prefix" in result
        assert "key_hash" in result
        assert "name" in result
        assert "scopes" in result

    @pytest.mark.asyncio
    async def test_create_api_key_with_expiration(self):
        """Test create_api_key with expiration."""
        result = await create_api_key(
            user_id=uuid4(),
            name="Test Key",
            scopes=["insights:read"],
            expires_in_days=30,
        )
        assert "expires_at" in result
        assert result["expires_at"] is not None

    @pytest.mark.asyncio
    async def test_create_api_key_prefix(self):
        """Test key prefix is first 15 chars."""
        result = await create_api_key(
            user_id=uuid4(),
            name="Test Key",
            scopes=["insights:read"],
        )
        assert result["key"].startswith(result["key_prefix"])
        assert len(result["key_prefix"]) == 15


class TestValidateApiKey:
    """Tests for validate_api_key function."""

    @pytest.mark.asyncio
    async def test_validate_api_key_returns_dict(self):
        """Test validate_api_key returns validation result."""
        result = await validate_api_key(key="si_test_key_123")
        assert result is not None
        assert "key_hash" in result

    @pytest.mark.asyncio
    async def test_validate_api_key_invalid_format(self):
        """Test validate_api_key rejects invalid format."""
        result = await validate_api_key(key="invalid_key")
        assert result is None

    @pytest.mark.asyncio
    async def test_validate_api_key_empty(self):
        """Test validate_api_key rejects empty key."""
        result = await validate_api_key(key="")
        assert result is None


class TestCheckApiKeyRateLimit:
    """Tests for check_api_key_rate_limit function."""

    @pytest.mark.asyncio
    async def test_check_rate_limit_returns_dict(self):
        """Test rate limit check returns result dict."""
        result = await check_api_key_rate_limit(
            key_id=str(uuid4()),
            user_tier="free",
        )
        assert isinstance(result, dict)
        assert "allowed" in result


class TestRecordApiKeyUsage:
    """Tests for record_api_key_usage function."""

    @pytest.mark.asyncio
    async def test_record_usage_returns_dict(self):
        """Test record usage returns result dict."""
        result = await record_api_key_usage(
            key_id=str(uuid4()),
            endpoint="/api/insights",
            method="GET",
            status_code=200,
            response_time_ms=45,
        )
        assert "api_key_id" in result
        assert "endpoint" in result
        assert "created_at" in result


class TestRevokeApiKey:
    """Tests for revoke_api_key function."""

    @pytest.mark.asyncio
    async def test_revoke_api_key_returns_dict(self):
        """Test revoke returns result dict."""
        result = await revoke_api_key(key_id=uuid4())
        assert "key_id" in result
        assert "revoked_at" in result
        assert result["is_active"] is False

    @pytest.mark.asyncio
    async def test_revoke_api_key_with_reason(self):
        """Test revoke includes reason."""
        result = await revoke_api_key(
            key_id=uuid4(),
            reason="Security concern",
        )
        assert result["revoked_reason"] == "Security concern"
