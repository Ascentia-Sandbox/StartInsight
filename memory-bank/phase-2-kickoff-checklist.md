# Phase 2 Kickoff Checklist

**Date**: 2026-01-18
**Status**: Ready to Start
**Prerequisites**: All ✓

---

## Pre-Implementation Verification

### Environment ✓
- [x] PostgreSQL 16 running on port 5433
- [x] Redis running on port 6379
- [x] Phase 1 migrations applied (raw_signals table exists)
- [x] FastAPI server can start successfully

### Dependencies ✓
- [x] `pydantic-ai>=0.0.13` installed
- [x] `anthropic>=0.25.0` installed
- [x] `openai>=1.12.0` installed
- [x] `tenacity>=8.2.0` installed

### Configuration ⚠️
- [x] `.env.example` has ANTHROPIC_API_KEY documented
- [x] `.env.example` has OPENAI_API_KEY documented
- [x] `.env.example` has ANALYSIS_BATCH_SIZE=10
- [ ] **ACTION REQUIRED**: Add actual ANTHROPIC_API_KEY to `.env` file
  - Get from: https://console.anthropic.com
- [ ] **OPTIONAL**: Add actual OPENAI_API_KEY to `.env` file (for fallback)
  - Get from: https://platform.openai.com

### Documentation ✓
- [x] `memory-bank/active-context.md` updated with Phase 2 focus
- [x] `memory-bank/phase-2-reference.md` created (comprehensive guide)
- [x] `memory-bank/progress.md` updated with Phase 2 prep entry
- [x] All Phase 2 implementation details documented

---

## Phase 2.1: Database Schema Extension

### Tasks
- [ ] Create `backend/app/models/insight.py`
  - Use template from `phase-2-reference.md`
  - Include all fields: id, raw_signal_id, problem_statement, proposed_solution, market_size_estimate, relevance_score, competitor_analysis, created_at
  - Add relationship: `raw_signal: Mapped["RawSignal"]`

- [ ] Update `backend/app/models/raw_signal.py`
  - Add reverse relationship: `insights: Mapped[list["Insight"]]`

- [ ] Update `backend/app/models/__init__.py`
  - Import Insight model for Alembic auto-discovery

- [ ] Create Alembic migration
  ```bash
  cd backend
  uv run alembic revision --autogenerate -m "create insights table"
  ```

- [ ] Review migration file
  - Verify all indexes created (relevance_score DESC, created_at DESC, raw_signal_id)
  - Verify foreign key constraint to raw_signals.id
  - Verify JSONB type for competitor_analysis

- [ ] Run migration
  ```bash
  uv run alembic upgrade head
  ```

- [ ] Create `backend/test_phase_2_1.py`
  - Test: Insight model can be created and saved
  - Test: Foreign key relationship works
  - Test: JSONB competitor_analysis accepts list of dicts
  - Test: All indexes exist
  - Test: Bidirectional relationship (Insight.raw_signal, RawSignal.insights)

- [ ] Run tests
  ```bash
  uv run python test_phase_2_1.py
  ```

### Success Criteria
- [ ] All tests pass
- [ ] Migration applies successfully
- [ ] Database schema matches architecture.md specification
- [ ] Relationships work bidirectionally

---

## Phase 2.2: AI Analyzer Agent

### Tasks
- [ ] Create `backend/app/agents/__init__.py`

- [ ] Create `backend/app/agents/analyzer.py`
  - Define Competitor Pydantic model
  - Define InsightSchema Pydantic model
  - Create PydanticAI agent with Claude 3.5 Sonnet
  - Implement `analyze_signal(raw_signal: RawSignal) -> Insight`
  - Add error handling with tenacity retry logic
  - Add fallback to GPT-4o on rate limits
  - Add logging for all LLM interactions

- [ ] Create `backend/test_phase_2_2.py`
  - Mock LLM responses
  - Test InsightSchema validation
  - Test Competitor schema validation
  - Test analyze_signal with mocked agent
  - Test error handling and retry logic

- [ ] Run tests
  ```bash
  uv run python test_phase_2_2.py
  ```

### Success Criteria
- [ ] Agent extracts structured insights from raw text
- [ ] Pydantic validation works correctly
- [ ] Retry logic handles API failures
- [ ] All tests pass

---

## Phase 2.3: Analysis Task Queue

### Tasks
- [ ] Update `backend/app/worker.py`
  - Add `analyze_signals_task()` function
  - Implement batch processing (10 signals at a time)
  - Mark signals as processed=True after analysis
  - Add task to WorkerSettings.functions

- [ ] Update `backend/app/tasks/scheduler.py`
  - Add `schedule_analysis_tasks()` function
  - Schedule analysis to run every 6 hours (after scraping)

- [ ] Update `backend/app/main.py`
  - Call `schedule_analysis_tasks()` in lifespan startup

- [ ] Create `backend/test_phase_2_3.py`
  - Test analyze_signals_task with mocked signals
  - Test batch processing logic
  - Test processed flag update
  - Test scheduler configuration

- [ ] Run tests
  ```bash
  uv run python test_phase_2_3.py
  ```

### Success Criteria
- [ ] Analysis task runs successfully
- [ ] Signals are marked as processed
- [ ] Scheduler triggers analysis automatically
- [ ] All tests pass

---

## Phase 2.4: Insights API Endpoints

### Tasks
- [ ] Create `backend/app/schemas/insight.py`
  - Define CompetitorResponse model
  - Define InsightResponse model
  - Define InsightListResponse model (paginated)

- [ ] Create `backend/app/api/routes/insights.py`
  - Implement `GET /api/insights` (list with filtering)
  - Implement `GET /api/insights/{id}` (single insight)
  - Implement `GET /api/insights/daily-top` (top 5 of day)

- [ ] Update `backend/app/main.py`
  - Register insights router

- [ ] Create `backend/test_phase_2_4.py`
  - Test list endpoint with pagination
  - Test filtering by min_score and source
  - Test get by ID endpoint
  - Test daily-top endpoint
  - Test 404 handling

- [ ] Run tests
  ```bash
  # Start server first
  uv run uvicorn app.main:app --reload

  # In another terminal
  uv run python test_phase_2_4.py
  ```

### Success Criteria
- [ ] All endpoints return correct data
- [ ] Pagination works correctly
- [ ] Filtering works correctly
- [ ] All tests pass

---

## Phase 2.5: Testing & Validation

### Tasks
- [ ] Create `backend/tests/test_agents.py`
  - Unit tests for analyzer agent
  - Mock LLM responses
  - Test all error cases

- [ ] Create `backend/test_phase_2_5_integration.py`
  - Test full pipeline: scrape → analyze → retrieve
  - Verify insights linked to raw signals
  - Test with real data

- [ ] Run all Phase 2 tests
  ```bash
  uv run pytest test_phase_2_*.py -v
  ```

- [ ] Run full test suite
  ```bash
  uv run pytest tests/ -v --cov=app
  ```

- [ ] Manual testing
  - Trigger scraping manually
  - Wait for analysis to run
  - Check /api/insights endpoint
  - Verify relevance scores are reasonable
  - Inspect competitor analysis accuracy

### Success Criteria
- [ ] All unit tests pass
- [ ] All integration tests pass
- [ ] Full pipeline works end-to-end
- [ ] Manual testing confirms quality
- [ ] Test coverage > 80%

---

## Post-Implementation Tasks

- [ ] Update `backend/README.md` with Phase 2 endpoints
  - Document `/api/insights` endpoints
  - Add example curl commands
  - Update development status section

- [ ] Update `memory-bank/progress.md`
  - Add Phase 2 completion entries
  - Document technical decisions
  - Note any blockers or issues

- [ ] Update `memory-bank/active-context.md`
  - Mark Phase 2 as complete
  - Update progress tracking (5/5 steps)
  - Set focus to Phase 3 (Frontend)

- [ ] Commit and push all changes
  ```bash
  git add .
  git commit -m "feat: Complete Phase 2 - Analysis Loop"
  git push origin main
  ```

---

## Quick Reference Commands

```bash
# Phase 2.1
cd backend
uv run alembic revision --autogenerate -m "create insights table"
uv run alembic upgrade head
uv run python test_phase_2_1.py

# Phase 2.2
uv run python test_phase_2_2.py

# Phase 2.3
uv run python test_phase_2_3.py

# Phase 2.4 (requires running server)
uv run uvicorn app.main:app --reload  # Terminal 1
uv run python test_phase_2_4.py       # Terminal 2

# Phase 2.5
uv run pytest test_phase_2_*.py -v
uv run pytest tests/ -v --cov=app

# Full pipeline test
uv run python test_phase_2_5_integration.py
```

---

## Notes

- **API Keys**: Remember to add actual ANTHROPIC_API_KEY to `.env` before Phase 2.2
- **Cost Tracking**: Monitor LLM usage in logs (PydanticAI logs token counts)
- **Rate Limits**: Claude has rate limits - fallback to GPT-4o is configured
- **Batch Size**: ANALYSIS_BATCH_SIZE=10 is conservative, can increase after testing

---

**Last Updated**: 2026-01-18
**Ready to Start**: ✅ Yes
**First Step**: Phase 2.1 - Create Insight database model
