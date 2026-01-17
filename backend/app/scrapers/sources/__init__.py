"""Source-specific scrapers for different data sources."""

from app.scrapers.sources.product_hunt_scraper import ProductHuntScraper
from app.scrapers.sources.reddit_scraper import RedditScraper
from app.scrapers.sources.trends_scraper import GoogleTrendsScraper

__all__ = [
    "RedditScraper",
    "ProductHuntScraper",
    "GoogleTrendsScraper",
]
