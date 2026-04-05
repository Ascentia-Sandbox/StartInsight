"""Social post model — tracks content generated for and posted to social platforms."""

from datetime import datetime
from uuid import UUID, uuid4

from sqlalchemy import DateTime, ForeignKey, String, Text, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class SocialPost(Base):
    """Tracks social media posts: pending → posted / failed."""

    __tablename__ = "social_posts"

    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)

    insight_id: Mapped[UUID | None] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("insights.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    platform: Mapped[str] = mapped_column(
        String(20),
        nullable=False,  # "twitter" | "linkedin"
    )

    content: Mapped[str] = mapped_column(Text, nullable=False)

    hashtags: Mapped[list | None] = mapped_column(JSONB, nullable=True)

    link_url: Mapped[str | None] = mapped_column(
        String(512),
        nullable=True,  # Insight/report URL with UTM
    )

    external_post_id: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,  # Tweet ID or LinkedIn URN
    )

    status: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="pending",  # pending | posted | failed
    )

    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)

    posted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    engagement_metrics: Mapped[dict | None] = mapped_column(JSONB, nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
