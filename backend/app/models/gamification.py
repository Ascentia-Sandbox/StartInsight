"""Gamification models for Phase 9.6: Gamification & Engagement.

Provides:
- Achievement: Achievement definitions
- UserAchievement: User earned achievements
- UserPoints: User points and levels
- UserCredits: Credit balance for premium features
- CreditTransaction: Credit transaction history
"""

from datetime import date, datetime
from typing import TYPE_CHECKING, Any
from uuid import UUID, uuid4

from sqlalchemy import Boolean, Date, DateTime, ForeignKey, Integer, String, Text, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

if TYPE_CHECKING:
    from app.models.user import User


class Achievement(Base):
    """Achievement definition for gamification."""

    __tablename__ = "achievements"

    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)

    # Achievement info
    name: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    badge_icon: Mapped[str | None] = mapped_column(String(500), nullable=True)
    points: Mapped[int] = mapped_column(Integer, nullable=False)

    # Criteria for earning
    criteria: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False)
    category: Mapped[str | None] = mapped_column(String(50), nullable=True)

    # Status
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    # Timestamp
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    # Relationships
    user_achievements: Mapped[list["UserAchievement"]] = relationship("UserAchievement", back_populates="achievement", cascade="all, delete-orphan", lazy="selectin")

    # Category constants
    CATEGORY_EXPLORER = "explorer"
    CATEGORY_CURATOR = "curator"
    CATEGORY_ANALYST = "analyst"
    CATEGORY_BUILDER = "builder"
    CATEGORY_SOCIAL = "social"
    CATEGORY_COMMUNITY = "community"
    CATEGORY_ENGAGEMENT = "engagement"

    def __repr__(self) -> str:
        return f"<Achievement(name={self.name}, points={self.points})>"


class UserAchievement(Base):
    """User earned achievement."""

    __tablename__ = "user_achievements"

    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    user_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    achievement_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), ForeignKey("achievements.id", ondelete="CASCADE"), nullable=False)
    earned_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    # Relationships
    user: Mapped["User"] = relationship("User", foreign_keys=[user_id], lazy="selectin")
    achievement: Mapped["Achievement"] = relationship("Achievement", back_populates="user_achievements")

    def __repr__(self) -> str:
        return f"<UserAchievement(user={self.user_id}, achievement={self.achievement_id})>"


class UserPoints(Base):
    """User points and level tracking."""

    __tablename__ = "user_points"

    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    user_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), unique=True, nullable=False)

    # Points and level
    total_points: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    level: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    achievements_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    # Streak tracking
    current_streak: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    longest_streak: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    last_activity_date: Mapped[date | None] = mapped_column(Date, nullable=True)

    # Timestamp
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    # Relationships
    user: Mapped["User"] = relationship("User", foreign_keys=[user_id], lazy="selectin")

    @classmethod
    def calculate_level(cls, points: int) -> int:
        """Calculate level based on points."""
        # Level thresholds: 100, 300, 600, 1000, 1500, 2100, 2800, 3600, 4500, 5500...
        # Formula: level n requires n*(n+1)*50 points
        level = 1
        threshold = 100
        while points >= threshold:
            level += 1
            threshold = level * (level + 1) * 50
        return level

    def __repr__(self) -> str:
        return f"<UserPoints(user={self.user_id}, points={self.total_points}, level={self.level})>"


class UserCredits(Base):
    """User credit balance for premium features."""

    __tablename__ = "user_credits"

    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    user_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), unique=True, nullable=False)

    # Balance
    balance: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    lifetime_earned: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    lifetime_spent: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    # Timestamp
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    # Relationships
    user: Mapped["User"] = relationship("User", foreign_keys=[user_id], lazy="selectin")

    def __repr__(self) -> str:
        return f"<UserCredits(user={self.user_id}, balance={self.balance})>"


class CreditTransaction(Base):
    """Credit transaction history."""

    __tablename__ = "credit_transactions"

    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    user_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)

    # Transaction details
    amount: Mapped[int] = mapped_column(Integer, nullable=False)  # positive = earn, negative = spend
    transaction_type: Mapped[str] = mapped_column(String(50), nullable=False)
    description: Mapped[str | None] = mapped_column(String(255), nullable=True)

    # Reference to related entity
    reference_id: Mapped[UUID | None] = mapped_column(PGUUID(as_uuid=True), nullable=True)
    reference_type: Mapped[str | None] = mapped_column(String(50), nullable=True)

    # Timestamp
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    # Relationships
    user: Mapped["User"] = relationship("User", foreign_keys=[user_id], lazy="selectin")

    # Transaction type constants
    TYPE_EARN_DAILY_LOGIN = "earn_daily_login"
    TYPE_EARN_SAVE_IDEA = "earn_save_idea"
    TYPE_EARN_VOTE = "earn_vote"
    TYPE_EARN_COMMENT = "earn_comment"
    TYPE_EARN_REFERRAL = "earn_referral"
    TYPE_EARN_PURCHASE = "earn_purchase"
    TYPE_SPEND_CHAT = "spend_chat"
    TYPE_SPEND_RESEARCH = "spend_research"
    TYPE_SPEND_EXPORT = "spend_export"
    TYPE_SPEND_LANDING_PAGE = "spend_landing_page"

    def __repr__(self) -> str:
        return f"<CreditTransaction(user={self.user_id}, amount={self.amount}, type={self.transaction_type})>"
