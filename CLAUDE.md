# StartInsight - Claude Code Guidelines

## ?? Memory Bank Protocol
1. **Context First**: Before answering complex questions, ALWAYS read `memory-bank/active-context.md` and `memory-bank/implementation-plan.md`.
2. **Update Always**: When a step is completed, you must ask to update `memory-bank/progress.md`.
3. **No Hallucinations**: Do not assume libraries. Check `memory-bank/tech-stack.md`.

## ?? Glue Coding Philosophy
- **Don't Reinvent**: If a standard library or tool exists (e.g., `firecrawl-py`, `pydantic-ai`), use it.
- **Copy-Paste Standard**: Use standard "wheels" (templates) for setup.
- **Simplicity**: Prefer "Glue Code" (connecting APIs) over complex custom logic.

## ??? Tech Stack Rules (Strict)
- **Backend**: FastAPI (Async), SQLAlchemy 2.0 (Async), Pydantic V2, `uv` or `poetry`. **NO Django.**
- **Frontend**: Next.js 14+ (App Router), TypeScript, Tailwind CSS, shadcn/ui.
- **Database**: PostgreSQL (AsyncPG). **NO Supabase SDK** (use standard SQL/Alchemy).
- **AI**: PydanticAI or LangChain. **LLM**: Claude 3.5 Sonnet.
- **Scraper**: Firecrawl (Official SDK).

## ? Common Commands
- **Backend Dev**: `cd backend && uvicorn app.main:app --reload`
- **Frontend Dev**: `cd frontend && pnpm dev`
- **DB Migrations**: `alembic upgrade head`
- **Test**: `pytest`

## ?? Coding Style
- **Python**: Type hints required (Strict). Docstrings for agents.
- **Async**: ALL I/O must be `async/await`.
- **Error Handling**: Fail gracefully. AI Agents must handle API timeouts/retries.
