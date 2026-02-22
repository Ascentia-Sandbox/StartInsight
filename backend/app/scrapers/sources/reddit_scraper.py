"""Reddit scraper using 3-method hybrid: JSON API + Crawl4AI/Firecrawl + PRAW."""

import asyncio
import logging
import re
from datetime import UTC, datetime
from typing import Any

import httpx
from pydantic import HttpUrl

from app.core.config import settings
from app.scrapers import get_scraper_client
from app.scrapers.base_scraper import BaseScraper
from app.scrapers.firecrawl_client import ScrapeResult

logger = logging.getLogger(__name__)

# Reddit JSON API requires a descriptive User-Agent to avoid 429s
_REDDIT_USER_AGENT = "StartInsight/1.0 (startup signal aggregator; +https://startinsight.co)"
_POST_ID_RE = re.compile(r"/comments/([a-z0-9]+)/")


class RedditScraper(BaseScraper):
    """
    3-method hybrid scraper for Reddit startup discussions.

    Method 1: Reddit JSON API (httpx, free, no auth) — primary structured data
    Method 2: Crawl4AI / Firecrawl — comment thread deep-dives on top posts
    Method 3: PRAW (optional) — enrichment when credentials exist

    Scrapes r/startups, r/SaaS (configurable) for:
    - Pain points mentioned in posts/comments
    - Feature requests and product discussions
    - Market validation signals
    """

    def __init__(
        self,
        subreddits: list[str] | None = None,
        limit: int = 25,
        time_filter: str = "day",
    ):
        super().__init__(source_name="reddit")

        self.subreddits = subreddits or [
            s.strip() for s in settings.reddit_subreddits.split(",")
        ]
        self.limit = limit
        self.time_filter = time_filter
        self.rate_limit = settings.reddit_json_rate_limit
        self.search_queries = [
            q.strip() for q in settings.reddit_search_queries.split(",")
        ]
        self.scrape_comments = settings.reddit_scrape_comments
        self.comment_limit = settings.reddit_comment_scrape_limit

        # Scraper client for comment thread deep-dives (Crawl4AI or Firecrawl)
        self.scraper_client = get_scraper_client()

        # Conditionally initialize PRAW
        self._reddit = None
        if self._has_praw_credentials():
            try:
                import praw

                self._reddit = praw.Reddit(
                    client_id=settings.reddit_client_id,
                    client_secret=settings.reddit_client_secret,
                    user_agent=settings.reddit_user_agent,
                )
                logger.info("PRAW client initialized for Reddit enrichment")
            except Exception as e:
                logger.warning(f"PRAW init failed, continuing without it: {e}")

        logger.info(
            f"Reddit scraper initialized: subreddits={self.subreddits}, "
            f"limit={limit}, praw={'yes' if self._reddit else 'no'}"
        )

    async def scrape(self) -> list[ScrapeResult]:
        """
        Execute 3-method hybrid scrape.

        Phase 1: Reddit JSON API (always runs)
        Phase 2: Comment thread deep-dives via Crawl4AI/Firecrawl (top N posts)
        Phase 3: PRAW enrichment (only when credentials exist)

        Returns deduplicated list of ScrapeResult.
        """
        all_results: list[ScrapeResult] = []

        # Phase 1: Reddit JSON API (structured data, always available)
        json_results = await self._scrape_via_json_api()
        all_results.extend(json_results)
        logger.info(f"Phase 1 (JSON API): {len(json_results)} posts")

        # Phase 2: Comment deep-dives on top posts
        if self.scrape_comments and json_results:
            comment_results = await self._scrape_comment_threads(json_results)
            all_results.extend(comment_results)
            logger.info(f"Phase 2 (Comment threads): {len(comment_results)} threads")

        # Phase 3: PRAW enrichment (optional)
        if self._reddit:
            praw_results = await self._scrape_via_praw()
            all_results.extend(praw_results)
            logger.info(f"Phase 3 (PRAW): {len(praw_results)} posts")

        # Deduplicate by Reddit post ID
        deduplicated = self._deduplicate_results(all_results)
        logger.info(
            f"Reddit scrape complete: {len(deduplicated)} unique results "
            f"(from {len(all_results)} total)"
        )

        self.log_scrape_summary(deduplicated)
        return deduplicated

    # ── Phase 1: Reddit JSON API ──────────────────────────────────────

    async def _scrape_via_json_api(self) -> list[ScrapeResult]:
        """Fetch posts from Reddit's public JSON API (no auth required)."""
        results: list[ScrapeResult] = []

        async with httpx.AsyncClient(
            headers={"User-Agent": _REDDIT_USER_AGENT},
            timeout=httpx.Timeout(30.0),
            follow_redirects=True,
        ) as client:
            # Subreddit feeds: top + new for each subreddit
            for sub in self.subreddits:
                for sort in ("top", "new"):
                    params: dict[str, Any] = {"limit": self.limit}
                    if sort == "top":
                        params["t"] = self.time_filter
                    url = f"https://www.reddit.com/r/{sub}/{sort}.json"

                    posts = await self._fetch_json_listing(client, url, params)
                    results.extend(posts)
                    await asyncio.sleep(self.rate_limit)

            # Cross-subreddit search queries
            for query in self.search_queries:
                url = "https://www.reddit.com/search.json"
                params = {"q": query, "t": self.time_filter, "limit": self.limit, "sort": "relevance"}
                posts = await self._fetch_json_listing(client, url, params)
                results.extend(posts)
                await asyncio.sleep(self.rate_limit)

        return results

    async def _fetch_json_listing(
        self,
        client: httpx.AsyncClient,
        url: str,
        params: dict[str, Any],
    ) -> list[ScrapeResult]:
        """Fetch a single Reddit JSON listing and convert to ScrapeResults."""
        try:
            resp = await client.get(url, params=params)
            resp.raise_for_status()
            data = resp.json()

            children = data.get("data", {}).get("children", [])
            results: list[ScrapeResult] = []

            for child in children:
                post = child.get("data", {})
                if not post:
                    continue

                # Skip posts older than 7 days
                created_utc = post.get("created_utc", 0)
                if created_utc:
                    age_days = (datetime.now(UTC) - datetime.fromtimestamp(created_utc, tz=UTC)).days
                    if age_days > 7:
                        continue

                permalink = post.get("permalink", "")
                post_url = f"https://reddit.com{permalink}" if permalink else ""
                if not post_url:
                    continue

                # Build markdown content
                title = post.get("title", "")
                selftext = post.get("selftext", "")
                subreddit = post.get("subreddit", "")
                author = post.get("author", "[deleted]")
                score = post.get("score", 0)
                num_comments = post.get("num_comments", 0)

                content_parts = [
                    f"# {title}\n",
                    f"**Subreddit**: r/{subreddit}",
                    f"**Author**: u/{author}",
                    f"**Score**: {score} upvotes",
                    f"**Comments**: {num_comments}\n",
                ]
                if selftext:
                    content_parts.append("## Post Content\n")
                    content_parts.append(selftext)

                content = "\n\n".join(content_parts)

                metadata = {
                    "subreddit": subreddit,
                    "upvotes": score,
                    "num_comments": num_comments,
                    "created_utc": created_utc,
                    "author": author,
                    "post_id": post.get("id", ""),
                    "source_method": "json_api",
                }

                results.append(
                    ScrapeResult(
                        url=HttpUrl(post_url),
                        title=title,
                        content=self.clean_text(content),
                        metadata=metadata,
                    )
                )

            logger.debug(f"JSON API: {len(results)} posts from {url}")
            return results

        except httpx.HTTPStatusError as e:
            logger.warning(f"Reddit JSON API HTTP error for {url}: {e.response.status_code}")
            return []
        except Exception as e:
            logger.warning(f"Reddit JSON API error for {url}: {type(e).__name__} - {e}")
            return []

    # ── Phase 2: Comment Thread Deep-Dives ────────────────────────────

    async def _scrape_comment_threads(
        self, posts: list[ScrapeResult]
    ) -> list[ScrapeResult]:
        """Scrape full comment threads for top N posts using Crawl4AI/Firecrawl."""
        # Sort by score descending and pick top N
        scored_posts = sorted(
            posts,
            key=lambda p: p.metadata.get("upvotes", 0),
            reverse=True,
        )
        top_posts = scored_posts[: self.comment_limit]

        results: list[ScrapeResult] = []

        for post in top_posts:
            permalink = str(post.url)
            # Use old.reddit.com for cleaner HTML (less JS)
            comment_url = permalink.replace("https://reddit.com", "https://old.reddit.com")

            try:
                scrape_result = await self.scraper_client.scrape_url(comment_url)

                # Enrich metadata to mark this as a comment-thread scrape
                post_id = self._extract_post_id(permalink)
                scrape_result.metadata.update({
                    "subreddit": post.metadata.get("subreddit", ""),
                    "upvotes": post.metadata.get("upvotes", 0),
                    "num_comments": post.metadata.get("num_comments", 0),
                    "post_id": post_id or "",
                    "source_method": "comment_thread",
                })

                results.append(scrape_result)
                logger.debug(f"Scraped comment thread: {post.title}")

            except Exception as e:
                logger.warning(
                    f"Comment thread scrape failed for {post.title}: "
                    f"{type(e).__name__} - {e}"
                )
                continue

        return results

    # ── Phase 3: PRAW Enrichment ──────────────────────────────────────

    async def _scrape_via_praw(self) -> list[ScrapeResult]:
        """Fetch posts via PRAW (wrapped in asyncio.to_thread since PRAW is sync)."""
        if not self._reddit:
            return []

        try:
            results = await asyncio.to_thread(self._praw_sync_fetch)
            return results
        except Exception as e:
            logger.warning(f"PRAW scraping failed: {type(e).__name__} - {e}")
            return []

    def _praw_sync_fetch(self) -> list[ScrapeResult]:
        """Synchronous PRAW fetch (runs in thread pool)."""

        results: list[ScrapeResult] = []

        for sub_name in self.subreddits:
            try:
                subreddit = self._reddit.subreddit(sub_name)

                for submission in subreddit.top(
                    time_filter=self.time_filter, limit=self.limit
                ):
                    # Skip old posts
                    age_days = (
                        datetime.now(UTC)
                        - datetime.fromtimestamp(submission.created_utc, tz=UTC)
                    ).days
                    if age_days > 7:
                        continue

                    post_url = f"https://reddit.com{submission.permalink}"
                    content = self._build_praw_content(submission)

                    metadata = {
                        "subreddit": sub_name,
                        "upvotes": submission.score,
                        "num_comments": submission.num_comments,
                        "created_utc": submission.created_utc,
                        "author": str(submission.author) if submission.author else "[deleted]",
                        "post_id": submission.id,
                        "source_method": "praw",
                    }

                    results.append(
                        ScrapeResult(
                            url=HttpUrl(post_url),
                            title=submission.title,
                            content=self.clean_text(content),
                            metadata=metadata,
                        )
                    )

            except Exception as e:
                logger.warning(f"PRAW error for r/{sub_name}: {type(e).__name__} - {e}")
                continue

        return results

    def _build_praw_content(self, submission) -> str:
        """Build markdown content from a PRAW submission with top comments."""
        parts = [
            f"# {submission.title}\n",
            f"**Subreddit**: r/{submission.subreddit.display_name}",
            f"**Author**: u/{submission.author if submission.author else '[deleted]'}",
            f"**Score**: {submission.score} upvotes",
            f"**Comments**: {submission.num_comments}\n",
        ]

        if submission.selftext:
            parts.append("## Post Content\n")
            parts.append(submission.selftext)

        # Fetch top comments
        try:
            submission.comment_limit = 5
            submission.comment_sort = "top"
            submission.comments.replace_more(limit=0)

            if submission.comments:
                parts.append("\n## Top Comments\n")
                for i, comment in enumerate(submission.comments[:5], 1):
                    if hasattr(comment, "body"):
                        author = comment.author if comment.author else "[deleted]"
                        parts.append(
                            f"**Comment {i}** (u/{author}, {comment.score} upvotes):\n"
                            f"{comment.body}\n"
                        )
        except Exception:
            pass  # Comments are bonus data, don't fail the post

        return "\n\n".join(parts)

    # ── Helpers ───────────────────────────────────────────────────────

    def _has_praw_credentials(self) -> bool:
        """Check if real PRAW credentials are configured (not placeholders)."""
        cid = settings.reddit_client_id
        if not cid or not settings.reddit_client_secret:
            return False
        # Skip placeholder values
        placeholders = ("your_reddit", "placeholder", "changeme", "xxx")
        return not any(p in cid.lower() for p in placeholders)

    @staticmethod
    def _extract_post_id(url: str) -> str | None:
        """Extract Reddit post ID from a URL like /comments/abc123/."""
        match = _POST_ID_RE.search(url)
        return match.group(1) if match else None

    @staticmethod
    def _deduplicate_results(results: list[ScrapeResult]) -> list[ScrapeResult]:
        """
        Deduplicate results by Reddit post ID.

        Priority: praw > comment_thread > json_api (richer data wins).
        """
        METHOD_PRIORITY = {"praw": 3, "comment_thread": 2, "json_api": 1}

        seen: dict[str, ScrapeResult] = {}
        no_id_results: list[ScrapeResult] = []

        for result in results:
            post_id = result.metadata.get("post_id")
            if not post_id:
                # Try extracting from URL
                post_id = RedditScraper._extract_post_id(str(result.url))

            if not post_id:
                no_id_results.append(result)
                continue

            existing = seen.get(post_id)
            if existing is None:
                seen[post_id] = result
            else:
                # Keep the one with higher priority source method
                existing_priority = METHOD_PRIORITY.get(
                    existing.metadata.get("source_method", ""), 0
                )
                new_priority = METHOD_PRIORITY.get(
                    result.metadata.get("source_method", ""), 0
                )
                if new_priority > existing_priority:
                    seen[post_id] = result

        return list(seen.values()) + no_id_results
