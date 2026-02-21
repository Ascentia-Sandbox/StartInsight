"""Pydantic schemas for public content (Phase 12.2: IdeaBrowser Replication).

Includes schemas for Tools, Success Stories, Trends, and Market Insights.
"""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field, field_validator

# =============================================================================
# Tool Schemas
# =============================================================================

class ToolBase(BaseModel):
    """Base schema for Tool with common fields."""
    name: str = Field(..., min_length=1, max_length=200, description="Tool name")
    tagline: str = Field(..., min_length=1, max_length=500, description="Brief one-line description")
    description: str = Field(..., min_length=1, description="Detailed description")
    category: str = Field(..., min_length=1, max_length=100, description="Tool category")
    pricing: str = Field(..., min_length=1, max_length=200, description="Pricing model")
    website_url: str = Field(..., min_length=1, max_length=500, description="Official website URL")
    logo_url: str | None = Field(None, max_length=500, description="Logo image URL")
    affiliate_url: str | None = Field(None, max_length=500, description="Affiliate/referral URL (overrides website_url for Visit button)")


class ToolCreate(ToolBase):
    """Schema for creating a new Tool."""
    is_featured: bool = Field(default=False, description="Featured on homepage")
    sort_order: int = Field(default=0, ge=0, description="Manual sort order")


class ToolUpdate(BaseModel):
    """Schema for updating a Tool (all fields optional)."""
    name: str | None = Field(None, min_length=1, max_length=200)
    tagline: str | None = Field(None, min_length=1, max_length=500)
    description: str | None = None
    category: str | None = Field(None, min_length=1, max_length=100)
    pricing: str | None = Field(None, min_length=1, max_length=200)
    website_url: str | None = Field(None, min_length=1, max_length=500)
    logo_url: str | None = Field(None, max_length=500)
    affiliate_url: str | None = Field(None, max_length=500)
    is_featured: bool | None = None
    sort_order: int | None = Field(None, ge=0)


class ToolResponse(ToolBase):
    """Schema for Tool API response."""
    id: UUID
    is_featured: bool
    sort_order: int
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class ToolListResponse(BaseModel):
    """Schema for paginated Tool list response."""
    tools: list[ToolResponse]
    total: int
    limit: int
    offset: int


# =============================================================================
# Success Story Schemas
# =============================================================================

class SuccessStoryBase(BaseModel):
    """Base schema for SuccessStory with common fields."""
    founder_name: str = Field(..., min_length=1, max_length=200, description="Founder name")
    company_name: str = Field(..., min_length=1, max_length=200, description="Company name")
    tagline: str = Field(..., min_length=1, max_length=500, description="One-line company tagline")
    idea_summary: str = Field(..., min_length=1, description="Brief summary of the startup idea")
    journey_narrative: str = Field(..., min_length=1, description="Founder journey narrative (Markdown)")
    metrics: dict = Field(default_factory=dict, description="Key metrics (MRR, users, funding)")
    timeline: list = Field(default_factory=list, description="Timeline milestones")
    avatar_url: str | None = Field(None, max_length=500, description="Founder avatar URL")
    company_logo_url: str | None = Field(None, max_length=500, description="Company logo URL")
    source_url: str | None = Field(None, max_length=500, description="Verification / original source URL")


class SuccessStoryCreate(SuccessStoryBase):
    """Schema for creating a new SuccessStory."""
    is_featured: bool = Field(default=False, description="Featured on homepage")
    is_published: bool = Field(default=True, description="Published and visible")


class SuccessStoryUpdate(BaseModel):
    """Schema for updating a SuccessStory (all fields optional)."""
    founder_name: str | None = Field(None, min_length=1, max_length=200)
    company_name: str | None = Field(None, min_length=1, max_length=200)
    tagline: str | None = Field(None, min_length=1, max_length=500)
    idea_summary: str | None = None
    journey_narrative: str | None = None
    metrics: dict | None = None
    timeline: list | None = None
    avatar_url: str | None = Field(None, max_length=500)
    company_logo_url: str | None = Field(None, max_length=500)
    source_url: str | None = Field(None, max_length=500)
    is_featured: bool | None = None
    is_published: bool | None = None


class SuccessStoryResponse(SuccessStoryBase):
    """Schema for SuccessStory API response."""
    id: UUID
    is_featured: bool
    is_published: bool
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class SuccessStoryListResponse(BaseModel):
    """Schema for paginated SuccessStory list response."""
    stories: list[SuccessStoryResponse]
    total: int
    limit: int
    offset: int


# =============================================================================
# Trend Schemas
# =============================================================================

class TrendBase(BaseModel):
    """Base schema for Trend with common fields."""
    keyword: str = Field(..., min_length=1, max_length=200, description="Trending keyword")
    category: str = Field(..., min_length=1, max_length=100, description="Trend category")
    search_volume: int = Field(..., ge=0, description="Monthly search volume")
    growth_percentage: float = Field(..., description="Growth percentage")
    business_implications: str = Field(..., min_length=1, description="Business implications description")
    trend_data: dict | None = Field(default_factory=dict, description="Trend timeseries data")
    source: str = Field(default="Google Trends", max_length=100, description="Data source")


class TrendCreate(TrendBase):
    """Schema for creating a new Trend."""
    is_featured: bool = Field(default=False, description="Featured trend")
    is_published: bool = Field(default=True, description="Published and visible")


class TrendUpdate(BaseModel):
    """Schema for updating a Trend (all fields optional)."""
    keyword: str | None = Field(None, min_length=1, max_length=200)
    category: str | None = Field(None, min_length=1, max_length=100)
    search_volume: int | None = Field(None, ge=0)
    growth_percentage: float | None = None
    business_implications: str | None = None
    trend_data: dict | None = None
    source: str | None = Field(None, max_length=100)
    is_featured: bool | None = None
    is_published: bool | None = None


class TrendResponse(TrendBase):
    """Schema for Trend API response."""
    id: UUID
    is_featured: bool
    is_published: bool
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class TrendListResponse(BaseModel):
    """Schema for paginated Trend list response."""
    trends: list[TrendResponse]
    total: int
    limit: int
    offset: int


# =============================================================================
# Market Insight Schemas
# =============================================================================

class MarketInsightBase(BaseModel):
    """Base schema for MarketInsight with common fields."""
    title: str = Field(..., min_length=1, max_length=500, description="Article title")
    summary: str = Field(..., min_length=1, description="Brief article summary")
    content: str = Field(..., min_length=1, description="Full article content (Markdown)")
    category: str = Field(..., min_length=1, max_length=100, description="Article category")
    author_name: str = Field(..., min_length=1, max_length=200, description="Author name")
    author_avatar_url: str | None = Field(None, max_length=500, description="Author avatar URL")
    cover_image_url: str | None = Field(None, max_length=500, description="Cover image URL")
    reading_time_minutes: int = Field(default=5, ge=1, description="Estimated reading time")


class MarketInsightCreate(MarketInsightBase):
    """Schema for creating a new MarketInsight."""
    slug: str | None = Field(None, max_length=500, description="URL-friendly slug (auto-generated if not provided)")
    is_featured: bool = Field(default=False, description="Featured article")
    is_published: bool = Field(default=False, description="Published and visible")

    @field_validator("slug", mode="before")
    @classmethod
    def generate_slug(cls, v, info):
        """Auto-generate slug from title if not provided."""
        if v is None and "title" in info.data:
            import re
            title = info.data["title"]
            slug = title.lower()
            slug = re.sub(r"[^\w\s-]", "", slug)
            slug = re.sub(r"[\s_]+", "-", slug)
            slug = re.sub(r"-+", "-", slug).strip("-")
            return slug[:500]
        return v


class MarketInsightUpdate(BaseModel):
    """Schema for updating a MarketInsight (all fields optional)."""
    title: str | None = Field(None, min_length=1, max_length=500)
    slug: str | None = Field(None, max_length=500)
    summary: str | None = None
    content: str | None = None
    category: str | None = Field(None, min_length=1, max_length=100)
    author_name: str | None = Field(None, min_length=1, max_length=200)
    author_avatar_url: str | None = Field(None, max_length=500)
    cover_image_url: str | None = Field(None, max_length=500)
    reading_time_minutes: int | None = Field(None, ge=1)
    is_featured: bool | None = None
    is_published: bool | None = None


class MarketInsightResponse(MarketInsightBase):
    """Schema for MarketInsight API response."""
    id: UUID
    slug: str
    view_count: int
    is_featured: bool
    is_published: bool
    published_at: datetime | None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class MarketInsightListResponse(BaseModel):
    """Schema for paginated MarketInsight list response."""
    articles: list[MarketInsightResponse]
    total: int
    limit: int
    offset: int
