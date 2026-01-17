---
name: async-alchemy
description: Database guardrail - ensures no blocking I/O in FastAPI backend. Use when writing or modifying SQLAlchemy models or database operations.
---

# Async SQLAlchemy Standards (The Database Guardrail)

This skill prevents the most common performance degradation in AI-generated code: accidentally introducing blocking I/O.

## Trigger
Automatically applies when working on:
- `backend/app/models/` - SQLAlchemy model definitions
- `backend/app/db/` - Database sessions and operations

## Rules

### 1. Async-Only SQLAlchemy
- Use ONLY `sqlalchemy.ext.asyncio`
- Import from: `from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine`
- NEVER use synchronous `Session` or `Engine`

### 2. SQLAlchemy 2.0 Syntax
- Use `mapped_column()` syntax for column definitions
- Use `Mapped[Type]` for type hints
- Example:
  ```python
  from sqlalchemy.orm import Mapped, mapped_column

  class User(Base):
      id: Mapped[int] = mapped_column(primary_key=True)
      name: Mapped[str] = mapped_column(String(100))
  ```

### 3. Async Context Managers
- Every session must be yielded via `async with` block
- Example:
  ```python
  async def get_db() -> AsyncGenerator[AsyncSession, None]:
      async with async_session_maker() as session:
          yield session
  ```

### 4. Explicit Relationship Loading
- NEVER rely on lazy loading (causes async errors)
- Always use `selectinload()` or `joinedload()` for relationships
- Example:
  ```python
  from sqlalchemy.orm import selectinload

  stmt = select(User).options(selectinload(User.insights))
  result = await session.execute(stmt)
  ```

### 5. Query Execution
- Always use `await session.execute(stmt)` for queries
- Use `scalars()` for single entity queries
- Example:
  ```python
  result = await session.execute(select(User).where(User.id == user_id))
  user = result.scalars().first()
  ```

## Anti-Patterns to Avoid
- ❌ `session.query()` - use `select()` instead
- ❌ `obj.relationship` without explicit loading - will fail in async
- ❌ `def` functions with database operations - must be `async def`
- ❌ Synchronous engine creation - use `create_async_engine()`

## Checklist
Before committing any database code, verify:
- [ ] All imports are from `sqlalchemy.ext.asyncio`
- [ ] All functions are `async def`
- [ ] All queries use `await session.execute()`
- [ ] All relationships use explicit loading strategies
- [ ] Session lifecycle uses `async with` blocks
