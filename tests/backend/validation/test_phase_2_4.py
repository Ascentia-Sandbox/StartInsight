"""Test Phase 2.4: Insights API Endpoints."""

import asyncio
import logging
from datetime import datetime
from uuid import uuid4

import httpx

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

BASE_URL = "http://localhost:8000"


async def test_list_insights_endpoint():
    """Test GET /api/insights endpoint."""
    logger.info("Testing GET /api/insights...")

    async with httpx.AsyncClient() as client:
        response = await client.get(f"{BASE_URL}/api/insights")

        assert response.status_code == 200
        data = response.json()

        assert "insights" in data
        assert "total" in data
        assert "limit" in data
        assert "offset" in data
        assert isinstance(data["insights"], list)

    logger.info("✓ GET /api/insights works")


async def test_list_insights_with_filters():
    """Test GET /api/insights with filters."""
    logger.info("Testing GET /api/insights with filters...")

    async with httpx.AsyncClient() as client:
        # Test with min_score filter
        response = await client.get(f"{BASE_URL}/api/insights?min_score=0.7")
        assert response.status_code == 200
        data = response.json()
        assert data["insights"] is not None

        # Test with pagination
        response = await client.get(f"{BASE_URL}/api/insights?limit=5&offset=0")
        assert response.status_code == 200
        data = response.json()
        assert data["limit"] == 5
        assert data["offset"] == 0

    logger.info("✓ Filters and pagination work")


async def test_daily_top_endpoint():
    """Test GET /api/insights/daily-top endpoint."""
    logger.info("Testing GET /api/insights/daily-top...")

    async with httpx.AsyncClient() as client:
        response = await client.get(f"{BASE_URL}/api/insights/daily-top")

        assert response.status_code == 200
        data = response.json()

        assert isinstance(data, list)
        # Can be empty if no insights in last 24 hours

    logger.info("✓ GET /api/insights/daily-top works")


async def test_get_insight_by_id_not_found():
    """Test GET /api/insights/{id} with non-existent ID."""
    logger.info("Testing GET /api/insights/{id} (not found)...")

    fake_uuid = "00000000-0000-0000-0000-000000000000"

    async with httpx.AsyncClient() as client:
        response = await client.get(f"{BASE_URL}/api/insights/{fake_uuid}")

        assert response.status_code == 404

    logger.info("✓ 404 handling works")


async def test_insights_router_registered():
    """Test that insights router is registered in FastAPI app."""
    logger.info("Testing insights router registration...")

    async with httpx.AsyncClient() as client:
        # Check OpenAPI schema
        response = await client.get(f"{BASE_URL}/openapi.json")
        assert response.status_code == 200

        schema = response.json()

        # Verify /api/insights endpoints exist
        assert "/api/insights" in schema["paths"]
        assert "/api/insights/daily-top" in schema["paths"]
        assert "/api/insights/{insight_id}" in schema["paths"]

    logger.info("✓ All insight endpoints registered")


async def run_all_tests():
    """Run all Phase 2.4 tests."""
    logger.info("=" * 60)
    logger.info("Phase 2.4 Test Suite: Insights API Endpoints")
    logger.info("=" * 60)
    logger.info("⚠️  NOTE: FastAPI server must be running on port 8000\n")

    try:
        await test_list_insights_endpoint()
        await test_list_insights_with_filters()
        await test_daily_top_endpoint()
        await test_get_insight_by_id_not_found()
        await test_insights_router_registered()

        logger.info("\n" + "=" * 60)
        logger.info("✓ ALL PHASE 2.4 TESTS PASSED")
        logger.info("=" * 60)
        return True

    except Exception as e:
        logger.error("=" * 60)
        logger.error(f"✗ PHASE 2.4 TESTS FAILED: {e}")
        logger.error("=" * 60)
        import traceback

        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = asyncio.run(run_all_tests())
    exit(0 if success else 1)
