"""Feature tests for the scraper pipeline.

End-to-end tests covering BaseScraper.save_to_database, CircuitBreaker
integration, and the full scrape→save workflow, using a concrete test
scraper, an in-memory mock session, and a mocked Redis backend.

The save_to_database method performs TWO session.execute calls per result:
  1. Hash-based dedup check (RawSignal.content_hash == hash)
  2. URL-based dedup check (RawSignal.url == url AND source == source)
Tests that need to simulate a duplicate must configure the mock to return
an existing record on the *first* execute call for that result.
"""

import time
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.scrapers.base_scraper import BaseScraper, CircuitBreaker, CircuitState
from app.scrapers.firecrawl_client import ScrapeResult

# ---------------------------------------------------------------------------
# Concrete test scraper
# ---------------------------------------------------------------------------


class _TestScraper(BaseScraper):
    """Concrete BaseScraper subclass used only in tests."""

    def __init__(self, results: list[ScrapeResult] | None = None):
        super().__init__("test_source")
        self._results = results or []

    async def scrape(self) -> list[ScrapeResult]:
        return self._results


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def make_result(
    url: str = "https://example.com/1",
    title: str = "Test",
    content: str = "Test content",
) -> ScrapeResult:
    """Create a ScrapeResult with sensible defaults."""
    return ScrapeResult(url=url, title=title, content=content, metadata={})


def _no_existing() -> MagicMock:
    """Mock execute result that signals no existing record (new signal)."""
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = None
    return mock_result


def _existing_record() -> MagicMock:
    """Mock execute result that signals a duplicate (existing record found)."""
    existing = MagicMock()
    existing.id = "existing-uuid"
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = existing
    return mock_result


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def mock_session():
    """Async session where every execute returns 'no existing record'."""
    session = AsyncMock()
    session.execute = AsyncMock(return_value=_no_existing())
    session.add = MagicMock()
    session.flush = AsyncMock()
    return session


@pytest.fixture
def mock_redis():
    """Async Redis mock for CircuitBreaker tests."""
    r = AsyncMock()
    r.get = AsyncMock(return_value=None)
    r.set = AsyncMock()
    r.incr = AsyncMock(return_value=1)
    pipe = AsyncMock()
    pipe.set = MagicMock()
    pipe.delete = MagicMock()
    pipe.execute = AsyncMock()
    r.pipeline = MagicMock(return_value=pipe)
    return r


# ---------------------------------------------------------------------------
# Test 1: Full scrape saves all signals
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_full_scrape_saves_signals(mock_session):
    """save_to_database with 3 results adds 3 signals and returns them."""
    results = [
        make_result(url=f"https://example.com/{i}", content=f"Content {i}") for i in range(3)
    ]
    scraper = _TestScraper(results)

    signals = await scraper.save_to_database(mock_session, results)

    assert len(signals) == 3
    assert mock_session.add.call_count == 3
    mock_session.flush.assert_awaited_once()


# ---------------------------------------------------------------------------
# Test 2: Duplicate signals (hash match) are skipped
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_duplicate_signals_skipped(mock_session):
    """When hash-check execute returns an existing record, that result is skipped."""
    result = make_result()

    # First execute call (hash dedup) returns an existing record → duplicate skipped.
    mock_session.execute = AsyncMock(return_value=_existing_record())

    scraper = _TestScraper()
    signals = await scraper.save_to_database(mock_session, [result])

    assert signals == []
    mock_session.add.assert_not_called()


# ---------------------------------------------------------------------------
# Test 3: Circuit breaker blocks after threshold failures
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_circuit_breaker_blocks_after_failures(mock_redis):
    """After FAILURE_THRESHOLD failures circuit is OPEN and can_execute returns False.

    Redis stores state as a plain string (the CircuitState enum value).
    The opened_at timestamp must be recent so the cooldown has NOT yet expired.
    """
    cb = CircuitBreaker("test_source")

    # Report OPEN state with a recent opened_at (cooldown NOT expired).
    recent_opened_at = str(time.time() - 10)  # 10 s ago, well inside 900 s cooldown

    async def fake_get(key: str):
        if "state" in key:
            return CircuitState.OPEN  # str value "open" — not bytes
        if "opened_at" in key:
            return recent_opened_at
        return None

    mock_redis.get = AsyncMock(side_effect=fake_get)

    with patch.object(CircuitBreaker, "_get_redis", return_value=mock_redis):
        result = await cb.can_execute()

    assert result is False


# ---------------------------------------------------------------------------
# Test 4: Circuit breaker recovers after cooldown
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_circuit_breaker_recovers(mock_redis):
    """After OPEN + cooldown expired, can_execute returns True (HALF_OPEN), then record_success closes it."""
    cb = CircuitBreaker("test_source")

    # Cooldown has elapsed (opened 2000 s ago, threshold is 900 s).
    # Return state as the plain string enum value, not bytes.
    old_opened_at = str(time.time() - 2000)

    async def fake_get(key: str):
        if "state" in key:
            return CircuitState.OPEN  # str "open"
        if "opened_at" in key:
            return old_opened_at
        return None

    mock_redis.get = AsyncMock(side_effect=fake_get)

    with patch.object(CircuitBreaker, "_get_redis", return_value=mock_redis):
        can = await cb.can_execute()  # Should be HALF_OPEN → True

    assert can is True

    # After record_success, pipeline should set state to CLOSED
    pipe = mock_redis.pipeline.return_value
    with patch.object(CircuitBreaker, "_get_redis", return_value=mock_redis):
        await cb.record_success()

    pipe.execute.assert_awaited()
    set_calls = [str(call) for call in pipe.set.call_args_list]
    assert any("CLOSED" in c for c in set_calls)


# ---------------------------------------------------------------------------
# Test 5: Empty scrape returns empty list
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_empty_scrape_returns_empty(mock_session):
    """save_to_database with an empty results list returns [] without touching DB."""
    scraper = _TestScraper()
    signals = await scraper.save_to_database(mock_session, [])

    assert signals == []
    mock_session.add.assert_not_called()
    # flush is NOT called for an empty list (early return before flush)
    mock_session.flush.assert_not_awaited()


# ---------------------------------------------------------------------------
# Test 6: Metadata is persisted into extra_metadata
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_save_with_metadata(mock_session):
    """ScrapeResult with metadata is stored in RawSignal.extra_metadata."""
    result = ScrapeResult(
        url="https://example.com/meta",
        title="Meta Test",
        content="Some content",
        metadata={"key": "value", "score": 42},
    )
    scraper = _TestScraper()

    signals = await scraper.save_to_database(mock_session, [result])

    assert len(signals) == 1
    signal = signals[0]
    assert signal.extra_metadata["key"] == "value"
    assert signal.extra_metadata["score"] == 42
    assert signal.extra_metadata["title"] == "Meta Test"


# ---------------------------------------------------------------------------
# Test 7: Content hash deduplication
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_content_hash_dedup(mock_session):
    """Same content → same hash → second result is deduped; different content → both saved."""
    scraper = _TestScraper()

    # Two results with identical content
    r1 = make_result(url="https://example.com/a", content="Identical content")
    r2 = make_result(url="https://example.com/b", content="Identical content")
    assert BaseScraper.compute_content_hash(r1.content) == BaseScraper.compute_content_hash(
        r2.content
    )

    # save_to_database issues TWO execute calls per result (hash check + URL check).
    # r1 needs both to return no-existing (hash=new, url=new) so it is saved.
    # r2 only needs the first (hash check) to find an existing record to be skipped.
    mock_session.execute = AsyncMock(
        side_effect=[
            _no_existing(),  # r1 hash check → new
            _no_existing(),  # r1 url check  → new (r1 is saved)
            _existing_record(),  # r2 hash check → duplicate → skip
        ]
    )

    signals = await scraper.save_to_database(mock_session, [r1, r2])

    # Only r1 should be saved
    assert len(signals) == 1

    # Two different contents → different hashes → both saved
    r3 = make_result(url="https://example.com/c", content="Unique content A")
    r4 = make_result(url="https://example.com/d", content="Unique content B")
    assert BaseScraper.compute_content_hash(r3.content) != BaseScraper.compute_content_hash(
        r4.content
    )

    mock_session2 = AsyncMock()
    mock_session2.execute = AsyncMock(return_value=_no_existing())
    mock_session2.add = MagicMock()
    mock_session2.flush = AsyncMock()

    signals2 = await scraper.save_to_database(mock_session2, [r3, r4])
    assert len(signals2) == 2


# ---------------------------------------------------------------------------
# Test 8: URL deduplication per source
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_url_dedup_per_source(mock_session):
    """Same URL + source combo is skipped when the URL dedup query finds a match.

    save_to_database issues two execute calls per result:
      1st → hash check (no existing), 2nd → URL check (existing found) → skip.
    """
    result = make_result(url="https://example.com/existing")
    scraper = _TestScraper()

    # 1st execute (hash check) → no duplicate; 2nd execute (URL check) → duplicate
    mock_session.execute = AsyncMock(side_effect=[_no_existing(), _existing_record()])

    signals = await scraper.save_to_database(mock_session, [result])

    assert signals == []
    mock_session.add.assert_not_called()


# ---------------------------------------------------------------------------
# Test 9: Scraper.run() calls scrape() then save_to_database()
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_scraper_run_workflow(mock_session):
    """run(session) executes scrape() and then save_to_database(), returning signals."""
    results = [make_result(content="Workflow content")]
    scraper = _TestScraper(results)

    signals = await scraper.run(mock_session)

    # save_to_database was called (evidenced by session.add being invoked)
    assert mock_session.add.call_count == 1
    assert len(signals) == 1
    assert signals[0].source == "test_source"


# ---------------------------------------------------------------------------
# Test 10: Individual errors on one result do not abort the whole batch
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_individual_error_continues():
    """An exception during execute for result 2 does not prevent result 1 being saved."""
    results = [
        make_result(url="https://example.com/good", content="Good content"),
        make_result(url="https://example.com/bad", content="Bad content"),
    ]
    scraper = _TestScraper(results)

    session = AsyncMock()
    session.add = MagicMock()
    session.flush = AsyncMock()

    call_count = 0

    async def execute_side_effect(query):
        nonlocal call_count
        call_count += 1
        # First two calls belong to result 1 (hash + URL checks) — return no existing.
        if call_count <= 2:
            return _no_existing()
        # Third call (hash check for result 2) raises an error.
        raise RuntimeError("DB error on second result")

    session.execute = AsyncMock(side_effect=execute_side_effect)

    signals = await scraper.save_to_database(session, results)

    # Result 1 should have been saved; result 2 error is swallowed (continue).
    assert len(signals) == 1
    assert session.add.call_count == 1
