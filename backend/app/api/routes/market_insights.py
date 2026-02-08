"""API endpoints for Market Insights blog (Phase 12.3: IdeaBrowser Replication).

Provides CRUD operations for blog articles with Markdown content.
"""

import logging
import re
from datetime import UTC, datetime
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import AdminUser
from app.db.session import get_db
from app.models.market_insight import MarketInsight
from app.schemas.public_content import (
    MarketInsightCreate,
    MarketInsightListResponse,
    MarketInsightResponse,
    MarketInsightUpdate,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/market-insights", tags=["market-insights"])


def generate_slug(title: str) -> str:
    """Generate URL-friendly slug from title."""
    slug = title.lower()
    slug = re.sub(r"[^\w\s-]", "", slug)
    slug = re.sub(r"[\s_]+", "-", slug)
    slug = re.sub(r"-+", "-", slug).strip("-")
    return slug[:500]


@router.get("", response_model=MarketInsightListResponse)
async def list_market_insights(
    category: Annotated[
        str | None, Query(description="Filter by category (Trends, Analysis, Guides)")
    ] = None,
    featured: Annotated[
        bool | None, Query(description="Filter by featured status")
    ] = None,
    search: Annotated[
        str | None, Query(description="Search by title or summary")
    ] = None,
    limit: Annotated[int, Query(ge=1, le=50, description="Number of results")] = 10,
    offset: Annotated[int, Query(ge=0, description="Pagination offset")] = 0,
    db: AsyncSession = Depends(get_db),
) -> MarketInsightListResponse:
    """
    List all market insights with filtering and pagination.

    Only returns published articles for public access.

    - **category**: Filter by article category (Trends, Analysis, Guides)
    - **featured**: Filter by featured status
    - **search**: Search in title and summary
    - **limit**: Number of results per page (default 10, max 50)
    - **offset**: Pagination offset
    """
    # Build query - only published articles
    query = select(MarketInsight).where(MarketInsight.is_published == True)

    # Apply filters
    if category:
        query = query.where(MarketInsight.category == category)
    if featured is not None:
        query = query.where(MarketInsight.is_featured == featured)
    if search:
        query = query.where(
            (MarketInsight.title.ilike(f"%{search}%"))
            | (MarketInsight.summary.ilike(f"%{search}%"))
        )

    # Sort by published_at descending
    query = query.order_by(MarketInsight.published_at.desc())

    # Pagination
    query = query.limit(limit).offset(offset)

    # Execute
    result = await db.execute(query)
    articles = result.scalars().all()

    # Get total count
    count_query = select(func.count(MarketInsight.id)).where(
        MarketInsight.is_published == True
    )
    if category:
        count_query = count_query.where(MarketInsight.category == category)
    if featured is not None:
        count_query = count_query.where(MarketInsight.is_featured == featured)
    if search:
        count_query = count_query.where(
            (MarketInsight.title.ilike(f"%{search}%"))
            | (MarketInsight.summary.ilike(f"%{search}%"))
        )

    total = await db.scalar(count_query)

    logger.info(f"Listed {len(articles)} market insights (category={category}, total={total})")

    return MarketInsightListResponse(
        articles=[MarketInsightResponse.model_validate(a) for a in articles],
        total=total or 0,
        limit=limit,
        offset=offset,
    )


@router.get("/recent", response_model=list[MarketInsightResponse])
async def get_recent_articles(
    limit: Annotated[int, Query(ge=1, le=10, description="Number of recent articles")] = 5,
    db: AsyncSession = Depends(get_db),
) -> list[MarketInsightResponse]:
    """
    Get most recent published articles.

    Useful for sidebar "Recent Articles" widget.
    """
    query = (
        select(MarketInsight)
        .where(MarketInsight.is_published == True)
        .order_by(MarketInsight.published_at.desc())
        .limit(limit)
    )

    result = await db.execute(query)
    articles = result.scalars().all()

    logger.info(f"Retrieved {len(articles)} recent market insights")

    return [MarketInsightResponse.model_validate(a) for a in articles]


@router.get("/categories", response_model=list[str])
async def get_article_categories(
    db: AsyncSession = Depends(get_db),
) -> list[str]:
    """
    Get all unique article categories.

    Useful for building category tabs.
    """
    query = (
        select(MarketInsight.category)
        .where(MarketInsight.is_published == True)
        .distinct()
        .order_by(MarketInsight.category)
    )

    result = await db.execute(query)
    categories = result.scalars().all()

    return list(categories)


@router.get("/{slug}", response_model=MarketInsightResponse)
async def get_market_insight_by_slug(
    slug: str,
    db: AsyncSession = Depends(get_db),
) -> MarketInsightResponse:
    """
    Get a single market insight by slug.

    Only returns if published (or admin access).
    Increments view count on each access.
    """
    query = select(MarketInsight).where(
        MarketInsight.slug == slug, MarketInsight.is_published == True
    )
    result = await db.execute(query)
    article = result.scalar_one_or_none()

    if not article:
        raise HTTPException(status_code=404, detail="Article not found")

    # Increment view count
    article.view_count += 1
    await db.commit()
    await db.refresh(article)

    return MarketInsightResponse.model_validate(article)


@router.get("/id/{article_id}", response_model=MarketInsightResponse)
async def get_market_insight_by_id(
    article_id: UUID,
    admin: AdminUser,
    db: AsyncSession = Depends(get_db),
) -> MarketInsightResponse:
    """
    Get a single market insight by ID.

    Admin access - returns even if not published.
    """

    query = select(MarketInsight).where(MarketInsight.id == article_id)
    result = await db.execute(query)
    article = result.scalar_one_or_none()

    if not article:
        raise HTTPException(status_code=404, detail="Article not found")

    return MarketInsightResponse.model_validate(article)


@router.post("", response_model=MarketInsightResponse, status_code=201)
async def create_market_insight(
    article_data: MarketInsightCreate,
    admin: AdminUser,
    db: AsyncSession = Depends(get_db),
) -> MarketInsightResponse:
    """
    Create a new market insight (admin only).

    Auto-generates slug from title if not provided.
    Sets published_at when is_published is True.
    """

    # Generate slug if not provided
    slug = article_data.slug or generate_slug(article_data.title)

    # Check for duplicate slug
    existing_query = select(MarketInsight).where(MarketInsight.slug == slug)
    existing = await db.execute(existing_query)
    if existing.scalar_one_or_none():
        raise HTTPException(
            status_code=400, detail=f"Article with slug '{slug}' already exists"
        )

    # Prepare data
    data = article_data.model_dump()
    data["slug"] = slug

    # Set published_at if publishing
    if data.get("is_published"):
        data["published_at"] = datetime.now(UTC)

    article = MarketInsight(**data)
    db.add(article)
    await db.commit()
    await db.refresh(article)

    logger.info(f"Created market insight: {article.title} (id={article.id})")

    return MarketInsightResponse.model_validate(article)


@router.patch("/{article_id}", response_model=MarketInsightResponse)
async def update_market_insight(
    article_id: UUID,
    article_data: MarketInsightUpdate,
    admin: AdminUser,
    db: AsyncSession = Depends(get_db),
) -> MarketInsightResponse:
    """
    Update an existing market insight (admin only).

    Updates published_at when first published.
    """

    query = select(MarketInsight).where(MarketInsight.id == article_id)
    result = await db.execute(query)
    article = result.scalar_one_or_none()

    if not article:
        raise HTTPException(status_code=404, detail="Article not found")

    # Update only provided fields
    update_data = article_data.model_dump(exclude_unset=True)

    # Check for duplicate slug if updating
    if "slug" in update_data and update_data["slug"] != article.slug:
        existing_query = select(MarketInsight).where(
            MarketInsight.slug == update_data["slug"]
        )
        existing = await db.execute(existing_query)
        if existing.scalar_one_or_none():
            raise HTTPException(
                status_code=400,
                detail=f"Article with slug '{update_data['slug']}' already exists",
            )

    # Set published_at when first published
    if (
        "is_published" in update_data
        and update_data["is_published"]
        and not article.is_published
    ):
        update_data["published_at"] = datetime.now(UTC)

    for field, value in update_data.items():
        setattr(article, field, value)

    await db.commit()
    await db.refresh(article)

    logger.info(f"Updated market insight: {article.title} (id={article.id})")

    return MarketInsightResponse.model_validate(article)


@router.delete("/{article_id}", status_code=204)
async def delete_market_insight(
    article_id: UUID,
    admin: AdminUser,
    db: AsyncSession = Depends(get_db),
) -> None:
    """
    Delete a market insight (admin only).
    """

    query = select(MarketInsight).where(MarketInsight.id == article_id)
    result = await db.execute(query)
    article = result.scalar_one_or_none()

    if not article:
        raise HTTPException(status_code=404, detail="Article not found")

    await db.delete(article)
    await db.commit()

    logger.info(f"Deleted market insight: {article.title} (id={article_id})")
