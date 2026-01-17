"""Unit tests for scrapers with mocked responses."""

import pytest
from unittest.mock import AsyncMock, Mock, patch
from pydantic import HttpUrl

from app.scrapers.firecrawl_client import ScrapeResult, FirecrawlClient
from app.scrapers.base_scraper import BaseScraper
from app.scrapers.sources.reddit_scraper import RedditScraper


class TestFirecrawlClient:
    """Test FirecrawlClient wrapper."""

    @pytest.mark.asyncio
    async def test_scrape_url_success(self):
        """Test successful scraping."""
        client = FirecrawlClient()

        # Mock the Firecrawl client response
        with patch.object(client.client, 'scrape_url') as mock_scrape:
            mock_scrape.return_value = {
                "metadata": {"title": "Test Page"},
                "markdown": "# Test Content\n\nThis is test content."
            }

            result = await client.scrape_url("https://example.com")

            assert isinstance(result, ScrapeResult)
            assert result.title == "Test Page"
            assert "Test Content" in result.content
            assert str(result.url) == "https://example.com/"

    @pytest.mark.asyncio
    async def test_scrape_url_empty_content(self):
        """Test handling of empty content."""
        client = FirecrawlClient()

        with patch.object(client.client, 'scrape_url') as mock_scrape:
            mock_scrape.return_value = {
                "metadata": {},
                "markdown": ""
            }

            result = await client.scrape_url("https://example.com")

            assert isinstance(result, ScrapeResult)
            assert result.content == ""


class TestBaseScraper:
    """Test BaseScraper abstract class."""

    def test_clean_text(self):
        """Test text cleaning utility."""
        dirty_text = "  Multiple    spaces\n\n\n\nMultiple   newlines  "
        clean = BaseScraper.clean_text(dirty_text)

        assert "Multiple spaces" in clean
        assert "\n\n\n" not in clean  # Should remove excessive newlines

    def test_truncate_content(self):
        """Test content truncation."""
        long_content = "a" * 60000
        truncated = BaseScraper.truncate_content(long_content, max_length=50000)

        assert len(truncated) <= 50100  # Allows for truncation message
        assert "[Content truncated...]" in truncated


class TestRedditScraper:
    """Test RedditScraper."""

    @pytest.mark.asyncio
    async def test_build_post_content(self):
        """Test post content building."""
        scraper = RedditScraper()

        # Mock submission
        mock_submission = Mock()
        mock_submission.title = "Test Post Title"
        mock_submission.subreddit.display_name = "startups"
        mock_submission.author = "testuser"
        mock_submission.score = 100
        mock_submission.num_comments = 50
        mock_submission.selftext = "This is the post body."
        mock_submission.comments = []

        content = scraper._build_post_content(mock_submission)

        assert "Test Post Title" in content
        assert "r/startups" in content
        assert "u/testuser" in content
        assert "100 upvotes" in content
        assert "This is the post body" in content


# Integration test markers
pytestmark = pytest.mark.asyncio
