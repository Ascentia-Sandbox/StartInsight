"""Product Hunt scraper using Firecrawl with proper HTML parsing.

This module scrapes Product Hunt daily launches using Firecrawl
for web scraping and BeautifulSoup for HTML parsing.

Strategy:
1. Fetch Product Hunt homepage/daily page with Firecrawl
2. Parse HTML with BeautifulSoup to extract product cards
3. Return structured ScrapeResult objects

Note: Product Hunt has dynamic JS rendering, so we use Firecrawl's
wait_for parameter to ensure content loads before parsing.
"""

import logging
import re
from datetime import UTC, datetime, timedelta
from typing import Any

from bs4 import BeautifulSoup
from pydantic import HttpUrl

from app.scrapers import get_scraper_client
from app.scrapers.base_scraper import BaseScraper
from app.scrapers.firecrawl_client import ScrapeResult

logger = logging.getLogger(__name__)


class ProductHuntScraper(BaseScraper):
    """
    Scraper for Product Hunt daily launches.

    Scrapes:
    - Daily top products
    - Product descriptions and taglines
    - Upvote counts
    - Maker information

    Uses Firecrawl to handle JavaScript rendering and
    BeautifulSoup for HTML parsing.
    """

    PRODUCT_HUNT_BASE_URL = "https://www.producthunt.com"

    # CSS selectors for Product Hunt (updated for current site structure)
    # Note: These may need adjustment as PH updates their frontend
    SELECTORS = {
        # Product card container - using data attributes for stability
        "product_card": "[data-test='post-item'], article[class*='post'], div[class*='postItem']",
        # Product name within card
        "product_name": "[data-test='post-name'], h3, a[href*='/posts/'] > span:first-child",
        # Tagline
        "tagline": "[data-test='tagline'], p[class*='tagline'], div[class*='description']",
        # Vote button/count
        "vote_count": "[data-test='vote-button'], button[class*='vote'], span[class*='vote']",
        # Product link
        "product_link": "a[href*='/posts/']",
        # Maker info
        "maker": "[data-test='maker'], a[href*='/@']",
    }

    def __init__(
        self,
        days_back: int = 1,
        limit: int = 10,
        wait_for_js: int = 3000,
    ):
        """
        Initialize Product Hunt scraper.

        Args:
            days_back: Number of days to look back (default: 1 = today only)
            limit: Max products to scrape per day (default: 10)
            wait_for_js: Milliseconds to wait for JS rendering (default: 3000)
        """
        super().__init__(source_name="product_hunt")
        self.days_back = days_back
        self.limit = limit
        self.wait_for_js = wait_for_js
        self.scraper_client = get_scraper_client()  # Auto-selects based on config

        logger.info(
            f"Product Hunt scraper initialized "
            f"(days_back={days_back}, limit={limit}, wait_for_js={wait_for_js}ms)"
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
            target_date = datetime.now(UTC) - timedelta(days=days_ago)
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
        # For today, use main page; for historical, use leaderboard
        if date_str == datetime.now(UTC).strftime("%Y-%m-%d"):
            url = self.PRODUCT_HUNT_BASE_URL
        else:
            # Product Hunt archive URL format
            url = f"{self.PRODUCT_HUNT_BASE_URL}/leaderboard/daily/{date_str.replace('-', '/')}"

        logger.info(f"Scraping Product Hunt: {url}")

        try:
            # Use Firecrawl to get the page with JavaScript rendering
            # Request both markdown and HTML for different parsing strategies
            result = await self.scraper_client.scrape_url(url)

            # Try to get raw HTML from Firecrawl metadata if available
            html_content = result.metadata.get("rawHtml", "")

            if html_content:
                # Parse with BeautifulSoup
                products = self._extract_products_from_html(
                    html_content, date_str, url
                )
            else:
                # Fallback to markdown parsing with improved heuristics
                products = self._extract_products_from_markdown(
                    result.content, date_str, url
                )

            return products[:self.limit]

        except Exception as e:
            logger.error(f"Error scraping daily page {date_str}: {e}")
            return []

    def _extract_products_from_html(
        self,
        html_content: str,
        date_str: str,
        source_url: str,
    ) -> list[ScrapeResult]:
        """
        Extract product information from HTML using BeautifulSoup.

        Args:
            html_content: Raw HTML content
            date_str: Date string for metadata
            source_url: Source page URL

        Returns:
            List of ScrapeResult objects
        """
        results: list[ScrapeResult] = []
        soup = BeautifulSoup(html_content, "html.parser")

        # Try multiple selector strategies
        product_cards = self._find_product_cards(soup)

        if not product_cards:
            logger.warning(
                f"No product cards found in HTML for {date_str}. "
                f"Selectors may need updating."
            )
            return results

        logger.debug(f"Found {len(product_cards)} potential product cards")

        for card in product_cards:
            try:
                product = self._parse_product_card(card, date_str, source_url)
                if product:
                    results.append(product)
            except Exception as e:
                logger.debug(f"Error parsing product card: {e}")
                continue

        logger.info(f"Extracted {len(results)} products from HTML for {date_str}")
        return results

    def _find_product_cards(self, soup: BeautifulSoup) -> list[Any]:
        """
        Find product card elements using multiple selector strategies.

        Args:
            soup: BeautifulSoup parsed HTML

        Returns:
            List of product card elements
        """
        cards = []

        # Try data-test attribute first (most stable)
        cards = soup.select("[data-test='post-item']")
        if cards:
            return cards

        # Try class-based selectors
        for selector in [
            "article[class*='post']",
            "div[class*='postItem']",
            "div[class*='ProductItem']",
            "li[class*='post']",
        ]:
            cards = soup.select(selector)
            if cards:
                return cards

        # Try finding by structure (product link + vote button)
        potential_cards = soup.find_all(
            lambda tag: (
                tag.name in ("div", "article", "li")
                and tag.find("a", href=re.compile(r"/posts/"))
                and tag.find(lambda t: "vote" in str(t.get("class", [])).lower())
            )
        )
        if potential_cards:
            return potential_cards

        return []

    def _parse_product_card(
        self,
        card: Any,
        date_str: str,
        source_url: str,
    ) -> ScrapeResult | None:
        """
        Parse a single product card element.

        Args:
            card: BeautifulSoup element for product card
            date_str: Date string
            source_url: Source page URL

        Returns:
            ScrapeResult or None if parsing fails
        """
        # Extract product name
        name = None
        name_elem = (
            card.select_one(self.SELECTORS["product_name"])
            or card.select_one("h3")
            or card.select_one("a[href*='/posts/'] > span")
        )
        if name_elem:
            name = name_elem.get_text(strip=True)

        if not name:
            return None

        # Extract tagline
        tagline = ""
        tagline_elem = (
            card.select_one(self.SELECTORS["tagline"])
            or card.select_one("p")
        )
        if tagline_elem:
            tagline = tagline_elem.get_text(strip=True)

        # Extract product URL
        link_elem = card.select_one(self.SELECTORS["product_link"])
        if link_elem and link_elem.get("href"):
            href = link_elem["href"]
            if href.startswith("/"):
                product_url = f"{self.PRODUCT_HUNT_BASE_URL}{href}"
            else:
                product_url = href
        else:
            # Generate a fallback URL
            slug = self._slugify(name)
            product_url = f"{self.PRODUCT_HUNT_BASE_URL}/posts/{slug}"

        # Extract upvote count
        upvotes = 0
        vote_elem = card.select_one(self.SELECTORS["vote_count"])
        if vote_elem:
            vote_text = vote_elem.get_text(strip=True)
            upvotes = self._parse_number(vote_text)

        # Extract maker info
        maker = None
        maker_elem = card.select_one(self.SELECTORS["maker"])
        if maker_elem:
            maker = maker_elem.get_text(strip=True)

        # Create markdown content for analysis
        content = self._format_product_content(
            name=name,
            tagline=tagline,
            upvotes=upvotes,
            maker=maker,
            url=product_url,
        )

        return ScrapeResult(
            url=HttpUrl(product_url),
            title=name,
            content=content,
            metadata={
                "source": "product_hunt",
                "date": date_str,
                "source_page": source_url,
                "name": name,
                "tagline": tagline,
                "upvotes": upvotes,
                "maker": maker,
                "scraped_at": datetime.now(UTC).isoformat(),
            },
        )

    def _extract_products_from_markdown(
        self,
        markdown_content: str,
        date_str: str,
        source_url: str,
    ) -> list[ScrapeResult]:
        """
        Extract products from markdown content (fallback method).

        Uses improved heuristics to identify product sections.

        Args:
            markdown_content: Markdown content from Firecrawl
            date_str: Date string for metadata
            source_url: Source page URL

        Returns:
            List of ScrapeResult objects
        """
        results: list[ScrapeResult] = []

        # Split content into sections by headers or dividers
        sections = re.split(r'\n(?=#{1,3}\s|\*{3,}|\-{3,})', markdown_content)

        for section in sections:
            if len(section.strip()) < 50:  # Skip short sections
                continue

            # Look for product patterns
            # Pattern 1: Header followed by description
            header_match = re.match(r'^#{1,3}\s+(.+?)(?:\n|$)', section)
            if header_match:
                name = header_match.group(1).strip()

                # Clean up common suffixes
                name = re.sub(r'\s*[-|]\s*Product Hunt.*$', '', name, flags=re.IGNORECASE)
                name = name.strip()

                if len(name) < 3 or len(name) > 100:
                    continue

                # Extract tagline (first paragraph after header)
                lines = section.split('\n')
                tagline = ""
                for line in lines[1:]:
                    line = line.strip()
                    if line and not line.startswith('#') and not line.startswith('*'):
                        tagline = line[:200]
                        break

                # Extract upvotes if present
                upvote_match = re.search(r'(\d+(?:,\d+)*)\s*(?:upvotes?|votes?)', section, re.IGNORECASE)
                upvotes = self._parse_number(upvote_match.group(1)) if upvote_match else 0

                # Generate URL
                slug = self._slugify(name)
                product_url = f"{self.PRODUCT_HUNT_BASE_URL}/posts/{slug}"

                content = self._format_product_content(
                    name=name,
                    tagline=tagline,
                    upvotes=upvotes,
                    maker=None,
                    url=product_url,
                )

                results.append(ScrapeResult(
                    url=HttpUrl(product_url),
                    title=name,
                    content=content,
                    metadata={
                        "source": "product_hunt",
                        "date": date_str,
                        "source_page": source_url,
                        "name": name,
                        "tagline": tagline,
                        "upvotes": upvotes,
                        "scraped_at": datetime.now(UTC).isoformat(),
                        "extraction_method": "markdown_fallback",
                    },
                ))

        logger.info(
            f"Extracted {len(results)} products from markdown for {date_str} "
            f"(fallback method)"
        )
        return results

    @staticmethod
    def _format_product_content(
        name: str,
        tagline: str,
        upvotes: int,
        maker: str | None,
        url: str,
    ) -> str:
        """
        Format product data as markdown content for LLM analysis.

        Args:
            name: Product name
            tagline: Product tagline
            upvotes: Upvote count
            maker: Maker name/username
            url: Product URL

        Returns:
            Formatted markdown content
        """
        content_parts = [
            f"# {name}",
            "",
            tagline if tagline else "No tagline available.",
            "",
            "---",
            f"**Upvotes:** {upvotes:,}",
        ]

        if maker:
            content_parts.append(f"**Maker:** {maker}")

        content_parts.extend([
            f"**URL:** {url}",
            "",
            "## Analysis Context",
            "",
            "This product was launched on Product Hunt and received "
            f"{upvotes:,} upvotes, indicating market interest and validation.",
        ])

        return "\n".join(content_parts)

    @staticmethod
    def _parse_number(text: str) -> int:
        """
        Parse number from text, handling K/M suffixes.

        Args:
            text: Text containing number (e.g., "1.2K", "500", "2M")

        Returns:
            Parsed integer value
        """
        if not text:
            return 0

        text = text.strip().upper()

        # Remove non-numeric characters except K, M, and decimal point
        text = re.sub(r'[^\d.KM]', '', text)

        try:
            if 'K' in text:
                return int(float(text.replace('K', '')) * 1000)
            elif 'M' in text:
                return int(float(text.replace('M', '')) * 1000000)
            else:
                return int(float(text)) if text else 0
        except (ValueError, TypeError):
            return 0

    @staticmethod
    def _slugify(text: str) -> str:
        """
        Convert text to URL-safe slug.

        Args:
            text: Text to slugify

        Returns:
            URL-safe slug
        """
        # Convert to lowercase
        slug = text.lower()
        # Replace spaces and special chars with hyphens
        slug = re.sub(r'[^\w\s-]', '', slug)
        slug = re.sub(r'[-\s]+', '-', slug)
        # Remove leading/trailing hyphens
        slug = slug.strip('-')
        return slug[:50]  # Limit length

    async def scrape_single_product(self, product_url: str) -> ScrapeResult:
        """
        Scrape a single product page for detailed information.

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
            result = await self.scraper_client.scrape_url(product_url)

            # Extract product name from title
            product_name = result.title.replace(" - Product Hunt", "").strip()

            return ScrapeResult(
                url=HttpUrl(product_url),
                title=product_name,
                content=self.clean_text(result.content),
                metadata={
                    **result.metadata,
                    "source": "product_hunt",
                    "scraped_at": datetime.now(UTC).isoformat(),
                },
            )

        except Exception as e:
            logger.error(f"Error scraping product {product_url}: {e}")
            raise
