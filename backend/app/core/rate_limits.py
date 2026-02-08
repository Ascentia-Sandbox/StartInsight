"""Rate limiting configuration using SlowAPI with tier-based limits.

Uses Redis for distributed rate limiting with user-aware key generation.
Subscription tiers get different rate limits:
- Anonymous: 20/minute
- Free:       30/minute
- Starter:    60/minute
- Pro:       120/minute
- Enterprise: 300/minute
"""

import logging

from fastapi import Request
from slowapi import Limiter
from slowapi.util import get_remote_address

from app.core.config import settings

logger = logging.getLogger(__name__)

import os

# Tier-based rate limit configuration (requests per minute)
TIER_RATE_LIMITS: dict[str, str] = {
    "anonymous": os.environ.get("RATE_LIMIT_TIER_ANONYMOUS", "20/minute"),
    "free": os.environ.get("RATE_LIMIT_TIER_FREE", "30/minute"),
    "starter": os.environ.get("RATE_LIMIT_TIER_STARTER", "60/minute"),
    "pro": os.environ.get("RATE_LIMIT_TIER_PRO", "120/minute"),
    "enterprise": os.environ.get("RATE_LIMIT_TIER_ENTERPRISE", "300/minute"),
}

# Default for unknown tiers
DEFAULT_RATE_LIMIT = "30/minute"


def get_identifier(request: Request) -> str:
    """
    Get rate limit identifier from request.

    Uses authenticated user ID if available, falls back to IP address.
    """
    # Try to get authenticated user from request state
    if hasattr(request.state, "user") and request.state.user:
        user_id = getattr(request.state.user, "id", None)
        if user_id:
            return f"user:{user_id}"

    # Fallback to IP address
    return get_remote_address(request)


def get_tier_rate_limit(request: Request) -> str:
    """
    Get dynamic rate limit based on user's subscription tier.

    Returns the rate limit string for SlowAPI based on the authenticated
    user's subscription_tier field.
    """
    if hasattr(request.state, "user") and request.state.user:
        tier = getattr(request.state.user, "subscription_tier", "free")
        return TIER_RATE_LIMITS.get(tier, DEFAULT_RATE_LIMIT)

    return TIER_RATE_LIMITS["anonymous"]


# Initialize SlowAPI limiter with Redis backend
limiter = Limiter(
    key_func=get_identifier,
    storage_uri=settings.redis_url,
    default_limits=["100/minute", "1000/hour"],  # Global defaults
    enabled=True,
)
