---
name: firecrawl-glue
description: Collection standard - ensures proper Firecrawl SDK usage instead of brittle scrapers. Use when working on web scraping logic.
---

# Firecrawl Integration Standards (The Collection Standard)

This skill ensures clean, maintainable web scraping using the Firecrawl SDK instead of brittle BeautifulSoup patterns.

## Trigger
Automatically applies when working on:
- `backend/app/scrapers/` - Web scraping implementations
- Any file involving web content extraction

## Rules

### 1. SDK-First Approach
- Always prioritize `firecrawl-py` SDK over raw HTTP calls
- NEVER write custom BeautifulSoup/lxml parsers unless absolutely necessary
- Use Firecrawl's API for content extraction

### 2. Markdown Output Format
- Request output in **markdown format** to optimize for LLM analysis
- Markdown is cleaner and more structured than raw HTML
- Example:
  ```python
  from firecrawl import FirecrawlApp

  app = FirecrawlApp(api_key=settings.FIRECRAWL_API_KEY)
  result = app.scrape_url(
      url=target_url,
      params={'formats': ['markdown']}
  )
  ```

### 3. Structured Data Models
- Implement a `ScrapeResult` Pydantic model for every scraper
- Normalize data before it hits the database
- Example:
  ```python
  from pydantic import BaseModel, Field, HttpUrl
  from datetime import datetime

  class ScrapeResult(BaseModel):
      url: HttpUrl
      title: str
      content: str = Field(..., description="Markdown-formatted content")
      scraped_at: datetime = Field(default_factory=datetime.utcnow)
      metadata: dict[str, Any] = Field(default_factory=dict)
  ```

### 4. 3-Tier Retry Logic
- Implement retry logic for 429 (Too Many Requests) and transient errors
- Use `tenacity` library for exponential backoff
- Example:
  ```python
  from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type
  import httpx

  @retry(
      stop=stop_after_attempt(3),
      wait=wait_exponential(multiplier=1, min=4, max=10),
      retry=retry_if_exception_type((httpx.HTTPStatusError, httpx.TimeoutException))
  )
  async def scrape_with_retry(url: str) -> ScrapeResult:
      # Firecrawl scraping logic here
      pass
  ```

### 5. Rate Limiting Compliance
- Respect Firecrawl's rate limits
- Implement backoff when receiving 429 responses
- Log rate limit headers for monitoring

## Standard Scraper Template

```python
from firecrawl import FirecrawlApp
from pydantic import BaseModel, HttpUrl
from tenacity import retry, stop_after_attempt, wait_exponential
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

class ScrapeResult(BaseModel):
    url: HttpUrl
    title: str
    content: str
    scraped_at: datetime
    metadata: dict

class BaseScraper:
    def __init__(self, api_key: str):
        self.client = FirecrawlApp(api_key=api_key)

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=4, max=10)
    )
    async def scrape(self, url: str) -> ScrapeResult:
        try:
            result = self.client.scrape_url(
                url=url,
                params={'formats': ['markdown']}
            )
            return ScrapeResult(
                url=url,
                title=result.get('metadata', {}).get('title', ''),
                content=result.get('markdown', ''),
                scraped_at=datetime.utcnow(),
                metadata=result.get('metadata', {})
            )
        except Exception as e:
            logger.error(f"Scrape failed for {url}: {e}")
            raise
```

## Anti-Patterns to Avoid
- ❌ Writing custom HTML parsers with BeautifulSoup
- ❌ Requesting raw HTML when markdown suffices
- ❌ No retry logic for transient failures
- ❌ Ignoring rate limits
- ❌ Unstructured scrape results (always use Pydantic models)

## Checklist
Before committing scraper code, verify:
- [ ] Uses `firecrawl-py` SDK
- [ ] Requests markdown format output
- [ ] Has a Pydantic `ScrapeResult` model
- [ ] Implements 3-tier retry logic with `tenacity`
- [ ] Handles rate limiting (429) gracefully
- [ ] Logs errors and rate limit info
