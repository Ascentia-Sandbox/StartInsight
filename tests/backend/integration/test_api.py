"""Integration tests for API endpoints."""

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.raw_signal import RawSignal


pytestmark = pytest.mark.asyncio


class TestHealthEndpoints:
    """Test health and root endpoints."""

    async def test_health_check(self, client: AsyncClient):
        """Test health check endpoint."""
        response = await client.get("/health")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "version" in data

    async def test_root_endpoint(self, client: AsyncClient):
        """Test root endpoint."""
        response = await client.get("/")

        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert "docs" in data


class TestSignalsEndpoints:
    """Test signals API endpoints."""

    async def test_list_signals_empty(self, client: AsyncClient):
        """Test listing signals when database is empty."""
        response = await client.get("/api/signals")

        assert response.status_code == 200
        data = response.json()
        assert "signals" in data
        assert "total" in data
        assert isinstance(data["signals"], list)

    async def test_list_signals_pagination(self, client: AsyncClient):
        """Test pagination parameters."""
        response = await client.get("/api/signals?limit=10&offset=0")

        assert response.status_code == 200
        data = response.json()
        assert data["limit"] == 10
        assert data["offset"] == 0

    async def test_list_signals_filter_by_source(self, client: AsyncClient):
        """Test filtering by source."""
        response = await client.get("/api/signals?source=reddit")

        assert response.status_code == 200
        data = response.json()
        # All returned signals should be from reddit
        for signal in data["signals"]:
            assert signal["source"] == "reddit" or len(data["signals"]) == 0

    async def test_list_signals_filter_by_processed(self, client: AsyncClient):
        """Test filtering by processed status."""
        response = await client.get("/api/signals?processed=false")

        assert response.status_code == 200
        data = response.json()
        # All returned signals should be unprocessed
        for signal in data["signals"]:
            assert signal["processed"] == False or len(data["signals"]) == 0  # noqa: E712

    async def test_signal_stats(self, client: AsyncClient):
        """Test signal statistics endpoint."""
        response = await client.get("/api/signals/stats/summary")

        assert response.status_code == 200
        data = response.json()
        assert "total_signals" in data
        assert "signals_by_source" in data
        assert "processed_count" in data
        assert "unprocessed_count" in data
        assert isinstance(data["signals_by_source"], dict)

    async def test_get_signal_not_found(self, client: AsyncClient):
        """Test getting a non-existent signal."""
        fake_uuid = "00000000-0000-0000-0000-000000000000"
        response = await client.get(f"/api/signals/{fake_uuid}")

        assert response.status_code == 404


class TestSignalsWithData:
    """Test signals endpoints with actual data."""

    @pytest.fixture
    async def sample_signal(self, db_session: AsyncSession):
        """Create a sample signal for testing."""
        signal = RawSignal(
            source="reddit",
            url="https://reddit.com/r/startups/test",
            content="# Test Signal\n\nThis is a test signal.",
            extra_metadata={"upvotes": 100, "comments": 50},
            processed=False
        )
        db_session.add(signal)
        await db_session.commit()
        await db_session.refresh(signal)
        return signal

    async def test_get_signal_by_id(
        self, client: AsyncClient, sample_signal: RawSignal
    ):
        """Test getting a signal by ID."""
        response = await client.get(f"/api/signals/{sample_signal.id}")

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == str(sample_signal.id)
        assert data["source"] == "reddit"
        assert data["processed"] == False  # noqa: E712

    async def test_list_signals_with_data(
        self, client: AsyncClient, sample_signal: RawSignal
    ):
        """Test listing signals with data."""
        response = await client.get("/api/signals")

        assert response.status_code == 200
        data = response.json()
        assert data["total"] >= 1
        assert len(data["signals"]) >= 1
