"""Rate limiting configuration using SlowAPI - Code simplification Phase 2.

Replaces custom 353-line rate_limiter.py with battle-tested SlowAPI library.
Uses Redis for distributed rate limiting with user-aware key generation.

SlowAPI provides:
- FastAPI-native decorators
- Redis backend support
- Automatic 429 responses
- Per-route rate limits
- User-aware limiting (authenticated user ID or IP fallback)
"""

import logging
from typing import Callable

from fastapi import Request
from slowapi import Limiter
from slowapi.util import get_remote_address

from app.core.config import settings

logger = logging.getLogger(__name__)


def get_identifier(request: Request) -> str:
    """
    Get rate limit identifier from request.

    Uses authenticated user ID if available, falls back to IP address.

    Args:
        request: FastAPI request object

    Returns:
        Rate limit key (user_id or IP address)
    """
    # Try to get authenticated user from request state
    if hasattr(request.state, "user") and request.state.user:
        user_id = getattr(request.state.user, "id", None)
        if user_id:
            return f"user:{user_id}"

    # Fallback to IP address
    return get_remote_address(request)


# Initialize SlowAPI limiter with Redis backend
limiter = Limiter(
    key_func=get_identifier,
    storage_uri=settings.redis_url,
    default_limits=["100/minute", "1000/hour"],  # Global defaults
    enabled=True,
)
