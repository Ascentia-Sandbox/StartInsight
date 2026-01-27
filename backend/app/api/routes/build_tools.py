"""Build Tools API Routes - Phase 5.2.

Endpoints for brand package and landing page generation.
"""

import logging
from uuid import UUID

from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field

from app.api.deps import get_current_user
from app.models import User
from app.services.brand_generator import (
    BrandPackage,
    generate_brand_package,
    get_default_brand_package,
)
from app.services.landing_page import (
    LandingPageTemplate,
    generate_landing_page,
    get_default_landing_page,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/build", tags=["Build Tools"])


# ============================================================
# Request/Response Schemas
# ============================================================


class BrandGenerateRequest(BaseModel):
    """Brand package generation request."""

    company_name: str = Field(..., min_length=2, max_length=100)
    idea_description: str = Field(..., min_length=50, max_length=2000)
    target_market: str = Field(..., min_length=10, max_length=500)
    industry: str = Field(..., min_length=2, max_length=100)
    brand_keywords: list[str] | None = Field(
        default=None, max_length=10, description="Optional branding keywords"
    )


class LandingPageRequest(BaseModel):
    """Landing page generation request."""

    company_name: str = Field(..., min_length=2, max_length=100)
    idea_description: str = Field(..., min_length=50, max_length=2000)
    target_market: str = Field(..., min_length=10, max_length=500)
    value_proposition: str = Field(..., min_length=20, max_length=300)
    include_pricing: bool = Field(default=True)


class BrandFromAnalysisRequest(BaseModel):
    """Generate brand from existing analysis."""

    analysis_id: UUID
    company_name: str = Field(..., min_length=2, max_length=100)
    brand_keywords: list[str] | None = Field(default=None, max_length=10)


class LandingPageFromAnalysisRequest(BaseModel):
    """Generate landing page from existing analysis."""

    analysis_id: UUID
    company_name: str = Field(..., min_length=2, max_length=100)
    include_pricing: bool = Field(default=True)


# ============================================================
# Brand Generation Endpoints
# ============================================================


@router.post("/brand", response_model=BrandPackage)
async def create_brand_package(
    request: BrandGenerateRequest,
    current_user: User = Depends(get_current_user),
) -> BrandPackage:
    """
    Generate a brand package for a startup idea.

    Requires authentication. Creates brand colors, fonts, logo concept, and voice guidelines.
    """
    try:
        brand = await generate_brand_package(
            company_name=request.company_name,
            idea_description=request.idea_description,
            target_market=request.target_market,
            industry=request.industry,
            brand_keywords=request.brand_keywords,
        )
        return brand

    except Exception as e:
        logger.error(f"Brand generation failed: {e}")
        # Return default brand as fallback
        return get_default_brand_package(request.company_name)


@router.get("/brand/default/{company_name}", response_model=BrandPackage)
async def get_default_brand(company_name: str) -> BrandPackage:
    """
    Get a default brand package template.

    Does not require authentication. Useful for testing or starting point.
    """
    return get_default_brand_package(company_name)


# ============================================================
# Landing Page Endpoints
# ============================================================


@router.post("/landing-page", response_model=LandingPageTemplate)
async def create_landing_page(
    request: LandingPageRequest,
    current_user: User = Depends(get_current_user),
) -> LandingPageTemplate:
    """
    Generate a landing page template for a startup idea.

    Requires authentication. Creates hero, features, social proof, FAQ, and SEO content.
    """
    try:
        landing_page = await generate_landing_page(
            company_name=request.company_name,
            idea_description=request.idea_description,
            target_market=request.target_market,
            value_proposition=request.value_proposition,
            include_pricing=request.include_pricing,
        )
        return landing_page

    except Exception as e:
        logger.error(f"Landing page generation failed: {e}")
        # Return default landing page as fallback
        return get_default_landing_page(request.company_name)


@router.get("/landing-page/default/{company_name}", response_model=LandingPageTemplate)
async def get_default_landing(company_name: str) -> LandingPageTemplate:
    """
    Get a default landing page template.

    Does not require authentication. Useful for testing or starting point.
    """
    return get_default_landing_page(company_name)


# ============================================================
# Generate from Existing Analysis
# ============================================================


@router.post("/brand/from-analysis", response_model=BrandPackage)
async def create_brand_from_analysis(
    request: BrandFromAnalysisRequest,
    current_user: User = Depends(get_current_user),
) -> BrandPackage:
    """
    Generate a brand package from an existing research analysis.

    Requires authentication. Uses analysis data to inform branding decisions.
    """
    # TODO: Fetch analysis from database
    # For now, return default brand
    logger.info(f"Brand from analysis {request.analysis_id} requested")
    return get_default_brand_package(request.company_name)


@router.post("/landing-page/from-analysis", response_model=LandingPageTemplate)
async def create_landing_from_analysis(
    request: LandingPageFromAnalysisRequest,
    current_user: User = Depends(get_current_user),
) -> LandingPageTemplate:
    """
    Generate a landing page from an existing research analysis.

    Requires authentication. Uses analysis data for targeted messaging.
    """
    # TODO: Fetch analysis from database
    # For now, return default landing page
    logger.info(f"Landing page from analysis {request.analysis_id} requested")
    return get_default_landing_page(request.company_name)
