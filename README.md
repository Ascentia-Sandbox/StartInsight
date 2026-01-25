# StartInsight

> **AI-Powered Business Intelligence Engine for Startup Idea Discovery**

StartInsight is a daily, automated intelligence platform that discovers, validates, and presents data-driven startup ideas by analyzing real-time market signals from social discussions, search trends, and product launches.

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.109+-00C7B7.svg)](https://fastapi.tiangolo.com)
[![Next.js 14+](https://img.shields.io/badge/Next.js-14+-black.svg)](https://nextjs.org)

---

## 🎯 What is StartInsight?

Unlike traditional brainstorming tools, StartInsight relies on **real-time market signals** to identify genuine market gaps and consumer pain points. The system operates on an automated **"Collect → Analyze → Present"** loop, functioning as an analyst that never sleeps.

### Core Philosophy

- **Signal over Noise**: Surface problems real people are complaining about or searching for
- **Data-Driven Intuition**: Every insight backed by source data (Reddit threads, search trends)
- **Automated Intelligence**: AI agents handle market research, leaving users with high-level decision-making

---

## ✨ Features

### Current (Phase 1-7 Complete)

**Data Intelligence**
- **Automated Data Collection**: 7 data sources (Reddit, Product Hunt, Google Trends, Hacker News, Twitter/X, RSS feeds)
- **AI-Powered Analysis**: Gemini 2.0 Flash with 8-dimension scoring (97% cost reduction vs Claude)
- **40-Step Research Agent**: Comprehensive market research with admin approval queue
- **Evidence Visualizations**: Radar charts, KPI cards, community engagement metrics

**User Features**
- **Visual Dashboard**: Next.js interface with insights, trend graphs, filters, dark mode
- **Workspace Management**: Save insights, rate quality, claim for development
- **Team Collaboration**: RBAC with owner/admin/member roles, shared insights
- **Custom Research**: Submit research requests with tier-based approval (Free: manual, Starter/Pro/Enterprise: auto-approved)

**Admin Portal**
- **Super Admin Sovereignty**: Full control over AI agents, research approval queue, system monitoring
- **Real-time Monitoring**: SSE streaming dashboard, agent status control (pause/resume/trigger)
- **Revenue Analytics**: Stripe 4-tier subscriptions, usage tracking, payment history
- **Multi-Tenancy**: Subdomain routing, custom domains, tenant branding

**Developer Features**
- **API Key Management**: Scoped keys with usage tracking, rate limiting
- **Export Tools**: PDF/CSV/JSON exports with brand customization
- **Row-Level Security**: Supabase RLS policies on all 22 tables
- **Comprehensive Testing**: 47 E2E tests (Playwright), 26 backend tests (pytest)

---

## 🏗️ Architecture

```mermaid
graph LR
    A[Reddit/PH/Trends] -->|Firecrawl| B[Arq Worker]
    B -->|Raw Signals| C[(PostgreSQL)]
    C -->|Unprocessed| D[Claude 3.5]
    D -->|Insights| C
    C -->|API| E[FastAPI]
    E -->|JSON| F[Next.js Dashboard]
    G[Redis] -.->|Queue| B
```

### The Three Core Loops

1. **Loop 1: Data Collection** (Every 6 hours)
   - Scrapes content using Firecrawl (markdown format)
   - Stores raw signals in PostgreSQL with metadata

2. **Loop 2: Analysis** (After each collection)
   - Claude 3.5 Sonnet processes unprocessed signals
   - Validates output with Pydantic schemas
   - Scores relevance and market potential

3. **Loop 3: Presentation** (On-demand)
   - FastAPI serves ranked insights via REST
   - Next.js dashboard displays top insights

---

## 🛠️ Tech Stack

### Backend
- **Framework**: FastAPI (async-first)
- **Language**: Python 3.11+
- **Database**: Supabase PostgreSQL (ap-southeast-1, Singapore)
- **ORM**: SQLAlchemy 2.0 (async)
- **Queue**: Redis + Arq (async task queue)
- **AI**: PydanticAI + Gemini 2.0 Flash ($0.10/M tokens)
- **Auth**: Supabase Auth (OAuth + email/password)

### Frontend
- **Framework**: Next.js 16.1.3 (App Router, React 19)
- **Language**: TypeScript
- **Styling**: Tailwind CSS
- **Components**: shadcn/ui
- **Charts**: Recharts (radar, line, area, bar)
- **State**: TanStack Query (React Query)

### Data Pipeline
- **Scraping**: Firecrawl (web → markdown), Tweepy (Twitter/X)
- **Reddit**: PRAW (Python Reddit API Wrapper)
- **Trends**: pytrends (Google Trends API)
- **RSS**: feedparser (custom feeds)

### Services
- **Payments**: Stripe (4-tier subscriptions, webhooks)
- **Email**: Resend (6 email templates)
- **Rate Limiting**: SlowAPI + Redis (tier-based quotas)

### DevOps
- **Database**: Supabase Cloud (PostgreSQL 15+, Row-Level Security)
- **Cache**: Redis 7
- **Package Managers**: `uv` (Python), `pnpm` (Node.js)
- **Migrations**: Alembic + Supabase migrations (15 total)
- **Linting**: Ruff (Python), ESLint + Prettier (TypeScript)

---

## 🚀 Quick Start

### Prerequisites

- **Python 3.11+**
- **Node.js 18+**
- **Docker & Docker Compose**
- **uv** (Python package manager): `curl -LsSf https://astral.sh/uv/install.sh | sh`
- **pnpm**: `npm install -g pnpm`

### 1. Clone the Repository

```bash
git clone https://github.com/Ascentia-Sandbox/StartInsight.git
cd StartInsight
```

### 2. Environment Setup

**Backend (.env)**:
```bash
cd backend
cp .env.example .env
```

Edit `backend/.env`:
```bash
# Database (Supabase Cloud or Local Docker)
DATABASE_URL=postgresql+asyncpg://postgres:[password]@db.[project].supabase.co:5432/postgres
SUPABASE_URL=https://[project].supabase.co
SUPABASE_SERVICE_ROLE_KEY=your_supabase_service_role_key

# Cache
REDIS_URL=redis://localhost:6379

# AI (Gemini 2.0 Flash)
GOOGLE_API_KEY=your_google_ai_api_key

# Scraping
FIRECRAWL_API_KEY=your_firecrawl_api_key
REDDIT_CLIENT_ID=your_reddit_client_id
REDDIT_CLIENT_SECRET=your_reddit_client_secret
TWITTER_BEARER_TOKEN=your_twitter_bearer_token

# Payments (Stripe)
STRIPE_SECRET_KEY=your_stripe_secret_key
STRIPE_WEBHOOK_SECRET=your_stripe_webhook_secret

# Email (Resend)
RESEND_API_KEY=your_resend_api_key
```

**Frontend (.env.local)**:
```bash
cd ../frontend
cp .env.example .env.local
```

Edit `frontend/.env.local`:
```bash
NEXT_PUBLIC_API_URL=http://localhost:8000
NEXT_PUBLIC_SUPABASE_URL=https://[project].supabase.co
NEXT_PUBLIC_SUPABASE_ANON_KEY=your_supabase_anon_key
```

### 3. Start Infrastructure

```bash
# OPTION A: Redis only (use Supabase Cloud for database)
docker-compose up -d redis

# OPTION B: Redis + PostgreSQL (for local dev/testing)
docker-compose up -d
```

Verify containers are running:
```bash
docker ps
# Should show: startinsight-redis (and startinsight-postgres if using Option B)
```

### 4. Initialize Database

```bash
cd backend

# Install dependencies
uv sync

# Run database setup
uv run python check_db_connection.py

# Run migrations
uv run alembic upgrade head
```

### 5. Start Backend

```bash
# From backend/ directory
uv run uvicorn app.main:app --reload
```

Backend runs at: **http://localhost:8000**
- API docs: http://localhost:8000/docs
- Health check: http://localhost:8000/health

### 6. Start Frontend (Phase 3)

```bash
# From frontend/ directory
pnpm install
pnpm dev
```

Frontend runs at: **http://localhost:3000**

---

## 🌏 Architecture: Supabase Cloud (Singapore)

StartInsight uses **Supabase Cloud** as the primary production database:

- **Region:** ap-southeast-1 (Singapore) - Optimized for APAC market
- **Latency:** <50ms for Southeast Asia (vs 180ms US-based)
- **Cost:** $25/mo (Supabase Pro) vs $69/mo (Neon) = 64% savings
- **Features:** PostgreSQL 15+, Row-Level Security, real-time, storage

### Local Development Options

**Option A: Supabase Cloud (Recommended)**
- Best for testing RLS policies
- Set `SUPABASE_URL` and `DATABASE_URL` in `.env`
- Compatible with all Supabase features (real-time, storage)

**Option B: Docker PostgreSQL (Faster Iteration)**
- Offline development capability
- Faster test execution (no network latency)
- Run `docker-compose up -d` for full local stack

---

## 📁 Project Structure

```
StartInsight/
├── backend/                    # FastAPI application
│   ├── app/
│   │   ├── core/              # Config, errors, dependencies
│   │   ├── db/                # Database session, base classes
│   │   ├── models/            # SQLAlchemy models
│   │   ├── schemas/           # Pydantic schemas
│   │   ├── api/               # API routes
│   │   ├── agents/            # AI agent definitions
│   │   ├── scrapers/          # Data collection modules
│   │   └── main.py            # FastAPI entry point
│   ├── alembic/               # Database migrations
│   ├── tests/                 # Pytest test suite
│   ├── pyproject.toml         # Python dependencies (uv)
│   └── README.md              # Backend-specific docs
│
├── frontend/                   # Next.js application (Phase 3)
│   ├── app/                   # Next.js 14+ App Router
│   ├── components/            # React components
│   ├── lib/                   # Utilities & API client
│   └── package.json           # Node dependencies
│
├── memory-bank/               # Project documentation
│   ├── project-brief.md       # Executive summary
│   ├── active-context.md      # Current phase & tasks
│   ├── implementation-plan.md # 3-phase roadmap
│   ├── architecture.md        # System design
│   ├── tech-stack.md          # Technology decisions
│   └── progress.md            # Development log
│
├── .claude/                   # Claude Code configuration
│   ├── agents/                # Custom Claude agents
│   └── skills/                # Code quality standards
│
├── docker-compose.yml         # PostgreSQL + Redis setup
├── CLAUDE.md                  # Claude Code guidelines
└── README.md                  # This file
```

---

## 🔄 Development Workflow

### Common Commands

```bash
# Backend Development
cd backend && uv run uvicorn app.main:app --reload

# Frontend Development
cd frontend && pnpm dev

# Database Migrations
cd backend && uv run alembic upgrade head

# Run Tests
cd backend && uv run pytest

# Lint & Format
cd backend && uv run ruff check . --fix
cd frontend && pnpm lint --fix
```

### Database Utilities

```bash
# Check database connection
uv run python backend/check_db_connection.py

# Create new migration
cd backend && uv run alembic revision --autogenerate -m "description"

# View migration history
cd backend && uv run alembic history

# Rollback migration
cd backend && uv run alembic downgrade -1
```

### Docker Management

```bash
# Start services
docker-compose up -d

# Stop services
docker-compose down

# View logs
docker-compose logs -f postgres
docker-compose logs -f redis

# Reset database (⚠️ destroys data)
docker-compose down -v
docker-compose up -d
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

```bash
# Run all tests
cd backend && uv run pytest

# Run with coverage
uv run pytest --cov=app --cov-report=html

# Run specific test file
uv run pytest tests/test_scrapers.py

# Run with verbose output
uv run pytest -v
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
| **Supabase** | Database + Auth (ap-southeast-1) | [supabase.com](https://supabase.com) |
| **Google AI** | Gemini 2.0 Flash (AI analysis) | [aistudio.google.com](https://aistudio.google.com) |
| **Firecrawl** | Web scraping (web → markdown) | [firecrawl.dev](https://firecrawl.dev) |
| **Reddit** | Reddit API (PRAW) | [reddit.com/prefs/apps](https://reddit.com/prefs/apps) |
| **Twitter** | Twitter/X API (Tweepy) | [developer.twitter.com](https://developer.twitter.com) |
| **Stripe** | Payments (subscriptions) | [stripe.com](https://stripe.com) |
| **Resend** | Email (transactional) | [resend.com](https://resend.com) |

Store keys in `backend/.env` and `frontend/.env.local` (never commit `.env` files).

---

## 📊 Current Status

**Active Phase**: Phase 1-7 Complete (100%) - Production Ready

**Backend**: 105 API endpoints, 22 database tables, 11 services
**Frontend**: 18 routes (dashboard, workspace, research, admin, teams, settings, billing)
**Database**: 15 Supabase migrations applied, Row-Level Security enabled
**AI Agents**: 3 agents (basic analyzer, 8-dimension scoring, 40-step research)

**Completed**:
- ✅ Phase 1-3: MVP Foundation (scrapers, analyzer, Next.js dashboard)
- ✅ Phase 4: Authentication & Admin Portal (Supabase Auth, SSE streaming, 8-dimension scoring)
- ✅ Phase 5: AI Research Agent (40-step research, admin approval queue, brand/landing generators)
- ✅ Phase 6: Monetization (Stripe 4-tier, Resend email, team collaboration)
- ✅ Phase 7: Expansion (Twitter/X scraper, API keys, multi-tenancy)
- ✅ Phase 5.2: Super Admin Sovereignty + Evidence Visualizations (research request queue, radar charts, KPI cards)

**Next**:
- 🚀 Production Deployment (Railway + Vercel + Supabase Cloud)
- 📊 Monitoring Setup (Sentry, uptime checks)
- 🧪 E2E Test Updates (optional, 47 tests exist)

See `memory-bank/active-context.md` for deployment checklist.

---

## 📄 License

MIT License - See [LICENSE](LICENSE) file for details.

---

## 🙏 Acknowledgments

- **FastAPI**: For the excellent async Python framework
- **Anthropic**: For Claude 3.5 Sonnet (the AI powering insights)
- **Firecrawl**: For making web scraping sane again
- **Next.js**: For the best React production framework

---

## 📞 Support

For questions or issues:
- Check `memory-bank/` documentation
- Review `backend/README.md` for backend-specific help
- See `CLAUDE.md` for development guidelines

---

**Built with the "Glue Coding" philosophy: Don't reinvent, integrate.**
