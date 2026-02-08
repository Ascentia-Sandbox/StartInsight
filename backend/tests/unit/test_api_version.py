"""Tests for API version middleware and versioning headers."""

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
class TestAPIVersionMiddleware:
    """Test API version headers on responses."""

    async def test_root_has_api_version_header(self, client: AsyncClient):
        """Root endpoint should have API-Version header."""
        response = await client.get("/")
        assert response.headers.get("api-version") == "1"

    async def test_root_has_full_version_header(self, client: AsyncClient):
        """Root endpoint should have X-API-Version header."""
        response = await client.get("/")
        assert response.headers.get("x-api-version") == "1.0.0"

    async def test_health_has_version_header(self, client: AsyncClient):
        """Health endpoint should have version headers."""
        response = await client.get("/health")
        assert response.headers.get("api-version") == "1"
        assert response.headers.get("x-api-version") == "1.0.0"

    async def test_api_endpoint_has_version_header(self, client: AsyncClient):
        """API endpoints should have version headers."""
        response = await client.get("/api/signals")
        assert response.headers.get("api-version") == "1"

    async def test_root_body_contains_api_version(self, client: AsyncClient):
        """Root endpoint body should contain api_version field."""
        response = await client.get("/")
        data = response.json()
        assert "api_version" in data
        assert data["api_version"] == "v1"
