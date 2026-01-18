# Active Context: StartInsight Development

## Current Phase
**Phase 1: The "Collector" (Data Collection Loop)** - ✅ COMPLETE

## Current Focus
**Phase 2: The "Analyzer" (Analysis Loop)** - Ready to Start

## Objective
Implement the AI-powered analysis engine using PydanticAI with Claude 3.5 Sonnet to analyze raw signals and generate structured insights.

---

## What We're Building Right Now
**Phase 2: The "Analyzer" (Analysis Loop)** - AI-powered insight extraction from raw signals.

The goal is to process raw signals collected in Phase 1 through a PydanticAI agent powered by Claude 3.5 Sonnet, extracting structured insights with market analysis, competitor research, and relevance scoring.

### Immediate Tasks (Phase 2.1: Database Schema Extension)

**Goal**: Create the `Insight` model to store AI-analyzed, structured insights.

**Tasks**:
- [ ] Create `backend/app/models/insight.py` with the following schema:
  ```python
  class Insight(Base):
      __tablename__ = "insights"

      id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid4)
      raw_signal_id: Mapped[UUID] = mapped_column(ForeignKey("raw_signals.id"), nullable=False)
      problem_statement: Mapped[str] = mapped_column(Text, nullable=False)
      proposed_solution: Mapped[str] = mapped_column(Text, nullable=False)
      market_size_estimate: Mapped[str] = mapped_column(String(20), nullable=False)  # "Small", "Medium", "Large"
      relevance_score: Mapped[float] = mapped_column(Float, nullable=False)  # 0.0 - 1.0
      competitor_analysis: Mapped[dict] = mapped_column(JSONB, nullable=True)  # List[Competitor]
      created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

      # Relationship
      raw_signal: Mapped["RawSignal"] = relationship(back_populates="insights")
  ```

- [ ] Update `backend/app/models/raw_signal.py` to add reverse relationship:
  ```python
  insights: Mapped[list["Insight"]] = relationship(back_populates="raw_signal")
  ```

- [ ] Create Alembic migration:
  ```bash
  cd backend
  uv run alembic revision --autogenerate -m "create insights table"
  uv run alembic upgrade head
  ```

- [ ] Create test file `test_phase_2_1.py` to verify:
  - Insight model can be created and saved
  - Foreign key relationship to RawSignal works
  - JSONB competitor_analysis field accepts list of dicts
  - All indexes are created (relevance_score DESC, created_at DESC, raw_signal_id)

**Success Criteria**:
- ✓ Insight model exists with all required fields
- ✓ Migration runs successfully
- ✓ Relationship between Insight ↔ RawSignal works bidirectionally
- ✓ All tests pass

---

## Technical Context

### What Works
- ✅ **Phase 1.1 Complete**: Git repository initialized, project structure created, Python environment with `uv` and 173 packages
- ✅ **Phase 1.2 Complete**: PostgreSQL 16 (port 5433) and Redis 7 (port 6379) running in Docker, SQLAlchemy 2.0 async configured, database connection verified
- ✅ **Phase 1.3 Complete**: RawSignal database model created, Alembic migrations configured, Firecrawl client wrapper with retry logic, 3 scrapers implemented (Reddit, Product Hunt, Google Trends)
- ✅ **Phase 1.4 Complete**: Arq worker with 4 task functions, APScheduler integration with 6-hour intervals, Redis connection validated
- ✅ **Phase 1.5 Complete**: FastAPI application with 5 REST endpoints (/api/signals, /health), CORS middleware, lifespan management, Pydantic V2 schemas
- ✅ **Phase 1.6 Complete**: Environment configuration with 15 validated variables, Pydantic Settings loading, Redis URL parsing
- ✅ **Phase 1.7 Complete**: Pytest infrastructure with conftest fixtures, unit tests for scrapers, integration tests for API endpoints
- ✅ **Phase 1.8 Complete**: Comprehensive backend README.md with setup guide, API docs, troubleshooting, Docker services
- Documentation is complete and production-ready:
  - `project-brief.md`: Defines the three core loops (Collection → Analysis → Presentation)
  - `tech-stack.md`: Lists all technologies, libraries, and dependencies
  - `implementation-plan.md`: Provides step-by-step roadmap for all 3 phases
  - `backend/README.md`: Complete backend documentation with setup, API, troubleshooting

### Phase 2 Roadmap (5 Steps)

**2.1 Database Schema Extension** (Current)
- Create Insight model with foreign key to RawSignal
- Add indexes for relevance_score, created_at, raw_signal_id
- Alembic migration and testing

**2.2 AI Analyzer Agent Implementation** (Next)
- Create `backend/app/agents/analyzer.py` with PydanticAI agent
- Define InsightSchema and Competitor Pydantic models for structured output
- Implement `analyze_signal(raw_signal: RawSignal) -> Insight`
- Add prompt template for Claude 3.5 Sonnet:
  ```
  Analyze this market signal and extract:
  1. Problem Statement (clear articulation of the problem)
  2. Proposed Solution (the suggested approach)
  3. Market Size (Small/Medium/Large based on TAM)
  4. Relevance Score (0.0-1.0 based on signal strength)
  5. Top 3 Competitors (name, URL, description, market position)

  Signal: {raw_content}
  ```
- Add error handling with tenacity retry logic (3 attempts, exponential backoff)
- Fallback to GPT-4o on Claude rate limits

**2.3 Analysis Task Queue**
- Add `analyze_signals_task()` to `backend/app/worker.py`
- Batch processing: process 10 unprocessed signals at a time
- Mark signals as `processed=True` after analysis
- Update `backend/app/tasks/scheduler.py` to trigger analysis after scraping
- Run analysis every 6 hours (coupled with scraping)

**2.4 Insights API Endpoints**
- Create `backend/app/api/routes/insights.py` with 3 endpoints:
  - `GET /api/insights` - List insights (sorted by relevance_score DESC)
  - `GET /api/insights/{id}` - Get single insight with related raw signal
  - `GET /api/insights/daily-top` - Top 5 insights of the day
- Create Pydantic schemas in `backend/app/schemas/insight.py`:
  - `InsightResponse` (includes related raw signal data)
  - `InsightListResponse` (paginated with total count)
- Query params: `?min_score=0.7&limit=20&offset=0&source=reddit`

**2.5 Testing & Validation**
- Unit tests for AI agent (mocked LLM responses)
- Integration tests for full pipeline (scrape → analyze → retrieve)
- Manual testing on real scraped data
- Verify relevance scores and competitor analysis accuracy

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

## Phase 2 Prerequisites

Before starting Phase 2.1, verify:

**Environment**:
- [x] PostgreSQL 16 running on port 5433 (`docker ps | grep postgres`)
- [x] Redis running on port 6379 (`docker ps | grep redis`)
- [x] Phase 1 migrations applied (`uv run alembic current`)
- [x] FastAPI server can start (`uv run uvicorn app.main:app --reload`)

**Dependencies Required** (all verified and installed):
- [x] `pydantic-ai>=0.0.13` - AI agent framework ✓
- [x] `anthropic>=0.25.0` - Claude API client ✓
- [x] `openai>=1.12.0` - GPT-4o fallback ✓
- [x] `tenacity>=8.2.0` - Retry logic for LLM calls ✓

**API Keys Required** (.env file - documented in .env.example):
- [x] `ANTHROPIC_API_KEY` - Claude 3.5 Sonnet access (documented in .env.example)
  - **Action Required**: Get key from https://console.anthropic.com
  - **Location**: Line 35 in backend/.env.example
- [x] `OPENAI_API_KEY` - GPT-4o fallback (optional, documented)
  - **Action Required**: Get key from https://platform.openai.com (optional)
  - **Location**: Line 38 in backend/.env.example
- [x] `ANALYSIS_BATCH_SIZE=10` - Already configured (line 70)

**Verification Commands**:
```bash
# Check current Alembic version
cd backend && uv run alembic current

# Verify dependencies
uv run python -c "import pydantic_ai, anthropic, openai; print('All AI dependencies installed')"

# Test database connection
uv run python check_db_connection.py

# Verify raw signals exist
uv run python -c "
from app.db.session import AsyncSessionLocal
from app.models.raw_signal import RawSignal
from sqlalchemy import select
import asyncio

async def check():
    async with AsyncSessionLocal() as session:
        result = await session.execute(select(RawSignal).limit(1))
        signal = result.scalar_one_or_none()
        if signal:
            print(f'✓ Raw signals exist: {signal.source}')
        else:
            print('⚠ No raw signals yet - run scraping first')

asyncio.run(check())
"
```

## Current Blockers
**None** - Phase 1 complete. All prerequisites ready for Phase 2 implementation.

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
2. Refer to `implementation-plan.md` Phase 2.1 for detailed steps on Insight model creation
3. Update this file after completing each major milestone
4. Check `progress.md` to see completed work and avoid duplication
5. Phase 1 is fully complete - start with Phase 2.1 (Insight Model) when continuing

---

## Progress Tracking

### Phase 1 Progress: ✅ 100% Complete (8/8 steps)
- [x] 1.1 Project Initialization
- [x] 1.2 Database Setup
- [x] 1.3 Firecrawl Integration
- [x] 1.4 Task Queue Setup
- [x] 1.5 FastAPI Endpoints
- [x] 1.6 Environment & Configuration
- [x] 1.7 Testing & Validation
- [x] 1.8 Documentation

### Phase 2 Progress: 0% Complete (0/5 steps)
- [ ] 2.1 Database Model (Insight)
- [ ] 2.2 AI Analyzer Agent (PydanticAI)
- [ ] 2.3 Analysis Task Queue
- [ ] 2.4 Insights API Endpoints
- [ ] 2.5 Testing & Validation

---

**Last Updated**: 2026-01-18
**Updated By**: Lead Architect (Claude)
**Status**: Phase 1 complete (Data Collection Loop) - Ready for Phase 2 (Analysis Loop)
