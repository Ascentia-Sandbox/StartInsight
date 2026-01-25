"""User service - Business logic for user workspace operations.

Encapsulates SavedInsight get-or-create logic to eliminate duplication.
Replaces 4 identical patterns in users.py endpoints.
"""

from datetime import datetime
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.saved_insight import SavedInsight
from app.models.user import User


class UserService:
    """Service layer for user workspace operations."""

    @staticmethod
    async def get_or_create_saved_insight(
        db: AsyncSession,
        user_id: UUID,
        insight_id: UUID,
        status: str = "saved",
        notes: str | None = None,
        tags: list[str] | None = None,
        claimed_at: datetime | None = None,
    ) -> SavedInsight:
        """
        Get existing SavedInsight or create new one.

        Replaces the repeated pattern:
        ```python
        result = await db.execute(
            select(SavedInsight).where(
                SavedInsight.user_id == user_id,
                SavedInsight.insight_id == insight_id,
            )
        )
        saved_insight = result.scalar_one_or_none()

        if saved_insight:
            saved_insight.status = status
        else:
            saved_insight = SavedInsight(...)
            db.add(saved_insight)
        ```

        Args:
            db: Database session
            user_id: User UUID
            insight_id: Insight UUID
            status: SavedInsight status (saved, interested, building, not_interested)
            notes: Optional personal notes
            tags: Optional tags list
            claimed_at: Optional claim timestamp (for status="building")

        Returns:
            SavedInsight (existing or newly created)
        """
        # Check if already saved
        result = await db.execute(
            select(SavedInsight).where(
                SavedInsight.user_id == user_id,
                SavedInsight.insight_id == insight_id,
            )
        )
        saved_insight = result.scalar_one_or_none()

        if saved_insight:
            # Update existing
            saved_insight.status = status
            if notes is not None:
                saved_insight.notes = notes
            if tags is not None:
                saved_insight.tags = tags
            if claimed_at is not None:
                saved_insight.claimed_at = claimed_at
        else:
            # Create new
            saved_insight = SavedInsight(
                user_id=user_id,
                insight_id=insight_id,
                status=status,
                notes=notes,
                tags=tags or [],
                claimed_at=claimed_at,
            )
            db.add(saved_insight)

        await db.commit()
        await db.refresh(saved_insight)

        return saved_insight

    @staticmethod
    async def increment_share_count(
        db: AsyncSession,
        user_id: UUID,
        insight_id: UUID,
    ) -> SavedInsight:
        """
        Increment share count for a SavedInsight.

        Gets or creates SavedInsight and increments shared_count.

        Args:
            db: Database session
            user_id: User UUID
            insight_id: Insight UUID

        Returns:
            SavedInsight with incremented share count
        """
        result = await db.execute(
            select(SavedInsight).where(
                SavedInsight.user_id == user_id,
                SavedInsight.insight_id == insight_id,
            )
        )
        saved_insight = result.scalar_one_or_none()

        if saved_insight:
            saved_insight.shared_count += 1
        else:
            saved_insight = SavedInsight(
                user_id=user_id,
                insight_id=insight_id,
                shared_count=1,
            )
            db.add(saved_insight)

        await db.commit()
        await db.refresh(saved_insight)

        return saved_insight
