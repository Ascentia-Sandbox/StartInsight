"""API endpoints for user authentication and workspace - Phase 4.1.

Endpoints:
- /api/users/me - Current user profile (GET, PATCH)
- /api/users/me/saved - Saved insights workspace
- /api/users/me/ratings - User ratings
- /api/users/insights/{id}/save - Save/unsave insight
- /api/users/insights/{id}/rate - Rate insight

See architecture.md "API Architecture Phase 4+" for full specification.
"""

import logging
import secrets
import string
from datetime import UTC, datetime
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import delete, func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.api.deps import CurrentUser
from app.db.query_helpers import count_by_field
from app.db.session import get_db
from app.models.insight import Insight
from app.models.insight_interaction import InsightInteraction
from app.models.saved_insight import SavedInsight
from app.models.user_rating import UserRating
from app.schemas.user import (
    ClaimResponse,
    InteractionCreate,
    InteractionResponse,
    InteractionStatsResponse,
    RatingCreate,
    RatingListResponse,
    RatingResponse,
    SavedInsightCreate,
    SavedInsightListResponse,
    SavedInsightResponse,
    SavedInsightUpdate,
    ShareResponse,
    UserResponse,
    UserUpdate,
    WorkspaceStatusResponse,
)
from app.services.user_service import UserService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/users", tags=["users"])

_REFERRAL_ALPHABET = string.ascii_uppercase + string.digits


def _generate_referral_code() -> str:
    """Generate an 8-char alphanumeric referral code (uppercase)."""
    return "".join(secrets.choice(_REFERRAL_ALPHABET) for _ in range(8))


# ============================================
# USER PROFILE ENDPOINTS
# ============================================


@router.get("/me", response_model=UserResponse)
async def get_current_user_profile(
    current_user: CurrentUser,
    db: AsyncSession = Depends(get_db),
) -> UserResponse:
    """
    Get current authenticated user's profile.

    Returns user profile including subscription tier and preferences.
    Also back-fills a referral code for users who don't have one yet.
    """
    # Back-fill referral code for existing users who don't have one
    if not current_user.referral_code:
        for _ in range(5):
            candidate = _generate_referral_code()
            existing = await db.scalar(
                select(current_user.__class__).where(
                    current_user.__class__.referral_code == candidate
                ).limit(1)
            )
            if not existing:
                current_user.referral_code = candidate
                current_user.updated_at = datetime.now(UTC)
                await db.commit()
                await db.refresh(current_user)
                logger.info(
                    f"Back-filled referral code {candidate} for user {current_user.email}"
                )
                break

    logger.info(f"User profile accessed: {current_user.email}")
    return UserResponse.model_validate(current_user)


@router.patch("/me", response_model=UserResponse)
async def update_user_profile(
    update_data: UserUpdate,
    current_user: CurrentUser,
    db: AsyncSession = Depends(get_db),
) -> UserResponse:
    """
    Update current user's profile.

    Updatable fields:
    - display_name
    - avatar_url
    - preferences (theme, notifications, etc.)
    """
    # Update provided fields
    if update_data.display_name is not None:
        current_user.display_name = update_data.display_name
    if update_data.avatar_url is not None:
        current_user.avatar_url = update_data.avatar_url
    if update_data.preferences is not None:
        # Merge preferences instead of replacing
        current_user.preferences = {
            **current_user.preferences,
            **update_data.preferences,
        }

    current_user.updated_at = datetime.now(UTC)
    await db.commit()
    await db.refresh(current_user)

    logger.info(f"User profile updated: {current_user.email}")
    return UserResponse.model_validate(current_user)


@router.get("/me/status", response_model=WorkspaceStatusResponse)
async def get_workspace_status(
    current_user: CurrentUser,
    db: AsyncSession = Depends(get_db),
) -> WorkspaceStatusResponse:
    """
    Get user's workspace statistics.

    Returns counts of saved, interested, and building insights.
    """
    # Count saved insights (uses count_by_field helper)
    saved_count = await count_by_field(db, SavedInsight, "user_id", current_user.id)

    # Count by status - Note: count_by_field only supports single field, so we keep compound WHERE for now
    interested_query = select(func.count()).select_from(SavedInsight).where(
        SavedInsight.user_id == current_user.id,
        SavedInsight.status == "interested",
    )
    interested_count = await db.scalar(interested_query) or 0

    building_query = select(func.count()).select_from(SavedInsight).where(
        SavedInsight.user_id == current_user.id,
        SavedInsight.status == "building",
    )
    building_count = await db.scalar(building_query) or 0

    # Count ratings (uses count_by_field helper)
    ratings_count = await count_by_field(db, UserRating, "user_id", current_user.id)

    return WorkspaceStatusResponse(
        saved_count=saved_count,
        interested_count=interested_count,
        building_count=building_count,
        ratings_count=ratings_count,
    )


# ============================================
# SAVED INSIGHTS ENDPOINTS
# ============================================


@router.get("/me/saved", response_model=SavedInsightListResponse)
async def list_saved_insights(
    current_user: CurrentUser,
    status: Annotated[
        str | None,
        Query(description="Filter by status: interested, saved, building, not_interested"),
    ] = None,
    limit: Annotated[int, Query(ge=1, le=100)] = 20,
    offset: Annotated[int, Query(ge=0)] = 0,
    db: AsyncSession = Depends(get_db),
) -> SavedInsightListResponse:
    """
    List user's saved insights with optional status filter.

    - **status**: Filter by status (interested, saved, building, not_interested)
    - **limit**: Results per page (max 100)
    - **offset**: Pagination offset
    """
    # Build query
    query = (
        select(SavedInsight)
        .options(selectinload(SavedInsight.insight))
        .where(SavedInsight.user_id == current_user.id)
        .order_by(SavedInsight.saved_at.desc())
    )

    if status:
        query = query.where(SavedInsight.status == status)

    # Get total count (simplified with count_by_field for single field case)
    if not status:
        # Simple case: count all for user
        total = await count_by_field(db, SavedInsight, "user_id", current_user.id)
    else:
        # Complex case: count with status filter (keep manual query)
        count_query = select(func.count()).select_from(SavedInsight).where(
            SavedInsight.user_id == current_user.id,
            SavedInsight.status == status,
        )
        total = await db.scalar(count_query) or 0

    # Paginate
    query = query.limit(limit).offset(offset)
    result = await db.execute(query)
    saved_insights = result.scalars().all()

    logger.info(
        f"Listed {len(saved_insights)} saved insights for user {current_user.email}"
    )

    return SavedInsightListResponse(
        items=[SavedInsightResponse.model_validate(s) for s in saved_insights],
        total=total,
        limit=limit,
        offset=offset,
    )


@router.get("/me/interested", response_model=SavedInsightListResponse)
async def list_interested_insights(
    current_user: CurrentUser,
    limit: Annotated[int, Query(ge=1, le=100)] = 20,
    offset: Annotated[int, Query(ge=0)] = 0,
    db: AsyncSession = Depends(get_db),
) -> SavedInsightListResponse:
    """
    List insights user marked as interested.
    """
    return await list_saved_insights(
        current_user=current_user,
        status="interested",
        limit=limit,
        offset=offset,
        db=db,
    )


@router.get("/me/building", response_model=SavedInsightListResponse)
async def list_building_insights(
    current_user: CurrentUser,
    limit: Annotated[int, Query(ge=1, le=100)] = 20,
    offset: Annotated[int, Query(ge=0)] = 0,
    db: AsyncSession = Depends(get_db),
) -> SavedInsightListResponse:
    """
    List insights user has claimed (building status).
    """
    return await list_saved_insights(
        current_user=current_user,
        status="building",
        limit=limit,
        offset=offset,
        db=db,
    )


# ============================================
# INSIGHT ACTIONS
# ============================================


@router.post("/insights/{insight_id}/save", response_model=SavedInsightResponse)
async def save_insight(
    insight_id: UUID,
    save_data: SavedInsightCreate | None = None,
    current_user: CurrentUser = None,
    db: AsyncSession = Depends(get_db),
) -> SavedInsightResponse:
    """
    Save an insight to user's workspace.

    - **notes**: Optional personal notes
    - **tags**: Optional tags for organization
    """
    # Verify insight exists
    insight = await db.get(Insight, insight_id)
    if not insight:
        raise HTTPException(status_code=404, detail="Insight not found")

    # Use UserService to get or create SavedInsight
    saved_insight = await UserService.get_or_create_saved_insight(
        db=db,
        user_id=current_user.id,
        insight_id=insight_id,
        status="saved",
        notes=save_data.notes if save_data else None,
        tags=save_data.tags if save_data else None,
    )

    logger.info(f"User {current_user.email} saved insight {insight_id}")
    return SavedInsightResponse.model_validate(saved_insight)


@router.delete("/insights/{insight_id}/save", status_code=status.HTTP_204_NO_CONTENT)
async def unsave_insight(
    insight_id: UUID,
    current_user: CurrentUser,
    db: AsyncSession = Depends(get_db),
) -> None:
    """
    Remove an insight from user's saved workspace.
    """
    result = await db.execute(
        delete(SavedInsight).where(
            SavedInsight.user_id == current_user.id,
            SavedInsight.insight_id == insight_id,
        )
    )

    if result.rowcount == 0:
        raise HTTPException(status_code=404, detail="Saved insight not found")

    await db.commit()
    logger.info(f"User {current_user.email} unsaved insight {insight_id}")


@router.patch("/insights/{insight_id}/save", response_model=SavedInsightResponse)
async def update_saved_insight(
    insight_id: UUID,
    update_data: SavedInsightUpdate,
    current_user: CurrentUser,
    db: AsyncSession = Depends(get_db),
) -> SavedInsightResponse:
    """
    Update saved insight notes, tags, or status.
    """
    result = await db.execute(
        select(SavedInsight).where(
            SavedInsight.user_id == current_user.id,
            SavedInsight.insight_id == insight_id,
        )
    )
    saved_insight = result.scalar_one_or_none()

    if not saved_insight:
        raise HTTPException(status_code=404, detail="Saved insight not found")

    # Update fields
    if update_data.notes is not None:
        saved_insight.notes = update_data.notes
    if update_data.tags is not None:
        saved_insight.tags = update_data.tags
    if update_data.status is not None:
        saved_insight.status = update_data.status
        if update_data.status == "building":
            saved_insight.claimed_at = datetime.now(UTC)

    await db.commit()
    await db.refresh(saved_insight)

    logger.info(f"User {current_user.email} updated saved insight {insight_id}")
    return SavedInsightResponse.model_validate(saved_insight)


@router.post("/insights/{insight_id}/interested", response_model=SavedInsightResponse)
async def mark_interested(
    insight_id: UUID,
    current_user: CurrentUser,
    db: AsyncSession = Depends(get_db),
) -> SavedInsightResponse:
    """
    Mark an insight as 'interested' (IdeaBrowser parity).
    """
    # Verify insight exists
    insight = await db.get(Insight, insight_id)
    if not insight:
        raise HTTPException(status_code=404, detail="Insight not found")

    # Use UserService to get or create SavedInsight with interested status
    saved_insight = await UserService.get_or_create_saved_insight(
        db=db,
        user_id=current_user.id,
        insight_id=insight_id,
        status="interested",
    )

    logger.info(f"User {current_user.email} marked insight {insight_id} as interested")
    return SavedInsightResponse.model_validate(saved_insight)


@router.post("/insights/{insight_id}/claim", response_model=ClaimResponse)
async def claim_insight(
    insight_id: UUID,
    current_user: CurrentUser,
    db: AsyncSession = Depends(get_db),
) -> ClaimResponse:
    """
    Claim an insight (mark as 'building').

    Indicates user is actively pursuing this idea.
    """
    # Verify insight exists
    insight = await db.get(Insight, insight_id)
    if not insight:
        raise HTTPException(status_code=404, detail="Insight not found")

    # Use UserService to get or create SavedInsight with building status
    claimed_at = datetime.now(UTC)
    await UserService.get_or_create_saved_insight(
        db=db,
        user_id=current_user.id,
        insight_id=insight_id,
        status="building",
        claimed_at=claimed_at,
    )

    logger.info(f"User {current_user.email} claimed insight {insight_id}")
    return ClaimResponse(
        status="building",
        claimed_at=claimed_at,
        insight_id=insight_id,
    )


@router.post("/insights/{insight_id}/share", response_model=ShareResponse)
async def track_share(
    insight_id: UUID,
    current_user: CurrentUser,
    db: AsyncSession = Depends(get_db),
) -> ShareResponse:
    """
    Track when user shares an insight.

    Increments share counter for analytics.
    """
    # Verify insight exists
    insight = await db.get(Insight, insight_id)
    if not insight:
        raise HTTPException(status_code=404, detail="Insight not found")

    # Use UserService to increment share count
    saved_insight = await UserService.increment_share_count(
        db=db,
        user_id=current_user.id,
        insight_id=insight_id,
    )

    logger.info(f"User {current_user.email} shared insight {insight_id}")
    return ShareResponse(
        insight_id=insight_id,
        shared_count=saved_insight.shared_count,
    )


# ============================================
# RATING ENDPOINTS
# ============================================


@router.post("/insights/{insight_id}/rate", response_model=RatingResponse)
async def rate_insight(
    insight_id: UUID,
    rating_data: RatingCreate,
    current_user: CurrentUser,
    db: AsyncSession = Depends(get_db),
) -> RatingResponse:
    """
    Rate an insight (1-5 stars).

    - **rating**: 1-5 star rating
    - **feedback**: Optional text feedback
    """
    # Verify insight exists
    insight = await db.get(Insight, insight_id)
    if not insight:
        raise HTTPException(status_code=404, detail="Insight not found")

    # Check for existing rating
    result = await db.execute(
        select(UserRating).where(
            UserRating.user_id == current_user.id,
            UserRating.insight_id == insight_id,
        )
    )
    existing_rating = result.scalar_one_or_none()

    if existing_rating:
        # Update existing rating
        existing_rating.rating = rating_data.rating
        existing_rating.feedback = rating_data.feedback
        existing_rating.rated_at = datetime.now(UTC)
        await db.commit()
        await db.refresh(existing_rating)
        rating = existing_rating
    else:
        # Create new rating
        rating = UserRating(
            user_id=current_user.id,
            insight_id=insight_id,
            rating=rating_data.rating,
            feedback=rating_data.feedback,
        )
        db.add(rating)
        await db.commit()
        await db.refresh(rating)

    logger.info(
        f"User {current_user.email} rated insight {insight_id}: {rating_data.rating}/5"
    )
    return RatingResponse.model_validate(rating)


@router.get("/insights/{insight_id}/rate", response_model=RatingResponse | None)
async def get_my_rating(
    insight_id: UUID,
    current_user: CurrentUser,
    db: AsyncSession = Depends(get_db),
) -> RatingResponse | None:
    """
    Get current user's rating for an insight.

    Returns None if not rated.
    """
    result = await db.execute(
        select(UserRating).where(
            UserRating.user_id == current_user.id,
            UserRating.insight_id == insight_id,
        )
    )
    rating = result.scalar_one_or_none()

    if not rating:
        return None

    return RatingResponse.model_validate(rating)


@router.delete(
    "/insights/{insight_id}/rate", status_code=status.HTTP_204_NO_CONTENT
)
async def delete_rating(
    insight_id: UUID,
    current_user: CurrentUser,
    db: AsyncSession = Depends(get_db),
) -> None:
    """
    Delete user's rating for an insight.
    """
    result = await db.execute(
        delete(UserRating).where(
            UserRating.user_id == current_user.id,
            UserRating.insight_id == insight_id,
        )
    )

    if result.rowcount == 0:
        raise HTTPException(status_code=404, detail="Rating not found")

    await db.commit()
    logger.info(f"User {current_user.email} deleted rating for insight {insight_id}")


@router.get("/me/ratings", response_model=RatingListResponse)
async def list_my_ratings(
    current_user: CurrentUser,
    limit: Annotated[int, Query(ge=1, le=100)] = 50,
    offset: Annotated[int, Query(ge=0)] = 0,
    db: AsyncSession = Depends(get_db),
) -> RatingListResponse:
    """
    List all ratings given by current user.
    """
    # Get total count (uses count_by_field helper)
    total = await count_by_field(db, UserRating, "user_id", current_user.id)

    # Get ratings
    query = (
        select(UserRating)
        .where(UserRating.user_id == current_user.id)
        .order_by(UserRating.rated_at.desc())
        .limit(limit)
        .offset(offset)
    )
    result = await db.execute(query)
    ratings = result.scalars().all()

    return RatingListResponse(
        items=[RatingResponse.model_validate(r) for r in ratings],
        total=total,
    )


# ============================================
# INTERACTION TRACKING ENDPOINTS (Phase 4.4)
# ============================================


@router.post("/insights/{insight_id}/track", response_model=InteractionResponse)
async def track_interaction(
    insight_id: UUID,
    interaction_data: InteractionCreate,
    current_user: CurrentUser,
    db: AsyncSession = Depends(get_db),
) -> InteractionResponse:
    """
    Track a user interaction with an insight.

    Interaction types:
    - **view**: User viewed insight details
    - **interested**: User marked as interested
    - **claim**: User claimed to build
    - **share**: User shared insight
    - **export**: User exported insight (PDF, etc.)

    This is used for analytics and recommendation improvements.
    """
    # Validate interaction type
    valid_types = ["view", "interested", "claim", "share", "export"]
    if interaction_data.interaction_type not in valid_types:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid interaction type. Must be one of: {valid_types}",
        )

    # Verify insight exists
    insight = await db.get(Insight, insight_id)
    if not insight:
        raise HTTPException(status_code=404, detail="Insight not found")

    # Create interaction record
    interaction = InsightInteraction(
        user_id=current_user.id,
        insight_id=insight_id,
        interaction_type=interaction_data.interaction_type,
        extra_metadata=interaction_data.extra_metadata,
    )
    db.add(interaction)
    await db.commit()
    await db.refresh(interaction)

    logger.info(
        f"User {current_user.email} tracked {interaction_data.interaction_type} "
        f"on insight {insight_id}"
    )
    return InteractionResponse.model_validate(interaction)


@router.get("/insights/{insight_id}/stats", response_model=InteractionStatsResponse)
async def get_insight_interaction_stats(
    insight_id: UUID,
    current_user: CurrentUser,
    db: AsyncSession = Depends(get_db),
) -> InteractionStatsResponse:
    """
    Get interaction statistics for an insight.

    Returns counts of views, interested, claims, shares, and exports.
    """
    # Verify insight exists
    insight = await db.get(Insight, insight_id)
    if not insight:
        raise HTTPException(status_code=404, detail="Insight not found")

    # Count interactions by type
    stats_query = (
        select(
            InsightInteraction.interaction_type,
            func.count().label("count"),
        )
        .where(InsightInteraction.insight_id == insight_id)
        .group_by(InsightInteraction.interaction_type)
    )
    result = await db.execute(stats_query)
    stats = {row.interaction_type: row.count for row in result}

    return InteractionStatsResponse(
        insight_id=insight_id,
        total_views=stats.get("view", 0),
        total_interested=stats.get("interested", 0),
        total_claims=stats.get("claim", 0),
        total_shares=stats.get("share", 0),
        total_exports=stats.get("export", 0),
    )
