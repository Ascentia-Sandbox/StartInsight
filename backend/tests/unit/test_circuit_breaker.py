"""Unit tests for CircuitBreaker in app.scrapers.base_scraper."""

import time
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.scrapers.base_scraper import CircuitBreaker, CircuitState


@pytest.fixture
def mock_redis():
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


@pytest.fixture
def cb():
    return CircuitBreaker("test_source")


@pytest.mark.asyncio
async def test_initial_state_closed(cb, mock_redis):
    """get_state returns CLOSED when Redis key is None."""
    mock_redis.get = AsyncMock(return_value=None)
    with patch.object(CircuitBreaker, "_get_redis", return_value=mock_redis):
        state = await cb.get_state()
    assert state == CircuitState.CLOSED


@pytest.mark.asyncio
async def test_can_execute_closed(cb, mock_redis):
    """can_execute returns True when circuit is CLOSED."""
    mock_redis.get = AsyncMock(return_value=None)
    with patch.object(CircuitBreaker, "_get_redis", return_value=mock_redis):
        result = await cb.can_execute()
    assert result is True


@pytest.mark.asyncio
async def test_can_execute_open(cb, mock_redis):
    """can_execute returns False when circuit is OPEN and cooldown has not expired."""
    # The Redis client is configured with decode_responses=True, so values are str not bytes.
    # CircuitState.OPEN == "open" — mock returns the decoded lowercase string.
    opened_at = str(time.time())

    async def fake_get(key):
        if "state" in key:
            return "open"
        if "opened_at" in key:
            return opened_at
        return None

    mock_redis.get = AsyncMock(side_effect=fake_get)
    with patch.object(CircuitBreaker, "_get_redis", return_value=mock_redis):
        result = await cb.can_execute()
    assert result is False


@pytest.mark.asyncio
async def test_can_execute_half_open(cb, mock_redis):
    """can_execute returns True when circuit is HALF_OPEN."""

    async def fake_get(key):
        if "state" in key:
            return "half_open"
        return None

    mock_redis.get = AsyncMock(side_effect=fake_get)
    with patch.object(CircuitBreaker, "_get_redis", return_value=mock_redis):
        result = await cb.can_execute()
    assert result is True


@pytest.mark.asyncio
async def test_open_to_half_open_after_cooldown(cb, mock_redis):
    """State transitions from OPEN to HALF_OPEN after cooldown period expires."""
    # Redis client uses decode_responses=True — values are plain str, not bytes.
    old_opened_at = str(time.time() - 1000)

    async def fake_get(key):
        if "state" in key:
            return "open"
        if "opened_at" in key:
            return old_opened_at
        return None

    mock_redis.get = AsyncMock(side_effect=fake_get)
    with patch.object(CircuitBreaker, "_get_redis", return_value=mock_redis):
        state = await cb.get_state()
    assert state == CircuitState.HALF_OPEN


@pytest.mark.asyncio
async def test_stays_open_before_cooldown(cb, mock_redis):
    """Circuit stays OPEN when cooldown period has not elapsed."""
    # Redis client uses decode_responses=True — values are plain str, not bytes.
    recent_opened_at = str(time.time() - 100)

    async def fake_get(key):
        if "state" in key:
            return "open"
        if "opened_at" in key:
            return recent_opened_at
        return None

    mock_redis.get = AsyncMock(side_effect=fake_get)
    with patch.object(CircuitBreaker, "_get_redis", return_value=mock_redis):
        state = await cb.get_state()
    assert state == CircuitState.OPEN


@pytest.mark.asyncio
async def test_record_success_resets_to_closed(cb, mock_redis):
    """record_success sets state=CLOSED and failures=0 via pipeline."""
    pipe = mock_redis.pipeline.return_value
    with patch.object(CircuitBreaker, "_get_redis", return_value=mock_redis):
        await cb.record_success()
    mock_redis.pipeline.assert_called_once()
    pipe.execute.assert_awaited_once()
    # Verify pipeline.set was called with CLOSED state and zero failures
    set_calls = [str(call) for call in pipe.set.call_args_list]
    assert any("CLOSED" in c for c in set_calls)
    assert any("0" in c for c in set_calls)


@pytest.mark.asyncio
async def test_record_failure_increments(cb, mock_redis):
    """record_failure increments failure count; no state change below threshold."""
    mock_redis.incr = AsyncMock(return_value=1)
    with patch.object(CircuitBreaker, "_get_redis", return_value=mock_redis):
        await cb.record_failure()
    mock_redis.incr.assert_awaited_once()
    # State should not be set to OPEN (set may not be called, or not with OPEN)
    if mock_redis.set.called:
        set_calls = [str(call) for call in mock_redis.set.call_args_list]
        assert not any("OPEN" in c for c in set_calls)


@pytest.mark.asyncio
async def test_record_failure_opens_circuit(cb, mock_redis):
    """record_failure opens circuit when failure count reaches FAILURE_THRESHOLD."""
    mock_redis.incr = AsyncMock(return_value=2)
    with patch.object(CircuitBreaker, "_get_redis", return_value=mock_redis):
        await cb.record_failure()
    mock_redis.incr.assert_awaited_once()
    # Circuit should now be set to OPEN
    set_calls = [str(call) for call in mock_redis.set.call_args_list]
    assert any("OPEN" in c for c in set_calls)


@pytest.mark.asyncio
async def test_single_failure_stays_closed(cb, mock_redis):
    """One failure below threshold leaves circuit CLOSED."""
    mock_redis.incr = AsyncMock(return_value=1)
    mock_redis.get = AsyncMock(return_value=None)
    with patch.object(CircuitBreaker, "_get_redis", return_value=mock_redis):
        await cb.record_failure()
        state = await cb.get_state()
    assert state == CircuitState.CLOSED


@pytest.mark.asyncio
async def test_get_state_redis_error_returns_closed(cb):
    """get_state returns CLOSED (fail-open) when Redis raises an exception."""
    bad_redis = AsyncMock()
    bad_redis.get = AsyncMock(side_effect=Exception("Redis connection refused"))
    with patch.object(CircuitBreaker, "_get_redis", return_value=bad_redis):
        state = await cb.get_state()
    assert state == CircuitState.CLOSED


@pytest.mark.asyncio
async def test_record_failure_redis_error_no_crash(cb):
    """record_failure does not propagate exceptions when Redis is unavailable."""
    bad_redis = AsyncMock()
    bad_redis.incr = AsyncMock(side_effect=Exception("Redis unavailable"))
    with patch.object(CircuitBreaker, "_get_redis", return_value=bad_redis):
        # Should not raise
        await cb.record_failure()
