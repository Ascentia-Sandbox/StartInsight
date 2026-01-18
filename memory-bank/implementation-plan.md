# Implementation Plan: StartInsight

## Overview
This document breaks down the StartInsight project into **3 distinct implementation phases**, each corresponding to one of the three core loops (Data Collection → Analysis → Presentation). Each phase is designed to be independently testable and deployable.

**Development Strategy**: Build vertically, not horizontally. Each phase should produce a working end-to-end slice before moving to the next.

---

## Phase 1: The "Collector" (Data Collection Loop)
**Goal**: Build a functional FastAPI backend that can scrape web data, store it in PostgreSQL, and expose it via REST API.

**Success Criteria**:
- The scraper runs successfully and stores raw data in the database.
- A GET endpoint returns stored raw signals.
- The system runs locally using Docker Compose.

### Phase 1 Checklist

#### 1.1 Project Initialization
- [ ] Initialize Git repository with `.gitignore` (Python, Node, .env files)
- [ ] Create project structure:
  ```
  StartInsight/
  ├── backend/            # FastAPI app
  ├── frontend/           # Next.js app (placeholder for Phase 3)
  ├── memory-bank/        # Documentation
  └── docker-compose.yml  # Local dev environment
  ```
- [ ] Set up Python environment using `uv` or `poetry`
- [ ] Create `backend/pyproject.toml` with core dependencies:
  - fastapi, uvicorn, pydantic, pydantic-settings
  - sqlalchemy[asyncio], alembic, asyncpg
  - redis, arq
  - firecrawl-py, praw, pytrends
  - python-dotenv, httpx

#### 1.2 Database Setup
- [ ] Create `docker-compose.yml` with PostgreSQL and Redis services
- [ ] Initialize SQLAlchemy async engine in `backend/app/database.py`
- [ ] Create database models in `backend/app/models/`:
  - `RawSignal` model:
    - `id` (UUID, primary key)
    - `source` (str: "reddit", "product_hunt", etc.)
    - `url` (str: source URL)
    - `content` (text: scraped markdown)
    - `metadata` (JSON: upvotes, comments, etc.)
    - `created_at` (timestamp)
    - `processed` (bool: default False)
- [ ] Set up Alembic for migrations:
  - `alembic init alembic`
  - Create initial migration for `raw_signals` table
  - Run migration: `alembic upgrade head`

#### 1.3 Firecrawl Integration (Web Scraper)
- [ ] Create `backend/app/scrapers/firecrawl_client.py`:
  - Initialize Firecrawl client with API key from env
  - Implement `scrape_url(url: str) -> dict` method
  - Handle rate limiting and errors
- [ ] Create `backend/app/scrapers/sources/`:
  - `reddit_scraper.py`: Scrape r/startups, r/SaaS (using PRAW + Firecrawl)
  - `product_hunt_scraper.py`: Scrape top launches (using Firecrawl)
  - `trends_scraper.py`: Fetch Google Trends data (using pytrends)
- [ ] Implement base `Scraper` class with common logic:
  - Save raw data to database
  - Log scraping activity
  - Error handling and retries

#### 1.4 Task Queue Setup (Arq)
- [ ] Create `backend/app/worker.py`:
  - Define `WorkerSettings` (Redis connection)
  - Register scraper tasks:
    - `scrape_reddit_task()`
    - `scrape_product_hunt_task()`
    - `scrape_trends_task()`
- [ ] Create `backend/app/tasks/scheduler.py`:
  - **Implementation Pattern** (APScheduler with Arq integration):
    ```python
    from apscheduler.schedulers.asyncio import AsyncIOScheduler
    from apscheduler.triggers.interval import IntervalTrigger
    from arq import create_pool
    from arq.connections import RedisSettings

    scheduler = AsyncIOScheduler()

    async def schedule_scraping_tasks():
        """Schedule all scraping tasks to run every 6 hours."""
        redis = await create_pool(RedisSettings())

        # Schedule scraping tasks
        scheduler.add_job(
            func=redis.enqueue_job,
            args=('scrape_reddit_task',),
            trigger=IntervalTrigger(hours=6),
            id='scrape_reddit',
            replace_existing=True
        )

        scheduler.add_job(
            func=redis.enqueue_job,
            args=('scrape_product_hunt_task',),
            trigger=IntervalTrigger(hours=6),
            id='scrape_product_hunt',
            replace_existing=True
        )

        scheduler.add_job(
            func=redis.enqueue_job,
            args=('scrape_trends_task',),
            trigger=IntervalTrigger(hours=6),
            id='scrape_trends',
            replace_existing=True
        )

        scheduler.start()
    ```
  - **Dependencies**: Add `apscheduler>=3.10.0` to `pyproject.toml`
  - **Startup**: Call `schedule_scraping_tasks()` in FastAPI `@app.on_event("startup")` hook
- [ ] Test task execution:
  - Run worker: `arq app.worker.WorkerSettings`
  - Verify tasks execute and store data in DB

#### 1.5 FastAPI Endpoints
- [ ] Create `backend/app/main.py`:
  - Initialize FastAPI app with CORS middleware
  - Health check endpoint: `GET /health`
- [ ] Create `backend/app/api/routes/signals.py`:
  - `GET /api/signals`: List all raw signals (with pagination)
  - `GET /api/signals/{id}`: Get single signal by ID
  - Query params: `?source=reddit&limit=20&offset=0`
- [ ] Create Pydantic response schemas in `backend/app/schemas/`:
  - `RawSignalResponse` (maps to database model)
  - `PaginatedResponse[T]` (generic pagination wrapper)

#### 1.6 Environment & Configuration
- [ ] Create `.env.example` with required keys:
  ```
  DATABASE_URL=postgresql+asyncpg://user:pass@localhost/startinsight
  REDIS_URL=redis://localhost:6379
  FIRECRAWL_API_KEY=your_key_here
  REDDIT_CLIENT_ID=your_key_here
  REDDIT_CLIENT_SECRET=your_key_here
  ANTHROPIC_API_KEY=your_key_here  # For Phase 2
  ```
- [ ] Create `backend/app/config.py` using `pydantic-settings`:
  - Load all environment variables
  - Validate required keys on startup

#### 1.7 Testing & Validation
- [ ] Write unit tests for scrapers (mock Firecrawl/PRAW responses)
- [ ] Write integration tests for API endpoints
- [ ] Test full scraping pipeline:
  - Run scrapers manually
  - Verify data appears in PostgreSQL
  - Query data via FastAPI endpoints
- [ ] Docker validation:
  - Ensure `docker-compose up` starts all services
  - Run migrations automatically on startup

#### 1.8 Documentation
- [ ] Create `backend/README.md` with:
  - Setup instructions
  - Environment variables reference
  - How to run scrapers manually
  - API endpoint documentation (or link to Swagger UI)

---

## Phase 2: The "Analyst" (Analysis Loop)
**Goal**: Integrate LLM agents to process raw signals into structured insights.

**Success Criteria**:
- Raw signals are automatically processed by an AI agent.
- Structured insights are stored in a new `insights` table.
- A GET endpoint returns ranked insights.

### Phase 2 Checklist

#### 2.1 Database Schema Extension
- [ ] Create `Insight` model in `backend/app/models/insight.py`:
  - `id` (UUID, primary key)
  - `raw_signal_id` (Foreign key to `RawSignal`)
  - `problem_statement` (text)
  - `proposed_solution` (text)
  - `market_size_estimate` (str: "Small", "Medium", "Large")
  - `relevance_score` (float: 0.0 - 1.0)
  - `competitor_analysis` (JSON: list of competitors)
  - `created_at` (timestamp)
- [ ] Create Alembic migration for `insights` table
- [ ] Run migration: `alembic upgrade head`

#### 2.2 AI Agent Implementation (PydanticAI)
- [ ] Create `backend/app/agents/analyzer.py`:
  - Initialize PydanticAI agent with Claude 3.5 Sonnet
  - Define `InsightSchema` (Pydantic model for structured output)
  - Implement `analyze_signal(raw_content: str) -> InsightSchema`
  - Add prompt template:
    ```
    Analyze this market signal and extract:
    1. Problem Statement
    2. Proposed Solution
    3. Market Size (Small/Medium/Large)
    4. Relevance Score (0.0-1.0)
    5. Top 3 Competitors (if any)

    Signal:
    {raw_content}
    ```
  - **Competitor Schema** (Pydantic model for structured competitor data):
    ```python
    from pydantic import BaseModel, HttpUrl
    from typing import Literal, Optional

    class Competitor(BaseModel):
        """Individual competitor entry in the analysis."""
        name: str  # Competitor company/product name
        url: HttpUrl  # Competitor website URL
        description: str  # Brief description of what they do
        market_position: Optional[Literal["Small", "Medium", "Large"]] = None  # Estimated market presence

    class InsightSchema(BaseModel):
        """Structured output from LLM analysis."""
        problem_statement: str
        proposed_solution: str
        market_size_estimate: Literal["Small", "Medium", "Large"]
        relevance_score: float  # 0.0 - 1.0
        competitor_analysis: list[Competitor]  # Max 3 competitors
        title: str  # Auto-generated from problem/solution
    ```
- [ ] Implement validation and error handling:
  - **Concrete Implementation Pattern**:
    ```python
    from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type
    from pydantic import ValidationError
    from anthropic import AnthropicError, RateLimitError
    import logging

    logger = logging.getLogger(__name__)

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=1, max=10),
        retry=retry_if_exception_type((AnthropicError, ValidationError)),
        reraise=True
    )
    async def analyze_signal(raw_signal: RawSignal) -> Insight:
        """
        Analyze a raw signal and extract structured insights.
        Retries up to 3 times with exponential backoff.
        """
        try:
            # Call PydanticAI agent
            result = await agent.run(raw_signal.content)

            # Validate output schema
            insight_data = InsightSchema.model_validate(result.data)

            # Save to database
            insight = Insight(
                raw_signal_id=raw_signal.id,
                problem_statement=insight_data.problem_statement,
                proposed_solution=insight_data.proposed_solution,
                market_size_estimate=insight_data.market_size_estimate,
                relevance_score=insight_data.relevance_score,
                competitor_analysis=insight_data.competitor_analysis,
                title=insight_data.title
            )

            logger.info(f"Successfully analyzed signal {raw_signal.id}")
            return insight

        except ValidationError as e:
            # LLM returned invalid JSON structure
            logger.warning(f"LLM validation error for signal {raw_signal.id}: {e}")
            raise  # Retry

        except RateLimitError as e:
            # Rate limit hit - fallback to GPT-4o
            logger.warning(f"Claude rate limit hit, falling back to GPT-4o")
            return await fallback_gpt4o_analysis(raw_signal)

        except AnthropicError as e:
            # Other Anthropic API errors
            logger.error(f"Anthropic API error: {e}")
            raise  # Retry

        except Exception as e:
            # Unexpected errors - log and skip
            logger.error(f"Unexpected error analyzing signal {raw_signal.id}: {e}")
            raise

    async def fallback_gpt4o_analysis(raw_signal: RawSignal) -> Insight:
        """Fallback to GPT-4o if Claude fails."""
        # Similar implementation with OpenAI SDK
        pass
    ```
  - **Dependencies**: Add `tenacity>=8.2.0` to `pyproject.toml`
  - **Logging**: All LLM interactions logged with timestamps and token usage

#### 2.3 Analysis Task Queue
- [ ] Add analysis task to `backend/app/worker.py`:
  - `analyze_signals_task()`: Fetch unprocessed signals, run analysis, save insights
  - Batch processing (process 10 signals at a time)
  - Mark signals as `processed=True` after analysis
- [ ] Create `backend/app/tasks/analysis_scheduler.py`:
  - Trigger analysis task after scraping completes
  - Run every 6 hours (right after scraping)

#### 2.4 Insights API Endpoints
- [ ] Create `backend/app/api/routes/insights.py`:
  - `GET /api/insights`: List insights (sorted by relevance_score DESC)
  - `GET /api/insights/{id}`: Get single insight with related raw signal
  - `GET /api/insights/daily-top`: Top 5 insights of the day
  - Query params: `?min_score=0.7&limit=20&offset=0`
- [ ] Create Pydantic schemas in `backend/app/schemas/insight.py`:
  - `InsightResponse` (includes related raw signal data)
  - `InsightListResponse` (paginated)

#### 2.5 Testing & Validation
- [ ] Unit tests for AI agent:
  - Mock LLM responses
  - Validate Pydantic schema parsing
- [ ] Integration tests:
  - Run full pipeline: scrape → analyze → retrieve insights
  - Verify insights are correctly linked to raw signals
- [ ] Manual testing:
  - Run analysis on real scraped data
  - Verify relevance scores are reasonable
  - Check competitor analysis accuracy

#### 2.6 Monitoring & Logging
- [ ] Add structured logging for LLM calls:
  - Log prompt, response, tokens used, latency
  - Track API costs (tokens × price per token)
- [ ] Create `backend/app/monitoring/metrics.py`:
  - Track: total insights generated, average relevance score, API errors

---

## Phase 3: The "Dashboard" (Presentation Loop)
**Goal**: Build a Next.js frontend to display insights to the end user.

**Success Criteria**:
- Users can view the top 5 insights of the day.
- Users can click an insight to see deep-dive details (source links, trend graphs).
- Dashboard is responsive and deployed to production.

### Phase 3 Checklist

#### 3.1 Next.js Project Setup
- [ ] Initialize Next.js app:
  ```bash
  cd frontend
  pnpm create next-app@latest . --typescript --tailwind --app
  ```
- [ ] Install dependencies:
  - `@tanstack/react-query` (server state)
  - `recharts` (charts)
  - `date-fns` (date formatting)
  - `zod` (validation)
  - `shadcn/ui` components (Button, Card, Badge, etc.)

#### 3.2 API Client Setup
- [ ] Create `frontend/lib/api-client.ts`:
  - Configure `fetch` with base URL (FastAPI backend)
  - Implement type-safe API functions:
    - `fetchInsights(params)` → `Insight[]`
    - `fetchInsightById(id)` → `Insight`
    - `fetchDailyTop()` → `Insight[]`
- [ ] Set up React Query:
  - Create `frontend/lib/query-client.ts`
  - Configure caching, refetch strategies
  - Wrap app in `QueryClientProvider`

#### 3.3 UI Components
- [ ] Create `frontend/components/insight-card.tsx`:
  - Display: problem statement, solution, relevance score
  - Badge for market size (color-coded)
  - "View Details" button
- [ ] Create `frontend/components/insight-detail-modal.tsx`:
  - Show full insight data
  - Display source URL (link to Reddit/Product Hunt)
  - Show competitor analysis
  - Trend chart (if trend data available)
- [ ] Create `frontend/components/filters.tsx`:
  - Filter by date range (last 7 days, 30 days, all time)
  - Filter by minimum relevance score (0.5, 0.7, 0.9)
  - Search by keyword (searches problem_statement and proposed_solution)
  - **State Management Pattern**: URL Search Params
    - Filters stored in URL: `?date_range=7d&min_score=0.7&search=AI`
    - **Benefits**: Shareable links, browser back/forward support, server-side rendering compatibility
    - **Implementation**:
      ```typescript
      // Use Next.js 14 App Router hooks
      import { useSearchParams, useRouter, usePathname } from 'next/navigation';

      export function Filters() {
        const searchParams = useSearchParams();
        const router = useRouter();
        const pathname = usePathname();

        const updateFilter = (key: string, value: string) => {
          const params = new URLSearchParams(searchParams.toString());
          params.set(key, value);
          router.push(`${pathname}?${params.toString()}`);
        };

        return (
          <div>
            <select onChange={(e) => updateFilter('date_range', e.target.value)}>
              <option value="7d">Last 7 days</option>
              <option value="30d">Last 30 days</option>
              <option value="all">All time</option>
            </select>
            {/* More filters... */}
          </div>
        );
      }
      ```
    - **API Integration**: Pass URL params to React Query fetch function
      ```typescript
      const { data } = useQuery({
        queryKey: ['insights', searchParams.toString()],
        queryFn: () => fetchInsights({
          dateRange: searchParams.get('date_range'),
          minScore: searchParams.get('min_score'),
          search: searchParams.get('search')
        })
      });
      ```

#### 3.4 Pages & Routing
- [ ] Create `frontend/app/page.tsx` (Home - Daily Top 5):
  - Fetch daily top insights using React Query
  - Display in grid layout (InsightCard components)
  - Loading and error states
- [ ] Create `frontend/app/insights/page.tsx` (All Insights):
  - Paginated list of all insights
  - Filters sidebar
  - Sort by relevance, date
- [ ] Create `frontend/app/insights/[id]/page.tsx` (Insight Detail):
  - Fetch single insight by ID
  - Display full details
  - Show related raw signal content

#### 3.5 Data Visualization
- [ ] Create `frontend/components/trend-chart.tsx`:
  - Use Recharts to display trend data
  - X-axis: Date, Y-axis: Search volume / upvotes
  - Tooltip showing exact values
- [ ] Integrate chart into Insight Detail page

#### 3.6 Styling & UX
- [ ] Implement dark mode toggle (using Tailwind's dark mode)
- [ ] Add responsive design (mobile-first)
- [ ] Add loading skeletons for better perceived performance
- [ ] Implement error boundaries for graceful error handling

#### 3.7 Deployment
- [ ] Backend deployment (Railway/Render):
  - Create `Dockerfile` for FastAPI app
  - Set up PostgreSQL and Redis instances
  - Configure environment variables
  - Deploy with GitHub Actions CI/CD
- [ ] Frontend deployment (Vercel):
  - Connect GitHub repo to Vercel
  - Set `NEXT_PUBLIC_API_URL` env variable
  - Deploy with auto-preview for PRs
- [ ] Configure CORS on FastAPI to allow frontend domain
- [ ] **Monitoring Setup**:
  - **Development**: Structured logging to console using `loguru`
    ```python
    # backend/app/core/logging.py
    from loguru import logger
    import sys

    logger.remove()  # Remove default handler
    logger.add(
        sys.stdout,
        format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan> - <level>{message}</level>",
        level="INFO"
    )
    ```
  - **Production**: Export to Railway/Render logs dashboard (automatic)
  - **Metrics**: Custom FastAPI middleware to track:
    ```python
    # backend/app/middleware/metrics.py
    import time
    from fastapi import Request

    @app.middleware("http")
    async def metrics_middleware(request: Request, call_next):
        start_time = time.time()
        response = await call_next(request)
        duration = time.time() - start_time

        logger.info(
            "API Request",
            extra={
                "method": request.method,
                "path": request.url.path,
                "status_code": response.status_code,
                "duration_ms": round(duration * 1000, 2)
            }
        )
        return response
    ```
  - **LLM Cost Tracking**:
    ```python
    # Track token usage after each LLM call
    logger.info(
        "LLM Call",
        extra={
            "model": "claude-3.5-sonnet",
            "tokens_used": result.usage.total_tokens,
            "cost_usd": result.usage.total_tokens * 0.000003,  # $3 per 1M tokens
            "request_id": result.id
        }
    )
    ```
  - **Alerting**: Set up Railway/Render alerts for:
    - API response time > 1s (p95)
    - Error rate > 5%
    - Database connection failures
  - **Dependencies**: Add `loguru>=0.7.0` to `pyproject.toml`

#### 3.8 Testing & QA
- [ ] End-to-end testing:
  - **Framework**: Playwright (better TypeScript support, faster than Cypress, built-in test isolation)
  - **Installation**:
    ```bash
    cd frontend
    pnpm add -D @playwright/test
    npx playwright install
    ```
  - **Test Data Setup**: Seed database with fixtures before tests
    ```typescript
    // frontend/tests/setup/seed.ts
    import { test as setup } from '@playwright/test';

    setup('seed database', async ({ request }) => {
      await request.post('http://localhost:8000/api/test/seed', {
        data: {
          insights: [
            { title: 'AI for Legal Docs', relevance_score: 0.87, /* ... */ },
            { title: 'SMB Inventory', relevance_score: 0.82, /* ... */ }
          ]
        }
      });
    });
    ```
  - **Test Scenarios**:
    - User can view daily top insights (`tests/daily-top.spec.ts`)
    - User can filter and search insights (`tests/filters.spec.ts`)
    - User can view insight details (`tests/insight-detail.spec.ts`)
  - **CI/CD Integration**: Run on GitHub Actions (see Phase 3.7)
    ```yaml
    # .github/workflows/test.yml
    - name: Run Playwright tests
      run: |
        cd frontend
        pnpm exec playwright test
    ```
- [ ] Performance testing:
  - Lighthouse score > 90
  - API response time < 500ms
- [ ] Cross-browser testing (Chrome, Safari, Firefox)

#### 3.9 Documentation
- [ ] Update `frontend/README.md` with:
  - Setup instructions
  - Environment variables
  - Deployment guide
- [ ] Create user guide (how to use the dashboard)

---

## Post-MVP Enhancements (Phase 4+)

### User Customization
- [ ] User authentication (Clerk or Auth0)
- [ ] User-specific keyword tracking
- [ ] Saved insights / favorites

### Advanced Analysis
- [ ] Multi-agent workflows (LangChain)
- [ ] Automated competitor research
- [ ] MVP plan generator (suggest tech stack for each idea)

### Notifications
- [ ] Daily email digest (SendGrid/Resend)
- [ ] Browser push notifications for high-score insights
- [ ] Slack/Discord webhook integration

### Data Sources Expansion
- [ ] Twitter/X scraping (via Apify)
- [ ] Indie Hackers forum
- [ ] Y Combinator news
- [ ] Patent databases (market validation)

---

## Development Principles

1. **Test Early**: Write tests for each component before moving to the next phase.
2. **Document as You Go**: Update documentation after each major milestone.
3. **Version Control**: Commit frequently with descriptive messages.
4. **Environment Parity**: Use Docker to ensure dev/prod parity.
5. **Security First**: Never commit secrets. Use `.env` files and secret managers.
6. **Performance Monitoring**: Add logging and monitoring from Day 1.

