"""Tenants API Routes - Phase 7.3.

Endpoints for multi-tenancy and white-label features.
"""

import logging
from typing import Any
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, get_db, require_admin
from app.core.config import settings
from app.models import User
from app.models.tenant import Tenant, TenantUser
from app.services.tenant_service import (
    configure_custom_domain,
    generate_tenant_slug,
    get_tenant_css_variables,
    validate_subdomain,
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
# Helpers
# ============================================================


def _tenant_to_response(tenant: Tenant) -> TenantResponse:
    """Convert a Tenant model to response."""
    return TenantResponse(
        id=str(tenant.id),
        name=tenant.name,
        slug=tenant.slug,
        subdomain=tenant.subdomain,
        custom_domain=tenant.custom_domain,
        custom_domain_verified=tenant.custom_domain_verified,
        app_name=tenant.app_name,
        logo_url=tenant.logo_url,
        primary_color=tenant.primary_color,
        status=tenant.status,
        created_at=tenant.created_at.isoformat(),
    )


def _tenant_to_branding_response(tenant: Tenant) -> TenantBrandingResponse:
    """Convert a Tenant model to branding response."""
    tenant_data = {
        "primary_color": tenant.primary_color or "#3B82F6",
        "secondary_color": tenant.secondary_color or "#10B981",
        "accent_color": tenant.accent_color or "#F59E0B",
        "app_name": tenant.app_name or "StartInsight",
    }
    return TenantBrandingResponse(
        logo_url=tenant.logo_url,
        favicon_url=tenant.favicon_url,
        primary_color=tenant.primary_color or "#3B82F6",
        secondary_color=tenant.secondary_color or "#10B981",
        accent_color=tenant.accent_color or "#F59E0B",
        app_name=tenant.app_name or "StartInsight",
        tagline=tenant.tagline or "AI-powered startup insights",
        css_variables=get_tenant_css_variables(tenant_data),
    )


async def _get_tenant_with_access(
    tenant_id: UUID,
    user_id: UUID,
    db: AsyncSession,
) -> Tenant:
    """Get tenant and verify user has access. Raises 404/403."""
    tenant_result = await db.execute(select(Tenant).where(Tenant.id == tenant_id))
    tenant = tenant_result.scalar_one_or_none()
    if not tenant:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Tenant not found",
        )

    membership = await db.execute(
        select(TenantUser).where(
            TenantUser.tenant_id == tenant_id,
            TenantUser.user_id == user_id,
            TenantUser.status == "active",
        )
    )
    if not membership.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have access to this tenant",
        )

    return tenant


async def _require_tenant_admin(
    tenant_id: UUID,
    user_id: UUID,
    db: AsyncSession,
) -> Tenant:
    """Get tenant and require admin/owner role."""
    tenant_result = await db.execute(select(Tenant).where(Tenant.id == tenant_id))
    tenant = tenant_result.scalar_one_or_none()
    if not tenant:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Tenant not found",
        )

    membership_result = await db.execute(
        select(TenantUser).where(
            TenantUser.tenant_id == tenant_id,
            TenantUser.user_id == user_id,
            TenantUser.status == "active",
        )
    )
    membership = membership_result.scalar_one_or_none()
    if not membership or membership.role not in ("owner", "admin"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only tenant owners and admins can perform this action",
        )

    return tenant


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
    slug = generate_tenant_slug(request.name)

    # Validate subdomain
    subdomain = request.subdomain or slug
    if request.subdomain:
        is_valid, error = validate_subdomain(request.subdomain)
        if not is_valid:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=error or "Invalid subdomain",
            )

    # Check subdomain uniqueness
    existing = await db.execute(
        select(Tenant).where(Tenant.subdomain == subdomain)
    )
    if existing.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Subdomain is already taken",
        )

    tenant = Tenant(
        name=request.name,
        slug=slug,
        subdomain=subdomain,
        owner_id=current_user.id,
        status="active",
        features={
            "enable_research": True,
            "enable_teams": True,
            "enable_export": True,
            "enable_api": False,
            "enable_white_label": False,
        },
        max_users=settings.default_max_users,
        max_teams=settings.default_max_teams,
        max_api_keys=settings.default_max_api_keys,
    )
    db.add(tenant)
    await db.flush()

    # Add owner as first user
    tenant_user = TenantUser(
        tenant_id=tenant.id,
        user_id=current_user.id,
        role="owner",
        status="active",
    )
    db.add(tenant_user)
    await db.commit()
    await db.refresh(tenant)

    logger.info(f"Tenant created: {request.name} (slug: {slug}) by {current_user.id}")

    return _tenant_to_response(tenant)


@router.get("/current", response_model=TenantResponse)
async def get_current_tenant(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> TenantResponse:
    """
    Get current user's tenant.

    Requires authentication.
    """
    query = (
        select(Tenant)
        .join(TenantUser, TenantUser.tenant_id == Tenant.id)
        .where(
            TenantUser.user_id == current_user.id,
            TenantUser.status == "active",
        )
        .order_by(Tenant.created_at.desc())
        .limit(1)
    )
    result = await db.execute(query)
    tenant = result.scalar_one_or_none()

    if not tenant:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No tenant found for user",
        )

    return _tenant_to_response(tenant)


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
    tenant = await _get_tenant_with_access(tenant_id, current_user.id, db)
    return _tenant_to_response(tenant)


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
    tenant = await _get_tenant_with_access(tenant_id, current_user.id, db)
    return _tenant_to_branding_response(tenant)


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
    tenant = await _require_tenant_admin(tenant_id, current_user.id, db)

    if request.logo_url is not None:
        tenant.logo_url = request.logo_url
    if request.favicon_url is not None:
        tenant.favicon_url = request.favicon_url
    if request.primary_color is not None:
        tenant.primary_color = request.primary_color
    if request.secondary_color is not None:
        tenant.secondary_color = request.secondary_color
    if request.accent_color is not None:
        tenant.accent_color = request.accent_color
    if request.app_name is not None:
        tenant.app_name = request.app_name
    if request.tagline is not None:
        tenant.tagline = request.tagline

    await db.commit()
    await db.refresh(tenant)

    logger.info(f"Tenant branding updated: {tenant_id}")

    return _tenant_to_branding_response(tenant)


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
    tenant = await _require_tenant_admin(tenant_id, current_user.id, db)

    try:
        result = await configure_custom_domain(tenant_id, request.custom_domain)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid domain format. Please provide a valid domain name.",
        )

    # Save domain to tenant
    tenant.custom_domain = result["custom_domain"]
    tenant.custom_domain_verified = False
    await db.commit()

    return DomainConfigResponse(
        custom_domain=result["custom_domain"],
        verified=result["custom_domain_verified"],
        dns_instructions=result["dns_instructions"],
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
    tenant = await _require_tenant_admin(tenant_id, current_user.id, db)

    if not tenant.custom_domain:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No custom domain configured for this tenant",
        )

    result = await verify_custom_domain(tenant_id, tenant.custom_domain)

    if result["verified"]:
        tenant.custom_domain_verified = True
        await db.commit()

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
    tenant = await _require_tenant_admin(tenant_id, current_user.id, db)

    tenant.custom_domain = None
    tenant.custom_domain_verified = False
    await db.commit()

    logger.info(f"Custom domain removed for tenant {tenant_id}")


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
    result = await db.execute(
        select(Tenant).where(
            Tenant.subdomain == subdomain,
            Tenant.status == "active",
        )
    )
    tenant = result.scalar_one_or_none()

    if not tenant:
        # Return default branding
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

    return _tenant_to_branding_response(tenant)


# ============================================================
# Admin Endpoints
# ============================================================


@router.get("/admin/list")
async def list_all_tenants(
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    current_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """
    List all tenants (admin only).

    Requires admin authentication.
    """
    total = await db.scalar(select(func.count(Tenant.id))) or 0

    query = (
        select(Tenant)
        .order_by(Tenant.created_at.desc())
        .limit(limit)
        .offset(offset)
    )
    result = await db.execute(query)
    tenants = result.scalars().all()

    return {
        "tenants": [
            {
                "id": str(t.id),
                "name": t.name,
                "slug": t.slug,
                "subdomain": t.subdomain,
                "status": t.status,
                "owner_id": str(t.owner_id) if t.owner_id else None,
                "created_at": t.created_at.isoformat(),
            }
            for t in tenants
        ],
        "total": total,
        "limit": limit,
        "offset": offset,
    }


@router.patch("/admin/{tenant_id}/status")
async def update_tenant_status(
    tenant_id: UUID,
    new_status: str = Query(..., alias="status"),
    current_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
) -> dict[str, str]:
    """
    Update tenant status (admin only).

    Requires admin authentication.
    Can suspend or reactivate tenants.
    """
    valid_statuses = ["active", "suspended", "pending", "trial"]
    if new_status not in valid_statuses:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid status. Must be one of: {valid_statuses}",
        )

    tenant_result = await db.execute(select(Tenant).where(Tenant.id == tenant_id))
    tenant = tenant_result.scalar_one_or_none()

    if not tenant:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Tenant not found",
        )

    tenant.status = new_status
    await db.commit()

    logger.info(f"Tenant {tenant_id} status updated to {new_status} by admin {current_user.id}")

    return {"tenant_id": str(tenant_id), "status": new_status}
