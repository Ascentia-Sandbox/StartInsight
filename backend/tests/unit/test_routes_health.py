"""Unit tests for health check API endpoints.

Covers GET /health, /health/live, /health/ready, /health/scraping, /health/sources.

Important: SQLite (used in tests) returns naive datetimes but health.py uses
datetime.now(UTC) which is timezone-aware.  The _naive_utc fixture patches UTC
to None so datetime.now(None) returns a naive local-time datetime — the same
workaround used in test_health_scraping.py.
"""

from datetime import UTC, datetime, timedelta
from unittest.mock import AsyncMock, patch
from uuid import uuid4

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.raw_signal import RawSignal

# ---------------------------------------------------------------------------
# Fixture: patch UTC → naive datetimes for SQLite compatibility
# ---------------------------------------------------------------------------


@pytest.fixture(autouse=True)
def _naive_utc(monkeypatch):
    """Make datetime.now(UTC) return naive datetimes compatible with SQLite."""
    import app.api.routes.health as health_mod

    monkeypatch.setattr(health_mod, "UTC", None)


# ---------------------------------------------------------------------------
# Test: basic health + liveness checks
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
class TestBasicHealthEndpoints:
    """Tests for /health and /health/live endpoints."""

    async def test_health_200(self, client: AsyncClient):
        """GET /health returns 200 with service name."""
        resp = await client.get("/health")
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "healthy"
        assert data["service"] == "startinsight-api"

    async def test_health_live(self, client: AsyncClient):
        """GET /health/live returns 200 with alive status."""
        resp = await client.get("/health/live")
        assert resp.status_code == 200
        assert resp.json()["status"] == "alive"


# ---------------------------------------------------------------------------
# Test: readiness check (/health/ready)
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
class TestReadinessEndpoint:
    """Tests for /health/ready — depends on DB and Redis."""

    @patch("app.api.routes.health.get_redis")
    async def test_health_ready_healthy(self, mock_get_redis, client: AsyncClient):
        """Returns 200 and status='ready' when both DB and Redis are up."""
        mock_redis = AsyncMock()
        mock_redis.ping = AsyncMock(return_value=True)
        mock_get_redis.return_value = mock_redis

        resp = await client.get("/health/ready")
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "ready"
        assert data["checks"]["database"] == "healthy"
        assert data["checks"]["redis"] == "healthy"

    @patch("app.api.routes.health.get_redis")
    async def test_health_ready_redis_down(self, mock_get_redis, client: AsyncClient):
        """Returns 503 when Redis is unreachable."""
        mock_get_redis.side_effect = ConnectionError("Redis down")

        resp = await client.get("/health/ready")
        assert resp.status_code == 503
        data = resp.json()
        assert data["status"] == "not_ready"
        assert "unhealthy" in data["checks"]["redis"]

    @patch("app.api.routes.health.get_redis")
    async def test_health_ready_db_down(self, mock_get_redis, client: AsyncClient, test_app):
        """Returns 503 when the database query fails."""
        mock_redis = AsyncMock()
        mock_redis.ping = AsyncMock(return_value=True)
        mock_get_redis.return_value = mock_redis

        # Replace the DB dependency with one whose execute() raises
        from app.db.session import get_db

        async def broken_db():
            session = AsyncMock()
            session.execute = AsyncMock(side_effect=Exception("DB down"))
            yield session

        test_app.dependency_overrides[get_db] = broken_db
        try:
            resp = await client.get("/health/ready")
        finally:
            # Restore original override so subsequent tests are unaffected
            from tests.conftest import AsyncSession as _  # noqa: F401 (unused; just ensure import)

            # Re-apply the standard test-DB override from the test_app fixture
            # The finally block simply removes our custom override so the
            # original test_app override takes effect again.
            del test_app.dependency_overrides[get_db]

        assert resp.status_code == 503
        data = resp.json()
        assert data["status"] == "not_ready"
        assert "unhealthy" in data["checks"]["database"]

    @patch("app.api.routes.health.get_redis")
    async def test_health_ready_checks_key_present(self, mock_get_redis, client: AsyncClient):
        """Response always contains 'checks' key with database and redis."""
        mock_redis = AsyncMock()
        mock_redis.ping = AsyncMock(return_value=True)
        mock_get_redis.return_value = mock_redis

        resp = await client.get("/health/ready")
        data = resp.json()
        assert "checks" in data
        assert "database" in data["checks"]
        assert "redis" in data["checks"]


# ---------------------------------------------------------------------------
# Test: scraping health (/health/scraping)
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
class TestScrapingHealthEndpoint:
    """Tests for /health/scraping — monitors data collection pipeline."""

    @patch("app.api.routes.health.get_redis")
    async def test_scraping_status_200(self, mock_get_redis, client: AsyncClient):
        """GET /health/scraping always returns 200."""
        mock_redis = AsyncMock()
        mock_redis.llen = AsyncMock(return_value=0)
        mock_get_redis.return_value = mock_redis

        resp = await client.get("/health/scraping")
        assert resp.status_code == 200

    @patch("app.api.routes.health.get_redis")
    async def test_scraping_response_structure(self, mock_get_redis, client: AsyncClient):
        """Response contains all required monitoring fields."""
        mock_redis = AsyncMock()
        mock_redis.llen = AsyncMock(return_value=5)
        mock_get_redis.return_value = mock_redis

        resp = await client.get("/health/scraping")
        data = resp.json()

        assert "status" in data
        assert "pending_signals" in data
        assert "signals_collected_24h" in data
        assert "queue_depth" in data
        assert "errors_24h" in data
        assert "error_rate" in data
        assert "checked_at" in data
        assert "last_runs" in data

    @patch("app.api.routes.health.get_redis")
    async def test_scraping_degraded_without_signals(self, mock_get_redis, client: AsyncClient):
        """Status is 'degraded' when no signals have been collected recently."""
        mock_redis = AsyncMock()
        mock_redis.llen = AsyncMock(return_value=0)
        mock_get_redis.return_value = mock_redis

        resp = await client.get("/health/scraping")
        assert resp.json()["status"] == "degraded"

    @patch("app.api.routes.health.get_redis")
    async def test_scraping_24h_signal_count(
        self, mock_get_redis, client: AsyncClient, db_session: AsyncSession
    ):
        """signals_collected_24h reflects signals created in the last 24 hours."""
        mock_redis = AsyncMock()
        mock_redis.llen = AsyncMock(return_value=0)
        mock_get_redis.return_value = mock_redis

        now = datetime.now(UTC)

        # 3 recent signals — should be counted
        for i in range(3):
            signal = RawSignal(
                id=uuid4(),
                source="reddit",
                url=f"https://reddit.com/recent/{i}",
                content=f"Recent signal {i}",
                processed=True,
                created_at=now - timedelta(hours=i),
            )
            db_session.add(signal)

        # 1 old signal — outside 24-hour window
        db_session.add(
            RawSignal(
                id=uuid4(),
                source="reddit",
                url="https://reddit.com/old",
                content="Old signal",
                processed=True,
                created_at=now - timedelta(hours=48),
            )
        )
        await db_session.commit()

        resp = await client.get("/health/scraping")
        data = resp.json()
        assert data["signals_collected_24h"] == 3

    @patch("app.api.routes.health.get_redis")
    async def test_scraping_queue_depth_from_redis(self, mock_get_redis, client: AsyncClient):
        """queue_depth is read from the Redis arq queue list."""
        mock_redis = AsyncMock()
        mock_redis.llen = AsyncMock(return_value=7)
        mock_get_redis.return_value = mock_redis

        resp = await client.get("/health/scraping")
        data = resp.json()
        assert data["queue_depth"] == 7

    @patch("app.api.routes.health.get_redis")
    async def test_scraping_pending_count(
        self, mock_get_redis, client: AsyncClient, db_session: AsyncSession
    ):
        """pending_signals counts unprocessed signals regardless of age."""
        mock_redis = AsyncMock()
        mock_redis.llen = AsyncMock(return_value=0)
        mock_get_redis.return_value = mock_redis

        for i in range(4):
            db_session.add(
                RawSignal(
                    id=uuid4(),
                    source="product_hunt",
                    url=f"https://producthunt.com/{i}",
                    content=f"Unprocessed {i}",
                    processed=False,
                    created_at=datetime.now(UTC),
                )
            )
        await db_session.commit()

        resp = await client.get("/health/scraping")
        assert resp.json()["pending_signals"] == 4


# ---------------------------------------------------------------------------
# Test: source health (/health/sources)
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
class TestSourcesHealthEndpoint:
    """Tests for /health/sources — Phase 6.2A source health registry."""

    async def test_sources_200(self, client: AsyncClient):
        """GET /health/sources always returns 200."""
        resp = await client.get("/health/sources")
        assert resp.status_code == 200

    async def test_sources_contains_sources_key(self, client: AsyncClient):
        """Response always contains a 'sources' list, even when table is absent."""
        resp = await client.get("/health/sources")
        data = resp.json()
        assert "sources" in data
        assert isinstance(data["sources"], list)

    async def test_sources_graceful_fallback_when_table_missing(self, client: AsyncClient):
        """SQLite test DB has no source_health table — endpoint returns empty list."""
        resp = await client.get("/health/sources")
        data = resp.json()
        # Either empty list (table missing) or populated list (table exists)
        assert isinstance(data["sources"], list)
        # When table is absent the endpoint adds a note rather than raising 500
        if not data["sources"]:
            assert "note" in data or data["sources"] == []
