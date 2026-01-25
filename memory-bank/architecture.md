---
**Memory Bank Protocol**
**Reading Priority:** CRITICAL
**Read When:** Before implementing features, designing database models, creating APIs
**Dependencies:** Read active-context.md for current phase, implementation-plan.md for step-by-step tasks
**Purpose:** System architecture, database schema (21 tables implemented), API endpoints (97 verified), SSE, authentication, admin portal
**Last Updated:** 2026-01-25
---

# System Architecture: StartInsight

## Overview
StartInsight is a modular, AI-powered business intelligence platform built on three core loops: **Collect → Analyze → Present**. This document provides the comprehensive architectural blueprint for the system.

**Architecture Type**: Modular Monolith with separate Frontend and Backend
**Communication**: RESTful API (FastAPI) + optional WebSockets for real-time updates
**Deployment**: Dockerized containers on Railway/Render (backend) and Vercel (frontend)

---

## 1. System Context Diagram

```mermaid
graph TD
    User[👤 End User] -->|HTTPS| Frontend[Next.js Frontend<br/>Port 3000]
    Frontend -->|REST API| Backend[FastAPI Backend<br/>Port 8000]

    Backend -->|SQL Queries| DB[(PostgreSQL<br/>Primary Database)]
    Backend -->|Task Queue| Redis[(Redis<br/>Queue & Cache)]
    Backend -->|Async Jobs| Worker[Arq Worker<br/>Background Tasks]

    Worker -->|Scrape| Reddit[🌐 Reddit API<br/>r/startups, r/SaaS]
    Worker -->|Scrape| PH[🌐 Product Hunt<br/>Daily Launches]
    Worker -->|Scrape| Trends[🌐 Google Trends<br/>Search Volume]

    Worker -->|Store Raw Data| DB
    Worker -->|Analyze| LLM[🤖 Claude 3.5 Sonnet<br/>Anthropic API]
    LLM -->|Structured Insights| DB

    Backend -->|Read Insights| DB

    style User fill:#e1f5ff
    style Frontend fill:#4CAF50
    style Backend fill:#2196F3
    style DB fill:#FF9800
    style Redis fill:#f44336
    style Worker fill:#9C27B0
    style LLM fill:#FF5722
    style Reddit fill:#FF4500
    style PH fill:#DA552F
    style Trends fill:#4285F4
```

### Key Components

| Component | Technology | Purpose | Port/URL |
|-----------|-----------|---------|----------|
| **Frontend** | Next.js 14+ (App Router) | User-facing dashboard | `localhost:3000` |
| **Backend** | FastAPI (Uvicorn ASGI) | REST API & business logic | `localhost:8000` |
| **Database** | PostgreSQL 16+ | Primary data store | `localhost:5433` (⚠️ Non-standard port to avoid system PostgreSQL conflicts) |
| **Cache/Queue** | Redis 7+ | Task queue & caching | `localhost:6379` |
| **Worker** | Arq (async task queue) | Background scraping & analysis | N/A (daemon) |
| **LLM** | Claude 3.5 Sonnet (Anthropic) | AI analysis engine | API endpoint |
| **Scraper** | Firecrawl + PRAW + pytrends | Web data extraction | API endpoints |

**Local Development Setup:**
- **PostgreSQL & Redis**: Run in Docker containers via `docker-compose up -d` (see `docker-compose.yml`)
- **Backend (FastAPI)**: Runs locally via `uvicorn app.main:app --reload` (NOT Dockerized in Phase 1-3)
  - Reason: Faster iteration during development, easier debugging with hot reload
  - Production: Backend will be containerized and deployed to Railway/Render
- **Frontend (Next.js)**: Runs locally via `pnpm dev` (NOT Dockerized in Phase 1-3)

---

## 2. Data Flow Pipeline

### The Three Core Loops

```mermaid
sequenceDiagram
    autonumber
    participant Scheduler as Arq Scheduler
    participant Worker as Arq Worker
    participant Firecrawl as Firecrawl API
    participant DB as PostgreSQL
    participant LLM as Claude 3.5 Sonnet
    participant API as FastAPI
    participant Frontend as Next.js

    Note over Scheduler,Worker: LOOP 1: COLLECTION (Every 6 hours)
    Scheduler->>Worker: Trigger scrape_reddit_task()
    Worker->>Firecrawl: scrape_url("reddit.com/r/startups")
    Firecrawl-->>Worker: Return Markdown content
    Worker->>DB: INSERT INTO raw_signals (source, url, content, metadata)

    Note over Scheduler,Worker: LOOP 2: ANALYSIS (After collection)
    Scheduler->>Worker: Trigger analyze_signals_task()
    Worker->>DB: SELECT * FROM raw_signals WHERE processed = false
    DB-->>Worker: Return unprocessed signals
    Worker->>LLM: Analyze signal content (PydanticAI)
    LLM-->>Worker: Return InsightSchema (problem, solution, score)
    Worker->>DB: INSERT INTO insights (problem, solution, relevance_score)
    Worker->>DB: UPDATE raw_signals SET processed = true

    Note over API,Frontend: LOOP 3: PRESENTATION (User request)
    Frontend->>API: GET /api/insights/daily-top
    API->>DB: SELECT * FROM insights ORDER BY relevance_score DESC LIMIT 5
    DB-->>API: Return top insights
    API-->>Frontend: JSON response (InsightResponse[])
    Frontend->>Frontend: Render InsightCard components
```

### Detailed Data Flow Steps

#### Phase 1: Collection (The Collector)
1. **Scheduler triggers scraping task** (runs every 6 hours via Arq cron)
2. **Worker executes scraper** for each data source:
   - **Reddit**: Uses PRAW to fetch top posts from r/startups, r/SaaS
   - **Product Hunt**: Uses Firecrawl to scrape daily launches
   - **Google Trends**: Uses pytrends to fetch rising search keywords
3. **Firecrawl converts HTML → Markdown** (LLM-ready format)
4. **Raw data stored in PostgreSQL**:
   - Table: `raw_signals`
   - Fields: `source`, `url`, `content`, `metadata`, `created_at`, `processed=false`

#### Phase 2: Analysis (The Analyst)
1. **Worker fetches unprocessed signals** from `raw_signals` table
2. **PydanticAI agent analyzes content**:
   - Sends raw text to Claude 3.5 Sonnet
   - Prompt: "Extract problem statement, solution, market size, relevance score"
   - Validates output using Pydantic schema (`InsightSchema`)
3. **Structured insight saved**:
   - Table: `insights`
   - Fields: `problem_statement`, `proposed_solution`, `market_size_estimate`, `relevance_score`, `competitor_analysis`
4. **Mark signal as processed**: `UPDATE raw_signals SET processed = true`

#### Phase 3: Presentation (The Dashboard)
1. **User opens dashboard** (Next.js app)
2. **Frontend fetches data** via React Query:
   - `GET /api/insights/daily-top` → Top 5 insights
   - `GET /api/insights?min_score=0.7` → Filtered insights
3. **FastAPI serves insights**:
   - Queries PostgreSQL with filters (date, score, source)
   - Returns paginated JSON response
4. **Frontend renders UI**:
   - Display `InsightCard` components
   - User clicks → Navigate to `/insight/[id]` for deep dive

---

## 3. UI/UX Architecture (The Display Layer)

### Site Map

```mermaid
graph LR
    Root[/ <br/> Homepage] --> Dashboard[/dashboard <br/> Daily Top 5]
    Root --> AllInsights[/insights <br/> All Insights]
    Root --> Settings[/settings <br/> User Preferences]

    AllInsights --> InsightDetail[/insight/[id] <br/> Detail View]

    Dashboard --> InsightDetail

    style Root fill:#4CAF50
    style Dashboard fill:#2196F3
    style AllInsights fill:#FF9800
    style InsightDetail fill:#9C27B0
    style Settings fill:#607D8B
```

### Page Structure

#### 1. `/` (Homepage / Landing)
**Purpose**: Marketing page + quick access to dashboard

**Components**:
- Hero section with value proposition
- "View Today's Insights" CTA button
- Feature highlights (automated, AI-powered, data-driven)
- Redirect to `/dashboard` for authenticated users

---

#### 2. `/dashboard` (Main Feed)
**Purpose**: Display the top 5 daily insights

**Layout**:
```
┌─────────────────────────────────────────┐
│  StartInsight Dashboard                 │
├─────────────────────────────────────────┤
│  📊 Top 5 Insights of the Day           │
│  └─ Updated: 2 hours ago                │
├─────────────────────────────────────────┤
│  ┌────────────────────────────────────┐ │
│  │ InsightCard #1                     │ │
│  │ Problem: "Legal docs are slow..."  │ │
│  │ Solution: "AI-powered contract..." │ │
│  │ Relevance: ⭐⭐⭐⭐⭐ (0.92)         │ │
│  │ Market Size: 🟢 Large              │ │
│  │ [View Details →]                   │ │
│  └────────────────────────────────────┘ │
│  ┌────────────────────────────────────┐ │
│  │ InsightCard #2                     │ │
│  │ ...                                │ │
│  └────────────────────────────────────┘ │
└─────────────────────────────────────────┘
```

**Components**:
- `DailyTopHeader`: Shows date and last update time
- `InsightCard[]`: Grid of top 5 insights (sorted by `relevance_score DESC`)
- Each card shows:
  - Problem statement (truncated to 2 lines)
  - Proposed solution (truncated to 2 lines)
  - Relevance score (0.0 - 1.0, displayed as stars)
  - Market size badge (Small/Medium/Large, color-coded)
  - "View Details" button → `/insight/[id]`

**Data Fetching**:
```typescript
const { data, isLoading } = useQuery({
  queryKey: ['daily-top'],
  queryFn: () => fetchDailyTop(),
  refetchInterval: 60000 // Refresh every minute
})
```

---

#### 3. `/insights` (All Insights)
**Purpose**: Paginated, filterable list of all insights

**Layout**:
```
┌──────────────────────────────────────────┐
│  All Insights                            │
├────────┬─────────────────────────────────┤
│ Filters│  ┌──────────────────────────┐   │
│        │  │ InsightCard #1           │   │
│ Date:  │  └──────────────────────────┘   │
│ [____] │  ┌──────────────────────────┐   │
│        │  │ InsightCard #2           │   │
│ Score: │  └──────────────────────────┘   │
│ 0.7+   │  ...                            │
│        │  [Load More]                    │
│ Source:│                                 │
│ ☑ Reddit                                │
│ ☑ PH   │                                 │
└────────┴─────────────────────────────────┘
```

**Components**:
- `FilterSidebar`: Date range, minimum score, source filters
- `InsightGrid`: Paginated list (infinite scroll or "Load More")
- `SearchBar`: Keyword search (searches problem + solution text)
- `SortDropdown`: Sort by relevance, date, or market size

**Data Fetching**:
```typescript
const { data, fetchNextPage, hasNextPage } = useInfiniteQuery({
  queryKey: ['insights', filters],
  queryFn: ({ pageParam = 0 }) => fetchInsights({
    offset: pageParam,
    limit: 20,
    min_score: filters.minScore,
    source: filters.source
  }),
  getNextPageParam: (lastPage, pages) => pages.length * 20
})
```

---

#### 4. `/insight/[id]` (Detail View)
**Purpose**: Deep dive into a single insight with full data

**Layout**:
```
┌─────────────────────────────────────────────┐
│  ← Back to Dashboard                        │
├─────────────────────────────────────────────┤
│  Problem Statement                          │
│  "Current legal document review is slow..." │
│                                             │
│  Proposed Solution                          │
│  "AI-powered contract analysis tool that..." │
│                                             │
│  Market Analysis                            │
│  • Size: 🟢 Large ($10B+ TAM)              │
│  • Relevance Score: 0.92 / 1.0             │
│                                             │
│  Competitor Landscape                       │
│  1. LegalZoom (limited AI features)        │
│  2. Clio (practice management focus)       │
│  3. Ross Intelligence (shut down)          │
│                                             │
│  Data Sources                               │
│  • Reddit: r/lawyers (50 comments)         │
│    → "Current tools are too expensive..."  │
│  • Google Trends: 300% spike in "AI legal" │
│                                             │
│  📈 Trend Chart                            │
│  [Line graph: Search volume over 30 days]  │
│                                             │
│  Glue Code Implementation Plan              │
│  Suggested Tech Stack:                      │
│  • Frontend: Next.js + shadcn/ui           │
│  • Backend: FastAPI + LangChain            │
│  • LLM: Claude 3.5 Sonnet                  │
│  • PDF Parser: PyPDF2 + Firecrawl          │
│                                             │
│  [💾 Save Insight] [📤 Share]              │
└─────────────────────────────────────────────┘
```

**Components**:
- `InsightHeader`: Problem + solution (full text)
- `MarketAnalysisCard`: Score, market size, competitors
- `DataSourcesList`: Links to original Reddit posts, Product Hunt launches
- `TrendChart`: Line graph showing search volume / upvote trends over time
- `ImplementationPlan`: "Glue Code" suggestions (tech stack, APIs)
- `ActionButtons`: Save, share, export

**Data Fetching**:
```typescript
const { data: insight } = useQuery({
  queryKey: ['insight', id],
  queryFn: () => fetchInsightById(id)
})

const { data: rawSignal } = useQuery({
  queryKey: ['raw-signal', insight.raw_signal_id],
  queryFn: () => fetchRawSignalById(insight.raw_signal_id),
  enabled: !!insight
})
```

---

#### 5. `/settings` (User Preferences)
**Purpose**: Customize keyword tracking and notifications (Post-MVP)

**Layout**:
```
┌─────────────────────────────────────────┐
│  Settings                               │
├─────────────────────────────────────────┤
│  Tracked Keywords                       │
│  [AI for legal] [SaaS automation] [+]   │
│                                         │
│  Notification Preferences               │
│  ☑ Email daily digest                  │
│  ☐ Browser push notifications           │
│                                         │
│  API Access (Developer)                 │
│  API Key: ****-****-****-1234 [Copy]   │
│                                         │
│  [Save Changes]                         │
└─────────────────────────────────────────┘
```

**Note**: This page is for Phase 4+ (Post-MVP). Not required for initial launch.

---

### Component Hierarchy

```
app/
├── layout.tsx (Root layout with providers)
├── page.tsx (Homepage/Landing)
├── dashboard/
│   └── page.tsx (Daily Top 5)
├── insights/
│   ├── page.tsx (All Insights with filters)
│   └── [id]/
│       └── page.tsx (Insight Detail)
└── settings/
    └── page.tsx (User Preferences)

components/
├── insight-card.tsx (Reusable card component)
├── insight-detail-modal.tsx (Detail view modal)
├── trend-chart.tsx (Recharts line graph)
├── filter-sidebar.tsx (Filters for /insights)
├── search-bar.tsx (Keyword search)
└── ui/ (shadcn/ui components)
    ├── button.tsx
    ├── card.tsx
    ├── badge.tsx
    └── ... (other shadcn components)

lib/
├── api-client.ts (Type-safe fetch functions)
├── query-client.ts (React Query setup)
└── utils.ts (Helper functions)
```

---

## 4. Directory Structure

### Backend (`backend/`)

```
backend/
├── app/
│   ├── __init__.py
│   ├── main.py                    # FastAPI app entry point
│   ├── config.py                  # Pydantic Settings (env vars)
│   ├── database.py                # SQLAlchemy async engine setup
│   │
│   ├── models/                    # Database models (SQLAlchemy)
│   │   ├── __init__.py
│   │   ├── raw_signal.py          # RawSignal model
│   │   └── insight.py             # Insight model
│   │
│   ├── schemas/                   # Pydantic schemas (request/response)
│   │   ├── __init__.py
│   │   ├── raw_signal.py          # RawSignalResponse
│   │   ├── insight.py             # InsightResponse, InsightSchema
│   │   └── common.py              # PaginatedResponse[T]
│   │
│   ├── api/                       # API routes
│   │   ├── __init__.py
│   │   ├── routes/
│   │   │   ├── __init__.py
│   │   │   ├── signals.py         # GET /api/signals
│   │   │   ├── insights.py        # GET /api/insights
│   │   │   └── health.py          # GET /health
│   │   └── deps.py                # Dependency injection (DB sessions)
│   │
│   ├── scrapers/                  # Web scraping logic
│   │   ├── __init__.py
│   │   ├── firecrawl_client.py    # Firecrawl SDK wrapper
│   │   ├── base.py                # Base Scraper class
│   │   └── sources/
│   │       ├── __init__.py
│   │       ├── reddit_scraper.py  # Reddit scraper (PRAW + Firecrawl)
│   │       ├── product_hunt_scraper.py
│   │       └── trends_scraper.py  # Google Trends (pytrends)
│   │
│   ├── agents/                    # AI agents (PydanticAI)
│   │   ├── __init__.py
│   │   └── analyzer.py            # Insight extraction agent
│   │
│   ├── tasks/                     # Background tasks (Arq)
│   │   ├── __init__.py
│   │   ├── scraping_tasks.py      # scrape_reddit_task(), etc.
│   │   ├── analysis_tasks.py      # analyze_signals_task()
│   │   └── scheduler.py           # Task scheduling logic
│   │
│   ├── worker.py                  # Arq worker settings
│   │
│   └── monitoring/                # Logging & metrics
│       ├── __init__.py
│       └── metrics.py             # LLM cost tracking, API metrics
│
├── alembic/                       # Database migrations
│   ├── versions/
│   │   ├── 001_create_raw_signals.py
│   │   └── 002_create_insights.py
│   ├── env.py
│   └── alembic.ini
│
├── .env.example                   # Example environment variables
├── pyproject.toml                 # Python dependencies (uv/poetry)
├── Dockerfile                     # Production Docker image
├── .dockerignore                  # Docker build context exclusions
├── railway.toml                   # Railway deployment config
├── render.yaml                    # Render deployment config
└── README.md                      # Backend setup instructions

Note: Backend tests moved to centralized tests/backend/ directory (see Root Structure below)
```

---

### Frontend (`frontend/`)

```
frontend/
├── app/                           # Next.js 14 App Router
│   ├── layout.tsx                 # Root layout (providers, fonts)
│   ├── page.tsx                   # Homepage (landing page)
│   ├── globals.css                # Tailwind base styles
│   │
│   ├── dashboard/
│   │   └── page.tsx               # Daily Top 5 insights
│   │
│   ├── insights/
│   │   ├── page.tsx               # All insights (paginated)
│   │   └── [id]/
│   │       └── page.tsx           # Insight detail view
│   │
│   └── settings/
│       └── page.tsx               # User preferences (Post-MVP)
│
├── components/                    # React components
│   ├── insight-card.tsx           # Reusable insight card
│   ├── insight-detail-modal.tsx   # Detail modal
│   ├── trend-chart.tsx            # Recharts line graph
│   ├── filter-sidebar.tsx         # Filters for /insights
│   ├── search-bar.tsx             # Keyword search
│   ├── daily-top-header.tsx       # Dashboard header
│   │
│   └── ui/                        # shadcn/ui components
│       ├── button.tsx
│       ├── card.tsx
│       ├── badge.tsx
│       ├── input.tsx
│       ├── select.tsx
│       └── ... (other components)
│
├── lib/                           # Utilities and clients
│   ├── api-client.ts              # Type-safe API fetch functions
│   ├── query-client.ts            # React Query setup
│   ├── utils.ts                   # Helper functions (cn, formatDate)
│   └── types.ts                   # TypeScript types (Insight, RawSignal)
│
├── hooks/                         # Custom React hooks
│   ├── use-insights.ts            # useInsights(), useDailyTop()
│   └── use-filters.ts             # Filter state management
│
├── public/                        # Static assets
│   ├── favicon.ico
│   └── images/
│
├── .env.local.example             # Example env vars
├── next.config.js                 # Next.js configuration
├── tailwind.config.ts             # Tailwind CSS config
├── tsconfig.json                  # TypeScript config
├── package.json                   # Node dependencies (pnpm)
├── vercel.json                    # Vercel deployment config
└── README.md                      # Frontend setup instructions

Note: Frontend E2E tests moved to centralized tests/frontend/ directory (see Root Structure below)
```

---

### Root Structure

```
StartInsight/
├── backend/                       # FastAPI backend (see above)
├── frontend/                      # Next.js frontend (see above)
├── memory-bank/                   # Documentation
│   ├── project-brief.md
│   ├── tech-stack.md
│   ├── implementation-plan.md
│   ├── active-context.md
│   ├── architecture.md            # THIS FILE
│   └── progress.md                # Phase completion tracking
│
├── tests/                         # Centralized testing infrastructure
│   ├── backend/                   # Backend tests (Python/Pytest)
│   │   ├── conftest.py            # Pytest fixtures & configuration
│   │   ├── unit/                  # Unit tests (isolated components)
│   │   │   └── test_scrapers.py   # Scraper unit tests
│   │   ├── integration/           # Integration tests (multiple components)
│   │   │   ├── test_api.py        # API endpoint tests
│   │   │   └── test_phase_2_5_integration.py  # Phase 2.5 full pipeline
│   │   └── validation/            # Phase validation tests (9 files)
│   │       ├── test_phase_1_4.py  # Task Queue & Scheduler
│   │       ├── test_phase_1_5.py  # FastAPI Endpoints
│   │       ├── test_phase_1_6.py  # Environment & Config
│   │       ├── test_phase_1_8.py  # Documentation
│   │       ├── test_phase_2_1.py  # Database Schema Extension
│   │       ├── test_phase_2_2.py  # AI Analyzer Agent
│   │       ├── test_phase_2_3.py  # Analysis Task Queue
│   │       ├── test_phase_2_4.py  # Insights API Endpoints
│   │       └── test_phase_2_6.py  # Monitoring & Logging
│   ├── frontend/                  # Frontend tests (TypeScript/Playwright)
│   │   ├── playwright.config.ts   # Playwright configuration
│   │   └── e2e/                   # E2E tests (47 scenarios)
│   │       ├── daily-top.spec.ts          # Homepage tests (10 scenarios)
│   │       ├── filters.spec.ts            # Filtering tests (10 scenarios)
│   │       ├── insight-detail.spec.ts     # Detail page tests (12 scenarios)
│   │       └── theme-responsive.spec.ts   # Dark mode, responsive, a11y (15 scenarios)
│   └── README.md                  # Testing infrastructure documentation
│
├── test-results/                  # Test execution documentation
│   ├── phase-3/                   # Phase 3 test documentation
│   │   ├── test_phase_3_1.md      # Phase 3.1: Next.js Setup
│   │   ├── test_phase_3_5.md      # Phase 3.5: Data Visualization
│   │   ├── test_phase_3_6.md      # Phase 3.6: Dark Mode & Error Boundaries
│   │   ├── test_phase_3_7.md      # Phase 3.7: Deployment Configuration
│   │   ├── test_phase_3_8.md      # Phase 3.8: E2E Testing (Playwright)
│   │   ├── test_phase_3_9.md      # Phase 3.9: Documentation
│   │   └── test_phase_3_complete.md # Phase 3.1-3.5 Summary
│   └── README.md                  # Test results documentation
│
├── .github/                       # GitHub configuration
│   └── workflows/
│       └── ci-cd.yml              # GitHub Actions CI/CD pipeline
│
├── docker-compose.yml             # Local dev environment
├── .gitignore                     # Git ignore rules
├── README.md                      # Project overview
├── DEPLOYMENT.md                  # Production deployment guide
└── CLAUDE.md                      # Claude Code guidelines
```

---

## 5. Database Schema

### Table: `raw_signals`
**Purpose**: Store raw, unprocessed data from scrapers

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `id` | UUID | PRIMARY KEY | Unique identifier |
| `source` | VARCHAR(50) | NOT NULL | Data source ("reddit", "product_hunt", "trends") |
| `url` | TEXT | NOT NULL | Source URL (original post/page) |
| `content` | TEXT | NOT NULL | Scraped content (Markdown format) |
| `metadata` | JSONB | | Additional data (upvotes, comments, timestamp) |
| `processed` | BOOLEAN | DEFAULT FALSE | Whether AI analysis is complete |
| `created_at` | TIMESTAMP | DEFAULT NOW() | Scrape timestamp |

**Indexes**:
- `idx_source` on `source`
- `idx_processed` on `processed`
- `idx_created_at` on `created_at`

---

### Table: `insights`
**Purpose**: Store AI-analyzed, structured insights

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `id` | UUID | PRIMARY KEY | Unique identifier |
| `raw_signal_id` | UUID | FOREIGN KEY | Reference to source raw signal |
| `problem_statement` | TEXT | NOT NULL | Identified market problem |
| `proposed_solution` | TEXT | NOT NULL | Suggested solution approach |
| `market_size_estimate` | VARCHAR(20) | NOT NULL | "Small", "Medium", or "Large" |
| `relevance_score` | FLOAT | NOT NULL | 0.0 - 1.0 relevance score |
| `competitor_analysis` | JSONB | | List of competitors (JSON array) |
| `created_at` | TIMESTAMP | DEFAULT NOW() | Analysis timestamp |

**Indexes**:
- `idx_relevance_score` on `relevance_score DESC`
- `idx_created_at` on `created_at DESC`
- `idx_raw_signal_id` on `raw_signal_id`

---

<!-- Supabase Cloud architecture added on 2026-01-25 for Phase 4.5 migration -->

### 5.10 Database Migration Strategy (Phase 4.5)

**Migration Approach:** Blue-Green Deployment with Dual-Write Period

```
Current State (PostgreSQL)
         ↓
┌────────────────────────┐
│  Week 1: Setup         │
│  - Create Supabase     │
│  - Migrate schema      │
│  - Configure RLS       │
└────────────────────────┘
         ↓
┌────────────────────────┐
│  Week 2: Dual-Write    │
│  - Write to both DBs   │
│  - Sync historical     │
│  - Validate integrity  │
└────────────────────────┘
         ↓
┌────────────────────────┐
│  Week 3: Testing       │
│  - Load tests          │
│  - Rollback practice   │
│  - Performance tuning  │
└────────────────────────┘
         ↓
┌────────────────────────┐
│  Week 4: Cutover       │
│  - Switch reads        │
│  - Monitor 48h         │
│  - Deprecate old DB    │
└────────────────────────┘
         ↓
Final State (Supabase Cloud)
```

**Migration Components:**

1. **Schema Migration** (Alembic → Supabase SQL)
   - Export schema: `alembic revision --autogenerate -m "export"`
   - Convert to Supabase SQL: Remove SQLAlchemy types, add RLS policies
   - Apply via Supabase Studio or CLI

2. **Data Migration**
   - Historical data: `pg_dump` → `pg_restore` to Supabase
   - Incremental sync: Custom Python script (read PostgreSQL, write Supabase)
   - Validation: Row counts, checksums, sample queries

3. **Application Migration**
   - Dual-write service: Write to both PostgreSQL + Supabase
   - Read from Supabase (fallback to PostgreSQL on error)
   - 48-hour monitoring period before PostgreSQL deprecation

4. **Rollback Plan**
   - Trigger: >5% error rate, >100ms p95 latency degradation, data integrity issues
   - Action: Switch reads back to PostgreSQL, pause dual-writes
   - Time: 30-minute rollback window

---

## 6. API Endpoints Reference

**Total Routes:** 35+ endpoints across all phases

**Phase Breakdown:**
- **Phase 1-3** (Implemented): 8 endpoints (raw signals CRUD, insights CRUD, health check)
- **Phase 4.1-4.4** (In Progress): +12 endpoints (users, saved insights, ratings, admin, workspace)
- **Phase 4.5+** (Planned): +15 endpoints (Supabase integration, real-time, storage)

**Note:** The sections below document all planned endpoints. Check active-context.md for current implementation status.

---

### Health & Status
- `GET /health` - Health check endpoint
- `GET /api/status` - System status (DB connection, worker status)

### Raw Signals (Phase 1)
- `GET /api/signals` - List raw signals (paginated)
  - Query params: `?source=reddit&limit=20&offset=0`
- `GET /api/signals/{id}` - Get single raw signal

### Insights (Phase 2)
- `GET /api/insights` - List all insights (paginated, filterable)
  - Query params: `?min_score=0.7&limit=20&offset=0&source=reddit`
- `GET /api/insights/{id}` - Get single insight with related raw signal
- `GET /api/insights/daily-top` - Top 5 insights of the day

### Analytics (Post-MVP)
- `GET /api/analytics/trends` - Trend data for charts
- `GET /api/analytics/sources` - Source breakdown statistics

### 6.2 API Response Schemas

#### Success Response (200 OK)

**GET /api/insights/{id}**
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "title": "AI for Legal Document Review",
  "problem": "Legal professionals spend 60% of their time on repetitive document review tasks, leading to burnout and high costs for clients.",
  "solution": "AI-powered document analysis tool that automates initial contract review, highlighting key clauses and potential issues.",
  "market_size": "Legal tech market: $28B+ globally, contract analysis segment growing 15% YoY",
  "competitor_analysis": [
    {
      "name": "LawGeex",
      "url": "https://lawgeex.com",
      "description": "Contract review automation for enterprises",
      "market_position": "Large"
    },
    {
      "name": "Kira Systems",
      "url": "https://kirasystems.com",
      "description": "Machine learning for contract analysis",
      "market_position": "Medium"
    }
  ],
  "relevance_score": 0.87,
  "raw_signal": {
    "id": "raw-signal-uuid",
    "source": "reddit",
    "url": "https://reddit.com/r/lawyers/comments/xyz",
    "content": "Original scraped content...",
    "scraped_at": "2026-01-18T10:30:00Z"
  },
  "created_at": "2026-01-18T11:00:00Z"
}
```

**GET /api/insights (Paginated)**
```json
{
  "items": [
    {
      "id": "uuid-1",
      "title": "AI for Legal Document Review",
      "problem": "Legal professionals spend 60%...",
      "solution": "AI-powered document analysis...",
      "relevance_score": 0.87,
      "created_at": "2026-01-18T11:00:00Z"
    },
    {
      "id": "uuid-2",
      "title": "SMB Inventory Management",
      "problem": "Small retailers struggle with...",
      "solution": "Cloud-based inventory tracker...",
      "relevance_score": 0.82,
      "created_at": "2026-01-18T09:30:00Z"
    }
  ],
  "total": 47,
  "limit": 20,
  "offset": 0,
  "has_more": true
}
```

**GET /api/insights/daily-top**
```json
{
  "date": "2026-01-18",
  "insights": [
    {
      "id": "uuid-1",
      "title": "AI for Legal Document Review",
      "problem": "Legal professionals spend 60%...",
      "relevance_score": 0.87
    }
  ],
  "count": 5
}
```

#### Error Responses

**404 Not Found**
```json
{
  "detail": "Insight not found",
  "error_code": "INSIGHT_NOT_FOUND",
  "timestamp": "2026-01-18T12:00:00Z"
}
```

**422 Validation Error**
```json
{
  "detail": [
    {
      "loc": ["query", "min_score"],
      "msg": "value must be between 0.0 and 1.0",
      "type": "value_error"
    }
  ],
  "error_code": "VALIDATION_ERROR"
}
```

**500 Internal Server Error**
```json
{
  "detail": "Internal server error occurred",
  "error_code": "INTERNAL_ERROR",
  "request_id": "req-abc123"
}
```

**503 Service Unavailable**
```json
{
  "detail": "Database connection unavailable",
  "error_code": "SERVICE_UNAVAILABLE",
  "retry_after": 30
}
```

---

## 7. Deployment Architecture

### Production Stack

```mermaid
graph TB
    subgraph "Vercel (Frontend)"
        NextJS[Next.js App<br/>Static + SSR]
    end

    subgraph "Railway/Render (Backend)"
        API[FastAPI Container]
        Worker[Arq Worker Container]
    end

    subgraph "Managed Services"
        DB[(Neon PostgreSQL<br/>Managed)]
        Redis[(Upstash Redis<br/>Managed)]
    end

    subgraph "External APIs"
        Anthropic[Anthropic API<br/>Claude 3.5]
        Firecrawl[Firecrawl API]
    end

    NextJS -->|HTTPS| API
    API --> DB
    API --> Redis
    Worker --> DB
    Worker --> Redis
    Worker --> Anthropic
    Worker --> Firecrawl

    style NextJS fill:#4CAF50
    style API fill:#2196F3
    style Worker fill:#9C27B0
    style DB fill:#FF9800
    style Redis fill:#f44336
```

### Environment Variables (Production)

**Backend (`railway.app`)**:
```bash
DATABASE_URL=postgresql+asyncpg://user:pass@neon.tech/startinsight
REDIS_URL=redis://upstash.com:6379
FIRECRAWL_API_KEY=fc-***
REDDIT_CLIENT_ID=***
REDDIT_CLIENT_SECRET=***
ANTHROPIC_API_KEY=sk-ant-***
ENVIRONMENT=production
LOG_LEVEL=info
```

**Frontend (`vercel.app`)**:
```bash
NEXT_PUBLIC_API_URL=https://startinsight-api.railway.app
NEXT_PUBLIC_ENV=production
```

---

## 8. Security & Performance

### Security Measures
1. **API Keys**: All secrets stored in environment variables (never committed)
2. **CORS**: FastAPI CORS middleware configured for frontend domain only
3. **Rate Limiting**: Redis-based rate limiting on API endpoints (future)
4. **SQL Injection**: SQLAlchemy parameterized queries (built-in protection)
5. **XSS Protection**: React auto-escapes user input

### Performance Optimizations
1. **Database Indexing**: Indexes on frequently queried columns (relevance_score, created_at)
2. **React Query Caching**: 5-minute cache for insights, 1-minute for daily top
3. **Pagination**: All list endpoints paginated (limit=20 default)
4. **Async I/O**: All database and API calls use async/await
5. **Redis Caching**: Cache hot insights (top 5 daily) in Redis with 1-hour TTL

### 8.3 Error Handling Strategy

**Fail Gracefully Principle**: The system must degrade gracefully when external services fail, ensuring core functionality remains available.

**1. External API Failures (Firecrawl, Reddit, Anthropic)**
- **Pattern**: Exponential backoff with retries (using `tenacity` library)
- **Retry Policy**: 3 attempts with 1s → 2s → 4s delays
- **Circuit Breaker**: After 5 consecutive failures, pause scraping for 15 minutes
- **Fallback**:
  - If Claude API fails → fallback to GPT-4o
  - If scraping fails → log error, continue with other sources
- **Example**: See `implementation-plan.md` Phase 2.2 for concrete code

**2. Database Connection Failures**
- **Pattern**: Connection pooling with health checks
- **Retry**: SQLAlchemy automatic retry on transient errors
- **Graceful Degradation**: Return cached data from Redis if DB unavailable
- **Response**: HTTP 503 Service Unavailable with `retry_after` header

**3. LLM Validation Errors (Invalid JSON, Hallucinations)**
- **Pattern**: Pydantic schema validation with retry on failure
- **Handling**:
  - ValidationError → retry with refined prompt (max 3 attempts)
  - If all retries fail → mark signal as `processing_failed`, log for manual review
  - Track validation failure rate in metrics
- **Monitoring**: Alert if validation failure rate > 10%

**4. Rate Limit Handling**
- **Anthropic API**: 429 response → exponential backoff + switch to GPT-4o
- **Reddit API**: 429 response → pause scraping for duration specified in `X-Ratelimit-Reset`
- **Firecrawl**: 429 response → queue tasks for delayed retry
- **Strategy**: Implement token bucket algorithm for proactive rate limiting

**5. Timeout Management**
- **Scraping Tasks**: 30s timeout per URL (Firecrawl default)
- **LLM API Calls**: 60s timeout (sufficient for Claude 3.5 Sonnet)
- **Database Queries**: 5s timeout (alert if exceeded)
- **Frontend API Calls**: 10s timeout with loading states

**6. Data Integrity Errors**
- **Duplicate Detection**: Unique constraint on `raw_signals.url` field
- **Handling**: On duplicate → log and skip (idempotent scraping)
- **Partial Failures**: Batch processing commits after each successful item (not all-or-nothing)

**7. Frontend Error Boundaries**
- **Pattern**: React Error Boundaries for component-level failures
- **User Experience**:
  - Show friendly error message
  - Provide "Retry" button
  - Log error to monitoring service
- **Example**: "Unable to load insights. Please try again."

**8. Logging & Alerting**
- **All Errors Logged**: Structured logs with context (request_id, user_id, timestamp)
- **Critical Alerts**:
  - Database connection down → immediate Slack/email alert
  - LLM API quota exceeded → alert ops team
  - Validation failure rate > 10% → investigate prompt quality
- **Non-Critical**: Log and monitor (scraping individual URLs failing)

---

## 9. Monitoring & Observability

### Logging Strategy
- **Structured Logging**: JSON logs with correlation IDs
- **Log Levels**:
  - `INFO`: API requests, task executions
  - `WARNING`: Rate limit hits, retries
  - `ERROR`: Failed scrapes, LLM errors
  - `DEBUG`: Detailed debugging info (dev only)

### Key Metrics to Track
1. **Scraper Metrics**:
   - Scrapes per day (by source)
   - Scrape success rate
   - Average scrape duration
2. **LLM Metrics**:
   - API calls per day
   - Average response time
   - Token usage (cost tracking)
   - Validation error rate
3. **API Metrics**:
   - Request rate (per endpoint)
   - Response time (p50, p95, p99)
   - Error rate (4xx, 5xx)
4. **Business Metrics**:
   - Total insights generated per day
   - Average relevance score
   - User engagement (page views, detail views)

---


<\!-- Phase 4+ architecture merged from architecture-phase4-addendum.md on 2026-01-24 -->

## Phase 4+ Architecture Overview

### System Context Diagram (Updated)

```mermaid
graph TB
    subgraph "Frontend (Next.js)"
        User[👤 User]
        Admin[🔧 Admin]
        NextJS[Next.js 16.1.3<br/>App Router]
        ClerkUI[Clerk UI Components]
    end

    subgraph "Authentication Layer"
        Clerk[Clerk Service<br/>JWT Provider]
    end

    subgraph "Backend (FastAPI)"
        API[FastAPI<br/>REST API]
        Auth[Auth Middleware<br/>JWT Verification]
        UserRoutes[User Routes]
        AdminRoutes[Admin Routes]
        InsightRoutes[Insight Routes]
        SSE[SSE Stream<br/>Admin Events]
    end

    subgraph "Data Layer"
        DB[(PostgreSQL<br/>v0.2 Schema)]
        Redis[(Redis<br/>State + Cache)]
    end

    subgraph "Background Workers"
        Scrapers[Scraper Workers]
        Analyzers[Analyzer Workers]
    end

    subgraph "External Services"
        LLM[Claude 3.5 Sonnet<br/>Anthropic API]
        Firecrawl[Firecrawl API]
    end

    User --> NextJS
    Admin --> NextJS
    NextJS --> ClerkUI
    ClerkUI --> Clerk
    NextJS --> API
    API --> Auth
    Auth --> Clerk

    Auth --> UserRoutes
    Auth --> AdminRoutes
    Auth --> InsightRoutes

    UserRoutes --> DB
    AdminRoutes --> DB
    AdminRoutes --> Redis
    AdminRoutes --> SSE
    InsightRoutes --> DB

    SSE --> Admin

    Scrapers --> Redis
    Analyzers --> Redis
    Scrapers --> LLM
    Analyzers --> LLM
    Scrapers --> Firecrawl

    Scrapers --> DB
    Analyzers --> DB

    style Clerk fill:#6366f1
    style Auth fill:#f59e0b
    style SSE fill:#10b981
    style Redis fill:#ef4444
```

### Phase 4 Architectural Layers

```
┌─────────────────────────────────────────────┐
│  Presentation Layer (Next.js)               │
│  - Public Pages (Home, Insights List)       │
│  - Protected Pages (Workspace, Admin)       │
│  - Clerk UI Components                      │
└─────────────────────────────────────────────┘
                    ↓
┌─────────────────────────────────────────────┐
│  Authentication Layer                       │
│  - Clerk JWT Verification                   │
│  - User Creation/Sync                       │
│  - Role-Based Authorization                 │
└─────────────────────────────────────────────┘
                    ↓
┌─────────────────────────────────────────────┐
│  API Layer (FastAPI)                        │
│  - Public Endpoints (no auth)               │
│  - User Endpoints (user auth)               │
│  - Admin Endpoints (admin auth)             │
│  - SSE Streaming (real-time)                │
└─────────────────────────────────────────────┘
                    ↓
┌─────────────────────────────────────────────┐
│  Business Logic Layer                       │
│  - User Management Service                  │
│  - Insight Service (Enhanced Scoring)       │
│  - Admin Service (Agent Control)            │
│  - Analytics Service                        │
└─────────────────────────────────────────────┘
                    ↓
┌─────────────────────────────────────────────┐
│  Data Access Layer                          │
│  - PostgreSQL (User, Insight, Admin data)   │
│  - Redis (Agent State, Cache, Sessions)     │
└─────────────────────────────────────────────┘
                    ↓
┌─────────────────────────────────────────────┐
│  Worker Layer                               │
│  - Scrapers (Redis State Check)             │
│  - Analyzers (Enhanced Scoring)             │
│  - Background Jobs (Metrics, Backfill)      │
└─────────────────────────────────────────────┘
```

---

## Authentication Architecture

### JWT-Based Authentication Flow

```mermaid
sequenceDiagram
    autonumber
    participant User
    participant NextJS as Next.js Frontend
    participant Clerk as Clerk Service
    participant API as FastAPI Backend
    participant DB as PostgreSQL

    User->>NextJS: Click "Sign In"
    NextJS->>Clerk: Redirect to Clerk UI
    Clerk->>User: Show sign-in form
    User->>Clerk: Enter credentials
    Clerk->>Clerk: Verify credentials
    Clerk->>NextJS: Return JWT token
    NextJS->>NextJS: Store token (cookie)

    Note over User,DB: Authenticated Request Flow

    User->>NextJS: Navigate to /workspace
    NextJS->>API: GET /api/users/me<br/>Authorization: Bearer {token}
    API->>API: Extract token from header
    API->>Clerk: Verify JWT signature
    Clerk->>API: Token valid, return user_id
    API->>DB: SELECT * FROM users WHERE clerk_user_id = ?
    DB->>API: User record (or null)

    alt User exists
        API->>NextJS: Return user profile
    else User doesn't exist (first login)
        API->>Clerk: GET /users/{clerk_user_id}
        Clerk->>API: Return user details (email, name, avatar)
        API->>DB: INSERT INTO users (clerk_user_id, email, ...)
        DB->>API: User created
        API->>NextJS: Return new user profile
    end

    NextJS->>User: Display workspace
```

### Token Storage Strategy

**Frontend Token Management:**

| Storage Option | Pros | Cons | Our Choice |
|----------------|------|------|------------|
| localStorage | Simple, survives refresh | Vulnerable to XSS | ❌ No |
| sessionStorage | Auto-clears on close | Lost on refresh | ❌ No |
| httpOnly Cookie | XSS-safe, auto-sent | Requires CSRF protection | ✅ Yes |
| In-memory | Most secure | Lost on refresh | ❌ No |

**Implementation:**

```typescript
// Clerk handles token storage automatically (httpOnly cookies)
// Token is automatically included in requests via Authorization header

import { auth } from "@clerk/nextjs/server";

export async function getServerSideProps(context) {
  const { userId } = await auth();

  if (!userId) {
    return { redirect: { destination: "/sign-in" } };
  }

  // userId available for API calls
  return { props: { userId } };
}
```

### Authorization Layers

```python
# backend/app/api/deps.py

from enum import Enum

class UserRole(str, Enum):
    USER = "user"
    MODERATOR = "moderator"
    ADMIN = "admin"

# Dependency: Require authentication
async def get_current_user(request: Request) -> User:
    """Verify JWT and return user (raises 401 if invalid)."""
    pass

# Dependency: Require admin role
async def require_admin(user: User = Depends(get_current_user)) -> User:
    """Verify user is admin (raises 403 if not)."""
    admin_record = await db.execute(
        select(AdminUser).where(AdminUser.user_id == user.id)
    )
    if not admin_record.scalar_one_or_none():
        raise HTTPException(403, "Admin access required")

    return user

# Usage
@router.get("/api/admin/dashboard")
async def admin_dashboard(admin: User = Depends(require_admin)):
    # Only admins can access
    pass

@router.get("/api/users/me")
async def get_profile(user: User = Depends(get_current_user)):
    # Any authenticated user can access
    pass

@router.get("/api/insights")
async def list_insights():
    # Public endpoint (no auth required)
    pass
```

### Session Management

**Clerk Session Lifecycle:**

```
User Sign In
    ↓
Clerk creates session (JWT token)
    ↓
Token stored in httpOnly cookie (expires in 1 hour)
    ↓
Frontend automatically refreshes token (before expiry)
    ↓
Backend verifies token on each request
    ↓
User Sign Out → Clerk invalidates session
```

**Token Refresh:**
- Automatic: Clerk SDK handles refresh before expiry
- Manual: User can force refresh via `getToken({ skipCache: true })`
- Fallback: If refresh fails, user redirected to sign-in

---

## Admin Portal Architecture

### Real-Time Update Mechanism (SSE)

**Architecture Decision:**
- ✅ Server-Sent Events (SSE) - Chosen
- ❌ WebSocket - Rejected (overkill for one-way streaming)
- ❌ Polling - Rejected (inefficient, 30-60s delay)

**SSE Implementation:**

```mermaid
sequenceDiagram
    participant Admin as Admin User
    participant Frontend as Admin Dashboard
    participant SSE as SSE Endpoint
    participant Redis as Redis
    participant Worker as Arq Worker
    participant DB as PostgreSQL

    Admin->>Frontend: Open /admin/dashboard
    Frontend->>SSE: GET /admin/events (EventSource)
    SSE->>Frontend: Connection established

    loop Every 5 seconds
        SSE->>Redis: GET agent_state:*
        Redis->>SSE: Agent states (running/paused)
        SSE->>DB: SELECT recent logs
        DB->>SSE: Last 10 executions
        SSE->>DB: SELECT SUM(cost) FROM metrics WHERE recorded_at > now() - interval '1 day'
        DB->>SSE: LLM cost today
        SSE->>Frontend: event: metrics_update<br/>data: {agents, logs, cost}
        Frontend->>Frontend: Update UI
    end

    Note over Admin,DB: Manual Agent Control (via POST)

    Admin->>Frontend: Click "Trigger Reddit Scraper"
    Frontend->>API: POST /admin/agents/reddit_scraper/trigger
    API->>Worker: Enqueue scrape_reddit_task()
    Worker->>DB: Log execution start
    API->>Frontend: {job_id, status: "triggered"}
    Frontend->>Admin: Show success toast

    Note over SSE: Next SSE update will show job in "running" state
```

**Backend SSE Implementation:**

```python
# backend/app/api/routes/admin.py
from sse_starlette.sse import EventSourceResponse
import asyncio
import json

@router.get("/admin/events")
async def admin_event_stream(
    admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    """Stream admin dashboard updates via Server-Sent Events."""

    async def event_generator():
        while True:
            try:
                # Gather metrics
                metrics = await gather_admin_metrics(db)

                # Send update
                yield {
                    "event": "metrics_update",
                    "data": json.dumps(metrics),
                    "retry": 5000,  # Reconnect after 5s if disconnected
                }

                # Wait 5 seconds
                await asyncio.sleep(5)

            except asyncio.CancelledError:
                # Client disconnected
                logger.info("Admin client disconnected from SSE")
                break
            except Exception as e:
                logger.error(f"SSE error: {e}")
                # Send error event
                yield {
                    "event": "error",
                    "data": json.dumps({"error": str(e)}),
                }
                await asyncio.sleep(5)

    return EventSourceResponse(event_generator())


async def gather_admin_metrics(db: AsyncSession) -> dict:
    """Gather all metrics for admin dashboard."""

    # Agent states from Redis
    agent_states = {}
    for agent in ["reddit_scraper", "product_hunt_scraper", "trends_scraper", "analyzer"]:
        state = await redis.get(f"agent_state:{agent}")
        agent_states[agent] = state.decode() if state else "running"

    # Last 10 execution logs
    logs = await db.execute(
        select(AgentExecutionLog)
        .order_by(AgentExecutionLog.created_at.desc())
        .limit(10)
    )
    recent_logs = [log.to_dict() for log in logs.scalars().all()]

    # LLM cost today
    cost_result = await db.execute(
        select(func.sum(SystemMetric.metric_value))
        .where(
            SystemMetric.metric_type == "llm_cost",
            SystemMetric.recorded_at >= func.now() - text("interval '1 day'")
        )
    )
    llm_cost_today = cost_result.scalar_one_or_none() or 0.0

    # Insights pending review
    pending_result = await db.execute(
        select(func.count())
        .select_from(Insight)
        .where(Insight.admin_status == "pending")
    )
    pending_count = pending_result.scalar_one()

    return {
        "agent_states": agent_states,
        "recent_logs": recent_logs,
        "llm_cost_today": float(llm_cost_today),
        "pending_insights": pending_count,
        "timestamp": datetime.now().isoformat(),
    }
```

**Frontend SSE Consumer:**

```typescript
// frontend/app/admin/page.tsx
"use client";

import { useEffect, useState } from "react";
import { useAuth } from "@clerk/nextjs";

interface AdminMetrics {
  agent_states: Record<string, string>;
  recent_logs: any[];
  llm_cost_today: number;
  pending_insights: number;
  timestamp: string;
}

export default function AdminDashboard() {
  const { getToken } = useAuth();
  const [metrics, setMetrics] = useState<AdminMetrics | null>(null);
  const [connectionStatus, setConnectionStatus] = useState<"connecting" | "connected" | "disconnected">("connecting");

  useEffect(() => {
    let eventSource: EventSource | null = null;

    async function connectSSE() {
      const token = await getToken();

      // Create EventSource connection with auth token
      eventSource = new EventSource(`/api/admin/events?token=${token}`);

      eventSource.onopen = () => {
        console.log("SSE connected");
        setConnectionStatus("connected");
      };

      eventSource.addEventListener("metrics_update", (event) => {
        const data = JSON.parse(event.data);
        setMetrics(data);
      });

      eventSource.addEventListener("error", (event) => {
        console.error("SSE error:", event);
        setConnectionStatus("disconnected");
      });

      eventSource.onerror = (error) => {
        console.error("SSE connection failed:", error);
        setConnectionStatus("disconnected");
        eventSource?.close();

        // Reconnect after 5 seconds
        setTimeout(connectSSE, 5000);
      };
    }

    connectSSE();

    // Cleanup on unmount
    return () => {
      eventSource?.close();
    };
  }, [getToken]);

  if (!metrics) {
    return <div>Loading dashboard...</div>;
  }

  return (
    <div>
      <div className="flex items-center gap-2 mb-4">
        <h1 className="text-3xl font-bold">Admin Dashboard</h1>
        <span className={`px-2 py-1 text-xs rounded ${
          connectionStatus === "connected" ? "bg-green-100 text-green-800" :
          connectionStatus === "connecting" ? "bg-yellow-100 text-yellow-800" :
          "bg-red-100 text-red-800"
        }`}>
          {connectionStatus === "connected" ? "● Live" :
           connectionStatus === "connecting" ? "● Connecting..." :
           "● Disconnected"}
        </span>
      </div>

      {/* Agent Status Cards */}
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
        {Object.entries(metrics.agent_states).map(([agent, state]) => (
          <AgentStatusCard key={agent} agent={agent} state={state} />
        ))}
      </div>

      {/* LLM Cost */}
      <div className="mt-6">
        <div className="text-sm text-muted-foreground">LLM Cost Today</div>
        <div className="text-3xl font-bold">${metrics.llm_cost_today.toFixed(2)}</div>
      </div>

      {/* Recent Logs */}
      <div className="mt-6">
        <h2 className="text-xl font-bold mb-4">Recent Executions</h2>
        <ExecutionLogTable logs={metrics.recent_logs} />
      </div>

      {/* Last updated timestamp */}
      <div className="text-xs text-muted-foreground mt-4">
        Last updated: {new Date(metrics.timestamp).toLocaleTimeString()}
      </div>
    </div>
  );
}
```

### Agent Control Architecture

**Redis-Based State Machine:**

```
┌──────────────┐
│ Agent States │
│ (Redis Keys) │
└──────────────┘
        ↓
agent_state:reddit_scraper = "running" | "paused"
agent_state:analyzer = "running" | "paused"

┌──────────────────────────────────────┐
│ State Transitions                    │
├──────────────────────────────────────┤
│ running → paused   (via POST /pause) │
│ paused → running   (via POST /resume)│
│ * → triggered      (via POST /trigger│
└──────────────────────────────────────┘

┌──────────────────────────────────────┐
│ Worker Behavior                      │
├──────────────────────────────────────┤
│ Before each task execution:          │
│   1. Read agent_state:{agent} from Redis│
│   2. If "paused" → skip, return early│
│   3. If "running" → proceed          │
│   4. Log execution to database       │
└──────────────────────────────────────┘
```

**Worker Implementation:**

```python
# backend/app/tasks/scraping_tasks.py

async def scrape_reddit_task(ctx):
    """Reddit scraping task with state management."""
    redis = ctx["redis"]
    db = ctx["db"]

    # Check agent state
    state = await redis.get("agent_state:reddit_scraper")
    if state == b"paused":
        logger.info("Reddit scraper is paused, skipping execution")
        return {"status": "skipped", "reason": "Agent paused by admin"}

    # Log execution start
    log = AgentExecutionLog(
        agent_type="scraper",
        source="reddit",
        status="running",
        started_at=datetime.now(),
    )
    db.add(log)
    await db.commit()

    try:
        # Perform scraping
        scraper = RedditScraper()
        results = await scraper.scrape()

        # Log success
        log.status = "completed"
        log.completed_at = datetime.now()
        log.duration_ms = (log.completed_at - log.started_at).total_seconds() * 1000
        log.items_processed = len(results)
        await db.commit()

        logger.info(f"Reddit scraper completed: {len(results)} items")
        return {"status": "completed", "items": len(results)}

    except Exception as e:
        # Log failure
        log.status = "failed"
        log.completed_at = datetime.now()
        log.duration_ms = (log.completed_at - log.started_at).total_seconds() * 1000
        log.error_message = str(e)
        await db.commit()

        logger.error(f"Reddit scraper failed: {e}")
        raise
```

**Admin API Control:**

```python
# backend/app/api/routes/admin.py

@router.post("/admin/agents/{agent_type}/pause")
async def pause_agent(
    agent_type: str,
    admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    """Pause agent execution."""
    # Validate agent type
    valid_agents = ["reddit_scraper", "product_hunt_scraper", "trends_scraper", "analyzer"]
    if agent_type not in valid_agents:
        raise HTTPException(400, f"Invalid agent type. Must be one of: {valid_agents}")

    # Set state to paused
    await redis.set(f"agent_state:{agent_type}", "paused")

    # Log admin action (audit trail)
    await log_admin_action(
        admin_user_id=admin.id,
        action="pause_agent",
        target=agent_type,
        metadata={"timestamp": datetime.now().isoformat()}
    )

    logger.info(f"Agent {agent_type} paused by admin {admin.email}")

    return {
        "status": "paused",
        "agent_type": agent_type,
        "paused_by": admin.email,
        "timestamp": datetime.now().isoformat(),
    }


@router.post("/admin/agents/{agent_type}/resume")
async def resume_agent(
    agent_type: str,
    admin: User = Depends(require_admin),
):
    """Resume agent execution."""
    await redis.set(f"agent_state:{agent_type}", "running")

    await log_admin_action(
        admin_user_id=admin.id,
        action="resume_agent",
        target=agent_type,
    )

    logger.info(f"Agent {agent_type} resumed by admin {admin.email}")

    return {"status": "running", "agent_type": agent_type}


@router.post("/admin/agents/{agent_type}/trigger")
async def trigger_agent(
    agent_type: str,
    admin: User = Depends(require_admin),
):
    """Manually trigger agent execution (out of schedule)."""
    from app.worker import arq_redis

    # Map agent_type to task function
    task_map = {
        "reddit_scraper": "scrape_reddit_task",
        "product_hunt_scraper": "scrape_product_hunt_task",
        "trends_scraper": "scrape_trends_task",
        "analyzer": "analyze_signals_task",
    }

    if agent_type not in task_map:
        raise HTTPException(400, f"Invalid agent type")

    # Enqueue job
    job = await arq_redis.enqueue_job(
        task_map[agent_type],
        _queue_name="startinsight"
    )

    await log_admin_action(
        admin_user_id=admin.id,
        action="trigger_agent",
        target=agent_type,
        metadata={"job_id": job.job_id}
    )

    logger.info(f"Agent {agent_type} triggered by admin {admin.email}, job_id={job.job_id}")

    return {
        "status": "triggered",
        "agent_type": agent_type,
        "job_id": job.job_id,
        "triggered_by": admin.email,
    }
```

---

## Enhanced Scoring Architecture

### Multi-Dimensional Scoring Pipeline

**Architecture Decision: Single-Prompt Serial Approach**

```mermaid
graph LR
    A[Raw Signal] --> B[Enhanced Analyzer]
    B --> C{PydanticAI Agent}
    C --> D[Claude 3.5 Sonnet]
    D --> E[Enhanced Prompt<br/>8 Dimensions + Frameworks]
    E --> F[Structured JSON Output]
    F --> G[Pydantic Validation]
    G --> H{Valid?}
    H -->|Yes| I[Save to Database]
    H -->|No| J[Retry with Refined Prompt]
    J --> C
    I --> K[Insight with<br/>8 Scores + Metadata]

    style D fill:#6366f1
    style G fill:#10b981
    style H fill:#f59e0b
```

**Cost vs Speed Analysis:**

| Approach | LLM Calls | Cost per Insight | Latency | Complexity | Our Choice |
|----------|-----------|------------------|---------|------------|------------|
| **Single-Prompt Serial** | 1 | $0.045 | 3-5s | Low | ✅ Yes |
| **Multi-Prompt Parallel** | 4 | $0.180 | 2-3s | High | ❌ No |
| **Hybrid** (2 calls) | 2 | $0.090 | 2-4s | Medium | Future |

**Scoring Dimensions:**

```python
# 8-Dimensional Scoring Model

class ScoreDimensions:
    """All scores are 1-10 integers."""

    # Core Opportunity Metrics
    opportunity_score: int      # Market size (1=tiny, 10=massive)
    problem_score: int          # Pain severity (1=mild, 10=existential)
    feasibility_score: int      # Technical ease (1=impossible, 10=trivial)
    why_now_score: int          # Market timing (1=wrong time, 10=perfect)

    # Business Fit Metrics
    revenue_potential: str      # $, $$, $$$, $$$$
    execution_difficulty: int   # Complexity (1=weekend, 10=years)
    go_to_market_score: int     # Distribution (1=hard sales, 10=viral)
    founder_fit_score: int      # Skill req (1=PhD needed, 10=anyone)

class AnalysisFrameworks:
    """Advanced frameworks for deeper insight."""

    # 4-Tier Pricing Model (IdeaBrowser parity)
    value_ladder: list[ValueLadderTier]  # Lead Magnet → Frontend → Core → Backend

    # Market Analysis
    market_gap_analysis: str    # Where competitors fail (200-300 words)
    why_now_analysis: str       # Why this is timely (200-300 words)

    # Validation Evidence
    proof_signals: list[ProofSignal]  # 3-5 evidence pieces

    # Actionable Plan
    execution_plan: list[ExecutionStep]  # 5-7 launch steps
```

**Enhanced Analyzer Agent:**

```python
# backend/app/agents/enhanced_analyzer.py

from pydantic_ai import Agent
from pydantic import BaseModel, Field

# Define enhanced schema (see implementation-plan-phase4-detailed.md for full schema)

ENHANCED_ANALYSIS_PROMPT = """
You are a startup idea validation expert analyzing market signals.

Analyze the following signal and provide comprehensive 8-dimension scoring:

**Signal:** {raw_content}
**Source:** {source}

## Output Requirements:

1. **Opportunity Score (1-10):** Market size
   - 1-3: <$10M TAM
   - 4-6: $10M-$1B
   - 7-9: $1B-$100B
   - 10: >$100B

2. **Problem Score (1-10):** Pain severity
   - 1-3: Nice-to-have
   - 4-6: Willing to pay
   - 7-9: Actively searching
   - 10: Existential pain

3. **Feasibility Score (1-10):** Technical difficulty
   - 1-3: Requires breakthrough tech
   - 4-6: Challenging but doable
   - 7-9: Can build with current tools
   - 10: No-code solution

4. **Why Now Score (1-10):** Market timing
   - 1-3: Too early/late
   - 4-6: Okay timing
   - 7-9: Good timing
   - 10: Perfect inflection point

5. **Revenue Potential:** $ (low), $$ (medium), $$$ (high), $$$$ (very high)

6. **Execution Difficulty (1-10):** Complexity
   - 1-3: Weekend project
   - 4-6: 3-6 months
   - 7-9: 1-2 years
   - 10: Multi-year, exceptional team

7. **Go-To-Market Score (1-10):** Distribution ease
   - 1-3: Enterprise sales
   - 4-6: SMB sales
   - 7-9: Self-serve
   - 10: Viral/PLG

8. **Founder Fit Score (1-10):** Skill requirements
   - 1-3: PhD + 10 years experience
   - 4-6: Domain knowledge helpful
   - 7-9: Generalist can learn
   - 10: No special knowledge

## Value Ladder Framework:

Design 4-tier pricing for this business:
- **Lead Magnet (Free):** What free tool captures emails?
- **Frontend ($9-$29/mo):** Entry product
- **Core ($49-$99/mo):** Main product
- **Backend ($299+/mo):** Premium offering

Provide specific examples for THIS idea.

## Market Gap Analysis:

Write 200-300 words on where current solutions fail.

## Why Now Analysis:

Write 200-300 words on why this is timely (technology enablers, market shifts, trends).

## Proof Signals:

List 3-5 validation evidence pieces:
- Signal Type: (search_trend, competitor_growth, community_discussion)
- Description: Evidence description
- Source: Where found
- Confidence: Low/Medium/High

## Execution Plan:

Provide 5-7 actionable steps:
- Step Number, Title, Description
- Estimated Time
- Resources Needed

Return ONLY valid JSON matching EnhancedInsightSchema.
"""

# Agent initialization
enhanced_analyzer = Agent(
    model="claude-3-5-sonnet-20241022",
    result_type=EnhancedInsightSchema,
    system_prompt=ENHANCED_ANALYSIS_PROMPT,
)

async def analyze_signal_enhanced(raw_signal: RawSignal) -> Insight:
    """Analyze signal with enhanced 8-dimension scoring."""

    # Run agent
    result = await enhanced_analyzer.run(
        raw_content=raw_signal.content,
        source=raw_signal.source,
        url=raw_signal.url,
    )

    # Validate result
    if not result.data:
        raise ValueError("Enhanced analysis failed: No data returned")

    # Convert to Insight model
    insight = Insight(
        raw_signal_id=raw_signal.id,
        title=result.data.title,
        problem_statement=result.data.problem_statement,
        proposed_solution=result.data.proposed_solution,
        market_size_estimate=result.data.market_size_estimate,
        relevance_score=result.data.relevance_score,
        competitor_analysis=result.data.competitor_analysis,

        # Enhanced scores
        opportunity_score=result.data.opportunity_score,
        problem_score=result.data.problem_score,
        feasibility_score=result.data.feasibility_score,
        why_now_score=result.data.why_now_score,
        revenue_potential=result.data.revenue_potential,
        execution_difficulty=result.data.execution_difficulty,
        go_to_market_score=result.data.go_to_market_score,
        founder_fit_score=result.data.founder_fit_score,

        # Frameworks (store as JSONB)
        value_ladder=[tier.model_dump() for tier in result.data.value_ladder],
        market_gap_analysis=result.data.market_gap_analysis,
        why_now_analysis=result.data.why_now_analysis,
        proof_signals=[signal.model_dump() for signal in result.data.proof_signals],
        execution_plan=[step.model_dump() for step in result.data.execution_plan],
    )

    return insight
```

### Cost Tracking & Optimization

**LLM Cost Calculation:**

```python
# backend/app/monitoring/llm_costs.py

class LLMCostTracker:
    """Track LLM API costs with token-level granularity."""

    # Pricing (per 1M tokens)
    COSTS = {
        "claude-3-5-sonnet-20241022": {
            "input": 3.00,    # $3/M input tokens
            "output": 15.00,  # $15/M output tokens
        },
        "claude-3-haiku-20240307": {
            "input": 0.25,    # $0.25/M input tokens
            "output": 1.25,   # $1.25/M output tokens
        },
    }

    @staticmethod
    def calculate_cost(model: str, input_tokens: int, output_tokens: int) -> float:
        """Calculate cost in USD."""
        if model not in LLMCostTracker.COSTS:
            logger.warning(f"Unknown model: {model}, using Sonnet pricing")
            model = "claude-3-5-sonnet-20241022"

        pricing = LLMCostTracker.COSTS[model]

        input_cost = (input_tokens / 1_000_000) * pricing["input"]
        output_cost = (output_tokens / 1_000_000) * pricing["output"]

        return input_cost + output_cost

    @staticmethod
    async def track_llm_call(
        db: AsyncSession,
        model: str,
        input_tokens: int,
        output_tokens: int,
        task_type: str,  # "insight_analysis", "custom_research", etc.
    ):
        """Track LLM call for cost analysis."""
        cost = LLMCostTracker.calculate_cost(model, input_tokens, output_tokens)

        # Store metric
        metric = SystemMetric(
            metric_type="llm_cost",
            metric_value=cost,
            dimensions={
                "model": model,
                "task_type": task_type,
                "input_tokens": input_tokens,
                "output_tokens": output_tokens,
            }
        )
        db.add(metric)
        await db.commit()

        logger.info(f"LLM call cost: ${cost:.4f} ({model}, {input_tokens}+{output_tokens} tokens)")

        # Check daily budget
        daily_cost = await get_daily_llm_cost(db)
        if daily_cost > 50.00:
            await send_budget_alert(daily_cost)
```

**Optimization Strategies:**

1. **Prompt Compression:** Use shortest effective prompts
2. **Response Caching:** Cache common analyses for 24 hours
3. **Model Selection:** Use Haiku for simple tasks (10x cheaper)
4. **Batch Processing:** Analyze multiple signals in single call (future)

---

## User Workspace Architecture

### Data Isolation Strategy

**User Data Segregation:**

```sql
-- All user data has user_id foreign key with CASCADE delete
-- User deletes account → all related data deleted automatically

saved_insights (user_id FK)
user_ratings (user_id FK)
insight_interactions (user_id FK)
custom_analyses (user_id FK)  -- Phase 5

-- Example: User deletion cascades
DELETE FROM users WHERE id = 'user-uuid';
-- Automatically deletes:
--   - saved_insights (via ON DELETE CASCADE)
--   - user_ratings (via ON DELETE CASCADE)
--   - insight_interactions (via ON DELETE CASCADE)
```

**Query Performance:**

```python
# Efficient user data queries

# Good: Use composite index
query = (
    select(SavedInsight)
    .where(SavedInsight.user_id == user_id)
    .order_by(SavedInsight.saved_at.desc())
    .limit(20)
)
# Uses: idx_saved_insights_user_saved (user_id, saved_at DESC)

# Bad: Full table scan
query = (
    select(SavedInsight)
    .order_by(SavedInsight.saved_at.desc())
    .limit(20)
)
# No user filter → scans entire table
```

### Workspace Features Architecture

**Status Tracking State Machine:**

```
┌─────────────────────────────────────┐
│ Insight Status Lifecycle            │
├─────────────────────────────────────┤
│                                     │
│    [New] ──┬──→ [Interested]       │
│            │                        │
│            ├──→ [Saved]             │
│            │                        │
│            ├──→ [Building] ◄─ Claimed│
│            │                        │
│            └──→ [Not Interested]    │
│                                     │
│ Transitions allowed:                │
│ - Any → Interested                  │
│ - Any → Saved                       │
│ - Any → Building (sets claimed_at)  │
│ - Any → Not Interested              │
│ - Any → null (remove status)        │
└─────────────────────────────────────┘
```

**Implementation:**

```python
# backend/app/api/routes/users.py

@router.post("/insights/{insight_id}/claim")
async def claim_idea(
    insight_id: UUID,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Mark insight as 'building' (claimed by user)."""

    # Check if insight exists
    insight = await db.get(Insight, insight_id)
    if not insight:
        raise HTTPException(404, "Insight not found")

    # Check if already saved
    saved = await db.execute(
        select(SavedInsight).where(
            SavedInsight.user_id == user.id,
            SavedInsight.insight_id == insight_id,
        )
    )
    saved_insight = saved.scalar_one_or_none()

    if saved_insight:
        # Update existing record
        saved_insight.status = "building"
        saved_insight.claimed_at = datetime.now()
    else:
        # Create new saved insight with building status
        saved_insight = SavedInsight(
            user_id=user.id,
            insight_id=insight_id,
            status="building",
            claimed_at=datetime.now(),
        )
        db.add(saved_insight)

    # Track interaction
    interaction = InsightInteraction(
        user_id=user.id,
        insight_id=insight_id,
        interaction_type="claim",
        metadata={"claimed_at": datetime.now().isoformat()}
    )
    db.add(interaction)

    await db.commit()

    logger.info(f"User {user.email} claimed insight {insight_id}")

    return {
        "status": "building",
        "claimed_at": saved_insight.claimed_at.isoformat(),
        "insight_id": str(insight_id),
    }
```

---

## Database Schema Extensions

### Complete Phase 4 Schema

```sql
-- ============================================
-- PHASE 4: USER AUTHENTICATION & WORKSPACE
-- ============================================

-- Users table (base authentication)
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    clerk_user_id VARCHAR(255) UNIQUE NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL,
    display_name VARCHAR(255),
    avatar_url TEXT,
    subscription_tier VARCHAR(20) DEFAULT 'free',  -- free, starter, pro, enterprise
    preferences JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    last_login_at TIMESTAMP WITH TIME ZONE
);

CREATE INDEX idx_users_clerk_id ON users(clerk_user_id);
CREATE INDEX idx_users_email ON users(email);
CREATE INDEX idx_users_tier ON users(subscription_tier);
CREATE INDEX idx_users_created ON users(created_at DESC);

-- Saved insights (user workspace)
CREATE TABLE saved_insights (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    insight_id UUID NOT NULL REFERENCES insights(id) ON DELETE CASCADE,
    notes TEXT,
    tags VARCHAR(50)[],
    is_pursuing BOOLEAN DEFAULT false,
    status VARCHAR(20) DEFAULT 'saved',  -- interested, saved, building, not_interested
    claimed_at TIMESTAMP WITH TIME ZONE,
    saved_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    shared_count INTEGER DEFAULT 0,
    UNIQUE(user_id, insight_id)
);

CREATE INDEX idx_saved_insights_user_saved ON saved_insights(user_id, saved_at DESC);
CREATE INDEX idx_saved_insights_user_status ON saved_insights(user_id, status);
CREATE INDEX idx_saved_insights_insight ON saved_insights(insight_id);
CREATE INDEX idx_saved_insights_pursuing ON saved_insights(user_id, is_pursuing) WHERE is_pursuing = true;

-- User ratings (1-5 stars + feedback)
CREATE TABLE user_ratings (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    insight_id UUID NOT NULL REFERENCES insights(id) ON DELETE CASCADE,
    rating INTEGER CHECK (rating BETWEEN 1 AND 5),
    feedback TEXT,
    rated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(user_id, insight_id)
);

CREATE INDEX idx_user_ratings_user ON user_ratings(user_id);
CREATE INDEX idx_user_ratings_insight ON user_ratings(insight_id);
CREATE INDEX idx_user_ratings_rated ON user_ratings(rated_at DESC);

-- Insight interactions (analytics)
CREATE TABLE insight_interactions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    insight_id UUID NOT NULL REFERENCES insights(id) ON DELETE CASCADE,
    interaction_type VARCHAR(20) NOT NULL,  -- view, interested, claim, share, export
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_interactions_user ON insight_interactions(user_id);
CREATE INDEX idx_interactions_insight ON insight_interactions(insight_id);
CREATE INDEX idx_interactions_type ON insight_interactions(interaction_type);
CREATE INDEX idx_interactions_created ON insight_interactions(created_at DESC);

-- ============================================
-- PHASE 4.2: ADMIN PORTAL
-- ============================================

-- Admin users (role-based access)
CREATE TABLE admin_users (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    role VARCHAR(20) NOT NULL,  -- admin, moderator, viewer
    permissions JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(user_id)
);

CREATE INDEX idx_admin_users_user ON admin_users(user_id);
CREATE INDEX idx_admin_users_role ON admin_users(role);

-- Agent execution logs
CREATE TABLE agent_execution_logs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    agent_type VARCHAR(50) NOT NULL,  -- scraper, analyzer
    source VARCHAR(50),  -- reddit, product_hunt, google_trends
    status VARCHAR(20) NOT NULL,  -- running, completed, failed
    started_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    completed_at TIMESTAMP WITH TIME ZONE,
    duration_ms INTEGER,
    items_processed INTEGER DEFAULT 0,
    items_failed INTEGER DEFAULT 0,
    error_message TEXT,
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_agent_logs_type_status ON agent_execution_logs(agent_type, status);
CREATE INDEX idx_agent_logs_created ON agent_execution_logs(created_at DESC);
CREATE INDEX idx_agent_logs_source ON agent_execution_logs(source);

-- System metrics (LLM costs, latencies, etc.)
CREATE TABLE system_metrics (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    metric_type VARCHAR(50) NOT NULL,  -- llm_cost, api_latency, error_rate
    metric_value DECIMAL(10, 4) NOT NULL,
    dimensions JSONB DEFAULT '{}',  -- {model: "claude-3.5", task: "analysis"}
    recorded_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_metrics_type_recorded ON system_metrics(metric_type, recorded_at DESC);
CREATE INDEX idx_metrics_type ON system_metrics(metric_type);

-- Extend insights table for admin control
ALTER TABLE insights
ADD COLUMN admin_status VARCHAR(20) DEFAULT 'approved',  -- approved, rejected, pending
ADD COLUMN admin_notes TEXT,
ADD COLUMN admin_override_score FLOAT,
ADD COLUMN edited_by UUID REFERENCES admin_users(id),
ADD COLUMN edited_at TIMESTAMP WITH TIME ZONE;

CREATE INDEX idx_insights_admin_status ON insights(admin_status);
CREATE INDEX idx_insights_edited_by ON insights(edited_by);

-- ============================================
-- PHASE 4.3: MULTI-DIMENSIONAL SCORING
-- ============================================

-- Extend insights table with 8-dimension scores
ALTER TABLE insights
-- Core scores (1-10)
ADD COLUMN opportunity_score INTEGER CHECK (opportunity_score BETWEEN 1 AND 10),
ADD COLUMN problem_score INTEGER CHECK (problem_score BETWEEN 1 AND 10),
ADD COLUMN feasibility_score INTEGER CHECK (feasibility_score BETWEEN 1 AND 10),
ADD COLUMN why_now_score INTEGER CHECK (why_now_score BETWEEN 1 AND 10),

-- Business fit metrics
ADD COLUMN revenue_potential VARCHAR(10),  -- $, $$, $$$, $$$$
ADD COLUMN execution_difficulty INTEGER CHECK (execution_difficulty BETWEEN 1 AND 10),
ADD COLUMN go_to_market_score INTEGER CHECK (go_to_market_score BETWEEN 1 AND 10),
ADD COLUMN founder_fit_score INTEGER CHECK (founder_fit_score BETWEEN 1 AND 10),

-- Advanced frameworks (JSONB for flexibility)
ADD COLUMN value_ladder JSONB,  -- 4-tier pricing model
ADD COLUMN market_gap_analysis TEXT,
ADD COLUMN why_now_analysis TEXT,
ADD COLUMN proof_signals JSONB,  -- Validation evidence
ADD COLUMN execution_plan JSONB;  -- 5-7 step launch plan

-- Indexes for sorting and filtering
CREATE INDEX idx_insights_opportunity ON insights(opportunity_score DESC);
CREATE INDEX idx_insights_feasibility ON insights(feasibility_score DESC);
CREATE INDEX idx_insights_why_now ON insights(why_now_score DESC);
CREATE INDEX idx_insights_revenue ON insights(revenue_potential);
CREATE INDEX idx_insights_multi_score ON insights(
    opportunity_score DESC,
    feasibility_score DESC,
    why_now_score DESC
);

-- ============================================
-- SCHEMA SUMMARY
-- ============================================

-- Total tables: 11 (2 from v0.1 + 9 from Phase 4)
-- Total indexes: 40+
-- Total foreign keys: 15
```

### Migration Order & Dependencies

```
Migration 001: raw_signals (v0.1 - existing)
Migration 002: insights (v0.1 - existing)
Migration 003: google_trends_metadata (v0.1 - existing)

Migration 004: users, saved_insights, user_ratings (Phase 4.1)
  └─ Depends on: insights (migration 002)

Migration 005: admin_users, agent_execution_logs, system_metrics (Phase 4.2)
  └─ Depends on: users (migration 004), insights (migration 002)

Migration 006: ALTER insights (add enhanced scoring columns) - Part 1 (nullable)
  └─ Depends on: insights (migration 002)

Migration 007: insight_interactions (Phase 4.4)
  └─ Depends on: users (migration 004), insights (migration 002)

Migration 008: Backfill enhanced scores (Python script, not SQL)
  └─ Depends on: migration 006

Migration 009: ALTER insights (add NOT NULL constraints) - Part 2
  └─ Depends on: migration 008 (backfill complete)
```

---

## API Architecture Phase 4+

### Endpoint Organization

**API Structure:**

```
/api
├── /insights               # Public (Phase 1-3)
│   ├── GET /               # List all insights
│   ├── GET /{id}           # Get single insight
│   ├── GET /daily-top      # Top 5 today
│   └── GET /idea-of-the-day  # Featured insight (Phase 4.4)
│
├── /signals                # Public (Phase 1)
│   ├── GET /               # List raw signals
│   ├── GET /{id}           # Get single signal
│   └── GET /stats/summary  # Statistics
│
├── /users                  # Protected (auth required) - Phase 4.1
│   ├── GET /me             # Current user profile
│   ├── PATCH /me           # Update profile
│   ├── GET /me/saved       # List saved insights
│   ├── GET /me/interested  # List interested
│   ├── GET /me/building    # List claimed ideas
│   └── POST /insights/{id}/save  # Save insight
│       DELETE               # Unsave
│       PATCH                # Update notes/tags
│   ├── POST /insights/{id}/rate  # Rate insight
│   ├── POST /insights/{id}/interested  # Mark interested
│   ├── POST /insights/{id}/claim  # Claim idea (building)
│   ├── POST /insights/{id}/share  # Track share
│   └── GET /insights/{id}/share-stats  # Share count
│
├── /admin                  # Admin only - Phase 4.2
│   ├── GET /dashboard      # Overview metrics
│   ├── GET /events         # SSE stream (real-time)
│   ├── /agents
│   │   ├── GET /           # List all agents
│   │   ├── GET /{type}/logs  # Execution logs
│   │   ├── POST /{type}/trigger  # Manual trigger
│   │   ├── POST /{type}/pause  # Pause agent
│   │   └── POST /{type}/resume  # Resume agent
│   ├── /scrapers
│   │   ├── GET /           # List scrapers
│   │   └── PATCH /{source}  # Update config
│   ├── /insights
│   │   ├── GET /?status=pending  # Review queue
│   │   ├── PATCH /{id}     # Approve/reject
│   │   └── DELETE /{id}    # Delete insight
│   ├── /metrics
│   │   └── GET /           # Query metrics
│   ├── /errors
│   │   └── GET /           # Recent errors
│   └── /users
│       └── GET /           # User management
│
└── /health                 # Public (Phase 1)
    └── GET /               # Health check
```

### Authentication Flow

```python
# Public endpoints (no auth required)
@router.get("/api/insights")
async def list_insights():
    # Anyone can access
    pass

# User endpoints (auth required)
@router.get("/api/users/me")
async def get_profile(user: User = Depends(get_current_user)):
    # Must be authenticated
    pass

# Admin endpoints (admin role required)
@router.get("/api/admin/dashboard")
async def admin_dashboard(admin: User = Depends(require_admin)):
    # Must be admin
    pass
```

### Rate Limiting Strategy

```python
# backend/app/api/middleware/rate_limit.py

from fastapi import Request, HTTPException
from redis.asyncio import Redis
import time

class RateLimiter:
    """Tier-based rate limiting."""

    LIMITS = {
        "free": {
            "requests_per_hour": 100,
            "custom_analyses_per_month": 0,
            "exports_per_month": 5,
        },
        "starter": {
            "requests_per_hour": 500,
            "custom_analyses_per_month": 0,
            "exports_per_month": 100,
        },
        "pro": {
            "requests_per_hour": 1000,
            "custom_analyses_per_month": 20,
            "exports_per_month": -1,  # Unlimited
        },
        "enterprise": {
            "requests_per_hour": 10000,
            "custom_analyses_per_month": -1,  # Unlimited
            "exports_per_month": -1,
        },
    }

    @staticmethod
    async def check_rate_limit(
        user: User,
        resource: str,  # "requests", "custom_analyses", "exports"
        redis: Redis,
    ):
        """Check if user is within rate limit."""
        tier = user.subscription_tier
        limits = RateLimiter.LIMITS[tier]

        if resource == "requests":
            # Per-hour limit
            key = f"rate_limit:{user.id}:requests:{int(time.time() // 3600)}"
            limit = limits["requests_per_hour"]
            ttl = 3600  # 1 hour
        elif resource == "custom_analyses":
            # Per-month limit
            key = f"rate_limit:{user.id}:analyses:{time.strftime('%Y-%m')}"
            limit = limits["custom_analyses_per_month"]
            ttl = 31 * 24 * 3600  # 1 month
        elif resource == "exports":
            # Per-month limit
            key = f"rate_limit:{user.id}:exports:{time.strftime('%Y-%m')}"
            limit = limits["exports_per_month"]
            ttl = 31 * 24 * 3600

        if limit == -1:
            # Unlimited
            return

        # Increment counter
        count = await redis.incr(key)
        if count == 1:
            # Set expiry on first increment
            await redis.expire(key, ttl)

        if count > limit:
            raise HTTPException(
                status_code=429,
                detail=f"Rate limit exceeded for {resource}. Upgrade your plan for higher limits.",
                headers={"Retry-After": str(ttl)}
            )

# Usage in endpoints
@router.post("/research/analyze")
async def analyze_idea(
    request: AnalyzeRequest,
    user: User = Depends(get_current_user),
    redis: Redis = Depends(get_redis),
):
    # Check rate limit
    await RateLimiter.check_rate_limit(user, "custom_analyses", redis)

    # Proceed with analysis...
```

---

## Real-Time Communication Patterns

### Server-Sent Events (SSE) vs WebSocket

**Comparison:**

| Feature | SSE | WebSocket |
|---------|-----|-----------|
| **Direction** | Server → Client only | Bidirectional |
| **Protocol** | HTTP | WebSocket (ws://) |
| **Complexity** | Simple (regular HTTP) | Complex (separate protocol) |
| **Auto-Reconnect** | Built-in browser support | Manual implementation |
| **Browser Support** | All modern browsers | All modern browsers |
| **Use Case** | Dashboard updates, logs | Real-time chat, games |
| **Our Choice** | ✅ Yes (Admin Portal) | ❌ No (not needed) |

**When to Use Each:**

```
Use SSE when:
- Server pushes updates to client (one-way)
- Updates are periodic (every few seconds)
- Simple implementation preferred
- Example: Admin dashboard metrics

Use WebSocket when:
- Client AND server send messages (two-way)
- Real-time collaboration required
- Low latency critical (<100ms)
- Example: Chat, multiplayer games

Use Polling when:
- SSE/WS not supported
- Updates are infrequent (>30s)
- Simple fallback needed
```

---

## Security Architecture

### Defense in Depth

**Security Layers:**

```
Layer 1: Network Security
  ├─ HTTPS only (TLS 1.3)
  ├─ CORS policy (specific origins)
  └─ DDoS protection (Cloudflare)

Layer 2: Authentication
  ├─ Clerk JWT verification
  ├─ Token expiry (1 hour)
  └─ httpOnly cookies (XSS protection)

Layer 3: Authorization
  ├─ Role-based access (RBAC)
  ├─ Resource-level permissions
  └─ Admin audit logging

Layer 4: Input Validation
  ├─ Pydantic schema validation
  ├─ SQL injection (SQLAlchemy ORM)
  └─ XSS prevention (React escaping)

Layer 5: Rate Limiting
  ├─ Tier-based limits (Redis)
  ├─ Per-endpoint throttling
  └─ IP-based blocking

Layer 6: Data Protection
  ├─ Database encryption at rest
  ├─ No PII in logs
  └─ GDPR compliance
```

### OWASP Top 10 Mitigation

| Vulnerability | Mitigation Strategy | Implementation |
|---------------|---------------------|----------------|
| **A01: Broken Access Control** | RBAC + resource checks | `require_admin()`, user_id validation |
| **A02: Cryptographic Failures** | TLS, encrypted backups | HTTPS only, database encryption |
| **A03: Injection** | ORM, parameterized queries | SQLAlchemy (no raw SQL) |
| **A04: Insecure Design** | Threat modeling, security reviews | Phase-by-phase security audits |
| **A05: Security Misconfiguration** | Default deny, least privilege | Admin role required for sensitive ops |
| **A06: Vulnerable Components** | Dependency scanning | Automated npm/pip audit |
| **A07: Authentication Failures** | JWT, secure sessions | Clerk (industry-standard) |
| **A08: Software Integrity** | Code signing, SRI | Git commit signatures |
| **A09: Logging Failures** | Structured logging, audit trail | Admin action logging |
| **A10: SSRF** | Input validation, allowlist | Validate URLs before scraping |

---

## Performance Architecture

### Caching Strategy

**Multi-Level Caching:**

```
┌──────────────────────────────────┐
│ Level 1: Browser Cache           │
│ - Static assets (1 year)         │
│ - API responses (ETags)          │
└──────────────────────────────────┘
         ↓ (Cache miss)
┌──────────────────────────────────┐
│ Level 2: React Query Cache       │
│ - Insights list (60s stale time) │
│ - User profile (5min)            │
└──────────────────────────────────┘
         ↓ (Cache miss)
┌──────────────────────────────────┐
│ Level 3: Redis Cache             │
│ - Daily top insights (5min TTL)  │
│ - Agent status (30s TTL)         │
│ - Rating stats (5min TTL)        │
└──────────────────────────────────┘
         ↓ (Cache miss)
┌──────────────────────────────────┐
│ Level 4: Database                │
│ - PostgreSQL with indexes        │
│ - Query result caching           │
└──────────────────────────────────┘
```

**Redis Caching Implementation:**

```python
# backend/app/cache/redis_cache.py

import json
from typing import Any, Optional
from redis.asyncio import Redis

class CacheService:
    """Centralized caching service."""

    def __init__(self, redis: Redis):
        self.redis = redis

    async def get(self, key: str) -> Optional[Any]:
        """Get cached value."""
        value = await self.redis.get(key)
        if value:
            return json.loads(value)
        return None

    async def set(self, key: str, value: Any, ttl: int = 300):
        """Set cached value with TTL (default 5 minutes)."""
        await self.redis.setex(
            key,
            ttl,
            json.dumps(value, default=str)  # Handle datetimes
        )

    async def delete(self, key: str):
        """Delete cached value."""
        await self.redis.delete(key)

    async def get_or_set(
        self,
        key: str,
        fetch_fn: callable,
        ttl: int = 300,
    ) -> Any:
        """Get from cache or fetch and cache."""
        # Try cache first
        value = await self.get(key)
        if value is not None:
            return value

        # Cache miss - fetch fresh data
        value = await fetch_fn()

        # Cache for future requests
        await self.set(key, value, ttl)

        return value

# Usage in endpoints
@router.get("/api/insights/daily-top")
async def get_daily_top(cache: CacheService = Depends(get_cache)):
    """Get top 5 insights (cached for 5 minutes)."""

    async def fetch_daily_top():
        # Fetch from database
        results = await db.execute(
            select(Insight)
            .where(Insight.created_at >= date.today())
            .order_by(Insight.relevance_score.desc())
            .limit(5)
        )
        return [insight.to_dict() for insight in results.scalars()]

    return await cache.get_or_set(
        key="daily_top_insights",
        fetch_fn=fetch_daily_top,
        ttl=300,  # 5 minutes
    )
```

### Database Query Optimization

**Index Strategy:**

```sql
-- Single-column indexes (basic lookups)
CREATE INDEX idx_users_email ON users(email);

-- Composite indexes (multi-column queries)
CREATE INDEX idx_saved_insights_user_saved ON saved_insights(user_id, saved_at DESC);
-- Supports: WHERE user_id = ? ORDER BY saved_at DESC

-- Partial indexes (filtered queries)
CREATE INDEX idx_insights_high_score ON insights(opportunity_score)
WHERE opportunity_score >= 8;
-- Supports: WHERE opportunity_score >= 8 (smaller, faster index)

-- Expression indexes (computed columns)
CREATE INDEX idx_insights_avg_score ON insights((
    (opportunity_score + feasibility_score + why_now_score) / 3
));
-- Supports: ORDER BY (opportunity_score + feasibility_score + why_now_score) / 3
```

**Query Performance Monitoring:**

```python
# backend/app/middleware/query_logging.py

import time
from sqlalchemy import event
from sqlalchemy.engine import Engine

# Log slow queries (>100ms)
@event.listens_for(Engine, "before_cursor_execute")
def before_cursor_execute(conn, cursor, statement, parameters, context, executemany):
    context._query_start_time = time.time()

@event.listens_for(Engine, "after_cursor_execute")
def after_cursor_execute(conn, cursor, statement, parameters, context, executemany):
    duration = time.time() - context._query_start_time
    if duration > 0.1:  # 100ms threshold
        logger.warning(
            f"Slow query ({duration:.2f}s): {statement[:200]}",
            extra={"duration_ms": duration * 1000, "query": statement}
        )
```

---

## Conclusion

---

<!-- Supabase Cloud architecture added on 2026-01-25 for Phase 4.5 migration -->

## 10. Phase 4.5: Supabase Cloud Architecture

### 10.1 Supabase Stack Overview

**Components:**
- **PostgreSQL**: Managed database (AWS Singapore ap-southeast-1)
- **PostgREST**: Auto-generated REST API from schema
- **GoTrue**: Authentication service (optional, using Clerk for now)
- **Realtime**: WebSocket server for live updates (Phase 5.1)
- **Storage**: S3-compatible object storage (Phase 5.2)
- **Edge Functions**: Deno runtime for serverless (Phase 5.3)

**StartInsight Usage (Phase 4.5):**
- PostgreSQL: ✅ Primary database
- PostgREST: ⚠️ Optional (still using FastAPI for complex queries)
- GoTrue: ❌ Not used (Clerk for authentication)
- Realtime: 🔜 Phase 5.1
- Storage: 🔜 Phase 5.2
- Edge Functions: 🔜 Phase 5.3

### 10.2 Row Level Security (RLS) Policies

**Principle:** Users can only access their own data (multi-tenant isolation)

**Tables with RLS:**
1. `users` - Users view their own profile
2. `saved_insights` - Users view their saved insights
3. `user_ratings` - Users view their ratings
4. `raw_signals` - Public read (admin write)
5. `insights` - Public read (system write)

**Example RLS Policies (SQL):**

```sql
-- users table: Users can view and update their own profile
ALTER TABLE users ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Users can view own profile"
  ON users FOR SELECT
  USING (clerk_user_id = auth.jwt() ->> 'sub');

CREATE POLICY "Users can update own profile"
  ON users FOR UPDATE
  USING (clerk_user_id = auth.jwt() ->> 'sub');

-- saved_insights table: Users can manage their own saved insights
ALTER TABLE saved_insights ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Users view own saved insights"
  ON saved_insights FOR SELECT
  USING (user_id = (SELECT id FROM users WHERE clerk_user_id = auth.jwt() ->> 'sub'));

CREATE POLICY "Users insert own saved insights"
  ON saved_insights FOR INSERT
  WITH CHECK (user_id = (SELECT id FROM users WHERE clerk_user_id = auth.jwt() ->> 'sub'));

CREATE POLICY "Users delete own saved insights"
  ON saved_insights FOR DELETE
  USING (user_id = (SELECT id FROM users WHERE clerk_user_id = auth.jwt() ->> 'sub'));

-- insights table: Public read, system write
ALTER TABLE insights ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Anyone can read insights"
  ON insights FOR SELECT
  USING (true);

CREATE POLICY "Only service role can write"
  ON insights FOR INSERT
  WITH CHECK (auth.role() = 'service_role');
```

**RLS Configuration:**
- Enable RLS on all tables during migration (Week 1)
- Use `auth.jwt()` to extract Clerk user ID from JWT
- Service role bypasses RLS (backend uses service_role key)

### 10.3 Database Architecture Decision (2026-01-25)

**Production Database:** Supabase Cloud (Singapore ap-southeast-1)
**Connection Method:** Dual-mode support

#### Primary: SQLAlchemy (ORM Operations)
- Connection: PostgreSQL protocol via AsyncPG
- Usage: All CRUD operations, Alembic migrations
- Supabase URL: `postgresql://[user]:[pass]@db.[project].supabase.co:5432/postgres`
- Advantage: Type-safe ORM, migration version control

#### Secondary: Supabase Client (Advanced Features)
- Connection: Supabase REST API + WebSocket
- Usage: Row-Level Security, real-time subscriptions (Phase 5+), storage
- Advantage: Built-in RLS, real-time, edge functions

#### Local Development Options

**Option A: Supabase Cloud (Recommended)**
- Best for testing RLS policies
- Same environment as production
- Required for real-time feature testing

**Option B: Docker PostgreSQL (Faster Iteration)**
- Offline development capability
- Faster test execution (no network latency)
- Cost-free local iterations
- Rollback safety net

#### Why Keep PostgreSQL Docker?
1. Offline development capability
2. Faster test execution (no network latency)
3. Cost-free local iterations
4. Rollback safety if Supabase issues arise
5. Supabase IS PostgreSQL (100% compatible)

**Migration Status:** Backend 100% ready, pending Supabase project creation

### 10.4 Connection Pooling

#### Current (SQLAlchemy)

```python
# backend/app/db/session.py
engine = create_async_engine(
    DATABASE_URL,
    pool_size=5,
    max_overflow=10
)  # Max 15 connections
```

**Supabase Cloud:**
- **Pooler Mode**: Transaction pooling (PgBouncer)
- **Max Connections**: 500 concurrent (Pro tier)
- **Connection String**: `postgresql://postgres:password@db.pooler.supabase.co:6543/postgres`

**Hybrid Approach (Phase 4.5):**
```python
# backend/app/db/session.py
from supabase import create_client, Client
from sqlalchemy.ext.asyncio import create_async_engine

# SQLAlchemy (keep during transition)
pg_engine = create_async_engine(
    settings.DATABASE_URL,
    pool_size=5,
    max_overflow=10
)

# Supabase client (new)
supabase: Client = create_client(
    settings.SUPABASE_URL,
    settings.SUPABASE_SERVICE_ROLE_KEY
)

# Dual-write wrapper
class DualWriteSession:
    async def add(self, obj):
        await pg_session.add(obj)  # Write to PostgreSQL
        await supabase.table(obj.__tablename__).insert(obj.dict())  # Write to Supabase

    async def commit(self):
        await pg_session.commit()
        # Supabase commit is automatic (no transactions in PostgREST)
```

### 10.5 Real-time Features (Phase 5.1)

**Supabase Realtime vs Current SSE:**

| Feature | SSE (Current) | Supabase Realtime |
|---------|---------------|-------------------|
| Protocol | HTTP long-polling | WebSocket |
| Latency | 1-5s | <100ms |
| Client lib | EventSource API | @supabase/realtime-js |
| Server complexity | High (Redis, FastAPI) | Low (built-in) |
| Scalability | Manual (Redis cluster) | Auto-scaled |
| Cost | Redis: $5/mo | Included in Pro |

**Migration Path:**
- Phase 4.5: Keep SSE for admin dashboard
- Phase 5.1: Migrate to Supabase Realtime for insights feed
- Phase 5.2: Deprecate custom SSE implementation

**Example (Python → TypeScript):**

```python
# Current SSE (backend/app/api/routes/sse.py)
@router.get("/stream")
async def stream_insights(request: Request):
    async def event_generator():
        while True:
            if await request.is_disconnected():
                break
            insight = await redis.get("latest_insight")
            yield f"data: {insight}\n\n"
            await asyncio.sleep(1)
    return EventSourceResponse(event_generator())
```

```typescript
// Supabase Realtime (frontend/app/insights/page.tsx)
useEffect(() => {
  const subscription = supabase
    .channel('insights')
    .on('postgres_changes', {
      event: 'INSERT',
      schema: 'public',
      table: 'insights'
    }, (payload) => {
      setInsights(prev => [payload.new, ...prev])
    })
    .subscribe()

  return () => subscription.unsubscribe()
}, [])
```

### 10.6 Migration Risks & Mitigation

| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|------------|
| Data loss during migration | Low | Critical | Dual-write, validation scripts, backups |
| Latency regression | Medium | High | Load testing, Singapore region, connection pooling |
| RLS misconfiguration | Medium | Critical | Test suite with multi-user scenarios |
| Supabase downtime | Low | High | Fallback to PostgreSQL, 99.9% SLA monitoring |
| Cost overrun | Low | Medium | Pro tier limit ($25/mo), usage alerts |
| JWT auth issues | Medium | High | Clerk + Supabase JWT compatibility testing |

**Monitoring Plan:**
- Pre-migration: Baseline latency (p50, p95, p99), error rate, throughput
- During migration: Real-time dashboard (Grafana), alerting (PagerDuty)
- Post-migration: 48-hour intensive monitoring, 2-week gradual relaxation

---

## Conclusion

This architecture provides a solid foundation for StartInsight's MVP while remaining flexible for future enhancements. The modular design ensures each component (Collector, Analyst, Presenter) can be developed, tested, and deployed independently.

**Key Architectural Principles**:
1. **Separation of Concerns**: Clear boundaries between data collection, analysis, and presentation
2. **Async-First**: All I/O operations leverage async/await for performance
3. **Type Safety**: Pydantic (backend) and TypeScript (frontend) ensure data integrity
4. **Scalability**: Modular architecture allows horizontal scaling of workers and API servers
5. **Maintainability**: Well-documented code structure with clear naming conventions

**Next Steps**: Proceed to Phase 1.1 (Project Initialization) as outlined in `implementation-plan.md`.

---

**Document Version**: 1.1
**Last Updated**: 2026-01-18
**Author**: Lead Architect (Claude)
**Status**: Production-Ready Blueprint
