"""Tests for Twitter scraper - Phase 7.1."""

from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.scrapers.sources.twitter_scraper import TwitterScraper, analyze_tweet_sentiment


class TestAnalyzeTweetSentiment:
    """Tests for analyze_tweet_sentiment function."""

    def test_positive_sentiment(self):
        """Test positive sentiment detection."""
        text = "This is amazing! Great product, love it!"
        result = analyze_tweet_sentiment(text)
        assert result == "positive"

    def test_negative_sentiment(self):
        """Test negative sentiment detection."""
        text = "Terrible product, hate it, worst experience ever"
        result = analyze_tweet_sentiment(text)
        assert result == "negative"

    def test_neutral_sentiment(self):
        """Test neutral sentiment detection."""
        text = "The product exists and it does things"
        result = analyze_tweet_sentiment(text)
        assert result == "neutral"

    def test_sentiment_with_emojis(self):
        """Test sentiment detection with emojis."""
        text = "Great news! 🎉 🚀"
        result = analyze_tweet_sentiment(text)
        # Emojis might not affect basic sentiment analysis
        assert result in ["positive", "neutral"]


class TestTwitterScraper:
    """Tests for TwitterScraper class."""

    def test_init_without_credentials(self):
        """Test scraper initializes without credentials."""
        with patch("app.scrapers.sources.twitter_scraper.settings") as mock_settings:
            mock_settings.twitter_bearer_token = None
            mock_settings.twitter_api_key = None
            mock_settings.twitter_api_secret = None
            mock_settings.twitter_access_token = None
            mock_settings.twitter_access_secret = None
            scraper = TwitterScraper()
            assert scraper.client is None

    def test_init_with_credentials(self):
        """Test scraper initializes with credentials."""
        with patch("app.scrapers.sources.twitter_scraper.settings") as mock_settings:
            mock_settings.twitter_bearer_token = "test_token"
            mock_settings.twitter_api_key = "test_key"
            mock_settings.twitter_api_secret = "test_secret"
            mock_settings.twitter_access_token = "test_access"
            mock_settings.twitter_access_secret = "test_access_secret"
            with patch("tweepy.Client") as mock_client:
                scraper = TwitterScraper()
                # Client should be created
                mock_client.assert_called_once()

    def test_source_name(self):
        """Test scraper has correct source name."""
        with patch("app.scrapers.sources.twitter_scraper.settings") as mock_settings:
            mock_settings.twitter_bearer_token = None
            mock_settings.twitter_api_key = None
            mock_settings.twitter_api_secret = None
            mock_settings.twitter_access_token = None
            mock_settings.twitter_access_secret = None
            scraper = TwitterScraper()
            assert scraper.source_name == "twitter"

    @pytest.mark.asyncio
    async def test_search_tweets_without_client(self):
        """Test search_tweets returns empty without client."""
        with patch("app.scrapers.sources.twitter_scraper.settings") as mock_settings:
            mock_settings.twitter_bearer_token = None
            mock_settings.twitter_api_key = None
            mock_settings.twitter_api_secret = None
            mock_settings.twitter_access_token = None
            mock_settings.twitter_access_secret = None
            scraper = TwitterScraper()
            result = await scraper.search_tweets("startup ideas")
            assert result == []

    @pytest.mark.asyncio
    async def test_search_tweets_with_client(self):
        """Test search_tweets with mock client."""
        with patch("app.scrapers.sources.twitter_scraper.settings") as mock_settings:
            mock_settings.twitter_bearer_token = "test_token"
            mock_settings.twitter_api_key = "test_key"
            mock_settings.twitter_api_secret = "test_secret"
            mock_settings.twitter_access_token = "test_access"
            mock_settings.twitter_access_secret = "test_access_secret"

            # Create mock tweet data
            mock_tweet = MagicMock()
            mock_tweet.id = 123456789
            mock_tweet.text = "Excited about AI startup ideas! #startup #AI"
            mock_tweet.created_at = datetime.now()
            mock_tweet.author_id = 987654321
            mock_tweet.public_metrics = {
                "like_count": 10,
                "retweet_count": 5,
                "reply_count": 2,
            }
            mock_tweet.entities = None
            mock_tweet.lang = "en"

            mock_user = MagicMock()
            mock_user.id = 987654321
            mock_user.username = "testuser"
            mock_user.name = "Test User"
            mock_user.public_metrics = {"followers_count": 1000}

            mock_response = MagicMock()
            mock_response.data = [mock_tweet]
            mock_response.includes = {"users": [mock_user]}

            with patch("tweepy.Client") as mock_client_class:
                mock_client = MagicMock()
                mock_client.search_recent_tweets.return_value = mock_response
                mock_client_class.return_value = mock_client

                scraper = TwitterScraper()
                result = await scraper.search_tweets("startup ideas")

                assert len(result) == 1
                assert result[0].text == mock_tweet.text

    @pytest.mark.asyncio
    async def test_get_startup_discussions(self):
        """Test get_startup_discussions method."""
        with patch("app.scrapers.sources.twitter_scraper.settings") as mock_settings:
            mock_settings.twitter_bearer_token = None
            mock_settings.twitter_api_key = None
            mock_settings.twitter_api_secret = None
            mock_settings.twitter_access_token = None
            mock_settings.twitter_access_secret = None
            scraper = TwitterScraper()
            result = await scraper.get_startup_discussions()
            # Should return empty list without client
            assert result == []

    @pytest.mark.asyncio
    async def test_get_user_timeline_without_client(self):
        """Test get_user_timeline without client."""
        with patch("app.scrapers.sources.twitter_scraper.settings") as mock_settings:
            mock_settings.twitter_bearer_token = None
            mock_settings.twitter_api_key = None
            mock_settings.twitter_api_secret = None
            mock_settings.twitter_access_token = None
            mock_settings.twitter_access_secret = None
            scraper = TwitterScraper()
            result = await scraper.get_user_timeline("elonmusk")
            assert result == []


class TestTwitterScraperIntegration:
    """Integration tests for Twitter scraper (requires actual API)."""

    @pytest.mark.skip(reason="Requires actual Twitter API credentials")
    @pytest.mark.asyncio
    async def test_live_search(self):
        """Test live search with actual API."""
        scraper = TwitterScraper()
        if scraper.client:
            result = await scraper.search_tweets(
                query="startup AI",
                max_results=10,
            )
            assert len(result) <= 10
