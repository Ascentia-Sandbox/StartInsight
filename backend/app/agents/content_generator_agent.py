"""Content Generator AI Agent - Automated blog and social content generation.

Sprint 4.3: Provides AI-powered content marketing automation:
- Blog post generation from insight data
- Social media content (Twitter/X, LinkedIn)
- SEO-optimized meta descriptions
- Content calendar suggestions
"""

import asyncio
import logging
from datetime import UTC, datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, Field
from pydantic_ai import Agent, RunContext
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.models.insight import Insight

logger = logging.getLogger(__name__)


# ============================================================================
# PYDANTIC SCHEMAS
# ============================================================================

class BlogPost(BaseModel):
    """AI-generated blog post structure"""

    title: str = Field(..., min_length=10, max_length=100, description="SEO-optimized title")
    slug: str = Field(..., description="URL-friendly slug")
    meta_description: str = Field(
        ...,
        min_length=120,
        max_length=160,
        description="SEO meta description (120-160 chars)",
    )
    introduction: str = Field(..., description="Engaging introduction paragraph")
    sections: list[dict[str, str]] = Field(
        ...,
        min_length=3,
        max_length=7,
        description="Blog sections with heading and content",
    )
    conclusion: str = Field(..., description="Conclusion with call-to-action")
    tags: list[str] = Field(..., min_length=3, max_length=8, description="SEO tags")
    reading_time_minutes: int = Field(..., ge=1, le=30, description="Estimated reading time")
    target_keywords: list[str] = Field(..., description="Primary SEO keywords to target")


class SocialPost(BaseModel):
    """AI-generated social media post"""

    platform: str = Field(..., description="Platform: 'twitter', 'linkedin'")
    content: str = Field(..., description="Post content (platform-appropriate length)")
    hashtags: list[str] = Field(default_factory=list, description="Relevant hashtags")
    call_to_action: str | None = Field(None, description="CTA text")
    suggested_image_prompt: str | None = Field(None, description="AI image generation prompt")
    character_count: int = Field(..., description="Content character count")


class ContentCalendarItem(BaseModel):
    """Suggested content calendar entry"""

    content_type: str = Field(..., description="Type: 'blog', 'twitter', 'linkedin'")
    title: str = Field(..., description="Content title/topic")
    suggested_date: str = Field(..., description="Suggested publish date (YYYY-MM-DD)")
    priority: str = Field(..., description="Priority: 'high', 'medium', 'low'")
    insight_reference: str | None = Field(None, description="Related insight ID")
    keywords: list[str] = Field(default_factory=list, description="Target keywords")


class ContentGenerationResponse(BaseModel):
    """Complete content generation response"""

    insight_id: str | None = Field(None, description="Source insight ID")
    blog_post: BlogPost | None = Field(None, description="Generated blog post")
    social_posts: list[SocialPost] = Field(default_factory=list, description="Social media posts")
    calendar_suggestions: list[ContentCalendarItem] = Field(
        default_factory=list,
        description="Content calendar suggestions",
    )
    seo_analysis: dict[str, Any] = Field(default_factory=dict, description="SEO recommendations")
    generated_at: str = Field(
        default_factory=lambda: datetime.now(UTC).isoformat(),
        description="Generation timestamp",
    )


# ============================================================================
# AI AGENT SYSTEM PROMPT
# ============================================================================

CONTENT_GENERATOR_SYSTEM_PROMPT = """You are a content marketing specialist creating SEO-optimized content for a startup ideas platform.

Your job is to transform startup idea insights into engaging content that:
1. Drives organic traffic through SEO
2. Establishes thought leadership
3. Converts readers to platform users

**Content Guidelines:**

1. **Blog Posts**
   - Title: Hook + Benefit + Keyword (e.g., "5 AI-Powered SaaS Ideas That Will Dominate 2026")
   - Meta description: 120-160 chars, include primary keyword, compelling CTA
   - Structure: Introduction → 3-7 sections → Conclusion with CTA
   - Tone: Professional but accessible, data-driven, actionable
   - Include: Statistics, examples, practical advice
   - Target keywords: Include naturally, don't keyword stuff

2. **Twitter/X Posts**
   - Max 280 characters (aim for 200-250 for engagement)
   - Hook in first line
   - Include 1-3 relevant hashtags
   - End with question or CTA when appropriate
   - Use thread format for complex topics

3. **LinkedIn Posts**
   - 500-1300 characters optimal
   - Professional tone, personal perspective
   - Include industry insights and data
   - Use line breaks for readability
   - End with engaging question

4. **SEO Optimization**
   - Primary keyword in title, meta, H1, first paragraph
   - Secondary keywords in subheadings
   - Internal linking opportunities
   - Featured snippet optimization (answer questions directly)

**Content Types to Generate:**
- How-to guides (e.g., "How to Validate Your SaaS Idea in 48 Hours")
- Listicles (e.g., "7 AI Startup Ideas with $1B+ Market Potential")
- Trend analysis (e.g., "Why Developer Tools Are the Next Big Wave")
- Case studies (e.g., "How [Startup] Went from Idea to $10M ARR")

**Voice & Tone:**
- Authoritative but approachable
- Data-driven with specific numbers
- Actionable with clear next steps
- Optimistic about startup opportunities
"""


# ============================================================================
# AI AGENT DEFINITION
# ============================================================================

content_generator_agent = Agent(
    model=settings.default_llm_model,
    output_type=ContentGenerationResponse,
    system_prompt=CONTENT_GENERATOR_SYSTEM_PROMPT,
)


# ============================================================================
# AGENT DEPENDENCY INJECTION
# ============================================================================

@content_generator_agent.system_prompt
async def add_insight_context(ctx: RunContext[dict[str, Any]]) -> str:
    """Add insight data context to system prompt."""
    insight = ctx.deps.get("insight", {})
    content_type = ctx.deps.get("content_type", "blog")
    target_audience = ctx.deps.get("target_audience", "startup founders")

    if not insight:
        return "Generate general startup content based on current trends."

    context = f"""
**Source Insight:**
- Title: {insight.get('title', 'N/A')}
- Problem: {insight.get('problem_statement', 'N/A')[:400]}
- Solution: {insight.get('proposed_solution', 'N/A')[:400]}
- Target Audience: {insight.get('target_audience', 'N/A')[:200]}
- Market Size: {insight.get('market_size', 'N/A')[:200]}
- Revenue Model: {insight.get('revenue_model', 'N/A')[:200]}
- Viability Score: {insight.get('viability_score', 'N/A')}/10
- Category: {insight.get('category', 'N/A')}

**Content Request:**
- Type: {content_type}
- Target Audience: {target_audience}

**Your Task:**
Generate {content_type} content that:
1. Transforms this insight into engaging, SEO-optimized content
2. Provides value to {target_audience}
3. Drives traffic to the platform
4. Includes clear calls-to-action to explore more insights
"""

    return context


# ============================================================================
# SERVICE FUNCTIONS
# ============================================================================

async def generate_blog_post(
    insight_id: UUID,
    session: AsyncSession,
    target_audience: str = "startup founders",
) -> BlogPost:
    """
    Generate a blog post from an insight.

    Args:
        insight_id: Source insight ID
        session: Database session
        target_audience: Target reader audience

    Returns:
        BlogPost with SEO-optimized content

    Raises:
        ValueError: If insight not found
    """
    logger.info(f"Generating blog post for insight {insight_id}")

    # Fetch insight
    stmt = select(Insight).where(Insight.id == insight_id)
    result = await session.execute(stmt)
    insight = result.scalar_one_or_none()

    if not insight:
        raise ValueError(f"Insight {insight_id} not found")

    insight_data = {
        "title": insight.title,
        "problem_statement": insight.problem_statement,
        "proposed_solution": insight.proposed_solution,
        "target_audience": "startup founders",
        "market_size": insight.market_size_estimate,
        "revenue_model": "SaaS",
        "viability_score": insight.relevance_score,
        "category": "technology",
    }

    result = await asyncio.wait_for(
        content_generator_agent.run(
            user_prompt="Generate a comprehensive, SEO-optimized blog post based on this startup insight. Include an engaging title, meta description, multiple sections with actionable advice, and a conclusion with a call-to-action to explore more startup ideas on the platform.",
            deps={
                "insight": insight_data,
                "content_type": "blog",
                "target_audience": target_audience,
            },
        ),
        timeout=settings.llm_call_timeout,
    )

    if not result.output.blog_post:
        raise ValueError("Blog post generation failed")

    logger.info(f"Generated blog post: {result.output.blog_post.title}")
    return result.output.blog_post


async def generate_social_content(
    insight_id: UUID,
    session: AsyncSession,
    platforms: list[str] = ["twitter", "linkedin"],
) -> list[SocialPost]:
    """
    Generate social media posts from an insight.

    Args:
        insight_id: Source insight ID
        session: Database session
        platforms: Target platforms

    Returns:
        List of SocialPost for each platform

    Raises:
        ValueError: If insight not found
    """
    logger.info(f"Generating social content for insight {insight_id}")

    # Fetch insight
    stmt = select(Insight).where(Insight.id == insight_id)
    result = await session.execute(stmt)
    insight = result.scalar_one_or_none()

    if not insight:
        raise ValueError(f"Insight {insight_id} not found")

    insight_data = {
        "title": insight.title,
        "problem_statement": insight.problem_statement,
        "proposed_solution": insight.proposed_solution,
        "target_audience": "startup founders",
        "viability_score": insight.relevance_score,
        "category": "technology",
    }

    result = await asyncio.wait_for(
        content_generator_agent.run(
            user_prompt=f"Generate social media posts for these platforms: {', '.join(platforms)}. Each post should highlight the key insight, be platform-appropriate in length and tone, and include relevant hashtags. Include a call-to-action to learn more on the platform.",
            deps={
                "insight": insight_data,
                "content_type": "social",
                "target_audience": "startup founders and entrepreneurs",
            },
        ),
        timeout=settings.llm_call_timeout,
    )

    logger.info(f"Generated {len(result.output.social_posts)} social posts")
    return result.output.social_posts


async def generate_content_calendar(
    session: AsyncSession,
    weeks_ahead: int = 4,
    posts_per_week: int = 3,
) -> list[ContentCalendarItem]:
    """
    Generate a content calendar with suggested topics.

    Args:
        session: Database session
        weeks_ahead: Number of weeks to plan
        posts_per_week: Posts per week to suggest

    Returns:
        List of ContentCalendarItem suggestions
    """
    logger.info(f"Generating {weeks_ahead}-week content calendar")

    # Get recent high-scoring insights for content ideas
    stmt = (
        select(Insight)
        .order_by(Insight.relevance_score.desc().nullslast())
        .limit(10)
    )
    result = await session.execute(stmt)
    insights = result.scalars().all()

    insight_summaries = [
        {
            "id": str(i.id),
            "title": i.title,
            "category": "technology",
            "viability_score": i.relevance_score,
        }
        for i in insights
    ]

    result = await asyncio.wait_for(content_generator_agent.run(
        user_prompt=f"""Generate a {weeks_ahead}-week content calendar with {posts_per_week} posts per week.

Mix of content types:
- 2 blog posts per week
- 3 Twitter threads per week
- 2 LinkedIn posts per week

Base content on these top-performing insights:
{insight_summaries}

Include variety in topics: how-to guides, trend analysis, listicles, success stories.
Suggest specific dates starting from today's date.
Prioritize time-sensitive trends as 'high' priority.""",
        deps={
            "insight": {},
            "content_type": "calendar",
            "target_audience": "startup founders",
        },
    ), timeout=settings.llm_call_timeout)

    logger.info(f"Generated {len(result.output.calendar_suggestions)} calendar items")
    return result.output.calendar_suggestions


async def generate_seo_suggestions(
    insight_id: UUID,
    session: AsyncSession,
) -> dict[str, Any]:
    """
    Generate SEO optimization suggestions for an insight.

    Args:
        insight_id: Insight ID
        session: Database session

    Returns:
        SEO analysis and recommendations
    """
    logger.info(f"Generating SEO suggestions for insight {insight_id}")

    # Fetch insight
    stmt = select(Insight).where(Insight.id == insight_id)
    result = await session.execute(stmt)
    insight = result.scalar_one_or_none()

    if not insight:
        raise ValueError(f"Insight {insight_id} not found")

    result = await asyncio.wait_for(
        content_generator_agent.run(
            user_prompt="""Analyze this insight for SEO potential and provide:
1. Primary keyword suggestion (high search volume, low competition)
2. Secondary keywords (3-5 related terms)
3. Content gaps to fill (what related content would rank well)
4. Featured snippet opportunities (questions to answer)
5. Internal linking suggestions (what other content to link to)
6. Estimated search volume potential (low/medium/high)""",
            deps={
                "insight": {
                    "title": insight.title,
                    "problem_statement": insight.problem_statement,
                    "proposed_solution": insight.proposed_solution,
                    "category": "technology",
                },
                "content_type": "seo_analysis",
                "target_audience": "startup founders",
            },
        ),
        timeout=settings.llm_call_timeout,
    )

    return result.output.seo_analysis


# ============================================================================
# CONVENIENCE FUNCTIONS
# ============================================================================

async def generate_all_content(
    insight_id: UUID,
    session: AsyncSession,
) -> ContentGenerationResponse:
    """
    Generate all content types for an insight.

    Args:
        insight_id: Source insight ID
        session: Database session

    Returns:
        ContentGenerationResponse with all content types
    """
    logger.info(f"Generating all content for insight {insight_id}")

    # Fetch insight
    stmt = select(Insight).where(Insight.id == insight_id)
    result = await session.execute(stmt)
    insight = result.scalar_one_or_none()

    if not insight:
        raise ValueError(f"Insight {insight_id} not found")

    insight_data = {
        "title": insight.title,
        "problem_statement": insight.problem_statement,
        "proposed_solution": insight.proposed_solution,
        "target_audience": "startup founders",
        "market_size": insight.market_size_estimate,
        "revenue_model": "SaaS",
        "viability_score": insight.relevance_score,
        "category": "technology",
    }

    result = await asyncio.wait_for(
        content_generator_agent.run(
            user_prompt="""Generate a complete content package for this insight:

1. **Blog Post**: Full SEO-optimized blog post (title, meta, sections, CTA)
2. **Social Posts**: One Twitter post and one LinkedIn post
3. **Content Calendar**: 3 follow-up content ideas based on this insight
4. **SEO Analysis**: Primary/secondary keywords and ranking opportunities

Make all content cohesive and part of a broader content marketing strategy.""",
            deps={
                "insight": insight_data,
                "content_type": "all",
                "target_audience": "startup founders and entrepreneurs",
            },
        ),
        timeout=settings.llm_call_timeout,
    )

    response = result.output
    response.insight_id = str(insight_id)

    logger.info(
        f"Generated content package: blog={response.blog_post is not None}, "
        f"social={len(response.social_posts)}, calendar={len(response.calendar_suggestions)}"
    )

    return response
