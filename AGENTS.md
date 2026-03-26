# Claude Code Agents — StartInsight

This project uses specialized Claude Code sub-agents (`.claude/agents/`) to handle domain-specific tasks. Each agent has focused context and tooling optimized for its role.

## Available Agents

| Agent | When to Use |
|-------|-------------|
| `implementation-engineer` | Implement code changes from the implementation plan |
| `product-planner` | Convert strategist feedback → actionable tasks in `implementation-plan.md` |
| `product-strategist` | Audit StartInsight visuals vs competitors (IdeaBrowser), generate frontend feedback |
| `db-schema-architect` | SQLAlchemy model changes, Alembic migrations, query optimization |
| `testing-agent` | Write pytest tests for scrapers/endpoints after code changes |
| `scout-scraper` | Fetch/scrape external web content (Reddit, forums, RSS) into structured data |
| `api-docs-specialist` | Research external API docs, auth patterns, rate limits (PRAW, Firecrawl, etc.) |

## Agent Details

### `implementation-engineer`
Implements code changes based on `memory-bank/implementation-plan.md`. Use after planning is complete and a task is ready to code.

### `product-planner`
Translates high-level product strategy (from `/office-hours`, `/plan-ceo-review`, strategist reports) into concrete sub-phases in `implementation-plan.md`. Bridges business vision → engineering tasks.

### `product-strategist`
Visual quality auditor. Compares StartInsight UI/charts against IdeaBrowser and other competitors. Generates scored feedback for the frontend team. Use before product reviews or when evaluating design changes.

### `db-schema-architect`
Database specialist. Handles all SQLAlchemy 2.0 async model changes, Alembic migration generation (naming convention: `cNNN`), index optimization. Always reads `memory-bank/architecture.md` Section 5 before proposing schema changes.

### `testing-agent`
Test writer for backend code. Produces pytest tests with mocked external dependencies (PRAW, Firecrawl, Gemini). Use after implementing scrapers, FastAPI endpoints, or AI agents.

### `scout-scraper`
Web research agent. Fetches content from external sources (Product Hunt, Reddit, HN, competitor sites) and returns clean structured JSON. Do NOT use for local file reads or internal API calls.

### `api-docs-specialist`
API integration researcher. Looks up authentication patterns, rate limits, and error handling for third-party APIs (PRAW, Firecrawl, pytrends, Tweepy, Stripe, Resend). Use before implementing new integrations or when hitting API errors.

## Agent Configuration

Agent files live in `.claude/agents/`. Each file follows Claude Code's agent format with `name:`, `description:`, and `model:` frontmatter.

Current models in use:
- `sonnet` — `implementation-engineer`, `product-planner`, `product-strategist`
- `inherit` (inherits from parent session) — all others

## Related

- `memory-bank/implementation-plan.md` — Task list agents execute against
- `memory-bank/architecture.md` — System design all agents reference
- `CLAUDE.md` — Session-level guidelines that apply before any agent is invoked
