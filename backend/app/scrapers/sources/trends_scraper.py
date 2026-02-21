"""Google Trends scraper using pytrends."""

import asyncio
import logging
import random

import pandas as pd
from pydantic import HttpUrl
from pytrends.request import TrendReq

from app.scrapers.base_scraper import BaseScraper
from app.scrapers.firecrawl_client import ScrapeResult

logger = logging.getLogger(__name__)

# Default delay between API calls (seconds)
DEFAULT_BATCH_DELAY = 30.0
# Maximum retries for 429 errors
MAX_RETRIES = 3
# Base delay for exponential backoff (seconds)
BACKOFF_BASE = 5.0


class GoogleTrendsScraper(BaseScraper):
    """
    Scraper for Google Trends search volume data.

    Tracks:
    - Search volume for startup/SaaS keywords
    - Rising search queries
    - Regional interest
    - Related queries

    Uses pytrends (unofficial Google Trends API).
    """

    # Default keywords to track for startup trends
    DEFAULT_KEYWORDS = [
        "AI startup",
        "SaaS product",
        "no code",
        "API integration",
        "automation tool",
        "project management software",
        "CRM software",
        "email marketing",
        "startup idea",
        "side hustle",
    ]

    def __init__(
        self,
        keywords: list[str] | None = None,
        timeframe: str = "now 7-d",
        geo: str = "US",
    ):
        """
        Initialize Google Trends scraper.

        Args:
            keywords: List of keywords to track (default: DEFAULT_KEYWORDS)
            timeframe: Timeframe for trends (default: "now 7-d" = last 7 days)
                      Options: "now 1-d", "now 7-d", "today 1-m", "today 3-m", "today 12-m"
            geo: Geographic location (default: "US")
                 Options: "" (worldwide), "US", "GB", "CA", etc.
        """
        super().__init__(source_name="google_trends")

        self.keywords = keywords or self.DEFAULT_KEYWORDS
        self.timeframe = timeframe
        self.geo = geo

        # Initialize pytrends client
        self.pytrends = TrendReq(hl="en-US", tz=360)

        logger.info(
            f"Google Trends scraper initialized "
            f"(keywords={len(self.keywords)}, timeframe={timeframe}, geo={geo})"
        )

    async def scrape(self) -> list[ScrapeResult]:
        """
        Scrape Google Trends data for configured keywords.

        Returns:
            List of ScrapeResult objects with trend data

        Example:
            >>> scraper = GoogleTrendsScraper(keywords=["AI startup", "SaaS"])
            >>> results = await scraper.scrape()
            >>> print(f"Scraped trends for {len(results)} keywords")
        """
        all_results: list[ScrapeResult] = []

        # Process keywords in batches of 5 (Google Trends API limit)
        batch_size = 5
        for i in range(0, len(self.keywords), batch_size):
            batch = self.keywords[i : i + batch_size]

            # Retry with exponential backoff for rate limits
            for retry in range(MAX_RETRIES):
                try:
                    results = await self._scrape_keyword_batch(batch)
                    all_results.extend(results)
                    logger.info(
                        f"Scraped trends for batch: {', '.join(batch)}"
                    )
                    break  # Success, exit retry loop
                except Exception as e:
                    error_str = str(e).lower()
                    if "429" in error_str or "too many" in error_str:
                        # Rate limited - exponential backoff with jitter
                        delay = BACKOFF_BASE * (2 ** retry) + random.uniform(0, 1)
                        logger.warning(
                            f"Rate limited (attempt {retry + 1}/{MAX_RETRIES}), "
                            f"waiting {delay:.1f}s before retry"
                        )
                        await asyncio.sleep(delay)
                        if retry == MAX_RETRIES - 1:
                            logger.error(
                                f"Max retries exceeded for batch {batch}: {e}"
                            )
                    else:
                        logger.error(
                            f"Error scraping trends for batch {batch}: "
                            f"{type(e).__name__} - {e}"
                        )
                        break  # Non-retryable error

            # Add delay between batches to avoid rate limits
            if i + batch_size < len(self.keywords):
                await asyncio.sleep(DEFAULT_BATCH_DELAY)

        # Also get rising queries (with delay to avoid rate limits)
        await asyncio.sleep(DEFAULT_BATCH_DELAY)
        try:
            rising_results = await self._scrape_rising_queries()
            all_results.extend(rising_results)
        except Exception as e:
            error_str = str(e).lower()
            if "429" in error_str or "too many" in error_str:
                logger.warning(f"Rising queries rate limited, skipping: {e}")
            else:
                logger.error(f"Error scraping rising queries: {e}")

        self.log_scrape_summary(all_results)
        return all_results

    async def _scrape_keyword_batch(self, keywords: list[str]) -> list[ScrapeResult]:
        """
        Scrape trends for a batch of keywords.

        Args:
            keywords: List of keywords (max 5)

        Returns:
            List of ScrapeResult objects
        """
        results: list[ScrapeResult] = []

        try:
            # Build payload for pytrends
            self.pytrends.build_payload(
                keywords, cat=0, timeframe=self.timeframe, geo=self.geo
            )

            # Get interest over time
            interest_df = self.pytrends.interest_over_time()

            if interest_df.empty:
                logger.warning(f"No data returned for keywords: {keywords}")
                return results

            # Create result for each keyword
            for keyword in keywords:
                if keyword not in interest_df.columns:
                    continue

                # Extract trend data
                keyword_data = interest_df[keyword]
                avg_interest = int(keyword_data.mean())
                max_interest = int(keyword_data.max())
                current_interest = int(keyword_data.iloc[-1])

                # Calculate trend direction
                trend_direction = self._calculate_trend_direction(keyword_data)

                # Build markdown content
                content = self._build_trend_markdown(
                    keyword=keyword,
                    avg_interest=avg_interest,
                    max_interest=max_interest,
                    current_interest=current_interest,
                    trend_direction=trend_direction,
                    data_points=keyword_data.to_dict(),
                )

                # Create metadata
                metadata = {
                    "keyword": keyword,
                    "avg_interest": avg_interest,
                    "max_interest": max_interest,
                    "current_interest": current_interest,
                    "trend_direction": trend_direction,
                    "timeframe": self.timeframe,
                    "geo": self.geo,
                    "data_points": len(keyword_data),
                }

                result = ScrapeResult(
                    url=HttpUrl(f"https://trends.google.com/trends/explore?q={keyword.replace(' ', '+')}"),
                    title=f"Google Trends: {keyword}",
                    content=content,
                    metadata=metadata,
                )

                results.append(result)
                logger.debug(
                    f"Scraped trends for '{keyword}': "
                    f"avg={avg_interest}, current={current_interest}, trend={trend_direction}"
                )

        except Exception as e:
            logger.error(f"Error fetching trend data for {keywords}: {e}")
            raise

        return results

    async def _scrape_rising_queries(self) -> list[ScrapeResult]:
        """
        Scrape rising (trending) search queries.

        Returns:
            List of ScrapeResult objects for rising queries
        """
        results: list[ScrapeResult] = []

        try:
            # Build payload for related queries
            self.pytrends.build_payload(
                [self.keywords[0]],  # Use first keyword as seed
                cat=0,
                timeframe=self.timeframe,
                geo=self.geo,
            )

            # Get rising queries
            related_queries = self.pytrends.related_queries()

            if not related_queries:
                return results

            # Extract rising queries
            for keyword, data in related_queries.items():
                if data is None or "rising" not in data:
                    continue

                rising_df = data["rising"]
                if rising_df is None or rising_df.empty:
                    continue

                # Build content from rising queries
                content = self._build_rising_queries_markdown(rising_df)

                metadata = {
                    "seed_keyword": keyword,
                    "num_rising_queries": len(rising_df),
                    "timeframe": self.timeframe,
                    "geo": self.geo,
                }

                result = ScrapeResult(
                    url=HttpUrl(f"https://trends.google.com/trends/explore?q={keyword.replace(' ', '+')}"),
                    title=f"Rising Queries for: {keyword}",
                    content=content,
                    metadata=metadata,
                )

                results.append(result)

        except Exception as e:
            logger.error(f"Error fetching rising queries: {e}")

        return results

    @staticmethod
    def _calculate_trend_direction(data: pd.Series) -> str:
        """
        Calculate trend direction (rising, falling, stable).

        Args:
            data: Pandas Series of trend data over time

        Returns:
            "rising", "falling", or "stable"
        """
        if len(data) < 2:
            return "stable"

        # Compare recent average vs older average
        midpoint = len(data) // 2
        older_avg = data.iloc[:midpoint].mean()
        recent_avg = data.iloc[midpoint:].mean()

        diff_pct = ((recent_avg - older_avg) / older_avg * 100) if older_avg > 0 else 0

        if diff_pct > 10:
            return "rising"
        elif diff_pct < -10:
            return "falling"
        else:
            return "stable"

    @staticmethod
    def _build_trend_markdown(
        keyword: str,
        avg_interest: int,
        max_interest: int,
        current_interest: int,
        trend_direction: str,
        data_points: dict,
    ) -> str:
        """Build markdown content for trend data."""
        content = [
            f"# Google Trends: {keyword}\n",
            f"**Trend Direction**: {trend_direction.upper()}",
            f"**Average Interest**: {avg_interest}/100",
            f"**Peak Interest**: {max_interest}/100",
            f"**Current Interest**: {current_interest}/100\n",
            "## Analysis",
        ]

        if trend_direction == "rising":
            content.append(
                f"✅ **Rising Trend**: '{keyword}' search volume is increasing, "
                "indicating growing market interest."
            )
        elif trend_direction == "falling":
            content.append(
                f"⚠️ **Falling Trend**: '{keyword}' search volume is decreasing."
            )
        else:
            content.append(
                f"📊 **Stable Trend**: '{keyword}' search volume is relatively stable."
            )

        return "\n\n".join(content)

    @staticmethod
    def _build_rising_queries_markdown(rising_df: pd.DataFrame) -> str:
        """Build markdown content for rising queries."""
        content = [
            "# Rising Search Queries\n",
            "The following queries are showing significant growth:\n",
        ]

        for idx, row in rising_df.head(10).iterrows():
            query = row["query"]
            value = row.get("value", "N/A")
            content.append(f"- **{query}** (+{value})")

        return "\n".join(content)
