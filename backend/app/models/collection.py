"""Collection model for Sprint 5.1 - Community Engagement Features.

Enables user-curated collections/lists of insights for organization and sharing.
"""

from datetime import datetime
from typing import TYPE_CHECKING
from uuid import UUID, uuid4

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text, func, Boolean
from sqlalchemy.dialects.postgresql import UUID as PGUUID, JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

if TYPE_CHECKING:
    from app.models.user import User
    from app.models.insight import Insight


class Collection(Base):
    """
    Collection model for user-curated insight lists.

    Supports:
    - Public/private visibility
    - Collaborative editing (multiple curators)
    - Ordering (sort_order on items)
    - Cover images and descriptions
    """

    __tablename__ = "collections"

    # Primary key
    id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        primary_key=True,
        default=uuid4,
        doc="Unique identifier for this collection",
    )

    # Basic info
    title: Mapped[str] = mapped_column(
        String(200),
        nullable=False,
        doc="Collection title",
    )

    slug: Mapped[str] = mapped_column(
        String(250),
        nullable=False,
        unique=True,
        index=True,
        doc="URL-friendly slug",
    )

    description: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
        doc="Collection description (Markdown supported)",
    )

    # Visual
    cover_image_url: Mapped[str | None] = mapped_column(
        String(500),
        nullable=True,
        doc="Cover image URL",
    )

    emoji_icon: Mapped[str | None] = mapped_column(
        String(10),
        nullable=True,
        doc="Emoji icon for collection",
    )

    # Ownership
    owner_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        doc="User who created this collection",
    )

    # Visibility
    is_public: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False,
        index=True,
        doc="Whether collection is publicly visible",
    )

    is_featured: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
        index=True,
        doc="Whether collection is featured on explore page",
    )

    # Stats (denormalized for performance)
    insight_count: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
        doc="Number of insights in collection",
    )

    follower_count: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
        doc="Number of users following this collection",
    )

    view_count: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
        doc="Total view count",
    )

    # Metadata
    tags: Mapped[list[str]] = mapped_column(
        JSONB,
        default=list,
        nullable=False,
        doc="Tags for discovery",
    )

    settings: Mapped[dict] = mapped_column(
        JSONB,
        default=dict,
        nullable=False,
        doc="Collection settings (allow_comments, allow_suggestions, etc.)",
    )

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
        index=True,
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    # ORM Relationships
    owner: Mapped["User"] = relationship(
        "User",
        lazy="selectin",
        doc="User who owns this collection",
    )

    items: Mapped[list["CollectionItem"]] = relationship(
        "CollectionItem",
        back_populates="collection",
        lazy="selectin",
        cascade="all, delete-orphan",
        order_by="CollectionItem.sort_order",
        doc="Insights in this collection",
    )

    followers: Mapped[list["CollectionFollower"]] = relationship(
        "CollectionFollower",
        back_populates="collection",
        lazy="selectin",
        cascade="all, delete-orphan",
        doc="Users following this collection",
    )

    def __repr__(self) -> str:
        return f"<Collection(id={self.id}, title='{self.title}', items={self.insight_count})>"


class CollectionItem(Base):
    """
    Association between collections and insights.

    Includes ordering and notes for each item.
    """

    __tablename__ = "collection_items"

    # Primary key
    id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        primary_key=True,
        default=uuid4,
    )

    # Relationships
    collection_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("collections.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    insight_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("insights.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Added by
    added_by_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        doc="User who added this item",
    )

    # Ordering
    sort_order: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
        index=True,
        doc="Sort order within collection",
    )

    # Optional curator note
    note: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
        doc="Curator's note about this insight",
    )

    # Timestamps
    added_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    # ORM Relationships
    collection: Mapped["Collection"] = relationship(
        "Collection",
        back_populates="items",
    )

    insight: Mapped["Insight"] = relationship(
        "Insight",
        lazy="selectin",
    )

    added_by: Mapped["User | None"] = relationship(
        "User",
        lazy="selectin",
    )

    def __repr__(self) -> str:
        return f"<CollectionItem(collection_id={self.collection_id}, insight_id={self.insight_id})>"


class CollectionFollower(Base):
    """
    Users following a collection.

    Receives notifications when new insights are added.
    """

    __tablename__ = "collection_followers"

    # Primary key
    id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        primary_key=True,
        default=uuid4,
    )

    # Relationships
    collection_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("collections.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    user_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Notification preferences
    notify_on_add: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False,
        doc="Notify when new insights are added",
    )

    # Timestamps
    followed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    # ORM Relationships
    collection: Mapped["Collection"] = relationship(
        "Collection",
        back_populates="followers",
    )

    user: Mapped["User"] = relationship(
        "User",
        lazy="selectin",
    )

    def __repr__(self) -> str:
        return f"<CollectionFollower(collection_id={self.collection_id}, user_id={self.user_id})>"


class UserReputation(Base):
    """
    User reputation/karma tracking.

    Karma is earned through:
    - Creating insights that get upvoted
    - Comments that get upvoted
    - Collections that gain followers
    - Verified expert status
    """

    __tablename__ = "user_reputation"

    # Primary key
    id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        primary_key=True,
        default=uuid4,
    )

    # User relationship
    user_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
        index=True,
    )

    # Karma scores
    total_karma: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
        index=True,
        doc="Total karma points",
    )

    insight_karma: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
        doc="Karma from insight contributions",
    )

    comment_karma: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
        doc="Karma from helpful comments",
    )

    collection_karma: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
        doc="Karma from popular collections",
    )

    # Expert verification
    is_verified_expert: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
        doc="Whether user is a verified expert",
    )

    expert_badge: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
        doc="Expert badge type (e.g., 'Industry Expert', 'Top Contributor')",
    )

    verified_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        doc="When expert status was verified",
    )

    # Stats
    insights_created: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
    )

    comments_created: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
    )

    collections_created: Mapped[int] = mapped_column(
        Integer,
        default=0,
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

    # ORM Relationships
    user: Mapped["User"] = relationship(
        "User",
        lazy="selectin",
    )

    def __repr__(self) -> str:
        return f"<UserReputation(user_id={self.user_id}, karma={self.total_karma})>"
