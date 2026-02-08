"""Pytest configuration and fixtures for StartInsight backend tests.

Provides:
- Async test database session
- Test client for API endpoints
- Mock user fixtures
- Factory fixtures for models
"""

import asyncio
from collections.abc import AsyncGenerator, Generator
from datetime import datetime
from uuid import uuid4

import pytest
import pytest_asyncio
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient
from sqlalchemy import JSON
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import StaticPool

from app.db.base import Base
from app.db.session import get_db
from app.main import app
from app.models import (
    AdminUser,
    CustomAnalysis,
    Insight,
    RawSignal,
    SavedInsight,
    User,
)

# ============================================
# SQLite Compatibility for PostgreSQL types
# ============================================

# Register PostgreSQL types to use SQLite-compatible types
from sqlalchemy.dialects import sqlite
from sqlalchemy.dialects.postgresql import ARRAY
from sqlalchemy.ext.compiler import compiles
from sqlalchemy.types import TypeDecorator
import json

# Override JSONB to use TEXT for SQLite (SQLAlchemy's JSON handles serialization)
@compiles(JSONB, "sqlite")
def compile_jsonb_sqlite(element, compiler, **kw):
    return "TEXT"


# Create a custom ARRAY type for SQLite that serializes to JSON
class SQLiteArrayAdapter(TypeDecorator):
    """ARRAY type that works with SQLite by serializing to JSON."""

    impl = JSON
    cache_ok = True

    def process_bind_param(self, value, dialect):
        if value is None:
            return None
        return value  # Let JSON type handle serialization

    def process_result_value(self, value, dialect):
        if value is None:
            return None
        return value


# Override ARRAY compilation for SQLite
@compiles(ARRAY, "sqlite")
def compile_array_sqlite(element, compiler, **kw):
    return "TEXT"


# ============================================
# Database Fixtures
# ============================================

# Use in-memory SQLite for tests
TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"


@pytest.fixture(scope="session")
def event_loop() -> Generator[asyncio.AbstractEventLoop, None, None]:
    """Create event loop for async tests."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest_asyncio.fixture(scope="function")
async def test_engine():
    """Create test database engine."""
    engine = create_async_engine(
        TEST_DATABASE_URL,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
        echo=False,
    )

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    yield engine

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

    await engine.dispose()


@pytest_asyncio.fixture(scope="function")
async def db_session(test_engine) -> AsyncGenerator[AsyncSession, None]:
    """Create test database session."""
    async_session = async_sessionmaker(
        test_engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )

    async with async_session() as session:
        yield session
        await session.rollback()


# ============================================
# App and Client Fixtures
# ============================================


@pytest_asyncio.fixture(scope="function")
async def test_app(db_session: AsyncSession) -> FastAPI:
    """Create test FastAPI app with overridden dependencies."""

    async def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    yield app
    app.dependency_overrides.clear()


@pytest_asyncio.fixture(scope="function")
async def client(test_app: FastAPI) -> AsyncGenerator[AsyncClient, None]:
    """Create async test client."""
    async with AsyncClient(
        transport=ASGITransport(app=test_app),
        base_url="http://test",
    ) as ac:
        yield ac


# ============================================
# User Fixtures
# ============================================


@pytest_asyncio.fixture
async def test_user(db_session: AsyncSession) -> User:
    """Create a test user."""
    user = User(
        id=uuid4(),
        supabase_user_id=f"test-supabase-{uuid4()}",
        email=f"test-{uuid4()}@example.com",
        display_name="Test User",
        subscription_tier="free",
        preferences={"theme": "dark"},
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user


@pytest_asyncio.fixture
async def pro_user(db_session: AsyncSession) -> User:
    """Create a pro tier test user."""
    user = User(
        id=uuid4(),
        supabase_user_id=f"pro-supabase-{uuid4()}",
        email=f"pro-{uuid4()}@example.com",
        display_name="Pro User",
        subscription_tier="pro",
        preferences={},
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user


@pytest_asyncio.fixture
async def admin_user(db_session: AsyncSession, test_user: User) -> AdminUser:
    """Create an admin user."""
    admin = AdminUser(
        id=uuid4(),
        user_id=test_user.id,
        role="admin",
        permissions={"all": True},
    )
    db_session.add(admin)
    await db_session.commit()
    await db_session.refresh(admin)
    return admin


# ============================================
# Signal and Insight Fixtures
# ============================================


@pytest_asyncio.fixture
async def test_signal(db_session: AsyncSession) -> RawSignal:
    """Create a test raw signal."""
    signal = RawSignal(
        id=uuid4(),
        source="reddit",
        url="https://reddit.com/r/startups/test",
        content="Looking for a tool to automate my startup research process. "
        "Currently spending 20+ hours per week manually analyzing markets.",
        extra_metadata={"subreddit": "startups", "upvotes": 150, "title": "Need help with market research automation", "author": "test_author"},
    )
    db_session.add(signal)
    await db_session.commit()
    await db_session.refresh(signal)
    return signal


@pytest_asyncio.fixture
async def test_insight(db_session: AsyncSession, test_signal: RawSignal) -> Insight:
    """Create a test insight."""
    insight = Insight(
        id=uuid4(),
        raw_signal_id=test_signal.id,
        title="AI-Powered Market Research Platform",
        problem_statement="Founders spend 20+ hours weekly on manual market research",
        proposed_solution="Automated AI platform for real-time market intelligence",
        market_size_estimate="Large",
        relevance_score=0.85,
        competitor_analysis=[
            {"name": "CB Insights", "url": "https://cbinsights.com", "description": "Market intelligence"}
        ],
        # Enhanced scores (Phase 4.3)
        opportunity_score=8,
        problem_score=7,
        feasibility_score=6,
        why_now_score=8,
        revenue_potential="$$$",
        execution_difficulty=5,
        go_to_market_score=7,
        founder_fit_score=8,
    )
    db_session.add(insight)
    await db_session.commit()
    await db_session.refresh(insight)
    return insight


@pytest_asyncio.fixture
async def saved_insight(
    db_session: AsyncSession, test_user: User, test_insight: Insight
) -> SavedInsight:
    """Create a saved insight for test user."""
    saved = SavedInsight(
        id=uuid4(),
        user_id=test_user.id,
        insight_id=test_insight.id,
        notes="This looks promising!",
        tags=["ai", "research"],
        status="interested",
    )
    db_session.add(saved)
    await db_session.commit()
    await db_session.refresh(saved)
    return saved


# ============================================
# Research Analysis Fixtures
# ============================================


@pytest_asyncio.fixture
async def test_analysis(db_session: AsyncSession, test_user: User) -> CustomAnalysis:
    """Create a test custom analysis."""
    analysis = CustomAnalysis(
        id=uuid4(),
        user_id=test_user.id,
        idea_description="An AI platform that helps startups validate their ideas using market signals and competitor analysis",
        target_market="Early-stage founders and solopreneurs",
        budget_range="10k-50k",
        status="completed",
        progress_percent=100,
        opportunity_score=0.82,
        market_fit_score=0.75,
        execution_readiness=0.68,
        tokens_used=15000,
        analysis_cost_usd=1.25,
        completed_at=datetime.utcnow(),
    )
    db_session.add(analysis)
    await db_session.commit()
    await db_session.refresh(analysis)
    return analysis


# ============================================
# Auth Mock Fixtures
# ============================================


@pytest.fixture
def mock_auth_header(test_user: User) -> dict:
    """Create mock authorization header."""
    # In real tests, this would be a valid JWT
    return {"Authorization": f"Bearer mock-token-{test_user.id}"}


@pytest.fixture
def auth_override(test_user: User):
    """Override auth dependency to return test user."""
    from app.api.deps import get_current_user

    async def mock_get_current_user():
        return test_user

    return {get_current_user: mock_get_current_user}


# ============================================
# Aliases for backwards compatibility
# ============================================


@pytest_asyncio.fixture(scope="function")
async def async_db_session(db_session: AsyncSession) -> AsyncSession:
    """Alias for db_session for backwards compatibility."""
    return db_session
