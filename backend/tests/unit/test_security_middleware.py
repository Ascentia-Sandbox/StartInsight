"""Tests for security headers middleware and request size limit middleware."""

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
class TestSecurityHeadersMiddleware:
    """Test security headers are present on all responses."""

    async def test_health_endpoint_has_security_headers(self, client: AsyncClient):
        """Security headers should be present on /health."""
        response = await client.get("/health")
        assert response.status_code == 200

        # Core security headers
        assert response.headers.get("x-frame-options") == "DENY"
        assert response.headers.get("x-content-type-options") == "nosniff"
        assert response.headers.get("x-xss-protection") == "1; mode=block"
        assert response.headers.get("referrer-policy") == "strict-origin-when-cross-origin"

    async def test_csp_header_present(self, client: AsyncClient):
        """Content-Security-Policy header should be set."""
        response = await client.get("/health")
        csp = response.headers.get("content-security-policy")
        assert csp is not None
        assert "default-src 'self'" in csp
        assert "script-src" in csp
        assert "style-src" in csp

    async def test_x_frame_options_deny(self, client: AsyncClient):
        """X-Frame-Options should be DENY to prevent clickjacking."""
        response = await client.get("/")
        assert response.headers.get("x-frame-options") == "DENY"

    async def test_security_headers_on_api_endpoint(self, client: AsyncClient):
        """Security headers should be on API endpoints too."""
        response = await client.get("/api/signals")
        assert response.headers.get("x-frame-options") == "DENY"
        assert response.headers.get("x-content-type-options") == "nosniff"


@pytest.mark.asyncio
class TestRequestSizeLimitMiddleware:
    """Test request size limit enforcement."""

    async def test_small_request_passes(self, client: AsyncClient):
        """Small requests should pass through normally."""
        response = await client.get("/health")
        assert response.status_code == 200

    async def test_oversized_content_length_rejected(self, client: AsyncClient):
        """Requests with Content-Length > 1MB should be rejected."""
        # Send a request with a large Content-Length header
        response = await client.post(
            "/api/insights",
            content=b"x" * 100,  # Small body
            headers={"content-length": "2000000"},  # Claims 2MB
        )
        # Should get 413 (request too large) or similar rejection
        assert response.status_code in (413, 422)
