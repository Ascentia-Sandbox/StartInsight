"""Database query helper functions.

Utility functions for common query patterns like filtering active users,
handling soft deletes, pagination, and count queries.

Code simplification Phase 1: Added count_by_field() and paginate_query() to
eliminate 16+ duplicate count queries and 10+ pagination blocks.
"""

from typing import Any, TypeVar

from sqlalchemy import Select, func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import DeclarativeMeta, Query

from app.models import User

T = TypeVar("T", bound=DeclarativeMeta)


def active_users_only(query: Select) -> Select:
    """
    Filter query to only include active (non-deleted) users.

    Usage:
        active_users = await db.execute(
            active_users_only(select(User))
        )

    Args:
        query: SQLAlchemy select query for User model

    Returns:
        Modified query with deleted_at IS NULL filter
    """
    return query.where(User.deleted_at.is_(None))


def include_deleted_users(query: Select) -> Select:
    """
    Explicitly include deleted users in query (no filter).

    This is the default behavior, but this function makes intent clear.

    Usage:
        all_users = await db.execute(
            include_deleted_users(select(User))
        )

    Args:
        query: SQLAlchemy select query for User model

    Returns:
        Unmodified query (for explicit documentation of intent)
    """
    return query


def only_deleted_users(query: Select) -> Select:
    """
    Filter query to only include deleted users.

    Useful for admin auditing, recovery operations, or cleanup jobs.

    Usage:
        deleted_users = await db.execute(
            only_deleted_users(select(User))
        )

    Args:
        query: SQLAlchemy select query for User model

    Returns:
        Modified query with deleted_at IS NOT NULL filter
    """
    return query.where(User.deleted_at.isnot(None))


# ============================================
# CODE SIMPLIFICATION PHASE 1
# ============================================


async def count_by_field(
    db: AsyncSession,
    model: type[T],
    field: str | None = None,
    value: Any | None = None,
) -> int:
    """
    Count rows in a model, optionally filtered by a single field.

    Replaces 16+ duplicate count query patterns across routes.

    Args:
        db: Database session
        model: SQLAlchemy model class
        field: Optional field name to filter on
        value: Optional value to match

    Returns:
        Row count as integer

    Examples:
        >>> # Total saved insights
        >>> count = await count_by_field(db, SavedInsight)
        >>> # Returns: 42

        >>> # Saved insights with status="interested"
        >>> count = await count_by_field(db, SavedInsight, "status", "interested")
        >>> # Returns: 12

        >>> # Total ratings for a user
        >>> count = await count_by_field(db, UserRating, "user_id", current_user.id)
        >>> # Returns: 7
    """
    query = select(func.count()).select_from(model)

    if field and value is not None:
        query = query.where(getattr(model, field) == value)

    result = await db.scalar(query)
    return result or 0


async def paginate_query(
    db: AsyncSession,
    query: Any,
    limit: int = 20,
    offset: int = 0,
) -> tuple[list[Any], int]:
    """
    Apply pagination and execute query with total count.

    Replaces 10+ duplicate pagination blocks across routes.

    Args:
        db: Database session
        query: SQLAlchemy select query (not yet executed)
        limit: Results per page
        offset: Pagination offset

    Returns:
        Tuple of (items, total_count)

    Examples:
        >>> query = select(SavedInsight).where(SavedInsight.user_id == user.id)
        >>> items, total = await paginate_query(db, query, limit=20, offset=0)
        >>> # Returns: ([SavedInsight(...), ...], 42)

        >>> # Replaces manual pattern:
        >>> # count_query = select(func.count()).select_from(SavedInsight)...
        >>> # total = await db.scalar(count_query)
        >>> # result = await db.execute(query.limit(20).offset(0))
        >>> # items = result.scalars().all()
    """
    # Build count query from the original query
    count_query = select(func.count()).select_from(query.froms[0])

    # Apply same WHERE clauses to count query
    if query.whereclause is not None:
        count_query = count_query.where(query.whereclause)

    # Get total count
    total = await db.scalar(count_query) or 0

    # Apply pagination to original query
    paginated_query = query.limit(limit).offset(offset)
    result = await db.execute(paginated_query)
    items = result.scalars().all()

    return items, total
