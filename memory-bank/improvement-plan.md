# StartInsight — Professional Improvement Plan

**Date:** 2026-02-22
**Status:** Production Live — All Phases 1-10 + A-L + Q1-Q9 + Security + Sentry + Redis complete
**Live URL:** https://startinsight.co

---

## Executive Summary

StartInsight is technically complete and production-stable. All 338 tests pass, 8 AI agents run on schedule, 235+ API endpoints are operational, and full Sentry monitoring is in place. The product competes on price (54–70% cheaper than IdeaBrowser), feature depth (8-dimension scoring vs 4, real-time SSE, public API), and latency (50ms APAC vs 180ms).

**The remaining gaps are not technical — they are growth, retention, and content gaps.** This plan addresses them in priority order.

---

## Current Baselines (Updated 2026-02-22)

| Metric | Value |
|--------|-------|
| Total insights in DB | ~399 |
| Daily new insights | Recovering (scraper pipeline fixed 2026-02-22) |
| Pulse signals (24h) | Recovering — Crawl4AI timeout + duplicate scheduling fixed |
| Organic search traffic | ~0 (not yet indexed) |
| Uptime monitoring | None |
| User analytics | None |
| E2E test coverage | Phase 1–3 only (47/~85 critical flows) |
| Paying subscribers | Unknown |

---

## Tier 1 — Immediate (This Week)

> These unlock the product's ability to grow and are blocking or near-blocking.

### 1.1 Fix the Scraper Pipeline ✓ FIXED (2026-02-22)

**Root cause:** Two bugs found and fixed:
1. `AsyncWebCrawler.arun()` in `crawl4ai_client.py` had no timeout → hung indefinitely, killed by Arq's 600s job timeout
2. `scrape_all_sources_task` + `analyze_signals_task` were scheduled by BOTH Arq `cron_jobs` AND APScheduler → competing double-runs

**Fix applied:** `asyncio.wait_for(..., timeout=30.0)` in crawl4ai_client.py; removed duplicate APScheduler entries.

**Files:** `backend/app/scrapers/crawl4ai_client.py`, `backend/app/scheduler.py`

---

### 1.2 Uptime Monitoring

**Problem:** No external monitoring. A Railway restart or Supabase connection issue could go undetected for hours.

**Fix:** Configure UptimeRobot (free) or Checkly:
- Endpoint: `GET https://backend-production-e845.up.railway.app/health` every 60 seconds
- Alert: Email on 2 consecutive failures
- SLA target: 99.5% (< 4 hours downtime/month)

**Effort:** ~15 minutes. No code changes.

---

### 1.3 Google Search Console + Sitemap Submission

**Problem:** Zero organic search traffic. The dynamic sitemap exists but has never been submitted.

**Steps:**
1. Add Google site verification `<meta>` tag to `frontend/app/layout.tsx`
2. Submit `https://start-insight-ascentias-projects.vercel.app/sitemap.xml` to Google Search Console
3. Submit to Bing Webmaster Tools
4. Request indexing for: `/`, `/insights`, `/pricing`, `/trends`, `/founder-fits`, `/validate`

**Files:** `frontend/app/layout.tsx`

---

### 1.4 Content Seeding via Admin Portal

**Problem:** Launch impact requires 50+ quality insights across 10+ categories. Current content may be sparse or unreviewed.

**Actions (no code required):**
1. Review `content_review_queue` in admin portal — approve/reject queued insights
2. Trigger `market_insight_publisher` agent for 5+ blog posts via admin agent control
3. Verify success stories count (6 showing live, target 12)
4. Confirm trends database has 175+ verified keywords

---

## Tier 2 — Short-Term (Month 1)

### 2.1 User Analytics — PostHog

**Problem:** No visibility into user behaviour — which pages convert, where users drop off, which features drive upgrades.

**Implementation:**
- Add PostHog JS SDK to `frontend/app/layout.tsx`
- Track key events: `insight_viewed`, `insight_saved`, `comparison_started`, `validate_submitted`, `upgrade_clicked`
- Set up conversion funnel: Landing → Signup → First Save → Upgrade
- Cost: Free up to 1M events/month

**Files:** `frontend/app/layout.tsx`, `frontend/lib/analytics.ts` (new helper)

---

### 2.2 New User Onboarding Banner

**Problem:** New users land on a dashboard showing `0/0/0/free`. There is no guided first action, which kills Day 1 retention.

**Fix:** First-time onboarding banner triggered when `insights_saved === 0`:
- Content: Step 1 → Browse Ideas, Step 2 → Save an Insight, Step 3 → Validate Your Idea
- Dismiss: stored in `localStorage` (no DB migration)
- Placement: top of dashboard, dismissible

**Files:**
- `frontend/app/[locale]/dashboard/page.tsx`
- `frontend/components/onboarding-banner.tsx` (new)

---

### 2.3 E2E Test Coverage Expansion

**Problem:** 47 E2E tests cover Phase 1–3 only. Auth, payments, admin, community, and gamification flows (~38 tests) are completely untested.

**Priority suites to add:**

| Suite | Tests | Priority |
|-------|-------|----------|
| Auth (signup, login, logout, reset) | 8 | High |
| Workspace (save, rate, claim insight) | 6 | High |
| Validate page (quota, submission) | 4 | High |
| Payment (Stripe checkout, portal) | 6 | Medium |
| Admin panel (smoke test) | 6 | Medium |
| Community (vote, comment) | 5 | Low |
| Gamification (achievement display) | 3 | Low |

**Files:** `frontend/tests/` — new `.spec.ts` per suite

---

### 2.4 Redis API Response Caching

**Problem:** High-traffic list endpoints (`/api/insights`, `/api/trends`, `/api/pulse`) run full DB queries on every request. With growing traffic this will hit Supabase connection limits.

**Implementation:**
- Cache `GET /api/insights` list for 60 seconds
- Cache `GET /api/trends` for 300 seconds
- Cache `GET /api/pulse` for 30 seconds
- Use existing Railway Redis (`redis.railway.internal:6379`)
- Cache invalidation: on admin content approval or manual trigger

**Files:**
- `backend/app/core/cache.py` (new — thin wrapper around `aioredis`)
- `backend/app/api/routes/insights.py`
- `backend/app/api/routes/trends.py`
- `backend/app/api/routes/pulse.py`

---

### 2.5 Frontend Sentry Release Tracking

**Problem:** Backend uses `RAILWAY_GIT_COMMIT_SHA` for release tracking, but frontend Sentry does not emit release tags. Errors can't be attributed to specific deploys.

**Implementation:**
- Pass `VERCEL_GIT_COMMIT_SHA` as `NEXT_PUBLIC_SENTRY_RELEASE` in Vercel env vars
- Update `sentry.client.config.ts` to use `process.env.NEXT_PUBLIC_SENTRY_RELEASE` as the release identifier

**Files:** `frontend/sentry.client.config.ts`, Vercel project settings

---

### 2.6 ProductHunt Launch

**Problem:** The product is launch-ready but no launch has been executed. A ProductHunt launch can drive 500–2,000 visitors in a single day.

**Pre-launch checklist:**
- [ ] Create ProductHunt maker account for founder
- [ ] Write tagline: *"AI finds startup ideas before the market catches on"*
- [ ] Prepare 5 product screenshots (dashboard, insights, comparison, pulse, validate)
- [ ] Record 60-second demo video
- [ ] Schedule for Tuesday or Wednesday (peak upvote days)
- [ ] Secure 20+ upvotes from network before 12:01 AM PT launch
- [ ] Prepare FAQ responses for anticipated questions

---

## Tier 3 — Medium-Term (Month 2–3)

### 3.1 Public API Documentation Page

**Competitive advantage:** IdeaBrowser has no public API. StartInsight has 235+ endpoints.

**Implementation:**
- Enable FastAPI's built-in Swagger UI at `/api/v1/docs` (currently likely disabled in production)
- Create public `/api-docs` page in the frontend
- Add API key management UI to user settings (DB tables `api_keys`, `api_key_usage_logs` already exist)

**Files:** `backend/app/main.py`, `frontend/app/[locale]/api-docs/page.tsx` (new)

---

### 3.2 Referral Program

**Problem:** No viral growth mechanism. Users have no incentive to invite others.

**Implementation:**
- Add `referral_code` (unique, auto-generated) and `referred_by` columns to `users` table
- Referrer reward: 1 month free Pro on first paid referral conversion
- Referee reward: 14-day Pro trial (vs standard 7-day free tier)
- Track via `?ref=<code>` URL parameter → store in `localStorage` → apply on signup

**Files:**
- `backend/app/models/user.py` (add 2 columns)
- `backend/app/api/routes/users.py` (referral tracking logic)
- `frontend/app/[locale]/settings/page.tsx` (referral share widget)
- 1 Alembic migration (add columns to `users`)

---

### 3.3 Email Digest Validation

**Problem:** The weekly email digest is scheduled (Mondays 09:00 UTC via arq) but has never been end-to-end tested with a real recipient.

**Fix:**
1. Trigger a test digest send via admin panel → verify formatting, links, unsubscribe
2. Add open-rate tracking (simple 1×1 pixel or PostHog event on link click)
3. A/B test two subject line variants

**Files:** `backend/app/services/email_service.py`, admin digest trigger route

---

### 3.4 Multi-Language Re-enablement (Post-Validation)

**Status:** DR-002 — English-only MVP. Rolled back with high reversibility (2–3 days to re-enable).

**Trigger condition:** APAC traffic > 20% of sessions OR 100+ paying subscribers.

**Effort:** 2–3 days (language files exist, just need re-enabling in `frontend/lib/i18n.ts`)

---

## Key Files Reference

| Area | Critical Files |
|------|---------------|
| Scrapers | `backend/app/scrapers/*.py` (6 files) |
| Scheduler | `backend/app/scheduler.py` |
| Worker | `backend/app/worker.py` |
| Insights API | `backend/app/api/routes/insights.py` |
| Dashboard | `frontend/app/[locale]/dashboard/page.tsx` |
| Layout / SEO | `frontend/app/layout.tsx` |
| User model | `backend/app/models/user.py` |
| Admin panel | `frontend/app/[locale]/admin/` |

---

## Execution Roadmap

```
Week 1
├── Diagnose + fix scraper pipeline (BLOCKING — no new content without this)
├── Configure uptime monitoring (15 min, no code)
├── Submit sitemap to Google Search Console
└── Seed content via admin portal (50+ insights, 5+ blog posts)

Month 1
├── PostHog user analytics
├── New user onboarding banner
├── E2E test expansion (auth + workspace + validate suites)
├── Redis caching for list endpoints
└── ProductHunt launch

Month 2
├── Public API documentation page
├── Email digest end-to-end validation
└── Referral program (1 migration + UI)

Month 3+
└── Multi-language re-enablement (if APAC traction confirmed)
```

---

## Success Metrics (30-Day Targets)

| Metric | Today | Target |
|--------|-------|--------|
| Pulse signals_24h | Recovering (scraper fixed) | 50+ |
| Daily new insights | Recovering (scraper fixed) | 20+ |
| Total insights | ~399 | 600+ |
| Organic search visitors | ~0 | 200+/month |
| Registered users | Unknown | 100+ |
| Paying subscribers | Unknown | 5+ |
| Uptime | Unmonitored | 99.5%+ monitored |
| E2E test coverage | ~55% | 85%+ |
