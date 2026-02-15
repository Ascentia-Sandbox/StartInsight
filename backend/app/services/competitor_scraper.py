"""Competitor Scraper Service - Extract competitor data from websites"""

import logging
from datetime import UTC, datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.competitor_profile import CompetitorProfile, CompetitorSnapshot
from app.scrapers import get_scraper_client

logger = logging.getLogger(__name__)


class CompetitorData(BaseModel):
    """Structured competitor data extracted from website"""

    name: str = Field(..., description="Company name")
    url: str = Field(..., description="Website URL")
    description: str | None = Field(None, description="Brief description from homepage")
    value_proposition: str | None = Field(None, description="Main value proposition or tagline")
    target_audience: str | None = Field(None, description="Who the product is for")

    # Metrics
    pricing: dict[str, str] | None = Field(
        None,
        description="Pricing information (e.g., {'free': '$0/mo', 'pro': '$29/mo'})",
    )
    team_size: str | None = Field(None, description="Company size (e.g., '50-100 employees')")
    funding: str | None = Field(None, description="Funding raised (e.g., '$50M Series B')")
    founded_year: int | None = Field(None, description="Year company was founded")

    # Features
    features: list[str] | None = Field(None, description="List of product features")

    # Social proof
    social_proof: dict[str, Any] | None = Field(
        None,
        description="Social proof metrics (followers, testimonials, etc.)",
    )


class CompetitorScraperService:
    """
    Service to scrape competitor websites using the configured scraper client.

    Extracts structured data about competitors (pricing, features, messaging)
    and creates/updates CompetitorProfile records.

    Uses Crawl4AI ($0 cost) by default for PMF validation,
    with fallback to Firecrawl if needed.
    """

    def __init__(self):
        """Initialize competitor scraper with configured client."""
        self.client = get_scraper_client()

    async def scrape_competitor(
        self,
        url: str,
        insight_id: UUID,
        session: AsyncSession,
    ) -> CompetitorProfile:
        """
        Scrape competitor website and create/update CompetitorProfile.

        Args:
            url: Competitor website URL
            insight_id: Associated insight ID
            session: Database session

        Returns:
            CompetitorProfile object

        Raises:
            Exception: If scraping fails
        """
        logger.info(f"Scraping competitor website: {url}")

        try:
            # Use configured scraper client to extract structured data
            scrape_result = await self.client.scrape_url(url)

            # Extract content from ScrapeResult object
            markdown_content = scrape_result.content
            metadata = scrape_result.metadata

            # Extract company name from metadata or URL
            company_name = scrape_result.title.split("|")[0].strip() if scrape_result.title else ""
            if not company_name:
                company_name = url.split("//")[1].split("/")[0].replace("www.", "")

            # Extract description from meta tags
            description = metadata.get("description", "")

            # Parse competitor data from markdown content
            competitor_data = self._parse_competitor_data(
                markdown_content=markdown_content,
                html_content="",  # Not provided by scraper client
                metadata=metadata,
                url=url,
            )

            # Check if competitor profile already exists
            stmt = select(CompetitorProfile).where(
                CompetitorProfile.insight_id == insight_id,
                CompetitorProfile.url == url,
            )
            result = await session.execute(stmt)
            existing_profile = result.scalar_one_or_none()

            if existing_profile:
                # Update existing profile
                profile = await self._update_competitor_profile(
                    profile=existing_profile,
                    data=competitor_data,
                    session=session,
                )
            else:
                # Create new profile
                profile = await self._create_competitor_profile(
                    insight_id=insight_id,
                    data=competitor_data,
                    session=session,
                )

            logger.info(f"Competitor profile saved: {profile.name} (ID: {profile.id})")
            return profile

        except Exception as e:
            logger.error(f"Failed to scrape competitor {url}: {type(e).__name__} - {e}")
            # Create/update profile with error status
            stmt = select(CompetitorProfile).where(
                CompetitorProfile.insight_id == insight_id,
                CompetitorProfile.url == url,
            )
            result = await session.execute(stmt)
            existing_profile = result.scalar_one_or_none()

            if existing_profile:
                existing_profile.scrape_status = "failed"
                existing_profile.scrape_error = str(e)
                existing_profile.last_scraped_at = datetime.now(UTC)
                session.add(existing_profile)
                await session.commit()
                return existing_profile
            else:
                # Create minimal profile with error
                profile = CompetitorProfile(
                    insight_id=insight_id,
                    name=url.split("//")[1].split("/")[0].replace("www.", ""),
                    url=url,
                    scrape_status="failed",
                    scrape_error=str(e),
                    last_scraped_at=datetime.now(UTC),
                )
                session.add(profile)
                await session.commit()
                return profile

    def _parse_competitor_data(
        self,
        markdown_content: str,
        html_content: str,
        metadata: dict[str, Any],
        url: str,
    ) -> CompetitorData:
        """
        Parse competitor data from scraped content.

        Uses heuristics and keyword matching to extract:
        - Pricing information
        - Features
        - Value proposition
        - Target audience

        Args:
            markdown_content: Markdown content from Firecrawl
            html_content: HTML content from Firecrawl
            metadata: Metadata from Firecrawl
            url: Website URL

        Returns:
            Structured CompetitorData
        """
        # Extract company name
        company_name = metadata.get("title", "").split("|")[0].strip()
        if not company_name:
            company_name = url.split("//")[1].split("/")[0].replace("www.", "")

        # Extract description
        description = metadata.get("description", "")

        # Extract value proposition (first H1 or first paragraph)
        value_prop = None
        lines = markdown_content.split("\n")
        for line in lines:
            if line.startswith("# ") and len(line) > 10:
                value_prop = line.replace("# ", "").strip()
                break
            elif line.strip() and len(line) > 30 and not line.startswith("#"):
                value_prop = line.strip()
                break

        # Extract pricing (look for price indicators)
        pricing = self._extract_pricing(markdown_content)

        # Extract features (look for bullet points or feature lists)
        features = self._extract_features(markdown_content)

        # Extract target audience (look for "for [audience]" patterns)
        target_audience = self._extract_target_audience(markdown_content)

        return CompetitorData(
            name=company_name,
            url=url,
            description=description or None,
            value_proposition=value_prop,
            target_audience=target_audience,
            pricing=pricing,
            features=features,
        )

    def _extract_pricing(self, content: str) -> dict[str, str] | None:
        """Extract pricing information from content"""
        import re

        pricing = {}

        # Look for price patterns: $XX/mo, $XX/month, $XX per month
        price_pattern = r"\$(\d+(?:,\d+)?(?:\.\d{2})?)\s*(?:/|per)?\s*(mo|month|yr|year|user)"

        matches = re.finditer(price_pattern, content, re.IGNORECASE)
        for match in matches:
            amount = match.group(1)
            period = match.group(2).lower()

            # Try to find tier name nearby (within 20 characters before)
            context_start = max(0, match.start() - 50)
            context = content[context_start : match.start()]

            tier_name = "unknown"
            if "free" in context.lower():
                tier_name = "free"
            elif "pro" in context.lower() or "professional" in context.lower():
                tier_name = "pro"
            elif "enterprise" in context.lower() or "business" in context.lower():
                tier_name = "enterprise"
            elif "starter" in context.lower() or "basic" in context.lower():
                tier_name = "starter"

            # Normalize period
            if period in ["mo", "month"]:
                pricing[tier_name] = f"${amount}/mo"
            elif period in ["yr", "year"]:
                pricing[tier_name] = f"${amount}/yr"
            elif period == "user":
                pricing[tier_name] = f"${amount}/user"

        return pricing if pricing else None

    def _extract_features(self, content: str) -> list[str] | None:
        """Extract feature list from content"""
        features = []

        # Look for bullet points (- or * or •)
        lines = content.split("\n")
        for line in lines:
            stripped = line.strip()
            if stripped.startswith(("- ", "* ", "• ")) and len(stripped) > 5:
                feature = stripped[2:].strip()
                # Filter out navigation items and short text
                if len(feature) > 10 and not feature.lower().startswith(("home", "about", "contact", "blog", "pricing")):
                    features.append(feature)

        # Limit to top 10 features
        return features[:10] if features else None

    def _extract_target_audience(self, content: str) -> str | None:
        """Extract target audience from content"""
        import re

        # Look for "for [audience]" patterns
        patterns = [
            r"for\s+([a-z\s]+?)(?:\s+who|\s+that|\s+to|\.|,)",
            r"built for\s+([a-z\s]+?)(?:\s+who|\s+that|\s+to|\.|,)",
            r"designed for\s+([a-z\s]+?)(?:\s+who|\s+that|\s+to|\.|,)",
        ]

        for pattern in patterns:
            match = re.search(pattern, content.lower())
            if match:
                audience = match.group(1).strip()
                if len(audience) > 5 and len(audience) < 100:
                    return audience

        return None

    async def _create_competitor_profile(
        self,
        insight_id: UUID,
        data: CompetitorData,
        session: AsyncSession,
    ) -> CompetitorProfile:
        """Create new competitor profile"""
        profile = CompetitorProfile(
            insight_id=insight_id,
            name=data.name,
            url=data.url,
            description=data.description,
            value_proposition=data.value_proposition,
            target_audience=data.target_audience,
            metrics={
                "pricing": data.pricing or {},
                "team_size": data.team_size,
                "funding": data.funding,
                "founded_year": data.founded_year,
                "social_proof": data.social_proof or {},
            },
            features={feature: True for feature in (data.features or [])},
            last_scraped_at=datetime.now(UTC),
            scrape_status="success",
        )

        session.add(profile)
        await session.commit()
        await session.refresh(profile)

        # Create initial snapshot
        await self._create_snapshot(profile=profile, session=session)

        return profile

    async def _update_competitor_profile(
        self,
        profile: CompetitorProfile,
        data: CompetitorData,
        session: AsyncSession,
    ) -> CompetitorProfile:
        """Update existing competitor profile and create snapshot if changes detected"""
        # Detect changes
        changes = []

        if profile.description != data.description:
            changes.append({
                "field": "description",
                "old_value": profile.description,
                "new_value": data.description,
                "change_type": "description_updated",
            })

        if profile.value_proposition != data.value_proposition:
            changes.append({
                "field": "value_proposition",
                "old_value": profile.value_proposition,
                "new_value": data.value_proposition,
                "change_type": "messaging_updated",
            })

        # Check pricing changes
        old_pricing = profile.metrics.get("pricing", {}) if profile.metrics else {}
        new_pricing = data.pricing or {}
        if old_pricing != new_pricing:
            changes.append({
                "field": "pricing",
                "old_value": old_pricing,
                "new_value": new_pricing,
                "change_type": "pricing_updated",
            })

        # Update profile
        profile.description = data.description
        profile.value_proposition = data.value_proposition
        profile.target_audience = data.target_audience
        profile.metrics = {
            "pricing": data.pricing or {},
            "team_size": data.team_size,
            "funding": data.funding,
            "founded_year": data.founded_year,
            "social_proof": data.social_proof or {},
        }
        profile.features = {feature: True for feature in (data.features or [])}
        profile.last_scraped_at = datetime.now(UTC)
        profile.scrape_status = "success"
        profile.scrape_error = None

        session.add(profile)
        await session.commit()
        await session.refresh(profile)

        # Create snapshot if changes detected
        if changes:
            await self._create_snapshot(
                profile=profile,
                session=session,
                changes=changes,
            )

        return profile

    async def _create_snapshot(
        self,
        profile: CompetitorProfile,
        session: AsyncSession,
        changes: list[dict] | None = None,
    ) -> CompetitorSnapshot:
        """Create historical snapshot of competitor data"""
        snapshot = CompetitorSnapshot(
            competitor_id=profile.id,
            snapshot_data={
                "name": profile.name,
                "url": profile.url,
                "description": profile.description,
                "value_proposition": profile.value_proposition,
                "target_audience": profile.target_audience,
                "metrics": profile.metrics,
                "features": profile.features,
            },
            changes_detected=changes or [],
            scraped_at=datetime.now(UTC),
            scrape_method="firecrawl",
        )

        session.add(snapshot)
        await session.commit()
        await session.refresh(snapshot)

        return snapshot


async def scrape_competitor_batch(
    competitor_urls: list[str],
    insight_id: UUID,
    session: AsyncSession,
) -> list[CompetitorProfile]:
    """
    Scrape multiple competitors in batch.

    Args:
        competitor_urls: List of competitor website URLs
        insight_id: Associated insight ID
        session: Database session

    Returns:
        List of CompetitorProfile objects
    """
    scraper = CompetitorScraperService()
    profiles = []

    for url in competitor_urls:
        try:
            profile = await scraper.scrape_competitor(
                url=url,
                insight_id=insight_id,
                session=session,
            )
            profiles.append(profile)
        except Exception as e:
            logger.error(f"Failed to scrape competitor {url}: {e}")
            continue

    return profiles
