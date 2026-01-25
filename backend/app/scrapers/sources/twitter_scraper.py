"""Twitter/X Scraper - Phase 7.1.

Scrapes startup-related discussions from Twitter/X using Tweepy.
Supports:
- Keyword search
- User timeline scraping
- Hashtag tracking
- Sentiment analysis
"""

import logging
from datetime import datetime, timedelta
from typing import Any

from pydantic import BaseModel, Field

from app.core.config import settings
from app.scrapers.base_scraper import BaseScraper

logger = logging.getLogger(__name__)


# ============================================================
# Tweet Schema
# ============================================================


class TweetData(BaseModel):
    """Structured tweet data."""

    id: str
    text: str
    author_id: str
    author_username: str
    author_name: str | None = None
    author_followers: int = 0
    created_at: str
    retweet_count: int = 0
    like_count: int = 0
    reply_count: int = 0
    quote_count: int = 0
    hashtags: list[str] = Field(default_factory=list)
    mentions: list[str] = Field(default_factory=list)
    urls: list[str] = Field(default_factory=list)
    lang: str | None = None
    sentiment: str | None = None  # positive, neutral, negative


# ============================================================
# Twitter Scraper
# ============================================================


class TwitterScraper(BaseScraper):
    """Twitter/X scraper using Tweepy v2 API."""

    def __init__(self):
        super().__init__(source_name="twitter")
        self.client = self._get_client()

    def _get_client(self):
        """Get Tweepy client instance."""
        try:
            import tweepy

            if not settings.twitter_bearer_token:
                logger.warning("Twitter bearer token not configured")
                return None

            return tweepy.Client(
                bearer_token=settings.twitter_bearer_token,
                consumer_key=settings.twitter_api_key,
                consumer_secret=settings.twitter_api_secret,
                access_token=settings.twitter_access_token,
                access_token_secret=settings.twitter_access_secret,
                wait_on_rate_limit=True,
            )
        except ImportError:
            logger.warning("Tweepy not installed")
            return None
        except Exception as e:
            logger.error(f"Failed to create Tweepy client: {e}")
            return None

    async def search_tweets(
        self,
        query: str,
        max_results: int = 100,
        start_time: datetime | None = None,
        end_time: datetime | None = None,
    ) -> list[TweetData]:
        """
        Search for tweets matching a query.

        Args:
            query: Search query (supports Twitter query syntax)
            max_results: Maximum tweets to return (10-100)
            start_time: Start of search window
            end_time: End of search window

        Returns:
            List of TweetData objects
        """
        if not self.client:
            logger.warning("Twitter client not available")
            return []

        try:
            # Default to last 7 days
            if not start_time:
                start_time = datetime.utcnow() - timedelta(days=7)
            if not end_time:
                end_time = datetime.utcnow()

            # Build query with startup-related filters
            full_query = f"{query} -is:retweet lang:en"

            response = self.client.search_recent_tweets(
                query=full_query,
                max_results=min(max_results, 100),
                start_time=start_time,
                end_time=end_time,
                tweet_fields=[
                    "created_at",
                    "public_metrics",
                    "entities",
                    "lang",
                    "author_id",
                ],
                user_fields=["username", "name", "public_metrics"],
                expansions=["author_id"],
            )

            if not response.data:
                return []

            # Build user lookup
            users = {}
            if response.includes and "users" in response.includes:
                for user in response.includes["users"]:
                    users[user.id] = user

            tweets = []
            for tweet in response.data:
                user = users.get(tweet.author_id)
                tweet_data = self._parse_tweet(tweet, user)
                tweets.append(tweet_data)

            logger.info(f"Fetched {len(tweets)} tweets for query: {query[:50]}")
            return tweets

        except Exception as e:
            logger.error(f"Twitter search failed: {e}")
            return []

    async def get_startup_discussions(
        self,
        max_results: int = 50,
    ) -> list[TweetData]:
        """
        Get tweets about startups and entrepreneurship.

        Uses predefined startup-related queries.

        Args:
            max_results: Maximum tweets per query

        Returns:
            Combined list of tweets
        """
        queries = [
            '"startup idea" OR "side project" OR "building in public"',
            '"looking for" AND ("saas" OR "app" OR "tool")',
            '"i wish there was" OR "someone should build"',
            '#buildinpublic OR #indiehacker OR #startups',
        ]

        all_tweets = []
        for query in queries:
            tweets = await self.search_tweets(query, max_results=max_results // len(queries))
            all_tweets.extend(tweets)

        # Deduplicate by ID
        seen = set()
        unique_tweets = []
        for tweet in all_tweets:
            if tweet.id not in seen:
                seen.add(tweet.id)
                unique_tweets.append(tweet)

        return unique_tweets

    async def get_user_timeline(
        self,
        username: str,
        max_results: int = 20,
    ) -> list[TweetData]:
        """
        Get recent tweets from a specific user.

        Args:
            username: Twitter username (without @)
            max_results: Maximum tweets to return

        Returns:
            List of TweetData objects
        """
        if not self.client:
            return []

        try:
            # Get user ID first
            user_response = self.client.get_user(
                username=username,
                user_fields=["public_metrics"],
            )

            if not user_response.data:
                logger.warning(f"User not found: {username}")
                return []

            user = user_response.data

            # Get timeline
            timeline = self.client.get_users_tweets(
                id=user.id,
                max_results=min(max_results, 100),
                tweet_fields=[
                    "created_at",
                    "public_metrics",
                    "entities",
                    "lang",
                ],
                exclude=["retweets", "replies"],
            )

            if not timeline.data:
                return []

            tweets = []
            for tweet in timeline.data:
                tweet_data = self._parse_tweet(tweet, user)
                tweets.append(tweet_data)

            return tweets

        except Exception as e:
            logger.error(f"Failed to get timeline for {username}: {e}")
            return []

    def _parse_tweet(self, tweet, user=None) -> TweetData:
        """Parse tweet object into TweetData."""
        # Extract entities
        hashtags = []
        mentions = []
        urls = []

        if hasattr(tweet, "entities") and tweet.entities:
            if "hashtags" in tweet.entities:
                hashtags = [h["tag"] for h in tweet.entities["hashtags"]]
            if "mentions" in tweet.entities:
                mentions = [m["username"] for m in tweet.entities["mentions"]]
            if "urls" in tweet.entities:
                urls = [u["expanded_url"] for u in tweet.entities["urls"]]

        # Extract metrics
        metrics = getattr(tweet, "public_metrics", {}) or {}

        # User info
        author_username = ""
        author_name = None
        author_followers = 0

        if user:
            author_username = user.username
            author_name = user.name
            if hasattr(user, "public_metrics") and user.public_metrics:
                author_followers = user.public_metrics.get("followers_count", 0)

        return TweetData(
            id=str(tweet.id),
            text=tweet.text,
            author_id=str(tweet.author_id),
            author_username=author_username,
            author_name=author_name,
            author_followers=author_followers,
            created_at=tweet.created_at.isoformat() if tweet.created_at else "",
            retweet_count=metrics.get("retweet_count", 0),
            like_count=metrics.get("like_count", 0),
            reply_count=metrics.get("reply_count", 0),
            quote_count=metrics.get("quote_count", 0),
            hashtags=hashtags,
            mentions=mentions,
            urls=urls,
            lang=getattr(tweet, "lang", None),
            sentiment=None,  # Set by sentiment analyzer
        )

    async def scrape(self, **kwargs) -> list[dict[str, Any]]:
        """
        Scrape Twitter for startup signals.

        Implements BaseScraper interface.

        Returns:
            List of raw signal dictionaries
        """
        tweets = await self.get_startup_discussions(
            max_results=kwargs.get("max_results", 50)
        )

        signals = []
        for tweet in tweets:
            # Filter by engagement threshold
            engagement = tweet.like_count + tweet.retweet_count + tweet.reply_count
            if engagement < 5:  # Minimum engagement threshold
                continue

            signals.append({
                "source": "twitter",
                "source_url": f"https://twitter.com/{tweet.author_username}/status/{tweet.id}",
                "title": f"@{tweet.author_username}: {tweet.text[:50]}...",
                "content": tweet.text,
                "author": tweet.author_username,
                "metadata": {
                    "tweet_id": tweet.id,
                    "likes": tweet.like_count,
                    "retweets": tweet.retweet_count,
                    "replies": tweet.reply_count,
                    "author_followers": tweet.author_followers,
                    "hashtags": tweet.hashtags,
                    "created_at": tweet.created_at,
                },
            })

        logger.info(f"Twitter scraper found {len(signals)} signals")
        return signals


# ============================================================
# Sentiment Analysis
# ============================================================


def analyze_tweet_sentiment(text: str) -> str:
    """
    Simple rule-based sentiment analysis.

    In production, use a proper NLP model.

    Args:
        text: Tweet text

    Returns:
        "positive", "neutral", or "negative"
    """
    text_lower = text.lower()

    positive_keywords = [
        "love", "great", "awesome", "amazing", "excited",
        "successful", "growth", "launched", "shipped", "milestone",
        "profit", "revenue", "customers", "users", "growing",
    ]

    negative_keywords = [
        "hate", "terrible", "awful", "struggling", "failed",
        "shutdown", "pivot", "layoff", "burned", "lost",
        "problem", "issue", "bug", "broken", "frustrated",
    ]

    positive_count = sum(1 for word in positive_keywords if word in text_lower)
    negative_count = sum(1 for word in negative_keywords if word in text_lower)

    if positive_count > negative_count:
        return "positive"
    elif negative_count > positive_count:
        return "negative"
    return "neutral"
