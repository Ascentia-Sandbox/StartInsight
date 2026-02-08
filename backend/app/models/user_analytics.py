"""User Analytics models for Phase 8.3: User & Revenue Intelligence.

Provides:
- UserActivityEvent: User behavior tracking
- UserSession: Session analytics
"""

from datetime import datetime
from typing import TYPE_CHECKING, Any
from uuid import UUID, uuid4

from sqlalchemy import DateTime, ForeignKey, Integer, String, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

if TYPE_CHECKING:
    from app.models.user import User


class UserActivityEvent(Base):
    """Tracks individual user actions for analytics."""

    __tablename__ = "user_activity_events"

    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    user_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    event_type: Mapped[str] = mapped_column(String(50), nullable=False, index=True, comment="page_view, feature_use, insight_save, etc.")
    event_data: Mapped[dict[str, Any] | None] = mapped_column(JSONB, nullable=True)
    session_id: Mapped[str | None] = mapped_column(String(100), nullable=True, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    # Relationships
    user: Mapped["User"] = relationship("User", lazy="selectin")

    # Event type constants
    PAGE_VIEW = "page_view"
    FEATURE_USE = "feature_use"
    INSIGHT_SAVE = "insight_save"
    INSIGHT_VIEW = "insight_view"
    RESEARCH_START = "research_start"
    EXPORT = "export"
    UPGRADE = "upgrade"

    def __repr__(self) -> str:
        return f"<UserActivityEvent(user={self.user_id}, type={self.event_type})>"


class UserSession(Base):
    """Tracks user sessions for analytics."""

    __tablename__ = "user_sessions"

    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    user_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    session_id: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    ended_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    duration_seconds: Mapped[int | None] = mapped_column(Integer, nullable=True)
    page_views: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    events_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    device_type: Mapped[str | None] = mapped_column(String(20), nullable=True)
    referrer: Mapped[str | None] = mapped_column(String(500), nullable=True)

    # Relationships
    user: Mapped["User"] = relationship("User", lazy="selectin")

    def __repr__(self) -> str:
        return f"<UserSession(user={self.user_id}, session={self.session_id})>"
