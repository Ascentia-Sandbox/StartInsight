---
**Memory Bank Protocol**
**Reading Priority:** CRITICAL
**Read When:** Before every task to understand current phase status
**Dependencies:** Read project-brief.md first for context
**Purpose:** Current phase tracking, immediate tasks, blockers, what's working/next
**Last Updated:** 2026-02-25
---

# Active Context: StartInsight Development

## Current Phase
**Status:** ✅ LIVE IN PRODUCTION — Post-launch: content growth & SEO
**Completed:** Phase 1-10 + A-L + Q1-Q9 + Security + Sentry + Redis + Domain + Favicon (100%)
**Testing:** 291 backend tests passing, 47 E2E tests (5 browsers)
**Database:** 69 tables, 232+ API endpoints, 8 AI agents, 6 active scrapers

## Infrastructure (2026-02-22)

| Service | Provider | URL / Details |
|---------|----------|---------------|
| **Frontend** | Vercel | `https://startinsight.co` ✅ |
| **Backend** | Railway | `https://api.startinsight.co` ✅ |
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

## Recent Work (2026-02-25)

1. ✅ **37 Sentry issues resolved** — backend 422 errors, chat route fixes, research pre-fill from `insight_id` query param
2. ✅ **Chat agent refactor** — `chat_agent.py` prompts improved; `insights/[slug]/chat/page.tsx` updated
3. ✅ **Admin agents page rewrite** — `admin/agents/page.tsx` fully rewritten with improved UX
4. ✅ **Trends backfill script** — `backend/scripts/backfill_trends_table.py` added; `trends/[id]/page.tsx` redesigned
5. ✅ **Memory-bank cleanup** — `improvement-plan.md` and `producthunt-launch.md` deleted (content captured in active-context Tier 1-3 table); all 6 remaining files updated to 2026-02-25

## Recent Work (2026-02-22)

1. ✅ **Domain sweep** — All 19× `startinsight.app` → `startinsight.co` across 11 files; `api.startinsight.ai` → `api.startinsight.co` in developers page (critical)
2. ✅ **Professional favicon system** — `icon.svg` (teal chart-bars, 32×32), `apple-icon.tsx` (180×180 ImageResponse), `opengraph-image.tsx` (1200×630 branded gradient); `metadata.icons` added to `layout.tsx`
3. ✅ **CI/CD VERCEL_TOKEN fix** — Production deploy step reverted to `VERCEL_TOKEN_STAGING` (no separate `VERCEL_TOKEN` secret exists; `--prod` flag controls env, not token name)
4. ✅ **Scraper pipeline fixed** — Crawl4AI 30s timeout added; duplicate APScheduler/Arq scheduling removed
5. ✅ **Uptime monitoring** — GitHub Actions every-5-min workflow; auto-creates/closes GitHub issues on failures
6. ✅ **SEO improvements** — JSON-LD Organization schema, Google verification meta, improved sitemap changeFrequency/priority
7. ✅ **Content seeding CLI** — `backend/scripts/seed_content.py` with status/scrape/analyze/pipeline/approve commands
8. ✅ **PostHog + Sentry release** — `PostHogProvider`, typed `analytics.ts`, `VERCEL_GIT_COMMIT_SHA` for release tracking
9. ✅ **Onboarding banner** — 3-step stepper on dashboard, shows only for new users, localStorage dismiss
10. ✅ **Redis caching** — 3 public endpoints cached (insights 60s, trends 300s, pulse 30s)
11. ✅ **E2E expansion** — 18 new tests: auth-flows, workspace, validate suites
12. ✅ **API docs page** — `/api-docs` branded page with sidebar; Swagger always-on; nav link added
13. ✅ **Referral program** — c011 migration; `GET /api/referrals/stats`; settings share widget; `?ref=` localStorage tracking
14. ✅ **Email tracking** — Open-rate pixel endpoint; UTM params on all digest links; plain-text fallback; admin digest test endpoint

## Recent Work (2026-02-21)

1. ✅ **Google Trends rate-limit hardening** — 30s batch delay, 10s request interval, 4×/day at :30 past 0/6/12/18h
2. ✅ **UX Round 2** — compare page, data formatting, teal brand, success-stories `formatFunding` fix
3. ✅ **`startinsight.co` domain live** — Vercel + Railway + Cloudflare DNS + Supabase + CORS end-to-end

## Recent Work (2026-02-20)

1. ✅ **API validator + research fixes** — `validator.py`: removed invalid `title=` kwarg; `research.py:536`: `Query(regex=)` → `Query(pattern=)`
2. ✅ **QA P0/P1/P2 bug fixes** — 11 bugs fixed: /terms + /privacy 404s, payments CORS, email prefs, Deep Research link, contact domain, Enterprise billing, Google OAuth, skeleton loaders
3. ✅ **Gemini 429 fix** — `quality_reviewer.py` tenacity retry (4 attempts, exponential backoff) + inter-call sleep

## Background Jobs (Scheduler) — All Running

All arq tasks now scheduled and running via APScheduler + Railway Redis:

| Agent | Task Function | Schedule |
|-------|--------------|----------|
| `enhanced_analyzer` | `analyze_signals_task` | Every 6h |
| `daily_insight_agent` | `fetch_daily_insight_task` | Daily 08:00 UTC |
| `success_stories_agent` | `update_success_stories_task` | Weekly Sunday |
| `market_insight_publisher` | `market_insight_publisher_task` | Every 3 days (Wed) |
| `insight_quality_reviewer` | `insight_quality_audit_task` | Dynamic (DB config) |
| `market_insight_quality_reviewer` | `market_insight_quality_review_task` | Dynamic (DB config) |
| Scrapers | `scrape_reddit/product_hunt/trends/twitter/hackernews_task` | Every 6h (Arq cron) |
| Weekly digest | `send_weekly_digest_task` | Monday 09:00 UTC |

## Current Focus: Post-Launch Growth

**Tier 1 — COMPLETE ✅**
1. ✅ Fix scraper pipeline — DONE (2026-02-22)
2. ✅ Uptime monitoring — GitHub Actions workflow `.github/workflows/uptime-check.yml` (every 5m)
3. ✅ Google Search Console SEO — sitemap improvements, JSON-LD, verification meta
4. ✅ Content seeding CLI — `backend/scripts/seed_content.py` (75 unprocessed signals found)

**Tier 2 — COMPLETE ✅**
5. ✅ PostHog analytics + Sentry release tracking — `PostHogProvider.tsx`, `analytics.ts`, `VERCEL_GIT_COMMIT_SHA`
6. ✅ Onboarding banner — `onboarding-banner.tsx` (3-step stepper, localStorage dismiss)
7. ✅ Redis API caching — 60s insights, 300s trends, 30s pulse
8. ✅ E2E tests expanded — `auth-flows.spec.ts`, `workspace.spec.ts`, `validate.spec.ts` (18 new tests)
9. ✅ ProductHunt launch plan — `memory-bank/producthunt-launch.md`

**Tier 3 — COMPLETE ✅**
10. ✅ Public API docs page — `/api-docs` branded page, Swagger always-on, nav link
11. ✅ Referral program — c011 migration, `GET /api/referrals/stats`, share widget in settings
12. ✅ Email digest validation + open-rate tracking — tracking pixel, UTM params, plain-text fallback

**Pending (requires manual action):**
- Set `NEXT_PUBLIC_POSTHOG_KEY` in Vercel dashboard to activate PostHog analytics
- Submit `https://startinsight.co/sitemap.xml` to Google Search Console
- Seed content to 600+ insights before ProductHunt launch (currently 522; pipeline running every 6h)

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
| Favicon | `frontend/app/icon.svg`, `frontend/app/apple-icon.tsx`, `frontend/app/opengraph-image.tsx` |

## Architecture in One Paragraph

6 scrapers → arq tasks (cron, not APScheduler) → Railway Redis queue → Supabase PostgreSQL → 8 AI agents (Gemini 2.0 Flash) → 232+ FastAPI endpoints → Next.js App Router. Auth via Supabase JWT (ES256). Payments via Stripe. Email via Resend. Errors/traces via Sentry. All infra on Railway (backend + Redis) + Vercel (frontend) + Supabase Pro (DB). CI/CD via GitHub Actions.

## Testing

- **Backend:** `cd backend && pytest tests/ -v --cov=app` (291 tests, 85% coverage)
- **Frontend:** `cd frontend && npx playwright test` (47 E2E, 5 browsers)
- **Lint:** `cd backend && uv run ruff check . --fix`

---

**Last Updated:** 2026-02-22
**Status:** LIVE IN PRODUCTION — All Tier 1/2/3 improvement tasks complete. 249 backend tests passing. Migration c011 pending on production. Awaiting PostHog key + Google Search Console verification + content seeding to 600+ insights for ProductHunt launch.
