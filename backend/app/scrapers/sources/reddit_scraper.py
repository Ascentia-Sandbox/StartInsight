"""Reddit scraper using PRAW + Firecrawl."""

import logging
from datetime import datetime, timedelta

import praw
from pydantic import HttpUrl

from app.core.config import settings
from app.scrapers.base_scraper import BaseScraper
from app.scrapers.firecrawl_client import ScrapeResult, get_firecrawl_client

logger = logging.getLogger(__name__)


class RedditScraper(BaseScraper):
    """
    Scraper for Reddit startup discussions.

    Scrapes r/startups and r/SaaS for:
    - Pain points mentioned in posts/comments
    - Feature requests and product discussions
    - Market validation signals
    - Competitor mentions

    Uses PRAW for Reddit API access + Firecrawl for content extraction.
    """

    def __init__(
        self,
        subreddits: list[str] | None = None,
        limit: int = 25,
        time_filter: str = "day",
    ):
        """
        Initialize Reddit scraper.

        Args:
            subreddits: List of subreddits to scrape (default: ["startups", "SaaS"])
            limit: Number of posts to fetch per subreddit (default: 25)
            time_filter: Time filter for posts ("day", "week", "month", "year")
        """
        super().__init__(source_name="reddit")

        self.subreddits = subreddits or ["startups", "SaaS"]
        self.limit = limit
        self.time_filter = time_filter

        # Initialize PRAW client
        self.reddit = praw.Reddit(
            client_id=settings.reddit_client_id,
            client_secret=settings.reddit_client_secret,
            user_agent=f"StartInsight Scraper v1.0 by u/{settings.reddit_username or 'StartInsight'}",
        )

        # Initialize Firecrawl client for content extraction
        self.firecrawl = get_firecrawl_client()

        logger.info(
            f"Reddit scraper initialized for: {', '.join(self.subreddits)} "
            f"(limit={limit}, time_filter={time_filter})"
        )

    async def scrape(self) -> list[ScrapeResult]:
        """
        Scrape top posts from configured subreddits.

        Returns:
            List of ScrapeResult objects with post content

        Example:
            >>> scraper = RedditScraper()
            >>> results = await scraper.scrape()
            >>> print(f"Scraped {len(results)} posts")
        """
        all_results: list[ScrapeResult] = []

        for subreddit_name in self.subreddits:
            try:
                results = await self._scrape_subreddit(subreddit_name)
                all_results.extend(results)
                logger.info(
                    f"Scraped {len(results)} posts from r/{subreddit_name}"
                )
            except Exception as e:
                logger.error(
                    f"Error scraping r/{subreddit_name}: "
                    f"{type(e).__name__} - {e}"
                )
                continue

        self.log_scrape_summary(all_results)
        return all_results

    async def _scrape_subreddit(self, subreddit_name: str) -> list[ScrapeResult]:
        """
        Scrape a single subreddit.

        Args:
            subreddit_name: Name of subreddit (without r/)

        Returns:
            List of ScrapeResult objects
        """
        subreddit = self.reddit.subreddit(subreddit_name)
        results: list[ScrapeResult] = []

        # Get top posts from the specified time period
        for submission in subreddit.top(
            time_filter=self.time_filter, limit=self.limit
        ):
            try:
                # Skip if post is too old (older than 7 days)
                post_age_days = (
                    datetime.utcnow() - datetime.utcfromtimestamp(submission.created_utc)
                ).days
                if post_age_days > 7:
                    logger.debug(f"Skipping old post: {submission.title} ({post_age_days} days old)")
                    continue

                # Extract post data
                post_url = f"https://reddit.com{submission.permalink}"

                # Build markdown content from post
                content = self._build_post_content(submission)

                # Create metadata
                metadata = {
                    "subreddit": subreddit_name,
                    "upvotes": submission.score,
                    "num_comments": submission.num_comments,
                    "created_utc": submission.created_utc,
                    "author": str(submission.author) if submission.author else "[deleted]",
                    "post_id": submission.id,
                }

                result = ScrapeResult(
                    url=HttpUrl(post_url),
                    title=submission.title,
                    content=self.clean_text(content),
                    metadata=metadata,
                )

                results.append(result)
                logger.debug(
                    f"Scraped: {submission.title} "
                    f"({submission.score} upvotes, {submission.num_comments} comments)"
                )

            except Exception as e:
                logger.error(
                    f"Error processing submission {submission.id}: "
                    f"{type(e).__name__} - {e}"
                )
                continue

        return results

    def _build_post_content(self, submission: praw.models.Submission) -> str:
        """
        Build markdown content from Reddit submission.

        Args:
            submission: PRAW submission object

        Returns:
            Markdown-formatted content
        """
        content_parts = [
            f"# {submission.title}\n",
            f"**Subreddit**: r/{submission.subreddit.display_name}",
            f"**Author**: u/{submission.author if submission.author else '[deleted]'}",
            f"**Score**: {submission.score} upvotes",
            f"**Comments**: {submission.num_comments}\n",
        ]

        # Add post body (selftext)
        if submission.selftext:
            content_parts.append("## Post Content\n")
            content_parts.append(submission.selftext)

        # Add top comments for additional context
        submission.comment_limit = 5
        submission.comment_sort = "top"
        submission.comments.replace_more(limit=0)  # Remove "MoreComments" objects

        if submission.comments:
            content_parts.append("\n## Top Comments\n")
            for i, comment in enumerate(submission.comments[:5], 1):
                if hasattr(comment, "body"):
                    content_parts.append(
                        f"**Comment {i}** (by u/{comment.author if comment.author else '[deleted]'}, "
                        f"{comment.score} upvotes):\n{comment.body}\n"
                    )

        return "\n\n".join(content_parts)

    async def scrape_user_posts(
        self, username: str, limit: int = 10
    ) -> list[ScrapeResult]:
        """
        Scrape posts from a specific Reddit user.

        Useful for tracking influential founders or thought leaders.

        Args:
            username: Reddit username (without u/)
            limit: Number of posts to fetch

        Returns:
            List of ScrapeResult objects
        """
        user = self.reddit.redditor(username)
        results: list[ScrapeResult] = []

        for submission in user.submissions.top(time_filter="month", limit=limit):
            try:
                post_url = f"https://reddit.com{submission.permalink}"
                content = self._build_post_content(submission)

                metadata = {
                    "subreddit": submission.subreddit.display_name,
                    "upvotes": submission.score,
                    "num_comments": submission.num_comments,
                    "created_utc": submission.created_utc,
                    "author": username,
                    "post_id": submission.id,
                }

                result = ScrapeResult(
                    url=HttpUrl(post_url),
                    title=submission.title,
                    content=self.clean_text(content),
                    metadata=metadata,
                )

                results.append(result)

            except Exception as e:
                logger.error(f"Error processing user post: {e}")
                continue

        logger.info(f"Scraped {len(results)} posts from u/{username}")
        return results
