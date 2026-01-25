"""Research Request database model - Admin queue for user-submitted research requests.

Phase 5.2: Super Admin Sovereignty
- Users submit research requests (queued for admin approval)
- Admins review queue, approve/reject with notes
- Analysis triggered only after admin approval
- Preserves tier-based quotas (Free 1/mo, Starter 3/mo, Pro 10/mo, Enterprise 100/mo)
"""

from datetime import datetime
from uuid import UUID, uuid4

from sqlalchemy import DateTime, ForeignKey, String, Text, func
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class ResearchRequest(Base):
    """
    Research Request model - User-submitted research requests pending admin approval.

    Workflow:
    1. User submits request via POST /api/research/request
    2. Free tier: Status = 'pending' (requires manual admin approval)
    3. Paid tiers: Status = 'approved' (auto-approved)
    4. Admin reviews queue, approves/rejects
    5. On approval, analysis is triggered and analysis_id is set
    6. Status transitions: pending -> approved/rejected -> completed
    """

    __tablename__ = "research_requests"

    # Primary key
    id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        primary_key=True,
        default=uuid4,
        doc="Unique identifier for this research request",
    )

    # User who submitted the request
    user_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        doc="User who submitted the request",
    )

    # Admin who reviewed the request (nullable until reviewed)
    admin_id: Mapped[UUID | None] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
        doc="Admin who reviewed/approved this request",
    )

    # Request status
    status: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="pending",
        index=True,
        doc="Status: pending, approved, rejected, completed",
    )

    # Request details (from user)
    idea_description: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        doc="User's startup idea description",
    )

    target_market: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
        doc="Target market for the idea",
    )

    budget_range: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
        doc="Budget range for execution",
    )

    # Admin review
    admin_notes: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
        doc="Admin notes explaining approval/rejection reasoning",
    )

    # Link to generated analysis (after approval)
    analysis_id: Mapped[UUID | None] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("custom_analyses.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
        doc="Link to the completed analysis (set after analysis completes)",
    )

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
        index=True,
        doc="When the request was submitted",
    )

    reviewed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        doc="When the request was reviewed by admin",
    )

    completed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        doc="When the analysis was completed",
    )

    # Relationships
    user: Mapped["User"] = relationship(
        "User",
        foreign_keys=[user_id],
        back_populates="research_requests",
        lazy="selectin",
        doc="User who submitted the request",
    )

    admin: Mapped["User"] = relationship(
        "User",
        foreign_keys=[admin_id],
        lazy="selectin",
        doc="Admin who reviewed the request",
    )

    analysis: Mapped["CustomAnalysis"] = relationship(
        "CustomAnalysis",
        back_populates="request",
        lazy="selectin",
        doc="The completed analysis (if approved)",
    )

    def __repr__(self) -> str:
        """String representation of ResearchRequest."""
        return (
            f"<ResearchRequest(id={self.id}, "
            f"user_id={self.user_id}, "
            f"status='{self.status}', "
            f"created_at={self.created_at})>"
        )

    def __str__(self) -> str:
        """Human-readable string representation."""
        return f"Research Request: {self.idea_description[:100]} ({self.status})"
