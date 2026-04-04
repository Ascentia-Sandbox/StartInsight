---
**Memory Bank Protocol**
**Reading Priority:** CRITICAL
**Read When:** Before every task to understand current phase status
**Dependencies:** Read project-brief.md first for context
**Purpose:** Current phase tracking, immediate tasks, blockers, what's working/next
**Last Updated:** 2026-04-04
---

# Active Context: StartInsight Development

## Current Phase
**Status:** ✅ LIVE IN PRODUCTION — GTM Phase 1 complete, Phase 2 next
**Completed:** Phase 1-10 + A-L + Q1-Q9 + Security + Sentry + Redis + Domain + Favicon + Phase 6 + GTM Phase 1
**Testing:** 454 backend tests passing (47% coverage), 47 E2E tests (5 browsers)
**Database:** 70 tables, 235+ API endpoints, 8 AI agents, 6 active scrapers
**Revenue:** $0 — demand experiment in progress

## Current Focus: Automated GTM System (2026-04-04)

**Full plan:** `memory-bank/gtm-automation-plan.md` (600+ lines, 4 phases)

### GTM Phase 1: Fix & Instrument (COMPLETE ✅ — 2026-04-04)
- ✅ Category reports linked in mega-menu, footer, sitemap (3 URLs)
- ✅ PostHog events: report_category_viewed, report_checkout_started, report_checkout_error
- ✅ TIER_COMPAT_MAP removed (was deadline 2026-04-23)
- ✅ ENABLE_DAILY_DIGEST=true set in Railway (deployed)
- ✅ Google Search Console verification meta tag added
- ⏳ Pending: GSC verification + sitemap submission (after deploy)

### GTM Phase 2: Automated Content Distribution (COMPLETE ✅ — 2026-04-04)
- ✅ Marketing module: `backend/app/marketing/` (modular monolith pattern)
- ✅ SocialPost model + migration c018 (social_posts table + nurture_stage column)
- ✅ Twitter posting service (Tweepy v2 Client, OAuth 1.0a)
- ✅ LinkedIn posting service (Marketing API + Make.com webhook fallback)
- ✅ Social posting agent (reads pending posts, rate limits 3 tweets + 2 LinkedIn/day)
- ✅ Content generator wired to social_posts table (auto-creates pending posts)
- ✅ Email nurture sequence: Day 1/3/7/14 templates + daily scheduler task
- ✅ Config: enable_social_posting flag, LinkedIn creds, daily post limits
- ✅ Registered in worker.py: post_social_content_task (10am/4pm UTC), run_email_nurture_task (10am UTC)
- ⏳ Pending (config): set ENABLE_SOCIAL_POSTING=true + Twitter/LinkedIn creds in Railway

### GTM Phase 3: Programmatic SEO (Week 4-6)
- Auto-generate /explore/[category] landing pages
- RSS feed for insights
- Internal linking system

### GTM Phase 4: Community & API (Week 6-8)
- ProductHunt launch
- Developer API activation + embeddable widget
- Referral incentive tiers

## Phase 6: Data Pipeline Resilience & Intelligence (COMPLETE ✅ — 2026-03-20)

**Delivered:**
- **6.1** Per-scraper circuit breakers, stale-on-error cache fallback, negative caching
- **6.2** Source health registry (`source_health` table), GET /health/sources, intelligence gap dashboard
- **6.3** L1 in-memory cache (cachetools TTLCache), bootstrap cache hydration
- **6.4** Welford anomaly detection, cross-source TF-IDF correlation (union-find grouping), keyword spike detection
- **6.5** AI fallback chain (Gemini → Claude → rule-based), source credibility weighting, Redis dedup locks

**New tables:** `source_health` (15 columns). **New columns on `insights`:** `correlation_group_id`, `correlation_score`, `source_count`.
**New endpoints:** GET /health/sources, GET /api/insights/correlated, GET /api/admin/intelligence-gaps.
**Migrations:** c012 (source_health), c013 (correlation columns).
**Key patterns:** Adapted from World Monitor (41K-star geopolitical intelligence platform).

## Infrastructure (2026-02-22)

| Service | Provider | URL / Details |
|---------|----------|---------------|
| **Frontend** | Vercel | `https://startinsight.co` ✅ |
| **Backend** | Railway | `https://api.startinsight.co` ✅ |
| **Database** | Supabase Pro | Sydney ap-southeast-2, c016 migration head, session-mode pooler |
| **Redis** | Railway (native) | `redis.railway.internal:6379`, provisioned 2026-02-19 ✅ |
| **Email** | Resend | Live mode, 3K/mo free tier |
| **Payments** | Stripe | Live mode, 3 products / 6 prices (monthly + yearly) |
| **Monitoring** | Sentry | Org: `ascentia-km`, backend + frontend projects |

**Staging:**
- Frontend: `https://start-insight-staging-ascentias-projects.vercel.app`
- Backend: `https://backend-staging-fbd7.up.railway.app`
- Database: Supabase branch `jsprkxymvuwoqoqkromr` (session-mode pooler only)

**CI/CD:** Push to `main` → production; push to `develop` → staging
Pipeline: Security Scan → Tests (split: fast + integration) → Migrate → Build → Deploy
Coverage gate: 35% enforced (`--cov-fail-under=35`), flaky test reruns (`--reruns 2`), PR coverage comments
GitHub Actions: `ci-cd.yml` + `set-vercel-sentry-env.yml` + `sentry-daily-triage.yml` + `sentry-autofix.yml`
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

## Recent Work (2026-03-20)

1. ✅ **Test suite expansion** — 398 backend tests (was 307), 47% coverage (was 17%). 8 new test files: cache (25), circuit breaker (12), base scraper (14), health routes (16), insights routes (10), enhanced analyzer (10), scraper pipeline (10), analysis pipeline (6). Phase 6 services (16).
2. ✅ **CI/CD hardening** — Split tests into fast (unit, no services) + integration (Postgres/Redis) parallel jobs. Added: uv cache, ruff format check, 35% coverage gate, `pytest-rerunfailures` (--reruns 2), PR coverage comments via orgoro/coverage.
3. ✅ **Sentry automation** — Daily triage workflow (Mon-Fri 9am UTC, creates GitHub issue with unresolved errors). Auto-fix workflow for 4 known patterns (ConnectionDoesNotExist, MaxClients, Gemini 429, analyzer timeout). Sentry issue template.
4. ✅ **CI/CD credential fix** — Production Vercel deploy was using `VERCEL_TOKEN_STAGING` / `VERCEL_PROJECT_ID_STAGING`; fixed to `VERCEL_TOKEN` / `VERCEL_PROJECT_ID`.

## Recent Work (2026-03-05)

1. ✅ **Frontend performance optimizations** — Home page SSR/ISR (revalidate:300); framer-motion (219KB) lazy via dynamic import; Satoshi font preloaded; Instrument Serif `display:optional`; ReactQueryDevtools prod-excluded; `optimizePackageImports` for lucide-react/recharts/@radix-ui. Staging Lighthouse: TBT 340ms→140ms; expected 85-90+ on production.
2. ✅ **Codebase cleanup** — Deleted stale root `app/validate/` (locale-unaware duplicate); deleted orphaned `trend-sparkline-lazy.tsx`; moved 16 root-level screenshots → `docs/screenshots/`; deleted stale `docs/memory-bank-readme-cleanup-2026-02-25` branch.

**Pending (from 2026-03-05):**
- Vercel Lighthouse staging score ~72 (Slow 4G simulation); production expected 85-90+ (ISR warm cache)
- SEO score 63 on staging (Vercel preview adds `noindex`) → production = 100

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
5. ✅ **Uptime monitoring** — UptimeRobot (free, 5-min interval); GitHub Actions schedule cron disabled
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
- ~~Set `NEXT_PUBLIC_POSTHOG_KEY` in Vercel dashboard~~ ✅ Done 2026-03-24 — `NEXT_PUBLIC_POSTHOG_KEY` + `NEXT_PUBLIC_POSTHOG_HOST=https://us.i.posthog.com` set for all environments
- Submit `https://startinsight.co/sitemap.xml` to Google Search Console (deferred — no deadline)
- Seed content to 600+ insights before ProductHunt launch (pipeline running every 6h; was 522 as of 2026-03-20)

## Recent Work (2026-03-24)

**Sprint: PLG Freemium + Stripe Compat + PostHog (6 items)**

1. ✅ **PostHog env vars** — `NEXT_PUBLIC_POSTHOG_KEY` + `NEXT_PUBLIC_POSTHOG_HOST` set in Vercel for all environments. Analytics events now live.
2. ✅ **TypeScript build fix** — 3 files blocked production builds (TS7006/TS7031/strict cast errors). Fixed `PostHogProvider.tsx`, `analytics.ts`, `useSubscription.ts`. Production restored at commit `c9b4625`.
3. ✅ **PLG: Gradient fade paywall** — `FeatureLock.tsx`: replaced `blur-sm opacity-50` with CSS gradient fade (transparent→bg at 88%) + bottom-anchored upgrade CTA. Editorial aesthetic, no hard blur.
4. ✅ **Stripe webhook compat** — `TIER_COMPAT_MAP` (starter→pro, enterprise→api) already present. Added tier sync to `_handle_subscription_updated` so canceled/unpaid/active status changes propagate to `user.subscription_tier`. Remove `TIER_COMPAT_MAP` by 2026-04-23.
5. ✅ **Newsletter merge-on-signup** — Migration c016 adds `user_id` FK to `newsletter_subscribers`. `_verify_and_get_user` links subscriber record after JIT user upsert.
6. ✅ **PDPA consent** — Explicit consent statement + Privacy Policy link added to `NewsletterForm.tsx`. All 5 PDPA sections (13–17) already present.
7. ✅ **DESIGN.md committed** — 234-line design system reference (oklch tokens, typography, spacing, component patterns, dark mode strategy). Closes TODOS.md P2 item.

**New migrations this sprint:** c014 (free_reports_used on users), c015 (newsletter_subscribers table), c016 (user_id FK)

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

6 scrapers → arq tasks (cron, not APScheduler) → Railway Redis queue → Supabase PostgreSQL → 8 AI agents (Gemini 2.0 Flash) → 235+ FastAPI endpoints → Next.js App Router. Auth via Supabase JWT (ES256). Payments via Stripe. Email via Resend. Errors/traces via Sentry. All infra on Railway (backend + Redis) + Vercel (frontend) + Supabase Pro (DB). CI/CD via GitHub Actions.

## Testing

- **Backend:** `cd backend && pytest tests/ -v --cov=app` (398 tests, 47% coverage)
- **Frontend:** `cd frontend && npx playwright test` (47 E2E, 5 browsers)
- **Lint:** `cd backend && uv run ruff check . --fix`

---

**Last Updated:** 2026-03-25
**Status:** LIVE IN PRODUCTION — All Tier 1/2/3 improvement tasks complete. 398 backend tests passing (47% coverage). Migrations c001–c016 applied. PostHog live. Sitemap submission + content seeding to 600+ insights for ProductHunt launch pending.
