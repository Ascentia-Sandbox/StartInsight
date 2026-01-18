# Phase 2 Quick Reference Guide

**Status**: Ready to Start (Phase 1 Complete)
**Last Updated**: 2026-01-18

---

## Overview

**Phase 2: The "Analyzer" (Analysis Loop)**

Transform raw signals into structured, actionable insights using PydanticAI with Claude 3.5 Sonnet.

**High-Level Flow**:
```
Raw Signals (Phase 1)
    ↓
AI Analysis (PydanticAI + Claude 3.5 Sonnet)
    ↓
Structured Insights (problem, solution, competitors, score)
    ↓
API Endpoints (/api/insights)
    ↓
Frontend Dashboard (Phase 3)
```

---

## Phase 2 Checklist (5 Steps)

### ✅ Phase 2.1: Database Schema Extension
**Files to Create**:
- `backend/app/models/insight.py` - Insight SQLAlchemy model
- `backend/alembic/versions/XXX_create_insights_table.py` - Migration
- `backend/test_phase_2_1.py` - Tests

**Key Fields**:
```python
class Insight:
    id: UUID (PK)
    raw_signal_id: UUID (FK → raw_signals.id)
    problem_statement: TEXT
    proposed_solution: TEXT
    market_size_estimate: VARCHAR(20)  # "Small", "Medium", "Large"
    relevance_score: FLOAT  # 0.0 - 1.0
    competitor_analysis: JSONB  # List[Competitor]
    created_at: TIMESTAMP
```

**Relationships**:
- `Insight.raw_signal` → `RawSignal` (many-to-one)
- `RawSignal.insights` → `List[Insight]` (one-to-many)

**Indexes**:
- `idx_relevance_score` on `relevance_score DESC`
- `idx_created_at` on `created_at DESC`
- `idx_raw_signal_id` on `raw_signal_id`

**Commands**:
```bash
cd backend
uv run alembic revision --autogenerate -m "create insights table"
uv run alembic upgrade head
uv run python test_phase_2_1.py
```

---

### ⬜ Phase 2.2: AI Analyzer Agent
**Files to Create**:
- `backend/app/agents/__init__.py`
- `backend/app/agents/analyzer.py` - PydanticAI agent implementation
- `backend/test_phase_2_2.py` - Tests with mocked LLM

**Key Components**:

**1. Pydantic Schemas** (for structured output):
```python
from pydantic import BaseModel, HttpUrl, Field
from typing import Literal

class Competitor(BaseModel):
    """Individual competitor entry."""
    name: str = Field(description="Competitor company/product name")
    url: HttpUrl = Field(description="Competitor website URL")
    description: str = Field(description="Brief description of what they do")
    market_position: Literal["Small", "Medium", "Large"] | None = None

class InsightSchema(BaseModel):
    """Structured LLM output."""
    problem_statement: str = Field(description="Identified market problem")
    proposed_solution: str = Field(description="Suggested solution approach")
    market_size_estimate: Literal["Small", "Medium", "Large"] = Field(
        description="Market size: Small (<$100M TAM), Medium ($100M-$1B), Large (>$1B)"
    )
    relevance_score: float = Field(
        ge=0.0, le=1.0,
        description="Signal relevance (0.0=weak, 1.0=strong)"
    )
    competitor_analysis: list[Competitor] = Field(
        max_length=3,
        description="Top 3 competitors (if any)"
    )
    title: str = Field(description="Auto-generated insight title")
```

**2. PydanticAI Agent**:
```python
from pydantic_ai import Agent
from app.core.config import settings

agent = Agent(
    model="claude-3-5-sonnet-20241022",
    system_prompt="""You are a startup analyst extracting market insights from web content.

    Analyze the signal and identify:
    1. The core problem being discussed
    2. The proposed solution or opportunity
    3. Market size estimate (based on TAM indicators)
    4. Relevance score (signal strength, discussion quality)
    5. Up to 3 direct competitors

    Be concise but accurate. Focus on actionable insights.""",
    result_type=InsightSchema,
    api_key=settings.anthropic_api_key,
)

async def analyze_signal(raw_signal: RawSignal) -> Insight:
    """Analyze raw signal and return structured insight."""
    result = await agent.run(raw_signal.content)

    # Convert to database model
    insight = Insight(
        raw_signal_id=raw_signal.id,
        problem_statement=result.data.problem_statement,
        proposed_solution=result.data.proposed_solution,
        market_size_estimate=result.data.market_size_estimate,
        relevance_score=result.data.relevance_score,
        competitor_analysis=[c.model_dump() for c in result.data.competitor_analysis],
        title=result.data.title,
    )

    return insight
```

**3. Error Handling & Retry Logic**:
```python
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type
from pydantic import ValidationError
from anthropic import AnthropicError, RateLimitError
import logging

logger = logging.getLogger(__name__)

@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=1, max=10),
    retry=retry_if_exception_type((AnthropicError, ValidationError)),
    reraise=True
)
async def analyze_signal_with_retry(raw_signal: RawSignal) -> Insight:
    """Analyze with automatic retry on failures."""
    try:
        return await analyze_signal(raw_signal)
    except RateLimitError:
        logger.warning("Claude rate limit hit, falling back to GPT-4o")
        return await fallback_gpt4o_analysis(raw_signal)
    except ValidationError as e:
        logger.error(f"LLM returned invalid structure: {e}")
        raise
    except Exception as e:
        logger.error(f"Unexpected error analyzing signal {raw_signal.id}: {e}")
        raise
```

**Dependencies**:
```bash
uv add tenacity>=8.2.0
```

**Commands**:
```bash
cd backend
uv run python test_phase_2_2.py  # Test with mocked responses
```

---

### ⬜ Phase 2.3: Analysis Task Queue
**Files to Modify**:
- `backend/app/worker.py` - Add analyze_signals_task
- `backend/app/tasks/scheduler.py` - Schedule analysis after scraping
- `backend/test_phase_2_3.py` - Tests

**Tasks to Add**:
```python
# backend/app/worker.py

async def analyze_signals_task(ctx: dict) -> dict:
    """Analyze batch of unprocessed signals."""
    from app.db.session import AsyncSessionLocal
    from app.models.raw_signal import RawSignal
    from app.models.insight import Insight
    from app.agents.analyzer import analyze_signal_with_retry
    from sqlalchemy import select

    batch_size = settings.analysis_batch_size  # Default: 10

    async with AsyncSessionLocal() as session:
        # Get unprocessed signals
        result = await session.execute(
            select(RawSignal)
            .where(RawSignal.processed == False)
            .limit(batch_size)
        )
        signals = result.scalars().all()

        if not signals:
            logger.info("No unprocessed signals to analyze")
            return {"analyzed": 0}

        analyzed_count = 0
        for signal in signals:
            try:
                # Analyze signal
                insight = await analyze_signal_with_retry(signal)
                session.add(insight)

                # Mark as processed
                signal.processed = True

                analyzed_count += 1
                logger.info(f"Analyzed signal {signal.id}: {insight.title}")

            except Exception as e:
                logger.error(f"Failed to analyze signal {signal.id}: {e}")
                # Don't mark as processed - retry later

        await session.commit()

    return {"analyzed": analyzed_count, "total": len(signals)}

# Register in WorkerSettings
class WorkerSettings:
    functions = [
        scrape_reddit_task,
        scrape_product_hunt_task,
        scrape_trends_task,
        scrape_all_sources_task,
        analyze_signals_task,  # NEW
    ]
```

**Scheduler Update**:
```python
# backend/app/tasks/scheduler.py

async def schedule_analysis_tasks() -> None:
    """Schedule analysis task to run after scraping."""
    redis = await create_pool(RedisSettings(...))

    scheduler.add_job(
        func=redis.enqueue_job,
        args=("analyze_signals_task",),
        trigger=IntervalTrigger(hours=settings.scrape_interval_hours),
        id="analyze_signals",
        replace_existing=True,
    )

    logger.info("Analysis task scheduled")
```

**Commands**:
```bash
cd backend
uv run python test_phase_2_3.py
```

---

### ⬜ Phase 2.4: Insights API Endpoints
**Files to Create**:
- `backend/app/api/routes/insights.py` - Insights endpoints
- `backend/app/schemas/insight.py` - Response schemas
- `backend/test_phase_2_4.py` - API tests

**Endpoints**:

**1. List Insights** (`GET /api/insights`):
```python
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from app.db.session import get_db
from app.models.insight import Insight
from app.schemas.insight import InsightListResponse

router = APIRouter(prefix="/api/insights", tags=["insights"])

@router.get("", response_model=InsightListResponse)
async def list_insights(
    min_score: float = Query(0.0, ge=0.0, le=1.0),
    source: str | None = Query(None),
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db),
):
    """List insights with filtering and pagination."""
    query = select(Insight)

    # Filter by minimum score
    if min_score > 0.0:
        query = query.where(Insight.relevance_score >= min_score)

    # Filter by source (via raw_signal relationship)
    if source:
        query = query.join(Insight.raw_signal).where(RawSignal.source == source)

    # Sort by relevance score descending
    query = query.order_by(Insight.relevance_score.desc())

    # Pagination
    query = query.limit(limit).offset(offset)

    # Execute
    result = await db.execute(query)
    insights = result.scalars().all()

    # Get total count
    count_query = select(func.count(Insight.id))
    if min_score > 0.0:
        count_query = count_query.where(Insight.relevance_score >= min_score)
    total = await db.scalar(count_query)

    return InsightListResponse(
        insights=[InsightResponse.model_validate(i) for i in insights],
        total=total,
        limit=limit,
        offset=offset,
    )
```

**2. Get Single Insight** (`GET /api/insights/{id}`):
```python
@router.get("/{insight_id}", response_model=InsightResponse)
async def get_insight(
    insight_id: UUID,
    db: AsyncSession = Depends(get_db),
):
    """Get single insight with related raw signal."""
    query = select(Insight).where(Insight.id == insight_id)
    result = await db.execute(query)
    insight = result.scalar_one_or_none()

    if not insight:
        raise HTTPException(status_code=404, detail="Insight not found")

    return InsightResponse.model_validate(insight)
```

**3. Daily Top Insights** (`GET /api/insights/daily-top`):
```python
@router.get("/daily-top", response_model=list[InsightResponse])
async def get_daily_top(
    limit: int = Query(5, ge=1, le=20),
    db: AsyncSession = Depends(get_db),
):
    """Get top insights from last 24 hours."""
    from datetime import datetime, timedelta

    yesterday = datetime.utcnow() - timedelta(days=1)

    query = (
        select(Insight)
        .where(Insight.created_at >= yesterday)
        .order_by(Insight.relevance_score.desc())
        .limit(limit)
    )

    result = await db.execute(query)
    insights = result.scalars().all()

    return [InsightResponse.model_validate(i) for i in insights]
```

**Response Schemas**:
```python
# backend/app/schemas/insight.py

from pydantic import BaseModel, Field
from uuid import UUID
from datetime import datetime
from typing import Any

class CompetitorResponse(BaseModel):
    """Competitor data in API response."""
    name: str
    url: str
    description: str
    market_position: str | None = None

class InsightResponse(BaseModel):
    """Single insight response."""
    id: UUID
    raw_signal_id: UUID
    problem_statement: str
    proposed_solution: str
    market_size_estimate: str
    relevance_score: float = Field(ge=0.0, le=1.0)
    competitor_analysis: list[dict[str, Any]]  # List of competitors
    created_at: datetime

    # Include raw signal data (if needed)
    raw_signal: RawSignalResponse | None = None

    class Config:
        from_attributes = True

class InsightListResponse(BaseModel):
    """Paginated insights response."""
    insights: list[InsightResponse]
    total: int
    limit: int
    offset: int
```

**Commands**:
```bash
cd backend
uv run python test_phase_2_4.py  # Requires server running
```

---

### ⬜ Phase 2.5: Testing & Validation
**Files to Create**:
- `backend/test_phase_2_5_integration.py` - Full pipeline test
- `backend/tests/test_agents.py` - Agent unit tests

**Test Coverage**:
1. **Unit Tests** (mocked LLM):
   - Test InsightSchema validation
   - Test Competitor schema validation
   - Test analyze_signal with mocked agent response
   - Test error handling and retry logic

2. **Integration Tests**:
   - Run full pipeline: scrape → analyze → retrieve
   - Verify insights are correctly linked to raw signals
   - Test filtering by min_score and source
   - Test pagination

3. **Manual Testing**:
   - Run analysis on real scraped data
   - Verify relevance scores are reasonable (0.5-0.9 range)
   - Check competitor analysis accuracy
   - Inspect LLM token usage and costs

**Commands**:
```bash
cd backend

# Run all Phase 2 tests
uv run pytest test_phase_2_*.py -v

# Run full pytest suite
uv run pytest tests/ -v

# Manual integration test
uv run python test_phase_2_5_integration.py
```

---

## Environment Variables

Add to `backend/.env`:

```bash
# Required for Phase 2
ANTHROPIC_API_KEY=sk-ant-...  # Get from https://console.anthropic.com
OPENAI_API_KEY=sk-...          # Optional, for GPT-4o fallback

# Analysis Configuration
ANALYSIS_BATCH_SIZE=10         # Number of signals to analyze per batch
```

Update `backend/app/core/config.py`:
```python
class Settings(BaseSettings):
    # ... existing fields ...

    # Phase 2: AI Analysis
    anthropic_api_key: str = Field(..., description="Anthropic API key for Claude")
    openai_api_key: str | None = Field(None, description="OpenAI API key (fallback)")
    analysis_batch_size: int = Field(10, description="Signals per batch")
```

---

## Success Criteria (Phase 2 Complete)

- [x] Insight model created with all required fields
- [x] AI agent extracts structured insights from raw signals
- [x] Analysis task runs automatically every 6 hours
- [x] API endpoints return paginated, filterable insights
- [x] Integration tests pass for full pipeline
- [x] Manual testing confirms reasonable relevance scores
- [x] All Phase 2 tests pass (test_phase_2_*.py)

**Expected Outcome**:
Raw signals are automatically analyzed and converted into structured insights with problem statements, solutions, market sizing, relevance scores, and competitor analysis. Insights are accessible via REST API endpoints, ready for frontend consumption in Phase 3.

---

## Quick Commands Reference

```bash
# Phase 2.1: Database
cd backend
uv run alembic revision --autogenerate -m "create insights table"
uv run alembic upgrade head
uv run python test_phase_2_1.py

# Phase 2.2: AI Agent
uv add tenacity>=8.2.0
uv run python test_phase_2_2.py

# Phase 2.3: Task Queue
uv run python test_phase_2_3.py

# Phase 2.4: API Endpoints
uv run uvicorn app.main:app --reload  # Start server
uv run python test_phase_2_4.py

# Phase 2.5: Integration Tests
uv run pytest test_phase_2_*.py -v
uv run python test_phase_2_5_integration.py

# Run all tests
uv run pytest tests/ -v --cov=app

# Check API docs
# Visit http://localhost:8000/docs
```

---

**Last Updated**: 2026-01-18
**Status**: Phase 1 Complete - Ready for Phase 2.1
**Next Step**: Create Insight database model
