"""API Key model for Phase 7.2 - Public API & Developer Portal.

Manages API keys for external access to StartInsight's public API.
"""

from datetime import datetime
from typing import TYPE_CHECKING
from uuid import uuid4

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

if TYPE_CHECKING:
    from app.models.user import User


class APIKey(Base):
    """API key for public API access.

    Each key has rate limits, permissions, and usage tracking.
    """

    __tablename__ = "api_keys"

    id: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid4,
    )

    # Owner
    user_id: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Key details
    name: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )
    description: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    # Key value (hashed prefix for display, full hash for verification)
    key_prefix: Mapped[str] = mapped_column(
        String(12),  # First 8 chars of key for display
        nullable=False,
        index=True,
    )
    key_hash: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        unique=True,
    )

    # Permissions
    scopes: Mapped[list] = mapped_column(
        JSONB,
        default=list,
        nullable=False,
    )  # ["insights:read", "insights:write", "research:create", etc.]

    # Rate limiting
    rate_limit_per_hour: Mapped[int] = mapped_column(
        Integer,
        default=100,
        nullable=False,
    )
    rate_limit_per_day: Mapped[int] = mapped_column(
        Integer,
        default=1000,
        nullable=False,
    )

    # Usage tracking
    requests_this_hour: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
    )
    requests_this_day: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
    )
    total_requests: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
    )
    last_used_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    # Status
    is_active: Mapped[bool] = mapped_column(
        default=True,
        nullable=False,
    )
    revoked_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    revoked_reason: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    # Expiration
    expires_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    # Allowed IPs (optional whitelist)
    allowed_ips: Mapped[list | None] = mapped_column(
        JSONB,
        default=None,
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
    user: Mapped["User"] = relationship(
        "User",
        back_populates="api_keys",
    )
    usage_logs: Mapped[list["APIKeyUsageLog"]] = relationship(
        "APIKeyUsageLog",
        back_populates="api_key",
        cascade="all, delete-orphan",
    )


class APIKeyUsageLog(Base):
    """Usage log for API key requests."""

    __tablename__ = "api_key_usage_logs"

    id: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid4,
    )

    api_key_id: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("api_keys.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Request details
    endpoint: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )
    method: Mapped[str] = mapped_column(
        String(10),
        nullable=False,
    )
    status_code: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )
    response_time_ms: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )

    # Client info
    ip_address: Mapped[str | None] = mapped_column(
        String(45),  # IPv6 max length
        nullable=True,
    )
    user_agent: Mapped[str | None] = mapped_column(
        String(500),
        nullable=True,
    )

    # Timestamp
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
        index=True,
    )

    # Relationships
    api_key: Mapped["APIKey"] = relationship(
        "APIKey",
        back_populates="usage_logs",
    )
