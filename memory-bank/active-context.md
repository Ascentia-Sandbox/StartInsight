# Active Context: StartInsight Development

## Current Phase
**Phase 1: The "Collector" (Data Collection Loop)**

## Current Focus
**Step 1.3: Firecrawl Integration**

## Objective
Integrate Firecrawl API for web scraping and implement source-specific scrapers for Reddit, Product Hunt, and Google Trends.

---

## What We're Building Right Now
We are integrating Firecrawl for web scraping and building source-specific scrapers to collect market signals from Reddit, Product Hunt, and Google Trends.

### Immediate Tasks
- [ ] Create database models (RawSignal, Insight) with SQLAlchemy 2.0 async syntax
- [ ] Set up Alembic for database migrations
- [ ] Integrate Firecrawl Python SDK for web scraping
- [ ] Implement Reddit scraper (r/startups, r/SaaS)
- [ ] Implement Product Hunt scraper (daily launches)
- [ ] Implement Google Trends scraper (search volume data)

---

## Technical Context

### What Works
- ✅ **Phase 1.1 Complete**: Git repository initialized, project structure created, Python environment with `uv` and 173 packages
- ✅ **Phase 1.2 Complete**: PostgreSQL 16 (port 5433) and Redis 7 (port 6379) running in Docker, SQLAlchemy 2.0 async configured, database connection verified
- Documentation is complete and production-ready:
  - `project-brief.md`: Defines the three core loops (Collection → Analysis → Presentation)
  - `tech-stack.md`: Lists all technologies, libraries, and dependencies
  - `implementation-plan.md`: Provides step-by-step roadmap for all 3 phases

### What's Next
1. **Database Models & Migrations** (Current - Part of Phase 1.3)
2. **Firecrawl Integration** (Current - Phase 1.3)
3. **Source-Specific Scrapers** (Current - Phase 1.3)
4. Task Queue Setup (Arq + Redis) - Phase 1.4
5. FastAPI Endpoints (REST API for raw signals) - Phase 1.5

---

## Key Decisions Made

### Technology Stack (Phase 1)
- **Backend Framework**: FastAPI (async, modern, fast)
- **Database**: PostgreSQL (managed on Railway/Neon for production)
- **ORM**: SQLAlchemy (async mode)
- **Scraper**: Firecrawl (AI-powered web → markdown conversion)
- **Task Queue**: Arq (lightweight, async-native)
- **Package Manager**: `uv` (blazing-fast Python dependency management)

### Architecture Principles
1. **Modular Monolith**: Single repo with clear separation (backend/, frontend/)
2. **Async-First**: All I/O operations use async/await
3. **Type Safety**: Pydantic for validation, TypeScript for frontend
4. **Environment Parity**: Docker Compose for local dev, mirrors production setup

---

## Current Blockers
**None** - Ready to begin implementation.

---

## Environment Setup Checklist
Before starting Phase 1.3, ensure you have:
- [x] Python 3.11+ installed
- [x] Docker Desktop installed and running
- [x] Git installed
- [x] `uv` package manager installed
- [x] PostgreSQL and Redis containers running (`docker-compose up -d`)
- [x] Text editor/IDE ready (VS Code recommended)

---

## Reference Files
- **Project Brief**: `memory-bank/project-brief.md`
- **Tech Stack**: `memory-bank/tech-stack.md`
- **Implementation Plan**: `memory-bank/implementation-plan.md`

---

## Notes for Next Session
When resuming work:
1. Read this file first to understand current context
2. Refer to `implementation-plan.md` Phase 1.3 for detailed steps
3. Update this file after completing each major milestone
4. Check `progress.md` to see completed work and avoid duplication
5. Move to Phase 1.4 (Task Queue) only after 1.3 is fully complete

---

## Progress Tracking

### Phase 1 Progress: ~25% Complete (2/8 steps)
- [x] 1.1 Project Initialization
- [x] 1.2 Database Setup
- [ ] 1.3 Firecrawl Integration (In Progress)
- [ ] 1.4 Task Queue Setup
- [ ] 1.5 FastAPI Endpoints
- [ ] 1.6 Environment & Configuration
- [ ] 1.7 Testing & Validation
- [ ] 1.8 Documentation

---

**Last Updated**: 2026-01-18
**Updated By**: Lead Architect (Claude)
**Status**: Phase 1.3 in progress - Database models and Firecrawl integration
