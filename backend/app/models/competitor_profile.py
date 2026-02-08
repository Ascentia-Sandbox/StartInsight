"""Competitor Profile Model - Track startup idea competitors"""

from datetime import UTC, datetime
from typing import TYPE_CHECKING
from uuid import UUID, uuid4

from sqlalchemy import TIMESTAMP, Text, String, Integer, Index, ForeignKey
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

if TYPE_CHECKING:
    from app.models.insight import Insight


class CompetitorProfile(Base):
    """
    Competitor Profile Model.

    Tracks competitor companies for each startup insight, including
    their positioning, features, pricing, and change history.

    Used in Phase 9.2: Competitive Intelligence Dashboard.
    """

    __tablename__ = "competitor_profiles"

    # Primary Key
    id: Mapped[UUID] = mapped_column(
        primary_key=True,
        default=uuid4,
        doc="Unique competitor profile ID",
    )

    # Foreign Keys
    insight_id: Mapped[UUID] = mapped_column(
        ForeignKey("insights.id", ondelete="CASCADE"),
        index=True,
        doc="Associated insight (idea) that this competitor is relevant to",
    )

    # Core Attributes
    name: Mapped[str] = mapped_column(
        String(200),
        index=True,
        doc="Competitor company name (e.g., 'Notion', 'Linear')",
    )

    url: Mapped[str | None] = mapped_column(
        String(500),
        nullable=True,
        doc="Competitor website URL",
    )

    description: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
        doc="Brief description of what the competitor does",
    )

    market_position: Mapped[str | None] = mapped_column(
        String(50),
        nullable=True,
        doc="Market position category (e.g., 'leader', 'challenger', 'niche', 'startup')",
    )

    # Metrics (JSONB for flexibility)
    metrics: Mapped[dict | None] = mapped_column(
        JSONB,
        nullable=True,
        default=dict,
        doc="""Competitor metrics (flexible schema)
        {
            "funding": "$50M Series B",
            "team_size": "50-100 employees",
            "pricing": {
                "free": "$0/mo",
                "pro": "$29/mo",
                "enterprise": "$299/mo"
            },
            "monthly_traffic": "500K visits/mo",
            "social_proof": {
                "twitter_followers": "10K",
                "linkedin_followers": "5K"
            },
            "alexa_rank": 15000,
            "founded_year": 2020
        }
        """,
    )

    # Features (JSONB for feature comparison matrix)
    features: Mapped[dict | None] = mapped_column(
        JSONB,
        nullable=True,
        default=dict,
        doc="""Competitor features (for comparison matrix)
        {
            "ai_powered": true,
            "real_time_updates": true,
            "api_access": false,
            "white_label": false,
            "custom_branding": true,
            "sso": true,
            "advanced_analytics": false
        }
        """,
    )

    # Messaging & Positioning
    value_proposition: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
        doc="Competitor's main value proposition (from homepage)",
    )

    target_audience: Mapped[str | None] = mapped_column(
        String(500),
        nullable=True,
        doc="Who the competitor targets (e.g., 'SaaS founders', 'enterprise teams')",
    )

    # Strengths & Weaknesses (from AI analysis)
    strengths: Mapped[list | None] = mapped_column(
        JSONB,
        nullable=True,
        default=list,
        doc="""Competitor strengths
        [
            "Strong brand recognition",
            "Extensive feature set",
            "Large user base"
        ]
        """,
    )

    weaknesses: Mapped[list | None] = mapped_column(
        JSONB,
        nullable=True,
        default=list,
        doc="""Competitor weaknesses
        [
            "High pricing",
            "Steep learning curve",
            "No mobile app"
        ]
        """,
    )

    # Market Positioning (for 2x2 matrix)
    positioning_x: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
        doc="X-axis position in 2x2 matrix (e.g., price: 1-10, low to high)",
    )

    positioning_y: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
        doc="Y-axis position in 2x2 matrix (e.g., features: 1-10, few to many)",
    )

    # Data Collection Metadata
    last_scraped_at: Mapped[datetime | None] = mapped_column(
        TIMESTAMP(timezone=True),
        nullable=True,
        doc="Last time competitor data was scraped from their website",
    )

    scrape_status: Mapped[str | None] = mapped_column(
        String(50),
        nullable=True,
        doc="Status of last scrape attempt (e.g., 'success', 'failed', 'pending')",
    )

    scrape_error: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
        doc="Error message from last scrape attempt (if failed)",
    )

    # AI Analysis Metadata
    analysis_generated_at: Mapped[datetime | None] = mapped_column(
        TIMESTAMP(timezone=True),
        nullable=True,
        doc="Last time AI analysis was run for this competitor",
    )

    analysis_model: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
        doc="LLM model used for analysis (e.g., 'claude-3-5-sonnet-20250122')",
    )

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True),
        default=lambda: datetime.now(UTC),
        index=True,
        doc="Timestamp when competitor profile was first created",
    )

    updated_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True),
        default=lambda: datetime.now(UTC),
        onupdate=lambda: datetime.now(UTC),
        doc="Timestamp when competitor profile was last updated",
    )

    # Relationships
    insight: Mapped["Insight"] = relationship(
        "Insight",
        back_populates="competitors",
        lazy="selectin",
    )

    snapshots: Mapped[list["CompetitorSnapshot"]] = relationship(
        "CompetitorSnapshot",
        back_populates="competitor",
        cascade="all, delete-orphan",
    )

    # Indexes
    __table_args__ = (
        Index("ix_competitor_profiles_insight_id_name", "insight_id", "name"),
        Index("ix_competitor_profiles_market_position", "market_position"),
        Index("ix_competitor_profiles_last_scraped_at", "last_scraped_at"),
    )

    def __repr__(self) -> str:
        return f"<CompetitorProfile(id={self.id}, name={self.name}, insight_id={self.insight_id})>"


class CompetitorSnapshot(Base):
    """
    Competitor Snapshot Model.

    Stores historical snapshots of competitor data to track changes over time
    (pricing changes, feature additions, messaging updates).

    Used in Phase 9.2: Competitive Intelligence Dashboard.
    """

    __tablename__ = "competitor_snapshots"

    # Primary Key
    id: Mapped[UUID] = mapped_column(
        primary_key=True,
        default=uuid4,
        doc="Unique snapshot ID",
    )

    # Foreign Keys
    competitor_id: Mapped[UUID] = mapped_column(
        ForeignKey("competitor_profiles.id", ondelete="CASCADE"),
        index=True,
        doc="Associated competitor profile",
    )

    # Snapshot Data (full copy of competitor state at this point in time)
    snapshot_data: Mapped[dict] = mapped_column(
        JSONB,
        doc="""Complete snapshot of competitor data at this point in time
        {
            "name": "Competitor Name",
            "url": "https://competitor.com",
            "description": "...",
            "metrics": {...},
            "features": {...},
            "value_proposition": "...",
            "pricing": {...}
        }
        """,
    )

    # Change Detection
    changes_detected: Mapped[list | None] = mapped_column(
        JSONB,
        nullable=True,
        default=list,
        doc="""List of detected changes since last snapshot
        [
            {
                "field": "pricing.pro",
                "old_value": "$29/mo",
                "new_value": "$39/mo",
                "change_type": "price_increase"
            },
            {
                "field": "features.ai_powered",
                "old_value": false,
                "new_value": true,
                "change_type": "feature_added"
            }
        ]
        """,
    )

    # Metadata
    scraped_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True),
        default=lambda: datetime.now(UTC),
        index=True,
        doc="When this snapshot was created",
    )

    scrape_method: Mapped[str | None] = mapped_column(
        String(50),
        nullable=True,
        doc="How data was collected (e.g., 'firecrawl', 'manual', 'api')",
    )

    # Relationships
    competitor: Mapped["CompetitorProfile"] = relationship(
        "CompetitorProfile",
        back_populates="snapshots",
    )

    # Indexes
    __table_args__ = (
        Index("ix_competitor_snapshots_competitor_id_scraped_at", "competitor_id", "scraped_at"),
    )

    def __repr__(self) -> str:
        return f"<CompetitorSnapshot(id={self.id}, competitor_id={self.competitor_id}, scraped_at={self.scraped_at})>"
