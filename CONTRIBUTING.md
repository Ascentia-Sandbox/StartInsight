# Contributing to StartInsight

## Quick Start

1. **Read the memory bank** before any change:
   - `memory-bank/project-brief.md` — what we're building and why
   - `memory-bank/active-context.md` — current state, recent work, what's next
   - `memory-bank/architecture.md` — before touching models, APIs, or DB schema

2. **Follow the tech stack** (see `CLAUDE.md` and `memory-bank/tech-stack.md`):
   - Backend: FastAPI async + SQLAlchemy 2.0 async + Pydantic V2 + `uv`
   - Frontend: Next.js 16 App Router + TypeScript + Tailwind CSS 4 + shadcn/ui
   - Database: PostgreSQL via Supabase (NO Supabase SDK — use SQLAlchemy directly)
   - AI: PydanticAI v1.x + Gemini 2.0 Flash

3. **Check the design system** (`DESIGN.md`) before any UI change.

---

## Branch Workflow

| Branch | Purpose | Deploys To |
|--------|---------|-----------|
| `main` | Production | startinsight.co + api.startinsight.co |
| `develop` | Staging | staging URLs |
| `feature/*` | Feature development | PR → develop |

```bash
git checkout develop
git checkout -b feature/my-feature
# ... make changes ...
git push origin feature/my-feature
# Open PR → develop
```

---

## Commit Messages

Conventional Commits format is **required** (used for auto-changelog):

```
<type>(<scope>): <short description>
```

| Type | When |
|------|------|
| `feat` | New feature |
| `fix` | Bug fix |
| `refactor` | Code change, no behaviour change |
| `test` | Adding/updating tests |
| `docs` | Documentation only |
| `chore` | Tooling, deps, config |
| `perf` | Performance improvement |
| `ci` | CI/CD pipeline changes |

Examples:
```
feat(insights): add save button API integration
fix(trends): remove hardcoded w-20 causing category truncation
fix(ci): resolve TS7006 implicit any in getSession
docs(memory-bank): update active-context for 2026-03-24 sprint
```

---

## Development Commands

```bash
# Backend
cd backend && uvicorn app.main:app --reload        # dev server
cd backend && pytest tests/ -v --cov=app           # tests (target: 35%+ coverage gate)
cd backend && uv run ruff check . --fix            # lint

# Frontend
cd frontend && npm run dev                         # dev server
cd frontend && npm run build                       # production build check
cd frontend && npx playwright test                 # E2E tests

# Database
cd backend && alembic upgrade head                 # run migrations
cd backend && alembic revision --autogenerate -m "cNNN_description"  # new migration
```

---

## Database Migration Naming

Migrations follow the `cNNN` convention (c001, c002, ... c016):

```bash
# Current head: c016
# Next migration: c017
alembic revision --autogenerate -m "c017_description"
```

⚠️ Never re-run migration `c006` (not idempotent).
⚠️ Migration `c008` (`purge_seed_data`) is irreversible — run staging first.

---

## AI Agent Development

All AI agents live in `backend/app/agents/`. Rules:

- Use PydanticAI v1.x API: `output_type=` and `result.output` (not `result_type`/`result.data`)
- Model string: `"google-gla:gemini-2.0-flash"` (hardcoded — no `settings.llm_model`)
- All agents must use `tenacity` retry for Gemini 429 errors (see `quality_reviewer.py`)
- Add `gen_ai.request` Sentry spans for observability (see `enhanced_analyzer.py`)

---

## Testing Standards

- **Coverage gate:** 35% enforced in CI (`--cov-fail-under=35`)
- **Flaky test handling:** `pytest-rerunfailures` with `--reruns 2`
- **Test isolation:** Unit tests must not require Postgres or Redis (use mocks)
- **Integration tests:** Run in a separate CI job with real services

---

## Automated Releases

Every push to `main` auto-creates a GitHub Release:
- Tag format: `v{YYYY}.{MM}.{DD}.{ci_run_number}` (e.g. `v2026.03.25.87`)
- Changelog: auto-generated from conventional commits since last tag

No manual action required.

---

## Code Review Checklist

Before opening a PR:
- [ ] `pytest tests/ -v --cov=app` passes with ≥35% coverage
- [ ] `uv run ruff check . --fix` clean
- [ ] `npm run build` succeeds (no TypeScript errors)
- [ ] All new API endpoints are async
- [ ] No Supabase SDK imports (use SQLAlchemy)
- [ ] `memory-bank/progress.md` updated (max 50-word entry)

---

## Getting Help

- `CLAUDE.md` — AI assistant guidelines and memory bank reading order
- `AGENTS.md` — Available Claude Code sub-agents and when to use them
- `memory-bank/architecture.md` — Full system design (endpoints, schema, auth)
- `memory-bank/tech-stack.md` — Exact dependency versions and decisions
