"""User database model - Phase 4.1 authentication and user management.

Integrates with Supabase Auth for authentication.
See architecture.md Section "Database Schema Extensions" for full specification.
"""

from datetime import datetime
from uuid import UUID, uuid4

from sqlalchemy import DateTime, String, Text, func
from sqlalchemy.dialects.postgresql import JSONB, UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class User(Base):
    """
    User model - Stores authenticated user profiles.

    Authentication is handled by Supabase Auth. This table stores:
    - User profile information (synced from Supabase Auth)
    - Subscription tier (free, starter, pro, enterprise)
    - User preferences (stored as JSONB)

    RLS Policy: Users can only read/update their own record.
    """

    __tablename__ = "users"

    # Primary key
    id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        primary_key=True,
        default=uuid4,
        doc="Unique identifier for this user",
    )

    # Supabase Auth integration
    supabase_user_id: Mapped[str] = mapped_column(
        String(255),
        unique=True,
        nullable=False,
        index=True,
        doc="Supabase Auth user ID (auth.users.id)",
    )

    # Profile information
    email: Mapped[str] = mapped_column(
        String(255),
        unique=True,
        nullable=False,
        index=True,
        doc="User email address",
    )

    display_name: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
        doc="User display name",
    )

    avatar_url: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
        doc="URL to user avatar image",
    )

    # Subscription tier (Phase 6 payments)
    subscription_tier: Mapped[str] = mapped_column(
        String(20),
        default="free",
        nullable=False,
        index=True,
        doc="Subscription tier: free, starter, pro, enterprise",
    )

    # User preferences (theme, notifications, etc.)
    preferences: Mapped[dict] = mapped_column(
        JSONB,
        default=dict,
        nullable=False,
        doc="User preferences as JSON (theme, email_digest, etc.)",
    )

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
        index=True,
        doc="When user registered",
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
        doc="Last profile update",
    )

    last_login_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        doc="Most recent login timestamp",
    )

    # Soft delete support (prevents permanent data loss)
    deleted_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        index=True,
        doc="Soft delete timestamp (NULL = active, non-NULL = deleted)",
    )

    deleted_by: Mapped[UUID | None] = mapped_column(
        PGUUID(as_uuid=True),
        nullable=True,
        doc="Admin who deleted this user (audit trail)",
    )

    deletion_reason: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
        doc="Reason for deletion (GDPR request, ban, abuse, etc.)",
    )

    # Relationships
    saved_insights: Mapped[list["SavedInsight"]] = relationship(
        "SavedInsight",
        back_populates="user",
        lazy="selectin",
        cascade="all, delete-orphan",
        doc="User's saved insights",
    )

    ratings: Mapped[list["UserRating"]] = relationship(
        "UserRating",
        back_populates="user",
        lazy="selectin",
        cascade="all, delete-orphan",
        doc="User's insight ratings",
    )

    interactions: Mapped[list["InsightInteraction"]] = relationship(
        "InsightInteraction",
        back_populates="user",
        lazy="selectin",
        cascade="all, delete-orphan",
        doc="User's insight interactions (Phase 4.4)",
    )

    custom_analyses: Mapped[list["CustomAnalysis"]] = relationship(
        "CustomAnalysis",
        back_populates="user",
        lazy="selectin",
        cascade="all, delete-orphan",
        doc="User's custom research analyses (Phase 5.1)",
    )

    # Phase 6.1: Subscription relationship
    subscription: Mapped["Subscription"] = relationship(
        "Subscription",
        back_populates="user",
        uselist=False,
        lazy="selectin",
        doc="User's active subscription (Phase 6.1)",
    )

    # Phase 6.4: Team relationships
    owned_teams: Mapped[list["Team"]] = relationship(
        "Team",
        foreign_keys="Team.owner_id",
        back_populates="owner",
        lazy="selectin",
        doc="Teams owned by this user (Phase 6.4)",
    )

    team_memberships: Mapped[list["TeamMember"]] = relationship(
        "TeamMember",
        back_populates="user",
        lazy="selectin",
        cascade="all, delete-orphan",
        doc="Team memberships (Phase 6.4)",
    )

    # Phase 7.2: API Key relationships
    api_keys: Mapped[list["APIKey"]] = relationship(
        "APIKey",
        back_populates="user",
        lazy="selectin",
        cascade="all, delete-orphan",
        doc="User's API keys (Phase 7.2)",
    )

    # Phase 7.3: Tenant relationships
    owned_tenants: Mapped[list["Tenant"]] = relationship(
        "Tenant",
        foreign_keys="Tenant.owner_id",
        back_populates="owner",
        lazy="selectin",
        doc="Tenants owned by this user (Phase 7.3)",
    )

    tenant_memberships: Mapped[list["TenantUser"]] = relationship(
        "TenantUser",
        back_populates="user",
        lazy="selectin",
        cascade="all, delete-orphan",
        doc="Tenant memberships (Phase 7.3)",
    )

    def __repr__(self) -> str:
        """String representation of User."""
        return f"<User(id={self.id}, email='{self.email}', tier='{self.subscription_tier}')>"

    def __str__(self) -> str:
        """Human-readable string representation."""
        return f"User: {self.email}"

    def to_dict(self) -> dict:
        """Convert to dictionary for API responses."""
        return {
            "id": str(self.id),
            "email": self.email,
            "display_name": self.display_name,
            "avatar_url": self.avatar_url,
            "subscription_tier": self.subscription_tier,
            "preferences": self.preferences,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
