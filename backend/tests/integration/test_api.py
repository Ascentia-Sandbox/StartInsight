"""Integration tests for API endpoints.

Note: These tests require PostgreSQL due to JSONB columns in models.
Run with: DATABASE_URL=postgresql+asyncpg://... pytest tests/integration/test_api.py

For CI/CD without PostgreSQL, these tests are marked to skip.
"""

import pytest
from httpx import AsyncClient

from app.models import User

# Mark all tests in this module to require PostgreSQL database
pytestmark = pytest.mark.skipif(
    True,  # Skip until PostgreSQL test database is configured
    reason="Integration tests require PostgreSQL (JSONB not supported in SQLite)",
)


class TestHealthEndpoints:
    """Tests for health and root endpoints."""

    @pytest.mark.asyncio
    async def test_health_check(self, client: AsyncClient):
        """Test health check endpoint."""
        response = await client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "version" in data

    @pytest.mark.asyncio
    async def test_root_endpoint(self, client: AsyncClient):
        """Test root endpoint."""
        response = await client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert "docs" in data


class TestSignalsEndpoints:
    """Tests for signals endpoints."""

    @pytest.mark.asyncio
    async def test_list_signals(self, client: AsyncClient, test_signal):
        """Test listing signals."""
        response = await client.get("/api/signals")
        assert response.status_code == 200
        data = response.json()
        assert "signals" in data
        assert "total" in data

    @pytest.mark.asyncio
    async def test_get_signal(self, client: AsyncClient, test_signal):
        """Test getting a specific signal."""
        response = await client.get(f"/api/signals/{test_signal.id}")
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == str(test_signal.id)
        assert data["source"] == "reddit"

    @pytest.mark.asyncio
    async def test_get_signal_not_found(self, client: AsyncClient):
        """Test getting non-existent signal."""
        from uuid import uuid4

        response = await client.get(f"/api/signals/{uuid4()}")
        assert response.status_code == 404


class TestInsightsEndpoints:
    """Tests for insights endpoints."""

    @pytest.mark.asyncio
    async def test_list_insights(self, client: AsyncClient, test_insight):
        """Test listing insights."""
        response = await client.get("/api/insights")
        assert response.status_code == 200
        data = response.json()
        assert "insights" in data
        assert "total" in data

    @pytest.mark.asyncio
    async def test_list_insights_with_filter(self, client: AsyncClient, test_insight):
        """Test listing insights with score filter."""
        response = await client.get("/api/insights?min_score=0.5")
        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_get_insight(self, client: AsyncClient, test_insight):
        """Test getting a specific insight."""
        response = await client.get(f"/api/insights/{test_insight.id}")
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == str(test_insight.id)
        assert data["relevance_score"] == test_insight.relevance_score

    @pytest.mark.asyncio
    async def test_daily_top_insights(self, client: AsyncClient, test_insight):
        """Test getting daily top insights."""
        response = await client.get("/api/insights/daily-top")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)

    @pytest.mark.asyncio
    async def test_idea_of_the_day(self, client: AsyncClient, test_insight):
        """Test getting idea of the day."""
        response = await client.get("/api/insights/idea-of-the-day")
        # May return 200 with insight or 200 with None
        assert response.status_code == 200


class TestProtectedEndpoints:
    """Tests for protected endpoints requiring authentication."""

    @pytest.mark.asyncio
    async def test_get_profile_unauthorized(self, client: AsyncClient):
        """Test accessing profile without auth."""
        response = await client.get("/api/users/me")
        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_get_saved_insights_unauthorized(self, client: AsyncClient):
        """Test accessing saved insights without auth."""
        response = await client.get("/api/users/me/saved")
        assert response.status_code == 401


class TestAuthenticatedUserEndpoints:
    """Tests for authenticated user endpoints."""

    @pytest.mark.asyncio
    async def test_get_profile(self, test_app, client: AsyncClient, test_user: User, auth_override):
        """Test getting user profile."""
        test_app.dependency_overrides.update(auth_override)
        try:
            response = await client.get("/api/users/me")
            assert response.status_code == 200
            data = response.json()
            assert data["email"] == test_user.email
        finally:
            test_app.dependency_overrides.clear()

    @pytest.mark.asyncio
    async def test_update_profile(self, test_app, client: AsyncClient, test_user: User, auth_override):
        """Test updating user profile."""
        test_app.dependency_overrides.update(auth_override)
        try:
            response = await client.patch(
                "/api/users/me",
                json={"display_name": "Updated Name"},
            )
            assert response.status_code == 200
            data = response.json()
            assert data["display_name"] == "Updated Name"
        finally:
            test_app.dependency_overrides.clear()

    @pytest.mark.asyncio
    async def test_get_workspace_status(self, test_app, client: AsyncClient, test_user: User, auth_override):
        """Test getting workspace status."""
        test_app.dependency_overrides.update(auth_override)
        try:
            response = await client.get("/api/users/me/status")
            assert response.status_code == 200
            data = response.json()
            assert "saved_count" in data
            assert "interested_count" in data
        finally:
            test_app.dependency_overrides.clear()

    @pytest.mark.asyncio
    async def test_save_insight(
        self, test_app, client: AsyncClient, test_user: User, test_insight, auth_override
    ):
        """Test saving an insight."""
        test_app.dependency_overrides.update(auth_override)
        try:
            response = await client.post(
                f"/api/users/insights/{test_insight.id}/save",
                json={"notes": "Testing save", "tags": ["test"]},
            )
            assert response.status_code in [200, 201]
        finally:
            test_app.dependency_overrides.clear()

    @pytest.mark.asyncio
    async def test_rate_insight(
        self, test_app, client: AsyncClient, test_user: User, test_insight, auth_override
    ):
        """Test rating an insight."""
        test_app.dependency_overrides.update(auth_override)
        try:
            response = await client.post(
                f"/api/users/insights/{test_insight.id}/rate",
                json={"rating": 5, "feedback": "Great insight!"},
            )
            assert response.status_code in [200, 201]
        finally:
            test_app.dependency_overrides.clear()


class TestResearchEndpoints:
    """Tests for research API endpoints."""

    @pytest.mark.asyncio
    async def test_get_quota_unauthorized(self, client: AsyncClient):
        """Test getting quota without auth."""
        response = await client.get("/api/research/quota")
        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_get_quota(self, test_app, client: AsyncClient, test_user: User, auth_override):
        """Test getting research quota."""
        test_app.dependency_overrides.update(auth_override)
        try:
            response = await client.get("/api/research/quota")
            assert response.status_code == 200
            data = response.json()
            assert "analyses_used" in data
            assert "analyses_limit" in data
            assert data["tier"] == "free"
        finally:
            test_app.dependency_overrides.clear()

    @pytest.mark.asyncio
    async def test_list_analyses(self, test_app, client: AsyncClient, test_user: User, auth_override):
        """Test listing analyses."""
        test_app.dependency_overrides.update(auth_override)
        try:
            response = await client.get("/api/research/analyses")
            assert response.status_code == 200
            data = response.json()
            assert "items" in data
            assert "total" in data
        finally:
            test_app.dependency_overrides.clear()

    @pytest.mark.asyncio
    async def test_get_analysis(
        self, test_app, client: AsyncClient, test_user: User, test_analysis, auth_override
    ):
        """Test getting specific analysis."""
        test_app.dependency_overrides.update(auth_override)
        try:
            response = await client.get(f"/api/research/analysis/{test_analysis.id}")
            assert response.status_code == 200
            data = response.json()
            assert data["id"] == str(test_analysis.id)
            assert data["status"] == "completed"
        finally:
            test_app.dependency_overrides.clear()


class TestAdminEndpoints:
    """Tests for admin endpoints."""

    @pytest.mark.asyncio
    async def test_admin_dashboard_unauthorized(self, client: AsyncClient):
        """Test admin dashboard without auth."""
        response = await client.get("/api/admin/dashboard")
        assert response.status_code == 401

    # Note: Full admin tests would require admin user auth setup
