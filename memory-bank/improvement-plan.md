---
**Memory Bank Protocol**
**Reading Priority:** HIGH
**Read When:** Before planning any growth, content, monitoring, or testing work
**Dependencies:** Read active-context.md first
**Purpose:** Post-launch growth roadmap — Tier 1/2/3 priorities with 30-day success metrics
**Last Updated:** 2026-03-05
---

# StartInsight - Improvement Plan

## Status: All Tiers Complete ✅ (as of 2026-02-25)

All Tier 1, 2, and 3 items were completed during the post-launch sprint (2026-02-19 → 2026-02-25).

---

## Tier 1 — Blocking (COMPLETE ✅)

| # | Item | Status | Completed |
|---|------|--------|-----------|
| 1 | Fix scraper pipeline (Crawl4AI timeout, duplicate scheduling) | ✅ | 2026-02-22 |
| 2 | Uptime monitoring (GitHub Actions every-5-min) | ✅ | 2026-02-22 |
| 3 | Google Search Console SEO (sitemap, JSON-LD, verification) | ✅ | 2026-02-22 |
| 4 | Content seeding CLI (`seed_content.py`) | ✅ | 2026-02-22 |

## Tier 2 — Month 1 (COMPLETE ✅)

| # | Item | Status | Completed |
|---|------|--------|-----------|
| 5 | PostHog analytics + Sentry release tracking | ✅ | 2026-02-22 |
| 6 | Onboarding banner (3-step stepper) | ✅ | 2026-02-22 |
| 7 | Redis API caching (insights 60s, trends 300s, pulse 30s) | ✅ | 2026-02-22 |
| 8 | E2E tests expanded (18 new: auth-flows, workspace, validate) | ✅ | 2026-02-22 |
| 9 | ProductHunt launch plan | ✅ | 2026-02-22 |

## Tier 3 — Month 2-3 (COMPLETE ✅)

| # | Item | Status | Completed |
|---|------|--------|-----------|
| 10 | Public API docs page (`/api-docs`, Swagger always-on) | ✅ | 2026-02-25 |
| 11 | Referral program (c011 migration, share widget) | ✅ | 2026-02-25 |
| 12 | Email digest validation + open-rate tracking | ✅ | 2026-02-25 |

---

## 30-Day Success Metrics (2026-03-01 target)

| Metric | Target | Notes |
|--------|--------|-------|
| Insights seeded | 600+ | Pipeline running every 6h; 522 as of 2026-02-22 |
| Uptime | 99.9%+ | Monitored via GitHub Actions workflow |
| Scraper success rate | >80% | All 6 scrapers active; Crawl4AI timeout fixed |
| Lighthouse (production) | 85-90+ | Staging ~72 Slow-4G; production expected significantly better |

---

## Next Growth Actions (Post Tier 3)

**Manual actions required:**
1. Set `NEXT_PUBLIC_POSTHOG_KEY` in Vercel dashboard to activate PostHog analytics
2. Submit `https://startinsight.co/sitemap.xml` to Google Search Console
3. Seed content to 600+ insights before ProductHunt launch

**Potential future improvements:**
- A/B testing on onboarding flow (PostHog feature flags)
- Webhook-based Stripe dunning emails (failed payment recovery)
- LinkedIn/Twitter social sharing cards per insight
- Mobile PWA manifest + service worker for offline access
