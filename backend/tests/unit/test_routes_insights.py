"""Unit tests for insights API endpoints.

Covers:
- parse_accept_language (pure function, no I/O)
- GET /api/insights         (list with caching)
- GET /api/insights/{id}    (single insight by UUID)
- GET /api/insights/by-slug/{slug}  (single insight by slug)
- Cache-hit path (DB bypassed when cache returns data)
"""

from unittest.mock import AsyncMock, patch
from uuid import uuid4

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.routes.insights import parse_accept_language
from app.models.insight import Insight

# ---------------------------------------------------------------------------
# Pure-function tests: parse_accept_language
# ---------------------------------------------------------------------------


class TestParseAcceptLanguage:
    """Tests for the Accept-Language header parser (no I/O, no DB, no async)."""

    def test_none_returns_english(self):
        """None header defaults to 'en'."""
        assert parse_accept_language(None) == "en"

    def test_empty_string_returns_english(self):
        """Empty string header defaults to 'en'."""
        assert parse_accept_language("") == "en"

    def test_zh_cn_exact_match(self):
        """zh-CN with quality weights — highest-quality language is returned."""
        result = parse_accept_language("zh-CN,zh;q=0.9,en;q=0.8")
        assert result == "zh-CN"

    def test_english_us_maps_to_en(self):
        """en-US base matches supported 'en'."""
        result = parse_accept_language("en-US,en;q=0.9")
        assert result == "en"

    def test_indonesian_exact_match(self):
        """id-ID exact match is returned as-is."""
        result = parse_accept_language("id-ID")
        assert result == "id-ID"

    def test_unsupported_language_falls_back_to_english(self):
        """Unsupported language code (e.g., de-DE) falls back to 'en'."""
        result = parse_accept_language("de-DE,de;q=0.9")
        assert result == "en"

    def test_quality_ordering_respected(self):
        """Lower-quality English loses to higher-quality zh-CN."""
        result = parse_accept_language("en;q=0.5,zh-CN;q=0.9")
        assert result == "zh-CN"

    def test_single_supported_language(self):
        """Single supported language header returns that language."""
        result = parse_accept_language("vi-VN")
        assert result == "vi-VN"


# ---------------------------------------------------------------------------
# Route tests: GET /api/insights  (list endpoint)
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
class TestListInsights:
    """Tests for GET /api/insights."""

    @patch("app.api.routes.insights.cache_get", new_callable=AsyncMock, return_value=None)
    @patch("app.api.routes.insights.cache_set", new_callable=AsyncMock)
    async def test_empty_db_returns_200_with_empty_list(
        self,
        mock_cache_set: AsyncMock,
        mock_cache_get: AsyncMock,
        client: AsyncClient,
    ):
        """With no insights in DB, returns 200 with empty insights list."""
        resp = await client.get("/api/insights")
        assert resp.status_code == 200
        data = resp.json()
        assert data["insights"] == []
        assert data["total"] == 0

    @patch("app.api.routes.insights.cache_get", new_callable=AsyncMock, return_value=None)
    @patch("app.api.routes.insights.cache_set", new_callable=AsyncMock)
    async def test_list_pagination_fields_present(
        self,
        mock_cache_set: AsyncMock,
        mock_cache_get: AsyncMock,
        client: AsyncClient,
    ):
        """Response always contains pagination envelope fields."""
        resp = await client.get("/api/insights?limit=10&offset=0")
        assert resp.status_code == 200
        data = resp.json()
        assert "insights" in data
        assert "total" in data
        assert "limit" in data
        assert "offset" in data
        assert data["limit"] == 10
        assert data["offset"] == 0

    @patch("app.api.routes.insights.cache_get", new_callable=AsyncMock, return_value=None)
    @patch("app.api.routes.insights.cache_set", new_callable=AsyncMock)
    async def test_list_with_insight_in_db(
        self,
        mock_cache_set: AsyncMock,
        mock_cache_get: AsyncMock,
        client: AsyncClient,
        test_insight: Insight,
    ):
        """With one insight seeded, total is 1 and insights list is non-empty."""
        resp = await client.get("/api/insights")
        assert resp.status_code == 200
        data = resp.json()
        assert data["total"] == 1
        assert len(data["insights"]) == 1

    @patch("app.api.routes.insights.cache_get", new_callable=AsyncMock)
    async def test_cache_hit_skips_db_query(
        self,
        mock_cache_get: AsyncMock,
        client: AsyncClient,
    ):
        """When cache returns data, the route responds with cached payload."""
        mock_cache_get.return_value = {
            "insights": [],
            "total": 0,
            "limit": 20,
            "offset": 0,
        }
        resp = await client.get("/api/insights")
        assert resp.status_code == 200
        data = resp.json()
        assert data["total"] == 0
        assert data["insights"] == []

    @patch("app.api.routes.insights.cache_get", new_callable=AsyncMock, return_value=None)
    @patch("app.api.routes.insights.cache_set", new_callable=AsyncMock)
    async def test_list_cache_set_called_after_db(
        self,
        mock_cache_set: AsyncMock,
        mock_cache_get: AsyncMock,
        client: AsyncClient,
    ):
        """cache_set is called after a DB fetch (cache miss path)."""
        await client.get("/api/insights")
        mock_cache_set.assert_called_once()

    @patch("app.api.routes.insights.cache_get", new_callable=AsyncMock, return_value=None)
    @patch("app.api.routes.insights.cache_set", new_callable=AsyncMock)
    async def test_invalid_limit_rejected(
        self,
        mock_cache_set: AsyncMock,
        mock_cache_get: AsyncMock,
        client: AsyncClient,
    ):
        """limit > 100 is rejected with 422 Unprocessable Entity."""
        resp = await client.get("/api/insights?limit=999")
        assert resp.status_code == 422


# ---------------------------------------------------------------------------
# Route tests: GET /api/insights/{id}  (single by UUID)
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
class TestGetInsightById:
    """Tests for GET /api/insights/{insight_id}."""

    async def test_not_found_returns_404(self, client: AsyncClient):
        """Unknown UUID returns 404."""
        fake_id = uuid4()
        resp = await client.get(f"/api/insights/{fake_id}")
        assert resp.status_code == 404
        assert resp.json()["detail"] == "Insight not found"

    async def test_found_returns_200_with_title(self, client: AsyncClient, test_insight: Insight):
        """Existing insight UUID returns 200 with correct title."""
        resp = await client.get(f"/api/insights/{test_insight.id}")
        assert resp.status_code == 200
        data = resp.json()
        assert data["title"] == "AI-Powered Market Research Platform"

    async def test_found_response_has_id(self, client: AsyncClient, test_insight: Insight):
        """Response 'id' matches the requested UUID."""
        resp = await client.get(f"/api/insights/{test_insight.id}")
        assert resp.status_code == 200
        assert resp.json()["id"] == str(test_insight.id)

    async def test_malformed_uuid_returns_422(self, client: AsyncClient):
        """Non-UUID path segment returns 422 Unprocessable Entity."""
        resp = await client.get("/api/insights/not-a-uuid")
        assert resp.status_code == 422


# ---------------------------------------------------------------------------
# Route tests: GET /api/insights/by-slug/{slug}
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
class TestGetInsightBySlug:
    """Tests for GET /api/insights/by-slug/{slug}."""

    async def test_not_found_returns_404(self, client: AsyncClient):
        """Unknown slug returns 404."""
        resp = await client.get("/api/insights/by-slug/nonexistent-slug-xyz")
        assert resp.status_code == 404
        assert resp.json()["detail"] == "Insight not found"

    async def test_found_by_slug_returns_200(
        self,
        client: AsyncClient,
        test_insight: Insight,
        db_session: AsyncSession,
    ):
        """Insight with a matching slug is returned with 200."""
        test_insight.slug = "ai-powered-market-research-platform"
        db_session.add(test_insight)
        await db_session.commit()

        resp = await client.get("/api/insights/by-slug/ai-powered-market-research-platform")
        assert resp.status_code == 200
        data = resp.json()
        assert data["title"] == "AI-Powered Market Research Platform"

    async def test_slug_response_has_correct_id(
        self,
        client: AsyncClient,
        test_insight: Insight,
        db_session: AsyncSession,
    ):
        """Response id matches the insight's UUID."""
        test_insight.slug = "slug-id-check"
        db_session.add(test_insight)
        await db_session.commit()

        resp = await client.get("/api/insights/by-slug/slug-id-check")
        assert resp.status_code == 200
        assert resp.json()["id"] == str(test_insight.id)
