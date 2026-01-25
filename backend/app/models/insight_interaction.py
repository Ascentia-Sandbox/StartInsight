"""InsightInteraction model - Phase 4.4 analytics tracking.

Tracks user interactions with insights:
- view: User viewed insight details
- interested: User marked as interested
- claim: User claimed to build
- share: User shared insight
- export: User exported insight (PDF, etc.)

See architecture.md Section 5 for schema specification.
"""

from datetime import datetime
from uuid import UUID, uuid4

from sqlalchemy import DateTime, ForeignKey, String, func
from sqlalchemy.dialects.postgresql import JSONB, UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class InsightInteraction(Base):
    """
    InsightInteraction model - Tracks user interactions for analytics.

    Interaction types:
    - view: Viewed insight details
    - interested: Marked as interested
    - claim: Claimed to build
    - share: Shared via social/link
    - export: Exported to PDF/CSV
    """

    __tablename__ = "insight_interactions"

    # Primary key
    id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        primary_key=True,
        default=uuid4,
        doc="Unique identifier for this interaction",
    )

    # Foreign keys
    user_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        doc="User who performed the interaction",
    )

    insight_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("insights.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        doc="Insight that was interacted with",
    )

    # Interaction type
    interaction_type: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        index=True,
        doc="Type: view, interested, claim, share, export",
    )

    # Additional metadata (e.g., share platform, export format)
    extra_metadata: Mapped[dict] = mapped_column(
        JSONB,
        nullable=False,
        default=dict,
        doc="Additional context (e.g., share platform, export format)",
    )

    # Timestamp
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
        index=True,
        doc="When the interaction occurred",
    )

    # Relationships
    user: Mapped["User"] = relationship(
        "User",
        back_populates="interactions",
        lazy="selectin",
        doc="User who performed this interaction",
    )

    insight: Mapped["Insight"] = relationship(
        "Insight",
        back_populates="interactions",
        lazy="selectin",
        doc="Insight that was interacted with",
    )

    def __repr__(self) -> str:
        """String representation of InsightInteraction."""
        return (
            f"<InsightInteraction(id={self.id}, "
            f"user_id={self.user_id}, "
            f"type={self.interaction_type})>"
        )

    def __str__(self) -> str:
        """Human-readable string representation."""
        return f"Interaction: {self.interaction_type} on insight {self.insight_id}"
