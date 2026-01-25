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
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.db.session import get_db
from app.models.user import User

logger = logging.getLogger(__name__)

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

    Args:
        user: Current authenticated user
        db: Database session

    Returns:
        User if admin

    Raises:
        HTTPException: 403 if not admin
    """
    # Import here to avoid circular imports
    from app.models.admin_user import AdminUser

    # Check admin_users table
    result = await db.execute(select(AdminUser).where(AdminUser.user_id == user.id))
    admin_record = result.scalar_one_or_none()

    if not admin_record:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required",
        )

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
        # Decode and verify JWT
        payload = jwt.decode(
            token,
            settings.jwt_secret,
            algorithms=[settings.jwt_algorithm],
            audience="authenticated",  # Supabase default audience
        )

        # Extract user info from JWT payload
        supabase_user_id: str = payload.get("sub")
        email: str = payload.get("email")

        if not supabase_user_id:
            raise credentials_exception

    except JWTError as e:
        logger.warning(f"JWT verification failed: {e}")
        raise credentials_exception

    # Find or create user (JIT provisioning)
    result = await db.execute(
        select(User).where(User.supabase_user_id == supabase_user_id)
    )
    user = result.scalar_one_or_none()

    if not user:
        # First login - create user record
        user = User(
            supabase_user_id=supabase_user_id,
            email=email or f"{supabase_user_id}@supabase.auth",
            display_name=payload.get("user_metadata", {}).get("full_name"),
            avatar_url=payload.get("user_metadata", {}).get("avatar_url"),
            preferences={},
        )
        db.add(user)
        await db.commit()
        await db.refresh(user)
        logger.info(f"Created new user: {user.email}")

    return user


# Type aliases for cleaner dependency injection
CurrentUser = Annotated[User, Depends(get_current_user)]
OptionalUser = Annotated[User | None, Depends(get_current_user_optional)]
AdminUser = Annotated[User, Depends(require_admin)]
