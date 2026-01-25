"""Team models for Phase 6.4 - Team Collaboration.

Enables team workspaces with shared insights and member management.
"""

from datetime import datetime
from typing import TYPE_CHECKING
from uuid import uuid4

from sqlalchemy import DateTime, ForeignKey, String, Text, UniqueConstraint, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

if TYPE_CHECKING:
    from app.models.user import User
    from app.models.insight import Insight


class Team(Base):
    """Team model for collaborative workspaces.

    Teams can have multiple members with different roles and share insights.
    """

    __tablename__ = "teams"

    id: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid4,
    )

    # Team details
    name: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )
    slug: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        unique=True,
        index=True,
    )
    description: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    # Owner (creator)
    owner_id: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Team settings
    settings: Mapped[dict] = mapped_column(
        JSONB,
        default=dict,
        nullable=False,
    )  # max_members, default_permissions, etc.

    # Branding (Phase 7.3)
    logo_url: Mapped[str | None] = mapped_column(
        String(500),
        nullable=True,
    )
    primary_color: Mapped[str | None] = mapped_column(
        String(7),  # #RRGGBB
        nullable=True,
    )

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    # Relationships
    owner: Mapped["User"] = relationship(
        "User",
        foreign_keys=[owner_id],
        back_populates="owned_teams",
    )
    members: Mapped[list["TeamMember"]] = relationship(
        "TeamMember",
        back_populates="team",
        cascade="all, delete-orphan",
    )
    shared_insights: Mapped[list["SharedInsight"]] = relationship(
        "SharedInsight",
        back_populates="team",
        cascade="all, delete-orphan",
    )
    invitations: Mapped[list["TeamInvitation"]] = relationship(
        "TeamInvitation",
        back_populates="team",
        cascade="all, delete-orphan",
    )


class TeamMember(Base):
    """Team membership with role-based permissions."""

    __tablename__ = "team_members"
    __table_args__ = (
        UniqueConstraint("team_id", "user_id", name="uq_team_member"),
    )

    id: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid4,
    )

    team_id: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("teams.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    user_id: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Role and permissions
    role: Mapped[str] = mapped_column(
        String(50),
        default="member",
        nullable=False,
    )  # owner, admin, member, viewer

    permissions: Mapped[dict] = mapped_column(
        JSONB,
        default=dict,
        nullable=False,
    )  # can_invite, can_share, can_export, etc.

    # Timestamps
    joined_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    # Relationships
    team: Mapped["Team"] = relationship(
        "Team",
        back_populates="members",
    )
    user: Mapped["User"] = relationship(
        "User",
        back_populates="team_memberships",
    )


class TeamInvitation(Base):
    """Team invitation for adding new members."""

    __tablename__ = "team_invitations"
    __table_args__ = (
        UniqueConstraint("team_id", "email", name="uq_team_invitation"),
    )

    id: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid4,
    )

    team_id: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("teams.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    invited_by_id: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Invitation details
    email: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        index=True,
    )
    role: Mapped[str] = mapped_column(
        String(50),
        default="member",
        nullable=False,
    )

    # Token for email link
    token: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        unique=True,
        index=True,
    )

    # Status
    status: Mapped[str] = mapped_column(
        String(50),
        default="pending",
        nullable=False,
    )  # pending, accepted, expired, revoked

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    expires_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
    )
    accepted_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    # Relationships
    team: Mapped["Team"] = relationship(
        "Team",
        back_populates="invitations",
    )
    invited_by: Mapped["User"] = relationship(
        "User",
        foreign_keys=[invited_by_id],
    )


class SharedInsight(Base):
    """Insights shared with a team."""

    __tablename__ = "shared_insights"
    __table_args__ = (
        UniqueConstraint("team_id", "insight_id", name="uq_shared_insight"),
    )

    id: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid4,
    )

    team_id: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("teams.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    insight_id: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("insights.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    shared_by_id: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Share details
    notes: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )
    permissions: Mapped[dict] = mapped_column(
        JSONB,
        default=dict,
        nullable=False,
    )  # can_edit, can_comment, can_reshare

    # Timestamps
    shared_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    # Relationships
    team: Mapped["Team"] = relationship(
        "Team",
        back_populates="shared_insights",
    )
    insight: Mapped["Insight"] = relationship(
        "Insight",
        back_populates="team_shares",
    )
    shared_by: Mapped["User"] = relationship(
        "User",
        foreign_keys=[shared_by_id],
    )
