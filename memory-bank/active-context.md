---
**Memory Bank Protocol**
**Reading Priority:** CRITICAL
**Read When:** Before every task to understand current phase status
**Dependencies:** Read project-brief.md first for context
**Purpose:** Current phase tracking, immediate tasks, blockers, what's working/next
**Last Updated:** 2026-02-19
---

# Active Context: StartInsight Development

## Current Phase
**Status:** ✅ LIVE IN PRODUCTION — Post-launch monitoring & content seeding
**Completed:** Phase 1-10 + A-L + Q1-Q9 + Security + Sentry + Redis (100%)
**Testing:** 291 backend tests passing, 47 E2E tests (5 browsers)
**Database:** 69 tables, 232+ API endpoints, 8 AI agents, 6 active scrapers

## Infrastructure (2026-02-19)

| Service | Provider | URL / Details |
|---------|----------|---------------|
| **Frontend** | Vercel | `https://start-insight-ascentias-projects.vercel.app` ✅ |
| **Backend** | Railway | `https://backend-production-e845.up.railway.app` ✅ |
| **Database** | Supabase Pro | Sydney ap-southeast-2, c009 migration, session-mode pooler |
| **Redis** | Railway (native) | `redis.railway.internal:6379`, provisioned 2026-02-19 ✅ |
| **Email** | Resend | Live mode, 3K/mo free tier |
| **Payments** | Stripe | Live mode, 3 products / 6 prices (monthly + yearly) |
| **Monitoring** | Sentry | Org: `ascentia-km`, backend + frontend projects |

**Staging:**
- Frontend: `https://start-insight-staging-ascentias-projects.vercel.app`
- Backend: `https://backend-staging-fbd7.up.railway.app`
- Database: Supabase branch `jsprkxymvuwoqoqkromr` (session-mode pooler only)

**CI/CD:** Push to `main` → production; push to `develop` → staging
Pipeline: Security Scan → Tests → Migrate → Build Docker → Deploy
GitHub Actions: `ci-cd.yml` + `set-vercel-sentry-env.yml`
Railway Project ID: `a3ece066-4758-4780-84d6-0379f1312227`

**Monthly Cost:** ~$30/mo (Supabase Pro $25 + Gemini ~$5; Railway/Vercel/Redis on free tiers)

## Sentry Configuration

| Item | Value |
|------|-------|
| Org | `ascentia-km` |
| Backend | FastAPI + SQLAlchemy + LoggingIntegration + `enable_logs=True` + AI spans |
| Frontend | Next.js App Router + browserTracingIntegration + consoleLoggingIntegration + Session Replay |
| AI Monitoring | Manual `gen_ai.request` spans on enhanced_analyzer, research_agent, market_intel_agent |
| Sample Rates | Production: 10% traces/profiles; Staging: 100% |
| Env Vars | Backend via Railway MCP; Frontend via GitHub Actions `set-vercel-sentry-env.yml` |

## Recent Work (2026-02-20)

1. ✅ **QA P0/P1/P2 bug fixes** — 11 bugs fixed: /terms + /privacy pages (404→200), payments CORS fix, email prefs 404, Deep Research link, `$$` double-dollar, contact domain/duplicate-select, Enterprise billing tier, Google OAuth on signup, context-aware CTAs, skeleton loaders
2. ✅ **Gemini 429 fix** — `quality_reviewer.py` now uses `tenacity` retry (4 attempts, 5s→10s→20s→40s backoff) + `asyncio.sleep(2)` inter-call delay for both insight audit + market article review loops; `tenacity>=8.2.0` added to `pyproject.toml`

## Recent Work (2026-02-19)

1. ✅ **Redis provisioned** — Railway native Redis service (`redis.railway.internal:6379`), `REDIS_URL` set on backend
2. ✅ **Scheduler SSL fix** — `scheduler.py` `_get_redis_settings()` now has `ssl=` parameter matching `worker.py`
3. ✅ **Scheduler task_map expanded** — 5 missing agent mappings added (`daily_insight_agent`, `success_stories_agent`, `market_insight_publisher`, `insight_quality_reviewer`, `market_insight_quality_reviewer`)
4. ✅ **Sentry verified** — Redis error gone; scheduler running cleanly; `localhost:6379` error cleared
5. ✅ **Sentry full coverage** — backend (FastAPI + SQLAlchemy + AI spans) + frontend (Next.js + replay + tracing)
6. ✅ **Security hardened** — HSTS, CSP, XSS prevention, JWT ES256, rate limiting, update-password flow
7. ✅ **Production deployed** — Railway backend + Vercel frontend, all healthy
8. ✅ **CI/CD pipeline** — `main`→production, `develop`→staging, all passing

## Background Jobs (Scheduler) — Now Running

All arq tasks now scheduled and running via APScheduler + Railway Redis:

| Agent | Task Function | Schedule |
|-------|--------------|----------|
| `enhanced_analyzer` | `analyze_signals_task` | Every 6h |
| `daily_insight_agent` | `fetch_daily_insight_task` | Daily 08:00 UTC |
| `success_stories_agent` | `update_success_stories_task` | Weekly Sunday |
| `market_insight_publisher` | `market_insight_publisher_task` | Every 3 days (Wed) |
| `insight_quality_reviewer` | `insight_quality_audit_task` | Dynamic (DB config) |
| `market_insight_quality_reviewer` | `market_insight_quality_review_task` | Dynamic (DB config) |
| Scrapers | `scrape_reddit/product_hunt/trends/twitter/hackernews_task` | Every 6h |
| Weekly digest | `send_weekly_digest_task` | Monday 09:00 UTC |

## Current Focus: Post-Launch Operations

**Priority 1 — Content Seeding (Immediate)**
- Seed 50+ insights across 10+ categories via admin portal
- Verify scraper pipeline health in admin → Pipeline Monitoring
- Check content review queue for pending approvals

**Priority 2 — Monitoring (Weekly)**
- Review Sentry for new production errors
- Monitor Stripe webhook health (checkout, subscription events)
- Check Railway metrics (CPU, memory, response times)

**Priority 3 — Growth (Next 2-4 weeks)**
- Submit sitemap to Google Search Console
- Set up UptimeRobot / Checkly uptime monitoring
- Create initial batch of marketing content
- Launch to waitlist/ProductHunt

## Key File Locations

| What | Where |
|------|-------|
| Backend entry | `backend/app/main.py` |
| Arq worker | `backend/app/worker.py` |
| Scheduler | `backend/app/tasks/scheduler.py` |
| Auth deps | `backend/app/api/deps.py` |
| Sentry config | `backend/app/main.py:25-43`, `frontend/sentry.*.config.ts` |
| AI agents | `backend/app/agents/` (8 agents) |
| Frontend pages | `frontend/app/[locale]/` |
| CI/CD | `.github/workflows/ci-cd.yml` |
| Production plan | `memory-bank/production-plan.md` |

## Architecture in One Paragraph

6 scrapers → arq tasks → Railway Redis queue → Supabase PostgreSQL → 8 AI agents (Gemini 2.0 Flash) → 232+ FastAPI endpoints → Next.js App Router. Auth via Supabase JWT (ES256). Payments via Stripe. Email via Resend. Errors/traces via Sentry. All infra on Railway (backend + Redis) + Vercel (frontend) + Supabase Pro (DB). CI/CD via GitHub Actions.

## Testing

- **Backend:** `cd backend && pytest tests/ -v --cov=app` (291 tests, 85% coverage)
- **Frontend:** `cd frontend && npx playwright test` (47 E2E, 5 browsers)
- **Lint:** `cd backend && uv run ruff check . --fix`

---

**Last Updated:** 2026-02-20
**Status:** LIVE IN PRODUCTION — All planned phases complete. Scheduler running. 11 QA bugs fixed. Gemini 429 retry added. Content seeding next.
