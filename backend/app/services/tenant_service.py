"""Tenant Service - Phase 7.3 Multi-tenancy & White-label.

Manages tenant creation, branding, and domain configuration.
"""

import logging
import re
import secrets
from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, Field

from app.core.config import settings

logger = logging.getLogger(__name__)


# ============================================================
# Tenant Schemas
# ============================================================


class TenantCreate(BaseModel):
    """Schema for tenant creation."""

    name: str = Field(..., min_length=2, max_length=100)
    subdomain: str | None = Field(None, min_length=3, max_length=50)


class TenantBrandingUpdate(BaseModel):
    """Schema for updating tenant branding."""

    logo_url: str | None = Field(None, max_length=500)
    favicon_url: str | None = Field(None, max_length=500)
    primary_color: str | None = Field(None, pattern=r"^#[0-9A-Fa-f]{6}$")
    secondary_color: str | None = Field(None, pattern=r"^#[0-9A-Fa-f]{6}$")
    accent_color: str | None = Field(None, pattern=r"^#[0-9A-Fa-f]{6}$")
    app_name: str | None = Field(None, max_length=100)
    tagline: str | None = Field(None, max_length=255)


class TenantDomainConfig(BaseModel):
    """Schema for domain configuration."""

    custom_domain: str | None = Field(None, max_length=255)
    support_email: str | None = Field(None, max_length=255)
    terms_url: str | None = Field(None, max_length=500)
    privacy_url: str | None = Field(None, max_length=500)


# ============================================================
# Tenant Service Functions
# ============================================================


def generate_tenant_slug(name: str) -> str:
    """Generate a URL-safe slug from tenant name."""
    # Convert to lowercase, replace spaces with hyphens
    slug = name.lower().strip()
    slug = re.sub(r"[^\w\s-]", "", slug)
    slug = re.sub(r"[\s_]+", "-", slug)
    slug = re.sub(r"-+", "-", slug)
    slug = slug.strip("-")

    # Ensure uniqueness with random suffix
    suffix = secrets.token_hex(4)
    return f"{slug}-{suffix}"


def validate_subdomain(subdomain: str) -> tuple[bool, str | None]:
    """
    Validate a subdomain string.

    Args:
        subdomain: Proposed subdomain

    Returns:
        tuple: (is_valid, error_message)
    """
    # Check length
    if len(subdomain) < 3 or len(subdomain) > 50:
        return False, "Subdomain must be 3-50 characters"

    # Check format (alphanumeric and hyphens only)
    if not re.match(r"^[a-z0-9][a-z0-9-]*[a-z0-9]$", subdomain):
        return False, "Subdomain must start and end with alphanumeric, contain only lowercase letters, numbers, and hyphens"

    # Reserved subdomains
    reserved = [
        "www", "api", "admin", "app", "dashboard", "mail", "email",
        "blog", "help", "support", "docs", "status", "cdn", "static",
        "auth", "login", "signup", "register", "account",
    ]
    if subdomain in reserved:
        return False, f"'{subdomain}' is a reserved subdomain"

    return True, None


async def create_tenant(
    name: str,
    owner_id: UUID,
    subdomain: str | None = None,
) -> dict[str, Any]:
    """
    Create a new tenant.

    Args:
        name: Tenant name
        owner_id: User ID of tenant creator
        subdomain: Optional custom subdomain

    Returns:
        Tenant data
    """
    slug = generate_tenant_slug(name)

    # Validate subdomain if provided
    if subdomain:
        is_valid, error = validate_subdomain(subdomain)
        if not is_valid:
            raise ValueError(error)
    else:
        subdomain = slug

    tenant_data = {
        "name": name,
        "slug": slug,
        "subdomain": subdomain,
        "owner_id": str(owner_id),
        "status": "active",
        "features": {
            "enable_research": True,
            "enable_teams": True,
            "enable_export": True,
            "enable_api": False,  # Requires upgrade
            "enable_white_label": False,  # Requires enterprise
        },
        "max_users": 10,
        "max_teams": 3,
        "max_api_keys": 2,
        "created_at": datetime.now().isoformat(),
    }

    logger.info(f"Tenant created: {name} (subdomain: {subdomain}) by {owner_id}")
    return tenant_data


async def update_tenant_branding(
    tenant_id: UUID,
    branding: TenantBrandingUpdate,
) -> dict[str, Any]:
    """
    Update tenant branding configuration.

    Args:
        tenant_id: Tenant UUID
        branding: Branding update data

    Returns:
        Updated branding data
    """
    branding_data = branding.model_dump(exclude_none=True)
    branding_data["updated_at"] = datetime.now().isoformat()

    logger.info(f"Tenant branding updated: {tenant_id}")
    return branding_data


async def configure_custom_domain(
    tenant_id: UUID,
    domain: str,
) -> dict[str, Any]:
    """
    Configure custom domain for tenant.

    Args:
        tenant_id: Tenant UUID
        domain: Custom domain (e.g., "insights.acme.com")

    Returns:
        Domain configuration with DNS instructions
    """
    # Validate domain format
    domain_pattern = r"^[a-z0-9]([a-z0-9-]*[a-z0-9])?(\.[a-z0-9]([a-z0-9-]*[a-z0-9])?)*\.[a-z]{2,}$"
    if not re.match(domain_pattern, domain.lower()):
        raise ValueError("Invalid domain format")

    # Generate verification token
    verification_token = f"{settings.tenant_base_domain.split('.')[0]}-verify={secrets.token_hex(16)}"

    domain_config = {
        "custom_domain": domain.lower(),
        "custom_domain_verified": False,
        "verification_token": verification_token,
        "dns_instructions": {
            "type": "CNAME",
            "name": domain.lower(),
            "value": f"custom.{settings.tenant_base_domain}",
            "txt_record": {
                "name": f"_{settings.tenant_base_domain.split('.')[0]}.{domain.lower()}",
                "value": verification_token,
            },
        },
        "configured_at": datetime.now().isoformat(),
    }

    logger.info(f"Custom domain configured for tenant {tenant_id}: {domain}")
    return domain_config


async def verify_custom_domain(
    tenant_id: UUID,
    domain: str,
) -> dict[str, Any]:
    """
    Verify custom domain DNS configuration.

    Args:
        tenant_id: Tenant UUID
        domain: Domain to verify

    Returns:
        Verification result
    """
    # In production, this would:
    # 1. Lookup TXT record for _startinsight.{domain}
    # 2. Verify token matches
    # 3. Check CNAME points to custom.startinsight.ai

    # Mock verification for development
    verification_result = {
        "domain": domain,
        "verified": True,  # Would be actual DNS check result
        "verified_at": datetime.now().isoformat(),
        "ssl_status": "pending",  # Would trigger SSL certificate provisioning
    }

    logger.info(f"Domain verified for tenant {tenant_id}: {domain}")
    return verification_result


# ============================================================
# Tenant Resolution
# ============================================================


async def resolve_tenant_from_host(host: str) -> dict[str, Any] | None:
    """
    Resolve tenant from request host.

    Args:
        host: Request host header

    Returns:
        Tenant data if found, None otherwise
    """
    # Remove port if present
    host = host.split(":")[0].lower()

    # Check if it's a custom domain
    # In production, query database for custom_domain match

    # Check if it's a subdomain of startinsight.ai
    if host.endswith(f".{settings.tenant_base_domain}"):
        subdomain = host.replace(f".{settings.tenant_base_domain}", "")
        if subdomain and subdomain != "www" and subdomain != "app":
            # In production, query database for subdomain match
            logger.debug(f"Resolved tenant from subdomain: {subdomain}")
            return {"subdomain": subdomain, "resolved_from": "subdomain"}

    # Default tenant
    if not settings.enable_multi_tenancy:
        return {"subdomain": settings.default_tenant_id, "resolved_from": "default"}

    return None


def get_tenant_css_variables(tenant: dict[str, Any]) -> str:
    """
    Generate CSS variables for tenant branding.

    Args:
        tenant: Tenant data with branding

    Returns:
        CSS custom properties string
    """
    primary = tenant.get("primary_color", "#3B82F6")
    secondary = tenant.get("secondary_color", "#10B981")
    accent = tenant.get("accent_color", "#F59E0B")

    return f""":root {{
  --tenant-primary: {primary};
  --tenant-secondary: {secondary};
  --tenant-accent: {accent};
  --tenant-name: "{tenant.get('app_name', 'StartInsight')}";
}}"""


# ============================================================
# Feature Flags
# ============================================================


def check_tenant_feature(tenant: dict[str, Any], feature: str) -> bool:
    """
    Check if tenant has a feature enabled.

    Args:
        tenant: Tenant data
        feature: Feature name to check

    Returns:
        True if feature is enabled
    """
    features = tenant.get("features", {})
    return features.get(feature, False)


def get_tenant_limits(tenant: dict[str, Any]) -> dict[str, int]:
    """Get tenant resource limits."""
    return {
        "max_users": tenant.get("max_users", 10),
        "max_teams": tenant.get("max_teams", 3),
        "max_api_keys": tenant.get("max_api_keys", 2),
    }
