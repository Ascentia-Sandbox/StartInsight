"""API Key Service - Phase 7.2 Public API.

Manages API key creation, validation, and usage tracking.
"""

import hashlib
import logging
import secrets
from datetime import datetime, timedelta
from typing import Any
from uuid import UUID

from pydantic import BaseModel, Field

from app.core.config import settings

# TODO: Rate limiting handled by SlowAPI globally, not custom service
# from app.services.rate_limiter import check_rate_limit, increment_usage

logger = logging.getLogger(__name__)


# ============================================================
# API Key Schemas
# ============================================================


class APIKeyCreate(BaseModel):
    """Schema for API key creation."""

    name: str = Field(..., min_length=1, max_length=100)
    description: str | None = Field(None, max_length=500)
    scopes: list[str] = Field(default_factory=lambda: ["insights:read"])
    expires_in_days: int | None = Field(None, ge=1, le=365)


class APIKeyResponse(BaseModel):
    """Response with generated API key (only shown once)."""

    id: str
    name: str
    key: str  # Full key, only shown at creation
    key_prefix: str  # For display
    scopes: list[str]
    rate_limit_per_hour: int
    expires_at: str | None
    created_at: str


class APIKeyPublicResponse(BaseModel):
    """Public response without full key."""

    id: str
    name: str
    key_prefix: str
    scopes: list[str]
    rate_limit_per_hour: int
    total_requests: int
    last_used_at: str | None
    is_active: bool
    created_at: str


# ============================================================
# Available Scopes
# ============================================================


AVAILABLE_SCOPES = {
    "insights:read": "Read public insights",
    "insights:write": "Save and rate insights",
    "research:read": "Read research analyses",
    "research:create": "Create new research analyses",
    "export:read": "Export insights and analyses",
    "feed:read": "Subscribe to real-time feed",
    "user:read": "Read own user profile",
    "admin:read": "Read admin data (requires admin)",
}


def validate_scopes(scopes: list[str]) -> list[str]:
    """Validate and filter to allowed scopes."""
    return [s for s in scopes if s in AVAILABLE_SCOPES]


# ============================================================
# Key Generation
# ============================================================


def generate_api_key() -> tuple[str, str, str]:
    """
    Generate a new API key.

    Returns:
        tuple: (full_key, key_prefix, key_hash)
    """
    # Generate 32-byte random key (64 hex chars)
    key_bytes = secrets.token_bytes(32)
    full_key = f"si_{key_bytes.hex()}"  # si_ prefix for StartInsight

    # Prefix for display (first 12 chars after prefix)
    key_prefix = full_key[:15]  # "si_" + 12 chars

    # Hash for storage
    key_hash = hash_api_key(full_key)

    return full_key, key_prefix, key_hash


def hash_api_key(key: str) -> str:
    """Create secure hash of API key."""
    return hashlib.sha256(key.encode()).hexdigest()


# ============================================================
# API Key Service Functions
# ============================================================


async def create_api_key(
    user_id: UUID,
    name: str,
    description: str | None = None,
    scopes: list[str] | None = None,
    expires_in_days: int | None = None,
) -> dict[str, Any]:
    """
    Create a new API key for a user.

    Args:
        user_id: User UUID
        name: Key name for identification
        description: Optional description
        scopes: Permissions for this key
        expires_in_days: Optional expiration

    Returns:
        API key data including the full key (only time it's visible)
    """
    # Validate scopes
    validated_scopes = validate_scopes(scopes or ["insights:read"])

    # Generate key
    full_key, key_prefix, key_hash = generate_api_key()

    # Calculate expiration
    expires_at = None
    if expires_in_days:
        expires_at = datetime.now() + timedelta(days=expires_in_days)

    # Determine rate limit based on user tier
    # In production, this would check the user's subscription
    rate_limit_per_hour = settings.public_api_rate_limit

    key_data = {
        "user_id": str(user_id),
        "name": name,
        "description": description,
        "key": full_key,  # Only included at creation
        "key_prefix": key_prefix,
        "key_hash": key_hash,
        "scopes": validated_scopes,
        "rate_limit_per_hour": rate_limit_per_hour,
        "rate_limit_per_day": rate_limit_per_hour * 10,
        "is_active": True,
        "expires_at": expires_at.isoformat() if expires_at else None,
        "created_at": datetime.now().isoformat(),
    }

    logger.info(f"API key created: {name} for user {user_id}")
    return key_data


async def validate_api_key(key: str) -> dict[str, Any] | None:
    """
    Validate an API key and return its data.

    Args:
        key: Full API key

    Returns:
        Key data if valid, None otherwise
    """
    if not key or not key.startswith("si_"):
        return None

    key_hash = hash_api_key(key)

    # In production, this would query the database
    # For now, return a mock validation result
    # The actual implementation would be in the route handler

    logger.debug(f"API key validated: {key[:15]}...")
    return {
        "key_hash": key_hash,
        "validated_at": datetime.now().isoformat(),
    }


async def check_api_key_rate_limit(
    key_id: str,
    user_tier: str = "free",
) -> dict[str, Any]:
    """
    Check rate limit for API key.

    Args:
        key_id: API key ID
        user_tier: User's subscription tier

    Returns:
        Rate limit status
    """
    # TODO: Rate limiting handled by SlowAPI globally
    # result = await check_rate_limit(
    #     identifier=f"apikey:{key_id}",
    #     tier=user_tier,
    #     limit_type="api_calls_per_hour",
    # )

    # Return mock result for now (rate limiting done at route level)
    return {"allowed": True, "remaining": 1000, "reset_at": None}


async def record_api_key_usage(
    key_id: str,
    endpoint: str,
    method: str,
    status_code: int,
    response_time_ms: int,
    ip_address: str | None = None,
    user_agent: str | None = None,
) -> dict[str, Any]:
    """
    Record API key usage for analytics and rate limiting.

    Args:
        key_id: API key ID
        endpoint: Requested endpoint
        method: HTTP method
        status_code: Response status code
        response_time_ms: Response time in milliseconds
        ip_address: Client IP
        user_agent: Client user agent

    Returns:
        Usage record data
    """
    # TODO: Usage tracking handled by SlowAPI globally
    # await increment_usage(f"apikey:{key_id}", "requests")

    usage_data = {
        "api_key_id": key_id,
        "endpoint": endpoint,
        "method": method,
        "status_code": status_code,
        "response_time_ms": response_time_ms,
        "ip_address": ip_address,
        "user_agent": user_agent,
        "created_at": datetime.now().isoformat(),
    }

    logger.debug(f"API key usage recorded: {key_id} - {method} {endpoint}")
    return usage_data


async def revoke_api_key(
    key_id: UUID,
    reason: str | None = None,
) -> dict[str, Any]:
    """
    Revoke an API key.

    Args:
        key_id: API key ID to revoke
        reason: Optional revocation reason

    Returns:
        Revocation result
    """
    revocation_data = {
        "key_id": str(key_id),
        "revoked_at": datetime.now().isoformat(),
        "revoked_reason": reason,
        "is_active": False,
    }

    logger.info(f"API key revoked: {key_id} - {reason}")
    return revocation_data


# ============================================================
# Scope Checking
# ============================================================


def check_scope(key_scopes: list[str], required_scope: str) -> bool:
    """
    Check if API key has required scope.

    Args:
        key_scopes: Scopes assigned to the key
        required_scope: Required scope for the operation

    Returns:
        True if scope is present
    """
    # Check exact match
    if required_scope in key_scopes:
        return True

    # Check wildcard (e.g., "insights:*" covers "insights:read")
    scope_parts = required_scope.split(":")
    if len(scope_parts) == 2:
        wildcard = f"{scope_parts[0]}:*"
        if wildcard in key_scopes:
            return True

    return False


def get_missing_scopes(key_scopes: list[str], required_scopes: list[str]) -> list[str]:
    """Get list of missing scopes."""
    return [s for s in required_scopes if not check_scope(key_scopes, s)]
