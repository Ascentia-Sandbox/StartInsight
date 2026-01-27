---
**Memory Bank Protocol**
**Reading Priority:** CRITICAL
**Read When:** When choosing libraries, verifying dependencies, resolving conflicts, cost planning
**Dependencies:** Read project-brief.md for "Glue Coding" philosophy
**Purpose:** Phase 1-7 dependencies, cost analysis ($639/mo at 10K users), revenue projections ($59K MRR)
**Last Updated:** 2026-01-25
---

Tech Stack: StartInsight
1. High-Level Architecture
Architecture Type: Modular Monolith (separate Frontend/Backend repos or Monorepo)

Communication: REST API (FastAPI) + WebSockets (Real-time updates)

Deployment Strategy: Dockerized containers (Railway/Render)

2. Frontend (The Dashboard)
Framework: Next.js 14+ (App Router) - React production framework.

Language: TypeScript - Strict typing for reliability.

Styling: Tailwind CSS - Utility-first CSS.

UI Components: shadcn/ui - Copy-paste accessible components (based on Radix UI).

State Management: React Query (TanStack Query) - Server state management.

Charting: Recharts v3.6.0 (React 19 compatible) - Data visualization for trend graphs and evidence presentation.

**VISUALIZATION MANDATE (Post-Ralph-Loop 2026-01-25):**
Every insight MUST include data-driven visualizations. Evidence MUST be visual, not just textual.

**Visualization Stack Strategy (Updated 2026-01-25):**
  - **Primary**: Recharts v3.6.0 (React 19.2.3 compatible) - ✅ Installed
  - **Complementary**: Tremor v3.16.0 for admin dashboards and KPI cards - ⚠️ Pending installation
  - **Current Choice**: Dual-stack approach (Recharts + Tremor + shadcn/ui)
  - **Reasoning**:
    - Recharts: Complex custom visualizations (trend charts, radar charts) - full control
    - Tremor: Financial charts, KPI cards, admin dashboards - cleaner API, less boilerplate
    - shadcn/ui: Layout primitives, buttons, badges, forms
  - **Competitive Analysis Finding**: IdeaBrowser uses Google Trends embedded charts (limited customization). StartInsight's dual-stack provides superior flexibility and visual quality.

**Implemented Components (Phase 5.2 - 40% Complete):**
  - ✅ TrendChart.tsx: Line charts for Google Trends search volume (Phase 3)
  - ⚠️ CommunitySignalsRadar.tsx: RadarChart or AreaChart for 4-platform engagement (PLANNED)
  - ⚠️ ScoreRadar.tsx: RadarChart for 8-dimension scoring visualization (PLANNED)
  - ⚠️ TrendKeywordCards.tsx: Keyword cards with volume + growth badges (PLANNED)
  - ⚠️ EvidencePanel Accordion: Collapsible sections for data sources (PLANNED)

**Evidence-First Requirements:**
Each insight requires minimum 3 visualizations:
  1. Trend line chart (search volume over time) - ✅ IMPLEMENTED
  2. Community signals chart (4-platform engagement) - ⚠️ PLANNED
  3. Scoring visualization (8-dimension radar or bar chart) - ⚠️ PLANNED

**Competitive Positioning:**
  - **IdeaBrowser**: Google Trends embedded charts, basic badges
  - **StartInsight**: Multi-chart evidence presentation (trend + community + scoring)
  - **Advantage**: Visual evidence for every claim (charts > badges)

3. Backend (The Intelligence Engine)
Framework: FastAPI - High-performance, async Python framework. Perfect for AI/IO-bound tasks.

Language: Python 3.11+

Process Manager: Uvicorn (ASGI server)

Validation: Pydantic V2 - Data validation and settings management.

4. Database & Storage (The Vault)
Primary Database: PostgreSQL - Robust relational database.

Local Dev: Docker container.

Production: Neon or Railway (Managed Postgres).

ORM: SQLAlchemy (Async) or Prisma Client Python - Type-safe database interaction.

Migrations: Alembic - Database schema version control.

Caching/Queue: Redis - Task queue for scheduled scrapers and caching hot insights.

5. AI & Data Pipeline (The "Vibe" Layer)

**LLM Agent Orchestration**
- **Primary Framework**: LangChain or PydanticAI
  - **LangChain** (if chosen):
    - `langchain-core`: Core abstractions and interfaces.
    - `langchain-openai` or `langchain-anthropic`: LLM provider integrations.
    - `langchain-community`: Additional integrations (Reddit API, etc.).
    - Use LCEL (LangChain Expression Language) for composable chains.
  - **PydanticAI** (if chosen):
    - Type-safe agent framework with built-in Pydantic validation.
    - Simpler API, better for structured output extraction.
    - Native async support.
- **[x] Decision (LOCKED)**: Use PydanticAI for MVP (Phases 1-3).
  - **Reason**: Simpler API, native Pydantic validation, adequate for single-agent analysis tasks.
  - **Migration Path**: If Phase 4+ requires complex multi-agent workflows or advanced tooling, evaluate LangChain migration at that time.
  - **Current Status**: PydanticAI installed (`pydantic-ai>=0.0.13` in `pyproject.toml`).

**LLM Provider**
- **Primary**: Google Gemini 2.0 Flash (via `google-generativeai` Python SDK)
  - 97% cost reduction vs Claude ($0.10/M input, $0.40/M output vs $3/$15)
  - 1M token context window for processing multiple signals at once.
  - Excellent at structured JSON output and reasoning tasks.
- **Fallback**: Anthropic Claude 3.5 Sonnet (via `anthropic` Python SDK)
  - Use if Gemini quota exceeded or for complex reasoning tasks.
- **Fallback**: OpenAI GPT-4o (via `openai` Python SDK)
  - Use for vision tasks (analyzing screenshots from Product Hunt).
- **Environment Variables**: Store API keys in `.env` files (never commit).

**Web Scraping & Data Extraction**
- **Primary Tool**: Firecrawl
  - **Library**: `firecrawl-py` (Official Python SDK)
  - **Purpose**: Convert web pages into clean, LLM-ready Markdown.
  - **Use Cases**:
    - Scraping Reddit threads (bypasses need for CSS selectors).
    - Extracting Product Hunt launches.
    - Reading blog posts and documentation.
  - **API**: Requires Firecrawl API key (cloud service).
- **Alternative/Supplementary**: Crawl4AI (self-hosted option)
  - Open-source, runs locally without API costs.
  - Trade-off: Requires more infrastructure setup.
- **Reddit-Specific**: `praw` (Python Reddit API Wrapper)
  - For structured Reddit data (scores, timestamps, subreddit metadata).
  - Complements Firecrawl by providing additional context.
- **Google Trends**: `pytrends` (Unofficial Google Trends API)
  - Extract search volume data for keywords.

**Task Scheduling & Queue**
- **Primary**: Arq (async task queue for Python)
  - Built on Redis, async-native (integrates perfectly with FastAPI).
  - Lighter than Celery, simpler setup.
- **Alternative**: Celery + Redis
  - More mature, better for complex workflows.
  - Use if we need advanced features (task retries, priority queues).

**Core Python Dependencies (Backend)**
```txt
# API Framework
fastapi>=0.109.0
uvicorn[standard]>=0.27.0
pydantic>=2.5.0
pydantic-settings>=2.1.0

# Database
sqlalchemy[asyncio]>=2.0.25
alembic>=1.13.0
asyncpg>=0.29.0  # Async PostgreSQL driver
redis>=5.0.1

# AI & Agents
pydantic-ai>=0.0.13  # Agent orchestration with structured output
google-generativeai>=0.8.0  # Primary: Gemini 2.0 Flash
anthropic>=0.25.0  # Fallback: Claude 3.5 Sonnet
openai>=1.12.0  # Fallback: GPT-4o

# Web Scraping
firecrawl-py>=0.0.16
praw>=7.7.1  # Reddit API
pytrends>=4.9.2  # Google Trends

# Task Queue
arq>=0.25.0

# Utilities
python-dotenv>=1.0.0  # Environment variables
httpx>=0.26.0  # Async HTTP client
```

**Core Frontend Dependencies (Next.js)**
```json
{
  "dependencies": {
    "next": "^14.1.0",
    "react": "^18.2.0",
    "react-dom": "^18.2.0",
    "@tanstack/react-query": "^5.20.0",
    "tailwindcss": "^3.4.0",
    "recharts": "^2.10.0",
    "date-fns": "^3.3.0",
    "zod": "^3.22.0"
  },
  "devDependencies": {
    "typescript": "^5.3.0",
    "@types/react": "^18.2.0",
    "@types/node": "^20.11.0",
    "eslint": "^8.56.0",
    "prettier": "^3.2.0"
  }
}
```

**Notes on Frontend Dependencies:**
- **`zod`**: Used for runtime type validation of API responses and form data. Ensures type safety between frontend TypeScript and backend Pydantic schemas.
- **`shadcn/ui`**: NOT listed in `package.json` because it's installed via CLI (`npx shadcn-ui@latest add button card badge`). Components are copied directly into your codebase (`/components/ui/`), not installed as an npm package. See Phase 3.1 in `implementation-plan.md` for installation instructions.

### Builder Integration Dependencies (Phase 5.2 Extension)

**Purpose:** Enable one-click deployment to external builder platforms

**Current Implementation:**
- Brand Package Generator: [x] Implemented (backend/app/services/brand_generator.py)
- Landing Page Generator: [x] Implemented (backend/app/services/landing_page.py)
- Dependencies: anthropic (Claude API), jinja2 (template engine)

**Planned Extensions (Phase 5.3+):**
- No new dependencies required (using existing anthropic + jinja2)
- Builder integration is URL-based (query parameters, no SDK integration)
- Pre-filled prompts generated server-side (FastAPI)
- Frontend opens builder URLs in new tab (window.open)

**Cost Impact:**
- Additional LLM calls: +$0.05 per prompt generation (100-200 tokens output)
- Total cost per insight build: $0.05 (negligible)

**Alternatives Rejected:**
- Playwright/Selenium (automated form filling): Too complex, brittle
- Custom SDKs (Lovable SDK, v0 SDK): Not available, proprietary
- Chosen: URL-based integration (universal, low-maintenance)

---

## Environment Variable Conventions

**Backend (Python with Pydantic Settings):**
- **File Format**: Use UPPERCASE names in `.env` files
- **Auto-Conversion**: Pydantic Settings automatically converts UPPERCASE → lowercase Python properties
- **Example**:
  ```bash
  # .env file
  DATABASE_URL=postgresql+asyncpg://user:pass@localhost:5433/startinsight
  REDIS_URL=redis://localhost:6379
  GOOGLE_API_KEY=AIza...  # Primary: Gemini
  ANTHROPIC_API_KEY=sk-ant-...  # Fallback: Claude
  API_HOST=0.0.0.0
  API_PORT=8000
  ```
  ```python
  # backend/app/core/config.py (auto-mapped)
  from pydantic_settings import BaseSettings

  class Settings(BaseSettings):
      database_url: PostgresDsn  # Maps from DATABASE_URL
      redis_url: RedisDsn         # Maps from REDIS_URL
      anthropic_api_key: str      # Maps from ANTHROPIC_API_KEY
      api_host: str               # Maps from API_HOST
      api_port: int               # Maps from API_PORT

      class Config:
          env_file = ".env"
  ```
- **Convention**: Always use UPPERCASE in `.env` files, lowercase in Python code

**Frontend (Next.js):**
- **Public Variables**: Prefix with `NEXT_PUBLIC_` to expose to browser
- **Example**:
  ```bash
  # frontend/.env.local
  NEXT_PUBLIC_API_URL=http://localhost:8000
  ```
- **Access**: Use `process.env.NEXT_PUBLIC_API_URL` in client components

---

6. Development Tools
Package Manager:

Frontend: pnpm (Fast, disk-efficient package manager).

Backend: uv (Blazing-fast Python package manager) or poetry.

Linting/Formatting:

Frontend: ESLint + Prettier

Backend: Ruff (Fast Python linter/formatter).

Version Control: Git


<\!-- Phase 4+ tech stack merged from tech-stack-phase4-addendum.md on 2026-01-24 -->

## Phase 4 Dependencies

### Backend (Python)

```toml
# backend/pyproject.toml

[project]
dependencies = [
    # ============================================
    # PHASE 1-3 (Existing - v0.1)
    # ============================================
    "fastapi>=0.109.0",
    "uvicorn[standard]>=0.27.0",
    "pydantic>=2.5.0",
    "pydantic-settings>=2.1.0",
    "sqlalchemy[asyncio]>=2.0.25",
    "alembic>=1.13.0",
    "asyncpg>=0.29.0",
    "redis>=5.0.1",
    "pydantic-ai>=0.0.13",
    "anthropic>=0.25.0",
    "openai>=1.12.0",
    "firecrawl-py>=0.0.16",
    "praw>=7.7.1",
    "pytrends>=4.9.2",
    "arq>=0.25.0",
    "python-dotenv>=1.0.0",
    "httpx>=0.26.0",
    "tenacity>=8.2.3",

    # ============================================
    # PHASE 4.1: USER AUTHENTICATION
    # ============================================
    "clerk-backend-api>=2.0.0",  # Clerk SDK for JWT verification

    # ============================================
    # PHASE 4.2: ADMIN PORTAL
    # ============================================
    "sse-starlette>=2.0.0",  # Server-Sent Events for real-time updates

    # ============================================
    # PHASE 5: EXPORT FEATURES
    # ============================================
    "reportlab>=4.0.0",  # PDF generation (better quality)
    # OR
    "weasyprint>=60.0",  # Alternative PDF (HTML → PDF)

    # ============================================
    # PHASE 6: PAYMENTS & EMAIL
    # ============================================
    "stripe>=7.0.0",  # Payment processing
    "resend>=0.8.0",  # Email notifications
    # OR
    "sendgrid>=6.11.0",  # Alternative email service

    # ============================================
    # PHASE 6: RATE LIMITING
    # ============================================
    "fastapi-limiter>=0.1.6",  # Redis-based rate limiting

    # ============================================
    # PHASE 7: ADDITIONAL SCRAPERS
    # ============================================
    "tweepy>=4.14.0",  # Twitter/X API
    # OR
    "twikit>=2.0.0",  # Alternative Twitter scraper (no API key)

    # ============================================
    # UTILITIES (Phase 4+)
    # ============================================
    "tiktoken>=0.5.2",  # Accurate token counting for LLM costs
    "pillow>=10.0.0",  # Image generation for brand packages
    "jinja2>=3.1.2",  # Template engine for landing pages/emails
]

[project.optional-dependencies]
dev = [
    "pytest>=7.4.0",
    "pytest-asyncio>=0.21.0",
    "pytest-cov>=4.1.0",
    "ruff>=0.1.0",
    "mypy>=1.7.0",
    "httpx>=0.26.0",  # For testing
]
```

**Dependency Justification:**

| Dependency | Purpose | Why Chosen | Alternatives Rejected |
|------------|---------|------------|----------------------|
| **clerk-backend-api** | JWT verification | Next.js native, generous free tier (10K MAU) | Auth0 ($240/yr), NextAuth (more setup) |
| **sse-starlette** | Real-time updates | Simple HTTP-based streaming for admin portal | WebSocket (overkill), Polling (inefficient) |
| **reportlab** | PDF export | Industry standard, high quality | PyPDF2 (no generation), wkhtmltopdf (deprecated) |
| **stripe** | Payments | Best developer experience, 2.9% + $0.30 | PayPal (higher fees), Paddle (complex) |
| **resend** | Email | Modern API, free 3K emails/month | SendGrid (complex), Mailgun (expensive) |
| **tiktoken** | Token counting | Official OpenAI library, accurate | Approximation (4 chars/token) |

---

### Frontend (JavaScript/TypeScript)

```json
{
  "name": "startinsight-frontend",
  "version": "0.2.0",
  "dependencies": {
    // ============================================
    // PHASE 1-3 (Existing - v0.1)
    // ============================================
    "next": "^16.1.3",
    "react": "^19.2.3",
    "react-dom": "^19.2.3",
    "@tanstack/react-query": "^5.20.0",
    "tailwindcss": "^4.0.0",
    "recharts": "^2.10.0",
    "date-fns": "^3.3.0",
    "zod": "^3.22.0",
    "axios": "^1.6.0",
    "lucide-react": "^0.263.1",

    // ============================================
    // PHASE 4.1: USER AUTHENTICATION
    // ============================================
    "@clerk/nextjs": "^5.0.0",  // Clerk SDK for Next.js

    // ============================================
    // PHASE 4.2: ADMIN PORTAL
    // ============================================
    "@tanstack/react-table": "^8.11.0",  // Advanced tables for logs
    // Note: SSE uses built-in EventSource API (no package needed)

    // ============================================
    // PHASE 4.4: SHARING & INTERACTIONS
    // ============================================
    "react-share": "^5.0.0",  // Social sharing components
    // Note: Optional, can implement custom share buttons

    // ============================================
    // PHASE 5: BUILD TOOLS
    // ============================================
    "html2canvas": "^1.4.0",  // Screenshot generation
    "jspdf": "^2.5.0",  // Client-side PDF generation (optional)

    // ============================================
    // PHASE 6: RICH TEXT EDITOR
    // ============================================
    "@tiptap/react": "^2.1.0",  // Rich text editor (for custom analyses)
    "@tiptap/starter-kit": "^2.1.0",

    // ============================================
    // PHASE 6: CHARTS & VISUALIZATION
    // ============================================
    // (recharts already included from Phase 3)
    "d3": "^7.8.0",  // Optional: Advanced visualizations
  },
  "devDependencies": {
    "typescript": "^5.3.0",
    "@types/react": "^19.0.0",
    "@types/node": "^20.11.0",
    "eslint": "^8.56.0",
    "prettier": "^3.2.0",
    "@playwright/test": "^1.57.0",  // E2E testing
    "eslint-config-next": "^16.1.3"
  }
}
```

**Frontend Dependency Justification:**

| Dependency | Purpose | Why Chosen | Alternatives |
|------------|---------|------------|-------------|
| **@clerk/nextjs** | Authentication | Best Next.js integration, free tier | NextAuth (DIY), Auth0 (expensive) |
| **@tanstack/react-table** | Admin logs table | Feature-rich, headless UI | Material Table (bloated), Custom (time-consuming) |
| **react-share** | Social sharing | Pre-built share buttons | Custom implementation |
| **@tiptap/react** | Rich text editor | Modern, extensible, React-native | Slate (complex), Quill (jQuery), Draft.js (deprecated) |

---

## Environment Variables (Phase 4+)

### Backend Environment Variables

```bash
# backend/.env

# ============================================
# PHASE 1-3 (Existing)
# ============================================
DATABASE_URL=postgresql+asyncpg://user:pass@localhost:5433/startinsight
REDIS_URL=redis://localhost:6379
FIRECRAWL_API_KEY=fc-***
REDDIT_CLIENT_ID=***
REDDIT_CLIENT_SECRET=***
REDDIT_USERNAME=***
GOOGLE_API_KEY=AIza...  # Primary: Gemini 2.0 Flash
ANTHROPIC_API_KEY=sk-ant-***  # Fallback: Claude 3.5 Sonnet
OPENAI_API_KEY=sk-***  # Fallback: GPT-4o
API_HOST=0.0.0.0
API_PORT=8000

# ============================================
# PHASE 4.1: CLERK AUTHENTICATION
# ============================================
CLERK_SECRET_KEY=sk_test_...  # Backend JWT verification key
CLERK_FRONTEND_API=clerk.startinsight.app  # Clerk domain

# ============================================
# PHASE 6.2: STRIPE PAYMENTS
# ============================================
STRIPE_SECRET_KEY=sk_test_...  # Test key for development
STRIPE_WEBHOOK_SECRET=whsec_...  # For webhook verification
STRIPE_PUBLISHABLE_KEY=pk_test_...  # Frontend key (NOT secret)

# ============================================
# PHASE 6.3: EMAIL (RESEND)
# ============================================
RESEND_API_KEY=re_...  # Resend API key
RESEND_FROM_EMAIL=noreply@startinsight.app  # Verified sender

# ============================================
# PHASE 7.1: TWITTER/X API
# ============================================
TWITTER_BEARER_TOKEN=...  # Twitter API v2 bearer token
# OR (for twikit)
TWITTER_USERNAME=...
TWITTER_PASSWORD=...

# ============================================
# MONITORING & ALERTS
# ============================================
SENTRY_DSN=https://...  # Error tracking (optional)
SLACK_WEBHOOK_URL=https://hooks.slack.com/...  # Admin alerts
```

### Frontend Environment Variables

```bash
# frontend/.env.local

# ============================================
# PHASE 1-3 (Existing)
# ============================================
NEXT_PUBLIC_API_URL=http://localhost:8000

# ============================================
# PHASE 4.1: CLERK AUTHENTICATION
# ============================================
NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY=pk_test_...
CLERK_SECRET_KEY=sk_test_...
NEXT_PUBLIC_CLERK_SIGN_IN_URL=/sign-in
NEXT_PUBLIC_CLERK_SIGN_UP_URL=/sign-up
NEXT_PUBLIC_CLERK_SIGN_IN_FORCE_REDIRECT_URL=/workspace
NEXT_PUBLIC_CLERK_SIGN_UP_FORCE_REDIRECT_URL=/workspace

# ============================================
# PHASE 6.2: STRIPE PAYMENTS (Frontend)
# ============================================
NEXT_PUBLIC_STRIPE_PUBLISHABLE_KEY=pk_test_...

# ============================================
# ANALYTICS (Optional)
# ============================================
NEXT_PUBLIC_GA_MEASUREMENT_ID=G-...  # Google Analytics
NEXT_PUBLIC_POSTHOG_KEY=phc_...  # PostHog analytics
```

---

## Technology Decisions & Rationale

### Authentication: Clerk vs Alternatives

**Decision: Clerk ✅**

**Comparison:**

| Feature | Clerk | Auth0 | NextAuth |
|---------|-------|-------|----------|
| **Free Tier** | 10K MAU | 7K MAU (then $35/mo) | Unlimited |
| **Next.js Integration** | Excellent (native) | Good | Excellent |
| **JWT Support** | Built-in | Built-in | Manual |
| **Social Logins** | 20+ providers | 30+ providers | OAuth 2.0 |
| **Setup Time** | 15 minutes | 30 minutes | 60 minutes |
| **Cost at 50K users** | $125/mo | $240/mo | $0 (self-hosted) |
| **Security** | Managed | Managed | Self-managed |

**Why Clerk:**
1. Best Next.js developer experience
2. Generous free tier (10K MAU vs 7K for Auth0)
3. No server setup needed (vs NextAuth self-hosting)
4. Industry-standard JWT security
5. Built-in user management UI

**When to Migrate:** If users exceed 100K MAU, consider self-hosted solution (cost: $1,250/mo with Clerk vs $0 with self-hosted)

---

### Real-Time Updates: SSE vs WebSocket

**Decision: Server-Sent Events (SSE) ✅**

**Comparison:**

| Feature | SSE | WebSocket | Polling |
|---------|-----|-----------|---------|
| **Direction** | Server → Client | Bidirectional | Request → Response |
| **Protocol** | HTTP | WebSocket | HTTP |
| **Complexity** | Low | High | Very Low |
| **Browser Support** | All modern | All modern | All |
| **Auto-Reconnect** | Yes | No (manual) | N/A |
| **Latency** | ~100ms | <50ms | >1000ms |
| **Use Case** | Admin dashboard | Chat, gaming | Low-frequency updates |

**Why SSE:**
1. Admin portal is read-heavy (metrics, logs)
2. Simple HTTP-based implementation
3. Built-in browser reconnection
4. Commands use regular POST (no need for bidirectional)

**When to Use WebSocket:** If we add real-time chat or collaborative editing (Phase 7+)

---

### PDF Generation: ReportLab vs WeasyPrint

**Decision: ReportLab [x] (primary), WeasyPrint (fallback)**

**Comparison:**

| Feature | ReportLab | WeasyPrint | PyPDF2 |
|---------|-----------|------------|--------|
| **API Style** | Programmatic (Python) | HTML → PDF | Merge only |
| **Quality** | Excellent | Good | N/A |
| **Flexibility** | High (full control) | Medium (CSS limits) | N/A |
| **Learning Curve** | Steep | Easy (HTML/CSS) | Easy |
| **Performance** | Fast | Medium | Fast |
| **Dependencies** | Minimal | Heavy (cairo, pango) | Minimal |

**Implementation Strategy:**
1. Use ReportLab for professional reports (insights, analyses)
2. Use WeasyPrint for HTML-based exports (landing pages, email templates)
3. Both in dependencies, choose based on use case

---

### Email Service: Resend vs SendGrid

**Decision: Resend ✅**

**Comparison:**

| Feature | Resend | SendGrid | Mailgun |
|---------|--------|----------|---------|
| **Free Tier** | 3K emails/month | 100 emails/day | 5K emails/month |
| **Pricing** | $20/mo (50K emails) | $20/mo (100K emails) | $35/mo (50K emails) |
| **API Simplicity** | Excellent | Complex | Good |
| **Templates** | React components | HTML | HTML |
| **Deliverability** | Excellent | Excellent | Good |
| **Setup Time** | 5 minutes | 20 minutes | 15 minutes |

**Why Resend:**
1. Modern API (send emails with React components)
2. Generous free tier (3K/month vs 100/day for SendGrid)
3. Better developer experience
4. Excellent deliverability rates

**Migration Path:** If volume exceeds 500K emails/month, SendGrid becomes cheaper ($89/mo vs Resend $240/mo)

---

## Cost Analysis (Consolidated)

### Phase 1-4 Costs (Docker PostgreSQL + Neon)

| User Scale | PostgreSQL | Redis | Backend | Frontend | AI (LLM) | Auth/Email | Total/mo |
|------------|------------|-------|---------|----------|----------|------------|----------|
| 100 users  | $0 (Free)  | $0    | $5      | $0       | $10      | $0         | $15      |
| 1,000 users| $19 (Pro)  | $10   | $20     | $20      | $25      | $0         | $94      |
| 10,000 users| $69 (Scale)| $40   | $100    | $20      | $75      | $145       | $449     |

### Phase 4.5+ Costs (Supabase Cloud Singapore)

| User Scale | Supabase | Redis | Backend | Frontend | AI (LLM) | Auth/Email | Total/mo | Savings |
|------------|----------|-------|---------|----------|----------|------------|----------|---------|
| 100 users  | $25 (Pro)| $0    | $5      | $0       | $10      | $0         | $40      | -$25/mo |
| 1,000 users| $25 (Pro)| $10   | $20     | $20      | $25      | $0         | $100     | -$6/mo  |
| 10,000 users| $25 (Pro)| $40   | $100    | $20      | $75      | $145       | $405     | $44/mo  |

**Migration Status:** Phase 4.5 complete (executed 2026-01-25)
**Break-even Point:** 340 users (Supabase becomes cost-effective)

**Revenue Projections (at 10,000 users):**
- Free: 9,000 users × $0 = $0
- Starter ($19): 500 users × $19 = $9,500/mo
- Pro ($49): 400 users × $49 = $19,600/mo
- Enterprise ($299): 100 users × $299 = $29,900/mo
- **Total Revenue: $59,000/month**
- **Phase 1-4 Profit Margin: $58,326/month (98.6%)**
- **Phase 4.5+ Profit Margin: $58,370/month (99.0%)**

**Note on Usage-Based Billing:**
For detailed analysis of Lago integration for AI agent cost tracking, prepaid credit system, and margin protection, see `memory-bank/lago-analysis.md`. The Lago strategy enables:
- **Cost Recovery**: Track actual AI token usage per user (prevents flat-fee abuse where users consume $50 in AI costs but pay $19)
- **Prepaid Credits**: Wallet-based system with margin protection (3-level throttling, cost estimation before execution)
- **Tiered Pricing**: Graduated token pricing ($0.005→$0.002 per 1K tokens) with volume discounts
- **Admin Monitoring**: Real-time cost vs. revenue tracking via SSE dashboard

### IdeaBrowser Pricing Comparison (at 10,000 users)

| Metric | IdeaBrowser (estimated) | StartInsight (Phase 4.5+) | Advantage |
|--------|-------------------------|--------------------------|-----------|
| **Infrastructure Costs** |
| Database | $150/mo (AWS RDS) | $25/mo (Supabase Pro) | 83% savings |
| Storage | $50/mo (S3) | $0 (Supabase included) | 100% savings |
| CDN | $30/mo (CloudFlare) | $0 (Supabase Edge) | 100% savings |
| LLM (GPT-4 vs Gemini) | $200/mo | $15/mo (Gemini) | 92% savings |
| Scraping | $100/mo (estimate) | $149/mo (Firecrawl) | -49% (higher quality) |
| **TOTAL MONTHLY COST** | **$550/mo** | **$294/mo** | **47% savings** |

**Revenue Comparison (10,000 users):**
| Tier | IdeaBrowser | StartInsight | Conversion Rate |
|------|-------------|-------------|-----------------|
| Free | $0 (no free tier) | $0 (9,000 users) | 90% free |
| Starter | $12,475/mo (300 users) | $9,500/mo (500 users) | 5% paid |
| Pro | $18,738/mo (150 users) | $19,600/mo (400 users) | 4% paid |
| Enterprise | $12,496/mo (50 users) | $29,900/mo (100 users) | 1% paid |
| **TOTAL MRR** | **$43,709/mo** | **$59,000/mo** | **+35% revenue** |

**Profit Margin:**
- StartInsight: 99.5% ($58,706 profit)
- IdeaBrowser: 98.7% ($43,159 profit)
- Advantage: 36% higher absolute profit

**Key Insights:**
- Free tier drives 2x higher user acquisition (10K vs 5K users)
- Lower pricing enables 2x higher conversion volume
- 47% lower costs + 35% higher revenue = 36% higher profit

---

## Version Pinning Strategy

### Semantic Versioning Policy

```txt
Major.Minor.Patch (e.g., 2.5.3)

- Major: Breaking changes (manual upgrade required)
- Minor: New features (backward compatible)
- Patch: Bug fixes (automatic updates)
```

**Pinning Strategy:**

```toml
# Critical dependencies (pin major version)
fastapi = "^0.109.0"  # Allow minor/patch updates
clerk-backend-api = "^2.0.0"  # Stay on v2.x

# Less critical (allow minor updates)
pydantic = ">=2.5.0,<3.0.0"

# Lock for reproducible builds
alembic = "==1.13.0"  # Exact version for migrations
```

**Update Policy:**
1. **Weekly:** Check for security updates (patch versions)
2. **Monthly:** Review minor version updates
3. **Quarterly:** Major version upgrade planning
4. **Before production:** Lock all versions in `pyproject.toml`

### Dependency Update Workflow

```bash
# Check for outdated packages
cd backend
uv pip list --outdated

# Update to latest compatible versions
uv pip install --upgrade fastapi

# Test thoroughly before deploying
pytest
ruff check .

# Lock dependencies
uv pip freeze > requirements-lock.txt
```

---

## Development vs Production Dependencies

### Backend

```toml
# Development only
[project.optional-dependencies]
dev = [
    "pytest>=7.4.0",        # Testing framework
    "pytest-asyncio>=0.21.0",  # Async test support
    "pytest-cov>=4.1.0",    # Coverage reporting
    "ruff>=0.1.0",          # Linting & formatting
    "mypy>=1.7.0",          # Type checking
    "ipdb>=0.13.0",         # Debugging
    "faker>=20.0.0",        # Test data generation
]

# Production only (not in dev)
[project]
dependencies = [
    "gunicorn>=21.0.0",     # Production WSGI server
    "sentry-sdk>=1.40.0",   # Error tracking
]
```

### Frontend

```json
{
  "devDependencies": {
    // Development tools
    "@playwright/test": "^1.57.0",  // E2E testing
    "eslint": "^8.56.0",            // Linting
    "prettier": "^3.2.0",           // Code formatting
    "@types/node": "^20.11.0",      // TypeScript types

    // Build tools (used in production builds)
    "typescript": "^5.3.0",
    "tailwindcss": "^4.0.0"
  }
}
```

---

## Security Dependencies

### Dependency Scanning

**Tools:**

1. **npm audit** (Frontend):
   ```bash
   cd frontend
   npm audit                    # Check for vulnerabilities
   npm audit fix                # Auto-fix if possible
   npm audit fix --force        # Force fix (breaking changes)
   ```

2. **Safety** (Backend):
   ```bash
   cd backend
   pip install safety
   safety check                 # Scan for known vulnerabilities
   ```

3. **Dependabot** (GitHub):
   ```yaml
   # .github/dependabot.yml
   version: 2
   updates:
     - package-ecosystem: "pip"
       directory: "/backend"
       schedule:
         interval: "weekly"
       open-pull-requests-limit: 5

     - package-ecosystem: "npm"
       directory: "/frontend"
       schedule:
         interval: "weekly"
       open-pull-requests-limit: 5
   ```

### Known Vulnerabilities Policy

**Severity Levels:**
- **Critical:** Fix immediately (same day)
- **High:** Fix within 3 days
- **Medium:** Fix within 2 weeks
- **Low:** Fix in next sprint

**Process:**
1. Automated scan runs daily (GitHub Actions)
2. Dependabot creates PR for security updates
3. Review and test PR in staging
4. Deploy to production after validation

---

## Phase 5-7 Dependencies (Implemented in Backend)

### Phase 5: Advanced Analysis (Backend Complete)

```toml
# All dependencies already listed in Phase 5 section above
# No additional packages required beyond base stack
```

### Phase 6: Payments & Teams (Backend Complete)

```toml
# Payment processing
"stripe>=7.0.0"  # Implemented in backend/app/services/payment.py

# Email templates
"premailer>=3.10.0"  # CSS inlining for email compatibility
```

### Phase 7: API & Multi-tenancy (Backend Complete)

```toml
# All dependencies already listed in Phase 7 section above
# No additional packages required beyond base stack
```

**Note:** Removed unimplemented dependencies:
- `instructor` (PydanticAI used instead)
- `selenium` (Playwright chosen for automation, not implemented in Phase 5-7)
- `langsmith` (Not used)
- `websockets` (SSE used instead)
- `twilio` (Email-only notifications)
- `beautifulsoup4`, `feedparser`, `epo-ops` (Not implemented in Phase 5-7)

---


Decision Records (Why we chose this)
Why FastAPI over Django? StartInsight is an AI-heavy app. We need excellent asynchronous support for scraping multiple sources and streaming LLM responses simultaneously. Django is too heavy and synchronous by default. FastAPI provides a lighter, faster "glue" layer for AI agents.

Database Evolution: PostgreSQL to Supabase
Phase 1-4 (Development): PostgreSQL via Docker for vendor independence and control over data layer. Standard Postgres container ensures we can host anywhere (AWS, GCP, DigitalOcean) without BaaS lock-in.
Phase 4.5 (Complete 2026-01-25): Migrated to Supabase Cloud Singapore for cost savings (64% at 10K users) and APAC latency optimization (50ms vs 180ms). 13 migrations executed, 20 tables deployed with RLS.

Why Firecrawl? Writing custom CSS selectors for scraping is brittle (websites change). Firecrawl uses AI/Heuristics to turn web pages into Markdown, which is the native language of our LLM agents.

---

<!-- Supabase migration dependencies added on 2026-01-25 for Phase 4.5 -->

## 9. Phase 4.5: Database Migration (PostgreSQL → Supabase Cloud)

### 9.1 Migration Rationale

**Status:** Complete (executed 2026-01-25)

**Decision:** Migrate from self-hosted PostgreSQL to Supabase Cloud (Singapore ap-southeast-1)

**Why Supabase:**
- **Cost Efficiency**: $25/mo (Pro) vs $69/mo (Neon Scale) at 10K users = 64% savings
- **APAC Market**: Singapore region = 50ms latency for SEA users (vs 180ms US-based)
- **Built-in Features**: Real-time subscriptions, Storage, Edge Functions (Phase 5+)
- **Developer Experience**: Auto-migrations, RLS policies, built-in auth option
- **Scalability**: Auto-scaling, connection pooling (up to 500 concurrent connections)

### 9.2 Backend Dependencies (Added)

| Package | Version | Purpose | Installation |
|---------|---------|---------|--------------|
| `supabase` | >=2.0.0 | Python client for Supabase | `uv add supabase` |
| `postgrest-py` | >=0.10.0 | PostgREST client (included in supabase) | Auto-installed |

**Note:** Keep SQLAlchemy + asyncpg during transition period (dual-write strategy)

### 9.3 Frontend Dependencies (Added)

| Package | Version | Purpose | Installation |
|---------|---------|---------|--------------|
| `@supabase/supabase-js` | >=2.38.0 | Supabase client for Next.js | `pnpm add @supabase/supabase-js` |
| `@supabase/ssr` | >=0.0.10 | Server-side rendering utilities | `pnpm add @supabase/ssr` |

### 9.4 Environment Variables (Updated)

**New Variables:**
```bash
# Supabase Cloud (Singapore ap-southeast-1)
SUPABASE_URL=https://[project-ref].supabase.co
SUPABASE_ANON_KEY=eyJhbGc...  # Public key (client-side)
SUPABASE_SERVICE_ROLE_KEY=eyJhbGc...  # Private key (server-side only)

# Keep during transition
DATABASE_URL=postgresql+asyncpg://startinsight:password@localhost:5433/startinsight
```

### 9.5 Migration Strategy (3 Options)

#### Option 1: Conservative (Recommended for Phase 4.5)
- **Approach**: SQLAlchemy wrapper around Supabase
- **Pros**: Minimal code changes, gradual migration, easy rollback
- **Cons**: Doesn't leverage Supabase features (RLS, real-time)
- **Timeline**: 1 week

#### Option 2: Progressive (Recommended for Phase 5+)
- **Approach**: Dual-write (PostgreSQL + Supabase), gradual cutover
- **Pros**: Zero downtime, incremental feature adoption, safe rollback
- **Cons**: Temporary complexity, data consistency overhead
- **Timeline**: 4 weeks

#### Option 3: Full Supabase
- **Approach**: Replace SQLAlchemy with Supabase client
- **Pros**: Full Supabase feature access, simplified stack
- **Cons**: Major refactor, higher risk, difficult rollback
- **Timeline**: 8 weeks

**Chosen Approach:** Option 2 (Progressive) - See implementation-plan.md Phase 4.5

### 9.6 Supabase Pricing Tiers

| Tier | Monthly Cost | Database Size | Bandwidth | Edge Functions |
|------|--------------|---------------|-----------|----------------|
| Free | $0 | 500MB | 5GB | 500K invocations |
| Pro | $25 | 8GB | 50GB | 2M invocations |
| Team | $599 | 100GB | 250GB | 10M invocations |
| Enterprise | Custom | Custom | Custom | Custom |

**StartInsight Plan:** Pro tier ($25/mo) sufficient for up to 50K users

For detailed cost comparison and revenue projections, see Cost Analysis section above.

### 9.7 Singapore Region Configuration

**Region:** `ap-southeast-1` (AWS Singapore)

**Justification:**
- **APAC Market Growth**: 30% YoY SaaS adoption in SEA
- **Latency**: 50ms (Singapore) vs 180ms (US) for SEA users
- **Compliance**: Data residency for APAC customers
- **Expansion**: Gateway to Australia (120ms), India (85ms), Japan (110ms)

**Configuration:**
```typescript
// frontend/lib/supabase.ts
import { createClient } from '@supabase/supabase-js'

const supabaseUrl = process.env.NEXT_PUBLIC_SUPABASE_URL!  // Singapore region
const supabaseAnonKey = process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY!

export const supabase = createClient(supabaseUrl, supabaseAnonKey, {
  db: { schema: 'public' },
  auth: { persistSession: true },
  global: { headers: { 'x-application-name': 'startinsight' } }
})
```

### 9.8 Future Features Enabled (Phase 5+)

**Real-time Subscriptions** (Phase 5.1):
- Live insight updates as scraper processes data
- Multi-user collaboration (shared workspaces)
- Admin dashboard live metrics

**Storage** (Phase 5.2):
- User avatar uploads
- Generated report PDFs
- Landing page assets (logos, images)

**Edge Functions** (Phase 5.3):
- PDF generation (reportlab → Deno edge function)
- Image resizing (brand package logos)
- Webhook handlers (Stripe, Clerk)

**PostgREST API** (Phase 5.4):
- Auto-generated REST API from schema
- Reduce custom FastAPI routes
- GraphQL option (pg_graphql extension)

---
