# Active Context: StartInsight Development

## Current Phase
**Phase 1: The "Collector" (Data Collection Loop)**

## Current Focus
**Step 1.4: Task Queue Setup (Arq)**

## Objective
Set up Arq task queue with Redis for scheduling scraping tasks and create scheduler for automated execution every 6 hours.

---

## What We're Building Right Now
We are setting up the Arq task queue with Redis to schedule automated scraping tasks and create the scheduler for running data collection every 6 hours.

### Immediate Tasks
- [ ] Create `backend/app/worker.py` with Arq WorkerSettings and scraper tasks
- [ ] Create `backend/app/tasks/scheduler.py` with APScheduler integration
- [ ] Register scraper tasks: scrape_reddit_task, scrape_product_hunt_task, scrape_trends_task
- [ ] Configure scheduler to run tasks every 6 hours
- [ ] Test task execution and verify data storage in database

---

## Technical Context

### What Works
- ✅ **Phase 1.1 Complete**: Git repository initialized, project structure created, Python environment with `uv` and 173 packages
- ✅ **Phase 1.2 Complete**: PostgreSQL 16 (port 5433) and Redis 7 (port 6379) running in Docker, SQLAlchemy 2.0 async configured, database connection verified
- ✅ **Phase 1.3 Complete**: RawSignal database model created, Alembic migrations configured, Firecrawl client wrapper with retry logic, 3 scrapers implemented (Reddit, Product Hunt, Google Trends)
- Documentation is complete and production-ready:
  - `project-brief.md`: Defines the three core loops (Collection → Analysis → Presentation)
  - `tech-stack.md`: Lists all technologies, libraries, and dependencies
  - `implementation-plan.md`: Provides step-by-step roadmap for all 3 phases

### What's Next
1. **Task Queue Setup** (Current - Phase 1.4) - Arq worker with scraper tasks
2. **Task Scheduler** (Current - Phase 1.4) - APScheduler for 6-hour intervals
3. FastAPI Endpoints (REST API for raw signals) - Phase 1.5
4. Environment & Configuration - Phase 1.6
5. Testing & Validation - Phase 1.7

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

### Phase 1 Progress: ~37% Complete (3/8 steps)
- [x] 1.1 Project Initialization
- [x] 1.2 Database Setup
- [x] 1.3 Firecrawl Integration
- [ ] 1.4 Task Queue Setup (In Progress)
- [ ] 1.5 FastAPI Endpoints
- [ ] 1.6 Environment & Configuration
- [ ] 1.7 Testing & Validation
- [ ] 1.8 Documentation

---

**Last Updated**: 2026-01-18
**Updated By**: Lead Architect (Claude)
**Status**: Phase 1.4 in progress - Task queue and scheduler setup
