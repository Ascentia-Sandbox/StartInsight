"""Supabase client initialization for Phase 4+ features.

This module provides async Supabase client instances for:
- Database operations (with RLS)
- Authentication verification
- Real-time subscriptions (Phase 5+)

Region: Asia Pacific (ap-southeast-1) Singapore
"""

import logging
from functools import lru_cache

from supabase import create_client, Client
from supabase.lib.client_options import ClientOptions

from app.core.config import settings

logger = logging.getLogger(__name__)


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


@lru_cache()
def get_supabase_admin_client() -> Client | None:
    """
    Get Supabase client with service role key (admin access).

    Used for:
    - Server-side operations bypassing RLS
    - Admin tasks (user management, migrations)
    - Background worker tasks

    WARNING: Never expose service role key to client

    Returns:
        Supabase admin client or None if not configured
    """
    if not settings.supabase_url or not settings.supabase_service_role_key:
        logger.warning("Supabase admin not configured. Set SUPABASE_SERVICE_ROLE_KEY.")
        return None

    options = ClientOptions(
        postgrest_client_timeout=30,
        storage_client_timeout=30,
    )

    return create_client(
        settings.supabase_url,
        settings.supabase_service_role_key,
        options=options,
    )


def verify_supabase_connection() -> bool:
    """
    Verify Supabase connection is working.

    Returns:
        True if connection successful, False otherwise
    """
    client = get_supabase_client()
    if not client:
        return False

    try:
        # Simple health check - list tables (will fail if no connection)
        # This is a lightweight operation that validates connectivity
        client.table("raw_signals").select("id", count="exact").limit(1).execute()
        logger.info("Supabase connection verified (ap-southeast-1)")
        return True
    except Exception as e:
        logger.error(f"Supabase connection failed: {e}")
        return False
