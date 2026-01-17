"""Firecrawl client wrapper with retry logic and error handling."""

import logging
from typing import Any

from firecrawl import FirecrawlApp
from pydantic import BaseModel, Field, HttpUrl
from tenacity import (
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

from app.core.config import settings

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


class FirecrawlClient:
    """
    Wrapper around Firecrawl SDK with retry logic and error handling.

    Implements the firecrawl-glue skill standards:
    - Uses official Firecrawl SDK
    - Requests markdown format for LLM optimization
    - 3-tier retry logic with exponential backoff
    - Structured output via Pydantic models
    """

    def __init__(self, api_key: str | None = None):
        """
        Initialize Firecrawl client.

        Args:
            api_key: Firecrawl API key. If not provided, uses settings.

        Raises:
            ValueError: If API key is not provided and not in settings.
        """
        self.api_key = api_key or settings.firecrawl_api_key
        if not self.api_key:
            raise ValueError(
                "Firecrawl API key not found. "
                "Set FIRECRAWL_API_KEY environment variable."
            )

        self.client = FirecrawlApp(api_key=self.api_key)
        logger.info("Firecrawl client initialized")

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
        - Rate limiting (429 responses)
        - Transient API failures

        Args:
            url: URL to scrape

        Returns:
            ScrapeResult with markdown content and metadata

        Raises:
            Exception: After 3 failed attempts

        Example:
            >>> client = FirecrawlClient()
            >>> result = await client.scrape_url("https://example.com")
            >>> print(result.content)  # Markdown content
        """
        try:
            logger.info(f"Scraping URL: {url}")

            # Request markdown format (optimal for LLM processing)
            response = self.client.scrape_url(
                url=url, params={"formats": ["markdown"]}
            )

            # Extract metadata safely
            metadata = response.get("metadata", {})
            title = metadata.get("title", "")
            markdown_content = response.get("markdown", "")

            if not markdown_content:
                logger.warning(f"Empty content returned for URL: {url}")

            result = ScrapeResult(
                url=url,
                title=title,
                content=markdown_content,
                metadata=metadata,
            )

            logger.info(
                f"Successfully scraped {url} "
                f"({len(markdown_content)} chars, title: {title})"
            )
            return result

        except Exception as e:
            logger.error(f"Error scraping {url}: {type(e).__name__} - {e}")
            raise

    def scrape_url_sync(self, url: str) -> ScrapeResult:
        """
        Synchronous version of scrape_url for non-async contexts.

        Note: Prefer async version when possible.

        Args:
            url: URL to scrape

        Returns:
            ScrapeResult with markdown content and metadata
        """
        try:
            logger.info(f"Scraping URL (sync): {url}")

            response = self.client.scrape_url(
                url=url, params={"formats": ["markdown"]}
            )

            metadata = response.get("metadata", {})
            title = metadata.get("title", "")
            markdown_content = response.get("markdown", "")

            result = ScrapeResult(
                url=url,
                title=title,
                content=markdown_content,
                metadata=metadata,
            )

            logger.info(f"Successfully scraped {url} (sync)")
            return result

        except Exception as e:
            logger.error(f"Error scraping {url} (sync): {e}")
            raise


# Global client instance for reuse
_firecrawl_client: FirecrawlClient | None = None


def get_firecrawl_client() -> FirecrawlClient:
    """
    Get or create global Firecrawl client instance.

    Returns:
        FirecrawlClient: Singleton client instance
    """
    global _firecrawl_client
    if _firecrawl_client is None:
        _firecrawl_client = FirecrawlClient()
    return _firecrawl_client
