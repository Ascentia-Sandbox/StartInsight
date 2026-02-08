"""Content Review models for Phase 8.1: Content Quality Management.

Provides:
- ContentReviewQueue: AI content review workflow
- ContentSimilarity: Duplicate detection tracking
"""

from datetime import datetime
from decimal import Decimal
from typing import TYPE_CHECKING
from uuid import UUID, uuid4

from sqlalchemy import Boolean, DateTime, ForeignKey, Numeric, String, Text, UniqueConstraint, func
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

if TYPE_CHECKING:
    from app.models.insight import Insight
    from app.models.user import User


class ContentReviewQueue(Base):
    """
    AI Content Review Queue for human oversight of AI-generated content.

    Workflow:
    1. AI generates content → automatically queued
    2. Quality score assigned (0.00-1.00)
    3. Auto-approval if score >= 0.85
    4. Human review for lower scores
    5. Approval/rejection with notes

    RLS Policy: Admin access only
    """

    __tablename__ = "content_review_queue"
    __table_args__ = (
        UniqueConstraint("content_type", "content_id", name="uq_content_review"),
    )

    id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        primary_key=True,
        default=uuid4,
    )

    content_type: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        index=True,
        comment="Content type: insight, research, brand_package",
    )

    content_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        nullable=False,
        comment="ID of the content being reviewed",
    )

    status: Mapped[str] = mapped_column(
        String(20),
        default="pending",
        nullable=False,
        index=True,
        comment="Review status: pending, approved, rejected, flagged",
    )

    quality_score: Mapped[Decimal | None] = mapped_column(
        Numeric(3, 2),
        nullable=True,
        comment="AI-assigned quality score 0.00-1.00",
    )

    auto_approved: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
        comment="True if automatically approved based on quality score",
    )

    reviewer_id: Mapped[UUID | None] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )

    review_notes: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
        comment="Notes from the reviewer",
    )

    rejection_reason: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
        comment="Reason for rejection if rejected",
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    reviewed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        comment="When the review was completed",
    )

    # Relationships
    reviewer: Mapped["User | None"] = relationship(
        "User",
        foreign_keys=[reviewer_id],
        lazy="selectin",
    )

    # Auto-approval thresholds
    AUTO_APPROVE_THRESHOLD = Decimal("0.85")
    AUTO_FLAG_THRESHOLD = Decimal("0.40")

    def should_auto_approve(self) -> bool:
        """Check if content should be auto-approved based on quality score."""
        if self.quality_score is None:
            return False
        return self.quality_score >= self.AUTO_APPROVE_THRESHOLD

    def should_auto_flag(self) -> bool:
        """Check if content should be auto-flagged for review."""
        if self.quality_score is None:
            return True
        return self.quality_score <= self.AUTO_FLAG_THRESHOLD

    def __repr__(self) -> str:
        return f"<ContentReviewQueue(id={self.id}, type={self.content_type}, status={self.status})>"


class ContentSimilarity(Base):
    """
    Tracks similar/duplicate insights for deduplication.

    Uses cosine similarity on TF-IDF vectors of problem_statement.
    Threshold: 0.85 for near-duplicates.

    RLS Policy: Admin access only
    """

    __tablename__ = "content_similarity"
    __table_args__ = (
        UniqueConstraint("source_insight_id", "similar_insight_id", name="uq_similarity_pair"),
    )

    id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        primary_key=True,
        default=uuid4,
    )

    source_insight_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("insights.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    similar_insight_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("insights.id", ondelete="CASCADE"),
        nullable=False,
    )

    similarity_score: Mapped[Decimal] = mapped_column(
        Numeric(4, 3),
        nullable=False,
        comment="Cosine similarity 0.000-1.000",
    )

    similarity_type: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        comment="Similarity type: exact, near, thematic",
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    resolved: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
        index=True,
    )

    resolution: Mapped[str | None] = mapped_column(
        String(20),
        nullable=True,
        comment="Resolution: keep_both, merge, delete_newer",
    )

    # Relationships
    source_insight: Mapped["Insight"] = relationship(
        "Insight",
        foreign_keys=[source_insight_id],
        lazy="selectin",
    )

    similar_insight: Mapped["Insight"] = relationship(
        "Insight",
        foreign_keys=[similar_insight_id],
        lazy="selectin",
    )

    # Similarity thresholds
    EXACT_THRESHOLD = Decimal("0.95")
    NEAR_THRESHOLD = Decimal("0.85")
    THEMATIC_THRESHOLD = Decimal("0.70")

    @classmethod
    def classify_similarity(cls, score: Decimal) -> str:
        """Classify similarity type based on score."""
        if score >= cls.EXACT_THRESHOLD:
            return "exact"
        elif score >= cls.NEAR_THRESHOLD:
            return "near"
        else:
            return "thematic"

    def __repr__(self) -> str:
        return f"<ContentSimilarity(source={self.source_insight_id}, similar={self.similar_insight_id}, score={self.similarity_score})>"
