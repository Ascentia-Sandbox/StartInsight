"""Real-time Feed API Routes - Phase 5.4.

Endpoints for real-time insight updates via SSE and polling.
"""

import logging
from datetime import datetime
from typing import Any
from uuid import uuid4

from fastapi import APIRouter, Depends, Query, Request
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
from sse_starlette.sse import EventSourceResponse

from app.api.deps import get_current_user_optional
from app.models import User
from app.services.realtime_feed import (
    InsightFeedMessage,
    generate_sse_stream,
    get_feed_stats,
    get_recent_insights,
    publish_new_insight,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/feed", tags=["Real-time Feed"])


# ============================================================
# Response Schemas
# ============================================================


class FeedStatusResponse(BaseModel):
    """Real-time feed status."""

    status: str = Field(description="Feed health status")
    subscriber_count: int = Field(description="Current active subscribers")
    recent_event_count: int = Field(description="Events in buffer")


class PollingResponse(BaseModel):
    """Polling endpoint response."""

    events: list[InsightFeedMessage]
    next_poll_timestamp: str = Field(description="Timestamp for next poll")
    has_more: bool = Field(description="Whether more events are available")


# ============================================================
# SSE Endpoint (Real-time)
# ============================================================


@router.get("/stream")
async def stream_insights(
    request: Request,
    min_score: float | None = Query(default=None, ge=0, le=1),
    current_user: User | None = Depends(get_current_user_optional),
) -> EventSourceResponse:
    """
    Stream real-time insight updates via Server-Sent Events (SSE).

    Optional authentication. Authenticated users get personalized feeds.
    Events include new insights, updates, and deletions.

    Usage with JavaScript:
    ```javascript
    const eventSource = new EventSource('/api/feed/stream');
    eventSource.addEventListener('new_insight', (event) => {
        const insight = JSON.parse(event.data);
        console.log('New insight:', insight);
    });
    eventSource.addEventListener('ping', () => {
        console.log('Connection alive');
    });
    ```
    """
    # Generate unique subscriber ID
    if current_user:
        subscriber_id = f"user-{current_user.id}"
    else:
        subscriber_id = f"anon-{uuid4()}"

    # Build filters
    filters = {}
    if min_score is not None:
        filters["min_score"] = min_score

    logger.info(f"SSE stream started for {subscriber_id}")

    return EventSourceResponse(
        generate_sse_stream(subscriber_id, filters),
        media_type="text/event-stream",
    )


# ============================================================
# Polling Endpoint (Fallback)
# ============================================================


@router.get("/poll", response_model=PollingResponse)
async def poll_insights(
    since: str | None = Query(
        default=None,
        description="ISO timestamp to get events after (e.g., 2025-01-01T00:00:00)",
    ),
    limit: int = Query(default=20, ge=1, le=100),
    current_user: User | None = Depends(get_current_user_optional),
) -> PollingResponse:
    """
    Poll for recent insight events.

    Fallback for environments that don't support SSE/WebSocket.
    Recommended polling interval: 30 seconds.
    """
    # Parse since timestamp
    since_dt = None
    if since:
        try:
            since_dt = datetime.fromisoformat(since.replace("Z", "+00:00"))
        except ValueError:
            pass

    events = get_recent_insights(since=since_dt, limit=limit)

    return PollingResponse(
        events=events,
        next_poll_timestamp=datetime.now().isoformat(),
        has_more=len(events) >= limit,
    )


# ============================================================
# Feed Status Endpoint
# ============================================================


@router.get("/status", response_model=FeedStatusResponse)
async def get_feed_status() -> FeedStatusResponse:
    """
    Get real-time feed health and statistics.

    Public endpoint for monitoring feed health.
    """
    stats = get_feed_stats()
    return FeedStatusResponse(
        status=stats["status"],
        subscriber_count=stats["subscriber_count"],
        recent_event_count=stats["recent_event_count"],
    )


# ============================================================
# Test Event Endpoint (Development Only)
# ============================================================


@router.post("/test-event", include_in_schema=False)
async def create_test_event(
    problem: str = "Test problem statement for real-time feed",
    score: float = 0.8,
) -> dict[str, Any]:
    """
    Create a test event for development purposes.

    Not included in production API documentation.
    """
    insight_id = str(uuid4())
    insight_data = {
        "id": insight_id,
        "problem_statement": problem,
        "relevance_score": score,
        "created_at": datetime.now().isoformat(),
    }

    await publish_new_insight(insight_id, insight_data)

    return {
        "status": "published",
        "insight_id": insight_id,
        "subscribers_notified": get_feed_stats()["subscriber_count"],
    }
