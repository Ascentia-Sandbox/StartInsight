"""SuccessStory database model - Founder case studies with revenue timelines.

Phase 12.2: IdeaBrowser Feature Replication
"""

from datetime import datetime
from uuid import UUID, uuid4

from sqlalchemy import DateTime, String, Text, Boolean, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class SuccessStory(Base):
    """
    SuccessStory model - Stores founder journey case studies.

    Represents real or anonymized founder journeys with:
    - Founder and company details
    - Idea summary and journey narrative
    - Metrics (MRR, users, funding) as JSONB
    - Timeline milestones as JSONB array
    - Avatar and company logo URLs
    """

    __tablename__ = "success_stories"

    # Primary key
    id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        primary_key=True,
        default=uuid4,
        doc="Unique identifier for this success story",
    )

    # Founder and company details
    founder_name: Mapped[str] = mapped_column(
        String(200),
        nullable=False,
        doc="Founder name (can be anonymized, e.g., 'Sarah T.')",
    )

    company_name: Mapped[str] = mapped_column(
        String(200),
        nullable=False,
        index=True,
        doc="Company name",
    )

    tagline: Mapped[str] = mapped_column(
        String(500),
        nullable=False,
        doc="One-line company tagline",
    )

    # Idea and journey narrative
    idea_summary: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        doc="Brief summary of the startup idea (200-300 words)",
    )

    journey_narrative: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        doc="Founder journey narrative (500-1000 words, IdeaBrowser-style storytelling)",
    )

    # Metrics and timeline (JSONB for flexibility)
    metrics: Mapped[dict] = mapped_column(
        JSONB,
        nullable=False,
        default=dict,
        doc="Key metrics: {mrr: 5000, users: 1200, funding: 100000, growth_rate: 15}",
    )

    timeline: Mapped[list] = mapped_column(
        JSONB,
        nullable=False,
        default=list,
        doc="Timeline milestones: [{date: '2023-01', event: 'Launched MVP', metric: '$1K MRR'}]",
    )

    # Images
    avatar_url: Mapped[str | None] = mapped_column(
        String(500),
        nullable=True,
        doc="Founder avatar/profile image URL",
    )

    company_logo_url: Mapped[str | None] = mapped_column(
        String(500),
        nullable=True,
        doc="Company logo URL",
    )

    source_url: Mapped[str | None] = mapped_column(
        String(500),
        nullable=True,
        doc="Link to original source / verification URL",
    )

    # Curation flags
    is_featured: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
        index=True,
        doc="Featured on homepage",
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
        doc="Translations: {zh-CN: {company_name: ..., tagline: ..., journey_narrative: ...}}",
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
        return f"<SuccessStory id={self.id} founder='{self.founder_name}' company='{self.company_name}' is_featured={self.is_featured}>"
