"""Tests for tenant service - Phase 7.3."""

from uuid import uuid4

import pytest

from app.services.tenant_service import (
    TenantBrandingUpdate,
    TenantCreate,
    create_tenant,
    get_tenant_css_variables,
)


class TestTenantCreate:
    """Tests for TenantCreate model."""

    def test_valid_tenant_create(self):
        """Test valid tenant creation data."""
        tenant = TenantCreate(
            name="Acme Corp",
            subdomain="acme",
        )
        assert tenant.name == "Acme Corp"
        assert tenant.subdomain == "acme"

    def test_tenant_create_without_subdomain(self):
        """Test tenant creation without subdomain."""
        tenant = TenantCreate(name="Acme Corp")
        assert tenant.name == "Acme Corp"
        assert tenant.subdomain is None


class TestTenantBrandingUpdate:
    """Tests for TenantBrandingUpdate model."""

    def test_valid_branding_update(self):
        """Test valid branding update data."""
        branding = TenantBrandingUpdate(
            primary_color="#FF5500",
            app_name="Acme Insights",
        )
        assert branding.primary_color == "#FF5500"
        assert branding.app_name == "Acme Insights"

    def test_branding_update_partial(self):
        """Test partial branding update."""
        branding = TenantBrandingUpdate(logo_url="https://example.com/logo.png")
        assert branding.logo_url == "https://example.com/logo.png"
        assert branding.primary_color is None


class TestCreateTenant:
    """Tests for create_tenant function."""

    @pytest.mark.asyncio
    async def test_create_tenant_returns_dict(self):
        """Test create_tenant returns tenant data dict."""
        result = await create_tenant(
            name="Acme Corp",
            owner_id=uuid4(),
        )
        assert "name" in result
        assert "slug" in result
        assert "status" in result
        assert "created_at" in result

    @pytest.mark.asyncio
    async def test_create_tenant_with_subdomain(self):
        """Test create_tenant with custom subdomain."""
        result = await create_tenant(
            name="Acme Corp",
            owner_id=uuid4(),
            subdomain="acme-insights",
        )
        assert result["subdomain"] == "acme-insights"

    @pytest.mark.asyncio
    async def test_create_tenant_default_status(self):
        """Test create_tenant sets default status."""
        result = await create_tenant(
            name="Acme Corp",
            owner_id=uuid4(),
        )
        assert result["status"] == "active"


class TestGetTenantCssVariables:
    """Tests for get_tenant_css_variables function."""

    def test_css_variables_custom_colors(self):
        """Test CSS variables use custom colors."""
        tenant_data = {
            "primary_color": "#123456",
        }
        css = get_tenant_css_variables(tenant_data)
        assert "#123456" in css

    def test_css_variables_includes_variables(self):
        """Test CSS variables include CSS custom properties."""
        tenant_data = {
            "app_name": "Acme Insights",
        }
        css = get_tenant_css_variables(tenant_data)
        # CSS should contain variable syntax
        assert "--" in css
