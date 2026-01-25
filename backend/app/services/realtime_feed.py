"""Real-time Insight Feed - Phase 5.4.

Provides real-time updates for new insights using:
- Server-Sent Events (SSE) for real-time streaming
- Polling fallback for WebSocket-incompatible environments
- Supabase Realtime integration (when deployed to Supabase Cloud)
"""

import asyncio
import json
import logging
from datetime import datetime
from typing import Any, AsyncGenerator
from uuid import UUID

from pydantic import BaseModel, Field

from app.core.config import settings

logger = logging.getLogger(__name__)


# ============================================================
# Message Types
# ============================================================


class InsightFeedMessage(BaseModel):
    """Real-time insight feed message."""

    event_type: str = Field(description="Event type: new_insight, update, delete")
    insight_id: str = Field(description="Insight UUID")
    timestamp: str = Field(description="ISO timestamp")
    data: dict[str, Any] = Field(description="Event payload")


class FeedSubscription(BaseModel):
    """Feed subscription configuration."""

    user_id: str | None = Field(default=None, description="User ID for personalized feed")
    filters: dict[str, Any] = Field(
        default_factory=dict,
        description="Optional filters (min_score, categories)",
    )
    last_event_id: str | None = Field(
        default=None, description="Last received event ID for reconnection"
    )


# ============================================================
# In-Memory Event Store (for development/single-instance)
# ============================================================


class EventStore:
    """Simple in-memory event store for development."""

    def __init__(self, max_events: int = 1000):
        self._events: list[InsightFeedMessage] = []
        self._max_events = max_events
        self._subscribers: dict[str, asyncio.Queue] = {}
        self._lock = asyncio.Lock()

    async def add_event(self, event: InsightFeedMessage) -> None:
        """Add an event to the store and notify subscribers."""
        async with self._lock:
            self._events.append(event)
            # Trim old events
            if len(self._events) > self._max_events:
                self._events = self._events[-self._max_events:]

        # Notify all subscribers
        for subscriber_id, queue in list(self._subscribers.items()):
            try:
                await queue.put(event)
            except Exception as e:
                logger.error(f"Failed to notify subscriber {subscriber_id}: {e}")

    async def subscribe(self, subscriber_id: str) -> asyncio.Queue:
        """Subscribe to events and return a queue."""
        async with self._lock:
            if subscriber_id in self._subscribers:
                # Return existing subscription
                return self._subscribers[subscriber_id]

            queue: asyncio.Queue = asyncio.Queue(maxsize=100)
            self._subscribers[subscriber_id] = queue
            logger.info(f"Subscriber {subscriber_id} connected")
            return queue

    async def unsubscribe(self, subscriber_id: str) -> None:
        """Unsubscribe from events."""
        async with self._lock:
            if subscriber_id in self._subscribers:
                del self._subscribers[subscriber_id]
                logger.info(f"Subscriber {subscriber_id} disconnected")

    def get_recent_events(self, count: int = 10) -> list[InsightFeedMessage]:
        """Get recent events for catch-up."""
        return self._events[-count:]

    @property
    def subscriber_count(self) -> int:
        """Get current subscriber count."""
        return len(self._subscribers)


# Global event store instance
_event_store: EventStore | None = None


def get_event_store() -> EventStore:
    """Get or create the global event store."""
    global _event_store
    if _event_store is None:
        _event_store = EventStore()
    return _event_store


# ============================================================
# Subscription Management
# ============================================================


async def subscribe_to_insights(
    subscriber_id: str,
    filters: dict[str, Any] | None = None,
) -> asyncio.Queue:
    """
    Subscribe to real-time insight updates.

    Args:
        subscriber_id: Unique subscriber identifier
        filters: Optional filters for the feed

    Returns:
        asyncio.Queue: Queue that receives InsightFeedMessage objects
    """
    store = get_event_store()
    return await store.subscribe(subscriber_id)


async def unsubscribe_from_insights(subscriber_id: str) -> None:
    """
    Unsubscribe from insight updates.

    Args:
        subscriber_id: Subscriber identifier to remove
    """
    store = get_event_store()
    await store.unsubscribe(subscriber_id)


# ============================================================
# Event Publishing
# ============================================================


async def publish_new_insight(
    insight_id: str,
    insight_data: dict[str, Any],
) -> None:
    """
    Publish a new insight event to all subscribers.

    Args:
        insight_id: The insight UUID
        insight_data: Insight data to include in event
    """
    event = InsightFeedMessage(
        event_type="new_insight",
        insight_id=insight_id,
        timestamp=datetime.now().isoformat(),
        data=insight_data,
    )

    store = get_event_store()
    await store.add_event(event)
    logger.info(f"Published new insight event: {insight_id}")


async def publish_insight_update(
    insight_id: str,
    update_data: dict[str, Any],
) -> None:
    """
    Publish an insight update event.

    Args:
        insight_id: The insight UUID
        update_data: Updated fields
    """
    event = InsightFeedMessage(
        event_type="update",
        insight_id=insight_id,
        timestamp=datetime.now().isoformat(),
        data=update_data,
    )

    store = get_event_store()
    await store.add_event(event)


async def publish_insight_delete(insight_id: str) -> None:
    """
    Publish an insight deletion event.

    Args:
        insight_id: The deleted insight UUID
    """
    event = InsightFeedMessage(
        event_type="delete",
        insight_id=insight_id,
        timestamp=datetime.now().isoformat(),
        data={},
    )

    store = get_event_store()
    await store.add_event(event)


# ============================================================
# SSE Generator
# ============================================================


async def generate_sse_stream(
    subscriber_id: str,
    filters: dict[str, Any] | None = None,
) -> AsyncGenerator[str, None]:
    """
    Generate Server-Sent Events stream for insight updates.

    Args:
        subscriber_id: Unique subscriber ID
        filters: Optional event filters

    Yields:
        str: SSE-formatted event strings
    """
    store = get_event_store()
    queue = await store.subscribe(subscriber_id)

    # Send initial connection message
    yield f"event: connected\ndata: {json.dumps({'subscriber_id': subscriber_id, 'timestamp': datetime.now().isoformat()})}\n\n"

    # Send recent events for catch-up
    recent = store.get_recent_events(count=5)
    for event in recent:
        yield f"event: {event.event_type}\ndata: {event.model_dump_json()}\n\n"

    try:
        while True:
            try:
                # Wait for new events with timeout for keepalive
                event = await asyncio.wait_for(queue.get(), timeout=30.0)

                # Apply filters if provided
                if filters:
                    min_score = filters.get("min_score")
                    if min_score and event.data.get("relevance_score", 1) < min_score:
                        continue

                # Format as SSE
                yield f"event: {event.event_type}\ndata: {event.model_dump_json()}\n\n"

            except asyncio.TimeoutError:
                # Send keepalive ping
                yield f"event: ping\ndata: {json.dumps({'timestamp': datetime.now().isoformat()})}\n\n"

    except asyncio.CancelledError:
        logger.info(f"SSE stream cancelled for {subscriber_id}")
    finally:
        await store.unsubscribe(subscriber_id)


# ============================================================
# Polling Endpoint Data
# ============================================================


def get_recent_insights(
    since: datetime | None = None,
    limit: int = 20,
) -> list[InsightFeedMessage]:
    """
    Get recent insight events for polling fallback.

    Args:
        since: Only return events after this timestamp
        limit: Maximum events to return

    Returns:
        list[InsightFeedMessage]: Recent events
    """
    store = get_event_store()
    events = store.get_recent_events(count=limit)

    if since:
        events = [
            e for e in events
            if datetime.fromisoformat(e.timestamp) > since
        ]

    return events


# ============================================================
# Feed Statistics
# ============================================================


def get_feed_stats() -> dict[str, Any]:
    """Get real-time feed statistics."""
    store = get_event_store()
    return {
        "subscriber_count": store.subscriber_count,
        "recent_event_count": len(store.get_recent_events(100)),
        "status": "healthy",
    }
