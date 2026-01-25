"""API dependencies for authentication and authorization.

Phase 4.1: Supabase Auth integration with JWT verification.
See architecture.md "Authentication Architecture" for full specification.
"""

import logging
from enum import Enum
from typing import Annotated

from fastapi import Depends, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError, jwt
from redis import asyncio as aioredis
from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.db.session import get_db
from app.models.user import User

logger = logging.getLogger(__name__)

# Redis client for role caching
_redis_client: aioredis.Redis | None = None


async def get_redis() -> aioredis.Redis:
    """Get Redis client for caching (lazy initialization)."""
    global _redis_client
    if _redis_client is None:
        _redis_client = await aioredis.from_url(
            settings.redis_url,
            encoding="utf-8",
            decode_responses=True,
        )
    return _redis_client

# HTTP Bearer token scheme
security = HTTPBearer(auto_error=False)


class UserRole(str, Enum):
    """User authorization roles."""

    USER = "user"
    MODERATOR = "moderator"
    ADMIN = "admin"


async def get_current_user_optional(
    request: Request,
    credentials: HTTPAuthorizationCredentials | None = Depends(security),
    db: AsyncSession = Depends(get_db),
) -> User | None:
    """
    Get current user if authenticated (optional).

    Used for endpoints that work for both authenticated and anonymous users.

    Args:
        request: FastAPI request object
        credentials: Bearer token from Authorization header
        db: Database session

    Returns:
        User object if authenticated, None otherwise
    """
    if not credentials:
        return None

    try:
        return await _verify_and_get_user(credentials.credentials, db)
    except HTTPException:
        return None


async def get_current_user(
    request: Request,
    credentials: HTTPAuthorizationCredentials | None = Depends(security),
    db: AsyncSession = Depends(get_db),
) -> User:
    """
    Get current authenticated user (required).

    Verifies JWT token from Supabase Auth and returns user.
    Creates user record on first login (JIT provisioning).

    Args:
        request: FastAPI request object
        credentials: Bearer token from Authorization header
        db: Database session

    Returns:
        Authenticated User object

    Raises:
        HTTPException: 401 if not authenticated
    """
    if not credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return await _verify_and_get_user(credentials.credentials, db)


async def require_admin(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> User:
    """
    Require admin role for endpoint access.

    Uses Redis cache (60s TTL) to avoid N+1 queries on admin dashboard.

    Args:
        user: Current authenticated user
        db: Database session

    Returns:
        User if admin

    Raises:
        HTTPException: 403 if not admin
    """
    # Check Redis cache first (1-minute TTL)
    cache_key = f"admin_role:{user.id}"
    try:
        redis = await get_redis()
        is_admin_cached = await redis.get(cache_key)

        if is_admin_cached == "1":
            return user
    except Exception as e:
        # Redis failure shouldn't break auth - log and continue to DB check
        logger.warning(f"Redis cache check failed: {e}")

    # Cache miss or Redis unavailable - check database
    from app.models.admin_user import AdminUser

    result = await db.execute(select(AdminUser).where(AdminUser.user_id == user.id))
    admin_record = result.scalar_one_or_none()

    if not admin_record:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required",
        )

    # Cache result for 60 seconds (reduces DB load on admin dashboard)
    try:
        redis = await get_redis()
        await redis.setex(cache_key, 60, "1")
    except Exception as e:
        logger.warning(f"Redis cache write failed: {e}")

    return user


async def _verify_and_get_user(token: str, db: AsyncSession) -> User:
    """
    Verify Supabase JWT token and get/create user.

    Args:
        token: JWT access token from Supabase Auth
        db: Database session

    Returns:
        User object

    Raises:
        HTTPException: 401 if token invalid
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid authentication credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    # Verify JWT secret is configured
    if not settings.jwt_secret:
        logger.error("JWT_SECRET not configured")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Authentication not configured",
        )

    try:
        # Decode and verify JWT with full validation
        payload = jwt.decode(
            token,
            settings.jwt_secret,
            algorithms=[settings.jwt_algorithm],
            audience="authenticated",  # Supabase default audience
            issuer=settings.supabase_url,  # Validate token issuer
            options={
                'verify_exp': True,      # ✅ Check expiration
                'verify_aud': True,      # ✅ Check audience
                'verify_iss': True,      # ✅ Check issuer
                'require_exp': True,     # ✅ Require exp claim
                'require_sub': True,     # ✅ Require sub claim
            }
        )

        # Extract user info from JWT payload
        supabase_user_id: str = payload.get("sub")
        email: str = payload.get("email")

        if not supabase_user_id:
            raise credentials_exception

        # ✅ Verify email is confirmed (security best practice)
        email_confirmed_at = payload.get("email_confirmed_at")
        if not email_confirmed_at:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Email verification required. Please check your inbox and verify your email.",
                headers={"WWW-Authenticate": "Bearer"},
            )

    except JWTError as e:
        logger.warning(f"JWT verification failed: {e}")
        raise credentials_exception

    # Find or create user (JIT provisioning) - atomic UPSERT prevents race conditions
    stmt = insert(User).values(
        supabase_user_id=supabase_user_id,
        email=email or f"{supabase_user_id}@supabase.auth",
        display_name=payload.get("user_metadata", {}).get("full_name"),
        avatar_url=payload.get("user_metadata", {}).get("avatar_url"),
        preferences={},
    ).on_conflict_do_update(
        index_elements=['supabase_user_id'],
        set_={
            'email': email or f"{supabase_user_id}@supabase.auth",
            'display_name': payload.get("user_metadata", {}).get("full_name"),
            'avatar_url': payload.get("user_metadata", {}).get("avatar_url"),
        }
    ).returning(User)

    result = await db.execute(stmt)
    user = result.scalar_one()
    await db.commit()

    # ✅ Check if user is soft-deleted (account deactivated)
    if user.deleted_at is not None:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account has been deactivated. Contact support for assistance.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    logger.info(f"Authenticated user: {user.email}")
    return user


# Type aliases for cleaner dependency injection
CurrentUser = Annotated[User, Depends(get_current_user)]
OptionalUser = Annotated[User | None, Depends(get_current_user_optional)]
AdminUser = Annotated[User, Depends(require_admin)]
