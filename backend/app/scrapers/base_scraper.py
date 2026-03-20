"""Base scraper class with common logic for all scrapers.

This module provides the abstract base class for all data scrapers,
including common functionality for:
- Saving raw data to database
- Logging scraping activity
- Error handling with retry logic
- Rate limiting integration
- Data deduplication
- Per-scraper circuit breakers (Phase 6.1A)
"""

import hashlib
import logging
import time
from abc import ABC, abstractmethod
from collections.abc import Callable
from enum import Enum

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
from app.scrapers.firecrawl_client import ScrapeResult  # Shared by both clients

logger = logging.getLogger(__name__)


# ============================================================
# Phase 6.1A: Per-Scraper Circuit Breakers
# ============================================================


class CircuitState(str, Enum):
    """Circuit breaker states."""

    CLOSED = "closed"  # Normal operation — requests flow through
    OPEN = "open"  # Failures exceeded threshold — requests blocked
    HALF_OPEN = "half_open"  # Cooldown expired — allow one probe request


class CircuitBreaker:
    """Per-scraper circuit breaker with Redis-backed state.

    Pattern: 2 consecutive failures → 15min cooldown → half-open (1 probe) → close on success.

    Redis keys:
        scraper:circuit:{source}:state — CLOSED/OPEN/HALF_OPEN
        scraper:circuit:{source}:failures — consecutive failure count
        scraper:circuit:{source}:opened_at — timestamp when circuit opened
    """

    FAILURE_THRESHOLD = 2
    COOLDOWN_SECONDS = 900  # 15 minutes

    def __init__(self, source_name: str):
        self.source_name = source_name
        self._key_prefix = f"scraper:circuit:{source_name}"

    async def _get_redis(self):
        from app.core.cache import get_redis

        return await get_redis()

    async def get_state(self) -> CircuitState:
        """Get current circuit state, auto-transitioning OPEN → HALF_OPEN after cooldown."""
        try:
            r = await self._get_redis()
            state = await r.get(f"{self._key_prefix}:state")
            if state is None:
                return CircuitState.CLOSED

            if state == CircuitState.OPEN:
                opened_at = await r.get(f"{self._key_prefix}:opened_at")
                if opened_at and (time.time() - float(opened_at)) >= self.COOLDOWN_SECONDS:
                    await r.set(f"{self._key_prefix}:state", CircuitState.HALF_OPEN)
                    logger.info(
                        f"Circuit breaker {self.source_name}: OPEN → HALF_OPEN (cooldown expired)"
                    )
                    return CircuitState.HALF_OPEN

            return CircuitState(state)
        except Exception as e:
            logger.warning(f"Circuit breaker read error for {self.source_name}: {e}")
            return CircuitState.CLOSED  # Fail open — allow requests if Redis is down

    async def can_execute(self) -> bool:
        """Check if a request is allowed through the circuit."""
        state = await self.get_state()
        if state == CircuitState.CLOSED:
            return True
        if state == CircuitState.HALF_OPEN:
            return True  # Allow one probe request
        # OPEN — blocked
        logger.info(f"Circuit breaker {self.source_name}: OPEN — request blocked")
        return False

    async def record_success(self) -> None:
        """Record a successful request. Resets failures and closes circuit."""
        try:
            r = await self._get_redis()
            state = await r.get(f"{self._key_prefix}:state")
            pipe = r.pipeline()
            pipe.set(f"{self._key_prefix}:state", CircuitState.CLOSED)
            pipe.set(f"{self._key_prefix}:failures", "0")
            pipe.delete(f"{self._key_prefix}:opened_at")
            await pipe.execute()
            if state and state != CircuitState.CLOSED:
                logger.info(f"Circuit breaker {self.source_name}: {state} → CLOSED (success)")
        except Exception as e:
            logger.warning(f"Circuit breaker write error for {self.source_name}: {e}")

    async def record_failure(self) -> None:
        """Record a failed request. Opens circuit after threshold exceeded."""
        try:
            r = await self._get_redis()
            failures = await r.incr(f"{self._key_prefix}:failures")
            if failures >= self.FAILURE_THRESHOLD:
                await r.set(f"{self._key_prefix}:state", CircuitState.OPEN)
                await r.set(f"{self._key_prefix}:opened_at", str(time.time()))
                logger.warning(
                    f"Circuit breaker {self.source_name}: CLOSED → OPEN "
                    f"({failures} consecutive failures, cooldown {self.COOLDOWN_SECONDS}s)"
                )
        except Exception as e:
            logger.warning(f"Circuit breaker write error for {self.source_name}: {e}")


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
                existing_query = select(RawSignal).where(RawSignal.content_hash == content_hash)
                existing_result = await session.execute(existing_query)
                existing = existing_result.scalar_one_or_none()

                if existing:
                    logger.debug(
                        f"Duplicate content skipped: {result.url} (matches signal {existing.id})"
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
                    logger.debug(f"Duplicate URL skipped: {result.url}")
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

                logger.debug(f"Added signal from {self.source_name}: {result.title or result.url}")

            except Exception as e:
                logger.error(f"Error creating signal for {result.url}: {type(e).__name__} - {e}")
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
            logger.info(f"{self.source_name}: Scraped {len(results)} items")

            # Step 2: Save to database
            signals = await self.save_to_database(session, results)

            logger.info(
                f"{self.source_name}: Workflow completed successfully. Saved {len(signals)} signals"
            )
            return signals

        except Exception as e:
            logger.error(f"{self.source_name}: Scraping workflow failed: {type(e).__name__} - {e}")
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
        avg_content_length = total_content_length // len(results) if results else 0

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

        logger.warning(f"Content truncated from {len(content)} to {max_length} chars")
        return content[:max_length] + "\n\n[Content truncated...]"
