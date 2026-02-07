"""Base scraper class with common logic for all scrapers.

This module provides the abstract base class for all data scrapers,
including common functionality for:
- Saving raw data to database
- Logging scraping activity
- Error handling with retry logic
- Rate limiting integration
- Data deduplication
"""

import hashlib
import logging
from abc import ABC, abstractmethod
from typing import Callable

import httpx
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from tenacity import (
    before_sleep_log,
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

from app.models.raw_signal import RawSignal
from app.scrapers.firecrawl_client import ScrapeResult

logger = logging.getLogger(__name__)

# Exceptions that are safe to retry
RETRYABLE_EXCEPTIONS = (
    httpx.TimeoutException,
    httpx.ConnectError,
    httpx.ReadTimeout,
    httpx.WriteTimeout,
    httpx.PoolTimeout,
    ConnectionError,
    TimeoutError,
    OSError,  # Includes network-related OS errors
)


def create_retry_decorator(
    max_attempts: int = 3,
    min_wait: float = 2.0,
    max_wait: float = 30.0,
    multiplier: float = 1.0,
) -> Callable:
    """
    Create a retry decorator for scraper methods.

    Uses exponential backoff with configurable parameters.

    Args:
        max_attempts: Maximum number of retry attempts
        min_wait: Minimum wait time between retries (seconds)
        max_wait: Maximum wait time between retries (seconds)
        multiplier: Multiplier for exponential backoff

    Returns:
        Configured retry decorator

    Example:
        >>> @create_retry_decorator(max_attempts=3)
        ... async def fetch_data():
        ...     ...
    """
    return retry(
        stop=stop_after_attempt(max_attempts),
        wait=wait_exponential(multiplier=multiplier, min=min_wait, max=max_wait),
        retry=retry_if_exception_type(RETRYABLE_EXCEPTIONS),
        before_sleep=before_sleep_log(logger, logging.WARNING),
        reraise=True,
    )


# Default retry decorator for scraper methods
scraper_retry = create_retry_decorator(max_attempts=3, min_wait=2, max_wait=30)


class BaseScraper(ABC):
    """
    Abstract base class for all data scrapers.

    Provides common functionality:
    - Saving raw data to database
    - Logging scraping activity
    - Error handling
    - Standardized interface

    All source-specific scrapers should inherit from this class.
    """

    def __init__(self, source_name: str):
        """
        Initialize scraper.

        Args:
            source_name: Identifier for this data source (e.g., "reddit", "product_hunt")
        """
        self.source_name = source_name
        logger.info(f"Initialized {source_name} scraper")

    @abstractmethod
    async def scrape(self) -> list[ScrapeResult]:
        """
        Scrape data from the source.

        This method must be implemented by each scraper subclass.

        Returns:
            List of ScrapeResult objects containing scraped data

        Raises:
            NotImplementedError: If not implemented by subclass
        """
        raise NotImplementedError("Subclasses must implement scrape() method")

    async def save_to_database(
        self, session: AsyncSession, results: list[ScrapeResult]
    ) -> list[RawSignal]:
        """
        Save scrape results to database with deduplication.

        Uses content hash to prevent storing duplicate content.

        Args:
            session: Async database session
            results: List of ScrapeResult objects to save

        Returns:
            List of created RawSignal database records

        Example:
            >>> scraper = RedditScraper()
            >>> results = await scraper.scrape()
            >>> async with AsyncSessionLocal() as session:
            >>>     signals = await scraper.save_to_database(session, results)
            >>>     await session.commit()
        """
        if not results:
            logger.warning(f"No results to save from {self.source_name}")
            return []

        signals: list[RawSignal] = []
        duplicates_skipped = 0

        for result in results:
            try:
                # Compute content hash for deduplication
                content_hash = self.compute_content_hash(result.content)

                # Check if content already exists
                existing_query = select(RawSignal).where(
                    RawSignal.content_hash == content_hash
                )
                existing_result = await session.execute(existing_query)
                existing = existing_result.scalar_one_or_none()

                if existing:
                    logger.debug(
                        f"Duplicate content skipped: {result.url} "
                        f"(matches signal {existing.id})"
                    )
                    duplicates_skipped += 1
                    continue

                # Also check URL deduplication (less strict)
                url_query = select(RawSignal).where(
                    RawSignal.url == str(result.url),
                    RawSignal.source == self.source_name,
                )
                url_result = await session.execute(url_query)
                url_existing = url_result.scalar_one_or_none()

                if url_existing:
                    logger.debug(
                        f"Duplicate URL skipped: {result.url}"
                    )
                    duplicates_skipped += 1
                    continue

                # Create RawSignal model instance
                signal = RawSignal(
                    source=self.source_name,
                    url=str(result.url),
                    content=result.content,
                    content_hash=content_hash,
                    extra_metadata={
                        "title": result.title,
                        **result.metadata,
                    },
                    processed=False,
                )

                session.add(signal)
                signals.append(signal)

                logger.debug(
                    f"Added signal from {self.source_name}: "
                    f"{result.title or result.url}"
                )

            except Exception as e:
                logger.error(
                    f"Error creating signal for {result.url}: "
                    f"{type(e).__name__} - {e}"
                )
                continue

        # Flush to get IDs without committing
        # (commit should be handled by caller)
        await session.flush()

        logger.info(
            f"Saved {len(signals)} signals from {self.source_name} to database "
            f"({duplicates_skipped} duplicates skipped)"
        )
        return signals

    @staticmethod
    def compute_content_hash(content: str) -> str:
        """
        Compute SHA-256 hash of content for deduplication.

        Args:
            content: Content string to hash

        Returns:
            64-character hex digest
        """
        return hashlib.sha256(content.encode("utf-8")).hexdigest()

    async def run(self, session: AsyncSession) -> list[RawSignal]:
        """
        Execute the full scraping workflow.

        Convenience method that:
        1. Scrapes data from source
        2. Saves to database
        3. Returns created records

        Args:
            session: Async database session

        Returns:
            List of created RawSignal records

        Example:
            >>> async with AsyncSessionLocal() as session:
            >>>     signals = await scraper.run(session)
            >>>     await session.commit()
        """
        logger.info(f"Starting scraping workflow for {self.source_name}")

        try:
            # Step 1: Scrape data
            results = await self.scrape()
            logger.info(
                f"{self.source_name}: Scraped {len(results)} items"
            )

            # Step 2: Save to database
            signals = await self.save_to_database(session, results)

            logger.info(
                f"{self.source_name}: Workflow completed successfully. "
                f"Saved {len(signals)} signals"
            )
            return signals

        except Exception as e:
            logger.error(
                f"{self.source_name}: Scraping workflow failed: "
                f"{type(e).__name__} - {e}"
            )
            raise

    def log_scrape_summary(self, results: list[ScrapeResult]) -> None:
        """
        Log a summary of scraping results.

        Args:
            results: List of scrape results to summarize
        """
        if not results:
            logger.info(f"{self.source_name}: No data scraped")
            return

        total_content_length = sum(len(r.content) for r in results)
        avg_content_length = (
            total_content_length // len(results) if results else 0
        )

        logger.info(
            f"{self.source_name} Scrape Summary:\n"
            f"  - Items scraped: {len(results)}\n"
            f"  - Total content: {total_content_length:,} chars\n"
            f"  - Avg per item: {avg_content_length:,} chars"
        )

    @staticmethod
    def clean_text(text: str) -> str:
        """
        Clean and normalize text content.

        Args:
            text: Raw text to clean

        Returns:
            Cleaned text with normalized whitespace
        """
        if not text:
            return ""

        # Remove excessive whitespace
        text = " ".join(text.split())

        # Remove common artifacts
        text = text.replace("\r\n", "\n")
        text = text.replace("\r", "\n")

        # Remove multiple consecutive newlines
        while "\n\n\n" in text:
            text = text.replace("\n\n\n", "\n\n")

        return text.strip()

    @staticmethod
    def truncate_content(content: str, max_length: int = 50000) -> str:
        """
        Truncate content if it exceeds maximum length.

        Args:
            content: Content to truncate
            max_length: Maximum allowed length (default: 50000 chars)

        Returns:
            Truncated content with indicator if truncated
        """
        if len(content) <= max_length:
            return content

        logger.warning(
            f"Content truncated from {len(content)} to {max_length} chars"
        )
        return content[:max_length] + "\n\n[Content truncated...]"
