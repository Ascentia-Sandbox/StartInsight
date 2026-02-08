"""Community models for Phase 9.3: Validation Acceleration.

Provides:
- IdeaVote: Upvote/downvote ideas
- IdeaComment: Discussion threads on ideas
- CommentUpvote: Upvotes on comments
- IdeaPoll: Quick polls on ideas
- PollResponse: User poll responses
"""

from datetime import datetime
from typing import TYPE_CHECKING, Any
from uuid import UUID, uuid4

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, Text, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

if TYPE_CHECKING:
    from app.models.insight import Insight
    from app.models.user import User


class IdeaVote(Base):
    """User vote on an idea (upvote/downvote)."""

    __tablename__ = "idea_votes"

    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    user_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    insight_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), ForeignKey("insights.id", ondelete="CASCADE"), nullable=False)
    vote_type: Mapped[str] = mapped_column(String(10), nullable=False)  # up, down
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    # Relationships
    user: Mapped["User"] = relationship("User", foreign_keys=[user_id], lazy="selectin")
    insight: Mapped["Insight"] = relationship("Insight", foreign_keys=[insight_id], lazy="selectin")

    # Vote type constants
    VOTE_UP = "up"
    VOTE_DOWN = "down"

    def __repr__(self) -> str:
        return f"<IdeaVote(user={self.user_id}, insight={self.insight_id}, type={self.vote_type})>"


class IdeaComment(Base):
    """User comment on an idea with threading support."""

    __tablename__ = "idea_comments"

    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    user_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    insight_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), ForeignKey("insights.id", ondelete="CASCADE"), nullable=False)
    parent_id: Mapped[UUID | None] = mapped_column(PGUUID(as_uuid=True), ForeignKey("idea_comments.id", ondelete="CASCADE"), nullable=True)

    # Comment content
    content: Mapped[str] = mapped_column(Text, nullable=False)
    upvotes: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    # Badges and moderation
    is_expert: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    is_pinned: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    is_deleted: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    # Relationships
    user: Mapped["User"] = relationship("User", foreign_keys=[user_id], lazy="selectin")
    insight: Mapped["Insight"] = relationship("Insight", foreign_keys=[insight_id], lazy="selectin")
    parent: Mapped["IdeaComment | None"] = relationship("IdeaComment", remote_side=[id], back_populates="replies", lazy="selectin")
    replies: Mapped[list["IdeaComment"]] = relationship("IdeaComment", back_populates="parent", lazy="selectin")

    def __repr__(self) -> str:
        return f"<IdeaComment(user={self.user_id}, insight={self.insight_id})>"


class CommentUpvote(Base):
    """User upvote on a comment."""

    __tablename__ = "comment_upvotes"

    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    user_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    comment_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), ForeignKey("idea_comments.id", ondelete="CASCADE"), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    # Relationships
    user: Mapped["User"] = relationship("User", foreign_keys=[user_id], lazy="selectin")
    comment: Mapped["IdeaComment"] = relationship("IdeaComment", foreign_keys=[comment_id], lazy="selectin")

    def __repr__(self) -> str:
        return f"<CommentUpvote(user={self.user_id}, comment={self.comment_id})>"


class IdeaPoll(Base):
    """Quick poll on an idea for validation."""

    __tablename__ = "idea_polls"

    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    insight_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), ForeignKey("insights.id", ondelete="CASCADE"), nullable=False)
    created_by: Mapped[UUID | None] = mapped_column(PGUUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)

    # Poll content
    question: Mapped[str] = mapped_column(String(255), nullable=False)
    poll_type: Mapped[str] = mapped_column(String(20), default="yes_no", nullable=False)  # yes_no, scale, multiple
    options: Mapped[dict[str, Any] | None] = mapped_column(JSONB, nullable=True)

    # Status
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    # Timestamp
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    # Relationships
    insight: Mapped["Insight"] = relationship("Insight", foreign_keys=[insight_id], lazy="selectin")
    creator: Mapped["User | None"] = relationship("User", foreign_keys=[created_by], lazy="selectin")
    responses: Mapped[list["PollResponse"]] = relationship("PollResponse", back_populates="poll", cascade="all, delete-orphan", lazy="selectin")

    # Poll type constants
    TYPE_YES_NO = "yes_no"
    TYPE_SCALE = "scale"
    TYPE_MULTIPLE = "multiple"

    def __repr__(self) -> str:
        return f"<IdeaPoll(insight={self.insight_id}, question={self.question[:30]})>"


class PollResponse(Base):
    """User response to a poll."""

    __tablename__ = "poll_responses"

    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    poll_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), ForeignKey("idea_polls.id", ondelete="CASCADE"), nullable=False)
    user_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    response: Mapped[str] = mapped_column(String(100), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    # Relationships
    poll: Mapped["IdeaPoll"] = relationship("IdeaPoll", back_populates="responses")
    user: Mapped["User"] = relationship("User", foreign_keys=[user_id], lazy="selectin")

    def __repr__(self) -> str:
        return f"<PollResponse(poll={self.poll_id}, user={self.user_id})>"
