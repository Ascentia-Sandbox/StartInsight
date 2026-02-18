"""Social models for Phase 9.5: Social & Community Features.

Provides:
- FounderProfile: Public founder profiles
- FounderConnection: Connection requests between founders
- IdeaClub: Topic-based communities
- ClubMember: Club membership
- ClubPost: Club discussion posts
"""

from datetime import datetime
from typing import TYPE_CHECKING
from uuid import UUID, uuid4

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, Text, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

if TYPE_CHECKING:
    from app.models.insight import Insight
    from app.models.user import User


class FounderProfile(Base):
    """Public profile for founders."""

    __tablename__ = "founder_profiles"

    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    user_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), unique=True, nullable=False)

    # Profile info
    username: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    display_name: Mapped[str | None] = mapped_column(String(100), nullable=True)
    bio: Mapped[str | None] = mapped_column(Text, nullable=True)
    avatar_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    location: Mapped[str | None] = mapped_column(String(100), nullable=True)

    # Skills and interests
    skills: Mapped[list[str] | None] = mapped_column(JSONB, nullable=True)
    interests: Mapped[list[str] | None] = mapped_column(JSONB, nullable=True)
    social_links: Mapped[dict[str, str] | None] = mapped_column(JSONB, nullable=True)  # {twitter, linkedin, github}

    # Visibility settings
    is_public: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    accepting_connections: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    # Stats
    connection_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    # Relationships
    user: Mapped["User"] = relationship("User", foreign_keys=[user_id], lazy="selectin")

    def __repr__(self) -> str:
        return f"<FounderProfile(username={self.username}, public={self.is_public})>"


class FounderConnection(Base):
    """Connection request between founders."""

    __tablename__ = "founder_connections"

    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    requester_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    recipient_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)

    # Connection state
    status: Mapped[str] = mapped_column(String(20), default="pending", nullable=False)  # pending, accepted, rejected
    message: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    responded_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    # Relationships
    requester: Mapped["User"] = relationship("User", foreign_keys=[requester_id], lazy="selectin")
    recipient: Mapped["User"] = relationship("User", foreign_keys=[recipient_id], lazy="selectin")

    # Status constants
    STATUS_PENDING = "pending"
    STATUS_ACCEPTED = "accepted"
    STATUS_REJECTED = "rejected"

    def __repr__(self) -> str:
        return f"<FounderConnection(requester={self.requester_id}, recipient={self.recipient_id}, status={self.status})>"


class IdeaClub(Base):
    """Topic-based community for founders."""

    __tablename__ = "idea_clubs"

    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)

    # Club info
    name: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    slug: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    category: Mapped[str | None] = mapped_column(String(50), nullable=True)
    cover_image_url: Mapped[str | None] = mapped_column(String(500), nullable=True)

    # Stats
    member_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    post_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    # Settings
    is_public: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    is_official: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    # Ownership
    created_by: Mapped[UUID | None] = mapped_column(PGUUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    # Relationships
    creator: Mapped["User | None"] = relationship("User", foreign_keys=[created_by], lazy="selectin")
    members: Mapped[list["ClubMember"]] = relationship("ClubMember", back_populates="club", cascade="all, delete-orphan", lazy="selectin")
    posts: Mapped[list["ClubPost"]] = relationship("ClubPost", back_populates="club", cascade="all, delete-orphan", lazy="selectin")

    def __repr__(self) -> str:
        return f"<IdeaClub(name={self.name}, members={self.member_count})>"


class ClubMember(Base):
    """Membership in an idea club."""

    __tablename__ = "club_members"

    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    club_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), ForeignKey("idea_clubs.id", ondelete="CASCADE"), nullable=False)
    user_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)

    # Role
    role: Mapped[str] = mapped_column(String(20), default="member", nullable=False)  # admin, moderator, member

    # Timestamp
    joined_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    # Relationships
    club: Mapped["IdeaClub"] = relationship("IdeaClub", back_populates="members")
    user: Mapped["User"] = relationship("User", foreign_keys=[user_id], lazy="selectin")

    # Role constants
    ROLE_ADMIN = "admin"
    ROLE_MODERATOR = "moderator"
    ROLE_MEMBER = "member"

    def __repr__(self) -> str:
        return f"<ClubMember(club={self.club_id}, user={self.user_id}, role={self.role})>"


class ClubPost(Base):
    """Discussion post in an idea club."""

    __tablename__ = "club_posts"

    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    club_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), ForeignKey("idea_clubs.id", ondelete="CASCADE"), nullable=False)
    user_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)

    # Post content
    title: Mapped[str | None] = mapped_column(String(255), nullable=True)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    post_type: Mapped[str] = mapped_column(String(20), default="discussion", nullable=False)  # discussion, idea_share, question

    # Linked idea (if sharing)
    insight_id: Mapped[UUID | None] = mapped_column(PGUUID(as_uuid=True), ForeignKey("insights.id", ondelete="SET NULL"), nullable=True)

    # Stats
    upvotes: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    comment_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    # Moderation
    is_pinned: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    is_deleted: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    # Relationships
    club: Mapped["IdeaClub"] = relationship("IdeaClub", back_populates="posts")
    user: Mapped["User"] = relationship("User", foreign_keys=[user_id], lazy="selectin")
    insight: Mapped["Insight | None"] = relationship("Insight", foreign_keys=[insight_id], lazy="selectin")

    # Post type constants
    TYPE_DISCUSSION = "discussion"
    TYPE_IDEA_SHARE = "idea_share"
    TYPE_QUESTION = "question"

    def __repr__(self) -> str:
        return f"<ClubPost(club={self.club_id}, type={self.post_type})>"
