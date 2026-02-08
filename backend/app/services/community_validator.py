"""Community signal verification service.

This module validates that community signals reference real communities
with accurate member counts, preventing LLM hallucination of fake
subreddits, Facebook groups, etc.

Uses PRAW for Reddit validation. Future: Add Facebook, YouTube validation.
"""

import asyncio
import logging
from dataclasses import dataclass
from functools import lru_cache

import praw
from praw.exceptions import InvalidURL, PRAWException
from prawcore.exceptions import (
    Forbidden,
    NotFound,
    Redirect,
    ResponseException,
    ServerError,
)

from app.core.config import settings

logger = logging.getLogger(__name__)


@dataclass
class SubredditValidationResult:
    """Result of subreddit validation."""

    subreddit_name: str
    is_valid: bool
    subscriber_count: int
    error: str | None = None


@dataclass
class CommunitySignalData:
    """Community signal data structure."""

    platform: str
    communities: str
    members: str
    score: int
    top_community: str


class CommunityValidator:
    """
    Validates that community signals reference real communities.

    Currently supports:
    - Reddit (via PRAW)

    Future support planned:
    - Facebook Groups (via Graph API)
    - YouTube Channels (via YouTube Data API)
    - LinkedIn Groups
    - Discord Servers
    """

    def __init__(self):
        """Initialize validator with Reddit client."""
        self._reddit: praw.Reddit | None = None
        self._cache: dict[str, SubredditValidationResult] = {}
        self._init_reddit()

    def _init_reddit(self) -> None:
        """Initialize Reddit client if credentials are available."""
        if not settings.reddit_client_id or not settings.reddit_client_secret:
            logger.warning(
                "Reddit credentials not configured. "
                "Subreddit validation will be skipped."
            )
            return

        try:
            self._reddit = praw.Reddit(
                client_id=settings.reddit_client_id,
                client_secret=settings.reddit_client_secret,
                user_agent=settings.reddit_user_agent,
            )
            logger.info("Community validator initialized with Reddit client")
        except Exception as e:
            logger.error(f"Failed to initialize Reddit client: {e}")
            self._reddit = None

    def _normalize_subreddit_name(self, name: str) -> str:
        """
        Normalize subreddit name by removing 'r/' prefix and whitespace.

        Args:
            name: Subreddit name (e.g., "r/startups", "/r/startups", "startups")

        Returns:
            Normalized name without prefix (e.g., "startups")
        """
        name = name.strip()
        # Remove various prefixes
        for prefix in ["r/", "/r/", "reddit.com/r/", "www.reddit.com/r/"]:
            if name.lower().startswith(prefix):
                name = name[len(prefix):]
        return name.strip("/")

    def validate_subreddit_sync(self, subreddit_name: str) -> SubredditValidationResult:
        """
        Synchronously validate that a subreddit exists and get subscriber count.

        Args:
            subreddit_name: Subreddit name (with or without r/ prefix)

        Returns:
            SubredditValidationResult with validation status and subscriber count
        """
        normalized_name = self._normalize_subreddit_name(subreddit_name)

        # Check cache first
        if normalized_name in self._cache:
            logger.debug(f"Cache hit for subreddit: r/{normalized_name}")
            return self._cache[normalized_name]

        if not self._reddit:
            result = SubredditValidationResult(
                subreddit_name=normalized_name,
                is_valid=False,
                subscriber_count=0,
                error="Reddit client not initialized",
            )
            return result

        try:
            subreddit = self._reddit.subreddit(normalized_name)
            # Accessing subscribers triggers API call
            subscribers = subreddit.subscribers

            if subscribers is None:
                result = SubredditValidationResult(
                    subreddit_name=normalized_name,
                    is_valid=False,
                    subscriber_count=0,
                    error="Subreddit has no subscriber count (may be private or banned)",
                )
            elif subscribers == 0:
                # Subreddit exists but has 0 subscribers (very unusual)
                result = SubredditValidationResult(
                    subreddit_name=normalized_name,
                    is_valid=True,
                    subscriber_count=0,
                    error=None,
                )
            else:
                result = SubredditValidationResult(
                    subreddit_name=normalized_name,
                    is_valid=True,
                    subscriber_count=subscribers,
                    error=None,
                )

            logger.info(
                f"Validated subreddit r/{normalized_name}: "
                f"valid={result.is_valid}, subscribers={result.subscriber_count}"
            )

        except NotFound:
            result = SubredditValidationResult(
                subreddit_name=normalized_name,
                is_valid=False,
                subscriber_count=0,
                error="Subreddit not found",
            )
            logger.debug(f"Subreddit not found: r/{normalized_name}")

        except Forbidden:
            result = SubredditValidationResult(
                subreddit_name=normalized_name,
                is_valid=False,
                subscriber_count=0,
                error="Subreddit is private or quarantined",
            )
            logger.debug(f"Subreddit forbidden: r/{normalized_name}")

        except Redirect:
            result = SubredditValidationResult(
                subreddit_name=normalized_name,
                is_valid=False,
                subscriber_count=0,
                error="Subreddit name redirects (may be misspelled)",
            )
            logger.debug(f"Subreddit redirects: r/{normalized_name}")

        except (InvalidURL, ResponseException, ServerError) as e:
            result = SubredditValidationResult(
                subreddit_name=normalized_name,
                is_valid=False,
                subscriber_count=0,
                error=f"Reddit API error: {type(e).__name__}",
            )
            logger.warning(f"Reddit API error for r/{normalized_name}: {e}")

        except PRAWException as e:
            result = SubredditValidationResult(
                subreddit_name=normalized_name,
                is_valid=False,
                subscriber_count=0,
                error=f"PRAW error: {str(e)}",
            )
            logger.error(f"PRAW error validating r/{normalized_name}: {e}")

        except Exception as e:
            result = SubredditValidationResult(
                subreddit_name=normalized_name,
                is_valid=False,
                subscriber_count=0,
                error=f"Unexpected error: {type(e).__name__}",
            )
            logger.error(f"Unexpected error validating r/{normalized_name}: {e}")

        # Cache result
        self._cache[normalized_name] = result
        return result

    async def validate_subreddit(
        self, subreddit_name: str
    ) -> SubredditValidationResult:
        """
        Async wrapper for subreddit validation.

        PRAW is synchronous, so this runs the validation in a thread pool.

        Args:
            subreddit_name: Subreddit name to validate

        Returns:
            SubredditValidationResult with validation status
        """
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            None, self.validate_subreddit_sync, subreddit_name
        )

    async def validate_community_signal(
        self, signal: CommunitySignalData
    ) -> tuple[CommunitySignalData, bool]:
        """
        Validate a single community signal and update with real data.

        Args:
            signal: Community signal data to validate

        Returns:
            Tuple of (updated signal, is_valid)
        """
        if signal.platform == "Reddit":
            result = await self.validate_subreddit(signal.top_community)

            if result.is_valid:
                # Update member count with real data
                signal.members = self._format_subscriber_count(result.subscriber_count)
                return (signal, True)
            else:
                logger.warning(
                    f"Invalid subreddit in community signal: {signal.top_community} "
                    f"({result.error})"
                )
                return (signal, False)

        # For non-Reddit platforms, accept as-is for now
        # TODO: Add Facebook, YouTube validation
        logger.debug(
            f"Skipping validation for {signal.platform} platform "
            f"(not yet supported)"
        )
        return (signal, True)

    async def validate_community_signals(
        self,
        signals: list[dict],
        min_valid_signals: int = 2,
    ) -> tuple[list[dict], int, int]:
        """
        Validate all community signals and return only valid ones.

        Args:
            signals: List of community signal dictionaries
            min_valid_signals: Minimum number of valid signals required

        Returns:
            Tuple of (validated_signals, valid_count, invalid_count)
        """
        if not signals:
            return ([], 0, 0)

        validated = []
        valid_count = 0
        invalid_count = 0

        for signal_dict in signals:
            signal = CommunitySignalData(
                platform=signal_dict.get("platform", "Other"),
                communities=signal_dict.get("communities", ""),
                members=signal_dict.get("members", ""),
                score=signal_dict.get("score", 5),
                top_community=signal_dict.get("top_community", ""),
            )

            updated_signal, is_valid = await self.validate_community_signal(signal)

            if is_valid:
                validated.append({
                    "platform": updated_signal.platform,
                    "communities": updated_signal.communities,
                    "members": updated_signal.members,
                    "score": updated_signal.score,
                    "top_community": updated_signal.top_community,
                })
                valid_count += 1
            else:
                invalid_count += 1

        logger.info(
            f"Community signal validation: {valid_count} valid, "
            f"{invalid_count} invalid out of {len(signals)} total"
        )

        if valid_count < min_valid_signals:
            logger.warning(
                f"Insufficient valid community signals: {valid_count} "
                f"(minimum required: {min_valid_signals})"
            )

        return (validated, valid_count, invalid_count)

    @staticmethod
    def _format_subscriber_count(count: int) -> str:
        """
        Format subscriber count in human-readable format.

        Args:
            count: Raw subscriber count

        Returns:
            Formatted string (e.g., "2.5M+ members", "150K+ members")
        """
        if count >= 1_000_000:
            return f"{count / 1_000_000:.1f}M+ members"
        elif count >= 1_000:
            return f"{count / 1_000:.1f}K+ members"
        else:
            return f"{count:,} members"

    def clear_cache(self) -> None:
        """Clear the validation cache."""
        self._cache.clear()
        logger.info("Community validator cache cleared")


# Global validator instance
_community_validator: CommunityValidator | None = None


def get_community_validator() -> CommunityValidator:
    """
    Get or create global community validator instance.

    Returns:
        CommunityValidator: Singleton validator instance
    """
    global _community_validator
    if _community_validator is None:
        _community_validator = CommunityValidator()
    return _community_validator
