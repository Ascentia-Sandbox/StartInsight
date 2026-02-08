"""API endpoints for Success Stories (Phase 12.3: IdeaBrowser Replication).

Provides CRUD operations for founder case studies with revenue timelines.
"""

import logging
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import AdminUser
from app.db.session import get_db
from app.models.success_story import SuccessStory
from app.schemas.public_content import (
    SuccessStoryCreate,
    SuccessStoryListResponse,
    SuccessStoryResponse,
    SuccessStoryUpdate,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/success-stories", tags=["success-stories"])


@router.get("", response_model=SuccessStoryListResponse)
async def list_success_stories(
    featured: Annotated[
        bool | None, Query(description="Filter by featured status")
    ] = None,
    search: Annotated[
        str | None, Query(description="Search by founder or company name")
    ] = None,
    limit: Annotated[int, Query(ge=1, le=50, description="Number of results")] = 10,
    offset: Annotated[int, Query(ge=0, description="Pagination offset")] = 0,
    db: AsyncSession = Depends(get_db),
) -> SuccessStoryListResponse:
    """
    List all success stories with filtering and pagination.

    Only returns published stories for public access.

    - **featured**: Filter by featured status
    - **search**: Search in founder name and company name
    - **limit**: Number of results per page (default 10, max 50)
    - **offset**: Pagination offset
    """
    # Build query - only published stories
    query = select(SuccessStory).where(SuccessStory.is_published == True)

    # Apply filters
    if featured is not None:
        query = query.where(SuccessStory.is_featured == featured)
    if search:
        query = query.where(
            (SuccessStory.founder_name.ilike(f"%{search}%"))
            | (SuccessStory.company_name.ilike(f"%{search}%"))
        )

    # Sort by created_at descending
    query = query.order_by(SuccessStory.created_at.desc())

    # Pagination
    query = query.limit(limit).offset(offset)

    # Execute
    result = await db.execute(query)
    stories = result.scalars().all()

    # Get total count
    count_query = select(func.count(SuccessStory.id)).where(
        SuccessStory.is_published == True
    )
    if featured is not None:
        count_query = count_query.where(SuccessStory.is_featured == featured)
    if search:
        count_query = count_query.where(
            (SuccessStory.founder_name.ilike(f"%{search}%"))
            | (SuccessStory.company_name.ilike(f"%{search}%"))
        )

    total = await db.scalar(count_query)

    logger.info(f"Listed {len(stories)} success stories (total={total})")

    return SuccessStoryListResponse(
        stories=[SuccessStoryResponse.model_validate(s) for s in stories],
        total=total or 0,
        limit=limit,
        offset=offset,
    )


@router.get("/featured", response_model=list[SuccessStoryResponse])
async def get_featured_stories(
    limit: Annotated[int, Query(ge=1, le=10, description="Number of featured stories")] = 3,
    db: AsyncSession = Depends(get_db),
) -> list[SuccessStoryResponse]:
    """
    Get featured success stories for homepage display.

    Returns published stories marked as featured, sorted by creation date.
    """
    query = (
        select(SuccessStory)
        .where(SuccessStory.is_featured == True, SuccessStory.is_published == True)
        .order_by(SuccessStory.created_at.desc())
        .limit(limit)
    )

    result = await db.execute(query)
    stories = result.scalars().all()

    logger.info(f"Retrieved {len(stories)} featured success stories")

    return [SuccessStoryResponse.model_validate(s) for s in stories]


@router.get("/{story_id}", response_model=SuccessStoryResponse)
async def get_success_story(
    story_id: UUID,
    db: AsyncSession = Depends(get_db),
) -> SuccessStoryResponse:
    """
    Get a single success story by ID.

    Only returns if published (or admin access).
    """
    query = select(SuccessStory).where(
        SuccessStory.id == story_id, SuccessStory.is_published == True
    )
    result = await db.execute(query)
    story = result.scalar_one_or_none()

    if not story:
        raise HTTPException(status_code=404, detail="Success story not found")

    return SuccessStoryResponse.model_validate(story)


@router.post("", response_model=SuccessStoryResponse, status_code=201)
async def create_success_story(
    story_data: SuccessStoryCreate,
    admin: AdminUser,
    db: AsyncSession = Depends(get_db),
) -> SuccessStoryResponse:
    """
    Create a new success story (admin only).
    """

    story = SuccessStory(**story_data.model_dump())
    db.add(story)
    await db.commit()
    await db.refresh(story)

    logger.info(f"Created success story: {story.company_name} (id={story.id})")

    return SuccessStoryResponse.model_validate(story)


@router.patch("/{story_id}", response_model=SuccessStoryResponse)
async def update_success_story(
    story_id: UUID,
    story_data: SuccessStoryUpdate,
    admin: AdminUser,
    db: AsyncSession = Depends(get_db),
) -> SuccessStoryResponse:
    """
    Update an existing success story (admin only).
    """

    query = select(SuccessStory).where(SuccessStory.id == story_id)
    result = await db.execute(query)
    story = result.scalar_one_or_none()

    if not story:
        raise HTTPException(status_code=404, detail="Success story not found")

    # Update only provided fields
    update_data = story_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(story, field, value)

    await db.commit()
    await db.refresh(story)

    logger.info(f"Updated success story: {story.company_name} (id={story.id})")

    return SuccessStoryResponse.model_validate(story)


@router.delete("/{story_id}", status_code=204)
async def delete_success_story(
    story_id: UUID,
    admin: AdminUser,
    db: AsyncSession = Depends(get_db),
) -> None:
    """
    Delete a success story (admin only).
    """

    query = select(SuccessStory).where(SuccessStory.id == story_id)
    result = await db.execute(query)
    story = result.scalar_one_or_none()

    if not story:
        raise HTTPException(status_code=404, detail="Success story not found")

    await db.delete(story)
    await db.commit()

    logger.info(f"Deleted success story: {story.company_name} (id={story_id})")
