"""Test Phase 1.5: FastAPI Endpoints."""

import asyncio
import logging

import httpx
from sqlalchemy import select

from app.db.session import AsyncSessionLocal
from app.models.raw_signal import RawSignal

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# We'll test against a running FastAPI server
API_BASE_URL = "http://localhost:8000"


async def test_health_endpoint():
    """Test health check endpoint."""
    logger.info("Testing health endpoint...")

    async with httpx.AsyncClient() as client:
        response = await client.get(f"{API_BASE_URL}/health")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        logger.info("✓ Health endpoint working")


async def test_root_endpoint():
    """Test root endpoint."""
    logger.info("Testing root endpoint...")

    async with httpx.AsyncClient() as client:
        response = await client.get(f"{API_BASE_URL}/")

        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert "docs" in data
        logger.info("✓ Root endpoint working")


async def test_list_signals_endpoint():
    """Test list signals endpoint."""
    logger.info("Testing list signals endpoint...")

    async with httpx.AsyncClient() as client:
        response = await client.get(f"{API_BASE_URL}/api/signals")

        assert response.status_code == 200
        data = response.json()
        assert "signals" in data
        assert "total" in data
        assert "limit" in data
        assert "offset" in data
        assert "has_more" in data
        logger.info(f"✓ List signals endpoint working (found {data['total']} signals)")


async def test_signal_stats_endpoint():
    """Test signal stats endpoint."""
    logger.info("Testing signal stats endpoint...")

    async with httpx.AsyncClient() as client:
        response = await client.get(f"{API_BASE_URL}/api/signals/stats/summary")

        assert response.status_code == 200
        data = response.json()
        assert "total_signals" in data
        assert "signals_by_source" in data
        assert "processed_count" in data
        assert "unprocessed_count" in data
        logger.info(f"✓ Signal stats endpoint working (total: {data['total_signals']})")


async def test_get_single_signal():
    """Test get single signal endpoint."""
    logger.info("Testing get single signal endpoint...")

    # First, get a signal ID from the database
    async with AsyncSessionLocal() as session:
        query = select(RawSignal).limit(1)
        result = await session.execute(query)
        signal = result.scalars().first()

    if signal:
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{API_BASE_URL}/api/signals/{signal.id}")

            assert response.status_code == 200
            data = response.json()
            assert data["id"] == str(signal.id)
            logger.info("✓ Get single signal endpoint working")
    else:
        logger.warning("⚠ No signals in database to test get single signal")


async def test_filter_by_source():
    """Test filtering signals by source."""
    logger.info("Testing filter by source...")

    async with httpx.AsyncClient() as client:
        response = await client.get(
            f"{API_BASE_URL}/api/signals",
            params={"source": "reddit"}
        )

        assert response.status_code == 200
        data = response.json()

        # All signals should be from reddit source
        for signal in data["signals"]:
            assert signal["source"] == "reddit"

        logger.info(f"✓ Filter by source working (found {len(data['signals'])} reddit signals)")


async def test_pagination():
    """Test pagination."""
    logger.info("Testing pagination...")

    async with httpx.AsyncClient() as client:
        # Get first page
        response1 = await client.get(
            f"{API_BASE_URL}/api/signals",
            params={"limit": 5, "offset": 0}
        )

        assert response1.status_code == 200
        data1 = response1.json()
        assert data1["limit"] == 5
        assert data1["offset"] == 0

        # Get second page
        response2 = await client.get(
            f"{API_BASE_URL}/api/signals",
            params={"limit": 5, "offset": 5}
        )

        assert response2.status_code == 200
        data2 = response2.json()
        assert data2["limit"] == 5
        assert data2["offset"] == 5

        logger.info("✓ Pagination working")


async def run_all_tests():
    """Run all Phase 1.5 tests."""
    logger.info("=" * 60)
    logger.info("Phase 1.5 Test Suite: FastAPI Endpoints")
    logger.info("=" * 60 + "\n")

    logger.info("NOTE: FastAPI server must be running at http://localhost:8000")
    logger.info("      Start with: uvicorn app.main:app --reload\n")

    try:
        await test_health_endpoint()
        await test_root_endpoint()
        await test_list_signals_endpoint()
        await test_signal_stats_endpoint()
        await test_get_single_signal()
        await test_filter_by_source()
        await test_pagination()

        logger.info("=" * 60)
        logger.info("✓ ALL PHASE 1.5 TESTS PASSED")
        logger.info("=" * 60)
        return True

    except httpx.ConnectError:
        logger.error("=" * 60)
        logger.error("✗ Cannot connect to API server at http://localhost:8000")
        logger.error("  Please start the server with: uvicorn app.main:app --reload")
        logger.error("=" * 60)
        return False

    except Exception as e:
        logger.error("=" * 60)
        logger.error(f"✗ PHASE 1.5 TESTS FAILED: {e}")
        logger.error("=" * 60)
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = asyncio.run(run_all_tests())
    exit(0 if success else 1)
