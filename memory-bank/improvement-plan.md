---
**Memory Bank Protocol**
**Reading Priority:** HIGH
**Read When:** Before planning any growth, content, monitoring, or testing work
**Dependencies:** Read active-context.md first
**Purpose:** Phase 6 data pipeline resilience & intelligence roadmap
**Last Updated:** 2026-03-20
---

# StartInsight - Improvement Plan

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
| 6.4A | `source_health` | ADD 3 columns (baseline_mean/variance/count) | c013 |
| 6.4B | `insights` | ADD 3 columns (correlation_group_id/score/source_count) | c014 |

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
