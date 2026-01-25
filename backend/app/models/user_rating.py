"""UserRating database model - Insight rating and feedback.

Phase 4.1: Allows users to rate insights 1-5 stars with optional feedback.
See architecture.md Section "Database Schema Extensions" for full specification.
"""

from datetime import datetime
from uuid import UUID, uuid4

from sqlalchemy import CheckConstraint, DateTime, ForeignKey, Integer, Text, UniqueConstraint, func
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class UserRating(Base):
    """
    UserRating model - User ratings and feedback for insights.

    Allows users to:
    - Rate insights 1-5 stars
    - Provide optional text feedback
    - Track rating history

    Used for:
    - Improving AI analysis quality
    - Personalizing recommendations
    - Aggregate insight quality metrics

    RLS Policy: Users can only access their own ratings.
    """

    __tablename__ = "user_ratings"

    # Composite unique constraint (one rating per user per insight)
    __table_args__ = (
        UniqueConstraint("user_id", "insight_id", name="uq_user_insight_rating"),
        CheckConstraint("rating >= 1 AND rating <= 5", name="ck_rating_range"),
    )

    # Primary key
    id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        primary_key=True,
        default=uuid4,
        doc="Unique identifier for this rating",
    )

    # Foreign keys
    user_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        doc="User who rated this insight",
    )

    insight_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("insights.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        doc="The rated insight",
    )

    # Rating data
    rating: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        doc="Star rating 1-5 (1=poor, 5=excellent)",
    )

    feedback: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
        doc="Optional text feedback explaining the rating",
    )

    # Timestamp
    rated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
        index=True,
        doc="When this rating was created/updated",
    )

    # Relationships
    user: Mapped["User"] = relationship(
        "User",
        back_populates="ratings",
        lazy="selectin",
        doc="User who rated this insight",
    )

    insight: Mapped["Insight"] = relationship(
        "Insight",
        lazy="selectin",
        doc="The rated insight",
    )

    def __repr__(self) -> str:
        """String representation of UserRating."""
        return (
            f"<UserRating(user_id={self.user_id}, "
            f"insight_id={self.insight_id}, "
            f"rating={self.rating})>"
        )

    def to_dict(self) -> dict:
        """Convert to dictionary for API responses."""
        return {
            "id": str(self.id),
            "insight_id": str(self.insight_id),
            "rating": self.rating,
            "feedback": self.feedback,
            "rated_at": self.rated_at.isoformat() if self.rated_at else None,
        }
