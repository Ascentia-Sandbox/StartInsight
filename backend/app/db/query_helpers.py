"""Database query helper functions.

Utility functions for common query patterns like filtering active users,
handling soft deletes, etc.
"""

from sqlalchemy import Select
from sqlalchemy.orm import Query

from app.models import User


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
