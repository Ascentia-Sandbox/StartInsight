"""Comment model for Sprint 5.1 - Community Engagement Features.

Enables insight discussions with threaded comments, voting, and moderation.
"""

from datetime import datetime
from typing import TYPE_CHECKING
from uuid import UUID, uuid4

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text, func, Boolean
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

if TYPE_CHECKING:
    from app.models.user import User
    from app.models.insight import Insight


class Comment(Base):
    """
    Comment model for insight discussions.

    Supports:
    - Threaded replies (parent_id)
    - Upvoting/downvoting (vote_score)
    - Moderation (status, flagged)
    - Edit history (edited_at)
    """

    __tablename__ = "comments"

    # Primary key
    id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        primary_key=True,
        default=uuid4,
        doc="Unique identifier for this comment",
    )

    # Content
    content: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        doc="Comment text content (Markdown supported)",
    )

    # Relationships
    insight_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("insights.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        doc="Insight this comment belongs to",
    )

    user_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        doc="User who wrote this comment",
    )

    # Threading (for nested replies)
    parent_id: Mapped[UUID | None] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("comments.id", ondelete="CASCADE"),
        nullable=True,
        index=True,
        doc="Parent comment ID for threaded replies",
    )

    # Depth tracking for thread display
    depth: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
        doc="Nesting depth (0=top level, 1=reply, 2=reply to reply, etc.)",
    )

    # Voting
    vote_score: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
        index=True,
        doc="Net vote score (upvotes - downvotes)",
    )

    upvote_count: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
        doc="Total upvotes",
    )

    downvote_count: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
        doc="Total downvotes",
    )

    # Moderation
    status: Mapped[str] = mapped_column(
        String(20),
        default="active",
        nullable=False,
        index=True,
        doc="Status: active, hidden, deleted, flagged",
    )

    flagged: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
        doc="Whether this comment has been flagged for review",
    )

    flag_reason: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
        doc="Reason for flagging",
    )

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
        index=True,
        doc="When comment was created",
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
        doc="Last update timestamp",
    )

    edited_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        doc="When comment was last edited by author",
    )

    # ORM Relationships
    user: Mapped["User"] = relationship(
        "User",
        lazy="selectin",
        doc="User who wrote this comment",
    )

    insight: Mapped["Insight"] = relationship(
        "Insight",
        lazy="selectin",
        doc="Insight this comment belongs to",
    )

    parent: Mapped["Comment | None"] = relationship(
        "Comment",
        remote_side=[id],
        back_populates="replies",
        lazy="selectin",
        doc="Parent comment (if reply)",
    )

    replies: Mapped[list["Comment"]] = relationship(
        "Comment",
        back_populates="parent",
        lazy="selectin",
        cascade="all, delete-orphan",
        doc="Reply comments",
    )

    votes: Mapped[list["CommentVote"]] = relationship(
        "CommentVote",
        back_populates="comment",
        lazy="selectin",
        cascade="all, delete-orphan",
        doc="Votes on this comment",
    )

    def __repr__(self) -> str:
        return f"<Comment(id={self.id}, user_id={self.user_id}, score={self.vote_score})>"


class CommentVote(Base):
    """
    Vote record for comments.

    Tracks individual user votes to prevent double-voting.
    """

    __tablename__ = "comment_votes"

    # Primary key
    id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        primary_key=True,
        default=uuid4,
    )

    # Relationships
    comment_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("comments.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    user_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Vote value
    vote_type: Mapped[str] = mapped_column(
        String(10),
        nullable=False,
        doc="Vote type: 'up' or 'down'",
    )

    # Timestamp
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    # ORM Relationships
    comment: Mapped["Comment"] = relationship(
        "Comment",
        back_populates="votes",
    )

    user: Mapped["User"] = relationship(
        "User",
        lazy="selectin",
    )

    def __repr__(self) -> str:
        return f"<CommentVote(comment_id={self.comment_id}, user_id={self.user_id}, type={self.vote_type})>"
