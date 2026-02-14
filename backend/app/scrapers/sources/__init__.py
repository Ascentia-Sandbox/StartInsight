"""Source-specific scrapers for different data sources."""

from app.scrapers.sources.hackernews_scraper import HackerNewsScraper
from app.scrapers.sources.product_hunt_scraper import ProductHuntScraper
from app.scrapers.sources.reddit_scraper import RedditScraper
from app.scrapers.sources.trends_scraper import GoogleTrendsScraper
from app.scrapers.sources.twitter_scraper import TwitterScraper

__all__ = [
    "RedditScraper",
    "ProductHuntScraper",
    "GoogleTrendsScraper",
    "TwitterScraper",
    "HackerNewsScraper",
]
