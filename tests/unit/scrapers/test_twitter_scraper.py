"""Tests for Twitter scraper.

Tests:
1. ScrapeResult interface compliance
2. Tweet formatting
3. Sentiment analysis
4. Engagement filtering
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from pydantic import HttpUrl

from app.scrapers.sources.twitter_scraper import (
    TwitterScraper,
    TweetData,
    analyze_tweet_sentiment,
)
from app.scrapers.firecrawl_client import ScrapeResult


class TestTwitterScraper:
    """Test TwitterScraper class."""

    @pytest.fixture
    def scraper(self):
        """Create Twitter scraper instance with mocked client."""
        with patch.object(TwitterScraper, '__init__', lambda x: None):
            scraper = TwitterScraper.__new__(TwitterScraper)
            scraper.source_name = "twitter"
            scraper.client = MagicMock()
            return scraper

    @pytest.fixture
    def sample_tweet(self):
        """Create sample tweet data."""
        return TweetData(
            id="123456789",
            text="Building a new SaaS product. #buildinpublic #startups",
            author_id="987654321",
            author_username="founder",
            author_name="Test Founder",
            author_followers=5000,
            created_at="2024-01-15T10:30:00Z",
            retweet_count=50,
            like_count=200,
            reply_count=25,
            quote_count=10,
            hashtags=["buildinpublic", "startups"],
            mentions=[],
            urls=[],
            lang="en",
            sentiment=None,
        )

    @pytest.mark.asyncio
    async def test_scrape_returns_scrape_result_list(self, scraper, sample_tweet):
        """Test that scrape returns list[ScrapeResult]."""
        with patch.object(scraper, 'get_startup_discussions', new_callable=AsyncMock) as mock:
            mock.return_value = [sample_tweet]

            results = await scraper.scrape()

            assert isinstance(results, list)
            assert len(results) == 1
            assert isinstance(results[0], ScrapeResult)

    @pytest.mark.asyncio
    async def test_scrape_returns_empty_without_client(self, scraper):
        """Test that scrape returns empty list without client."""
        scraper.client = None
        results = await scraper.scrape()
        assert results == []

    @pytest.mark.asyncio
    async def test_scrape_filters_low_engagement(self, scraper):
        """Test that low engagement tweets are filtered."""
        low_engagement_tweet = TweetData(
            id="111111",
            text="Test tweet",
            author_id="222222",
            author_username="test",
            created_at="2024-01-15T10:00:00Z",
            retweet_count=0,
            like_count=2,
            reply_count=0,
        )

        with patch.object(scraper, 'get_startup_discussions', new_callable=AsyncMock) as mock:
            mock.return_value = [low_engagement_tweet]

            results = await scraper.scrape(min_engagement=5)

            assert len(results) == 0

    @pytest.mark.asyncio
    async def test_scrape_includes_high_engagement(self, scraper, sample_tweet):
        """Test that high engagement tweets are included."""
        with patch.object(scraper, 'get_startup_discussions', new_callable=AsyncMock) as mock:
            mock.return_value = [sample_tweet]

            results = await scraper.scrape(min_engagement=5)

            assert len(results) == 1

    @pytest.mark.asyncio
    async def test_scrape_includes_correct_metadata(self, scraper, sample_tweet):
        """Test that ScrapeResult has correct metadata."""
        with patch.object(scraper, 'get_startup_discussions', new_callable=AsyncMock) as mock:
            mock.return_value = [sample_tweet]

            results = await scraper.scrape()
            result = results[0]

            assert result.metadata["source"] == "twitter"
            assert result.metadata["tweet_id"] == "123456789"
            assert result.metadata["author_username"] == "founder"
            assert result.metadata["like_count"] == 200
            assert result.metadata["hashtags"] == ["buildinpublic", "startups"]

    @pytest.mark.asyncio
    async def test_scrape_generates_correct_url(self, scraper, sample_tweet):
        """Test that tweet URL is correctly generated."""
        with patch.object(scraper, 'get_startup_discussions', new_callable=AsyncMock) as mock:
            mock.return_value = [sample_tweet]

            results = await scraper.scrape()
            result = results[0]

            expected_url = "https://twitter.com/founder/status/123456789"
            assert str(result.url) == expected_url

    def test_format_tweet_markdown(self, scraper, sample_tweet):
        """Test tweet markdown formatting."""
        content = scraper._format_tweet_markdown(sample_tweet)

        assert "# Tweet by @founder" in content
        assert sample_tweet.text in content
        assert "**Likes:** 200" in content
        assert "**Retweets:** 50" in content
        assert "**Followers:** 5,000" in content
        assert "#buildinpublic" in content

    def test_format_tweet_markdown_without_name(self, scraper):
        """Test tweet formatting without author name."""
        tweet = TweetData(
            id="123",
            text="Test",
            author_id="456",
            author_username="test",
            author_name=None,
            created_at="2024-01-15T10:00:00Z",
        )

        content = scraper._format_tweet_markdown(tweet)

        assert "**Name:**" not in content


class TestAnalyzeTweetSentiment:
    """Test sentiment analysis function."""

    def test_positive_sentiment(self):
        """Test positive sentiment detection."""
        positive_texts = [
            "Just launched my product and it's amazing!",
            "Love the growth we're seeing",
            "Excited about our new milestone",
            "Successful launch, feeling great",
        ]

        for text in positive_texts:
            sentiment = analyze_tweet_sentiment(text)
            assert sentiment == "positive", f"Expected positive for: {text}"

    def test_negative_sentiment(self):
        """Test negative sentiment detection."""
        negative_texts = [
            "Struggling with this problem",
            "We had to pivot after failing",
            "Frustrated with the bugs",
            "Lost customers this month",
        ]

        for text in negative_texts:
            sentiment = analyze_tweet_sentiment(text)
            assert sentiment == "negative", f"Expected negative for: {text}"

    def test_neutral_sentiment(self):
        """Test neutral sentiment detection."""
        neutral_texts = [
            "Working on a new feature today",
            "Released version 2.0",
            "Meeting with investors tomorrow",
        ]

        for text in neutral_texts:
            sentiment = analyze_tweet_sentiment(text)
            assert sentiment == "neutral", f"Expected neutral for: {text}"

    def test_case_insensitive(self):
        """Test that sentiment analysis is case insensitive."""
        assert analyze_tweet_sentiment("LOVE this product") == "positive"
        assert analyze_tweet_sentiment("HATE this bug") == "negative"

    def test_mixed_sentiment_dominant_positive(self):
        """Test mixed sentiment with more positive words."""
        text = "Despite some issues, I love this amazing tool"
        sentiment = analyze_tweet_sentiment(text)
        assert sentiment == "positive"

    def test_mixed_sentiment_dominant_negative(self):
        """Test mixed sentiment with more negative words."""
        text = "I hate the terrible bugs even though growth looks good"
        sentiment = analyze_tweet_sentiment(text)
        assert sentiment == "negative"


class TestTweetData:
    """Test TweetData model."""

    def test_default_values(self):
        """Test TweetData default values."""
        tweet = TweetData(
            id="123",
            text="Test tweet",
            author_id="456",
            author_username="test",
            created_at="2024-01-15T10:00:00Z",
        )

        assert tweet.retweet_count == 0
        assert tweet.like_count == 0
        assert tweet.reply_count == 0
        assert tweet.quote_count == 0
        assert tweet.hashtags == []
        assert tweet.mentions == []
        assert tweet.urls == []
        assert tweet.author_followers == 0
        assert tweet.sentiment is None

    def test_full_tweet_data(self):
        """Test TweetData with all fields."""
        tweet = TweetData(
            id="123",
            text="Test tweet #test",
            author_id="456",
            author_username="testuser",
            author_name="Test User",
            author_followers=1000,
            created_at="2024-01-15T10:00:00Z",
            retweet_count=10,
            like_count=50,
            reply_count=5,
            quote_count=2,
            hashtags=["test"],
            mentions=["someone"],
            urls=["https://example.com"],
            lang="en",
            sentiment="positive",
        )

        assert tweet.author_name == "Test User"
        assert tweet.author_followers == 1000
        assert len(tweet.hashtags) == 1
        assert tweet.sentiment == "positive"
