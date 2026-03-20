"""Unit tests for BaseScraper in app.scrapers.base_scraper."""

import hashlib
from unittest.mock import AsyncMock, MagicMock

import pytest

from app.scrapers.base_scraper import BaseScraper
from app.scrapers.firecrawl_client import ScrapeResult


class _TestScraper(BaseScraper):
    """Concrete subclass of BaseScraper used only in tests."""

    def __init__(self):
        super().__init__("test_source")
        self._results = []

    async def scrape(self):
        return self._results


@pytest.fixture
def scraper():
    return _TestScraper()


@pytest.fixture
def mock_session():
    session = AsyncMock()
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = None
    session.execute = AsyncMock(return_value=mock_result)
    session.add = MagicMock()
    session.flush = AsyncMock()
    return session


def make_result(
    url: str = "https://example.com/1",
    title: str = "Test",
    content: str = "Test content",
    metadata: dict | None = None,
) -> ScrapeResult:
    """Helper to build a ScrapeResult for tests."""
    return ScrapeResult(url=url, title=title, content=content, metadata=metadata or {})


# ---------------------------------------------------------------------------
# compute_content_hash
# ---------------------------------------------------------------------------


def test_content_hash_deterministic(scraper):
    """Same content always produces the same SHA-256 hex digest."""
    h1 = scraper.compute_content_hash("hello world")
    h2 = scraper.compute_content_hash("hello world")
    assert h1 == h2
    assert h1 == hashlib.sha256(b"hello world").hexdigest()


def test_content_hash_different(scraper):
    """Different content produces different hashes."""
    h1 = scraper.compute_content_hash("alpha")
    h2 = scraper.compute_content_hash("beta")
    assert h1 != h2


# ---------------------------------------------------------------------------
# clean_text
# ---------------------------------------------------------------------------


def test_clean_text_whitespace(scraper):
    """Multiple internal spaces are collapsed to a single space and stripped."""
    assert scraper.clean_text("  hello   world  ") == "hello world"


def test_clean_text_carriage_returns(scraper):
    """Carriage returns and newlines are treated as whitespace and collapsed."""
    # split() treats \r\n as whitespace tokens → joined with single space
    result = scraper.clean_text("hello\r\nworld")
    assert result == "hello world"


def test_clean_text_triple_newlines(scraper):
    """Triple newlines are treated as whitespace; split() collapses them to a space."""
    # " ".join("a\n\n\nb".split()) → "a b"
    assert scraper.clean_text("a\n\n\nb") == "a b"


def test_clean_text_empty(scraper):
    """Empty string returns empty string."""
    assert scraper.clean_text("") == ""


# ---------------------------------------------------------------------------
# truncate_content
# ---------------------------------------------------------------------------


def test_truncate_short_unchanged(scraper):
    """Content shorter than max_length is returned unchanged."""
    content = "x" * 100
    assert scraper.truncate_content(content, max_length=50000) == content


def test_truncate_long(scraper):
    """Content longer than max_length is truncated and a marker is appended."""
    content = "a" * 60000
    result = scraper.truncate_content(content, max_length=50000)
    assert len(result) < len(content)
    assert "[Content truncated...]" in result


def test_truncate_boundary(scraper):
    """Content exactly at max_length is not truncated."""
    content = "b" * 50000
    result = scraper.truncate_content(content, max_length=50000)
    assert result == content


# ---------------------------------------------------------------------------
# save_to_database
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_save_new_signals(scraper, mock_session):
    """Two fresh results each create a new RawSignal; session.add called twice."""
    results = [
        make_result(url="https://example.com/1", content="content one"),
        make_result(url="https://example.com/2", content="content two"),
    ]
    # Both hash and URL checks return None (no duplicates)
    fresh_result = MagicMock()
    fresh_result.scalar_one_or_none.return_value = None
    mock_session.execute = AsyncMock(return_value=fresh_result)

    saved = await scraper.save_to_database(mock_session, results)

    assert mock_session.add.call_count == 2
    assert len(saved) == 2


@pytest.mark.asyncio
async def test_save_dedup_by_hash(scraper, mock_session):
    """Result whose content_hash already exists in DB is skipped."""
    results = [make_result(content="duplicate content")]

    existing = MagicMock()
    existing.scalar_one_or_none.return_value = MagicMock()  # non-None → already exists

    mock_session.execute = AsyncMock(return_value=existing)

    saved = await scraper.save_to_database(mock_session, results)

    mock_session.add.assert_not_called()
    assert saved == []


@pytest.mark.asyncio
async def test_save_dedup_by_url(scraper, mock_session):
    """Result whose URL+source already exists is skipped even if hash is new."""
    results = [make_result(url="https://example.com/exists", content="unique content")]

    call_count = 0

    async def side_effect(*args, **kwargs):
        nonlocal call_count
        call_count += 1
        result = MagicMock()
        # First call = hash check → None (new hash)
        # Second call = URL check → existing record
        result.scalar_one_or_none.return_value = None if call_count == 1 else MagicMock()
        return result

    mock_session.execute = AsyncMock(side_effect=side_effect)

    saved = await scraper.save_to_database(mock_session, results)

    mock_session.add.assert_not_called()
    assert saved == []


@pytest.mark.asyncio
async def test_save_empty_results(scraper, mock_session):
    """Passing an empty list returns an empty list with no DB operations."""
    saved = await scraper.save_to_database(mock_session, [])

    mock_session.add.assert_not_called()
    assert saved == []


@pytest.mark.asyncio
async def test_save_individual_error_continues(scraper, mock_session):
    """An error processing one result does not prevent others from being saved."""
    results = [
        make_result(url="https://example.com/bad", content="bad content"),
        make_result(url="https://example.com/good", content="good content"),
    ]

    call_count = 0

    async def side_effect(*args, **kwargs):
        nonlocal call_count
        call_count += 1
        # First result's first DB call raises; all subsequent calls succeed
        if call_count == 1:
            raise Exception("DB error on first result")
        result = MagicMock()
        result.scalar_one_or_none.return_value = None
        return result

    mock_session.execute = AsyncMock(side_effect=side_effect)

    # Should not raise; good result should still be processed
    saved = await scraper.save_to_database(mock_session, results)

    # At least the second result was added
    assert mock_session.add.call_count >= 1
