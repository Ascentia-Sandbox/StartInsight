"""User Preferences models for Phase 9.1: User Attraction Features.

Provides:
- UserPreferences: Idea matching and personalization
- EmailPreferences: Digest and alert settings
- EmailSend: Email delivery tracking
"""

from datetime import datetime
from decimal import Decimal
from typing import TYPE_CHECKING
from uuid import UUID, uuid4

from sqlalchemy import Boolean, DateTime, ForeignKey, Numeric, String, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

if TYPE_CHECKING:
    from app.models.user import User


class UserPreferences(Base):
    """User preferences for idea matching and personalization."""

    __tablename__ = "user_preferences"

    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    user_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), unique=True, nullable=False)

    # Idea match quiz fields
    background: Mapped[str | None] = mapped_column(String(50), nullable=True)  # tech, business, creative, other
    budget_range: Mapped[str | None] = mapped_column(String(20), nullable=True)  # 0-1k, 1k-10k, 10k+
    time_commitment: Mapped[str | None] = mapped_column(String(20), nullable=True)  # nights_weekends, part_time, full_time
    market_preference: Mapped[str | None] = mapped_column(String(10), nullable=True)  # b2b, b2c, both
    risk_tolerance: Mapped[str | None] = mapped_column(String(10), nullable=True)  # low, medium, high

    # Extended profile
    skills: Mapped[list[str] | None] = mapped_column(JSONB, nullable=True)
    interests: Mapped[list[str] | None] = mapped_column(JSONB, nullable=True)

    # Quiz completion tracking
    completed_quiz: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    # Relationships
    user: Mapped["User"] = relationship("User", foreign_keys=[user_id], lazy="selectin")

    # Background options
    BACKGROUND_TECH = "tech"
    BACKGROUND_BUSINESS = "business"
    BACKGROUND_CREATIVE = "creative"
    BACKGROUND_OTHER = "other"

    # Budget range options
    BUDGET_LOW = "0-1k"
    BUDGET_MEDIUM = "1k-10k"
    BUDGET_HIGH = "10k+"

    # Time commitment options
    TIME_NIGHTS = "nights_weekends"
    TIME_PART = "part_time"
    TIME_FULL = "full_time"

    # Market preference options
    MARKET_B2B = "b2b"
    MARKET_B2C = "b2c"
    MARKET_BOTH = "both"

    # Risk tolerance options
    RISK_LOW = "low"
    RISK_MEDIUM = "medium"
    RISK_HIGH = "high"

    def __repr__(self) -> str:
        return f"<UserPreferences(user={self.user_id}, quiz={self.completed_quiz})>"


class EmailPreferences(Base):
    """Email digest and alert preferences."""

    __tablename__ = "email_preferences"

    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    user_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), unique=True, nullable=False)

    # Digest settings
    daily_digest: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    weekly_digest: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    instant_alerts: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    # Alert configuration
    tracked_keywords: Mapped[list[str] | None] = mapped_column(JSONB, nullable=True)
    min_score_alert: Mapped[Decimal] = mapped_column(Numeric(3, 2), default=Decimal("0.85"), nullable=False)

    # Timing preferences
    digest_time_utc: Mapped[str] = mapped_column(String(5), default="09:00", nullable=False)
    timezone: Mapped[str] = mapped_column(String(50), default="UTC", nullable=False)

    # Unsubscribe tracking
    unsubscribed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    # Relationships
    user: Mapped["User"] = relationship("User", foreign_keys=[user_id], lazy="selectin")

    def __repr__(self) -> str:
        return f"<EmailPreferences(user={self.user_id}, daily={self.daily_digest})>"


class EmailSend(Base):
    """Email delivery tracking for analytics."""

    __tablename__ = "email_sends"

    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    user_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)

    # Email details
    email_type: Mapped[str] = mapped_column(String(50), nullable=False)  # daily_digest, weekly_digest, instant_alert
    subject: Mapped[str | None] = mapped_column(String(255), nullable=True)
    content_hash: Mapped[str | None] = mapped_column(String(64), nullable=True)  # Prevent duplicate sends

    # Tracking
    sent_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    opened_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    clicked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    # Relationships
    user: Mapped["User"] = relationship("User", foreign_keys=[user_id], lazy="selectin")

    # Email type constants
    TYPE_DAILY_DIGEST = "daily_digest"
    TYPE_WEEKLY_DIGEST = "weekly_digest"
    TYPE_INSTANT_ALERT = "instant_alert"

    def __repr__(self) -> str:
        return f"<EmailSend(user={self.user_id}, type={self.email_type})>"
