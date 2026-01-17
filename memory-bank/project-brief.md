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

8. Future Roadmap (Post-MVP)
User Customization: Users can track specific keywords or niches.

Competitor Radar: AI agents automatically find and list existing competitors for a generated idea.

Newsletter Integration: Automated daily email summaries.
