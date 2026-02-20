---
**Memory Bank Protocol**
**Reading Priority:** CRITICAL
**Read When:** When choosing libraries, verifying dependencies, resolving conflicts, cost planning
**Dependencies:** Read project-brief.md for "Glue Coding" philosophy
**Purpose:** Actual technology stack, dependency versions, MVP cost structure
**Last Updated:** 2026-02-19
---

# Tech Stack: StartInsight

## 1. MVP Cost Philosophy

**Constraint:** Minimize cost for PMF validation. Only two paid services are required — everything else runs on free tiers.

| Service | Cost | Tier | Purpose |
|---------|------|------|---------|
| **Supabase Pro** | **$25/mo** | Pro (required) | PostgreSQL + Auth, 8GB, 200 connections |
| **Gemini API** | **~$1-5/mo** | Pay-as-you-go | Primary LLM — $0.10/M input, $0.40/M output |
| Railway | $0 | Free (500h/mo) | Backend hosting + native Redis |
| Vercel | $0 | Hobby | Frontend hosting, unlimited bandwidth |
| Sentry | $0 | Free (5K events/mo) | Error tracking + performance |
| Resend | $0 | Free (3K emails/mo) | Transactional email |
| PRAW | $0 | Free API | Reddit scraping |
| pytrends | $0 | Unofficial API | Google Trends (no key required) |
| Firecrawl | $0 | Free (500 pages/mo) | Web → Markdown; free tier covers MVP |
| Crawl4AI | $0 | Self-hosted | Free Firecrawl alternative (runs in container) |
| Twitter/X | $0 | Free basic tier | 500K tweets/mo read access |
| Stripe | $0/mo + 2.9% | No monthly fee | Payments (fees only on revenue) |
| **Total** | **~$30/mo** | — | Full production platform |

**Scalability note:** At 10K paying users ($59K MRR target), costs scale to ~$50-70/mo (still 99%+ margin). Firecrawl Pro ($149/mo) is the only meaningful cost addition at that scale.

---

## 2. Frontend Stack

### Framework & Language
- **Next.js 16.1.3** — App Router, React Server Components, Turbopack
- **React 19.2.3** — Latest stable with concurrent features
- **TypeScript** — Strict typing throughout
- **Node.js 22.x LTS**

### Styling & Design System
- **Tailwind CSS 4.0** — New CSS architecture with `@layer` syntax
- **shadcn/ui** — 25 components (copy-paste, based on Radix UI)
- **Design system:** Deep teal primary + warm amber accent — "Data Intelligence" aesthetic
- **Typography:** Instrument Serif (headings) · Satoshi (body) · JetBrains Mono (data/scores)
- **Animation:** Framer Motion 12.x — stagger reveals, counter animations, skeleton morphing

### State & Data
- **TanStack Query 5.x** (`@tanstack/react-query`) — Server state, 60s stale time, 2 retries
- **React Hook Form + @hookform/resolvers** — Forms with Zod schema validation
- **Zod 4.x** — Runtime type validation of API responses and form data

### Charts & Visualization
- **Recharts 3.6.0** — React 19 compatible; radar charts, scatter charts, line/area/bar
- All visualizations implemented via Recharts. Tremor is not installed (not needed).

### Key Frontend Dependencies (actual `package.json`)
```json
{
  "next": "16.1.3",
  "react": "19.2.3",
  "react-dom": "19.2.3",
  "@tanstack/react-query": "^5.90.19",
  "recharts": "^3.6.0",
  "framer-motion": "^12.29.2",
  "tailwindcss": "^4.0",
  "@sentry/nextjs": "^10.38.0",
  "@supabase/ssr": "^0.8.0",
  "@supabase/supabase-js": "^2.91.1",
  "axios": "^1.13.2",
  "date-fns": "^4.1.0",
  "zod": "^4.3.6",
  "react-hook-form": "^7.71.1",
  "react-markdown": "^10.1.0",
  "remark-gfm": "^4.0.1",
  "lucide-react": "^0.562.0",
  "next-themes": "^0.4.6",
  "sonner": "^2.0.7",
  "@vercel/analytics": "^1.6.1",
  "@vercel/speed-insights": "^1.3.1"
}
```

---

## 3. Backend Stack

### Framework & Language
- **FastAPI ≥0.109** — Async-first, automatic OpenAPI/Swagger
- **Python 3.11+**
- **Uvicorn[standard]** — ASGI server
- **Pydantic V2** — Strict validation throughout
- **Pydantic Settings** — Environment variable management

### Database
- **PostgreSQL** via **Supabase Pro** (ap-southeast-2 Sydney)
  - Connection: session-mode pooler, SSL required
  - Pool: 20 size, 30 max overflow, recycle 3600s
  - 69 tables, all with Row-Level Security enabled
  - 25+ Alembic migrations (c009 at head)
- **SQLAlchemy 2.0 async** (`sqlalchemy[asyncio]>=2.0.25`)
- **asyncpg ≥0.29** — Async PostgreSQL driver
- **Alembic ≥1.13** — Migration version control

### Task Queue & Cache
- **Arq ≥0.25** — Async task queue (built on Redis), lighter than Celery
- **APScheduler ≥3.11** — Cron/interval job scheduling within FastAPI lifespan
- **Redis** — **Railway native Redis** (`redis.railway.internal:6379`, free, no TLS needed)
- `conn_retries=0, conn_timeout=3` — Fast startup even if Redis unavailable

### AI & Agents
- **PydanticAI ≥1.x** — Agent orchestration, native async, structured JSON output
  - All 8 agents use `output_type=` and `result.output` (v1.x API)
  - Model string: `"google-gla:gemini-2.0-flash"` (hardcoded in all agents)
- **Primary LLM: Gemini 2.0 Flash** via `GOOGLE_API_KEY`
  - $0.10/M input · $0.40/M output — 97% cheaper than Claude
  - 1M token context window
- **Fallback LLMs** (installed but not used in production to minimize cost):
  - `anthropic>=0.25.0` — Claude 3.5 Sonnet (activate only if Gemini quota exceeded)
  - `openai>=1.12.0` — GPT-4o (activate only for vision tasks if needed)

### Scraping & Data Collection
- **PRAW ≥7.7** — Reddit API (structured posts, scores, metadata). Free.
- **pytrends ≥4.9** — Google Trends (unofficial API, no key needed). Free.
- **Tweepy ≥4.14** — Twitter/X API (free basic tier, 500K reads/mo)
- **Firecrawl** (`firecrawl-py>=0.0.16`) — Web → Markdown. Free tier (500 pages/mo) for MVP.
- **Crawl4AI ≥0.2** (`USE_CRAWL4AI=true` on Railway) — Self-hosted Firecrawl alternative, $0 cost
- **BeautifulSoup4** — HTML parsing (Product Hunt scraper)

### Authentication & Security
- **python-jose[cryptography] ≥3.3** — JWT ES256 validation via Supabase JWKS
  - JWKS URL: `{supabase_url}/auth/v1/.well-known/jwks.json`
  - Issuer: `{supabase_url}/auth/v1`
- **bleach ≥6.1** — XSS prevention on all user inputs
- **itsdangerous ≥2.1** — Token signing for email unsubscribe

### Services
- **Stripe ≥7.0** — Subscriptions + webhooks. No monthly fee, 2.9% + 30¢ per transaction.
- **Resend ≥0.7** — Transactional email. Free tier (3K/mo) covers MVP.
- **SlowAPI ≥0.1.9** — Rate limiting (tier-based, in-memory for non-production)
- **sse-starlette ≥1.6.5** — Server-Sent Events for real-time feed + admin updates

### Observability
- **sentry-sdk[fastapi] ≥2.0.0**
  - `enable_logs=True` + `LoggingIntegration` (WARNING+ → Sentry Logs)
  - `FastApiIntegration` + `SqlalchemyIntegration`
  - User context via `sentry_sdk.set_user()` in `deps.py`
  - Manual `gen_ai.request` spans in enhanced_analyzer, research_agent, market_intel_agent
  - Sample rate: 10% production, 100% staging

### Key Backend Dependencies (actual `pyproject.toml`)
```toml
dependencies = [
    "fastapi>=0.109.0",
    "uvicorn[standard]>=0.27.0",
    "pydantic>=2.5.0",
    "pydantic-settings>=2.1.0",
    "sqlalchemy[asyncio]>=2.0.25",
    "alembic>=1.13.0",
    "asyncpg>=0.29.0",
    "redis>=5.0.1",
    "pydantic-ai>=0.0.13",        # v1.x in practice
    "anthropic>=0.25.0",           # fallback only
    "openai>=1.12.0",              # fallback only
    "firecrawl-py>=0.0.16",
    "crawl4ai>=0.2.0",             # free alternative (USE_CRAWL4AI=true)
    "playwright>=1.40.0",          # required by crawl4ai
    "praw>=7.7.1",
    "pytrends>=4.9.2",
    "tweepy>=4.14.0",
    "arq>=0.25.0",
    "apscheduler>=3.11.2",
    "python-dotenv>=1.0.0",
    "httpx>=0.26.0",
    "python-jose[cryptography]>=3.3.0",
    "sse-starlette>=1.6.5",
    "stripe>=7.0.0",
    "resend>=0.7.0",
    "slowapi>=0.1.9",
    "sentry-sdk[fastapi]>=2.0.0",
    "beautifulsoup4>=4.14.3",
    "bleach>=6.1.0",
    "itsdangerous>=2.1.0",
    "rich>=14.2.0",
]
```

---

## 4. Infrastructure & DevOps

### Hosting (All Free Tiers)
| Service | Purpose | Tier | Notes |
|---------|---------|------|-------|
| **Railway** | Backend (FastAPI + Arq worker) | Free (500h/mo) | Docker, port 8080, `railway.toml` |
| **Railway Redis** | Task queue + rate limiting | Free (native) | `redis.railway.internal:6379`, plain TCP |
| **Vercel** | Frontend (Next.js) | Hobby (free) | App Router, unlimited bandwidth |

### CI/CD
- **GitHub Actions** — `.github/workflows/ci-cd.yml`
  - `main` push → production (Security Scan → Tests → Migrate → Build → Deploy)
  - `develop` push → staging (same pipeline, staging env)
  - `RAILWAY_API_TOKEN` (account-level) + `--project` flag required

### Database Migrations
- **Alembic** — Python-managed, 25+ migrations
- **Never re-run** migration c006 (not idempotent)
- **Migration c008** (`purge_seed_data`) is irreversible — run staging first
- Current head: `c009`

### Package Managers
- **uv** (Python) — Blazing-fast, replaces pip/poetry: `uv sync`, `uv run`
- **npm** (Node.js) — Standard package management

### Linting / Quality
- **Ruff** — Python linter + formatter (replaces flake8 + black)
- **ESLint + Prettier** — TypeScript/React
- **pytest ≥7.4** with `pytest-asyncio` + `pytest-cov` — 291 tests, 85% coverage
- **Playwright** — 47 E2E tests, 5 browsers (Chrome, Firefox, Safari, Mobile Chrome, Mobile Safari)

---

## 5. Architecture: Three Core Loops

```
[Reddit / PH / Google Trends / HN / Twitter/X]
         ↓ PRAW, pytrends, Tweepy, Firecrawl/Crawl4AI
[Arq Worker + APScheduler] ──► [Railway Redis Queue]
         ↓ every 6h
[Supabase PostgreSQL: raw_signals table]
         ↓ unprocessed signals
[8 PydanticAI Agents] ──► [Gemini 2.0 Flash $0.10/M]
         ↓ structured insights
[Supabase PostgreSQL: insights table (69 tables total)]
         ↓ REST / SSE
[FastAPI: 232+ endpoints]
         ↓ JSON
[Next.js 16 App Router: 35+ routes]
```

**Loop 1 — Collection** (every 6h via APScheduler):
- 6 scrapers produce 150+ signals/day
- Raw signals stored with provenance (source, URL, timestamp)

**Loop 2 — Analysis** (after each collection):
- `analyze_signals_task` processes unprocessed signals in batches of 10
- Gemini 2.0 Flash produces 8-dimension scored insights
- Post-LLM validation: 300+ word minimum, SHA-256 deduplication

**Loop 3 — Presentation** (on-demand):
- FastAPI serves ranked insights, SSE streams live updates
- Next.js renders editorial UI with radar charts, evidence badges, trend sparklines

---

## 6. AI Agents (8 Agents)

| Agent | File | Task Function | Schedule |
|-------|------|--------------|----------|
| `enhanced_analyzer` | `enhanced_analyzer.py` | `analyze_signals_task` | Every 6h |
| `research` | `research_agent.py` | `fetch_daily_insight_task` | Daily 08:00 UTC |
| `competitive_intel` | `competitive_intel_agent.py` | — | Manual |
| `market_intel` | `market_intel_agent.py` | `market_insight_publisher_task` | Wed every 3 days |
| `content_generator` | `content_generator.py` | `run_content_pipeline_task` | Dynamic |
| `chat_agent` | `chat_agent.py` | — | On-demand (SSE) |
| `quality_reviewer` | `quality_reviewer.py` | `insight_quality_audit_task` | Dynamic |
| `market_insight_publisher` | `market_insight_publisher.py` | `market_insight_publisher_task` | Wed every 3 days |

All agents use `output_type=` (PydanticAI v1.x) and `result.output` (not `result.data`).
Model string: `"google-gla:gemini-2.0-flash"` (hardcoded, no `settings.llm_model`).

---

## 7. Environment Variables

### Backend (Railway production)
```bash
ENVIRONMENT=production
DATABASE_URL=postgresql+asyncpg://postgres.[REF]:[PASS]@aws-1-ap-southeast-2.pooler.supabase.com:5432/postgres
SUPABASE_URL=https://[REF].supabase.co
SUPABASE_ANON_KEY=eyJ...
SUPABASE_SERVICE_ROLE_KEY=eyJ...
GOOGLE_API_KEY=AIza...          # Gemini 2.0 Flash
REDIS_URL=redis://default:[PASS]@redis.railway.internal:6379  # Railway native
STRIPE_SECRET_KEY=sk_live_...
STRIPE_WEBHOOK_SECRET=whsec_...
RESEND_API_KEY=re_...
SENTRY_DSN=https://...@ingest.us.sentry.io/...
CORS_ORIGINS=https://start-insight-ascentias-projects.vercel.app,...
PORT=8080
DB_SSL=true
USE_CRAWL4AI=true               # Free scraping alternative
```

### Frontend (Vercel production)
```bash
NEXT_PUBLIC_API_URL=https://backend-production-e845.up.railway.app
NEXT_PUBLIC_SUPABASE_URL=https://[REF].supabase.co
NEXT_PUBLIC_SUPABASE_ANON_KEY=eyJ...
NEXT_PUBLIC_ENVIRONMENT=production
NEXT_PUBLIC_SENTRY_DSN=https://...
SENTRY_DSN=https://...
SENTRY_ORG=ascentia-km
SENTRY_PROJECT=frontend
SENTRY_AUTH_TOKEN=sntrys_...
```

**Key rule:** `NEXT_PUBLIC_*` vars are baked at build time — changing them in Vercel requires a redeploy.

---

## 8. Sentry Observability Configuration

### Backend (`backend/app/main.py`)
```python
sentry_sdk.init(
    dsn=settings.sentry_dsn,
    environment=settings.environment,          # "production" or "staging"
    release=os.environ.get("RAILWAY_GIT_COMMIT_SHA", "local"),
    traces_sample_rate=settings.sentry_traces_sample_rate,  # 0.1 prod, 1.0 staging
    enable_logs=True,
    integrations=[
        FastApiIntegration(transaction_style="url"),
        SqlalchemyIntegration(),
        LoggingIntegration(
            level=logging.INFO,
            event_level=logging.ERROR,
            sentry_logs_level=logging.WARNING,
        ),
    ],
    before_send=lambda event, hint:
        None if event.get("request", {}).get("url", "").endswith("/health") else event,
)
```

### Frontend (`frontend/sentry.client.config.ts`)
```typescript
Sentry.init({
  dsn: process.env.NEXT_PUBLIC_SENTRY_DSN,
  environment: process.env.NEXT_PUBLIC_ENVIRONMENT,
  enableLogs: true,
  integrations: [
    Sentry.browserTracingIntegration(),
    Sentry.replayIntegration({ maskAllText: true, blockAllMedia: true }),
    Sentry.consoleLoggingIntegration({ levels: ["warn", "error"] }),
  ],
});
```

---

## 9. Security Stack

| Layer | Implementation | Library |
|-------|---------------|---------|
| HTTP Security Headers | HSTS + CSP + X-Frame-Options | Custom `SecurityMiddleware` |
| JWT Authentication | ES256 via Supabase JWKS endpoint | `python-jose[cryptography]` |
| Input Sanitization | XSS prevention on all user inputs | `bleach` |
| Rate Limiting | Tier-based sliding window (in-memory for non-prod) | `slowapi` |
| Password Recovery | `/auth/update-password` with Supabase recovery token | Supabase Auth |
| RBAC | 4 roles: superadmin, admin, member, viewer | `deps.py` |

---

## 10. Decision Log

| Decision | Choice | Reason |
|----------|--------|--------|
| LLM primary | Gemini 2.0 Flash | 97% cheaper than Claude, 1M context |
| LLM framework | PydanticAI v1.x | Type-safe, native async, no LangChain complexity |
| Task queue | Arq + Redis | Lighter than Celery, async-native |
| Redis provider | Railway native | Free, same private network, no TLS needed |
| Database | Supabase Pro | $25/mo, built-in auth, RLS, APAC region |
| Scraping primary | PRAW + pytrends + Tweepy | Free APIs, no per-call costs |
| Scraping supplement | Crawl4AI (self-hosted) | Free Firecrawl alternative (`USE_CRAWL4AI=true`) |
| Auth | Supabase JWT (ES256) | No shared secret needed, JWKS endpoint |
| Frontend hosting | Vercel Hobby | Free, global CDN, Next.js-native |
| Backend hosting | Railway Free | Docker, 500h/mo, Redis built-in |
| Email | Resend Free | 3K/mo covers MVP, no monthly fee |
| Payments | Stripe | No monthly fee, industry standard |
