# StartInsight

> **AI-Powered Business Intelligence Engine for Startup Idea Discovery**

StartInsight is a daily, automated intelligence platform that discovers, validates, and presents data-driven startup ideas by analyzing real-time market signals from social discussions, search trends, and product launches.

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.109+-00C7B7.svg)](https://fastapi.tiangolo.com)
[![Next.js 16+](https://img.shields.io/badge/Next.js-16+-black.svg)](https://nextjs.org)
[![CI/CD](https://github.com/Ascentia-Sandbox/StartInsight/actions/workflows/ci-cd.yml/badge.svg)](https://github.com/Ascentia-Sandbox/StartInsight/actions/workflows/ci-cd.yml)

---

## 🌐 Live Production

| Environment | URL | Status |
|-------------|-----|--------|
| **Frontend** | [startinsight.co](https://startinsight.co) | ✅ Live (Vercel) |
| **Backend API** | [api.startinsight.co](https://api.startinsight.co) | ✅ Live (Railway) |
| **Staging Frontend** | [start-insight-staging-ascentias-projects.vercel.app](https://start-insight-staging-ascentias-projects.vercel.app) | ✅ Live |
| **Staging Backend** | [backend-staging-fbd7.up.railway.app](https://backend-staging-fbd7.up.railway.app) | ✅ Live |
| **API Docs** | `/docs` (Swagger) | [Available](https://api.startinsight.co/docs) |

---

## 🎯 What is StartInsight?

Unlike traditional brainstorming tools, StartInsight relies on **real-time market signals** to identify genuine market gaps and consumer pain points. The system operates on an automated **"Collect → Analyze → Present"** loop, functioning as an analyst that never sleeps.

### Core Philosophy

- **Signal over Noise**: Surface problems real people are complaining about or searching for
- **Data-Driven Intuition**: Every insight backed by source data (Reddit threads, search trends)
- **Automated Intelligence**: AI agents handle market research, leaving users with high-level decision-making

---

## ✨ Features

### Current (Phase 1-10, 12-14, A-L, Q1-Q9, Security, Sentry — Production Live)

**Data Intelligence**
- **Automated Data Collection**: 6 scrapers (Reddit, Product Hunt, Google Trends, Twitter/X, Hacker News, Firecrawl) — 150+ signals/day target
- **AI-Powered Analysis**: Gemini 2.0 Flash with 8-dimension scoring (97% cost reduction vs Claude)
- **8 AI Agents**: Enhanced analyzer, 40-step research agent, competitive intel, market intel, content generator, chat strategist, quality reviewer, weekly digest
- **Evidence Visualizations**: Radar charts, KPI cards, confidence badges, trend verification, engagement metrics
- **Content Quality Gates**: Post-LLM validation (300+ word minimum), SHA-256 deduplication, auto-approval at 0.85

**Design System (Phase G) — "Data Intelligence" Aesthetic**
- **Typography**: Instrument Serif (editorial headings), Satoshi (body), JetBrains Mono (data/scores)
- **Color System**: Deep teal primary, warm amber accent — distinctive identity, not a generic SaaS clone
- **Motion**: Framer Motion staggered reveals, counter animations, skeleton morphing
- **Textures**: Dot grid backgrounds, gradient mesh heroes, card noise overlays

**Content Pipeline (Phase H)**
- **6 Active Scrapers**: Reddit (50/run), Product Hunt (30/run), Google Trends (6 regions), Twitter/X, Hacker News (50+ score filter), Firecrawl
- **Real Trend Data**: No more synthetic charts — real Google Trends data with "Search Interest" badge fallback
- **Multi-Region**: Google Trends scraped across US, UK, Germany, Japan, Sydney, Australia

**Admin Portal Excellence (Phase I)**
- **Dashboard Charts**: 4 Recharts visualizations (content volume, agent activity, user growth, quality trends)
- **Cmd+K Command Palette**: Global keyboard shortcut, 16 commands, arrow key navigation, category groups
- **Data Pagination**: Reusable pagination with URL state (page/per_page), integrated in 3+ admin pages
- **Export**: CSV/JSON export endpoints with frontend download buttons
- **Bulk Operations**: Row selection, bulk delete with confirmation, bulk export

**Public Editorial Design (Phase J)**
- **Story-Driven Homepage**: Hero gradient with serif titles, animated counters, latest insights grid, 8-dimension deep-dive
- **InsightCard Redesign**: Teal score bar, platform-colored source badges, market size circles, relative dates
- **Magazine Detail Pages**: Editorial hero, score dashboard, problem/solution columns, evidence section, sticky action bar
- **Market Insights**: AI-generated badges, reading time estimates, enhanced author bios

**Evidence & Social Proof (Phase K)**
- **Confidence Badges**: High/Medium/Needs Verification on every insight card
- **Public Stats API**: Real-time counters (total insights, signals, avg quality) on homepage
- **Engagement Metrics**: View/save/share counts on insight detail pages
- **Evidence Scoring**: Evidence Score badges, Google Trends verification, data point counts

**Competitive Differentiators (Phase L)**
- **5 Chat Strategist Modes**: General, Pressure Test, GTM Planning, Pricing Strategy, Competitive Analysis
- **Competitive Landscape Map**: Recharts ScatterChart with Market Maturity × Innovation Score quadrants
- **Enhanced Validator**: Hero gradient, radar chart results, free tier badge
- **Weekly Email Digest**: Top 10 insights every Monday, scheduled via Arq worker

**Enterprise Features (Phase 8-10)**
- **Superadmin Control Center**: Content quality management, pipeline monitoring, AI agent prompt control, cost tracking
- **User Engagement**: Preferences & email digests, AI idea chat, community voting/comments/polls, gamification
- **Integration Ecosystem**: External integrations, webhooks with retry logic, OAuth connections

**User Features**
- **Visual Dashboard**: Next.js interface with insights, trend graphs, filters, dark mode
- **Workspace Management**: Save insights, rate quality, claim for development
- **Team Collaboration**: RBAC with owner/admin/member roles, shared insights
- **Custom Research**: Submit research requests with tier-based approval

**Reliability & Rate-Limit Handling**
- **Gemini 429 Retry**: `quality_reviewer.py` uses `tenacity` with 4-attempt exponential backoff (5s → 10s → 20s → 40s) + 2s inter-call sleep — eliminates RESOURCE_EXHAUSTED cascades in 10/20-insight audit batches
- **All AI Agents Protected**: `enhanced_analyzer.py` and `research_agent.py` also use tenacity retry — consistent pattern across all LLM-calling agents

**Security & Observability**
- **Security Headers**: HSTS (`max-age=31536000`), CSP, X-Frame-Options, X-Content-Type-Options via middleware
- **JWT Authentication**: ES256 (ECDSA P-256) via Supabase JWKS endpoint — no shared secret needed
- **XSS Prevention**: `bleach` sanitization on all user inputs, `markupsafe.escape()` for display
- **Password Recovery**: `/auth/update-password` page with Supabase recovery token flow
- **Sentry Monitoring**: Errors + performance traces + structured logs + AI spans on production + staging
- **AI Agent Observability**: Manual `gen_ai.request` spans (model, token usage, latency) in Sentry Traces
- **Session Replay**: Sentry Session Replay (maskAllText, blockAllMedia) on frontend errors

**Developer Features**
- **Public API**: 232+ REST endpoints with Swagger/OpenAPI documentation
- **API Key Management**: Scoped keys with usage tracking, rate limiting
- **Export Tools**: CSV/JSON exports with brand customization
- **Row-Level Security**: Supabase RLS policies on all 69 tables
- **Comprehensive Testing**: 291 backend tests passing, 47 E2E tests (8 suites, 5 browsers)
- **CI/CD Pipeline**: GitHub Actions — Security Scan → Tests → Migrate → Build → Deploy

---

## 🏗️ Architecture

```mermaid
graph LR
    A[Reddit/PH/Trends/HN/Twitter] -->|6 Scrapers| B[Arq Worker]
    B -->|Raw Signals| C[(Supabase PostgreSQL)]
    C -->|Unprocessed| D[Gemini 2.0 Flash]
    D -->|8-Dim Insights| C
    C -->|API| E[FastAPI]
    E -->|JSON/SSE| F[Next.js Dashboard]
    G[Railway Redis] -.->|Queue| B
```

**Cloud Infrastructure:**
- **Database**: Supabase Pro PostgreSQL (Sydney, ap-southeast-2), 200 connection pool limit
- **Cache/Queue**: Railway Redis (native service, `redis.railway.internal:6379`)
- **Backend**: Railway (port 8080, Docker, `railway.toml`)
- **Frontend**: Vercel (Next.js App Router)

### The Three Core Loops

1. **Loop 1: Data Collection** (Every 6 hours)
   - Scrapes content using Firecrawl (markdown format)
   - Stores raw signals in Supabase PostgreSQL with metadata

2. **Loop 2: Analysis** (After each collection)
   - Gemini 2.0 Flash processes unprocessed signals
   - Validates output with Pydantic schemas
   - Scores relevance and market potential (8-dimension scoring)

3. **Loop 3: Presentation** (On-demand)
   - FastAPI serves ranked insights via REST
   - Next.js dashboard displays top insights with visualizations

---

## 🛠️ Tech Stack

### Backend
- **Framework**: FastAPI (async-first)
- **Language**: Python 3.11+
- **Database**: Supabase Pro PostgreSQL (ap-southeast-2, Sydney)
- **ORM**: SQLAlchemy 2.0 (async)
- **Queue**: Redis + Arq (async task queue)
- **AI**: PydanticAI + Gemini 2.0 Flash ($0.10/M tokens)
- **Auth**: Supabase Auth (OAuth + email/password)

### Frontend
- **Framework**: Next.js 16.1.3 (App Router, React 19.2.3)
- **Language**: TypeScript
- **Styling**: Tailwind CSS 4.0, teal/amber "Data Intelligence" design system
- **Typography**: Instrument Serif (headings), Satoshi (body), JetBrains Mono (data)
- **Components**: shadcn/ui (25+ components), Cmd+K command palette
- **Charts**: Recharts (radar, scatter, line, area, bar)
- **Animation**: Framer Motion (stagger reveals, counters, skeleton morphing)
- **State**: TanStack Query (React Query)
- **Markdown**: react-markdown + remark-gfm + rehype-sanitize

### Data Pipeline
- **Scraping**: Firecrawl (web → markdown), Tweepy (Twitter/X)
- **Reddit**: PRAW (Python Reddit API Wrapper)
- **Trends**: pytrends (Google Trends API)
- **RSS**: feedparser (custom feeds)

### Services
- **Payments**: Stripe (4-tier subscriptions, webhooks) — live mode, 3 products, 6 prices (monthly + yearly), webhook configured
- **Email**: Resend (6 email templates)
- **Rate Limiting**: SlowAPI + Redis (tier-based quotas)
- **Error Tracking**: Sentry (`sentry-sdk[fastapi]>=2.0.0`, `@sentry/nextjs@^10.38.0`) — errors + traces + logs

### DevOps & CI/CD
- **CI/CD**: GitHub Actions (`.github/workflows/ci-cd.yml`) — `main` → production, `develop` → staging
- **Backend Hosting**: Railway (Dockerfile + `railway.toml`, port 8080)
- **Frontend Hosting**: Vercel (App Router, Next.js 16+)
- **IaC**: Railway MCP + Vercel MCP for environment variable management

### DevOps
- **Database**: Supabase Pro (PostgreSQL 15+, Row-Level Security, DB_SSL=True)
- **Cache**: Redis 7
- **Package Managers**: `uv` (Python), `npm` (Node.js)
- **Migrations**: Alembic + Supabase migrations (25+ total)
- **Linting**: Ruff (Python), ESLint + Prettier (TypeScript)
- **Testing**: pytest (backend), Playwright (E2E, 5 browsers)

---

## 🚀 Quick Start

> **Cloud-First Setup**: StartInsight uses Supabase Cloud PostgreSQL (production) and Railway Redis (production). Local dev uses a local Redis instance.

For detailed setup instructions, see **[SETUP.md](SETUP.md)** - a comprehensive guide covering:
- Prerequisites (Supabase accounts)
- Backend and frontend configuration
- Database initialization
- Troubleshooting common issues
- Production deployment

### Prerequisites

- **Python 3.12+**
- **Node.js 18+**
- **uv** (Python package manager): `curl -LsSf https://astral.sh/uv/install.sh | sh`
- **Supabase Account**: [supabase.com](https://supabase.com) (PostgreSQL database + auth)
- **Redis**: Local Redis for dev; Railway Redis auto-provisioned in production

### 1. Clone the Repository

```bash
git clone https://github.com/Ascentia-Sandbox/StartInsight.git
cd StartInsight
```

### 2. Create Supabase Project

1. Go to [supabase.com](https://supabase.com) and create a new project
2. Choose **Asia Pacific (Sydney)** region
3. Copy your connection string from **Project Settings > Database > Connection string** (Connection Pooling mode)
4. Copy your API keys from **Project Settings > API**

### 3. Redis Setup

**Production**: Handled automatically — Railway Redis service is provisioned in the project (`redis.railway.internal:6379`). No external account needed.

**Local development**: Install Redis locally (`brew install redis` / `apt install redis`) and set `REDIS_URL=redis://localhost:6379`.

### 4. Configure Backend

```bash
cd backend
cp .env.example .env
```

Edit `backend/.env` with your cloud credentials:
```bash
# Database (Supabase Cloud)
DATABASE_URL=postgresql+asyncpg://postgres.[PROJECT_REF]:[PASSWORD]@aws-0-ap-southeast-2.pooler.supabase.com:5432/postgres?pgbouncer=true

# Supabase Auth
SUPABASE_URL=https://[PROJECT_REF].supabase.co
SUPABASE_ANON_KEY=your_supabase_anon_key
SUPABASE_SERVICE_ROLE_KEY=your_supabase_service_role_key
JWT_SECRET=your_jwt_secret_from_supabase

# Redis (local dev; production uses Railway Redis automatically)
REDIS_URL=redis://localhost:6379

# AI (Gemini 2.0 Flash)
GOOGLE_API_KEY=your_google_api_key

# See .env.example for all required keys
```

### 5. Configure Frontend

```bash
cd ../frontend
cp .env.example .env.local
```

Edit `frontend/.env.local`:
```bash
NEXT_PUBLIC_API_URL=https://api.startinsight.co  # production; use http://localhost:8000 for local dev
NEXT_PUBLIC_SUPABASE_URL=https://[PROJECT_REF].supabase.co
NEXT_PUBLIC_SUPABASE_ANON_KEY=your_supabase_anon_key
```

### 6. Initialize Database

```bash
cd backend

# Install dependencies
uv sync

# Run migrations
alembic upgrade head
```

### 7. Start Backend

```bash
# From backend/ directory
uvicorn app.main:app --reload
```

Backend runs at: **http://localhost:8000**
- API docs: http://localhost:8000/docs
- Health check: http://localhost:8000/health

### 8. Start Frontend

```bash
# From frontend/ directory
npm install
npm run dev
```

Frontend runs at: **http://localhost:3000**

---

## 📖 Full Setup Guide

For troubleshooting, production deployment, and advanced configuration, see:

**[SETUP.md](SETUP.md)** - Comprehensive cloud-first setup guide

---

## 🚀 Deployment

### Infrastructure Overview

| Service | Purpose | Tier | Cost |
|---------|---------|------|------|
| **Supabase** | PostgreSQL + Auth | Pro | $25/mo |
| **Gemini 2.0 Flash** | AI analysis | Pay-as-you-go | ~$5/mo |
| **Railway** | Backend + Redis | Free (500h/mo + free Redis) | $0 |
| **Vercel** | Frontend hosting | Hobby | $0 |
| **Sentry** | Error tracking | Free (5K events) | $0 |
| **Resend** | Transactional email | Free (3K emails) | $0 |
| | | **Total** | **~$30/mo** |

### Environment Templates

| Environment | Backend | Frontend |
|-------------|---------|----------|
| **Staging** | [`backend/.env.staging.example`](backend/.env.staging.example) | [`frontend/.env.staging.example`](frontend/.env.staging.example) |
| **Production** | [`backend/.env.production.example`](backend/.env.production.example) | [`frontend/.env.production.example`](frontend/.env.production.example) |
| **Development** | [`backend/.env.example`](backend/.env.example) | [`frontend/.env.example`](frontend/.env.example) |

### CI/CD Pipeline (Automated)

Deployment is fully automated via GitHub Actions:

```
Push to main  → Security Scan → Backend Tests → Frontend Tests
             → Migrate Production DB → Build Docker Image → Deploy to Production

Push to develop → Security Scan → Backend Tests → Frontend Tests
               → Migrate Staging DB → Deploy to Staging
```

**Deployed URLs:**
- Production Backend: `https://api.startinsight.co`
- Production Frontend: `https://startinsight.co`
- Staging Backend: `https://backend-staging-fbd7.up.railway.app`

### Manual Deployment (First Time)

```bash
# 1. Create accounts: Railway, Vercel, Sentry, Resend, Google AI Studio
# 2. Run database migrations against Supabase
cd backend && DATABASE_URL="postgresql+asyncpg://..." alembic upgrade head

# 3. Deploy backend to Railway (link GitHub repo, set root dir to repo root)
#    Add all vars from backend/.env.production.example in Railway dashboard
#    ⚠️ Set target port = 8080 in Railway domain settings

# 4. Deploy frontend to Vercel (import repo, set root dir to frontend/)
#    Add all vars from frontend/.env.production.example in Vercel dashboard

# 5. Update CORS: set Railway CORS_ORIGINS to match Vercel URL
# 6. Verify: curl https://[railway-url]/health → {"status":"healthy"}
```

### Gotchas

- **Railway target port** — must be `8080` (Railway injects `PORT=8080`, not 8000)
- **NEXT_PUBLIC_* vars are build-time** — changing them in Vercel requires a redeploy
- **Railway Redis URL** — uses `redis://` (plain TCP on private network), no TLS needed
- **Sentry env vars** — set via Railway MCP (backend) and GitHub Actions workflow (Vercel)
- **Alembic migration c008** — `purge_seed_data` is irreversible, run on staging first
- **CORS whitelist** — production origins must exactly match `CORS_ALLOWED_PRODUCTION_ORIGINS`
- **Railway 512MB RAM** — Playwright+Chromium takes ~400MB. If OOM, set `USE_CRAWL4AI=false`

---

## 🌏 Cloud-First Architecture

StartInsight uses **cloud services by default** to ensure consistency between development and production:

### Supabase Pro PostgreSQL (Sydney)

- **Tier:** Supabase Pro ($25/mo) - sole database, no local PostgreSQL required
- **Region:** ap-southeast-2 (Sydney) - Optimized for APAC market
- **Latency:** <50ms for Southeast Asia (vs 180ms US-based)
- **Cost:** $25/mo (Supabase Pro) vs $69/mo (Neon) = 64% savings
- **Features:** PostgreSQL 15+, Row-Level Security, connection pooling (200 limit), real-time subscriptions, SSL required

### Railway Redis (Production)

- **Location:** Same Railway project as backend (private network, zero latency)
- **Hostname:** `redis.railway.internal:6379` (internal only, not publicly accessible)
- **Cost:** Free (Railway free tier includes Redis)
- **Use Cases:** Arq task queue, rate limiting (tier-based quotas)

### Why Cloud-First?

1. **No Infrastructure Setup**: Skip Docker, PostgreSQL installation (only local Redis needed for dev)
2. **Production Parity**: Development environment matches production closely
3. **Managed Backups**: Automatic backups and point-in-time recovery (Supabase Pro)
4. **Global Accessibility**: Access your database from anywhere
5. **RLS Testing**: Test Row-Level Security policies in real Supabase environment

---

## 📁 Project Structure

```
StartInsight/
├── backend/                    # FastAPI application
│   ├── app/
│   │   ├── core/              # Config, errors, dependencies
│   │   ├── db/                # Database session, base classes
│   │   ├── models/            # SQLAlchemy models (69 tables)
│   │   ├── schemas/           # Pydantic schemas
│   │   ├── api/               # API routes (230 endpoints)
│   │   │   ├── routes/        # Insight, user, admin, public content
│   │   │   ├── tools.py       # Tools directory API (6 endpoints)
│   │   │   ├── success_stories.py # Success stories API (6 endpoints)
│   │   │   ├── trends.py      # Trends API (5 endpoints)
│   │   │   └── market_insights.py # Blog API (6 endpoints)
│   │   ├── agents/            # 8 AI agents (enhanced_analyzer, research, competitive_intel, market_intel, content_generator, chat_agent, quality_reviewer, market_insight_publisher)
│   │   ├── scrapers/          # Data collection modules (4 sources)
│   │   ├── scripts/           # Seed scripts (84 content items)
│   │   └── main.py            # FastAPI entry point
│   ├── alembic/               # Database migrations (25+ migrations)
│   ├── tests/                 # Pytest test suite
│   ├── pyproject.toml         # Python dependencies (uv)
│   └── README.md              # Backend-specific docs
│
├── frontend/                   # Next.js application (Phase 3-14)
│   ├── app/                   # Next.js 16+ App Router
│   │   ├── (routes)           # 34 total routes
│   │   ├── tools/             # Tools directory page
│   │   ├── success-stories/   # Founder case studies
│   │   ├── trends/            # Trending keywords
│   │   ├── market-insights/   # Blog articles
│   │   ├── admin/             # Admin content management
│   │   └── sitemap.ts         # Dynamic sitemap generation
│   ├── components/            # React components
│   │   ├── navigation/        # Mega-menu, mobile drawer
│   │   ├── ui/                # 25 shadcn components
│   │   └── evidence/          # Charts, visualizations
│   ├── lib/                   # Utilities & API client
│   └── package.json           # Node dependencies
│
├── memory-bank/               # Project documentation
│   ├── project-brief.md       # Executive summary
│   ├── active-context.md      # Current phase & tasks
│   ├── implementation-plan.md # 3-phase roadmap
│   ├── architecture.md        # System design
│   ├── tech-stack.md          # Technology decisions
│   ├── progress.md            # Development log
│   └── improvement-plan.md    # Growth roadmap (Tier 1-3)
│
├── research/                  # Competitive intelligence
│   ├── ideabrowser-analysis.md          # Full IdeaBrowser teardown
│   ├── ideabrowser-executive-summary.md # Key findings
│   └── ideabrowser-competitive-analysis.json
│
├── .claude/                   # Claude Code configuration
│   ├── agents/                # Custom Claude agents
│   └── skills/                # Code quality standards
│
├── docker-compose.yml         # Redis setup (database is Supabase Pro)
├── CLAUDE.md                  # Claude Code guidelines
└── README.md                  # This file
```

---

## 🔄 Development Workflow

### Common Commands

```bash
# Backend Development
cd backend && uvicorn app.main:app --reload

# Frontend Development
cd frontend && npm run dev

# Database Migrations
cd backend && alembic upgrade head

# Backend Tests (291 tests, 85% coverage)
cd backend && pytest tests/ -v --cov=app

# Frontend E2E Tests (47 tests, 5 browsers)
cd frontend && npx playwright test

# Lint & Format
cd backend && uv run ruff check . --fix
cd frontend && npm run lint --fix
```

### Database Utilities

```bash
# Create new migration
cd backend && uv run alembic revision --autogenerate -m "description"

# View migration history
cd backend && uv run alembic history

# Rollback migration
cd backend && uv run alembic downgrade -1
```

### Cloud Service Management

```bash
# Verify backend health
curl https://api.startinsight.co/health

# View Supabase logs
# Go to: https://supabase.com/dashboard/project/[PROJECT_REF]/logs/postgres-logs

# View Railway Redis metrics
# Railway dashboard → startInsight project → Redis service

# Reset database (⚠️ use with caution)
cd backend && alembic downgrade base && alembic upgrade head
```

---

## 📚 Documentation

Comprehensive documentation is maintained in the `memory-bank/` directory:

| File | Purpose |
|------|---------|
| **[project-brief.md](memory-bank/project-brief.md)** | Executive summary, business objectives, core philosophy |
| **[active-context.md](memory-bank/active-context.md)** | Current phase, immediate tasks, blockers |
| **[implementation-plan.md](memory-bank/implementation-plan.md)** | Step-by-step 3-phase roadmap |
| **[architecture.md](memory-bank/architecture.md)** | System design, data flows, database schema, API endpoints |
| **[tech-stack.md](memory-bank/tech-stack.md)** | Technology decisions, dependencies, library versions |
| **[progress.md](memory-bank/progress.md)** | Development log, completed tasks |

---

## 🧪 Testing

### Backend Testing (pytest)

**Stats**: 291 tests across 22 files, 85% coverage

```bash
# Run all backend tests
cd backend && pytest tests/ -v

# Run with coverage report
pytest tests/ --cov=app --cov-report=html

# Run specific test file
pytest tests/services/test_payment_service.py -v

# Run specific test category
pytest tests/unit/ -v        # Unit tests only
pytest tests/services/ -v    # Service tests only
```

### Frontend Testing (Playwright)

**Stats**: 47 E2E tests across 8 suites, 5 browser platforms (Chrome, Firefox, Safari, Mobile Chrome, Mobile Safari)

```bash
# Run all E2E tests
cd frontend && npx playwright test

# Run with browser UI
npx playwright test --headed

# Run specific browser
npx playwright test --project=chromium

# Run specific test file
npx playwright test tests/frontend/e2e/auth.spec.ts

# Interactive mode
npx playwright test --ui

# Generate test report
npx playwright show-report
```

---

## 🤝 Contributing

This is a private development project. If you have access:

1. **Read Documentation First**: Check `memory-bank/active-context.md` for current phase
2. **Follow Coding Standards**: See `.claude/skills/` for quality guidelines
3. **Update Progress**: Log changes to `memory-bank/progress.md`
4. **Use Conventional Commits**: `feat:`, `fix:`, `docs:`, `chore:`

### Code Quality Standards

The project enforces 4 core skills via Claude Code:

- **async-alchemy**: Prevents blocking I/O in FastAPI/SQLAlchemy
- **firecrawl-glue**: Enforces Firecrawl SDK over brittle scrapers
- **pydantic-validator**: Ensures structured AI agent outputs
- **vibe-protocol**: Automates documentation synchronization

---

## 🔑 API Keys Required

| Service | Purpose | Get Key |
|---------|---------|---------|
| **Supabase** | Database + Auth (ap-southeast-2) | [supabase.com](https://supabase.com) |
| **Google AI** | Gemini 2.0 Flash (AI analysis) | [aistudio.google.com](https://aistudio.google.com) |
| **Firecrawl** | Web scraping (web → markdown) | [firecrawl.dev](https://firecrawl.dev) |
| **Reddit** | Reddit API (PRAW) | [reddit.com/prefs/apps](https://reddit.com/prefs/apps) |
| **Twitter** | Twitter/X API (Tweepy) | [developer.twitter.com](https://developer.twitter.com) |
| **Stripe** | Payments (subscriptions) | [stripe.com](https://stripe.com) |
| **Resend** | Email (transactional) | [resend.com](https://resend.com) |
| **Sentry** | Error tracking + monitoring | [sentry.io](https://sentry.io) |

Store keys in `backend/.env` and `frontend/.env.local` (never commit `.env` files).

---

## 📊 Current Status

**Status**: ✅ **PRODUCTION LIVE** (2026-02-22) — Custom domain `startinsight.co` live

| Metric | Value |
|--------|-------|
| **Backend** | 232+ API endpoints, 69 database tables, 15+ services |
| **Frontend** | 35+ routes (dashboard, workspace, research, admin, 10 public pages) |
| **Database** | 25+ Alembic migrations (c009 latest), Row-Level Security enabled |
| **AI Agents** | 8 agents (enhanced_analyzer, research, competitive_intel, market_intel, content_generator, chat_agent, quality_reviewer, weekly_digest) |
| **Testing** | 291 backend tests (22 files, 85% coverage), 47 E2E tests (8 suites, 5 browsers) |
| **Content** | 84+ seeded items (54 tools, 12 success stories, 180+ trends, 13 blog articles) |
| **Payments** | Stripe live mode — 3 products, 6 prices (monthly + yearly), webhook active |
| **Monitoring** | Sentry (errors + traces + logs + AI spans), ascentia-km org, events confirmed |
| **Security** | HSTS, CSP, JWT ES256 JWKS, XSS prevention (bleach), rate limiting |
| **CI/CD** | GitHub Actions — main→production, develop→staging, all passing |
| **Scheduler** | All background jobs running (APScheduler + Railway Redis, verified 2026-02-19) — Gemini 429 retry active |

**Phase Completion**:
- ✅ Phase 1-3: MVP Foundation (scrapers, AI analysis, Next.js dashboard)
- ✅ Phase 4: Authentication & Admin Portal (Supabase Auth, 8-dimension scoring)
- ✅ Phase 5-7: Advanced Features (research, Stripe, teams, API keys, multi-tenancy)
- ✅ Phase 8-10: Enterprise Features (superadmin, engagement, integrations)
- ✅ Phase 12-14: Public Content & SEO (tools, success stories, trends, blog, sitemap)
- ✅ Phase A-L: Professional Overhaul (design system, admin portal, competitive features)
- ✅ Phase Q1-Q9: Quality Audit Fixes (Pulse, SEO, sanitization, rate limiting)
- ✅ Phase S: Security Hardening (HSTS, CSP, JWT ES256, XSS prevention)
- ✅ Phase M: Sentry Monitoring (errors + traces + logs + AI spans + Session Replay)
- ✅ Phase P: Production Deployment (Railway + Vercel + CI/CD pipeline)
- ✅ Phase R: Redis + Scheduler (Railway Redis provisioned, scheduler running clean)
- ✅ QA Bug Fixes: 11 P0/P1/P2 bugs fixed (terms/privacy 404, CORS, Deep Research, `$$`, Google OAuth signup, context-aware CTAs, skeleton loaders)
- ✅ 429 Rate-Limit Fix: tenacity retry + inter-call sleep in quality_reviewer.py (Gemini RESOURCE_EXHAUSTED eliminated)
- ✅ API Fixes: `/api/validate` 500 fixed (invalid `RawSignal` kwarg); `research.py` FastAPI deprecation warning cleared

**Business Metrics (Targets)**:
- Signup Conversion: 4% target (2% pre-Phase 14 baseline)
- PMF Validation Cost: ~$30/mo (Supabase Pro $25 + Gemini ~$5)
- Revenue Target: $59K MRR at 10K users (10% paid conversion)

**Competitive Position**:
- 100% feature parity with IdeaBrowser
- 11 unique competitive advantages
- 50-70% lower pricing

**Post-Launch Priorities (Tier 1 — This Week)**:
- ✅ Scraper pipeline fixed (Crawl4AI timeout + duplicate scheduling — 2026-02-22)
- ✅ CI/CD production deploy token fixed (`VERCEL_TOKEN`)
- ⏳ Uptime monitoring (UptimeRobot / Checkly — free, 15 min)
- ⏳ Google Search Console submission (`https://startinsight.co/sitemap.xml`)
- ⏳ Content seeding (50+ insights via admin portal → target 600+)

**Post-Launch Priorities (Tier 2 — Month 1)**:
- PostHog user analytics SDK
- New user onboarding banner
- Redis API response caching (60–300s TTL)
- E2E test expansion (auth + workspace + validate — ~38 tests)
- ProductHunt launch

See `memory-bank/improvement-plan.md` for full growth roadmap and `memory-bank/active-context.md` for current state.

---

## 📄 License

MIT License - See [LICENSE](LICENSE) file for details.

---

## 🙏 Acknowledgments

- **FastAPI**: For the excellent async Python framework
- **Google**: For Gemini 2.0 Flash (97% cost reduction, primary LLM)
- **Anthropic**: For Claude 3.5 Sonnet (fallback LLM, quality validation)
- **Firecrawl**: For making web scraping sane again
- **Next.js**: For the best React production framework
- **Playwright**: For comprehensive cross-browser E2E testing

---

## 📞 Support

For questions or issues:
- Check `memory-bank/` documentation
- Review `backend/README.md` for backend-specific help
- See `CLAUDE.md` for development guidelines

---

**Built with the "Glue Coding" philosophy: Don't reinvent, integrate.**

---

*v1.0.4 — Scraper pipeline fixed. CI/CD token fixed. Domain sweep complete. Professional favicon + OG image. ~$30/mo. (2026-02-22)*
