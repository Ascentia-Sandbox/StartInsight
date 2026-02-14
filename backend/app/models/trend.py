"""Trend database model - 180+ trending keywords with volume/growth metrics.

Phase 12.2: IdeaBrowser Feature Replication
"""

from datetime import datetime
from uuid import UUID, uuid4

from sqlalchemy import Boolean, DateTime, Float, Integer, String, Text, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class Trend(Base):
    """
    Trend model - Stores trending keywords with search volume and growth data.

    Represents standalone trends (separate from insights) with:
    - Keyword and category
    - Search volume and growth percentage
    - Business implications description
    - Trend data timeseries as JSONB
    - Source attribution (Google Trends, Twitter, etc.)
    """

    __tablename__ = "trends"

    # Primary key
    id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        primary_key=True,
        default=uuid4,
        doc="Unique identifier for this trend",
    )

    # Trend identification
    keyword: Mapped[str] = mapped_column(
        String(200),
        nullable=False,
        index=True,
        unique=True,
        doc="Trending keyword or phrase (e.g., 'AI automation tools')",
    )

    category: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        index=True,
        doc="Trend category (e.g., 'AI', 'SaaS', 'Health Tech')",
    )

    # Metrics
    search_volume: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        index=True,
        doc="Monthly search volume (e.g., 27000)",
    )

    growth_percentage: Mapped[float] = mapped_column(
        Float,
        nullable=False,
        index=True,
        doc="Growth percentage (e.g., 86.5 for +86.5%)",
    )

    # Analysis
    business_implications: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        doc="Business implications description (100-200 words)",
    )

    # Timeseries data
    trend_data: Mapped[dict] = mapped_column(
        JSONB,
        nullable=True,
        default=dict,
        doc="Trend timeseries data: {dates: ['2024-01', ...], values: [45, 67, ...]}",
    )

    # Attribution
    source: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        default="Google Trends",
        doc="Data source (e.g., 'Google Trends', 'Twitter Trends')",
    )

    # Curation flags
    is_featured: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
        index=True,
        doc="Featured trend (admin curated)",
    )

    is_published: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
        index=True,
        doc="Published and visible to users",
    )

    # Phase 15: APAC Language Support
    translations: Mapped[dict | None] = mapped_column(
        JSONB,
        nullable=True,
        default=dict,
        doc="Translations: {zh-CN: {keyword: ..., business_implications: ...}}",
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
        return f"<Trend id={self.id} keyword='{self.keyword}' volume={self.search_volume} growth={self.growth_percentage}%>"
