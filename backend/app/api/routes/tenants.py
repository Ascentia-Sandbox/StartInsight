"""Tenants API Routes - Phase 7.3.

Endpoints for multi-tenancy and white-label features.
"""

import logging
from typing import Any
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, get_db, require_admin
from app.models import Tenant, User
from app.services.tenant_service import (
    configure_custom_domain,
    create_tenant,
    get_tenant_css_variables,
    resolve_tenant_from_host,
    update_tenant_branding,
    verify_custom_domain,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/tenants", tags=["Tenants"])


# ============================================================
# Request/Response Schemas
# ============================================================


class TenantCreateRequest(BaseModel):
    """Tenant creation request."""

    name: str = Field(..., min_length=2, max_length=100)
    subdomain: str | None = Field(None, min_length=3, max_length=50)


class TenantBrandingRequest(BaseModel):
    """Tenant branding update request."""

    logo_url: str | None = Field(None, max_length=500)
    favicon_url: str | None = Field(None, max_length=500)
    primary_color: str | None = Field(None, pattern=r"^#[0-9A-Fa-f]{6}$")
    secondary_color: str | None = Field(None, pattern=r"^#[0-9A-Fa-f]{6}$")
    accent_color: str | None = Field(None, pattern=r"^#[0-9A-Fa-f]{6}$")
    app_name: str | None = Field(None, max_length=100)
    tagline: str | None = Field(None, max_length=255)


class TenantDomainRequest(BaseModel):
    """Custom domain configuration request."""

    custom_domain: str = Field(..., max_length=255)


class TenantResponse(BaseModel):
    """Tenant response."""

    id: str
    name: str
    slug: str
    subdomain: str | None
    custom_domain: str | None
    custom_domain_verified: bool
    app_name: str | None
    logo_url: str | None
    primary_color: str | None
    status: str
    created_at: str


class TenantBrandingResponse(BaseModel):
    """Tenant branding response."""

    logo_url: str | None
    favicon_url: str | None
    primary_color: str | None
    secondary_color: str | None
    accent_color: str | None
    app_name: str | None
    tagline: str | None
    css_variables: str


class DomainConfigResponse(BaseModel):
    """Domain configuration response."""

    custom_domain: str
    verified: bool
    dns_instructions: dict[str, Any]


# ============================================================
# Tenant CRUD Endpoints
# ============================================================


@router.post("", response_model=TenantResponse, status_code=status.HTTP_201_CREATED)
async def create_new_tenant(
    request: TenantCreateRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> TenantResponse:
    """
    Create a new tenant.

    Requires authentication. Creates a white-label instance.
    Enterprise feature - requires enterprise subscription.
    """
    try:
        tenant_data = await create_tenant(
            name=request.name,
            owner_id=current_user.id,
            subdomain=request.subdomain,
        )

        # TODO: Save to database

        return TenantResponse(
            id=tenant_data["slug"],
            name=tenant_data["name"],
            slug=tenant_data["slug"],
            subdomain=tenant_data["subdomain"],
            custom_domain=None,
            custom_domain_verified=False,
            app_name=None,
            logo_url=None,
            primary_color=None,
            status=tenant_data["status"],
            created_at=tenant_data["created_at"],
        )

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


@router.get("/current", response_model=TenantResponse)
async def get_current_tenant(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> TenantResponse:
    """
    Get current user's tenant.

    Requires authentication.
    """
    # TODO: Query database for user's tenant
    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail="No tenant found for user",
    )


@router.get("/{tenant_id}", response_model=TenantResponse)
async def get_tenant(
    tenant_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> TenantResponse:
    """
    Get tenant details.

    Requires authentication. User must be tenant member.
    """
    # TODO: Query database
    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail="Tenant not found",
    )


# ============================================================
# Branding Endpoints
# ============================================================


@router.get("/{tenant_id}/branding", response_model=TenantBrandingResponse)
async def get_tenant_branding(
    tenant_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> TenantBrandingResponse:
    """
    Get tenant branding configuration.

    Requires authentication.
    """
    # TODO: Query database
    # Return default branding for now
    return TenantBrandingResponse(
        logo_url=None,
        favicon_url=None,
        primary_color="#3B82F6",
        secondary_color="#10B981",
        accent_color="#F59E0B",
        app_name="StartInsight",
        tagline="AI-powered startup insights",
        css_variables=get_tenant_css_variables({}),
    )


@router.patch("/{tenant_id}/branding", response_model=TenantBrandingResponse)
async def update_branding(
    tenant_id: UUID,
    request: TenantBrandingRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> TenantBrandingResponse:
    """
    Update tenant branding.

    Requires authentication. User must be tenant owner or admin.
    """
    from app.services.tenant_service import TenantBrandingUpdate

    branding_update = TenantBrandingUpdate(**request.model_dump(exclude_none=True))
    result = await update_tenant_branding(tenant_id, branding_update)

    # Build CSS variables
    tenant_data = {
        "primary_color": request.primary_color or "#3B82F6",
        "secondary_color": request.secondary_color or "#10B981",
        "accent_color": request.accent_color or "#F59E0B",
        "app_name": request.app_name or "StartInsight",
    }

    return TenantBrandingResponse(
        logo_url=request.logo_url,
        favicon_url=request.favicon_url,
        primary_color=request.primary_color,
        secondary_color=request.secondary_color,
        accent_color=request.accent_color,
        app_name=request.app_name,
        tagline=request.tagline,
        css_variables=get_tenant_css_variables(tenant_data),
    )


# ============================================================
# Custom Domain Endpoints
# ============================================================


@router.post("/{tenant_id}/domain", response_model=DomainConfigResponse)
async def configure_domain(
    tenant_id: UUID,
    request: TenantDomainRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> DomainConfigResponse:
    """
    Configure custom domain for tenant.

    Requires authentication. User must be tenant owner.
    Returns DNS instructions for domain verification.
    """
    try:
        result = await configure_custom_domain(tenant_id, request.custom_domain)

        return DomainConfigResponse(
            custom_domain=result["custom_domain"],
            verified=result["custom_domain_verified"],
            dns_instructions=result["dns_instructions"],
        )

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


@router.post("/{tenant_id}/domain/verify")
async def verify_domain(
    tenant_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """
    Verify custom domain DNS configuration.

    Requires authentication. Checks if DNS is properly configured.
    """
    # TODO: Get domain from database
    result = await verify_custom_domain(tenant_id, "example.com")

    return {
        "domain": result["domain"],
        "verified": result["verified"],
        "ssl_status": result["ssl_status"],
    }


@router.delete("/{tenant_id}/domain", status_code=status.HTTP_204_NO_CONTENT)
async def remove_custom_domain(
    tenant_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> None:
    """
    Remove custom domain configuration.

    Requires authentication. Reverts to subdomain access.
    """
    # TODO: Remove domain from database
    pass


# ============================================================
# Public Tenant Resolution (No Auth)
# ============================================================


@router.get("/resolve/{subdomain}", response_model=TenantBrandingResponse)
async def resolve_tenant_branding(
    subdomain: str,
    db: AsyncSession = Depends(get_db),
) -> TenantBrandingResponse:
    """
    Resolve tenant branding by subdomain.

    Public endpoint - no authentication required.
    Used by frontend to load correct branding.
    """
    # TODO: Query database for tenant by subdomain
    # Return default branding for now
    return TenantBrandingResponse(
        logo_url=None,
        favicon_url=None,
        primary_color="#3B82F6",
        secondary_color="#10B981",
        accent_color="#F59E0B",
        app_name="StartInsight",
        tagline="AI-powered startup insights",
        css_variables=get_tenant_css_variables({}),
    )


# ============================================================
# Admin Endpoints
# ============================================================


@router.get("/admin/list")
async def list_all_tenants(
    current_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """
    List all tenants (admin only).

    Requires admin authentication.
    """
    # TODO: Query all tenants
    return {
        "tenants": [],
        "total": 0,
    }


@router.patch("/admin/{tenant_id}/status")
async def update_tenant_status(
    tenant_id: UUID,
    status: str,
    current_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
) -> dict[str, str]:
    """
    Update tenant status (admin only).

    Requires admin authentication.
    Can suspend or reactivate tenants.
    """
    valid_statuses = ["active", "suspended", "pending", "trial"]
    if status not in valid_statuses:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid status. Must be one of: {valid_statuses}",
        )

    # TODO: Update tenant status in database
    return {"tenant_id": str(tenant_id), "status": status}
