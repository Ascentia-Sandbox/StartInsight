"""Tests for scraper health check endpoint."""

from datetime import datetime, timedelta
from uuid import uuid4

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.raw_signal import RawSignal


@pytest.mark.asyncio
class TestScraperHealthEndpoint:
    """Test /health/scraping endpoint."""

    async def test_returns_200(self, client: AsyncClient):
        """Health check should return 200."""
        response = await client.get("/health/scraping")
        assert response.status_code == 200

    async def test_response_structure(self, client: AsyncClient):
        """Response should contain expected fields."""
        response = await client.get("/health/scraping")
        data = response.json()

        assert "status" in data
        assert "last_runs" in data
        assert "pending_signals" in data
        assert "queue_depth" in data
        assert "signals_collected_24h" in data
        assert "target_rate" in data
        assert "actual_rate" in data
        assert "errors_24h" in data
        assert "checked_at" in data

    async def test_status_degraded_without_signals(self, client: AsyncClient):
        """Without any signals, status should be degraded."""
        response = await client.get("/health/scraping")
        data = response.json()
        assert data["status"] == "degraded"

    async def test_pending_signals_count(
        self,
        client: AsyncClient,
        db_session: AsyncSession,
    ):
        """Should count unprocessed signals."""
        # Add some unprocessed signals
        for i in range(3):
            signal = RawSignal(
                id=uuid4(),
                source="reddit",
                url=f"https://reddit.com/post/{i}",
                content=f"Test signal {i}",
                metadata={},
                processed=False,
                created_at=datetime.utcnow(),
            )
            db_session.add(signal)
        await db_session.commit()

        response = await client.get("/health/scraping")
        data = response.json()
        assert data["pending_signals"] == 3

    async def test_24h_signal_count(
        self,
        client: AsyncClient,
        db_session: AsyncSession,
    ):
        """Should count signals from last 24 hours."""
        now = datetime.utcnow()

        # Add recent signals (should count)
        for i in range(5):
            signal = RawSignal(
                id=uuid4(),
                source="product_hunt",
                url=f"https://producthunt.com/post/{i}",
                content=f"Recent signal {i}",
                metadata={},
                processed=True,
                created_at=now - timedelta(hours=i),
            )
            db_session.add(signal)

        # Add old signal (should not count)
        old_signal = RawSignal(
            id=uuid4(),
            source="reddit",
            url="https://reddit.com/old",
            content="Old signal",
            metadata={},
            processed=True,
            created_at=now - timedelta(hours=48),
        )
        db_session.add(old_signal)
        await db_session.commit()

        response = await client.get("/health/scraping")
        data = response.json()
        assert data["signals_collected_24h"] == 5

    async def test_last_runs_per_source(
        self,
        client: AsyncClient,
        db_session: AsyncSession,
    ):
        """Should report last run time per source."""
        now = datetime.utcnow()

        for source in ["reddit", "product_hunt"]:
            signal = RawSignal(
                id=uuid4(),
                source=source,
                url=f"https://{source}.com/post/1",
                content=f"Signal from {source}",
                metadata={},
                processed=True,
                created_at=now - timedelta(hours=1),
            )
            db_session.add(signal)
        await db_session.commit()

        response = await client.get("/health/scraping")
        data = response.json()

        assert "reddit" in data["last_runs"]
        assert "product_hunt" in data["last_runs"]
        assert data["last_runs"]["reddit"] is not None
        assert data["last_runs"]["product_hunt"] is not None

    async def test_target_rate_displayed(self, client: AsyncClient):
        """Should display target collection rate."""
        response = await client.get("/health/scraping")
        data = response.json()
        assert data["target_rate"] == "360/day"

    async def test_zero_error_rate_with_good_signals(
        self,
        client: AsyncClient,
        db_session: AsyncSession,
    ):
        """Should show 0% error rate when all signals have content."""
        now = datetime.utcnow()

        # 4 good signals (all have content)
        for i in range(4):
            signal = RawSignal(
                id=uuid4(),
                source="reddit",
                url=f"https://reddit.com/good/{i}",
                content=f"Good signal {i}",
                metadata={},
                processed=True,
                created_at=now - timedelta(hours=1),
            )
            db_session.add(signal)
        await db_session.commit()

        response = await client.get("/health/scraping")
        data = response.json()

        assert data["errors_24h"] == 0
        assert data["signals_collected_24h"] == 4
        assert data["error_rate"] == "0.0%"
