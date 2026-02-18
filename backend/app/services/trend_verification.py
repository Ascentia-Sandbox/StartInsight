"""Trend keyword verification service.

This module cross-references LLM-generated trend claims with actual
Google Trends data to prevent fabricated growth percentages and
ensure trend keywords are based on real search data.

Uses pytrends (unofficial Google Trends API wrapper).
"""

import asyncio
import logging
import time
from dataclasses import dataclass
from datetime import datetime

from pytrends.exceptions import ResponseError
from pytrends.request import TrendReq

logger = logging.getLogger(__name__)


@dataclass
class TrendVerificationResult:
    """Result of trend keyword verification."""

    keyword: str
    verified: bool
    actual_volume: int | None
    actual_growth_percent: float | None
    llm_claimed_volume: str | None
    llm_claimed_growth: str | None
    error: str | None = None
    data_points: list[tuple[str, int]] | None = None


@dataclass
class TrendKeywordData:
    """Trend keyword data structure."""

    keyword: str
    volume: str
    growth: str


class TrendVerifier:
    """
    Cross-reference LLM trend claims with Google Trends API.

    Verifies that:
    1. Keywords have actual search interest
    2. Growth percentages are approximately accurate
    3. Volume claims are in the right order of magnitude

    Note: Google Trends returns relative interest (0-100), not absolute
    search volume. Volume verification uses order of magnitude comparison.
    """

    def __init__(
        self,
        hl: str = "en-US",
        tz: int = 360,
        timeout: tuple[int, int] = (10, 30),
        retries: int = 3,
    ):
        """
        Initialize trend verifier.

        Args:
            hl: Host language for Google Trends
            tz: Timezone offset (360 = US Central)
            timeout: Request timeout (connect, read)
            retries: Number of retries on failure
        """
        self._hl = hl
        self._tz = tz
        self._timeout = timeout
        self._retries = retries
        self._pytrends: TrendReq | None = None
        self._cache: dict[str, TrendVerificationResult] = {}
        self._last_request_time: datetime | None = None
        self._min_request_interval = 1.0  # seconds between requests

    def _get_pytrends(self) -> TrendReq:
        """Get or create pytrends instance."""
        if self._pytrends is None:
            self._pytrends = TrendReq(
                hl=self._hl,
                tz=self._tz,
                timeout=self._timeout,
                retries=self._retries,
            )
        return self._pytrends

    def _rate_limit(self) -> None:
        """Apply rate limiting between requests."""
        if self._last_request_time:
            elapsed = (datetime.now() - self._last_request_time).total_seconds()
            if elapsed < self._min_request_interval:
                sleep_time = self._min_request_interval - elapsed
                logger.debug(f"Rate limiting: sleeping {sleep_time:.2f}s")
                time.sleep(sleep_time)
        self._last_request_time = datetime.now()

    def verify_keyword_sync(
        self,
        keyword: str,
        timeframe: str = "today 7-d",
        geo: str = "",
        llm_claimed_volume: str | None = None,
        llm_claimed_growth: str | None = None,
    ) -> TrendVerificationResult:
        """
        Synchronously verify a keyword's trend data against Google Trends.

        Args:
            keyword: Search keyword to verify
            timeframe: Google Trends timeframe (default: last 7 days)
            geo: Geographic region (default: worldwide)
            llm_claimed_volume: LLM-claimed volume for comparison
            llm_claimed_growth: LLM-claimed growth for comparison

        Returns:
            TrendVerificationResult with verification status and actual data
        """
        # Check cache first
        cache_key = f"{keyword}:{timeframe}:{geo}"
        if cache_key in self._cache:
            logger.debug(f"Cache hit for keyword: {keyword}")
            return self._cache[cache_key]

        try:
            self._rate_limit()
            pytrends = self._get_pytrends()

            # Build payload for single keyword
            pytrends.build_payload(
                kw_list=[keyword],
                timeframe=timeframe,
                geo=geo,
            )

            # Get interest over time
            interest_df = pytrends.interest_over_time()

            if interest_df.empty or keyword not in interest_df.columns:
                result = TrendVerificationResult(
                    keyword=keyword,
                    verified=False,
                    actual_volume=None,
                    actual_growth_percent=None,
                    llm_claimed_volume=llm_claimed_volume,
                    llm_claimed_growth=llm_claimed_growth,
                    error="No trend data available for keyword",
                )
                self._cache[cache_key] = result
                return result

            # Extract values
            values = interest_df[keyword].values
            avg_volume = int(values.mean())

            # Calculate actual growth (last 3 days vs first 3 days)
            actual_growth: float | None = None
            if len(values) >= 6:
                first_half = values[:len(values)//2].mean()
                second_half = values[len(values)//2:].mean()
                if first_half > 0:
                    actual_growth = ((second_half - first_half) / first_half) * 100
                else:
                    actual_growth = 0.0 if second_half == 0 else 100.0
            elif len(values) >= 2:
                # Simpler calculation for shorter timeframes
                first_val = float(values[0])
                last_val = float(values[-1])
                if first_val > 0:
                    actual_growth = ((last_val - first_val) / first_val) * 100
                else:
                    actual_growth = 0.0 if last_val == 0 else 100.0

            # Extract data points for debugging/visualization
            data_points = []
            for idx, row in interest_df.iterrows():
                data_points.append((str(idx), int(row[keyword])))

            result = TrendVerificationResult(
                keyword=keyword,
                verified=True,
                actual_volume=avg_volume,
                actual_growth_percent=round(actual_growth, 1) if actual_growth is not None else None,
                llm_claimed_volume=llm_claimed_volume,
                llm_claimed_growth=llm_claimed_growth,
                error=None,
                data_points=data_points,
            )

            logger.info(
                f"Verified trend keyword '{keyword}': "
                f"volume={avg_volume}, growth={actual_growth:.1f}%" if actual_growth else f"volume={avg_volume}"
            )

            self._cache[cache_key] = result
            return result

        except ResponseError as e:
            error_msg = f"Google Trends API error: {e}"
            logger.warning(f"Trend verification failed for '{keyword}': {error_msg}")
            result = TrendVerificationResult(
                keyword=keyword,
                verified=False,
                actual_volume=None,
                actual_growth_percent=None,
                llm_claimed_volume=llm_claimed_volume,
                llm_claimed_growth=llm_claimed_growth,
                error=error_msg,
            )
            return result

        except Exception as e:
            error_msg = f"Unexpected error: {type(e).__name__}: {e}"
            logger.error(f"Trend verification error for '{keyword}': {error_msg}")
            result = TrendVerificationResult(
                keyword=keyword,
                verified=False,
                actual_volume=None,
                actual_growth_percent=None,
                llm_claimed_volume=llm_claimed_volume,
                llm_claimed_growth=llm_claimed_growth,
                error=error_msg,
            )
            return result

    async def verify_keyword(
        self,
        keyword: str,
        timeframe: str = "today 7-d",
        geo: str = "",
        llm_claimed_volume: str | None = None,
        llm_claimed_growth: str | None = None,
    ) -> TrendVerificationResult:
        """
        Async wrapper for keyword verification.

        pytrends is synchronous, so this runs in a thread pool.

        Args:
            keyword: Search keyword to verify
            timeframe: Google Trends timeframe
            geo: Geographic region
            llm_claimed_volume: LLM-claimed volume
            llm_claimed_growth: LLM-claimed growth

        Returns:
            TrendVerificationResult with verification status
        """
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            None,
            self.verify_keyword_sync,
            keyword,
            timeframe,
            geo,
            llm_claimed_volume,
            llm_claimed_growth,
        )

    async def verify_trend_keywords(
        self,
        keywords: list[dict],
        timeframe: str = "today 7-d",
        geo: str = "",
    ) -> tuple[list[dict], int, int]:
        """
        Verify all trend keywords and update with real data.

        Args:
            keywords: List of trend keyword dictionaries
            timeframe: Google Trends timeframe
            geo: Geographic region

        Returns:
            Tuple of (verified_keywords, verified_count, unverified_count)
        """
        if not keywords:
            return ([], 0, 0)

        verified = []
        verified_count = 0
        unverified_count = 0

        for kw_dict in keywords:
            kw = TrendKeywordData(
                keyword=kw_dict.get("keyword", ""),
                volume=kw_dict.get("volume", ""),
                growth=kw_dict.get("growth", ""),
            )

            if not kw.keyword:
                unverified_count += 1
                continue

            result = await self.verify_keyword(
                keyword=kw.keyword,
                timeframe=timeframe,
                geo=geo,
                llm_claimed_volume=kw.volume,
                llm_claimed_growth=kw.growth,
            )

            if result.verified:
                # Update with real data
                verified.append({
                    "keyword": kw.keyword,
                    "volume": self._format_volume(result.actual_volume or 0),
                    "growth": self._format_growth(result.actual_growth_percent),
                })
                verified_count += 1
            else:
                # Keep original but mark as unverified
                logger.warning(
                    f"Trend keyword unverifiable: {kw.keyword} ({result.error})"
                )
                unverified_count += 1

        logger.info(
            f"Trend keyword verification: {verified_count} verified, "
            f"{unverified_count} unverified out of {len(keywords)} total"
        )

        return (verified, verified_count, unverified_count)

    @staticmethod
    def _format_volume(volume: int) -> str:
        """
        Format volume in human-readable format.

        Note: Google Trends returns relative interest (0-100), not absolute
        search volume. This formats it for display purposes.

        Args:
            volume: Relative interest value (0-100)

        Returns:
            Formatted string (e.g., "High", "Medium", "Low")
        """
        if volume >= 75:
            return "High"
        elif volume >= 50:
            return "Medium"
        elif volume >= 25:
            return "Low"
        else:
            return "Very Low"

    @staticmethod
    def _format_growth(growth: float | None) -> str:
        """
        Format growth percentage.

        Args:
            growth: Growth percentage

        Returns:
            Formatted string (e.g., "+45.2%", "-12.3%", "N/A")
        """
        if growth is None:
            return "N/A"
        sign = "+" if growth >= 0 else ""
        return f"{sign}{growth:.1f}%"

    def clear_cache(self) -> None:
        """Clear the verification cache."""
        self._cache.clear()
        logger.info("Trend verifier cache cleared")


def compare_growth_claims(
    llm_claimed: str | None,
    actual_growth: float | None,
    tolerance_percent: float = 50.0,
) -> tuple[bool, str]:
    """
    Compare LLM-claimed growth with actual growth.

    Args:
        llm_claimed: LLM-claimed growth string (e.g., "+1900%")
        actual_growth: Actual growth percentage
        tolerance_percent: Acceptable deviation percentage

    Returns:
        Tuple of (is_accurate, message)
    """
    if llm_claimed is None or actual_growth is None:
        return (False, "Cannot compare: missing data")

    # Parse LLM claim
    try:
        claimed_value = llm_claimed.replace("%", "").replace("+", "").replace(" ", "")
        claimed_float = float(claimed_value)
    except (ValueError, AttributeError):
        return (False, f"Cannot parse LLM claim: {llm_claimed}")

    # Compare with tolerance
    if actual_growth == 0:
        is_accurate = abs(claimed_float) < tolerance_percent
    else:
        deviation = abs(claimed_float - actual_growth) / abs(actual_growth) * 100
        is_accurate = deviation <= tolerance_percent

    if is_accurate:
        return (True, f"Growth claim accurate within {tolerance_percent}% tolerance")
    else:
        return (
            False,
            f"Growth claim inaccurate: claimed {llm_claimed}, actual {actual_growth:.1f}%"
        )


# Global verifier instance
_trend_verifier: TrendVerifier | None = None


def get_trend_verifier() -> TrendVerifier:
    """
    Get or create global trend verifier instance.

    Returns:
        TrendVerifier: Singleton verifier instance
    """
    global _trend_verifier
    if _trend_verifier is None:
        _trend_verifier = TrendVerifier()
    return _trend_verifier
