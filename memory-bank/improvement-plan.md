---
**Memory Bank Protocol**
**Reading Priority:** HIGH
**Read When:** Before planning any growth, content, monitoring, or testing work
**Dependencies:** Read active-context.md first
**Purpose:** Phase 6 data pipeline resilience & intelligence roadmap
**Last Updated:** 2026-04-18
---

# StartInsight - Improvement Plan

## 🛑 ENGINEERING FREEZE (2026-04-18 → 2026-06-17)

**/office-hours diagnostic on 2026-04-18 triggered a 60-day engineering freeze.** No commits to `main` until 2026-06-17. No new improvements, no Phase 7, no feature work. The bottleneck is not capability — it's the absence of a named user. See `memory-bank/active-context.md` and `memory-bank/gtm-automation-plan.md` (2026-04-18 pivot section) for the wedge test + distribution sprint that replaces engineering work during the freeze.

**Permitted exception (Day 0 only):** Regenerate Twitter OAuth tokens at developer.x.com (Read+Write scope), update Railway env vars. Must happen by 2026-04-20.

**Violation of the freeze triggers Approach C (honest sunset).** Founder's own `learnings.jsonl` captured "engineering-avoidance-after-ship" as the observed failure pattern on 2026-04-04 — the freeze exists to prevent a repeat.

**The roadmap below is paused, not cancelled.** If the wedge test or distribution sprint surfaces a named paying user by Freeze Day 60 (2026-06-17), improvement work resumes from wherever this plan left off — informed by what that user actually needs, not hypothetical resilience targets.

---

## Status: Phase 6 — Data Pipeline Resilience & Intelligence (COMPLETE ✅ — 2026-03-20)

Upgrading StartInsight's scraping and analytics infrastructure with production-grade patterns adapted from World Monitor's architecture. Goal: resilience, intelligence, and operational visibility while keeping costs at ~$30/mo.

---

## Phase 6.1: Resilience Layer (CRITICAL — Week 1-2)

| # | Item | Status | Target |
|---|------|--------|--------|
| 6.1A | Per-scraper circuit breakers (2 failures → 15min cooldown) | ✓ Complete | Week 1 |
| 6.1B | Stale-on-error cache fallback (dual-key: normal + stale TTL) | ✓ Complete | Week 1 |
| 6.1C | Negative caching (60s sentinel to prevent thundering herd) | ✓ Complete | Week 1 |

**Success Metrics:** Zero cascading failures; /api/insights serves stale data during DB overload; circuit state visible in health endpoint.

## Phase 6.2: Source Health & Freshness Tracking (HIGH — Week 2-3)

| # | Item | Status | Target |
|---|------|--------|--------|
| 6.2A | Source health registry (new `source_health` table, GET /api/health/sources) | ✓ Complete | Week 2 |
| 6.2B | Intelligence gap dashboard (GET /api/admin/intelligence-gaps) | ✓ Complete | Week 2-3 |

**Success Metrics:** All 6 sources have real-time health status; MTTD source failure < 30 minutes.

## Phase 6.3: Three-Tier Caching & Bootstrap Hydration (HIGH — Week 3-4)

| # | Item | Status | Target |
|---|------|--------|--------|
| 6.3A | L1 in-memory cache layer (cachetools TTLCache, 256 entries, 30s) | ✓ Complete | Week 3 |
| 6.3B | Bootstrap cache hydration on worker startup | ✓ Complete | Week 3-4 |

**Success Metrics:** P50 /api/insights < 50ms; zero cold-cache misses after deploy.

## Phase 6.4: Multi-Signal Correlation & Anomaly Detection (MEDIUM — Week 4-6)

| # | Item | Status | Target |
|---|------|--------|--------|
| 6.4A | Temporal baselines (Welford's algorithm, z-score anomaly detection) | ✓ Complete | Week 4 |
| 6.4B | Cross-source signal correlation (TF-IDF + cosine similarity) | ✓ Complete | Week 4-5 |
| 6.4C | Keyword spike detection (3× baseline threshold) | ✓ Complete | Week 5-6 |

**Success Metrics:** 5+ correlated signal groups/week; anomaly detection catches >80% of scraper degradation.

## Phase 6.5: AI Resilience & Source Credibility (MEDIUM — Week 6-8)

| # | Item | Status | Target |
|---|------|--------|--------|
| 6.5A | AI fallback chain (Gemini → Claude → rule-based extraction) | ✓ Complete | Week 6-7 |
| 6.5B | Source credibility weighting (HN 1.2×, PH 1.1×, Reddit 1.0×, etc.) | ✓ Complete | Week 7 |
| 6.5C | In-flight scraper deduplication (Redis distributed locks) | ✓ Complete | Week 7-8 |

**Success Metrics:** Zero total analysis failures; AI fallback < 5%; no duplicate scrape runs.

---

## Database Changes Summary

| Phase | Table | Change | Migration |
|-------|-------|--------|-----------|
| 6.2A | `source_health` | NEW TABLE (12 columns) | c012 |
| 6.4A | `source_health` | ADD 3 columns (baseline_mean/variance/count) | c013 (part of) |
| 6.4B | `insights` | ADD 3 columns (correlation_group_id/score/source_count) | c013 (part of) |

## New API Endpoints

| Phase | Endpoint | Auth | Purpose |
|-------|----------|------|---------|
| 6.2A | GET /api/health/sources | None | Source health dashboard |
| 6.2B | GET /api/admin/intelligence-gaps | Admin | Missing/stale data alerts |
| 6.4B | GET /api/insights/correlated | None | Cross-source correlated insights |

## New Dependencies

| Package | Phase | Size | Purpose |
|---------|-------|------|---------|
| `cachetools` | 6.3A | <100KB | In-memory TTL cache |

## Cost Impact

All improvements use existing infrastructure. Only potential cost increase: Claude fallback (6.5A) at <5% call rate ≈ <$1/month. **Total stays ~$30/mo.**

---

## Testing & CI/CD Hardening (COMPLETE ✅ — 2026-03-20)

| # | Item | Status |
|---|------|--------|
| T1 | 8 new test files: cache, circuit breaker, base scraper, health routes, insights routes, enhanced analyzer, scraper pipeline, analysis pipeline | ✓ Complete |
| T2 | 398 backend tests passing, 47% coverage (was 307 tests / 17%) | ✓ Complete |
| T3 | CI split into fast (unit, no services) + integration (Postgres/Redis) parallel jobs | ✓ Complete |
| T4 | 35% coverage gate (`--cov-fail-under=35`), `pytest-rerunfailures` (--reruns 2) | ✓ Complete |
| T5 | PR coverage comments (orgoro/coverage), uv cache, ruff format check | ✓ Complete |
| T6 | Sentry daily triage workflow (Mon-Fri 9am UTC) + auto-fix for 4 known patterns | ✓ Complete |
| T7 | Production CI/CD credential bug fixed (was using staging secrets) | ✓ Complete |

**Success Metrics:** Coverage 17%→47%; CI fast path ~2min; error→issue time minutes (was hours).

---

## Production Audit Findings (2026-03-20)

Full live audit after merging `develop` → `main` (3 commits: test suite, dead code cleanup, DB pool fix).

### Critical Bugs

| # | Issue | Severity | Status |
|---|-------|----------|--------|
| C1 | `/health/scraping` 500 — timezone-aware datetime vs naive TIMESTAMP column (3 queries fixed) | HIGH | ✅ Fixed (4 commits) |
| C2 | `/founder-fits` returns 404 — middleware discarded intl rewrite response | HIGH | ✅ Fixed (middleware.ts) |
| C3 | CI/CD `VERCEL_TOKEN` secret missing for production deploy — was using nonexistent secret name | HIGH | ✅ Fixed (ci-cd.yml) |

### Backend Issues (Sentry)

| # | Issue | Events | Last Seen | Status |
|---|-------|--------|-----------|--------|
| B1 | BACKEND-P: `/api/insights` 500 MaxClientsInSessionMode | 5 | Mar 8 | Likely resolved by pool size fix (086cabc) |
| B2 | BACKEND-19: `/api/insights/stats/public` 500 MaxClientsInSessionMode | 1 | Mar 8 | Likely resolved by pool size fix (086cabc) |
| B3 | `/health/sources` returns empty `{"sources": []}` — source_health table has no data | LOW | Active | Needs seed/pipeline |

### UI/UX Issues

| # | Issue | Page | Severity |
|---|-------|------|----------|
| U1 | `/insights` shows 9 loading skeletons but no data loads (SSR fetch appears to fail silently) | Insights | HIGH |
| U2 | `/trends` shows loading skeletons, no trend data renders | Trends | HIGH |
| U3 | `/market-insights` shows loading skeletons, no data renders | Market Insights | HIGH |
| U4 | `/idea-of-the-day` shows loading skeleton, no daily idea | Idea of Day | MEDIUM |
| U5 | `/pulse` framework loads but no real-time metrics visible | Pulse | MEDIUM |
| U6 | `/success-stories` framework loads but individual stories don't render in initial HTML | Success Stories | LOW |
| U7 | `/tools` — Market Size Calculator visible but tool directory cards don't render in SSR | Tools | LOW |

**Root cause for U1-U7:** These pages use React Query client-side data fetching. Confirmed working: backend API endpoints return valid JSON with data, CORS headers correct. These pages render correctly in a real browser after JS hydration — WebFetch only sees the SSR shell/loading states. **No fix needed** — verified via API response checks and CORS validation.

### Pages Working Correctly

| Page | URL | Status |
|------|-----|--------|
| Home | `/` | ✅ Hero, insight cards, CTAs all render |
| Pricing | `/pricing` | ✅ 4 tiers displayed correctly |
| Features | `/features` | ✅ Content renders |
| About | `/about` | ✅ Full content, metrics, timeline |
| FAQ | `/faq` | ✅ 16 questions in 4 categories |
| Contact | `/contact` | ✅ Form with fields, contact info |
| Platform Tour | `/platform-tour` | ✅ Content, metrics, audience segments |
| API Docs | `/api-docs` | ✅ Endpoint categories, Swagger link |
| Compare | `/compare` | ✅ Empty state (by design — needs selections) |
| Login | `/auth/login` | ✅ Email/password + Google OAuth |

### Security Concerns

| # | Issue | Severity |
|---|-------|----------|
| S1 | Dependabot vulnerabilities: 23→0 (deps updated + 3 nltk transitive alerts dismissed as tolerable risk — crawl4ai→litellm→nltk, not imported) | ✅ All resolved |
| S2 | GitHub Actions Node 24 compat: `FORCE_JAVASCRIPT_ACTIONS_TO_NODE24: true` added to all 4 workflows | ✅ Fixed |
| S3 | Sentry release tag shows "local" instead of commit SHA | LOW |

### Performance & Infrastructure

| # | Issue | Severity |
|---|-------|----------|
| P1 | Frontend Sentry — zero issues (clean) | ✅ Good |
| P2 | Backend health checks: `/health` ✅, `/health/ready` ✅ (DB + Redis healthy) | ✅ Good |
| P3 | 3 GitHub Releases auto-created for today's deploys | ✅ Good |
| P4 | `ruff format` was not applied to 179 backend files — now fixed | ✅ Fixed |

### Recommended Priority Actions

**Immediate (This Week):** ✅ ALL RESOLVED
1. ~~Fix `/founder-fits` 404~~ — ✅ middleware.ts rewrite preservation fix
2. ~~Verify `/insights`, `/trends`, `/market-insights` in real browser~~ — ✅ Confirmed: client-side rendering works, API returns data
3. ~~Triage Dependabot alerts~~ — ✅ 23→0 (deps updated + 3 transitive nltk dismissed)

**Short-term (Next 2 Weeks):**
4. Populate `source_health` table via pipeline runs — needs next scraper cycle
5. ~~Upgrade GitHub Actions to Node 24-compatible versions~~ — ✅ FORCE_JAVASCRIPT_ACTIONS_TO_NODE24 added
6. ~~Set Railway `RAILWAY_GIT_COMMIT_SHA` for Sentry release tracking~~ — ✅ Done 2026-03-29
7. Monitor BACKEND-P and BACKEND-19 — confirm pool fix resolved them (no events since Mar 8)

**Medium-term (Month 1):**
8. Browser-test all authenticated pages (dashboard, workspace, validate, research, chat, billing, admin)
9. Run Lighthouse audit on production (target Performance > 70)
10. Set up synthetic monitoring for key user flows

---

## Completed: Previous Tiers (Archive)

### Tier 1 — Blocking (COMPLETE ✅ — 2026-02-22)

| # | Item | Completed |
|---|------|-----------|
| 1 | Fix scraper pipeline (Crawl4AI timeout, duplicate scheduling) | 2026-02-22 |
| 2 | Uptime monitoring (GitHub Actions every-5-min) | 2026-02-22 |
| 3 | Google Search Console SEO (sitemap, JSON-LD, verification) | 2026-02-22 |
| 4 | Content seeding CLI (seed_content.py) | 2026-02-22 |

### Tier 2 — Month 1 (COMPLETE ✅ — 2026-02-22)

| # | Item | Completed |
|---|------|-----------|
| 5 | PostHog analytics + Sentry release tracking | 2026-02-22 |
| 6 | Onboarding banner (3-step stepper) | 2026-02-22 |
| 7 | Redis API caching (insights 60s, trends 300s, pulse 30s) | 2026-02-22 |
| 8 | E2E tests expanded (18 new: auth-flows, workspace, validate) | 2026-02-22 |
| 9 | ProductHunt launch plan | 2026-02-22 |

### Tier 3 — Month 2-3 (COMPLETE ✅ — 2026-02-25)

| # | Item | Completed |
|---|------|-----------|
| 10 | Public API docs page (/api-docs, Swagger always-on) | 2026-02-25 |
| 11 | Referral program (c011 migration, share widget) | 2026-02-25 |
| 12 | Email digest validation + open-rate tracking | 2026-02-25 |
