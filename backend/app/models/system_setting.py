"""SystemSetting database model - Admin system settings.

Phase G: System settings for admin portal configuration.
Stores key-value pairs grouped by category (general, email, features, pipeline, ai).
"""

from datetime import datetime
from typing import TYPE_CHECKING, Any
from uuid import UUID, uuid4

from sqlalchemy import DateTime, ForeignKey, String, Text, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

if TYPE_CHECKING:
    from app.models.user import User


class SystemSetting(Base):
    """
    SystemSetting model - Key-value configuration store.

    Categories:
    - general: Site name, tagline, branding
    - email: Sender addresses, digest settings
    - features: Feature flags (community voting, gamification, etc.)
    - pipeline: Scraping intervals, batch sizes, thresholds
    - ai: Model selection, temperature, token limits

    All values stored as JSONB to support any JSON-serializable type.
    """

    __tablename__ = "system_settings"

    # Primary key
    id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        primary_key=True,
        default=uuid4,
        doc="Unique identifier for this setting",
    )

    # Setting key (unique, indexed)
    key: Mapped[str] = mapped_column(
        String(255),
        unique=True,
        index=True,
        nullable=False,
        doc="Unique setting key (e.g., 'general.site_name')",
    )

    # Setting value (JSONB for flexible types)
    value: Mapped[Any] = mapped_column(
        JSONB,
        nullable=False,
        doc="Setting value (string, number, boolean, or object)",
    )

    # Category for grouping
    category: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        index=True,
        doc="Setting category: general, email, features, pipeline, ai",
    )

    # Human-readable description
    description: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
        doc="Human-readable description of what this setting controls",
    )

    # Tracking fields
    updated_by: Mapped[UUID | None] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        doc="User who last updated this setting",
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
        doc="When this setting was last updated",
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
        doc="When this setting was created",
    )

    # Relationships
    updater: Mapped["User | None"] = relationship(
        "User",
        foreign_keys=[updated_by],
        lazy="selectin",
        doc="User who last updated this setting",
    )

    def __repr__(self) -> str:
        """String representation of SystemSetting."""
        return f"<SystemSetting(key='{self.key}', category='{self.category}')>"
