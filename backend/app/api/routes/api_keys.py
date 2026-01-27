"""API Keys Routes - Phase 7.2.

Endpoints for managing public API keys.
"""

import logging
from typing import Any
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, get_db
from app.models import User
from app.services.api_key_service import (
    AVAILABLE_SCOPES,
    create_api_key,
    revoke_api_key,
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

    key_data = await create_api_key(
        user_id=current_user.id,
        name=request.name,
        description=request.description,
        scopes=request.scopes,
        expires_in_days=request.expires_in_days,
    )

    # TODO: Save to database

    return APIKeyCreateResponse(
        id=key_data["key_prefix"],  # Use prefix as temp ID
        name=key_data["name"],
        key=key_data["key"],  # Full key - shown only once!
        key_prefix=key_data["key_prefix"],
        scopes=key_data["scopes"],
        rate_limit_per_hour=key_data["rate_limit_per_hour"],
        expires_at=key_data.get("expires_at"),
        created_at=key_data["created_at"],
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
    # TODO: Query database
    return APIKeyListResponse(keys=[], total=0)


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
    # TODO: Query database
    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail="API key not found",
    )


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
    result = await revoke_api_key(key_id=key_id, reason=reason)
    # TODO: Update database
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
    # TODO: Fetch existing key, create new key, revoke old
    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail="API key not found",
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
    # TODO: Query usage logs
    return {
        "key_id": str(key_id),
        "period_days": days,
        "total_requests": 0,
        "successful_requests": 0,
        "failed_requests": 0,
        "avg_response_time_ms": 0,
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
    # TODO: Check rate limit status
    return {
        "key_id": str(key_id),
        "rate_limit_per_hour": 100,
        "rate_limit_per_day": 1000,
        "requests_this_hour": 0,
        "requests_this_day": 0,
        "remaining_this_hour": 100,
        "remaining_this_day": 1000,
        "reset_at_hour": "",
        "reset_at_day": "",
    }
