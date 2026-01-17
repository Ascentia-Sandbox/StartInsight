# StartInsight - Claude Code Guidelines

## 📚 Memory Bank Protocol

### CRITICAL: Always Read These Files First
Before answering ANY complex question or starting ANY implementation task, you MUST read the relevant memory-bank files in this order:

1. **`memory-bank/project-brief.md`** (103 lines)
   - Purpose: Executive summary, business objectives, 3 core loops (Collect → Analyze → Present)
   - When to read: At the start of any new session, before proposing architectural changes

2. **`memory-bank/active-context.md`** (109 lines)
   - Purpose: Current phase, immediate tasks, blockers, what's working/what's next
   - When to read: Before every task to understand current state

3. **`memory-bank/implementation-plan.md`** (360 lines)
   - Purpose: Detailed 3-phase roadmap with step-by-step instructions
   - When to read: When planning implementation steps, checking phase requirements

4. **`memory-bank/architecture.md`** (769 lines)
   - Purpose: System architecture, data flows, UI/UX design, database schema, API endpoints
   - When to read: Before implementing features, designing database models, creating APIs

5. **`memory-bank/tech-stack.md`** (169 lines)
   - Purpose: Technology decisions, dependencies, library versions
   - When to read: When choosing libraries, verifying dependencies, resolving conflicts

6. **`memory-bank/progress.md`** (42 lines)
   - Purpose: Completed work log, upcoming tasks
   - When to read: After completing tasks (for logging), before starting work (to avoid duplication)

### Context-Based Reading Guide

| Scenario | Files to Read | Priority |
|----------|---------------|----------|
| **Starting a new session** | project-brief.md, active-context.md, progress.md | HIGH |
| **Implementing a feature** | active-context.md, implementation-plan.md, architecture.md | HIGH |
| **Database/model changes** | architecture.md (Database Schema section), tech-stack.md | CRITICAL |
| **API endpoint creation** | architecture.md (API Endpoints section), implementation-plan.md | CRITICAL |
| **Library selection** | tech-stack.md, project-brief.md (Glue Coding philosophy) | CRITICAL |
| **Debugging/questions** | All files (in reading order above) | MEDIUM |

### Rules
1. **No Hallucinations**: Do not assume libraries or patterns. Check `tech-stack.md` first.
2. **Update Always**: When a step is completed, append to `progress.md` using the Workflows format.
3. **Verify Current Phase**: Read `active-context.md` to confirm what phase you're in before starting work.
4. **Check Architecture**: Before creating models, APIs, or database changes, read the relevant sections in `architecture.md`.

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
- **Lint**: `cd backend && uv run ruff check . --fix`

## ?? Coding Style
- **Python**: Type hints required (Strict). Docstrings for agents.
- **Async**: ALL I/O must be `async/await`.
- **Error Handling**: Fail gracefully. AI Agents must handle API timeouts/retries.

## 🔄 Workflows
- **Progress Logging**: After every successful file modification or terminal execution, you must append a log entry to `memory-bank/progress.md` detailing what was changed and why. Use this format:
  ```
  - [DATE] [TASK_ID]: [Brief Description]
    - Files modified: [path/to/file]
    - Technical notes: [Key architectural decisions]
    - Status: [✓ Complete / ⚠️ Blocked]
  ```
- **Context Refresh**: Before logging to progress.md, re-read `active-context.md` to ensure your changes align with the current phase.
- **README.md Updates**: When creating a git commit, remember to update relevant README.md files to reflect changes:
  - `backend/README.md`: Update if backend entry points, setup instructions, or project structure changed
  - Root `README.md`: Update if overall project setup or architecture changed (when created)
  - Ensure instructions remain accurate and synchronized with actual code
