"""Crawl4AI client wrapper matching Firecrawl's interface for cost optimization."""

import asyncio
import logging
from typing import Any

from crawl4ai import AsyncWebCrawler
from pydantic import BaseModel, Field, HttpUrl
from tenacity import (
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

logger = logging.getLogger(__name__)


class ScrapeResult(BaseModel):
    """
    Standardized scrape result model.

    All scrapers must return data in this format to ensure consistency
    before data is stored in the database.
    """

    url: HttpUrl = Field(..., description="URL that was scraped")
    title: str = Field(default="", description="Page title")
    content: str = Field(..., description="Markdown-formatted content")
    metadata: dict[str, Any] = Field(
        default_factory=dict,
        description="Additional metadata (source-specific)",
    )


class Crawl4AIClient:
    """
    Wrapper around Crawl4AI (open-source alternative to Firecrawl).

    Benefits:
    - $0 cost (self-hosted, runs in Railway container)
    - Better privacy (data stays on your servers)
    - Same interface as Firecrawl (drop-in replacement)

    Trade-offs:
    - 20-30% slower than Firecrawl (acceptable for PMF validation)
    - +50MB container size (within Railway limits)

    Implements the same standards as FirecrawlClient:
    - Requests markdown format for LLM optimization
    - 3-tier retry logic with exponential backoff
    - Structured output via Pydantic models
    """

    def __init__(self):
        """
        Initialize Crawl4AI client.

        Note: No API key required (self-hosted).
        """
        logger.info("Crawl4AI client initialized (self-hosted, $0 cost)")

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=4, max=10),
        retry=retry_if_exception_type(Exception),
        reraise=True,
    )
    async def scrape_url(self, url: str) -> ScrapeResult:
        """
        Scrape a URL and return markdown content with retry logic.

        Implements 3-tier retry with exponential backoff for:
        - Network errors
        - Browser timeouts
        - Transient scraping failures

        Args:
            url: URL to scrape

        Returns:
            ScrapeResult with markdown content and metadata

        Raises:
            Exception: After 3 failed attempts

        Example:
            >>> client = Crawl4AIClient()
            >>> result = await client.scrape_url("https://example.com")
            >>> print(result.content)  # Markdown content
        """
        try:
            logger.info(f"Scraping URL with Crawl4AI: {url}")

            # Use AsyncWebCrawler with context manager for proper cleanup
            async with AsyncWebCrawler(verbose=False) as crawler:
                # word_count_threshold=10 filters out boilerplate
                # 30s timeout prevents hanging the entire scrape_all_sources_task
                result = await asyncio.wait_for(
                    crawler.arun(
                        url=url,
                        word_count_threshold=10,
                        bypass_cache=False,  # Use cache for repeated URLs
                    ),
                    timeout=30.0,
                )

                # Extract content (prefer markdown, fallback to cleaned HTML)
                title = result.metadata.get("title", "") if result.metadata else ""
                markdown_content = result.markdown or result.cleaned_html or ""

                if not markdown_content:
                    logger.warning(f"Empty content returned for URL: {url}")

                scrape_result = ScrapeResult(
                    url=url,
                    title=title,
                    content=markdown_content,
                    metadata={
                        "source": "crawl4ai",
                        "success": result.success,
                        "status_code": result.status_code if hasattr(result, "status_code") else None,
                    },
                )

                logger.info(
                    f"Successfully scraped {url} with Crawl4AI "
                    f"({len(markdown_content)} chars, title: {title})"
                )
                return scrape_result

        except Exception as e:
            logger.error(f"Error scraping {url} with Crawl4AI: {type(e).__name__} - {e}")
            raise

    def scrape_url_sync(self, url: str) -> ScrapeResult:
        """
        Synchronous version not implemented (Crawl4AI is async-only).

        Args:
            url: URL to scrape

        Raises:
            NotImplementedError: Use async version instead
        """
        raise NotImplementedError(
            "Crawl4AI is async-only. Use scrape_url() with asyncio.run() or await."
        )


# Global client instance for reuse
_crawl4ai_client: Crawl4AIClient | None = None


def get_crawl4ai_client() -> Crawl4AIClient:
    """
    Get or create global Crawl4AI client instance.

    Returns:
        Crawl4AIClient: Singleton client instance
    """
    global _crawl4ai_client
    if _crawl4ai_client is None:
        _crawl4ai_client = Crawl4AIClient()
    return _crawl4ai_client
