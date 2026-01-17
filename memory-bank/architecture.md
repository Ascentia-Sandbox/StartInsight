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
├── tests/                         # Unit & integration tests
│   ├── __init__.py
│   ├── test_scrapers.py
│   ├── test_agents.py
│   └── test_api.py
│
├── .env.example                   # Example environment variables
├── pyproject.toml                 # Python dependencies (uv/poetry)
├── Dockerfile                     # Production Docker image
└── README.md                      # Backend setup instructions
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
└── README.md                      # Frontend setup instructions
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
├── docker-compose.yml             # Local dev environment
├── .gitignore                     # Git ignore rules
├── README.md                      # Project overview
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

## 6. API Endpoints Reference

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

## 10. Future Architectural Enhancements (Post-MVP)

### Phase 4: User Customization
- Add `users` table with authentication (Clerk/Auth0)
- Add `user_keywords` table for custom tracking
- Add `saved_insights` table for favorites

### Phase 5: Advanced Analysis
- Implement multi-agent workflows (LangChain)
- Add `competitors` table with automated research
- Add `mvp_plans` table with tech stack suggestions

### Phase 6: Real-Time Updates
- WebSocket endpoint (`/ws`) for live insight updates
- Server-Sent Events (SSE) for dashboard auto-refresh
- Push notifications via Firebase Cloud Messaging

### Phase 7: Data Source Expansion
- Twitter/X scraping (via Apify)
- Indie Hackers forum scraping
- Y Combinator news scraping
- Patent database integration

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
