"""Content Review API routes - Phase 8.1: Content Quality Management.

Provides admin endpoints for:
- Review queue management (list, approve, reject)
- Bulk operations
- Duplicate detection and resolution
- Queue statistics
"""

import logging
from datetime import UTC, datetime
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy import func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db, require_admin
from app.models.content_review import ContentReviewQueue, ContentSimilarity
from app.models.insight import Insight
from app.models.user import User

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/admin/content", tags=["Content Review"])


# ============================================
# Request/Response Schemas
# ============================================


class ReviewQueueItem(BaseModel):
    """Single item in the review queue."""

    id: UUID
    content_type: str
    content_id: UUID
    status: str
    quality_score: float | None
    auto_approved: bool
    reviewer_id: UUID | None
    review_notes: str | None
    rejection_reason: str | None
    created_at: datetime
    reviewed_at: datetime | None

    model_config = ConfigDict(from_attributes=True)


class ReviewQueueResponse(BaseModel):
    """Paginated review queue response."""

    items: list[ReviewQueueItem]
    total: int
    page: int
    page_size: int
    has_more: bool


class ReviewAction(BaseModel):
    """Action to take on a review item."""

    action: str = Field(..., pattern="^(approve|reject|flag)$")
    notes: str | None = None
    rejection_reason: str | None = None


class BulkReviewAction(BaseModel):
    """Bulk action on multiple review items."""

    ids: list[UUID]
    action: str = Field(..., pattern="^(approve|reject)$")
    notes: str | None = None


class QueueStatsResponse(BaseModel):
    """Review queue statistics."""

    pending_count: int
    approved_count: int
    rejected_count: int
    flagged_count: int
    auto_approved_rate: float
    avg_quality_score: float | None
    avg_review_time_hours: float | None


class SimilarityItem(BaseModel):
    """Duplicate detection item."""

    id: UUID
    source_insight_id: UUID
    similar_insight_id: UUID
    similarity_score: float
    similarity_type: str
    resolved: bool
    resolution: str | None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class SimilarityResponse(BaseModel):
    """Paginated similarity response."""

    items: list[SimilarityItem]
    total: int
    has_more: bool


class ResolveSimilarityAction(BaseModel):
    """Action to resolve a similarity."""

    resolution: str = Field(..., pattern="^(keep_both|merge|delete_newer)$")


# ============================================
# Review Queue Endpoints
# ============================================


@router.get("/review-queue", response_model=ReviewQueueResponse)
async def list_review_queue(
    db: Annotated[AsyncSession, Depends(get_db)],
    admin: Annotated[User, Depends(require_admin)],
    status_filter: Annotated[str | None, Query(alias="status")] = None,
    content_type: str | None = None,
    quality_score_lt: float | None = None,
    page: int = 1,
    page_size: int = 20,
):
    """
    List pending content for review.

    - **status**: Filter by status (pending, approved, rejected, flagged)
    - **content_type**: Filter by type (insight, research, brand_package)
    - **quality_score_lt**: Filter by quality score less than value
    """
    query = select(ContentReviewQueue).order_by(ContentReviewQueue.created_at.desc())

    # Apply filters
    if status_filter:
        query = query.where(ContentReviewQueue.status == status_filter)
    if content_type:
        query = query.where(ContentReviewQueue.content_type == content_type)
    if quality_score_lt is not None:
        query = query.where(ContentReviewQueue.quality_score < quality_score_lt)

    # Count total
    count_query = select(func.count()).select_from(query.subquery())
    total = (await db.execute(count_query)).scalar() or 0

    # Paginate
    offset = (page - 1) * page_size
    query = query.offset(offset).limit(page_size)

    result = await db.execute(query)
    items = result.scalars().all()

    return ReviewQueueResponse(
        items=[ReviewQueueItem.model_validate(item) for item in items],
        total=total,
        page=page,
        page_size=page_size,
        has_more=offset + len(items) < total,
    )


@router.patch("/review-queue/{item_id}", response_model=ReviewQueueItem)
async def review_content(
    item_id: UUID,
    action: ReviewAction,
    db: Annotated[AsyncSession, Depends(get_db)],
    admin: Annotated[User, Depends(require_admin)],
):
    """
    Approve, reject, or flag content.

    - **approve**: Mark content as approved
    - **reject**: Mark content as rejected with reason
    - **flag**: Flag for additional review
    """
    result = await db.execute(
        select(ContentReviewQueue).where(ContentReviewQueue.id == item_id)
    )
    item = result.scalar_one_or_none()

    if not item:
        raise HTTPException(status_code=404, detail="Review item not found")

    # Update status
    if action.action == "approve":
        item.status = "approved"
    elif action.action == "reject":
        item.status = "rejected"
        item.rejection_reason = action.rejection_reason
    elif action.action == "flag":
        item.status = "flagged"

    item.reviewer_id = admin.id
    item.review_notes = action.notes
    item.reviewed_at = datetime.now(UTC)

    await db.commit()
    await db.refresh(item)

    logger.info(f"Content {item_id} {action.action}ed by admin {admin.id}")

    return ReviewQueueItem.model_validate(item)


@router.post("/review-queue/bulk", response_model=dict)
async def bulk_review_content(
    action: BulkReviewAction,
    db: Annotated[AsyncSession, Depends(get_db)],
    admin: Annotated[User, Depends(require_admin)],
):
    """
    Bulk approve or reject multiple items.
    """
    new_status = "approved" if action.action == "approve" else "rejected"

    result = await db.execute(
        update(ContentReviewQueue)
        .where(ContentReviewQueue.id.in_(action.ids))
        .values(
            status=new_status,
            reviewer_id=admin.id,
            review_notes=action.notes,
            reviewed_at=datetime.now(UTC),
        )
        .returning(ContentReviewQueue.id)
    )

    updated_ids = [row[0] for row in result.fetchall()]
    await db.commit()

    logger.info(f"Bulk {action.action} on {len(updated_ids)} items by admin {admin.id}")

    return {
        "action": action.action,
        "processed": len(updated_ids),
        "ids": updated_ids,
    }


@router.get("/review-queue/stats", response_model=QueueStatsResponse)
async def get_queue_stats(
    db: Annotated[AsyncSession, Depends(get_db)],
    admin: Annotated[User, Depends(require_admin)],
):
    """
    Get review queue statistics.
    """
    # Count by status
    status_counts = await db.execute(
        select(
            ContentReviewQueue.status,
            func.count(ContentReviewQueue.id),
        ).group_by(ContentReviewQueue.status)
    )
    counts = {row[0]: row[1] for row in status_counts.fetchall()}

    # Auto-approved rate
    total_approved = await db.execute(
        select(func.count()).where(ContentReviewQueue.status == "approved")
    )
    auto_approved = await db.execute(
        select(func.count()).where(
            ContentReviewQueue.status == "approved",
            ContentReviewQueue.auto_approved == True,
        )
    )
    total_approved_count = total_approved.scalar() or 0
    auto_approved_count = auto_approved.scalar() or 0
    auto_approved_rate = (
        auto_approved_count / total_approved_count if total_approved_count > 0 else 0.0
    )

    # Average quality score
    avg_score = await db.execute(
        select(func.avg(ContentReviewQueue.quality_score))
    )
    avg_quality = avg_score.scalar()

    # Average review time (for reviewed items)
    # This would require a more complex query with date arithmetic

    return QueueStatsResponse(
        pending_count=counts.get("pending", 0),
        approved_count=counts.get("approved", 0),
        rejected_count=counts.get("rejected", 0),
        flagged_count=counts.get("flagged", 0),
        auto_approved_rate=auto_approved_rate,
        avg_quality_score=float(avg_quality) if avg_quality else None,
        avg_review_time_hours=None,  # TODO: Implement
    )


# ============================================
# Duplicate Detection Endpoints
# ============================================


@router.get("/duplicates", response_model=SimilarityResponse)
async def list_duplicates(
    db: Annotated[AsyncSession, Depends(get_db)],
    admin: Annotated[User, Depends(require_admin)],
    resolved: bool | None = None,
    similarity_type: str | None = None,
    limit: int = 50,
    offset: int = 0,
):
    """
    List potential duplicate insights.

    - **resolved**: Filter by resolution status
    - **similarity_type**: Filter by type (exact, near, thematic)
    """
    query = select(ContentSimilarity).order_by(
        ContentSimilarity.similarity_score.desc()
    )

    if resolved is not None:
        query = query.where(ContentSimilarity.resolved == resolved)
    if similarity_type:
        query = query.where(ContentSimilarity.similarity_type == similarity_type)

    # Count total
    count_query = select(func.count()).select_from(query.subquery())
    total = (await db.execute(count_query)).scalar() or 0

    # Apply pagination
    query = query.offset(offset).limit(limit)

    result = await db.execute(query)
    items = result.scalars().all()

    return SimilarityResponse(
        items=[SimilarityItem.model_validate(item) for item in items],
        total=total,
        has_more=offset + len(items) < total,
    )


@router.post("/duplicates/{similarity_id}/resolve", response_model=SimilarityItem)
async def resolve_duplicate(
    similarity_id: UUID,
    action: ResolveSimilarityAction,
    db: Annotated[AsyncSession, Depends(get_db)],
    admin: Annotated[User, Depends(require_admin)],
):
    """
    Resolve a duplicate pair.

    - **keep_both**: Mark as reviewed, keep both insights
    - **merge**: Merge into source insight (delete newer)
    - **delete_newer**: Delete the similar insight
    """
    result = await db.execute(
        select(ContentSimilarity).where(ContentSimilarity.id == similarity_id)
    )
    similarity = result.scalar_one_or_none()

    if not similarity:
        raise HTTPException(status_code=404, detail="Similarity record not found")

    if similarity.resolved:
        raise HTTPException(status_code=400, detail="Already resolved")

    similarity.resolved = True
    similarity.resolution = action.resolution

    # Handle delete_newer action
    if action.resolution == "delete_newer":
        await db.execute(
            update(Insight)
            .where(Insight.id == similarity.similar_insight_id)
            .values(is_deleted=True)
        )

    await db.commit()
    await db.refresh(similarity)

    logger.info(
        f"Duplicate {similarity_id} resolved as {action.resolution} by admin {admin.id}"
    )

    return SimilarityItem.model_validate(similarity)


@router.get("/duplicates/stats", response_model=dict)
async def get_duplicate_stats(
    db: Annotated[AsyncSession, Depends(get_db)],
    admin: Annotated[User, Depends(require_admin)],
):
    """
    Get duplicate detection statistics.
    """
    total = await db.execute(select(func.count(ContentSimilarity.id)))
    unresolved = await db.execute(
        select(func.count()).where(ContentSimilarity.resolved == False)
    )
    avg_score = await db.execute(
        select(func.avg(ContentSimilarity.similarity_score))
    )

    # Count by type
    by_type = await db.execute(
        select(
            ContentSimilarity.similarity_type,
            func.count(ContentSimilarity.id),
        ).group_by(ContentSimilarity.similarity_type)
    )
    type_counts = {row[0]: row[1] for row in by_type.fetchall()}

    return {
        "total_pairs": total.scalar() or 0,
        "unresolved": unresolved.scalar() or 0,
        "avg_similarity_score": float(avg_score.scalar() or 0),
        "by_type": type_counts,
    }
