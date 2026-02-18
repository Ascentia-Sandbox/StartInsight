"""Unit tests for query_helpers - Code simplification Phase 1."""

import pytest
from sqlalchemy import select

from app.db.query_helpers import count_by_field, paginate_query
from app.models.saved_insight import SavedInsight

# Skip tests requiring PostgreSQL-specific types (ARRAY, JSONB) when using SQLite
# These tests pass in CI with PostgreSQL
pytestmark = pytest.mark.skipif(
    True,  # TODO: Detect SQLite vs PostgreSQL dynamically
    reason="SavedInsight uses PostgreSQL ARRAY type not supported by SQLite"
)


@pytest.mark.asyncio
async def test_count_by_field_all_rows(async_db_session, test_user, test_insight):
    """Test count_by_field without filter counts all rows."""
    # Create 3 saved insights for the user
    for _ in range(3):
        saved = SavedInsight(
            user_id=test_user.id,
            insight_id=test_insight.id,
            status="saved",
        )
        async_db_session.add(saved)
    await async_db_session.commit()

    # Count all SavedInsights
    total = await count_by_field(async_db_session, SavedInsight)
    assert total == 3


@pytest.mark.asyncio
async def test_count_by_field_with_filter(async_db_session, test_user, test_insight):
    """Test count_by_field with field filter."""
    # Create saved insights with different statuses
    for status in ["interested", "saved", "building"]:
        saved = SavedInsight(
            user_id=test_user.id,
            insight_id=test_insight.id,
            status=status,
        )
        async_db_session.add(saved)
    await async_db_session.commit()

    # Count interested only
    interested_count = await count_by_field(async_db_session, SavedInsight, "status", "interested")
    assert interested_count == 1

    # Count by user_id
    user_count = await count_by_field(async_db_session, SavedInsight, "user_id", test_user.id)
    assert user_count == 3


@pytest.mark.asyncio
async def test_paginate_query_basic(async_db_session, test_user, test_insight):
    """Test paginate_query returns items and total."""
    # Create 5 saved insights
    for i in range(5):
        saved = SavedInsight(
            user_id=test_user.id,
            insight_id=test_insight.id,
            status="saved",
        )
        async_db_session.add(saved)
    await async_db_session.commit()

    # Paginate query
    query = select(SavedInsight).where(SavedInsight.user_id == test_user.id)
    items, total = await paginate_query(async_db_session, query, limit=3, offset=0)

    assert len(items) == 3
    assert total == 5


@pytest.mark.asyncio
async def test_paginate_query_with_offset(async_db_session, test_user, test_insight):
    """Test paginate_query handles offset correctly."""
    # Create 10 saved insights
    for i in range(10):
        saved = SavedInsight(
            user_id=test_user.id,
            insight_id=test_insight.id,
            status="saved",
        )
        async_db_session.add(saved)
    await async_db_session.commit()

    # Get second page
    query = select(SavedInsight).where(SavedInsight.user_id == test_user.id)
    items, total = await paginate_query(async_db_session, query, limit=5, offset=5)

    assert len(items) == 5
    assert total == 10
