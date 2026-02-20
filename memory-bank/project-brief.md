---
**Memory Bank Protocol**
**Reading Priority:** HIGH
**Read When:** At the start of any new session, before proposing architectural changes
**Dependencies:** None (this is the entry point)
**Purpose:** Executive summary, business objectives, 3 core loops, competitive positioning
**Last Updated:** 2026-02-19
---

# Project Brief: StartInsight

## 1. Executive Summary

StartInsight is a daily, AI-powered business intelligence engine that discovers, validates, and presents data-driven startup ideas. It relies on real-time market signals scraped from social discussions, search trends, and product launches to identify genuine market gaps and consumer pain points.

The system operates on an automated **Collect → Analyze → Present** loop — functioning as an analyst that never sleeps.

**Status:** Live in production as of 2026-02-19. All phases complete.

---

## 2. Core Philosophy

**Signal over Noise:** We do not generate random ideas. We surface problems that real people are complaining about or searching for.

**Data-Driven Intuition:** Every insight is backed by source data (specific Reddit threads, rising Google search keywords, Product Hunt launches).

**Automated Intelligence:** AI agents handle market research heavy lifting, leaving users with high-level decision-making.

**MVP Cost Philosophy:** Minimize cost at all layers except Supabase Pro ($25/mo) + Gemini API (~$1-5/mo). Total production cost ~$30/mo regardless of user count (up to free-tier limits).

---

## 3. Key Objectives

**Automated Trend Scouting:** Consistently aggregate data from 6 high-signal sources:
- Reddit, Product Hunt, Google Trends (primary)
- Twitter/X, Hacker News, Firecrawl (active)

**AI Analysis Pipeline:** 8 PydanticAI agents (Gemini 2.0 Flash) process raw text into structured Insight Reports (Problem, Solution, Market Size, Competitor Check, 8-dimension scoring).

**Super Admin Agent Controller:** Real-time monitoring and control dashboard for AI agents with pause/resume capabilities, SSE streaming updates, cost tracking, and execution logs.

**Visual Dashboard:** Clean, minimal Next.js frontend for browsing, filtering, and saving insights.

---

## 4. User Journey & Discovery Features

**Consumer-Focused Experience:**
Users are readers, not creators. The platform emphasizes discovery, curation, and validation. Users cannot trigger AI Research Agents (admin-only capability).

**Multi-Modal Discovery Paths:**

1. **Daily Digest** — Top 5 insights of the day
2. **Database Filtering** (IdeaBrowser-inspired):
   - Status tabs: New, For You, Interested, Saved, Building, Not Interested
   - Full-text search, 12 results/page, URL filtering
3. **Trends Discovery** — 180+ trending keywords with volume/growth metrics, sparkline charts
4. **Deep Dive** — Per-insight view with 8-dimension radar chart, trend keywords, community signals
5. **Validation** — Generated MVP plan + Glue Code suggestions
6. **Pulse Page** — Real-time SSE feed of live signals (Q1 feature)
7. **Idea of the Day** — Daily featured insight with social sharing (Q3 feature)
8. **Insight Comparison** — Side-by-side 2-insight radar chart + table (Q5 feature)

---

## 5. The Three Core Loops

### Loop 1: Data Collection (The Collector)

- **Purpose:** Extract raw market signals from 6 high-signal sources
- **Schedule:** Every 6 hours (arq tasks via Railway Redis)
- **Process:**
  - 6 scrapers: Reddit, Product Hunt, Google Trends, Twitter/X, Hacker News, Firecrawl
  - Raw content stored in `raw_signals` table with full provenance (source URL, timestamp, content hash)
- **Output:** Raw text data stored in PostgreSQL

### Loop 2: Analysis (The Analyst)

- **Purpose:** Transform raw signals into actionable structured insights
- **Schedule:** Every 6 hours (post-collection)
- **Process:**
  - 8 PydanticAI agents (Gemini 2.0 Flash) process unprocessed signals
  - Identify pain points, score relevance, extract: Problem Statement, Solution, Market Size, Competitor Landscape
  - Pydantic V2 schema validation on all outputs
- **Output:** Structured JSON stored in `insights` table with 8-dimension scores

### Loop 3: Presentation (The Dashboard)

- **Purpose:** Surface insights to end users in a consumable format
- **Trigger:** User accesses Next.js dashboard
- **Process:**
  - FastAPI serves ranked insights via 232+ REST endpoints
  - Frontend displays: Top 5 daily, deep-dive view, trend graphs, validation data
  - User filters by category, date, keyword, status
- **Output:** Interactive Next.js dashboard

---

## 6. Architecture Overview

```
6 Scrapers → arq tasks → Railway Redis queue → Supabase PostgreSQL
          → 8 AI Agents (Gemini 2.0 Flash) → 232+ FastAPI endpoints
          → Next.js App Router (Vercel)
```

| Layer | Technology | Hosting |
|-------|------------|---------|
| **Frontend** | Next.js 14+ App Router, TypeScript, Tailwind, shadcn/ui | Vercel (free) |
| **Backend** | FastAPI async, SQLAlchemy 2.0, Pydantic V2 | Railway (free 500h/mo) |
| **Database** | PostgreSQL via Supabase Pro, 69 tables | Supabase Pro ($25/mo) |
| **Task Queue** | arq + Redis | Railway Redis (free) |
| **Auth** | Supabase JWT (ES256 via JWKS) | Supabase Pro (included) |
| **AI** | PydanticAI v1.x + Gemini 2.0 Flash | Google API (~$1-5/mo) |
| **Email** | Resend | Free (3K/mo) |
| **Payments** | Stripe | Free + 2.9% per transaction |
| **Errors** | Sentry | Free (5K events/mo) |
| **Total** | | **~$30/mo** |

---

## 7. Data Scale (Production)

- **Database:** 69 tables (26 core + 43 Phase 8-10 features)
- **API Endpoints:** 232+
- **AI Agents:** 8 active agents
- **Scrapers:** 6 active scrapers
- **Tests:** 291 backend tests (85% coverage), 47 E2E tests (5 browsers)
- **Background Jobs:** 8 scheduled arq tasks (every 6h + daily + weekly)

---

## 8. Competitive Positioning vs IdeaBrowser

**Pricing:**
| Tier | IdeaBrowser | StartInsight | Advantage |
|------|-------------|--------------|-----------|
| Free | No free tier | $0 | ✅ |
| Starter | $499/yr ($41/mo) | $19/mo | ✅ 54% cheaper |
| Pro | $1,999/yr ($166/mo) | $49/mo | ✅ 70% cheaper |
| Enterprise | $2,999/yr ($250/mo) | $299/mo | ✅ Similar |

**Feature Comparison:**
| Feature | IdeaBrowser | StartInsight |
|---------|-------------|--------------|
| Scoring dimensions | 4 | **8 (2x)** |
| Data sources | 4 | **6 (+50%)** |
| Real-time updates | 24h digest | **<100ms SSE** |
| Public API | No | **232+ endpoints** |
| Admin agent controller | No | **Yes (SSE streaming)** |
| Team collaboration | Empire tier only | **All tiers (RBAC)** |
| APAC latency | 180ms (US-based) | **50ms (Sydney)** |

**Unique Value Proposition:**
> "The only AI-powered startup idea discovery platform with 8-dimension scoring, real-time trend updates, and public API — at 50-70% lower cost than competitors."

---

## 9. Content Infrastructure (Live)

All content fully seeded and live:

- **Insights:** AI-generated daily (growing)
- **Trends:** 180+ keywords with volume/growth metrics
- **Tools Directory:** 54 tools, 6 categories
- **Success Stories:** 12 founder case studies
- **Blog (Market Insights):** 6 articles, targeting 12 articles/6 months
- **Public Pages:** 10 pre-auth pages (/, /tools, /success-stories, /trends, /market-insights, /about, /contact, /faq, /pricing, /platform-tour)

---

## 10. Post-Launch Priorities

**Immediate (Content Seeding):**
- Seed 50+ insights across 10+ categories via admin portal
- Verify scraper pipeline health in admin → Pipeline Monitoring
- Submit sitemap to Google Search Console

**Short-term (Growth):**
- Set up UptimeRobot / Checkly uptime monitoring
- Launch to waitlist / Product Hunt
- Create initial batch of marketing content

**Monitoring (Ongoing):**
- Review Sentry for new production errors weekly
- Monitor Stripe webhook health (checkout, subscription events)
- Check Railway metrics (CPU, memory, response times)

---

**Last Updated:** 2026-02-19
**Status:** LIVE IN PRODUCTION — All phases complete. Scheduler running. Content seeding next.
