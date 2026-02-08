"""Analytics API routes - Phase 8.3: User & Revenue Intelligence.

Provides admin endpoints for:
- User analytics and cohort analysis
- Revenue metrics and forecasting
- User management
"""

import logging
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from typing import Annotated, Any
from uuid import UUID, uuid4

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from pydantic import BaseModel, EmailStr, Field
from sqlalchemy import func, select, update, and_, or_
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import require_admin, get_db
from app.models.user import User
from app.models.admin_user import AdminUser
from app.models.agent_control import AuditLog
from app.models.user_analytics import UserActivityEvent, UserSession
from app.models.subscription import Subscription
from app.models.saved_insight import SavedInsight

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/admin/analytics", tags=["Analytics"])


# ============================================
# Schemas
# ============================================

class UserOverview(BaseModel):
    total_users: int
    active_users_7d: int
    active_users_30d: int
    new_users_7d: int
    churn_rate_30d: float

class TierStats(BaseModel):
    tier: str
    count: int
    active_rate: float
    mrr: float

class EngagementStats(BaseModel):
    avg_session_duration: float
    avg_insights_viewed: float
    avg_insights_saved: float
    feature_usage: dict[str, int]

class CohortData(BaseModel):
    signup_week: str
    total_users: int
    retention_week_1: float
    retention_week_4: float
    conversion_to_paid: float

class UserAnalyticsResponse(BaseModel):
    overview: UserOverview
    by_tier: list[TierStats]
    engagement: EngagementStats

class RevenueMetrics(BaseModel):
    mrr: float
    arr: float
    active_subscriptions: int
    mrr_growth_mom: float
    churn_rate: float

class UserListItem(BaseModel):
    id: UUID
    email: str
    display_name: str | None
    subscription_tier: str
    created_at: datetime
    last_active: datetime | None
    admin_role: str | None = None
    is_suspended: bool = False
    language: str = "en"
    last_login_at: datetime | None = None

    class Config:
        from_attributes = True

class UserDetail(BaseModel):
    id: UUID
    email: str
    display_name: str | None
    avatar_url: str | None
    subscription_tier: str
    created_at: datetime
    insights_saved: int
    research_count: int
    total_sessions: int
    admin_role: str | None = None
    is_suspended: bool = False
    language: str = "en"
    last_login_at: datetime | None = None

class UserCreateRequest(BaseModel):
    email: EmailStr
    display_name: str | None = None
    subscription_tier: str = "free"
    language: str = "en"

class UserUpdateRequest(BaseModel):
    subscription_tier: str | None = None
    is_suspended: bool | None = None
    display_name: str | None = None
    language: str | None = None

class UserDeleteRequest(BaseModel):
    reason: str = ""

class BulkUserActionRequest(BaseModel):
    user_ids: list[UUID]
    action: str  # delete, suspend, unsuspend, change_tier
    tier: str | None = None
    reason: str | None = None


# ============================================
# User Analytics Endpoints
# ============================================

@router.get("/users", response_model=UserAnalyticsResponse)
async def get_user_analytics(
    db: Annotated[AsyncSession, Depends(get_db)],
    admin: Annotated[User, Depends(require_admin)],
):
    """Get comprehensive user analytics."""
    now = datetime.now(UTC)
    week_ago = now - timedelta(days=7)
    month_ago = now - timedelta(days=30)

    # Total users
    total_users = await db.execute(select(func.count(User.id)))

    # Active users (have sessions in period)
    active_7d = await db.execute(
        select(func.count(func.distinct(UserSession.user_id)))
        .where(UserSession.started_at >= week_ago)
    )
    active_30d = await db.execute(
        select(func.count(func.distinct(UserSession.user_id)))
        .where(UserSession.started_at >= month_ago)
    )

    # New users this week
    new_7d = await db.execute(
        select(func.count(User.id)).where(User.created_at >= week_ago)
    )

    # By tier stats
    tier_counts = await db.execute(
        select(User.subscription_tier, func.count(User.id))
        .group_by(User.subscription_tier)
    )
    tier_stats = []
    for tier, count in tier_counts.fetchall():
        # Calculate active rate for tier
        active_in_tier = await db.execute(
            select(func.count(func.distinct(UserSession.user_id)))
            .join(User, User.id == UserSession.user_id)
            .where(User.subscription_tier == tier, UserSession.started_at >= month_ago)
        )
        active_count = active_in_tier.scalar() or 0
        active_rate = active_count / count if count > 0 else 0

        # MRR for tier
        mrr = 0.0
        if tier == "starter":
            mrr = count * 19.0
        elif tier == "pro":
            mrr = count * 49.0
        elif tier == "enterprise":
            mrr = count * 199.0

        tier_stats.append(TierStats(tier=tier, count=count, active_rate=round(active_rate, 2), mrr=mrr))

    # Engagement stats
    avg_duration = await db.execute(select(func.avg(UserSession.duration_seconds)))
    avg_saved = await db.execute(
        select(func.count(SavedInsight.id) / func.nullif(func.count(func.distinct(SavedInsight.user_id)), 0))
    )

    # Feature usage
    feature_usage = await db.execute(
        select(UserActivityEvent.event_type, func.count(UserActivityEvent.id))
        .where(UserActivityEvent.created_at >= month_ago)
        .group_by(UserActivityEvent.event_type)
    )
    features = {row[0]: row[1] for row in feature_usage.fetchall()}

    return UserAnalyticsResponse(
        overview=UserOverview(
            total_users=total_users.scalar() or 0,
            active_users_7d=active_7d.scalar() or 0,
            active_users_30d=active_30d.scalar() or 0,
            new_users_7d=new_7d.scalar() or 0,
            churn_rate_30d=0.0  # TODO: Calculate actual churn
        ),
        by_tier=tier_stats,
        engagement=EngagementStats(
            avg_session_duration=float(avg_duration.scalar() or 0),
            avg_insights_viewed=0.0,  # TODO: Calculate from events
            avg_insights_saved=float(avg_saved.scalar() or 0),
            feature_usage=features
        )
    )


@router.get("/users/cohorts", response_model=list[CohortData])
async def get_cohort_analysis(
    db: Annotated[AsyncSession, Depends(get_db)],
    admin: Annotated[User, Depends(require_admin)],
    weeks: int = 12,
):
    """Get cohort retention analysis."""
    cohorts = []
    now = datetime.now(UTC)

    for i in range(weeks):
        week_start = now - timedelta(weeks=i+1)
        week_end = now - timedelta(weeks=i)

        # Users who signed up in this week
        users_in_cohort = await db.execute(
            select(func.count(User.id)).where(
                User.created_at >= week_start,
                User.created_at < week_end
            )
        )
        total = users_in_cohort.scalar() or 0
        if total == 0:
            continue

        # Week 1 retention
        week1_end = week_end + timedelta(weeks=1)
        retained_week1 = await db.execute(
            select(func.count(func.distinct(UserSession.user_id)))
            .join(User, User.id == UserSession.user_id)
            .where(
                User.created_at >= week_start,
                User.created_at < week_end,
                UserSession.started_at >= week_end,
                UserSession.started_at < week1_end
            )
        )

        # Week 4 retention
        week4_end = week_end + timedelta(weeks=4)
        retained_week4 = await db.execute(
            select(func.count(func.distinct(UserSession.user_id)))
            .join(User, User.id == UserSession.user_id)
            .where(
                User.created_at >= week_start,
                User.created_at < week_end,
                UserSession.started_at >= week_end + timedelta(weeks=3),
                UserSession.started_at < week4_end
            )
        )

        # Conversion to paid
        paid_count = await db.execute(
            select(func.count(User.id)).where(
                User.created_at >= week_start,
                User.created_at < week_end,
                User.subscription_tier != "free"
            )
        )

        cohorts.append(CohortData(
            signup_week=week_start.strftime("%Y-%W"),
            total_users=total,
            retention_week_1=round((retained_week1.scalar() or 0) / total, 2),
            retention_week_4=round((retained_week4.scalar() or 0) / total, 2),
            conversion_to_paid=round((paid_count.scalar() or 0) / total, 2)
        ))

    return cohorts


@router.get("/revenue", response_model=RevenueMetrics)
async def get_revenue_metrics(
    db: Annotated[AsyncSession, Depends(get_db)],
    admin: Annotated[User, Depends(require_admin)],
):
    """Get revenue metrics."""
    # Count by tier
    tier_counts = await db.execute(
        select(User.subscription_tier, func.count(User.id))
        .where(User.subscription_tier != "free")
        .group_by(User.subscription_tier)
    )

    mrr = 0.0
    active_subs = 0
    for tier, count in tier_counts.fetchall():
        active_subs += count
        if tier == "starter":
            mrr += count * 19.0
        elif tier == "pro":
            mrr += count * 49.0
        elif tier == "enterprise":
            mrr += count * 199.0

    return RevenueMetrics(
        mrr=mrr,
        arr=mrr * 12,
        active_subscriptions=active_subs,
        mrr_growth_mom=0.0,  # TODO: Calculate from historical data
        churn_rate=0.0  # TODO: Calculate actual churn
    )


# ============================================
# User Management Endpoints
# ============================================

@router.get("/users/list", response_model=list[UserListItem])
async def list_users(
    db: Annotated[AsyncSession, Depends(get_db)],
    admin: Annotated[User, Depends(require_admin)],
    search: str | None = None,
    tier: str | None = None,
    limit: int = 50,
    offset: int = 0,
):
    """List users with search and filter, including admin role and status."""
    query = (
        select(User, AdminUser.role)
        .outerjoin(AdminUser, AdminUser.user_id == User.id)
        .order_by(User.created_at.desc())
    )

    if search:
        query = query.where(
            or_(
                User.email.ilike(f"%{search}%"),
                User.display_name.ilike(f"%{search}%")
            )
        )

    if tier:
        query = query.where(User.subscription_tier == tier)

    query = query.offset(offset).limit(limit)
    result = await db.execute(query)
    rows = result.all()

    return [
        UserListItem(
            id=u.id,
            email=u.email,
            display_name=u.display_name,
            subscription_tier=u.subscription_tier,
            created_at=u.created_at,
            last_active=None,
            admin_role=admin_role,
            is_suspended=u.deleted_at is not None,
            language=u.language,
            last_login_at=u.last_login_at,
        )
        for u, admin_role in rows
    ]


@router.get("/users/{user_id}", response_model=UserDetail)
async def get_user_detail(
    user_id: UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
    admin: Annotated[User, Depends(require_admin)],
):
    """Get detailed user information."""
    result = await db.execute(
        select(User, AdminUser.role)
        .outerjoin(AdminUser, AdminUser.user_id == User.id)
        .where(User.id == user_id)
    )
    row = result.one_or_none()

    if not row:
        raise HTTPException(status_code=404, detail="User not found")

    user, admin_role = row

    # Get saved insights count
    saved_count = await db.execute(
        select(func.count(SavedInsight.id)).where(SavedInsight.user_id == user_id)
    )

    # Get research count
    from app.models.custom_analysis import CustomAnalysis
    research_count = await db.execute(
        select(func.count(CustomAnalysis.id)).where(CustomAnalysis.user_id == user_id)
    )

    # Get session count
    session_count = await db.execute(
        select(func.count(UserSession.id)).where(UserSession.user_id == user_id)
    )

    return UserDetail(
        id=user.id,
        email=user.email,
        display_name=user.display_name,
        avatar_url=user.avatar_url,
        subscription_tier=user.subscription_tier,
        created_at=user.created_at,
        insights_saved=saved_count.scalar() or 0,
        research_count=research_count.scalar() or 0,
        total_sessions=session_count.scalar() or 0,
        admin_role=admin_role,
        is_suspended=user.deleted_at is not None,
        language=user.language,
        last_login_at=user.last_login_at,
    )


@router.patch("/users/{user_id}")
async def update_user(
    user_id: UUID,
    updates: UserUpdateRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
    admin: Annotated[User, Depends(require_admin)],
    request: Request,
):
    """Update user (tier, display_name, language, suspension status)."""
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    changes: dict[str, Any] = {}

    if updates.subscription_tier is not None:
        changes["subscription_tier"] = {"old": user.subscription_tier, "new": updates.subscription_tier}
        user.subscription_tier = updates.subscription_tier

    if updates.display_name is not None:
        changes["display_name"] = {"old": user.display_name, "new": updates.display_name}
        user.display_name = updates.display_name

    if updates.language is not None:
        changes["language"] = {"old": user.language, "new": updates.language}
        user.language = updates.language

    if updates.is_suspended is not None:
        if updates.is_suspended and user.deleted_at is None:
            user.deleted_at = datetime.now(UTC)
            user.deleted_by = admin.id
            user.deletion_reason = "Suspended by admin"
            changes["suspended"] = True
        elif not updates.is_suspended and user.deleted_at is not None:
            user.deleted_at = None
            user.deleted_by = None
            user.deletion_reason = None
            changes["unsuspended"] = True

    # Audit log
    audit = AuditLog(
        user_id=admin.id,
        action=AuditLog.ACTION_UPDATE,
        resource_type="user",
        resource_id=user_id,
        details=changes,
        ip_address=request.client.host if request.client else None,
    )
    db.add(audit)

    await db.commit()
    await db.refresh(user)

    logger.info(f"User {user_id} updated by admin {admin.id}")
    return {"status": "updated", "user_id": str(user_id)}


@router.post("/users")
async def create_user(
    payload: UserCreateRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
    admin: Annotated[User, Depends(require_admin)],
    request: Request,
):
    """Create a new user (admin action)."""
    # Check email uniqueness
    existing = await db.execute(select(User).where(User.email == payload.email))
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=409, detail="Email already registered")

    user = User(
        supabase_user_id=f"admin-created-{uuid4()}",
        email=payload.email,
        display_name=payload.display_name,
        subscription_tier=payload.subscription_tier,
        language=payload.language,
    )
    db.add(user)

    # Audit log
    audit = AuditLog(
        user_id=admin.id,
        action=AuditLog.ACTION_CREATE,
        resource_type="user",
        details={"email": payload.email, "tier": payload.subscription_tier},
        ip_address=request.client.host if request.client else None,
    )
    db.add(audit)

    await db.commit()
    await db.refresh(user)

    logger.info(f"User {user.id} created by admin {admin.id}")
    return {"status": "created", "user_id": str(user.id)}


@router.delete("/users/{user_id}")
async def delete_user(
    user_id: UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
    admin: Annotated[User, Depends(require_admin)],
    request: Request,
    reason: str = "",
):
    """Soft delete a user."""
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    user.deleted_at = datetime.now(UTC)
    user.deleted_by = admin.id
    user.deletion_reason = reason or "Deleted by admin"

    # Audit log
    audit = AuditLog(
        user_id=admin.id,
        action=AuditLog.ACTION_DELETE,
        resource_type="user",
        resource_id=user_id,
        details={"email": user.email, "reason": reason},
        ip_address=request.client.host if request.client else None,
    )
    db.add(audit)

    await db.commit()

    logger.info(f"User {user_id} soft-deleted by admin {admin.id}")
    return {"status": "deleted", "user_id": str(user_id)}


@router.post("/users/bulk")
async def bulk_user_action(
    payload: BulkUserActionRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
    admin: Annotated[User, Depends(require_admin)],
    request: Request,
):
    """Bulk action on users (delete, suspend, unsuspend, change_tier)."""
    if not payload.user_ids:
        raise HTTPException(status_code=400, detail="No user IDs provided")

    result = await db.execute(select(User).where(User.id.in_(payload.user_ids)))
    users = result.scalars().all()

    if not users:
        raise HTTPException(status_code=404, detail="No users found")

    affected = 0
    for user in users:
        if payload.action == "delete":
            user.deleted_at = datetime.now(UTC)
            user.deleted_by = admin.id
            user.deletion_reason = payload.reason or "Bulk deleted by admin"
            affected += 1
        elif payload.action == "suspend":
            if user.deleted_at is None:
                user.deleted_at = datetime.now(UTC)
                user.deleted_by = admin.id
                user.deletion_reason = "Bulk suspended by admin"
                affected += 1
        elif payload.action == "unsuspend":
            if user.deleted_at is not None:
                user.deleted_at = None
                user.deleted_by = None
                user.deletion_reason = None
                affected += 1
        elif payload.action == "change_tier":
            if payload.tier:
                user.subscription_tier = payload.tier
                affected += 1

    # Audit log
    audit = AuditLog(
        user_id=admin.id,
        action=AuditLog.ACTION_UPDATE,
        resource_type="user",
        details={
            "bulk_action": payload.action,
            "user_count": affected,
            "tier": payload.tier,
            "reason": payload.reason,
        },
        ip_address=request.client.host if request.client else None,
    )
    db.add(audit)

    await db.commit()

    logger.info(f"Bulk {payload.action} on {affected} users by admin {admin.id}")
    return {"status": "ok", "affected": affected}


@router.get("/users/export")
async def export_users(
    db: Annotated[AsyncSession, Depends(get_db)],
    admin: Annotated[User, Depends(require_admin)],
    format: str = "csv",
):
    """Export user list."""
    result = await db.execute(select(User).order_by(User.created_at.desc()))
    users = result.scalars().all()

    # Return as JSON for now (CSV export would need file response)
    return {
        "format": format,
        "count": len(users),
        "data": [
            {
                "id": str(u.id),
                "email": u.email,
                "display_name": u.display_name,
                "tier": u.subscription_tier,
                "created_at": u.created_at.isoformat()
            }
            for u in users
        ]
    }
