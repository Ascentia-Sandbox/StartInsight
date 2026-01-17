"""Scrapers package for collecting data from various sources."""

from app.scrapers.base_scraper import BaseScraper
from app.scrapers.firecrawl_client import (
    FirecrawlClient,
    ScrapeResult,
    get_firecrawl_client,
)

__all__ = [
    "BaseScraper",
    "FirecrawlClient",
    "ScrapeResult",
    "get_firecrawl_client",
]
