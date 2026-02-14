"""Hacker News Scraper - Phase H.3.

Scrapes startup-related discussions from Hacker News using the
free Algolia Search API (no authentication required).

Supports:
- Top stories from the last 24 hours
- "Show HN" posts (launches/demos)
- Filtering by minimum score for quality
- Async HTTP via httpx
"""

import logging
from datetime import UTC, datetime, timedelta

import httpx
from pydantic import HttpUrl

from app.scrapers.base_scraper import BaseScraper, scraper_retry
from app.scrapers.firecrawl_client import ScrapeResult

logger = logging.getLogger(__name__)

# HN Algolia API base URL (free, no auth required)
HN_ALGOLIA_API = "https://hn.algolia.com/api/v1"


class HackerNewsScraper(BaseScraper):
    """
    Hacker News scraper using the Algolia Search API.

    Fetches top stories and "Show HN" posts from the last 24 hours,
    filtered by minimum score for quality signals.

    The Algolia API is free and requires no authentication.
    """

    def __init__(
        self,
        min_score: int = 50,
        max_results: int = 30,
        hours_back: int = 24,
    ):
        """
        Initialize Hacker News scraper.

        Args:
            min_score: Minimum HN score (points) to include (default: 50)
            max_results: Maximum stories to return (default: 30)
            hours_back: How far back to look for stories (default: 24 hours)
        """
        super().__init__(source_name="hacker_news")
        self.min_score = min_score
        self.max_results = max_results
        self.hours_back = hours_back

    @scraper_retry
    async def _fetch_stories(
        self,
        query: str = "",
        tags: str = "story",
        num_results: int = 50,
    ) -> list[dict]:
        """
        Fetch stories from HN Algolia API.

        Args:
            query: Search query string (empty for all)
            tags: HN Algolia tags filter (e.g., "story", "show_hn")
            num_results: Number of results to request from API

        Returns:
            List of story dicts from the API response

        Raises:
            httpx.HTTPStatusError: On non-2xx responses
        """
        cutoff_timestamp = int(
            (datetime.now(UTC) - timedelta(hours=self.hours_back)).timestamp()
        )

        params = {
            "query": query,
            "tags": tags,
            "numericFilters": f"created_at_i>{cutoff_timestamp},points>{self.min_score}",
            "hitsPerPage": num_results,
        }

        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(
                f"{HN_ALGOLIA_API}/search",
                params=params,
            )
            response.raise_for_status()
            data = response.json()

        hits = data.get("hits", [])
        logger.info(
            f"HN Algolia returned {len(hits)} hits "
            f"(query={query!r}, tags={tags}, min_score={self.min_score})"
        )
        return hits

    async def scrape(self) -> list[ScrapeResult]:
        """
        Scrape Hacker News for startup-relevant stories.

        Fetches top stories and "Show HN" posts from the last 24 hours,
        filtered by minimum score. Returns deduplicated results sorted
        by score descending.

        Returns:
            List of ScrapeResult objects with story data
        """
        all_hits: list[dict] = []

        # Fetch top stories (general high-score posts)
        try:
            top_stories = await self._fetch_stories(
                tags="story",
                num_results=self.max_results,
            )
            all_hits.extend(top_stories)
        except Exception as e:
            logger.error(f"Failed to fetch HN top stories: {type(e).__name__} - {e}")

        # Fetch "Show HN" posts (launches, demos, side projects)
        try:
            show_hn = await self._fetch_stories(
                tags="show_hn",
                num_results=self.max_results,
            )
            all_hits.extend(show_hn)
        except Exception as e:
            logger.error(f"Failed to fetch HN Show HN posts: {type(e).__name__} - {e}")

        if not all_hits:
            logger.warning("No stories fetched from Hacker News")
            return []

        # Deduplicate by objectID
        seen_ids: set[str] = set()
        unique_hits: list[dict] = []
        for hit in all_hits:
            object_id = hit.get("objectID", "")
            if object_id and object_id not in seen_ids:
                seen_ids.add(object_id)
                unique_hits.append(hit)

        # Sort by score descending, take top max_results
        unique_hits.sort(key=lambda h: h.get("points", 0), reverse=True)
        unique_hits = unique_hits[: self.max_results]

        # Convert to ScrapeResult objects
        results: list[ScrapeResult] = []
        for hit in unique_hits:
            try:
                result = self._hit_to_scrape_result(hit)
                if result:
                    results.append(result)
            except Exception as e:
                logger.error(
                    f"Error converting HN hit {hit.get('objectID', '?')}: "
                    f"{type(e).__name__} - {e}"
                )

        logger.info(f"Hacker News scraper found {len(results)} signals")
        self.log_scrape_summary(results)
        return results

    def _hit_to_scrape_result(self, hit: dict) -> ScrapeResult | None:
        """
        Convert an Algolia hit dict to a ScrapeResult.

        Args:
            hit: Raw hit dict from Algolia API

        Returns:
            ScrapeResult or None if essential data is missing
        """
        object_id = hit.get("objectID", "")
        title = hit.get("title", "")
        if not title:
            return None

        # Use the story URL if available, otherwise link to HN comments
        story_url = hit.get("url") or f"https://news.ycombinator.com/item?id={object_id}"
        hn_url = f"https://news.ycombinator.com/item?id={object_id}"

        points = hit.get("points", 0)
        num_comments = hit.get("num_comments", 0)
        author = hit.get("author", "unknown")
        created_at = hit.get("created_at", "")
        story_text = hit.get("story_text") or ""

        # Determine if this is a Show HN post
        is_show_hn = title.startswith("Show HN:")
        post_type = "show_hn" if is_show_hn else "story"

        # Build formatted content for LLM analysis
        content = self._format_story_markdown(
            title=title,
            author=author,
            points=points,
            num_comments=num_comments,
            created_at=created_at,
            story_url=story_url,
            hn_url=hn_url,
            story_text=story_text,
            post_type=post_type,
        )

        return ScrapeResult(
            url=HttpUrl(hn_url),
            title=title,
            content=self.clean_text(content),
            metadata={
                "source": "hacker_news",
                "hn_id": object_id,
                "author": author,
                "points": points,
                "num_comments": num_comments,
                "created_at": created_at,
                "story_url": story_url,
                "post_type": post_type,
                "is_show_hn": is_show_hn,
            },
        )

    @staticmethod
    def _format_story_markdown(
        title: str,
        author: str,
        points: int,
        num_comments: int,
        created_at: str,
        story_url: str,
        hn_url: str,
        story_text: str,
        post_type: str,
    ) -> str:
        """
        Format HN story data as markdown content for LLM analysis.

        Args:
            title: Story title
            author: HN username of submitter
            points: Upvote count
            num_comments: Number of comments
            created_at: ISO timestamp of submission
            story_url: External URL (if any)
            hn_url: HN discussion URL
            story_text: Self-text for text posts (e.g., Show HN descriptions)
            post_type: "story" or "show_hn"

        Returns:
            Formatted markdown content
        """
        type_label = "Show HN" if post_type == "show_hn" else "Story"

        content_parts = [
            f"# {title}",
            "",
            f"**Type:** {type_label}",
            f"**Author:** {author}",
            f"**Posted:** {created_at}",
            "",
            "---",
            "",
            "## Engagement",
            "",
            f"- **Points:** {points:,}",
            f"- **Comments:** {num_comments:,}",
            "",
            "## Links",
            "",
            f"- **HN Discussion:** {hn_url}",
        ]

        if story_url and story_url != hn_url:
            content_parts.append(f"- **External Link:** {story_url}")

        if story_text:
            content_parts.extend([
                "",
                "## Description",
                "",
                story_text,
            ])

        return "\n".join(content_parts)
