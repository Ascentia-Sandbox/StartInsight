"""Tenant model for Phase 7.3 - White-label & Multi-tenancy.

Enables white-label deployments with custom branding and subdomain routing.
"""

from datetime import datetime
from typing import TYPE_CHECKING
from uuid import uuid4

from sqlalchemy import DateTime, ForeignKey, Integer, String, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

if TYPE_CHECKING:
    from app.models.user import User


class Tenant(Base):
    """Tenant model for multi-tenancy support.

    Each tenant can have custom branding, domain, and isolated data.
    """

    __tablename__ = "tenants"

    id: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid4,
    )

    # Tenant identification
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

    # Domain configuration
    subdomain: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
        unique=True,
        index=True,
    )  # e.g., "acme" for acme.startinsight.ai
    custom_domain: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
        unique=True,
    )  # e.g., "insights.acme.com"
    custom_domain_verified: Mapped[bool] = mapped_column(
        default=False,
        nullable=False,
    )

    # Branding
    logo_url: Mapped[str | None] = mapped_column(
        String(500),
        nullable=True,
    )
    favicon_url: Mapped[str | None] = mapped_column(
        String(500),
        nullable=True,
    )
    primary_color: Mapped[str | None] = mapped_column(
        String(7),  # #RRGGBB
        nullable=True,
    )
    secondary_color: Mapped[str | None] = mapped_column(
        String(7),
        nullable=True,
    )
    accent_color: Mapped[str | None] = mapped_column(
        String(7),
        nullable=True,
    )

    # Custom content
    app_name: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
    )  # Override "StartInsight" branding
    tagline: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )
    support_email: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )
    terms_url: Mapped[str | None] = mapped_column(
        String(500),
        nullable=True,
    )
    privacy_url: Mapped[str | None] = mapped_column(
        String(500),
        nullable=True,
    )

    # Feature flags
    features: Mapped[dict] = mapped_column(
        JSONB,
        default=dict,
        nullable=False,
    )  # enable_research, enable_teams, enable_export, etc.

    # Limits
    max_users: Mapped[int] = mapped_column(
        Integer,
        default=100,
        nullable=False,
    )
    max_teams: Mapped[int] = mapped_column(
        Integer,
        default=10,
        nullable=False,
    )
    max_api_keys: Mapped[int] = mapped_column(
        Integer,
        default=5,
        nullable=False,
    )

    # Status
    status: Mapped[str] = mapped_column(
        String(50),
        default="active",
        nullable=False,
    )  # active, suspended, pending, trial

    # Billing
    billing_email: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )
    stripe_customer_id: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    # Owner
    owner_id: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    # Extra data
    tenant_metadata: Mapped[dict] = mapped_column(
        JSONB,
        default=dict,
        nullable=False,
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
        back_populates="owned_tenants",
    )
    users: Mapped[list["TenantUser"]] = relationship(
        "TenantUser",
        back_populates="tenant",
        cascade="all, delete-orphan",
    )


class TenantUser(Base):
    """Association between tenants and users."""

    __tablename__ = "tenant_users"

    id: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid4,
    )

    tenant_id: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("tenants.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    user_id: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Role within tenant
    role: Mapped[str] = mapped_column(
        String(50),
        default="user",
        nullable=False,
    )  # owner, admin, user

    # Status
    status: Mapped[str] = mapped_column(
        String(50),
        default="active",
        nullable=False,
    )  # active, suspended, pending

    # Timestamps
    joined_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    # Relationships
    tenant: Mapped["Tenant"] = relationship(
        "Tenant",
        back_populates="users",
    )
    user: Mapped["User"] = relationship(
        "User",
        back_populates="tenant_memberships",
    )
