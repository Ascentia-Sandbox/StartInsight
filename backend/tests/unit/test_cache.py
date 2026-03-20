"""Unit tests for app.core.cache.

Covers:
- _Encoder: UUID, datetime, date, Decimal serialization
- _serialize / _deserialize: JSON round-trips with Pydantic support
- cache_get / cache_set: L1 (TTLCache) ↔ L2 (Redis)
- cache_set_with_stale / cache_get_with_fallback: stale-on-error pattern
- cache_negative / negative sentinel handling
- cached decorator: key templating, TTL resolution, cache hit/miss

All I/O is async.  Redis is always mocked via @patch("app.core.cache.get_redis").
"""

import json
from datetime import UTC, date, datetime
from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import pytest
from pydantic import BaseModel

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture(autouse=True)
def reset_l1_cache():
    """Clear the global TTLCache before and after every test."""
    from app.core.cache import _l1_cache

    _l1_cache.clear()
    yield
    _l1_cache.clear()


@pytest.fixture
def mock_redis():
    """Async-mock Redis client with all methods needed by cache.py."""
    r = AsyncMock()
    r.get = AsyncMock(return_value=None)
    r.setex = AsyncMock()
    r.delete = AsyncMock()
    r.ping = AsyncMock()
    r.info = AsyncMock(return_value={"used_memory_human": "1M"})

    pipe = AsyncMock()
    # pipeline.setex / pipeline.expire are queued (synchronous call, not awaited)
    pipe.setex = MagicMock()
    pipe.execute = AsyncMock()
    r.pipeline = MagicMock(return_value=pipe)

    return r


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


class _SampleModel(BaseModel):
    """Minimal Pydantic model for serialization tests."""

    name: str
    value: int


# ---------------------------------------------------------------------------
# TestSerializer
# ---------------------------------------------------------------------------


class TestSerializer:
    """Tests for _Encoder and _serialize / _deserialize."""

    def test_encoder_uuid(self):
        """UUID instance must be serialized to its string representation."""
        from app.core.cache import _Encoder

        uid = uuid4()
        result = json.dumps({"id": uid}, cls=_Encoder)
        parsed = json.loads(result)
        assert parsed["id"] == str(uid)

    def test_encoder_datetime(self):
        """datetime must be serialized via isoformat()."""
        from app.core.cache import _Encoder

        dt = datetime(2026, 3, 20, 12, 0, 0, tzinfo=UTC)
        result = json.dumps({"ts": dt}, cls=_Encoder)
        parsed = json.loads(result)
        assert parsed["ts"] == dt.isoformat()

    def test_encoder_date(self):
        """date (without time) must be serialized via isoformat()."""
        from app.core.cache import _Encoder

        d = date(2026, 3, 20)
        result = json.dumps({"d": d}, cls=_Encoder)
        parsed = json.loads(result)
        assert parsed["d"] == d.isoformat()

    def test_encoder_decimal(self):
        """Decimal must be serialized to a float."""
        from app.core.cache import _Encoder

        val = Decimal("3.14159")
        result = json.dumps({"price": val}, cls=_Encoder)
        parsed = json.loads(result)
        assert isinstance(parsed["price"], float)
        assert abs(parsed["price"] - float(val)) < 1e-9

    def test_serialize_pydantic_model(self):
        """A single Pydantic BaseModel uses model_dump_json for serialization."""
        from app.core.cache import _deserialize, _serialize

        model = _SampleModel(name="hello", value=42)
        serialized = _serialize(model)
        assert serialized is not None
        # Must round-trip back to a dict or model with the same values
        recovered = _deserialize(serialized)
        assert recovered["name"] == "hello"
        assert recovered["value"] == 42


# ---------------------------------------------------------------------------
# TestCacheGetSet
# ---------------------------------------------------------------------------


class TestCacheGetSet:
    """Tests for cache_get and cache_set — L1 / L2 interaction."""

    async def test_cache_get_l1_hit(self, mock_redis):
        """When the key is already in _l1_cache, Redis must not be called.

        L1 stores the *deserialized* value — that is what cache_get deposits
        after a Redis hit (line: _l1_cache[key] = deserialized).  So we must
        pre-populate L1 with the plain dict, not a JSON string.
        """
        from app.core.cache import _l1_cache, cache_get

        key = "test:l1_hit"
        _l1_cache[key] = {"data": 1}  # store deserialized form, as real code does

        with patch("app.core.cache.get_redis", return_value=mock_redis):
            result = await cache_get(key)

        mock_redis.get.assert_not_called()
        assert result == {"data": 1}

    async def test_cache_get_l2_hit_promotes_to_l1(self, mock_redis):
        """When Redis has the value, it should be promoted into _l1_cache."""
        from app.core.cache import _l1_cache, _serialize, cache_get

        key = "test:l2_hit"
        payload = _serialize({"data": 2})
        mock_redis.get = AsyncMock(return_value=payload)

        with patch("app.core.cache.get_redis", return_value=mock_redis):
            result = await cache_get(key)

        assert result == {"data": 2}
        assert key in _l1_cache, "Value should have been promoted to L1 cache"

    async def test_cache_get_miss(self, mock_redis):
        """When both L1 and Redis miss, cache_get must return None."""
        from app.core.cache import cache_get

        mock_redis.get = AsyncMock(return_value=None)

        with patch("app.core.cache.get_redis", return_value=mock_redis):
            result = await cache_get("test:miss")

        assert result is None

    async def test_cache_get_redis_error_returns_none(self, mock_redis):
        """A Redis exception must be swallowed and None returned."""
        from app.core.cache import cache_get

        mock_redis.get = AsyncMock(side_effect=ConnectionError("Redis down"))

        with patch("app.core.cache.get_redis", return_value=mock_redis):
            result = await cache_get("test:redis_error")

        assert result is None

    async def test_cache_set_writes_redis_and_l1(self, mock_redis):
        """cache_set must write to Redis via setex AND populate _l1_cache."""
        from app.core.cache import _l1_cache, cache_set

        key = "test:set_both"
        value = {"answer": 42}

        with patch("app.core.cache.get_redis", return_value=mock_redis):
            success = await cache_set(key, value, ttl=60)

        assert success is True
        mock_redis.setex.assert_called_once()
        assert key in _l1_cache

    async def test_cache_set_redis_error_returns_false(self, mock_redis):
        """When Redis raises on setex, cache_set must return False without crashing."""
        from app.core.cache import cache_set

        mock_redis.setex = AsyncMock(side_effect=ConnectionError("Redis down"))

        with patch("app.core.cache.get_redis", return_value=mock_redis):
            result = await cache_set("test:set_error", {"x": 1}, ttl=60)

        assert result is False


# ---------------------------------------------------------------------------
# TestStaleOnError
# ---------------------------------------------------------------------------


class TestStaleOnError:
    """Tests for cache_set_with_stale and cache_get_with_fallback."""

    async def test_cache_set_with_stale_writes_both_keys(self, mock_redis):
        """pipeline.setex must be called twice: once for fresh, once for stale (10× TTL)."""
        from app.core.cache import cache_set_with_stale

        key = "test:stale_write"
        value = {"ok": True}
        ttl = 300

        pipe = mock_redis.pipeline.return_value

        with patch("app.core.cache.get_redis", return_value=mock_redis):
            await cache_set_with_stale(key, value, ttl=ttl)

        assert pipe.setex.call_count == 2
        calls = [call.args for call in pipe.setex.call_args_list]
        # One call must use the stale key (10× TTL)
        ttls_used = [c[1] for c in calls]  # second positional arg = TTL
        assert ttl in ttls_used
        assert ttl * 10 in ttls_used

    async def test_cache_get_with_fallback_fresh_hit(self, mock_redis):
        """When the fresh Redis key exists, it must be returned immediately."""
        from app.core.cache import _serialize, cache_get_with_fallback

        key = "test:fresh_hit"
        payload = _serialize({"fresh": True})
        mock_redis.get = AsyncMock(return_value=payload)

        with patch("app.core.cache.get_redis", return_value=mock_redis):
            result = await cache_get_with_fallback(key)

        assert result == {"fresh": True}

    async def test_cache_get_with_fallback_stale_fallback(self, mock_redis):
        """When fresh key misses but stale key hits, the stale value must be returned."""
        from app.core.cache import _serialize, cache_get_with_fallback

        key = "test:stale_fallback"
        stale_payload = _serialize({"stale": True})

        # fresh miss, stale hit
        async def fake_get(redis_key: str):
            if "stale:" in redis_key:
                return stale_payload
            return None

        mock_redis.get = AsyncMock(side_effect=fake_get)

        with patch("app.core.cache.get_redis", return_value=mock_redis):
            result = await cache_get_with_fallback(key)

        assert result == {"stale": True}

    async def test_cache_get_with_fallback_total_miss(self, mock_redis):
        """When both fresh and stale keys miss, None must be returned."""
        from app.core.cache import cache_get_with_fallback

        mock_redis.get = AsyncMock(return_value=None)

        with patch("app.core.cache.get_redis", return_value=mock_redis):
            result = await cache_get_with_fallback("test:total_miss")

        assert result is None

    async def test_cache_get_with_fallback_redis_error_returns_l1(self, mock_redis):
        """When Redis raises, the L1 cache value must be returned as fallback.

        The error-path returns `_l1_cache.get(key)` raw.  L1 stores deserialized
        dicts (as deposited by the Redis-hit path), so we pre-populate accordingly.
        """
        from app.core.cache import _l1_cache, cache_get_with_fallback

        key = "test:redis_fail_l1"
        _l1_cache[key] = {"from": "l1"}  # deserialized form, as real code stores

        mock_redis.get = AsyncMock(side_effect=ConnectionError("Redis down"))

        with patch("app.core.cache.get_redis", return_value=mock_redis):
            result = await cache_get_with_fallback(key)

        assert result == {"from": "l1"}


# ---------------------------------------------------------------------------
# TestNegativeCache
# ---------------------------------------------------------------------------


class TestNegativeCache:
    """Tests for cache_negative and the __NEG__ sentinel handling."""

    async def test_cache_negative_stores_sentinel(self, mock_redis):
        """cache_negative must store the __NEG__ sentinel string in Redis."""
        from app.core.cache import _NEGATIVE_SENTINEL, cache_negative

        key = "test:neg_sentinel"

        with patch("app.core.cache.get_redis", return_value=mock_redis):
            await cache_negative(key)

        mock_redis.setex.assert_called_once()
        call_args = mock_redis.setex.call_args
        # Value written must be the sentinel (raw bytes or string)
        written_value = call_args.args[2] if call_args.args else call_args.kwargs.get("value")
        assert _NEGATIVE_SENTINEL in str(written_value)

    async def test_cache_get_with_fallback_negative_sentinel_returns_none(self, mock_redis):
        """When Redis holds the sentinel for the fresh key, result must be None."""
        from app.core.cache import _NEGATIVE_SENTINEL, cache_get_with_fallback

        key = "test:neg_in_redis"
        # Encode exactly as the cache module would store it
        mock_redis.get = AsyncMock(return_value=_NEGATIVE_SENTINEL.encode())

        with patch("app.core.cache.get_redis", return_value=mock_redis):
            result = await cache_get_with_fallback(key)

        assert result is None

    async def test_cache_get_with_fallback_l1_negative_returns_none(self, mock_redis):
        """When L1 cache holds the sentinel, Redis must not be called and None returned."""
        from app.core.cache import _NEGATIVE_SENTINEL, _l1_cache, cache_get_with_fallback

        key = "test:neg_in_l1"
        _l1_cache[key] = _NEGATIVE_SENTINEL

        with patch("app.core.cache.get_redis", return_value=mock_redis):
            result = await cache_get_with_fallback(key)

        mock_redis.get.assert_not_called()
        assert result is None

    async def test_cache_negative_ttl_parameter(self, mock_redis):
        """A custom TTL passed to cache_negative must be forwarded to setex."""
        from app.core.cache import cache_negative

        key = "test:neg_ttl"
        custom_ttl = 777

        with patch("app.core.cache.get_redis", return_value=mock_redis):
            await cache_negative(key, ttl=custom_ttl)

        mock_redis.setex.assert_called_once()
        call_args = mock_redis.setex.call_args
        written_ttl = call_args.args[1] if call_args.args else call_args.kwargs.get("time")
        assert written_ttl == custom_ttl


# ---------------------------------------------------------------------------
# TestCachedDecorator
# ---------------------------------------------------------------------------


class TestCachedDecorator:
    """Tests for the @cached decorator."""

    async def test_cached_hit_skips_function(self, mock_redis):
        """When the cache key exists, the decorated function must NOT be called."""
        from app.core.cache import _serialize, cached

        payload = _serialize({"result": "cached_value"})
        mock_redis.get = AsyncMock(return_value=payload)

        call_count = 0

        @cached("test:decorator:hit")
        async def expensive() -> dict:
            nonlocal call_count
            call_count += 1
            return {"result": "fresh_value"}

        with patch("app.core.cache.get_redis", return_value=mock_redis):
            result = await expensive()

        assert call_count == 0
        assert result == {"result": "cached_value"}

    async def test_cached_miss_calls_function_and_caches(self, mock_redis):
        """On a cache miss, the function must be called and the result stored."""
        from app.core.cache import cached

        mock_redis.get = AsyncMock(return_value=None)
        mock_redis.setex = AsyncMock()

        call_count = 0

        @cached("test:decorator:miss", ttl=120)
        async def compute() -> dict:
            nonlocal call_count
            call_count += 1
            return {"computed": True}

        with patch("app.core.cache.get_redis", return_value=mock_redis):
            result = await compute()

        assert call_count == 1
        assert result == {"computed": True}
        mock_redis.setex.assert_called_once()

    async def test_cached_kwargs_template(self, mock_redis):
        """Key template variables must be filled from the decorated function's kwargs."""
        from app.core.cache import cached

        mock_redis.get = AsyncMock(return_value=None)
        mock_redis.setex = AsyncMock()

        captured_keys: list[str] = []

        original_setex = mock_redis.setex

        async def capture_setex(key, *args, **kwargs):
            captured_keys.append(key)

        mock_redis.setex = AsyncMock(side_effect=capture_setex)

        @cached("insights:list:{page}:{limit}", ttl=60)
        async def list_insights(page: int = 1, limit: int = 10) -> list:
            return []

        with patch("app.core.cache.get_redis", return_value=mock_redis):
            await list_insights(page=2, limit=5)

        assert len(captured_keys) == 1
        # The resolved key must contain the actual kwarg values
        resolved_key = captured_keys[0]
        assert "2" in resolved_key
        assert "5" in resolved_key

    async def test_cached_ttl_key_lookup(self, mock_redis):
        """ttl_key="tools" must cause the decorator to use CACHE_TTL["tools"]."""
        from app.core.cache import CACHE_TTL, cached

        mock_redis.get = AsyncMock(return_value=None)

        captured_ttls: list[int] = []

        async def capture_setex(key, ttl, *args, **kwargs):
            captured_ttls.append(ttl)

        mock_redis.setex = AsyncMock(side_effect=capture_setex)

        @cached("test:ttl_key", ttl_key="tools")
        async def get_tools() -> list:
            return ["tool_a"]

        with patch("app.core.cache.get_redis", return_value=mock_redis):
            await get_tools()

        assert len(captured_ttls) == 1
        assert captured_ttls[0] == CACHE_TTL["tools"]

    async def test_cached_explicit_ttl_override(self, mock_redis):
        """An explicit ttl= argument must take precedence over ttl_key lookup."""
        from app.core.cache import CACHE_TTL, cached

        mock_redis.get = AsyncMock(return_value=None)

        captured_ttls: list[int] = []

        async def capture_setex(key, ttl, *args, **kwargs):
            captured_ttls.append(ttl)

        mock_redis.setex = AsyncMock(side_effect=capture_setex)

        # ttl_key points at "tools" (3600) but explicit ttl=999 should win
        @cached("test:ttl_override", ttl=999, ttl_key="tools")
        async def get_data() -> dict:
            return {}

        assert 999 != CACHE_TTL.get("tools"), "Sanity: explicit TTL must differ from tools TTL"

        with patch("app.core.cache.get_redis", return_value=mock_redis):
            await get_data()

        assert len(captured_ttls) == 1
        assert captured_ttls[0] == 999
