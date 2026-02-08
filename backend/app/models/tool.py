"""Tool database model - 54-tool directory for startup resources.

Phase 12.2: IdeaBrowser Feature Replication
"""

from datetime import datetime
from uuid import UUID, uuid4

from sqlalchemy import DateTime, Integer, String, Text, Boolean, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class Tool(Base):
    """
    Tool model - Stores curated tools for startup builders.

    Represents resources like Stripe, Notion, Airtable with:
    - Name and tagline
    - Description and category
    - Pricing and website URL
    - Featured flag for homepage spotlight
    - Sort order for manual curation
    """

    __tablename__ = "tools"

    # Primary key
    id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        primary_key=True,
        default=uuid4,
        doc="Unique identifier for this tool",
    )

    # Core tool data
    name: Mapped[str] = mapped_column(
        String(200),
        nullable=False,
        index=True,
        doc="Tool name (e.g., 'Stripe', 'Notion')",
    )

    tagline: Mapped[str] = mapped_column(
        String(500),
        nullable=False,
        doc="Brief one-line description",
    )

    description: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        doc="Detailed description of tool features and benefits",
    )

    category: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        index=True,
        doc="Tool category (e.g., 'Payments', 'No-Code', 'Analytics')",
    )

    pricing: Mapped[str] = mapped_column(
        String(200),
        nullable=False,
        doc="Pricing model (e.g., 'Free', '$29/mo', 'Usage-based')",
    )

    website_url: Mapped[str] = mapped_column(
        String(500),
        nullable=False,
        doc="Official website URL",
    )

    logo_url: Mapped[str | None] = mapped_column(
        String(500),
        nullable=True,
        doc="Logo image URL (optional)",
    )

    # Curation flags
    is_featured: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
        index=True,
        doc="Featured on homepage (admin curated)",
    )

    sort_order: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
        doc="Manual sort order (lower = higher priority)",
    )

    # Phase 15: APAC Language Support
    translations: Mapped[dict | None] = mapped_column(
        JSONB,
        nullable=True,
        default=dict,
        doc="Translations: {zh-CN: {name: ..., tagline: ..., description: ...}}",
    )

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
        index=True,
        doc="Creation timestamp",
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
        doc="Last update timestamp",
    )

    def __repr__(self) -> str:
        return f"<Tool id={self.id} name='{self.name}' category='{self.category}' is_featured={self.is_featured}>"
