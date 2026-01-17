"""Product Hunt scraper using Firecrawl."""

import logging
from datetime import datetime, timedelta

from pydantic import HttpUrl

from app.scrapers.base_scraper import BaseScraper
from app.scrapers.firecrawl_client import ScrapeResult, get_firecrawl_client

logger = logging.getLogger(__name__)


class ProductHuntScraper(BaseScraper):
    """
    Scraper for Product Hunt daily launches.

    Scrapes:
    - Daily top products
    - Product descriptions and taglines
    - Upvote counts
    - Comment discussions

    Uses Firecrawl to convert Product Hunt pages into clean markdown.
    """

    PRODUCT_HUNT_BASE_URL = "https://www.producthunt.com"

    def __init__(self, days_back: int = 1, limit: int = 10):
        """
        Initialize Product Hunt scraper.

        Args:
            days_back: Number of days to look back (default: 1 = today only)
            limit: Max products to scrape per day (default: 10)
        """
        super().__init__(source_name="product_hunt")
        self.days_back = days_back
        self.limit = limit
        self.firecrawl = get_firecrawl_client()

        logger.info(
            f"Product Hunt scraper initialized "
            f"(days_back={days_back}, limit={limit})"
        )

    async def scrape(self) -> list[ScrapeResult]:
        """
        Scrape Product Hunt for daily top products.

        Returns:
            List of ScrapeResult objects with product details

        Example:
            >>> scraper = ProductHuntScraper(days_back=1, limit=5)
            >>> results = await scraper.scrape()
            >>> print(f"Scraped {len(results)} products")
        """
        all_results: list[ScrapeResult] = []

        # Scrape products from each day
        for days_ago in range(self.days_back):
            target_date = datetime.utcnow() - timedelta(days=days_ago)
            date_str = target_date.strftime("%Y-%m-%d")

            try:
                results = await self._scrape_daily_products(date_str)
                all_results.extend(results)
                logger.info(
                    f"Scraped {len(results)} products from Product Hunt ({date_str})"
                )
            except Exception as e:
                logger.error(
                    f"Error scraping Product Hunt for {date_str}: "
                    f"{type(e).__name__} - {e}"
                )
                continue

        self.log_scrape_summary(all_results)
        return all_results

    async def _scrape_daily_products(self, date_str: str) -> list[ScrapeResult]:
        """
        Scrape products for a specific date.

        Args:
            date_str: Date in YYYY-MM-DD format

        Returns:
            List of ScrapeResult objects
        """
        # Product Hunt daily URL format
        daily_url = f"{self.PRODUCT_HUNT_BASE_URL}/posts/{date_str}"

        logger.info(f"Scraping Product Hunt daily page: {daily_url}")

        try:
            # Use Firecrawl to get the daily page content
            daily_page_result = await self.firecrawl.scrape_url(daily_url)

            # Extract product information from the markdown content
            products = self._extract_products_from_markdown(
                daily_page_result.content, date_str
            )

            return products[:self.limit]

        except Exception as e:
            logger.error(f"Error scraping daily page {date_str}: {e}")
            return []

    def _extract_products_from_markdown(
        self, markdown_content: str, date_str: str
    ) -> list[ScrapeResult]:
        """
        Extract product information from Product Hunt page markdown.

        Note: This is a simplified parser. In production, you might want to:
        - Use Product Hunt's official API (requires approval)
        - Use more sophisticated HTML/markdown parsing
        - Implement selectors for specific product elements

        Args:
            markdown_content: Markdown content from Firecrawl
            date_str: Date string for metadata

        Returns:
            List of ScrapeResult objects
        """
        results: list[ScrapeResult] = []

        # Simple heuristic: Split by product sections
        # Note: This is a placeholder - real implementation would need
        # more sophisticated parsing based on actual Product Hunt structure

        lines = markdown_content.split("\n")
        current_product = []
        product_url = None

        for line in lines:
            # Detect product headings (simplified heuristic)
            if line.startswith("#") and len(current_product) > 5:
                # Save previous product
                if current_product and product_url:
                    content = "\n".join(current_product)
                    title = current_product[0].replace("#", "").strip()

                    result = ScrapeResult(
                        url=HttpUrl(product_url),
                        title=title,
                        content=self.clean_text(content),
                        metadata={
                            "date": date_str,
                            "source_page": f"{self.PRODUCT_HUNT_BASE_URL}/posts/{date_str}",
                        },
                    )
                    results.append(result)

                # Start new product
                current_product = [line]
                product_url = f"{self.PRODUCT_HUNT_BASE_URL}/posts/product-{len(results)+1}"

            else:
                current_product.append(line)

        # Add last product
        if current_product and product_url:
            content = "\n".join(current_product)
            title = current_product[0].replace("#", "").strip()

            result = ScrapeResult(
                url=HttpUrl(product_url),
                title=title,
                content=self.clean_text(content),
                metadata={
                    "date": date_str,
                    "source_page": f"{self.PRODUCT_HUNT_BASE_URL}/posts/{date_str}",
                },
            )
            results.append(result)

        logger.info(
            f"Extracted {len(results)} products from markdown for {date_str}"
        )
        return results

    async def scrape_single_product(self, product_url: str) -> ScrapeResult:
        """
        Scrape a single product page.

        Useful for getting detailed information about a specific product.

        Args:
            product_url: Full URL to product page

        Returns:
            ScrapeResult with product details

        Example:
            >>> scraper = ProductHuntScraper()
            >>> result = await scraper.scrape_single_product(
            ...     "https://www.producthunt.com/posts/example-product"
            ... )
        """
        logger.info(f"Scraping single product: {product_url}")

        try:
            result = await self.firecrawl.scrape_url(product_url)

            # Extract product name from title
            product_name = result.title.replace(" - Product Hunt", "").strip()

            return ScrapeResult(
                url=HttpUrl(product_url),
                title=product_name,
                content=self.clean_text(result.content),
                metadata={
                    **result.metadata,
                    "scraped_at": datetime.utcnow().isoformat(),
                },
            )

        except Exception as e:
            logger.error(f"Error scraping product {product_url}: {e}")
            raise
