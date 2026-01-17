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
  - Schedule tasks to run every 6 hours
  - Add cron-like scheduling logic
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
  - Query params: `?source=reddit&limit=10&offset=0`
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
- [ ] Implement validation and error handling:
  - Retry logic for API failures
  - Fallback to GPT-4o if Claude fails
  - Log all LLM interactions

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
  - Query params: `?min_score=0.7&limit=10`
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
  - Filter by date range
  - Filter by minimum relevance score
  - Search by keyword

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

#### 3.8 Testing & QA
- [ ] End-to-end testing:
  - User can view daily top insights
  - User can filter and search insights
  - User can view insight details
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

---

## Next Steps
👉 **Start with Phase 1, Step 1.1: Project Initialization**
