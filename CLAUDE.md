# StartInsight - Claude Code Guidelines

## 📚 Memory Bank Protocol

### CRITICAL: Always Read These Files First
Before answering ANY complex question or starting ANY implementation task, you MUST read the relevant memory-bank files in this order:

1. **`memory-bank/project-brief.md`** (582 lines)
   - Purpose: Executive summary, business objectives, 3 core loops, competitive positioning vs IdeaBrowser
   - When to read: At the start of any new session, before proposing architectural changes

2. **`memory-bank/active-context.md`** (742 lines)
   - Purpose: Current phase (Phase 1-10 complete, production ready), immediate tasks, testing status, what's working/next
   - When to read: Before every task to understand current state

3. **`memory-bank/implementation-plan.md`** (572 lines)
   - Purpose: Phases 1-10 completion status, testing requirements (291 backend + 47 E2E), decision records (DR-001 to DR-005)
   - When to read: When planning implementation steps, checking phase requirements

4. **`memory-bank/architecture.md`** (2,118 lines)
   - Purpose: System architecture, 69 tables, 230 API endpoints, SSE architecture, authentication, admin portal, Phase 8-10 features
   - When to read: Before implementing features, designing database models, creating APIs

5. **`memory-bank/tech-stack.md`** (1,197 lines)
   - Purpose: Phase 1-10 dependencies, cost analysis ($294/mo at 10K users), revenue projections ($59K MRR at 10K users)
   - When to read: When choosing libraries, verifying dependencies, resolving conflicts, cost planning

6. **`memory-bank/progress.md`** (707 lines, updated 2026-02-08)
   - Purpose: Completion log (Phase 1-10 complete, production ready), recent changes, historical milestones
   - When to read: After completing tasks (for logging), before starting work (to avoid duplication)

### Context-Based Reading Guide

| Scenario | Files to Read | Priority |
|----------|---------------|----------|
| **Starting a new session** | project-brief.md, active-context.md, progress.md | HIGH |
| **Implementing a feature** | active-context.md, implementation-plan.md, architecture.md | HIGH |
| **Database/model changes** | architecture.md (Database Schema section), tech-stack.md | CRITICAL |
| **API endpoint creation** | architecture.md (API Endpoints section), implementation-plan.md | CRITICAL |
| **Library selection** | tech-stack.md, project-brief.md (Glue Coding philosophy) | CRITICAL |
| **Implementing Phase 8-10 features** | active-context.md, implementation-plan.md (Phase 8-10), architecture.md (Phase 8-10 sections) | CRITICAL |
| **Authentication/Admin setup** | architecture.md (Authentication Architecture, Admin Portal), implementation-plan.md (Phase 4.1-4.2) | CRITICAL |
| **Cost/pricing planning** | tech-stack.md (Cost Analysis), project-brief.md (Competitive Positioning) | HIGH |
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
- **Backend**: FastAPI (Async), SQLAlchemy 2.0 (Async), Pydantic V2, `uv` package manager. **NO Django.**
- **Frontend**: Next.js 14+ (App Router), TypeScript, Tailwind CSS, shadcn/ui.
- **Database**: PostgreSQL (AsyncPG). **NO Supabase SDK** (use standard SQL/Alchemy).
- **AI**: PydanticAI v1.x (standard). **LLM**: Gemini 2.0 Flash (primary), Claude 3.5 Sonnet (fallback).
- **Scraper**: Firecrawl (Official SDK).

## ? Common Commands
- **Backend Dev**: `cd backend && uvicorn app.main:app --reload`
- **Frontend Dev**: `cd frontend && npm run dev`
- **DB Migrations**: `cd backend && alembic upgrade head`
- **Backend Tests**: `cd backend && pytest tests/ -v --cov=app`
- **Frontend E2E Tests**: `cd frontend && npx playwright test`
- **Lint**: `cd backend && uv run ruff check . --fix`

## ?? Coding Style
- **Python**: Type hints required (Strict). Docstrings for agents.
- **Async**: ALL I/O must be `async/await`.
- **Error Handling**: Fail gracefully. AI Agents must handle API timeouts/retries.

## 🔄 Workflows

### Progress Logging Protocol

**When:** After every file modification or terminal execution
**Format:** Direct and Straightforward (max 50 words per entry)

```
- [YYYY-MM-DD] [TASK-ID]: Short description (max 10 words)
  - Files: file1.ext, file2.ext (max 5)
  - Tech: ONE sentence (max 15 words)
  - Status: [✓ Complete / ⚠️ Blocked / → In Progress]
```

**Rules:**
1. **Be Concise**: Max 50 words total per entry
2. **No Redundancy**: Don't repeat architecture.md or tech-stack.md
3. **Outcome-Focused**: Log WHAT shipped, not HOW
4. **Reference External Docs**: For complex analyses, create separate .md files
5. **One Sentence Tech Note**: Max 15 words describing key decision

**Examples:**

✅ **GOOD** (32 words):
```
- [2026-01-25] [PHASE-6.1]: Payment integration with Stripe
  - Files: services/payment.py, models/subscription.py
  - Tech: 4-tier pricing with webhook-based subscription management
  - Status: [✓ Complete]
```

❌ **BAD** (200+ words):
```
- [2026-01-25] [PHASE-6.1]: Complete Phase 6.1 Payment Integration
  - Files modified:
    - backend/app/services/payment.py (NEW)
    - backend/app/models/subscription.py (NEW)
    - [lists 15 files...]
  - Technical notes: Implemented comprehensive Stripe payment
    integration with 4 pricing tiers... [continues for 150+ words]
```

**Anti-Patterns (Avoid):**
- Listing every file modified (max 5)
- Explaining implementation details from architecture.md
- Multi-paragraph "how we built it" stories
- Duplicating tech-stack.md dependency lists

**Context Refresh:** Re-read active-context.md before logging

**Strategic Analyses:** For 10K+ word docs, create memory-bank/*.md and log ONE-LINE reference

### README.md Updates
When creating git commits, update relevant README.md files:
- `backend/README.md`: If backend entry points or setup changed
- Root `README.md`: If overall project setup changed

## 🏷️ Release & Versioning Standard

### Automated Releases
Every push to `main` auto-creates a GitHub Release via `.github/workflows/release.yml`:
- **Tag format:** `v{YYYY}.{MM}.{DD}.{ci_run_number}` (e.g. `v2026.02.20.42`)
- **Changelog:** Auto-generated from commits since last tag
- No manual action required — happens after every merge/push to main

### Commit Message Standard (Conventional Commits — REQUIRED)
```
<type>(<scope>): <short description>
```
Types: `feat` | `fix` | `docs` | `refactor` | `test` | `chore` | `ci` | `perf`

Examples:
- `feat(insights): add save button API integration`
- `fix(trends): remove hardcoded w-20 causing category truncation`
- `fix(ci): resolve TS7006 implicit any in getSession`

### Rules
1. Every merge to `main` MUST produce a GitHub Release with a descriptive changelog
2. Commit messages MUST follow conventional commits (enforced by clarity, not lint — yet)
3. Breaking changes: prefix with `BREAKING CHANGE:` in commit body

