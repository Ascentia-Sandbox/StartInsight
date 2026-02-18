"""API Keys Routes - Phase 7.2.

Endpoints for managing public API keys.
"""

import logging
from datetime import UTC, datetime, timedelta
from typing import Any
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, get_db
from app.models import User
from app.models.api_key import APIKey, APIKeyUsageLog
from app.services.api_key_service import (
    AVAILABLE_SCOPES,
    generate_api_key,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/keys", tags=["API Keys"])


# ============================================================
# Request/Response Schemas
# ============================================================


class APIKeyCreateRequest(BaseModel):
    """API key creation request."""

    name: str = Field(..., min_length=1, max_length=100)
    description: str | None = Field(None, max_length=500)
    scopes: list[str] = Field(default=["insights:read"])
    expires_in_days: int | None = Field(None, ge=1, le=365)


class APIKeyCreateResponse(BaseModel):
    """API key creation response (includes full key, shown only once)."""

    id: str
    name: str
    key: str  # Full key - only shown at creation!
    key_prefix: str
    scopes: list[str]
    rate_limit_per_hour: int
    expires_at: str | None
    created_at: str


class APIKeyPublicResponse(BaseModel):
    """API key public response (no full key)."""

    id: str
    name: str
    key_prefix: str
    description: str | None
    scopes: list[str]
    rate_limit_per_hour: int
    total_requests: int
    last_used_at: str | None
    is_active: bool
    expires_at: str | None
    created_at: str


class APIKeyListResponse(BaseModel):
    """List of API keys."""

    keys: list[APIKeyPublicResponse]
    total: int


class ScopesResponse(BaseModel):
    """Available scopes response."""

    scopes: dict[str, str]


# ============================================================
# Scopes Endpoint
# ============================================================


@router.get("/scopes", response_model=ScopesResponse)
async def list_available_scopes() -> ScopesResponse:
    """
    List available API key scopes.

    Public endpoint - no authentication required.
    """
    return ScopesResponse(scopes=AVAILABLE_SCOPES)


# ============================================================
# API Key CRUD Endpoints
# ============================================================


def _key_to_public_response(key: APIKey) -> APIKeyPublicResponse:
    """Convert an APIKey model to public response."""
    return APIKeyPublicResponse(
        id=str(key.id),
        name=key.name,
        key_prefix=key.key_prefix,
        description=key.description,
        scopes=key.scopes or [],
        rate_limit_per_hour=key.rate_limit_per_hour,
        total_requests=key.total_requests,
        last_used_at=key.last_used_at.isoformat() if key.last_used_at else None,
        is_active=key.is_active,
        expires_at=key.expires_at.isoformat() if key.expires_at else None,
        created_at=key.created_at.isoformat(),
    )


@router.post("", response_model=APIKeyCreateResponse, status_code=status.HTTP_201_CREATED)
async def create_new_api_key(
    request: APIKeyCreateRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> APIKeyCreateResponse:
    """
    Create a new API key.

    Requires authentication. The full API key is only shown once at creation.
    Store it securely - it cannot be retrieved again!
    """
    # Validate scopes
    invalid_scopes = [s for s in request.scopes if s not in AVAILABLE_SCOPES]
    if invalid_scopes:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid scopes: {invalid_scopes}",
        )

    # Generate key
    full_key, key_prefix, key_hash = generate_api_key()

    # Calculate expiration
    expires_at = None
    if request.expires_in_days:
        expires_at = datetime.now(UTC) + timedelta(days=request.expires_in_days)

    # Create database record
    api_key = APIKey(
        user_id=current_user.id,
        name=request.name,
        description=request.description,
        key_prefix=key_prefix,
        key_hash=key_hash,
        scopes=request.scopes,
        rate_limit_per_hour=100,
        rate_limit_per_day=1000,
        expires_at=expires_at,
        is_active=True,
    )
    db.add(api_key)
    await db.commit()
    await db.refresh(api_key)

    logger.info(f"API key created: {request.name} for user {current_user.id}")

    return APIKeyCreateResponse(
        id=str(api_key.id),
        name=api_key.name,
        key=full_key,
        key_prefix=api_key.key_prefix,
        scopes=api_key.scopes or [],
        rate_limit_per_hour=api_key.rate_limit_per_hour,
        expires_at=api_key.expires_at.isoformat() if api_key.expires_at else None,
        created_at=api_key.created_at.isoformat(),
    )


@router.get("", response_model=APIKeyListResponse)
async def list_api_keys(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> APIKeyListResponse:
    """
    List user's API keys.

    Requires authentication. Does not return full key values.
    """
    query = (
        select(APIKey)
        .where(APIKey.user_id == current_user.id)
        .order_by(APIKey.created_at.desc())
    )
    result = await db.execute(query)
    keys = result.scalars().all()

    count_query = select(func.count(APIKey.id)).where(APIKey.user_id == current_user.id)
    total = await db.scalar(count_query) or 0

    return APIKeyListResponse(
        keys=[_key_to_public_response(k) for k in keys],
        total=total,
    )


@router.get("/{key_id}", response_model=APIKeyPublicResponse)
async def get_api_key(
    key_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> APIKeyPublicResponse:
    """
    Get API key details.

    Requires authentication. Does not return full key value.
    """
    query = select(APIKey).where(APIKey.id == key_id, APIKey.user_id == current_user.id)
    result = await db.execute(query)
    key = result.scalar_one_or_none()

    if not key:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="API key not found",
        )

    return _key_to_public_response(key)


@router.delete("/{key_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_api_key(
    key_id: UUID,
    reason: str | None = Query(None, max_length=255),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> None:
    """
    Revoke an API key.

    Requires authentication. This action cannot be undone.
    """
    query = select(APIKey).where(APIKey.id == key_id, APIKey.user_id == current_user.id)
    result = await db.execute(query)
    key = result.scalar_one_or_none()

    if not key:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="API key not found",
        )

    key.is_active = False
    key.revoked_at = datetime.now(UTC)
    key.revoked_reason = reason
    await db.commit()

    logger.info(f"API key revoked: {key_id}")


@router.patch("/{key_id}/regenerate", response_model=APIKeyCreateResponse)
async def regenerate_api_key(
    key_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> APIKeyCreateResponse:
    """
    Regenerate an API key.

    Requires authentication. Creates a new key and revokes the old one.
    The new key is only shown once - store it securely!
    """
    query = select(APIKey).where(APIKey.id == key_id, APIKey.user_id == current_user.id)
    result = await db.execute(query)
    old_key = result.scalar_one_or_none()

    if not old_key:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="API key not found",
        )

    # Revoke old key
    old_key.is_active = False
    old_key.revoked_at = datetime.now(UTC)
    old_key.revoked_reason = "Regenerated"

    # Generate new key with same settings
    full_key, key_prefix, key_hash = generate_api_key()
    new_key = APIKey(
        user_id=current_user.id,
        name=old_key.name,
        description=old_key.description,
        key_prefix=key_prefix,
        key_hash=key_hash,
        scopes=old_key.scopes,
        rate_limit_per_hour=old_key.rate_limit_per_hour,
        rate_limit_per_day=old_key.rate_limit_per_day,
        expires_at=old_key.expires_at,
        is_active=True,
    )
    db.add(new_key)
    await db.commit()
    await db.refresh(new_key)

    logger.info(f"API key regenerated: {key_id} -> {new_key.id}")

    return APIKeyCreateResponse(
        id=str(new_key.id),
        name=new_key.name,
        key=full_key,
        key_prefix=new_key.key_prefix,
        scopes=new_key.scopes or [],
        rate_limit_per_hour=new_key.rate_limit_per_hour,
        expires_at=new_key.expires_at.isoformat() if new_key.expires_at else None,
        created_at=new_key.created_at.isoformat(),
    )


# ============================================================
# Usage Statistics
# ============================================================


@router.get("/{key_id}/usage")
async def get_api_key_usage(
    key_id: UUID,
    days: int = Query(default=7, ge=1, le=30),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """
    Get API key usage statistics.

    Requires authentication.
    """
    # Verify ownership
    key_query = select(APIKey).where(APIKey.id == key_id, APIKey.user_id == current_user.id)
    result = await db.execute(key_query)
    key = result.scalar_one_or_none()

    if not key:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="API key not found",
        )

    # Query usage logs for the period
    since = datetime.now(UTC) - timedelta(days=days)
    logs_query = (
        select(APIKeyUsageLog)
        .where(APIKeyUsageLog.api_key_id == key_id, APIKeyUsageLog.created_at >= since)
        .order_by(APIKeyUsageLog.created_at.desc())
    )
    logs_result = await db.execute(logs_query)
    logs = logs_result.scalars().all()

    total = len(logs)
    successful = sum(1 for log in logs if 200 <= log.status_code < 400)
    failed = total - successful
    avg_time = sum(log.response_time_ms for log in logs) / max(total, 1)

    return {
        "key_id": str(key_id),
        "period_days": days,
        "total_requests": total,
        "successful_requests": successful,
        "failed_requests": failed,
        "avg_response_time_ms": round(avg_time, 1),
        "requests_by_endpoint": {},
        "requests_by_day": [],
    }


# ============================================================
# Rate Limit Info
# ============================================================


@router.get("/{key_id}/limits")
async def get_api_key_limits(
    key_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """
    Get API key rate limit status.

    Requires authentication.
    """
    key_query = select(APIKey).where(APIKey.id == key_id, APIKey.user_id == current_user.id)
    result = await db.execute(key_query)
    key = result.scalar_one_or_none()

    if not key:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="API key not found",
        )

    return {
        "key_id": str(key_id),
        "rate_limit_per_hour": key.rate_limit_per_hour,
        "rate_limit_per_day": key.rate_limit_per_day,
        "requests_this_hour": key.requests_this_hour,
        "requests_this_day": key.requests_this_day,
        "remaining_this_hour": key.rate_limit_per_hour - key.requests_this_hour,
        "remaining_this_day": key.rate_limit_per_day - key.requests_this_day,
    }
