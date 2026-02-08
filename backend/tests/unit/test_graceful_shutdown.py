"""Tests for graceful shutdown behavior."""

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
class TestGracefulShutdown:
    """Test graceful shutdown related functionality."""

    async def test_app_responds_during_normal_operation(self, client: AsyncClient):
        """App should respond normally before shutdown."""
        response = await client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"

    async def test_root_returns_version(self, client: AsyncClient):
        """Root endpoint should return current version info."""
        response = await client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert "version" in data
        assert data["version"] == "0.1.0"

    async def test_close_db_function_exists(self):
        """close_db function should be importable and callable."""
        from app.db.session import close_db
        assert callable(close_db)

    async def test_close_redis_function_exists(self):
        """close_redis function should be importable and callable."""
        from app.core.cache import close_redis
        assert callable(close_redis)
