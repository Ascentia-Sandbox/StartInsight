"""Programmatic SEO endpoints — topic-based insight pages + category listing.

GET /api/explore/categories — list all SEO categories (for sitemap)
GET /api/explore/{slug}    — insights matching a topic slug's keywords
GET /api/widgets/trending   — embeddable widget (top 5 trending ideas, CORS: *)
"""

import logging

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import JSONResponse
from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.marketing.services.seo_categories import get_all_categories, get_category
from app.models.insight import Insight

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api", tags=["Explore & Widgets"])


@router.get("/explore/categories")
async def list_categories():
    """List all SEO categories for sitemap and navigation."""
    return [
        {
            "slug": c.slug,
            "title": c.title,
            "description": c.description,
            "meta_description": c.meta_description,
        }
        for c in get_all_categories()
    ]


@router.get("/explore/{slug}")
async def get_topic_insights(
    slug: str,
    limit: int = Query(20, le=50),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db),
):
    """Return insights matching a topic slug's keywords for programmatic SEO pages."""
    category = get_category(slug)
    if not category:
        raise HTTPException(status_code=404, detail=f"Category '{slug}' not found")

    # Build OR filter matching any keyword in title, problem_statement, or proposed_solution
    keyword_filters = []
    for kw in category.keywords:
        pattern = f"%{kw}%"
        keyword_filters.append(Insight.title.ilike(pattern))
        keyword_filters.append(Insight.problem_statement.ilike(pattern))
        keyword_filters.append(Insight.proposed_solution.ilike(pattern))

    result = await db.execute(
        select(Insight)
        .where(
            Insight.relevance_score >= 0.5,
            or_(*keyword_filters),
        )
        .order_by(Insight.relevance_score.desc())
        .offset(offset)
        .limit(limit)
    )
    insights = result.scalars().all()

    return {
        "category": {
            "slug": category.slug,
            "title": category.title,
            "description": category.description,
            "meta_description": category.meta_description,
        },
        "insights": [
            {
                "id": str(i.id),
                "slug": i.slug,
                "title": i.title,
                "problem_statement": i.problem_statement,
                "proposed_solution": i.proposed_solution,
                "market_size_estimate": i.market_size_estimate,
                "relevance_score": i.relevance_score,
                "opportunity_score": i.opportunity_score,
                "created_at": i.created_at.isoformat() if i.created_at else None,
            }
            for i in insights
        ],
        "total": len(insights),
        "limit": limit,
        "offset": offset,
    }


@router.get("/widgets/trending")
async def widget_trending_ideas(
    limit: int = Query(5, le=10),
    db: AsyncSession = Depends(get_db),
):
    """Embeddable widget endpoint — top trending ideas as JSON. CORS: allow all origins."""
    result = await db.execute(
        select(Insight)
        .where(Insight.relevance_score >= 0.7)
        .order_by(Insight.created_at.desc())
        .limit(limit)
    )
    insights = result.scalars().all()

    data = [
        {
            "title": i.title or i.proposed_solution,
            "score": round(i.relevance_score, 2) if i.relevance_score else None,
            "url": f"https://startinsight.co/insights/{i.slug or i.id}",
        }
        for i in insights
    ]

    return JSONResponse(
        content={"ideas": data, "source": "startinsight.co"},
        headers={
            "Access-Control-Allow-Origin": "*",
            "Cache-Control": "public, max-age=300",
        },
    )
