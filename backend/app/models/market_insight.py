"""MarketInsight database model - Blog articles with Markdown content.

Phase 12.2: IdeaBrowser Feature Replication
"""

from datetime import datetime
from uuid import UUID, uuid4

from sqlalchemy import Boolean, DateTime, Integer, String, Text, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class MarketInsight(Base):
    """
    MarketInsight model - Stores blog articles about startup trends and analysis.

    Represents blog content with:
    - Title, slug, and summary
    - Full Markdown content
    - Category and author details
    - Cover image and reading time
    - Published flag for draft management
    """

    __tablename__ = "market_insights"

    # Primary key
    id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        primary_key=True,
        default=uuid4,
        doc="Unique identifier for this article",
    )

    # Article metadata
    title: Mapped[str] = mapped_column(
        String(500),
        nullable=False,
        index=True,
        doc="Article title",
    )

    slug: Mapped[str] = mapped_column(
        String(500),
        nullable=False,
        unique=True,
        index=True,
        doc="URL-friendly slug (auto-generated from title)",
    )

    summary: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        doc="Brief article summary (150-200 words)",
    )

    # Content
    content: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        doc="Full article content in Markdown format",
    )

    # Categorization
    category: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        index=True,
        doc="Article category (e.g., 'Trends', 'Analysis', 'Guides')",
    )

    # Author information
    author_name: Mapped[str] = mapped_column(
        String(200),
        nullable=False,
        doc="Author name",
    )

    author_avatar_url: Mapped[str | None] = mapped_column(
        String(500),
        nullable=True,
        doc="Author avatar/profile image URL",
    )

    # Media
    cover_image_url: Mapped[str | None] = mapped_column(
        String(500),
        nullable=True,
        doc="Article cover image URL (optional)",
    )

    # Metrics
    reading_time_minutes: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=5,
        doc="Estimated reading time in minutes",
    )

    view_count: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
        doc="Article view count (incremented on page view)",
    )

    # Publishing
    is_featured: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
        index=True,
        doc="Featured article (shown on homepage)",
    )

    is_published: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
        index=True,
        doc="Published and visible to users (drafts are false)",
    )

    published_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        index=True,
        doc="Publication timestamp (null for drafts)",
    )

    # Phase 15: APAC Language Support
    translations: Mapped[dict | None] = mapped_column(
        JSONB,
        nullable=True,
        default=dict,
        doc="Translations: {zh-CN: {title: ..., summary: ..., content: ...}}",
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
        return f"<MarketInsight id={self.id} title='{self.title}' category='{self.category}' is_published={self.is_published}>"
