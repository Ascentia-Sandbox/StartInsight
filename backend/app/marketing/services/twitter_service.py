"""Twitter/X posting service — uses Tweepy v2 Client with OAuth 1.0a."""

import logging

import tweepy

from app.core.config import settings

logger = logging.getLogger(__name__)


def _get_client() -> tweepy.Client | None:
    """Build Tweepy v2 Client for posting. Returns None if creds missing."""
    if not all(
        [
            settings.twitter_api_key,
            settings.twitter_api_secret,
            settings.twitter_access_token,
            settings.twitter_access_secret,
        ]
    ):
        logger.warning("Twitter credentials not configured — skipping")
        return None

    return tweepy.Client(
        consumer_key=settings.twitter_api_key,
        consumer_secret=settings.twitter_api_secret,
        access_token=settings.twitter_access_token,
        access_token_secret=settings.twitter_access_secret,
    )


async def post_tweet(content: str) -> dict:
    """Post a tweet. Returns {"id": tweet_id, "text": content} or raises."""
    client = _get_client()
    if client is None:
        raise RuntimeError("Twitter credentials not configured")

    response = client.create_tweet(text=content)

    tweet_id = str(response.data["id"])
    logger.info(f"Tweet posted: {tweet_id}")
    return {"id": tweet_id, "text": content}
