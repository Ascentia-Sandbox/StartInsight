"""Tests for community signal validation service.

Tests the CommunityValidator class which validates that community
signals reference real communities (currently Reddit subreddits).
"""

import pytest
from unittest.mock import MagicMock, patch

from app.services.community_validator import (
    CommunityValidator,
    SubredditValidationResult,
    CommunitySignalData,
    get_community_validator,
)


class TestSubredditNameNormalization:
    """Test subreddit name normalization."""

    def test_normalize_with_r_prefix(self):
        """Should remove r/ prefix."""
        validator = CommunityValidator()
        validator._reddit = None  # Skip PRAW init

        assert validator._normalize_subreddit_name("r/startups") == "startups"
        assert validator._normalize_subreddit_name("/r/startups") == "startups"

    def test_normalize_with_url(self):
        """Should handle full URLs."""
        validator = CommunityValidator()
        validator._reddit = None

        result = validator._normalize_subreddit_name("reddit.com/r/startups")
        assert result == "startups"

    def test_normalize_plain_name(self):
        """Should handle plain names."""
        validator = CommunityValidator()
        validator._reddit = None

        assert validator._normalize_subreddit_name("startups") == "startups"


class TestSubscriberCountFormatting:
    """Test subscriber count formatting."""

    def test_format_millions(self):
        """Should format millions correctly."""
        result = CommunityValidator._format_subscriber_count(2_500_000)
        assert result == "2.5M+ members"

    def test_format_thousands(self):
        """Should format thousands correctly."""
        result = CommunityValidator._format_subscriber_count(150_000)
        assert result == "150.0K+ members"

    def test_format_hundreds(self):
        """Should format small counts correctly."""
        result = CommunityValidator._format_subscriber_count(500)
        assert result == "500 members"


class TestCommunityValidatorInit:
    """Test CommunityValidator initialization."""

    @patch('app.services.community_validator.praw.Reddit')
    @patch('app.services.community_validator.settings')
    def test_init_with_credentials(self, mock_settings, mock_reddit):
        """Should initialize with credentials."""
        mock_settings.reddit_client_id = "test_client_id"
        mock_settings.reddit_client_secret = "test_secret"
        mock_settings.reddit_user_agent = "test_agent"

        validator = CommunityValidator()

        mock_reddit.assert_called_once()
        assert validator._reddit is not None

    @patch('app.services.community_validator.settings')
    def test_init_without_credentials(self, mock_settings):
        """Should handle missing credentials gracefully."""
        mock_settings.reddit_client_id = None
        mock_settings.reddit_client_secret = None

        validator = CommunityValidator()

        assert validator._reddit is None


class TestValidateCommunitySignals:
    """Test community signal validation."""

    @pytest.mark.asyncio
    async def test_validate_empty_list(self):
        """Should handle empty signal list."""
        validator = CommunityValidator()
        validator._reddit = None

        validated, valid, invalid = await validator.validate_community_signals([])

        assert validated == []
        assert valid == 0
        assert invalid == 0

    @pytest.mark.asyncio
    async def test_validate_non_reddit_platform(self):
        """Should accept non-Reddit platforms without validation."""
        validator = CommunityValidator()
        validator._reddit = None

        signals = [
            {
                "platform": "Facebook",
                "communities": "2 groups",
                "members": "50K members",
                "score": 7,
                "top_community": "Startup Ideas",
            }
        ]

        validated, valid, invalid = await validator.validate_community_signals(signals)

        assert len(validated) == 1
        assert valid == 1
        assert invalid == 0


class TestGetCommunityValidator:
    """Test singleton getter."""

    def test_returns_validator_instance(self):
        """Should return a CommunityValidator instance."""
        validator = get_community_validator()
        assert isinstance(validator, CommunityValidator)

    def test_returns_same_instance(self):
        """Should return the same instance on subsequent calls."""
        validator1 = get_community_validator()
        validator2 = get_community_validator()
        assert validator1 is validator2
