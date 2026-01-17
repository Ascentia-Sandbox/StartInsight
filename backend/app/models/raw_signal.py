"""Raw signal database model for storing scraped data."""

import uuid
from datetime import datetime
from typing import Any

from sqlalchemy import Boolean, String, Text, func
from sqlalchemy.dialects.postgresql import JSON, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class RawSignal(Base):
    """
    Raw signal model for storing unprocessed scraped data.

    Stores market signals from various sources (Reddit, Product Hunt, Google Trends)
    before they are processed by the AI analysis pipeline.

    Attributes:
        id: Unique identifier (UUID)
        source: Data source identifier (e.g., "reddit", "product_hunt", "google_trends")
        url: Source URL where the data was scraped from
        content: Scraped content in markdown format
        extra_metadata: Additional structured data (upvotes, comments, timestamps, etc.)
        created_at: Timestamp when the signal was created
        processed: Flag indicating if this signal has been analyzed (default: False)
    """

    __tablename__ = "raw_signals"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        index=True
    )

    source: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        index=True,
        comment="Data source: reddit, product_hunt, google_trends"
    )

    url: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        comment="Source URL where data was scraped"
    )

    content: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        comment="Scraped content in markdown format"
    )

    extra_metadata: Mapped[dict[str, Any]] = mapped_column(
        JSON,
        nullable=False,
        default=dict,
        comment="Additional structured data (upvotes, comments, etc.)"
    )

    created_at: Mapped[datetime] = mapped_column(
        nullable=False,
        server_default=func.now(),
        index=True,
        comment="Timestamp when signal was created"
    )

    processed: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
        index=True,
        comment="Flag indicating if signal has been analyzed"
    )

    def __repr__(self) -> str:
        """String representation of RawSignal."""
        return f"<RawSignal(id={self.id}, source={self.source}, processed={self.processed})>"
