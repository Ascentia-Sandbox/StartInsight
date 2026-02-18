"""Tests for Product Hunt scraper.

Tests:
1. HTML parsing with BeautifulSoup
2. Markdown fallback parsing
3. ScrapeResult type compliance
4. Number parsing (K/M suffixes)
5. URL slugification
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from pydantic import HttpUrl

from app.scrapers.sources.product_hunt_scraper import ProductHuntScraper
from app.scrapers.firecrawl_client import ScrapeResult


class TestProductHuntScraper:
    """Test ProductHuntScraper class."""

    @pytest.fixture
    def scraper(self):
        """Create Product Hunt scraper instance."""
        with patch.object(ProductHuntScraper, '__init__', lambda x: None):
            scraper = ProductHuntScraper.__new__(ProductHuntScraper)
            scraper.source_name = "product_hunt"
            scraper.days_back = 1
            scraper.limit = 10
            scraper.wait_for_js = 3000
            scraper.firecrawl = MagicMock()
            scraper.PRODUCT_HUNT_BASE_URL = "https://www.producthunt.com"
            scraper.SELECTORS = ProductHuntScraper.SELECTORS
            return scraper

    def test_parse_number_handles_plain_integer(self, scraper):
        """Test number parsing with plain integers."""
        assert scraper._parse_number("123") == 123
        assert scraper._parse_number("0") == 0
        assert scraper._parse_number("999") == 999

    def test_parse_number_handles_k_suffix(self, scraper):
        """Test number parsing with K suffix."""
        assert scraper._parse_number("1K") == 1000
        assert scraper._parse_number("1.5K") == 1500
        assert scraper._parse_number("2.3k") == 2300

    def test_parse_number_handles_m_suffix(self, scraper):
        """Test number parsing with M suffix."""
        assert scraper._parse_number("1M") == 1000000
        assert scraper._parse_number("2.5M") == 2500000
        assert scraper._parse_number("0.5m") == 500000

    def test_parse_number_handles_whitespace(self, scraper):
        """Test number parsing strips whitespace."""
        assert scraper._parse_number("  123  ") == 123
        assert scraper._parse_number("\t1K\n") == 1000

    def test_parse_number_handles_special_chars(self, scraper):
        """Test number parsing removes special characters."""
        assert scraper._parse_number("1,234") == 1234
        assert scraper._parse_number("▲ 567") == 567

    def test_parse_number_returns_zero_for_empty(self, scraper):
        """Test number parsing returns 0 for empty string."""
        assert scraper._parse_number("") == 0
        assert scraper._parse_number(None) == 0

    def test_slugify_basic_text(self, scraper):
        """Test slugification of basic text."""
        assert scraper._slugify("Hello World") == "hello-world"
        assert scraper._slugify("My Product") == "my-product"

    def test_slugify_special_characters(self, scraper):
        """Test slugification removes special characters."""
        assert scraper._slugify("Test!@#$%") == "test"
        assert scraper._slugify("Product (v2.0)") == "product-v20"

    def test_slugify_limits_length(self, scraper):
        """Test slugification limits to 50 characters."""
        long_name = "A" * 100
        slug = scraper._slugify(long_name)
        assert len(slug) <= 50

    def test_slugify_handles_consecutive_spaces(self, scraper):
        """Test slugification handles multiple spaces."""
        assert scraper._slugify("Hello   World") == "hello-world"

    def test_format_product_content(self, scraper):
        """Test product content formatting."""
        content = scraper._format_product_content(
            name="Test Product",
            tagline="The best test product ever",
            upvotes=1234,
            maker="@testmaker",
            url="https://example.com",
        )

        assert "# Test Product" in content
        assert "The best test product ever" in content
        assert "**Upvotes:** 1,234" in content
        assert "**Maker:** @testmaker" in content
        assert "**URL:** https://example.com" in content

    def test_format_product_content_without_maker(self, scraper):
        """Test product content formatting without maker."""
        content = scraper._format_product_content(
            name="Test Product",
            tagline="A tagline",
            upvotes=100,
            maker=None,
            url="https://example.com",
        )

        assert "**Maker:**" not in content

    def test_format_product_content_without_tagline(self, scraper):
        """Test product content formatting without tagline."""
        content = scraper._format_product_content(
            name="Test Product",
            tagline="",
            upvotes=100,
            maker=None,
            url="https://example.com",
        )

        assert "No tagline available" in content

    @pytest.mark.asyncio
    async def test_scrape_returns_scrape_result_list(self, scraper):
        """Test that scrape returns list of ScrapeResult."""
        # Mock the internal methods
        mock_result = ScrapeResult(
            url=HttpUrl("https://www.producthunt.com/posts/test"),
            title="Test Product",
            content="# Test\n\nTest content",
            metadata={"source": "product_hunt"},
        )

        with patch.object(scraper, '_scrape_daily_products', new_callable=AsyncMock) as mock_scrape:
            mock_scrape.return_value = [mock_result]

            results = await scraper.scrape()

            assert isinstance(results, list)
            assert len(results) == 1
            assert isinstance(results[0], ScrapeResult)

    def test_extract_products_from_markdown_basic(self, scraper):
        """Test markdown extraction with basic structure."""
        markdown = """# Product One

A great product tagline.

Some more description.

---

# Product Two

Another product.

500 upvotes received.
"""
        results = scraper._extract_products_from_markdown(
            markdown,
            "2024-01-15",
            "https://www.producthunt.com",
        )

        assert len(results) == 2
        assert results[0].title == "Product One"
        assert isinstance(results[0], ScrapeResult)

    def test_extract_products_from_markdown_filters_short_sections(self, scraper):
        """Test that short sections are filtered out."""
        markdown = """# Short

Hi.

# Valid Product

This is a valid product with a longer description that provides enough context.
"""
        results = scraper._extract_products_from_markdown(
            markdown,
            "2024-01-15",
            "https://www.producthunt.com",
        )

        # Should only include the valid product with longer content
        assert len(results) == 1
        assert results[0].title == "Valid Product"

    def test_extract_products_from_markdown_cleans_title(self, scraper):
        """Test that Product Hunt suffix is removed from titles."""
        markdown = """# Cool App - Product Hunt

The best cool app.

Long description goes here.
"""
        results = scraper._extract_products_from_markdown(
            markdown,
            "2024-01-15",
            "https://www.producthunt.com",
        )

        assert results[0].title == "Cool App"


class TestProductHuntHTMLParsing:
    """Test HTML parsing functionality."""

    @pytest.fixture
    def scraper(self):
        """Create scraper for HTML tests."""
        with patch.object(ProductHuntScraper, '__init__', lambda x: None):
            scraper = ProductHuntScraper.__new__(ProductHuntScraper)
            scraper.source_name = "product_hunt"
            scraper.PRODUCT_HUNT_BASE_URL = "https://www.producthunt.com"
            scraper.SELECTORS = ProductHuntScraper.SELECTORS
            return scraper

    def test_find_product_cards_with_data_test(self, scraper):
        """Test finding product cards with data-test attribute."""
        from bs4 import BeautifulSoup

        html = """
        <div>
            <div data-test="post-item">Product 1</div>
            <div data-test="post-item">Product 2</div>
        </div>
        """
        soup = BeautifulSoup(html, "html.parser")
        cards = scraper._find_product_cards(soup)

        assert len(cards) == 2

    def test_find_product_cards_fallback_to_class(self, scraper):
        """Test fallback to class-based selectors."""
        from bs4 import BeautifulSoup

        html = """
        <div>
            <article class="postItem-abc123">Product 1</article>
            <article class="postItem-def456">Product 2</article>
        </div>
        """
        soup = BeautifulSoup(html, "html.parser")
        cards = scraper._find_product_cards(soup)

        assert len(cards) == 2

    def test_parse_product_card_extracts_name(self, scraper):
        """Test product name extraction from card."""
        from bs4 import BeautifulSoup

        html = """
        <div data-test="post-item">
            <span data-test="post-name">Amazing Product</span>
            <p data-test="tagline">Best tagline ever</p>
            <a href="/posts/amazing-product">Link</a>
            <button data-test="vote-button">250</button>
        </div>
        """
        soup = BeautifulSoup(html, "html.parser")
        card = soup.select_one("[data-test='post-item']")

        result = scraper._parse_product_card(card, "2024-01-15", "https://www.producthunt.com")

        assert result is not None
        assert result.title == "Amazing Product"

    def test_parse_product_card_returns_none_without_name(self, scraper):
        """Test that cards without names return None."""
        from bs4 import BeautifulSoup

        html = """
        <div data-test="post-item">
            <p>No name here</p>
        </div>
        """
        soup = BeautifulSoup(html, "html.parser")
        card = soup.select_one("[data-test='post-item']")

        result = scraper._parse_product_card(card, "2024-01-15", "https://www.producthunt.com")

        assert result is None
