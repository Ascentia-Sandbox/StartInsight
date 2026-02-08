"""Gamification API routes - Phase 9.6: Gamification & Engagement.

Provides endpoints for:
- Achievements
- User points and levels
- Credits
- Leaderboards
"""

import logging
from datetime import UTC, date, datetime
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, require_admin, get_db
from app.models.gamification import (
    Achievement,
    UserAchievement,
    UserPoints,
    UserCredits,
    CreditTransaction,
)
from app.models.user import User

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/gamification", tags=["Gamification"])


# ============================================
# Schemas
# ============================================

class AchievementResponse(BaseModel):
    id: UUID
    name: str
    description: str | None
    badge_icon: str | None
    points: int
    criteria: dict
    category: str | None
    is_active: bool

    class Config:
        from_attributes = True


class UserAchievementResponse(BaseModel):
    id: UUID
    achievement_id: UUID
    earned_at: datetime
    achievement: AchievementResponse

    class Config:
        from_attributes = True


class UserPointsResponse(BaseModel):
    id: UUID
    user_id: UUID
    total_points: int
    level: int
    achievements_count: int
    current_streak: int
    longest_streak: int
    last_activity_date: date | None

    class Config:
        from_attributes = True


class UserCreditsResponse(BaseModel):
    id: UUID
    user_id: UUID
    balance: int
    lifetime_earned: int
    lifetime_spent: int

    class Config:
        from_attributes = True


class CreditTransactionResponse(BaseModel):
    id: UUID
    amount: int
    transaction_type: str
    description: str | None
    created_at: datetime

    class Config:
        from_attributes = True


class LeaderboardEntry(BaseModel):
    user_id: UUID
    display_name: str | None
    total_points: int
    level: int
    rank: int


# ============================================
# Achievements Endpoints
# ============================================

@router.get("/achievements", response_model=list[AchievementResponse])
async def list_achievements(
    db: Annotated[AsyncSession, Depends(get_db)],
    category: str | None = None,
):
    """List all available achievements."""
    query = select(Achievement).where(Achievement.is_active == True).order_by(Achievement.points)

    if category:
        query = query.where(Achievement.category == category)

    result = await db.execute(query)
    return [AchievementResponse.model_validate(a) for a in result.scalars().all()]


@router.get("/achievements/mine", response_model=list[UserAchievementResponse])
async def get_my_achievements(
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
):
    """Get current user's earned achievements."""
    result = await db.execute(
        select(UserAchievement)
        .where(UserAchievement.user_id == current_user.id)
        .order_by(UserAchievement.earned_at.desc())
    )
    return [UserAchievementResponse.model_validate(ua) for ua in result.scalars().all()]


# ============================================
# Points & Levels Endpoints
# ============================================

@router.get("/points", response_model=UserPointsResponse)
async def get_my_points(
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
):
    """Get current user's points and level."""
    result = await db.execute(
        select(UserPoints).where(UserPoints.user_id == current_user.id)
    )
    points = result.scalar_one_or_none()

    if not points:
        # Create default points record
        points = UserPoints(user_id=current_user.id)
        db.add(points)
        await db.commit()
        await db.refresh(points)

    return UserPointsResponse.model_validate(points)


@router.post("/points/check-in")
async def daily_check_in(
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
):
    """Record daily check-in, update streak, earn credits."""
    today = date.today()

    # Get or create points record
    result = await db.execute(
        select(UserPoints).where(UserPoints.user_id == current_user.id)
    )
    points = result.scalar_one_or_none()

    if not points:
        points = UserPoints(user_id=current_user.id)
        db.add(points)

    # Check if already checked in today
    if points.last_activity_date == today:
        return {"status": "already_checked_in", "streak": points.current_streak}

    # Calculate streak
    yesterday = date.today().replace(day=today.day - 1) if today.day > 1 else None
    if points.last_activity_date == yesterday:
        points.current_streak += 1
    else:
        points.current_streak = 1

    if points.current_streak > points.longest_streak:
        points.longest_streak = points.current_streak

    points.last_activity_date = today
    points.updated_at = datetime.now(UTC)

    # Award daily credits
    result = await db.execute(
        select(UserCredits).where(UserCredits.user_id == current_user.id)
    )
    credits = result.scalar_one_or_none()

    if not credits:
        credits = UserCredits(user_id=current_user.id)
        db.add(credits)

    daily_credit_amount = 5
    credits.balance += daily_credit_amount
    credits.lifetime_earned += daily_credit_amount
    credits.updated_at = datetime.now(UTC)

    # Record transaction
    transaction = CreditTransaction(
        user_id=current_user.id,
        amount=daily_credit_amount,
        transaction_type=CreditTransaction.TYPE_EARN_DAILY_LOGIN,
        description="Daily check-in bonus",
    )
    db.add(transaction)

    await db.commit()

    logger.info(f"User {current_user.id} checked in, streak: {points.current_streak}")
    return {
        "status": "checked_in",
        "streak": points.current_streak,
        "credits_earned": daily_credit_amount,
    }


# ============================================
# Credits Endpoints
# ============================================

@router.get("/credits", response_model=UserCreditsResponse)
async def get_my_credits(
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
):
    """Get current user's credit balance."""
    result = await db.execute(
        select(UserCredits).where(UserCredits.user_id == current_user.id)
    )
    credits = result.scalar_one_or_none()

    if not credits:
        credits = UserCredits(user_id=current_user.id)
        db.add(credits)
        await db.commit()
        await db.refresh(credits)

    return UserCreditsResponse.model_validate(credits)


@router.get("/credits/transactions", response_model=list[CreditTransactionResponse])
async def get_credit_transactions(
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
    limit: int = Query(50, le=100),
    offset: int = 0,
):
    """Get credit transaction history."""
    result = await db.execute(
        select(CreditTransaction)
        .where(CreditTransaction.user_id == current_user.id)
        .order_by(CreditTransaction.created_at.desc())
        .offset(offset)
        .limit(limit)
    )
    return [CreditTransactionResponse.model_validate(t) for t in result.scalars().all()]


# ============================================
# Leaderboard Endpoints
# ============================================

@router.get("/leaderboard/points", response_model=list[LeaderboardEntry])
async def get_points_leaderboard(
    db: Annotated[AsyncSession, Depends(get_db)],
    limit: int = Query(10, le=100),
):
    """Get top users by points."""
    result = await db.execute(
        select(UserPoints, User)
        .join(User, UserPoints.user_id == User.id)
        .order_by(UserPoints.total_points.desc())
        .limit(limit)
    )

    entries = []
    for i, (points, user) in enumerate(result.all(), 1):
        entries.append(LeaderboardEntry(
            user_id=points.user_id,
            display_name=user.full_name or user.email.split("@")[0],
            total_points=points.total_points,
            level=points.level,
            rank=i,
        ))

    return entries


@router.get("/leaderboard/streak", response_model=list[LeaderboardEntry])
async def get_streak_leaderboard(
    db: Annotated[AsyncSession, Depends(get_db)],
    limit: int = Query(10, le=100),
):
    """Get top users by current streak."""
    result = await db.execute(
        select(UserPoints, User)
        .join(User, UserPoints.user_id == User.id)
        .order_by(UserPoints.current_streak.desc())
        .limit(limit)
    )

    entries = []
    for i, (points, user) in enumerate(result.all(), 1):
        entries.append(LeaderboardEntry(
            user_id=points.user_id,
            display_name=user.full_name or user.email.split("@")[0],
            total_points=points.current_streak,  # Using points field for streak
            level=points.level,
            rank=i,
        ))

    return entries


# ============================================
# Admin Endpoints
# ============================================

@router.post("/admin/grant-credits/{user_id}")
async def admin_grant_credits(
    user_id: UUID,
    amount: int,
    db: Annotated[AsyncSession, Depends(get_db)],
    admin: Annotated[User, Depends(require_admin)],
    description: str = "Admin grant",
):
    """Admin: Grant credits to a user."""
    if amount <= 0:
        raise HTTPException(status_code=400, detail="Amount must be positive")

    # Get or create credits
    result = await db.execute(
        select(UserCredits).where(UserCredits.user_id == user_id)
    )
    credits = result.scalar_one_or_none()

    if not credits:
        credits = UserCredits(user_id=user_id)
        db.add(credits)

    credits.balance += amount
    credits.lifetime_earned += amount
    credits.updated_at = datetime.now(UTC)

    # Record transaction
    transaction = CreditTransaction(
        user_id=user_id,
        amount=amount,
        transaction_type="admin_grant",
        description=description,
    )
    db.add(transaction)

    await db.commit()

    logger.info(f"Admin {admin.id} granted {amount} credits to user {user_id}")
    return {"status": "granted", "amount": amount, "new_balance": credits.balance}


@router.post("/admin/grant-achievement/{user_id}/{achievement_id}")
async def admin_grant_achievement(
    user_id: UUID,
    achievement_id: UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
    admin: Annotated[User, Depends(require_admin)],
):
    """Admin: Grant an achievement to a user."""
    # Verify achievement exists
    result = await db.execute(select(Achievement).where(Achievement.id == achievement_id))
    achievement = result.scalar_one_or_none()
    if not achievement:
        raise HTTPException(status_code=404, detail="Achievement not found")

    # Check if already earned
    result = await db.execute(
        select(UserAchievement).where(
            UserAchievement.user_id == user_id,
            UserAchievement.achievement_id == achievement_id,
        )
    )
    if result.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="User already has this achievement")

    # Grant achievement
    user_achievement = UserAchievement(
        user_id=user_id,
        achievement_id=achievement_id,
    )
    db.add(user_achievement)

    # Update user points
    result = await db.execute(
        select(UserPoints).where(UserPoints.user_id == user_id)
    )
    points = result.scalar_one_or_none()

    if not points:
        points = UserPoints(user_id=user_id)
        db.add(points)

    points.total_points += achievement.points
    points.achievements_count += 1
    points.level = UserPoints.calculate_level(points.total_points)
    points.updated_at = datetime.now(UTC)

    await db.commit()

    logger.info(f"Admin {admin.id} granted achievement {achievement_id} to user {user_id}")
    return {"status": "granted", "achievement": achievement.name, "points_earned": achievement.points}
