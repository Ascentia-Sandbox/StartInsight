"""SavedInsight database model - User workspace functionality.

Phase 4.1: Allows users to save, organize, and track insights.
See architecture.md Section "Database Schema Extensions" for full specification.
"""

from datetime import datetime
from uuid import UUID, uuid4

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text, UniqueConstraint, func
from sqlalchemy.dialects.postgresql import ARRAY, JSONB, UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class SavedInsight(Base):
    """
    SavedInsight model - User's saved insights workspace.

    Allows users to:
    - Save insights for later review
    - Add personal notes and tags
    - Track insight status (interested, saved, building)
    - Claim ideas they're pursuing

    RLS Policy: Users can only access their own saved insights.
    """

    __tablename__ = "saved_insights"

    # Composite unique constraint
    __table_args__ = (
        UniqueConstraint("user_id", "insight_id", name="uq_user_insight"),
    )

    # Primary key
    id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        primary_key=True,
        default=uuid4,
        doc="Unique identifier for this saved insight record",
    )

    # Foreign keys
    user_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        doc="User who saved this insight",
    )

    insight_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("insights.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        doc="The saved insight",
    )

    # User notes and organization
    notes: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
        doc="User's personal notes about this insight",
    )

    tags: Mapped[list[str] | None] = mapped_column(
        ARRAY(String(50)),
        nullable=True,
        default=list,
        doc="User-defined tags for organization",
    )

    # Status tracking (IdeaBrowser parity)
    status: Mapped[str] = mapped_column(
        String(20),
        default="saved",
        nullable=False,
        index=True,
        doc="Status: interested, saved, building, not_interested",
    )

    # Claim tracking (for "I'm building this")
    claimed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        doc="When user claimed this idea (status=building)",
    )

    # Timestamps
    saved_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
        index=True,
        doc="When user saved this insight",
    )

    # Share tracking
    shared_count: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
        doc="Number of times user shared this insight",
    )

    # Relationships
    user: Mapped["User"] = relationship(
        "User",
        back_populates="saved_insights",
        lazy="selectin",
        doc="User who saved this insight",
    )

    insight: Mapped["Insight"] = relationship(
        "Insight",
        lazy="selectin",
        doc="The saved insight",
    )

    def __repr__(self) -> str:
        """String representation of SavedInsight."""
        return (
            f"<SavedInsight(user_id={self.user_id}, "
            f"insight_id={self.insight_id}, "
            f"status='{self.status}')>"
        )

    def to_dict(self) -> dict:
        """Convert to dictionary for API responses."""
        return {
            "id": str(self.id),
            "insight_id": str(self.insight_id),
            "notes": self.notes,
            "tags": self.tags or [],
            "status": self.status,
            "claimed_at": self.claimed_at.isoformat() if self.claimed_at else None,
            "saved_at": self.saved_at.isoformat() if self.saved_at else None,
            "shared_count": self.shared_count,
        }
