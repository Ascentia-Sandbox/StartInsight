---
**Memory Bank Protocol**
**Reading Priority:** HIGH
**Read When:** At the start of any new session, before proposing architectural changes
**Dependencies:** None (this is the entry point)
**Purpose:** Executive summary, business objectives, 3 core loops, competitive positioning
**Last Updated:** 2026-01-25
---

Project Brief: StartInsight
1. Executive Summary
StartInsight is a daily, AI-powered business intelligence engine designed to discover, validate, and present data-driven startup ideas. Unlike traditional brainstorming tools, StartInsight relies on real-time market signalsscraped from social discussions, search trends, and product launchesto identify genuine market gaps and consumer pain points.

The system operates on an automated "Collect-Analyze-Present" loop, functioning as an automated analyst that never sleeps.

2. Core Philosophy (The Vibe)
Signal over Noise: We do not generate random ideas. We surface problems that real people are complaining about or searching for.

Data-Driven Intuition: Every insight must be backed by source data (e.g., specific Reddit threads, rising Google search keywords).

Automated Intelligence: The "heavy lifting" of market research is offloaded to AI agents, leaving the user with high-level decision-making capability.

3. Key Objectives
Automated Trend Scouting: consistently aggregate data from high-signal sources. **Phase 1 MVP**: Reddit, Product Hunt, Google Trends. **Phase 4+ Expansion**: X/Twitter, Hacker News.

AI Analysis Pipeline: Use LLMs to process raw unstructured text into structured "Insight Reports" (Problem, Solution, Market Size, Competitor Check).

Visual Dashboard: A clean, minimal web interface for users to browse, filter, and save insights.

4. User Journey
Daily Digest: User logs in to see the "Top 5 Insights of the Day."

Deep Dive: User clicks an insight (e.g., "AI for Legal Docs") and sees the underlying data:

"300% spike in search volume."

"50+ negative comments on r/lawyers about current tools."

Validation: User sees a generated MVP plan or "Glue Code" suggestions to build the solution.

5. The Three Core Loops
StartInsight operates on three distinct, sequential processing loops that run continuously:

**Loop 1: Data Collection (The Collector)**
- **Purpose**: Extract raw market signals from high-signal sources.
- **Trigger**: Runs on a scheduled basis (e.g., every 6 hours or daily).
- **Process**:
  - **Phase 1 MVP**: Scrapes content from Reddit, Product Hunt, and Google Trends.
  - **Phase 4+ Expansion**: Twitter/X and Hacker News (see Future Enhancements).
  - Uses Firecrawl to convert web pages into LLM-readable markdown.
  - Stores raw, unprocessed data in PostgreSQL with metadata (source, timestamp, URL).
- **Output**: Raw text data (posts, comments, trends) stored in the `raw_signals` table.

**Loop 2: Analysis (The Analyst)**
- **Purpose**: Transform raw signals into actionable, structured insights.
- **Trigger**: Runs immediately after each data collection cycle completes (coupled execution).
- **Frequency**: Every 6 hours (aligned with scraping schedule).
- **Process**:
  - Fetches unprocessed raw signals from the database.
  - Uses LLM agents (LangChain/PydanticAI) to:
    - Identify pain points and market gaps.
    - Score relevance and market potential.
    - Extract structured data: Problem Statement, Proposed Solution, Market Size Estimate, Competitor Landscape.
  - Validates output using Pydantic schemas.
- **Output**: Structured JSON insights stored in the `insights` table with relevance scores.

**Loop 3: Presentation (The Dashboard)**
- **Purpose**: Surface insights to the end user in a consumable format.
- **Trigger**: User accesses the Next.js dashboard.
- **Process**:
  - FastAPI serves ranked insights via REST endpoints.
  - Frontend displays:
    - Top 5 insights of the day (sorted by relevance score).
    - Deep-dive view showing source links, trend graphs, and validation data.
  - User can filter by category, date, or keyword.
- **Output**: Visual, interactive dashboard accessible via browser.

6. Architectural High-Level Overview
The system follows a Modular Agentic Architecture:

**The Collector (ETL Layer)**
- Scheduled Python service utilizing Firecrawl for web scraping.
- Converts unstructured web content into markdown for LLM consumption.
- Stores raw data with full provenance (source URL, timestamp, content hash).

**The Analyst (AI Core)**
- LLM-powered processing pipeline using LangChain or PydanticAI.
- Transforms raw text into structured, validated JSON insights.
- Scores each insight for relevance, market size, and feasibility.

**The Platform (Web & API)**
- Next.js 14+ frontend with TypeScript and Tailwind CSS.
- FastAPI backend exposing RESTful endpoints.
- Real-time updates via WebSockets (optional for MVP).

**The Vault (Storage)**
- PostgreSQL database with two primary tables: `raw_signals` and `insights`.
- Redis for task queue management and caching hot insights.
- Hosted on Railway/Neon for production, Docker for local development.

7. Success Metrics (MVP)
System Stability: The automated pipeline runs daily without crashing.

Data Quality: Insights are coherent and directly traceable to a source URL.

User Value: The dashboard successfully displays at least 10 high-quality insights per day.


<\!-- Competitive positioning merged from implementation-plan-phase4-detailed.md on 2026-01-24 -->

### IdeaBrowser Competitive Analysis Summary

**What They Charge:** $499-$2,999/year ($41-$250/month)

**What We'll Charge:** $19-$299/month (50-70% cheaper)

**Feature Parity Achieved:**
- [x] 8-dimension scoring (vs. their 6)
- [x] Value Ladder framework (4-tier pricing model)
- [x] Custom AI analysis (our Research Agent)
- [x] Build tools (landing pages, brand packages)
- [x] Export to PDF/CSV
- [x] Status tracking (Interested/Saved/Building)

**Our Unique Features:**
- Admin portal (monitor AI agents)
- Real-time updates (6-hour vs 24-hour)
- Public API (Phase 7)
- Team collaboration (Phase 7)
- White-label (Phase 7)

**Full Analysis:** See `memory-bank/ideabrowser-analysis.md`

---

<!-- Supabase competitive positioning added on 2026-01-25 for Phase 4.5 -->

## 9. Supabase Migration - Competitive Advantage

### Phase 4.5 Strategic Positioning

**Infrastructure Decision:** Migrating from self-hosted PostgreSQL to Supabase Cloud (Singapore)

**Cost Leadership:**
| Metric | Current (Neon) | Supabase Pro | IdeaBrowser (est.) |
|--------|----------------|--------------|-------------------|
| Monthly Cost (10K users) | $69 | $25 | $150+ (AWS RDS) |
| Revenue (10K users) | $59K MRR | $59K MRR | $50K MRR ($5/user avg) |
| Profit Margin | 98.6% | 99.5% | 97.5% |
| Cost per User | $0.0069 | $0.0025 | $0.015 |

**At 10K users:** Supabase saves $44/mo vs current, $125/mo vs IdeaBrowser infrastructure

**Real-time Advantage (Phase 5+):**
- **IdeaBrowser**: Static daily digests (24-hour latency)
- **StartInsight**: Real-time insight feed (<100ms latency via Supabase Realtime)
- **Competitive Edge**: "See ideas the moment they're discovered, not tomorrow"

**APAC Market Focus:**
- **Singapore Region**: 50ms latency for SEA users (vs 180ms US-based)
- **Market Growth**: 30% YoY SaaS adoption in APAC (Gartner 2024)
- **IdeaBrowser**: US-based (no APAC optimization)
- **Opportunity**: "Built for Asia Pacific entrepreneurs"

**Scalability Story:**
- **Current**: 15 concurrent connections (PostgreSQL pool)
- **Supabase**: 500 concurrent connections (Pro tier)
- **IdeaBrowser**: ~100 connections (estimated)
- **Marketing**: "Enterprise-grade infrastructure at startup prices"

### Updated Cost Structure (10K Users)

| Category | Current | Supabase Migration | Savings |
|----------|---------|-------------------|---------|
| **Infrastructure** |
| Database | $69 (Neon) | $25 (Supabase Pro) | -$44 |
| Redis | $5 (Upstash) | $5 (Upstash) | $0 |
| Hosting | $10 (Vercel) | $10 (Vercel) | $0 |
| **AI APIs** |
| Claude API | $450 | $450 | $0 |
| Firecrawl | $149 | $149 | $0 |
| **Total** | **$683/mo** | **$639/mo** | **-$44/mo** |

**Profit Margin:** 98.9% (vs 98.6% current)

**Revenue Target:** $25K MRR by Month 6 (Phase 4.5 complete)

---
