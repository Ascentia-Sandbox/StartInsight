"""Scrapers package for collecting data from various sources."""

import logging

from app.core.config import settings
from app.scrapers.base_scraper import BaseScraper
from app.scrapers.crawl4ai_client import Crawl4AIClient, get_crawl4ai_client
from app.scrapers.firecrawl_client import (
    FirecrawlClient,
    ScrapeResult,
    get_firecrawl_client,
)

logger = logging.getLogger(__name__)


def get_scraper_client() -> FirecrawlClient | Crawl4AIClient:
    """
    Get the configured scraper client based on PMF optimization settings.

    Returns Crawl4AI ($0 cost) for PMF validation by default,
    with fallback to Firecrawl if needed.

    Returns:
        Scraper client (Crawl4AIClient or FirecrawlClient)

    Example:
        >>> client = get_scraper_client()
        >>> result = await client.scrape_url("https://example.com")
    """
    if settings.use_crawl4ai:
        logger.debug("Using Crawl4AI client (PMF optimization mode)")
        return get_crawl4ai_client()
    else:
        logger.debug("Using Firecrawl client (production mode)")
        return get_firecrawl_client()


__all__ = [
    "BaseScraper",
    "FirecrawlClient",
    "Crawl4AIClient",
    "ScrapeResult",
    "get_firecrawl_client",
    "get_crawl4ai_client",
    "get_scraper_client",
]
