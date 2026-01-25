"""Supabase client initialization for Phase 4+ features.

This module provides async Supabase client instances for:
- Database operations (with RLS)
- Authentication verification
- Real-time subscriptions (Phase 5+)

Region: Asia Pacific (ap-southeast-1) Singapore
"""

import logging
from datetime import datetime, timedelta
from functools import lru_cache

from supabase import create_client, Client
from supabase.lib.client_options import ClientOptions

from app.core.config import settings

logger = logging.getLogger(__name__)

# Admin client cache with TTL (10-minute expiry for key rotation safety)
_admin_client_cache: Client | None = None
_admin_client_cache_time: datetime | None = None
_ADMIN_CACHE_TTL_MINUTES = 10


@lru_cache()
def get_supabase_client() -> Client | None:
    """
    Get Supabase client with anon key (public access).

    Used for:
    - Client-side authenticated requests (with user JWT)
    - RLS-protected queries

    Returns:
        Supabase client or None if not configured
    """
    if not settings.supabase_url or not settings.supabase_anon_key:
        logger.warning("Supabase not configured. Set SUPABASE_URL and SUPABASE_ANON_KEY.")
        return None

    options = ClientOptions(
        postgrest_client_timeout=30,
        storage_client_timeout=30,
    )

    return create_client(
        settings.supabase_url,
        settings.supabase_anon_key,
        options=options,
    )


def get_supabase_admin_client() -> Client | None:
    """
    Get Supabase client with service role key (admin access).

    Uses TTL-based cache (10-minute expiry) to allow key rotation without server restart.
    This is CRITICAL for security - service role bypasses ALL RLS policies.

    Used for:
    - Server-side operations bypassing RLS
    - Admin tasks (user management, migrations)
    - Background worker tasks

    WARNING: Never expose service role key to client

    Returns:
        Supabase admin client or None if not configured
    """
    global _admin_client_cache, _admin_client_cache_time

    if not settings.supabase_url or not settings.supabase_service_role_key:
        logger.warning("Supabase admin not configured. Set SUPABASE_SERVICE_ROLE_KEY.")
        return None

    # Check if cache is valid (within TTL)
    now = datetime.utcnow()
    cache_expired = (
        _admin_client_cache_time is None
        or (now - _admin_client_cache_time) > timedelta(minutes=_ADMIN_CACHE_TTL_MINUTES)
    )

    if _admin_client_cache is None or cache_expired:
        # Create new client (cache expired or first call)
        options = ClientOptions(
            postgrest_client_timeout=30,
            storage_client_timeout=30,
        )

        _admin_client_cache = create_client(
            settings.supabase_url,
            settings.supabase_service_role_key,
            options=options,
        )
        _admin_client_cache_time = now

        if cache_expired and _admin_client_cache_time:
            logger.info("Supabase admin client cache refreshed (key rotation safety)")

    return _admin_client_cache


def verify_supabase_connection() -> bool:
    """
    Verify Supabase connection is working.

    Uses admin client to bypass RLS policies for accurate health check.

    Returns:
        True if connection successful, False otherwise
    """
    # Use admin client to bypass RLS (health check shouldn't depend on RLS policies)
    client = get_supabase_admin_client()
    if not client:
        logger.warning("Supabase admin client not configured - skipping health check")
        return False

    try:
        # Lightweight health check - just verify connection (count only, no data)
        client.table("raw_signals").select("count", count="exact").limit(0).execute()
        logger.info("Supabase connection verified (ap-southeast-1, Singapore)")
        return True
    except Exception as e:
        logger.error(f"Supabase health check failed: {type(e).__name__}: {e}")
        return False
