"""Competitor URL validation service.

This module validates that competitor URLs are reachable and resolve
correctly, preventing LLM hallucination of non-existent competitor
websites.

Uses httpx for async HTTP HEAD requests with redirect following.
"""

import asyncio
import logging
from dataclasses import dataclass
from urllib.parse import urlparse

import httpx

logger = logging.getLogger(__name__)


@dataclass
class URLValidationResult:
    """Result of URL validation."""

    url: str
    valid: bool
    final_url: str | None
    status_code: int | None
    redirect_count: int
    response_time_ms: float | None
    error: str | None = None


@dataclass
class CompetitorData:
    """Competitor data structure."""

    name: str
    url: str
    description: str
    market_position: str | None = None


class URLValidator:
    """
    Validate competitor URLs are reachable and resolve correctly.

    Features:
    - Async HTTP HEAD requests for efficiency
    - Follows redirects to get final URL
    - Configurable timeout and retry
    - Caching to avoid repeated validation
    - Domain normalization
    """

    def __init__(
        self,
        timeout: float = 10.0,
        max_redirects: int = 5,
        verify_ssl: bool = True,
        user_agent: str = "StartInsight URL Validator/1.0",
    ):
        """
        Initialize URL validator.

        Args:
            timeout: Request timeout in seconds
            max_redirects: Maximum redirects to follow
            verify_ssl: Whether to verify SSL certificates
            user_agent: User-Agent header value
        """
        self._timeout = timeout
        self._max_redirects = max_redirects
        self._verify_ssl = verify_ssl
        self._user_agent = user_agent
        self._cache: dict[str, URLValidationResult] = {}

    def _normalize_url(self, url: str) -> str:
        """
        Normalize URL for consistent handling.

        Args:
            url: URL to normalize

        Returns:
            Normalized URL with scheme
        """
        url = url.strip()

        # Add scheme if missing
        if not url.startswith(("http://", "https://")):
            url = "https://" + url

        # Parse and reconstruct to normalize
        parsed = urlparse(url)
        if not parsed.netloc:
            raise ValueError(f"Invalid URL: cannot parse netloc from {url}")

        # Reconstruct with normalized parts
        normalized = f"{parsed.scheme}://{parsed.netloc}"
        if parsed.path and parsed.path != "/":
            normalized += parsed.path.rstrip("/")
        if parsed.query:
            normalized += f"?{parsed.query}"

        return normalized

    def _is_valid_url_format(self, url: str) -> tuple[bool, str | None]:
        """
        Check if URL has valid format.

        Args:
            url: URL to validate

        Returns:
            Tuple of (is_valid, error_message)
        """
        try:
            parsed = urlparse(url)

            if not parsed.scheme:
                return (False, "Missing URL scheme (http:// or https://)")

            if parsed.scheme not in ("http", "https"):
                return (False, f"Invalid scheme: {parsed.scheme}")

            if not parsed.netloc:
                return (False, "Missing domain/netloc")

            # Check for common invalid patterns
            if parsed.netloc.startswith(".") or parsed.netloc.endswith("."):
                return (False, "Invalid domain format")

            if " " in parsed.netloc:
                return (False, "Domain contains spaces")

            return (True, None)

        except Exception as e:
            return (False, f"URL parse error: {e}")

    async def validate_url(
        self,
        url: str,
        use_cache: bool = True,
    ) -> URLValidationResult:
        """
        Validate that a URL is reachable and returns a valid response.

        Args:
            url: URL to validate
            use_cache: Whether to use cached results

        Returns:
            URLValidationResult with validation status and details
        """
        # Normalize URL
        try:
            normalized_url = self._normalize_url(url)
        except ValueError as e:
            return URLValidationResult(
                url=url,
                valid=False,
                final_url=None,
                status_code=None,
                redirect_count=0,
                response_time_ms=None,
                error=str(e),
            )

        # Check cache
        if use_cache and normalized_url in self._cache:
            logger.debug(f"Cache hit for URL: {normalized_url}")
            return self._cache[normalized_url]

        # Validate URL format
        is_valid, format_error = self._is_valid_url_format(normalized_url)
        if not is_valid:
            result = URLValidationResult(
                url=url,
                valid=False,
                final_url=None,
                status_code=None,
                redirect_count=0,
                response_time_ms=None,
                error=format_error,
            )
            self._cache[normalized_url] = result
            return result

        # Make HTTP request
        try:
            async with httpx.AsyncClient(
                timeout=self._timeout,
                follow_redirects=True,
                max_redirects=self._max_redirects,
                verify=self._verify_ssl,
            ) as client:
                import time
                start_time = time.perf_counter()

                # Use HEAD request for efficiency
                response = await client.head(
                    normalized_url,
                    headers={"User-Agent": self._user_agent},
                )

                response_time_ms = (time.perf_counter() - start_time) * 1000

                # Check if response is successful (2xx or 3xx)
                is_valid = response.status_code < 400

                result = URLValidationResult(
                    url=url,
                    valid=is_valid,
                    final_url=str(response.url),
                    status_code=response.status_code,
                    redirect_count=len(response.history),
                    response_time_ms=round(response_time_ms, 2),
                    error=None if is_valid else f"HTTP {response.status_code}",
                )

                logger.info(
                    f"URL validation {'passed' if is_valid else 'failed'}: "
                    f"{url} -> {response.status_code} "
                    f"(final: {response.url}, {response_time_ms:.0f}ms)"
                )

        except httpx.TimeoutException:
            result = URLValidationResult(
                url=url,
                valid=False,
                final_url=None,
                status_code=None,
                redirect_count=0,
                response_time_ms=None,
                error=f"Timeout after {self._timeout}s",
            )
            logger.debug(f"URL timeout: {url}")

        except httpx.TooManyRedirects:
            result = URLValidationResult(
                url=url,
                valid=False,
                final_url=None,
                status_code=None,
                redirect_count=self._max_redirects,
                response_time_ms=None,
                error=f"Too many redirects (max: {self._max_redirects})",
            )
            logger.debug(f"URL too many redirects: {url}")

        except httpx.ConnectError as e:
            result = URLValidationResult(
                url=url,
                valid=False,
                final_url=None,
                status_code=None,
                redirect_count=0,
                response_time_ms=None,
                error=f"Connection error: {e}",
            )
            logger.debug(f"URL connection error: {url} - {e}")

        except httpx.HTTPError as e:
            result = URLValidationResult(
                url=url,
                valid=False,
                final_url=None,
                status_code=None,
                redirect_count=0,
                response_time_ms=None,
                error=f"HTTP error: {type(e).__name__}",
            )
            logger.debug(f"URL HTTP error: {url} - {e}")

        except Exception as e:
            result = URLValidationResult(
                url=url,
                valid=False,
                final_url=None,
                status_code=None,
                redirect_count=0,
                response_time_ms=None,
                error=f"Unexpected error: {type(e).__name__}",
            )
            logger.error(f"Unexpected URL validation error: {url} - {e}")

        # Cache result
        self._cache[normalized_url] = result
        return result

    async def validate_competitor(
        self,
        competitor: dict,
    ) -> tuple[dict, bool]:
        """
        Validate a single competitor's URL and update with final URL.

        Args:
            competitor: Competitor dictionary with 'url' field

        Returns:
            Tuple of (updated_competitor, is_valid)
        """
        url = competitor.get("url", "")
        if not url:
            return (competitor, False)

        result = await self.validate_url(url)

        if result.valid:
            # Update URL with final URL (after redirects)
            competitor["url"] = result.final_url or url
            return (competitor, True)
        else:
            logger.warning(
                f"Invalid competitor URL: {url} ({result.error})"
            )
            return (competitor, False)

    async def validate_competitors(
        self,
        competitors: list[dict],
    ) -> tuple[list[dict], int, int]:
        """
        Validate all competitors' URLs and return only valid ones.

        Args:
            competitors: List of competitor dictionaries

        Returns:
            Tuple of (valid_competitors, valid_count, invalid_count)
        """
        if not competitors:
            return ([], 0, 0)

        valid_competitors = []
        valid_count = 0
        invalid_count = 0

        # Validate concurrently with semaphore to limit connections
        semaphore = asyncio.Semaphore(5)  # Max 5 concurrent requests

        async def validate_with_semaphore(comp):
            async with semaphore:
                return await self.validate_competitor(comp.copy())

        results = await asyncio.gather(
            *[validate_with_semaphore(c) for c in competitors],
            return_exceptions=True,
        )

        for result in results:
            if isinstance(result, Exception):
                invalid_count += 1
                logger.error(f"Competitor validation exception: {result}")
                continue

            competitor, is_valid = result
            if is_valid:
                valid_competitors.append(competitor)
                valid_count += 1
            else:
                invalid_count += 1

        logger.info(
            f"Competitor URL validation: {valid_count} valid, "
            f"{invalid_count} invalid out of {len(competitors)} total"
        )

        return (valid_competitors, valid_count, invalid_count)

    async def batch_validate_urls(
        self,
        urls: list[str],
        max_concurrent: int = 10,
    ) -> list[URLValidationResult]:
        """
        Validate multiple URLs concurrently.

        Args:
            urls: List of URLs to validate
            max_concurrent: Maximum concurrent validations

        Returns:
            List of URLValidationResult in same order as input
        """
        semaphore = asyncio.Semaphore(max_concurrent)

        async def validate_with_semaphore(url):
            async with semaphore:
                return await self.validate_url(url)

        results = await asyncio.gather(
            *[validate_with_semaphore(url) for url in urls],
            return_exceptions=True,
        )

        # Convert exceptions to failed results
        processed_results = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                processed_results.append(URLValidationResult(
                    url=urls[i],
                    valid=False,
                    final_url=None,
                    status_code=None,
                    redirect_count=0,
                    response_time_ms=None,
                    error=f"Validation exception: {type(result).__name__}",
                ))
            else:
                processed_results.append(result)

        return processed_results

    def clear_cache(self) -> None:
        """Clear the validation cache."""
        self._cache.clear()
        logger.info("URL validator cache cleared")

    def get_cache_stats(self) -> dict:
        """Get cache statistics."""
        return {
            "cached_urls": len(self._cache),
            "valid_cached": sum(1 for r in self._cache.values() if r.valid),
            "invalid_cached": sum(1 for r in self._cache.values() if not r.valid),
        }


# Global validator instance
_url_validator: URLValidator | None = None


def get_url_validator() -> URLValidator:
    """
    Get or create global URL validator instance.

    Returns:
        URLValidator: Singleton validator instance
    """
    global _url_validator
    if _url_validator is None:
        _url_validator = URLValidator()
    return _url_validator
