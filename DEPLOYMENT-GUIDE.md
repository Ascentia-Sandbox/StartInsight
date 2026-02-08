# StartInsight - Deployment & Product Reference

> Comprehensive deployment, infrastructure, and operational reference for StartInsight.
> Sourced from actual codebase configuration files as of 2026-02-09.
> **Infrastructure:** Supabase Pro as sole database (no local PostgreSQL needed).

---

## Table of Contents

1. [Product Overview](#1-product-overview)
2. [Infrastructure & Cost](#2-infrastructure--cost)
3. [Complete Environment Variables](#3-complete-environment-variables)
4. [Local Development Setup](#4-local-development-setup)
5. [Database & Migrations](#5-database--migrations)
6. [Backend Architecture](#6-backend-architecture)
7. [Frontend Architecture](#7-frontend-architecture)
8. [CI/CD Pipeline](#8-cicd-pipeline)
9. [Production Deployment](#9-production-deployment)
10. [Monitoring & Observability](#10-monitoring--observability)
11. [Post-Deployment Monitoring](#11-post-deployment-monitoring)
12. [Rollback Procedures](#12-rollback-procedures)
13. [Troubleshooting](#13-troubleshooting)
14. [Testing](#14-testing)

---

## 1. Product Overview

StartInsight is an AI-powered startup insight platform that scrapes signals from Reddit, Product Hunt, Google Trends, and Twitter, runs them through 6 PydanticAI agents (Gemini 2.0 Flash), and surfaces actionable startup ideas with evidence-backed scoring.

**Key Stats:** 69 database tables | 230 API endpoints | 6 AI agents | 4 data sources | 4 pricing tiers

### Architecture Diagram

```
                    +-----------+
                    |  Vercel   |
                    | Next.js   |
                    | 16.1.3    |
                    +-----+-----+
                          |
                          | HTTPS (REST + SSE)
                          v
                    +-----+-----+
                    |  Railway   |
                    |  FastAPI   |
                    |  Python    |
                    |  3.12      |
                    +--+--+--+--+
                       |  |  |
            +----------+  |  +----------+
            |             |             |
            v             v             v
     +------+---+  +-----+------+  +---+-------+
     | Supabase |  |  Upstash   |  |  Gemini   |
     | Postgres |  |  Redis     |  |  2.0 Flash|
     | (SG)     |  |            |  |  + Claude  |
     +----------+  +------------+  +-----------+
```

---

## 2. Infrastructure & Cost

### Provider Table

| Provider | Service | Purpose | Plan |
|----------|---------|---------|------|
| **Railway** | Backend hosting | FastAPI + Docker | Pro ($20/mo) or Free ($5 credit) |
| **Vercel** | Frontend hosting | Next.js 16 | Pro ($20/mo) or Hobby (Free) |
| **Supabase** | PostgreSQL (Australia) | Sole database (dev + prod) | Pro ($25/mo) |
| **Upstash** | Redis | Cache + task queue | Pay-as-you-go (~$40/mo) or Railway Free |
| **Google** | Gemini 2.0 Flash | Primary LLM | Free tier (1.5K req/day) or API |
| **Crawl4AI** | Web scraping | Self-hosted scraper | $0 (runs in Railway) |
| **Sentry** | Error tracking | Backend + frontend | Free (5K events) or Team ($26/mo) |
| **Resend** | Transactional email | Notifications | Free (3K emails) or Pro ($35/mo) |
| **Stripe** | Payment processing | Subscriptions | 2.9% + $0.30/tx |

### PMF Validation Cost (~$30/mo)

| Service | Tier | Monthly Cost | Notes |
|---------|------|-------------|-------|
| **Supabase** | **Pro** | **$25** | 8GB, 200 connections (already paid) |
| **Railway** | Free | $5 | $5 starter credit, single container |
| **Vercel** | Hobby (Free) | $0 | Frontend hosting |
| **Redis** | Railway addon | $0 | Included in Railway |
| **Gemini AI** | Free tier | $0 | 1,500 requests/day |
| **Resend** | Free tier | $0 | 3K emails/month |
| **Sentry** | Free tier | $0 | 5K events/month |
| **Crawl4AI** | Self-hosted | $0 | Runs in Railway container |
| **TOTAL** | | **~$30/mo** | |

### Production Cost (at 10K users)

| Component | Cost | Notes |
|-----------|------|-------|
| Supabase (Pro) | $25 | Sole database (200 connections, 8GB) |
| Upstash Redis | $40 | Cache + task queue |
| Railway (Backend) | $100 | FastAPI hosting |
| Vercel (Frontend) | $20 | Next.js hosting |
| AI/LLM (Gemini) | $75 | Primary agent (97% cheaper than Claude) |
| Auth + Email | $145 | Supabase Auth + Resend |
| Marketing | $78 | Resend Pro + Vercel Analytics |
| **Total** | **~$483/mo** | **PMF: ~$30/mo** (94% reduction) |

### Revenue Projections (10K users)

| Tier | Users | Price | MRR |
|------|-------|-------|-----|
| Free | 9,000 | $0 | $0 |
| Starter | 500 | $19/mo | $9,500 |
| Pro | 400 | $49/mo | $19,600 |
| Enterprise | 100 | $299/mo | $29,900 |
| **Total** | **10,000** | | **$59,000/mo** |

**Profit margin:** ~99% ($58,500/mo profit)

### Competitive Positioning vs IdeaBrowser

| Metric | IdeaBrowser (est.) | StartInsight |
|--------|-------------------|--------------|
| Infrastructure cost | $550/mo | $483/mo (12% less) |
| MRR at 10K users | $43,709 | $59,000 (+35%) |
| LLM cost (GPT-4 vs Gemini) | $200/mo | $75/mo (63% less) |

---

## 3. Complete Environment Variables

### Backend (Railway) - from `backend/app/core/config.py`

#### Core

| Variable | Type | Default | Prod Required |
|----------|------|---------|:---:|
| `ENVIRONMENT` | str | `"development"` | Yes |
| `LOG_LEVEL` | str | `"info"` | No |
| `APP_VERSION` | str | `"0.1.0"` | No |
| `APP_URL` | str | `"http://localhost:3001"` | Yes (must be HTTPS) |

#### Database

| Variable | Type | Default | Prod Required |
|----------|------|---------|:---:|
| `DATABASE_URL` | PostgresDsn | (none) | Yes |
| `DB_POOL_SIZE` | int | `20` | No |
| `DB_MAX_OVERFLOW` | int | `30` | No |
| `DB_POOL_TIMEOUT` | int | `30` | No |
| `DB_POOL_RECYCLE` | int | `3600` | No |
| `DB_SSL` | bool | `True` | No |

#### Redis

| Variable | Type | Default | Prod Required |
|----------|------|---------|:---:|
| `REDIS_URL` | str | `"redis://localhost:6379"` | Yes |
| `REDIS_SSL` | bool | `False` | No |
| `REDIS_SOCKET_CONNECT_TIMEOUT` | int | `5` | No |
| `REDIS_SOCKET_TIMEOUT` | int | `5` | No |

#### AI / LLM

| Variable | Type | Default | Prod Required |
|----------|------|---------|:---:|
| `GOOGLE_API_KEY` | str? | `None` | Yes (primary) |
| `ANTHROPIC_API_KEY` | str? | `None` | Fallback |
| `OPENAI_API_KEY` | str? | `None` | Fallback |
| `DEFAULT_LLM_MODEL` | str | `"google-gla:gemini-2.0-flash"` | No |
| `LLM_CALL_TIMEOUT` | int | `120` (sec) | No |

#### Web Scraping

| Variable | Type | Default | Prod Required |
|----------|------|---------|:---:|
| `FIRECRAWL_API_KEY` | str? | `None` | Yes |
| `REDDIT_CLIENT_ID` | str? | `None` | Yes |
| `REDDIT_CLIENT_SECRET` | str? | `None` | Yes |
| `REDDIT_USER_AGENT` | str | `"StartInsight Bot v1.0"` | No |
| `REDDIT_USERNAME` | str? | `None` | No |
| `REDDIT_SUBREDDITS` | str | `"startups,SaaS"` | No |
| `REDDIT_POST_LIMIT` | int | `25` | No |
| `PRODUCT_HUNT_DAYS_BACK` | int | `1` | No |
| `PRODUCT_HUNT_LIMIT` | int | `10` | No |
| `TRENDS_TIMEFRAME` | str | `"now 7-d"` | No |
| `TRENDS_GEO` | str | `"US"` | No |

#### Auth / JWT (Supabase)

| Variable | Type | Default | Prod Required |
|----------|------|---------|:---:|
| `SUPABASE_URL` | str? | `None` | Yes |
| `SUPABASE_ANON_KEY` | str? | `None` | No |
| `SUPABASE_SERVICE_ROLE_KEY` | str? | `None` | Yes |
| `JWT_SECRET` | str? | `None` (min 32 chars) | Yes |
| `JWT_ALGORITHM` | str | `"HS256"` | No |
| `REFRESH_TOKEN_SECRET` | str? | `None` | Yes |
| `JWKS_FETCH_TIMEOUT` | float | `10.0` | No |
| `JWKS_CACHE_TTL` | int | `3600` | No |

#### Stripe Payments

| Variable | Type | Default | Prod Required |
|----------|------|---------|:---:|
| `STRIPE_SECRET_KEY` | str? | `None` | Yes |
| `STRIPE_PUBLISHABLE_KEY` | str? | `None` | Yes |
| `STRIPE_WEBHOOK_SECRET` | str? | `None` | Yes |
| `STRIPE_PRICE_STARTER` | str? | `None` | Yes |
| `STRIPE_PRICE_PRO` | str? | `None` | Yes |

#### Email (Resend)

| Variable | Type | Default | Prod Required |
|----------|------|---------|:---:|
| `RESEND_API_KEY` | str? | `None` | Yes |
| `EMAIL_FROM_ADDRESS` | str | `"noreply@startinsight.ai"` | No |
| `EMAIL_FROM_NAME` | str | `"StartInsight"` | No |

#### Rate Limiting

| Variable | Type | Default | Prod Required |
|----------|------|---------|:---:|
| `RATE_LIMIT_PER_MINUTE` | int | `60` | No |
| `RATE_LIMIT_PER_HOUR` | int | `1000` | No |
| `PUBLIC_API_RATE_LIMIT` | int | `100` (req/hr/key) | No |

#### Twitter/X

| Variable | Type | Default | Prod Required |
|----------|------|---------|:---:|
| `TWITTER_API_KEY` | str? | `None` | Optional |
| `TWITTER_API_SECRET` | str? | `None` | Optional |
| `TWITTER_ACCESS_TOKEN` | str? | `None` | Optional |
| `TWITTER_ACCESS_SECRET` | str? | `None` | Optional |
| `TWITTER_BEARER_TOKEN` | str? | `None` | Optional |

#### Multi-tenancy

| Variable | Type | Default | Prod Required |
|----------|------|---------|:---:|
| `ENABLE_MULTI_TENANCY` | bool | `False` | No |
| `DEFAULT_TENANT_ID` | str | `"default"` | No |
| `TENANT_BASE_DOMAIN` | str | `"startinsight.ai"` | No |
| `DEFAULT_MAX_USERS` | int | `10` | No |
| `DEFAULT_MAX_TEAMS` | int | `3` | No |
| `DEFAULT_MAX_API_KEYS` | int | `2` | No |

#### Monitoring / Observability

| Variable | Type | Default | Prod Required |
|----------|------|---------|:---:|
| `SENTRY_DSN` | str? | `None` | Yes |
| `SENTRY_TRACES_SAMPLE_RATE` | float | `0.1` (10%) | No |
| `SENTRY_PROFILES_SAMPLE_RATE` | float | `0.1` (10%) | No |
| `SLACK_WEBHOOK_URL` | str? | `None` | Recommended |

#### Middleware & Security

| Variable | Type | Default | Prod Required |
|----------|------|---------|:---:|
| `MAX_REQUEST_SIZE` | int | `1000000` (1MB) | No |
| `SSE_MAX_DURATION` | int | `3600` (1h) | No |
| `CORS_ORIGINS` | str | `"http://localhost:3000,..."` | Yes |
| `CORS_ALLOWED_METHODS` | str | `"GET,POST,PUT,PATCH,DELETE,OPTIONS"` | No |
| `CORS_ALLOWED_HEADERS` | str | `"Authorization,Content-Type,..."` | No |
| `CORS_ALLOWED_PRODUCTION_ORIGINS` | str | `"https://startinsight.app,..."` | No |
| `CSP_CONNECT_SRC` | str | `"'self' https://generativelanguage.googleapis.com https://*.supabase.co"` | No |

#### Worker (Arq)

| Variable | Type | Default | Prod Required |
|----------|------|---------|:---:|
| `WORKER_MAX_JOBS` | int | `10` | No |
| `WORKER_JOB_TIMEOUT` | int | `600` (10min) | No |
| `SCRAPE_INTERVAL_HOURS` | int | `6` | No |
| `ANALYSIS_BATCH_SIZE` | int | `10` | No |

#### API Server

| Variable | Type | Default | Prod Required |
|----------|------|---------|:---:|
| `API_HOST` | str | `"0.0.0.0"` | No |
| `API_PORT` | int | `8000` | No |
| `API_RELOAD` | bool | `False` | Must be `False` |

### Frontend (Vercel) - from `frontend/lib/env.ts`

| Variable | Required | Notes |
|----------|:--------:|-------|
| `NEXT_PUBLIC_API_URL` | Yes | Backend API base URL |
| `NEXT_PUBLIC_SUPABASE_URL` | Yes | Supabase project URL |
| `NEXT_PUBLIC_SUPABASE_ANON_KEY` | Yes | Supabase anonymous key |
| `NEXT_PUBLIC_SUPPORT_EMAIL` | No | Default: `support@startinsight.ai` |
| `NEXT_PUBLIC_CONTACT_EMAIL` | No | Default: `hello@startinsight.ai` |
| `NEXT_PUBLIC_ENTERPRISE_EMAIL` | No | Default: `enterprise@startinsight.ai` |
| `NEXT_PUBLIC_PRIVACY_EMAIL` | No | Default: `privacy@startinsight.ai` |
| `NEXT_PUBLIC_ENVIRONMENT` | No | `production` in prod |
| `NEXT_PUBLIC_STRIPE_PUBLISHABLE_KEY` | Yes | Stripe public key |
| `NEXT_PUBLIC_SITE_URL` | No | Canonical URL for sitemap |
| `NEXT_PUBLIC_SITE_NAME` | No | OG tags, meta titles |
| `SENTRY_DSN` | Yes | Server-side Sentry DSN |
| `NEXT_PUBLIC_SENTRY_DSN` | Yes | Client-side Sentry DSN |

### CI/CD (GitHub Actions) Secrets

| Secret | Used By | Purpose |
|--------|---------|---------|
| `RAILWAY_TOKEN` | deploy job | Railway CLI authentication |
| `VERCEL_TOKEN` | deploy job | Vercel CLI authentication |
| `VERCEL_ORG_ID` | deploy job | Vercel organization ID |
| `VERCEL_PROJECT_ID` | deploy job | Vercel project ID |
| `BACKEND_URL` | deploy job | Post-deploy health check URL |

---

## 4. Local Development Setup

### Prerequisites

- Python 3.12
- Node.js 20+ (22 LTS recommended)
- Docker & Docker Compose
- `uv` (Python package manager)

### Backend

```bash
cd backend

# Install dependencies
uv pip install --system -r pyproject.toml

# Copy environment file
cp .env.example .env  # Edit with your API keys

# Start Docker services (Redis only -- database is Supabase Pro, no local PostgreSQL needed)
docker compose up -d

# Run database migrations
alembic upgrade head

# Start development server
uvicorn app.main:app --reload --port 8000
```

### Frontend

```bash
cd frontend

# Install dependencies
npm install

# Create environment file
cp .env.example .env.local  # Edit with your keys

# Start development server
npm run dev  # Default: http://localhost:3000
```

### Worker (Background Jobs)

```bash
cd backend
arq app.worker.WorkerSettings
```

### Docker Compose Services

From `docker-compose.yml` (database is Supabase Pro -- no local PostgreSQL):

| Service | Image | Port | Purpose |
|---------|-------|------|---------|
| `redis` | redis:7-alpine | 6379:6379 | Cache + task queue |
| `redis-commander` | rediscommander (tools profile) | 8081:8081 | Redis GUI |

```bash
# Start Redis
docker compose up -d

# Start with dev tools (Redis Commander)
docker compose --profile tools up -d
```

**Database connection string** (Supabase Pro - Session Pooler):
```
postgresql+asyncpg://postgres.[PROJECT_REF]:[PASSWORD]@aws-1-ap-southeast-2.pooler.supabase.com:5432/postgres
```

**Connection Pool Configuration:**
- Pool size: 20 (restore from 5 for Pro tier)
- Max overflow: 30 (restore from 10 for Pro tier)
- SSL: Required (`DB_SSL=true`)
- Supabase Pro: 200 connections, 8GB storage, $25/mo

---

## 5. Database & Migrations

### Alembic Commands

```bash
cd backend

# Apply all migrations
alembic upgrade head

# Rollback one migration
alembic downgrade -1

# Rollback to specific revision
alembic downgrade b009

# Generate new migration
alembic revision --autogenerate -m "description"

# Show migration history
alembic history --verbose

# Show current revision
alembic current
```

### Migration Inventory

37 migration files across phases 1-14 (selected highlights):

| Migration | Phase | Description |
|-----------|-------|-------------|
| `955917ed64f1` | 1 | Create raw_signals table |
| `3d17254743b8` | 1 | Create insights table |
| `a001` - `a005` | 4-5 | User auth, admin, scoring, interactions, analyses |
| `68bc7f9b5a31` | 6-7 | Subscriptions, teams, API keys |
| `b001` - `b011` | 6-12 | Webhooks, soft delete, visualizations, indexes, content hash |
| `b012` - `b021` | 8-10 | Content quality, pipeline, analytics, agents, preferences, community, social, gamification, integrations |
| `b022` - `b023` | 12 | Market sizing, success story URLs |

### Connection Pool Configuration

From `config.py` — applied via SQLAlchemy `create_async_engine` (Supabase Pro: 200 connections):

| Setting | Default | Description |
|---------|---------|-------------|
| `DB_POOL_SIZE` | 20 | Maintained connections |
| `DB_MAX_OVERFLOW` | 30 | Extra connections beyond pool |
| `DB_POOL_TIMEOUT` | 30s | Wait for available connection |
| `DB_POOL_RECYCLE` | 3600s | Recycle connections after 1 hour |
| `DB_SSL` | true | Required for Supabase |

**Effective max connections:** 50 (20 pool + 30 overflow) out of 200 available (Supabase Pro)

---

## 6. Backend Architecture

### Middleware Stack

Middleware executes **bottom-up** for requests and **top-down** for responses. Registration order in `main.py`:

```
# Registration order (last registered = outermost = runs first):
1. TracingMiddleware          # Correlation IDs + request timing
2. RequestIDMiddleware        # X-Request-ID header
3. SecurityHeadersMiddleware  # CSP, HSTS, X-Frame-Options
4. RequestSizeLimitMiddleware # 1MB max body size (413 if exceeded)
5. APIVersionMiddleware       # API-Version + X-API-Version headers
6. CORSMiddleware             # CORS policy enforcement
```

**Security headers added by SecurityHeadersMiddleware:**
- `X-Frame-Options: DENY`
- `X-Content-Type-Options: nosniff`
- `Strict-Transport-Security: max-age=31536000; includeSubDomains` (HTTPS only)
- `X-XSS-Protection: 1; mode=block`
- `Referrer-Policy: strict-origin-when-cross-origin`
- `Content-Security-Policy: default-src 'self'; connect-src {configurable}`

### Health Endpoints

| Endpoint | Purpose | Response |
|----------|---------|----------|
| `GET /health` | Basic liveness (load balancer) | `{"status": "healthy"}` |
| `GET /health/ready` | Readiness (checks DB + Redis) | `{"status": "ready", "checks": {...}}` |
| `GET /health/live` | Liveness (deadlock detection) | `{"status": "alive"}` |
| `GET /health/scraping` | Pipeline monitoring | Last runs, pending signals, queue depth, error rate |

### Background Jobs (APScheduler + Arq)

8 scheduled tasks defined in `backend/app/tasks/scheduler.py`:

| Job | Schedule | Description |
|-----|----------|-------------|
| `scrape_all_sources` | Every 6h (configurable) | Reddit, Product Hunt, Google Trends |
| `analyze_signals` | Every 6h | PydanticAI analysis of raw signals |
| `send_daily_digests` | Daily 09:00 UTC (Cron) | Email digest to subscribers |
| `fetch_daily_insight` | Daily 08:00 UTC (Cron) | AI-generated insight of the day |
| `market_insight_publisher` | Every 3 days 06:00 UTC | Publish market insight articles |
| `market_insight_quality_review` | Every 3 days 08:30 UTC | Quality review of published articles |
| `insight_quality_audit` | Weekly Mon 03:00 UTC | Audit insight quality scores |
| `update_success_stories` | Weekly Sun 05:00 UTC | Refresh success story data |

**Architecture:** APScheduler triggers jobs -> Arq enqueues tasks into Redis -> Worker processes asynchronously.

### Redis Cache TTLs

From `backend/app/core/cache.py`:

| Entity | TTL | Key Pattern |
|--------|-----|-------------|
| Tools directory | 1 hour | `cache:tools:*` |
| Trends | 15 min | `cache:trends:*` |
| Insights | 5 min | `cache:insights:*` |
| Success stories | 1 hour | `cache:success_stories:*` |
| Market insights | 30 min | `cache:market_insights:*` |
| Idea of the day | 1 hour | `cache:idea_of_day` |
| Default | 5 min | `cache:*` |

### Rate Limiting (SlowAPI + Redis)

Tier-based rate limits from `backend/app/core/rate_limits.py`:

| Tier | Limit | Key Strategy |
|------|-------|-------------|
| Anonymous | 20/min | IP address |
| Free | 30/min | User ID |
| Starter | 60/min | User ID |
| Pro | 120/min | User ID |
| Enterprise | 300/min | User ID |

**Global defaults:** 100/min, 1000/hour

### Authentication

- **JWT:** ES256 (ECDSA P-256) via Supabase JWKS endpoint, with HS256 fallback
- **JWKS URL:** `{SUPABASE_URL}/auth/v1/.well-known/jwks.json`
- **JWT issuer:** `{SUPABASE_URL}/auth/v1`
- **Token verification:** `python-jose[cryptography]`
- **Production validation:** `config.py` model validator enforces JWT_SECRET, SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY, SENTRY_DSN, REFRESH_TOKEN_SECRET, HTTPS APP_URL, no localhost CORS, no API_RELOAD

### Global Exception Handlers

Registered in `main.py`:

| Exception | HTTP Code | Behavior |
|-----------|-----------|----------|
| `Exception` (catch-all) | 500 | Generic message, logs stack trace, Sentry capture |
| `RequestValidationError` | 422 | Field-level error details |
| `IntegrityError` | 409 | Duplicate key / FK constraint messages |
| `OperationalError` | 503 | Service unavailable, Sentry capture |
| `JWTError` | 401 | Invalid/expired token |
| `RateLimitExceeded` | 429 | Rate limit message with Retry-After header |

---

## 7. Frontend Architecture

### Stack

- **Framework:** Next.js 16.1.3 (App Router, Turbopack)
- **Language:** TypeScript 5.3+
- **Styling:** Tailwind CSS 4.0 + shadcn/ui (25 components)
- **State:** TanStack Query 5.x (React Query)
- **Charts:** Recharts 3.6.0 (React 19 compatible)
- **i18n:** next-intl
- **Error tracking:** Sentry (client + server)

### Centralized Environment Config

`frontend/lib/env.ts` provides build-time validation:

```typescript
export const config = {
  apiUrl: requireEnv('NEXT_PUBLIC_API_URL'),
  supabaseUrl: requireEnv('NEXT_PUBLIC_SUPABASE_URL'),
  supabaseAnonKey: requireEnv('NEXT_PUBLIC_SUPABASE_ANON_KEY'),
  // ... optional vars with defaults
}
```

Build fails immediately if required env vars are missing.

### Docker Output

Next.js configured with `standalone` output for Docker deployments.

---

## 8. CI/CD Pipeline

### GitHub Actions Workflow

File: `.github/workflows/ci-cd.yml`

**Triggers:** Push to `main`/`develop`, PRs to `main`

#### Jobs

| Job | Runs On | Dependencies | Condition |
|-----|---------|-------------|-----------|
| `backend-test` | ubuntu-latest | PG 16 + Redis 7 | Always |
| `frontend-test` | ubuntu-latest | Node.js 20 | Always |
| `security-scan` | ubuntu-latest | pip-audit + npm audit | Always |
| `docker-build` | ubuntu-latest | Needs backend-test + frontend-test | `main` branch only |
| `deploy` | ubuntu-latest | Needs all above | `main` branch push |

#### backend-test Steps

1. Checkout code
2. Set up Python 3.12
3. Install uv 0.5.14
4. Install dependencies (`uv pip install --system -r pyproject.toml`)
5. Run linter (`ruff check .`)
6. Run tests (`pytest tests/ -v --cov=app --cov-report=xml`)
7. Upload coverage to Codecov

**CI services:** PostgreSQL 16 (port 5432), Redis 7 (port 6379)

**CI env vars:** `DATABASE_URL`, `REDIS_URL`, `ANTHROPIC_API_KEY`, `OPENAI_API_KEY`, `FIRECRAWL_API_KEY`, `REDDIT_CLIENT_ID`, `REDDIT_CLIENT_SECRET`, `REDDIT_USER_AGENT` (all set to test values)

#### frontend-test Steps

1. Checkout code
2. Set up Node.js 20 (npm cache)
3. Install dependencies (`npm ci`)
4. Run linter (`npm run lint`)
5. TypeScript check (`npx tsc --noEmit`)
6. Build (`npm run build` with placeholder env vars)

#### security-scan Steps

1. Python: `pip-audit --strict` (backend dependencies)
2. Node.js: `npm audit --audit-level=high` (frontend dependencies)

#### docker-build Steps

1. Set up Docker Buildx
2. Build backend image (`backend/Dockerfile`, GHA cache)
3. Build frontend image (`frontend/Dockerfile`, GHA cache)

#### deploy Steps

1. Install Railway CLI + Vercel CLI
2. Deploy backend to Railway (`railway up --service backend`)
3. Deploy frontend to Vercel (`vercel --prod`)
4. Post-deploy health check (`curl /health`)

### Required GitHub Secrets

| Secret | Purpose |
|--------|---------|
| `RAILWAY_TOKEN` | Railway CLI authentication |
| `VERCEL_TOKEN` | Vercel CLI authentication |
| `VERCEL_ORG_ID` | Vercel organization identifier |
| `VERCEL_PROJECT_ID` | Vercel project identifier |
| `BACKEND_URL` | Production backend URL for health check |

---

## 9. Production Deployment

### Pre-Flight Checklist (~30 min)

#### 1. Rotate All Secrets (15 min)

```bash
# Generate new secrets
openssl rand -hex 64  # JWT_SECRET (128 chars)
openssl rand -hex 32  # REFRESH_TOKEN_SECRET (64 chars)

# Regenerate API keys:
# - Google: https://console.cloud.google.com
# - Stripe: https://dashboard.stripe.com (restricted keys)
# - Firecrawl: https://firecrawl.dev
# - Reddit: https://reddit.com/prefs/apps
# - Supabase: https://supabase.com/dashboard (rotate service role key)
```

#### 2. Create Sentry Projects (5 min)

Create two projects at https://sentry.io:
- `startinsight-backend` (Platform: Python/FastAPI)
- `startinsight-frontend` (Platform: Next.js)

Copy DSNs from Settings -> Client Keys (DSN).

#### 3. Set Environment Variables (10 min)

**Railway (Backend)** - set all [production-required variables](#backend-railway---from-backendappcoreconfg.py) listed in Section 3.

**Vercel (Frontend)** - set all [required frontend variables](#frontend-vercel---from-frontendlibenvts) listed in Section 3.

#### 4. Supabase Pro (already active)

Supabase Pro ($25/mo) provides 8GB storage and 200 connections. DATABASE_URL must point to Supabase Pro with SSL enabled (`DB_SSL=true`).

### Step-by-Step Deployment

#### Step 1: Migrate Database

```bash
cd backend
export DATABASE_URL="<production_database_url>"
alembic upgrade head
```

Verify production indexes (8 new indexes from `b010`):
```bash
psql $DATABASE_URL -c \
  "SELECT indexname FROM pg_indexes WHERE schemaname='public' AND indexname LIKE 'idx_%';"
```

#### Step 2: Deploy Backend (Railway)

```bash
git push origin main  # Railway auto-deploys from main
# Wait 2-3 minutes for deployment
```

**Railway configuration** (`backend/railway.toml`):
```toml
[build]
builder = "DOCKERFILE"
dockerfilePath = "backend/Dockerfile"

[deploy]
startCommand = "alembic upgrade head && uvicorn app.main:app --host 0.0.0.0 --port $PORT"
healthcheckPath = "/health"
healthcheckTimeout = 100
restartPolicyType = "ON_FAILURE"
restartPolicyMaxRetries = 10
```

#### Step 3: Verify Backend Health

```bash
curl https://api.startinsight.app/health/ready
# Expected: {"status":"ready","checks":{"database":"healthy","redis":"healthy"}}
```

#### Step 4: Deploy Frontend (Vercel)

```bash
cd frontend
vercel --prod
# Wait 1-2 minutes
```

**Vercel configuration** (`frontend/vercel.json`):
```json
{
  "framework": "nextjs",
  "regions": ["sfo1"],
  "headers": [
    {
      "source": "/(.*)",
      "headers": [
        { "key": "X-Content-Type-Options", "value": "nosniff" },
        { "key": "X-Frame-Options", "value": "DENY" },
        { "key": "X-XSS-Protection", "value": "1; mode=block" }
      ]
    }
  ]
}
```

#### Step 5: Smoke Tests

```bash
# 1. Frontend loads
curl -I https://startinsight.app
# Expected: 200 OK

# 2. API responds with request ID
curl -I https://api.startinsight.app/api/insights
# Expected: X-Request-ID header present

# 3. Rate limiting works
for i in {1..101}; do curl -s https://api.startinsight.app/api/insights > /dev/null; done
# Request #101 should return 429

# 4. Sentry receives errors
curl https://api.startinsight.app/api/test-sentry-error
# Check Sentry dashboard for event
```

### Dockerfile (Multi-Stage)

From `backend/Dockerfile`:

```dockerfile
# Stage 1: Builder
FROM python:3.12-slim AS builder
WORKDIR /app
RUN apt-get update && apt-get install -y curl build-essential && rm -rf /var/lib/apt/lists/*
RUN curl -LsSf https://astral.sh/uv/0.5.14/install.sh | sh
ENV PATH="/root/.local/bin:${PATH}"
COPY pyproject.toml .python-version* ./
RUN uv pip install --system -r pyproject.toml

# Stage 2: Runtime (no build tools)
FROM python:3.12-slim AS runtime
WORKDIR /app
COPY --from=builder /usr/local/lib/python3.12/site-packages /usr/local/lib/python3.12/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin
RUN apt-get update && apt-get install -y curl && rm -rf /var/lib/apt/lists/*
COPY app ./app
COPY alembic ./alembic
COPY alembic.ini ./
RUN useradd -m -u 1000 appuser && chown -R appuser:appuser /app
USER appuser
EXPOSE 8000
HEALTHCHECK --interval=30s --timeout=10s --start-period=10s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "2"]
```

**Key features:** Multi-stage build (builder + runtime), non-root user (`appuser`), pinned uv 0.5.14, 2 Uvicorn workers, built-in health check.

---

## 10. Monitoring & Observability

### Sentry Error Tracking

Initialized in `main.py` only when `SENTRY_DSN` is set AND `ENVIRONMENT=production`:

- **Integrations:** FastAPI (URL-style transactions), SQLAlchemy
- **Traces sample rate:** 10% (configurable via `SENTRY_TRACES_SAMPLE_RATE`)
- **Profiles sample rate:** 10% (configurable via `SENTRY_PROFILES_SAMPLE_RATE`)
- **Noise filtering:** Health check endpoints excluded via `before_send`
- **Docs disabled in production:** `/docs` and `/redoc` return 404

### Structured JSON Logging

From `backend/app/core/logging.py`:

- **Production:** JSON format via `JSONFormatter` (for log aggregation - ELK, Datadog, etc.)
- **Development:** Human-readable format (`timestamp - logger - level - message`)
- **Third-party noise reduction:** httpx, httpcore, SQLAlchemy engine set to WARNING

Each log entry includes:
```json
{
  "timestamp": "...",
  "level": "INFO",
  "logger": "app.main",
  "message": "GET /api/insights -> 200",
  "correlation_id": "a1b2c3d4",
  "request": { "method": "GET", "path": "/api/insights", "user_id": null, "client_ip": "..." }
}
```

### Request Tracing

**TracingMiddleware** (`app/middleware/tracing.py`):
- Extracts or generates `X-Correlation-ID` (8-char UUID prefix)
- Adds `X-Correlation-ID` and `X-Response-Time-Ms` to responses
- Logs every request: method, path, status, duration, client IP, user ID

**RequestIDMiddleware** (in `main.py`):
- Extracts or generates `X-Request-ID` (full UUID)
- Adds `X-Request-ID` to all responses

### Slack Alerts

Configure `SLACK_WEBHOOK_URL` for CRITICAL-level alerts.

### LLM Cost Tracking

MetricsTracker with per-model pricing (Gemini/Claude/GPT) for monitoring AI spend per user.

---

## 11. Post-Deployment Monitoring

### Hour 1: Critical Monitoring (every 15 min)

1. **Sentry Dashboard** (https://sentry.io)
   - Backend: <5 errors/hour expected
   - Frontend: <10 errors/hour (mostly 404s)

2. **Railway Logs**
   ```bash
   railway logs --environment production --filter ERROR
   ```
   - No connection pool timeouts
   - No 500 errors

3. **Supabase Dashboard**
   - Connection pooling: <50/200 connections (<25%) — Supabase Pro provides 200 connections
   - Alert if >160/200 (>80%)
   - Pool configured: 20 size + 30 overflow = 50 max per backend instance

### Hour 2-24: Regular Monitoring (every 2 hours)

1. **Error Rate** (Sentry): Threshold <1%, alert if >5%
2. **Response Time** (Railway): p95 <1s, alert if >3s
3. **Cache Hit Rate** (Upstash): Expected >80% after first hour

### Success Metrics (First Week)

| Metric | Target | Alert If |
|--------|--------|----------|
| Error Rate | <1% | >5% |
| Uptime | >99.9% | <99.5% |
| Response Time (p95) | <1s | >3s |
| Connection Pool Usage | <50/200 | >160/200 |
| Cache Hit Rate | >80% | <60% |
| Sentry Events | <100/day | >500/day |

---

## 12. Rollback Procedures

### Backend Rollback

```bash
# Option 1: Redeploy previous version via Railway UI
# Dashboard -> Deployments -> Previous deployment -> "Redeploy"

# Option 2: Rollback database migration
cd backend
export DATABASE_URL="<production_url>"
alembic downgrade -1  # Or specific revision: alembic downgrade b009

# Option 3: Git revert
git revert HEAD
git push origin main  # Railway auto-deploys
```

### Frontend Rollback

```bash
# Vercel UI: Deployments -> Previous deployment -> "Promote to Production"
# OR via CLI:
vercel rollback
```

---

## 13. Troubleshooting

### Health check returns "not_ready" (503)

**Diagnosis:**
```bash
curl https://api.startinsight.app/health/ready | python3 -m json.tool
# Shows: "database": "unhealthy" or "redis": "unhealthy"
```

**Database unhealthy:**
- Check Supabase dashboard for outages
- Verify `DATABASE_URL` is correct
- Check connection pool: `SELECT count(*) FROM pg_stat_activity;`

**Redis unhealthy:**
- Check Upstash dashboard
- Verify `REDIS_URL` is correct
- Test connectivity: `redis-cli -u $REDIS_URL ping`

### Connection pool exhaustion

**Symptoms:** `sqlalchemy.exc.TimeoutError: QueuePool limit exceeded`

**Diagnosis:**
```bash
psql $DATABASE_URL -c "SELECT count(*) FROM pg_stat_activity WHERE datname='postgres';"
# Alert if >45/50
```

**Solutions:**
1. **Immediate:** Restart Railway service (frees connections)
2. **Short-term:** Increase `DB_POOL_SIZE`/`DB_MAX_OVERFLOW` (currently 20/30 for Supabase Pro with 200 total connections)
3. **Long-term:** Identify slow queries holding connections; add query timeouts
4. **Note:** Supabase Pro provides 200 connections, sufficient for 4 backend instances (50 connections each)

### Rate limiting too aggressive

**Symptoms:** Users report "429 Too Many Requests"

**Diagnosis:**
Check tier configuration in `backend/app/core/rate_limits.py`:
```
Anonymous: 20/min, Free: 30/min, Starter: 60/min, Pro: 120/min, Enterprise: 300/min
```

**Solutions:**
1. Override tier limits via env vars: `RATE_LIMIT_TIER_FREE=50/minute`
2. Adjust global defaults in `rate_limits.py` (currently 100/min, 1000/hour)

### Sentry not receiving errors

**Symptoms:** Sentry dashboard shows no events after 1 hour

**Diagnosis:**
```bash
# Check env vars are set
railway variables | grep SENTRY
railway variables | grep ENVIRONMENT
```

**Solutions:**
- Verify `SENTRY_DSN` is correct (check Sentry project settings)
- Verify `ENVIRONMENT=production` (Sentry only initializes when both are set)
- Check Railway logs for Sentry initialization messages
- Test: `curl -X POST https://api.startinsight.app/api/test-sentry-error`

### Worker / scheduler not running

**Symptoms:** No new signals scraped, stale data

**Diagnosis:**
```bash
# Check scraping health
curl https://api.startinsight.app/health/scraping | python3 -m json.tool
# Shows last_runs per source, pending_signals, queue_depth
```

**Solutions:**
- Verify Redis is reachable (scheduler depends on Arq -> Redis)
- Check worker logs: `railway logs --service worker --filter ERROR`
- Manual trigger: `POST /api/admin/scraping/trigger`
- Verify `SCRAPE_INTERVAL_HOURS` (default: 6)

### Build fails on frontend

**Symptoms:** Vercel deploy fails during build

**Common causes:**
1. Missing env vars: `frontend/lib/env.ts` throws at build time if `NEXT_PUBLIC_API_URL`, `NEXT_PUBLIC_SUPABASE_URL`, or `NEXT_PUBLIC_SUPABASE_ANON_KEY` are missing
2. TypeScript errors: Run `npx tsc --noEmit` locally first
3. Lint errors: Run `npm run lint` locally first

---

## 14. Testing

### Backend Tests

```bash
cd backend

# Run all tests with coverage
pytest tests/ -v --cov=app --cov-report=html

# Run specific test file
pytest tests/test_health.py -v

# Run with marker
pytest -m "not slow" -v
```

**Target:** 291 tests, 85% coverage

### Frontend E2E Tests

```bash
cd frontend

# Install browsers (first time)
npx playwright install

# Run all E2E tests
npx playwright test

# Run with UI
npx playwright test --ui

# Run specific test
npx playwright test tests/insights.spec.ts
```

**Target:** 47 scenarios across 5 browsers (Chromium, Firefox, WebKit, Mobile Chrome, Mobile Safari)

### Linting

```bash
# Backend
cd backend && uv run ruff check . --fix

# Frontend
cd frontend && npm run lint
```

---

## Support Contacts

- **Railway:** https://railway.app/help
- **Vercel:** https://vercel.com/support
- **Supabase:** https://supabase.com/support
- **Sentry:** https://sentry.io/support

---

**Last Updated:** 2026-02-08
**Document Owner:** DevOps Team
**Review Frequency:** After each production deployment
