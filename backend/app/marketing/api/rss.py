"""RSS 2.0 feed of latest insights and market insight articles."""

import logging
from datetime import UTC, datetime
from xml.etree.ElementTree import Element, SubElement, tostring

from fastapi import APIRouter, Depends
from fastapi.responses import Response
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.models.insight import Insight
from app.models.market_insight import MarketInsight

logger = logging.getLogger(__name__)

router = APIRouter(tags=["RSS"])

SITE_URL = "https://startinsight.co"


def _rfc822(dt: datetime | None) -> str:
    """Format datetime as RFC 822 for RSS pubDate."""
    if dt is None:
        dt = datetime.now(UTC)
    return dt.strftime("%a, %d %b %Y %H:%M:%S +0000")


@router.get("/api/feed/rss", response_class=Response)
async def rss_feed(db: AsyncSession = Depends(get_db)):
    """RSS 2.0 feed of latest insights + market insight articles (20 items)."""

    # Fetch latest insights
    insights_result = await db.execute(
        select(Insight)
        .where(Insight.relevance_score >= 0.6)
        .order_by(Insight.created_at.desc())
        .limit(12)
    )
    insights = insights_result.scalars().all()

    # Fetch latest articles
    articles_result = await db.execute(
        select(MarketInsight)
        .where(MarketInsight.status == "published")
        .order_by(MarketInsight.published_at.desc())
        .limit(8)
    )
    articles = articles_result.scalars().all()

    # Build RSS XML
    rss = Element("rss", version="2.0")
    rss.set("xmlns:atom", "http://www.w3.org/2005/Atom")
    channel = SubElement(rss, "channel")

    SubElement(channel, "title").text = "StartInsight — Startup Ideas & Market Gaps"
    SubElement(channel, "link").text = SITE_URL
    SubElement(channel, "description").text = (
        "AI-discovered startup ideas scored across 8 dimensions. "
        "Data from Reddit, Product Hunt, Google Trends, and more."
    )
    SubElement(channel, "language").text = "en"
    SubElement(channel, "lastBuildDate").text = _rfc822(datetime.now(UTC))

    atom_link = SubElement(channel, "atom:link")
    atom_link.set("href", f"{SITE_URL}/api/feed/rss")
    atom_link.set("rel", "self")
    atom_link.set("type", "application/rss+xml")

    # Add insight items
    for i in insights:
        item = SubElement(channel, "item")
        title = i.title or i.proposed_solution or "Startup Idea"
        slug = i.slug or str(i.id)
        link = f"{SITE_URL}/insights/{slug}?utm_source=rss&utm_medium=feed"

        SubElement(item, "title").text = title
        SubElement(item, "link").text = link
        SubElement(item, "guid").text = link
        SubElement(item, "pubDate").text = _rfc822(i.created_at)

        desc = i.problem_statement or ""
        if len(desc) > 300:
            desc = desc[:297] + "..."
        SubElement(item, "description").text = desc
        SubElement(item, "category").text = "Startup Ideas"

    # Add article items
    for a in articles:
        item = SubElement(channel, "item")
        link = f"{SITE_URL}/market-insights/{a.slug}?utm_source=rss&utm_medium=feed"

        SubElement(item, "title").text = a.title or "Market Insight"
        SubElement(item, "link").text = link
        SubElement(item, "guid").text = link
        SubElement(item, "pubDate").text = _rfc822(a.published_at)

        desc = a.summary or ""
        if len(desc) > 300:
            desc = desc[:297] + "..."
        SubElement(item, "description").text = desc
        SubElement(item, "category").text = "Market Insights"

    xml_bytes = b'<?xml version="1.0" encoding="UTF-8"?>\n' + tostring(
        rss, encoding="unicode"
    ).encode("utf-8")

    return Response(
        content=xml_bytes,
        media_type="application/rss+xml",
        headers={"Cache-Control": "public, max-age=3600"},
    )
