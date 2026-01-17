Tech Stack: StartInsight
1. High-Level Architecture
Architecture Type: Modular Monolith (separate Frontend/Backend repos or Monorepo)

Communication: REST API (FastAPI) + WebSockets (Real-time updates)

Deployment Strategy: Dockerized containers (Railway/Render)

2. Frontend (The Dashboard)
Framework: Next.js 14+ (App Router) - React production framework.

Language: TypeScript - Strict typing for reliability.

Styling: Tailwind CSS - Utility-first CSS.

UI Components: shadcn/ui - Copy-paste accessible components (based on Radix UI).

State Management: React Query (TanStack Query) - Server state management.

Charting: Recharts or Tremor - Data visualization for trend graphs.

3. Backend (The Intelligence Engine)
Framework: FastAPI - High-performance, async Python framework. Perfect for AI/IO-bound tasks.

Language: Python 3.11+

Process Manager: Uvicorn (ASGI server)

Validation: Pydantic V2 - Data validation and settings management.

4. Database & Storage (The Vault)
Primary Database: PostgreSQL - Robust relational database.

Local Dev: Docker container.

Production: Neon or Railway (Managed Postgres).

ORM: SQLAlchemy (Async) or Prisma Client Python - Type-safe database interaction.

Migrations: Alembic - Database schema version control.

Caching/Queue: Redis - Task queue for scheduled scrapers and caching hot insights.

5. AI & Data Pipeline (The "Vibe" Layer)

**LLM Agent Orchestration**
- **Primary Framework**: LangChain or PydanticAI
  - **LangChain** (if chosen):
    - `langchain-core`: Core abstractions and interfaces.
    - `langchain-openai` or `langchain-anthropic`: LLM provider integrations.
    - `langchain-community`: Additional integrations (Reddit API, etc.).
    - Use LCEL (LangChain Expression Language) for composable chains.
  - **PydanticAI** (if chosen):
    - Type-safe agent framework with built-in Pydantic validation.
    - Simpler API, better for structured output extraction.
    - Native async support.
- **✅ Decision (LOCKED)**: Use PydanticAI for MVP (Phases 1-3).
  - **Reason**: Simpler API, native Pydantic validation, adequate for single-agent analysis tasks.
  - **Migration Path**: If Phase 4+ requires complex multi-agent workflows or advanced tooling, evaluate LangChain migration at that time.
  - **Current Status**: PydanticAI installed (`pydantic-ai>=0.0.13` in `pyproject.toml`).

**LLM Provider**
- **Primary**: Anthropic Claude 3.5 Sonnet (via `anthropic` Python SDK)
  - Better at structured analysis and reasoning tasks.
  - Larger context window (200k tokens) for processing multiple signals at once.
- **Fallback**: OpenAI GPT-4o (via `openai` Python SDK)
  - Use for vision tasks (analyzing screenshots from Product Hunt).
- **Environment Variables**: Store API keys in `.env` files (never commit).

**Web Scraping & Data Extraction**
- **Primary Tool**: Firecrawl
  - **Library**: `firecrawl-py` (Official Python SDK)
  - **Purpose**: Convert web pages into clean, LLM-ready Markdown.
  - **Use Cases**:
    - Scraping Reddit threads (bypasses need for CSS selectors).
    - Extracting Product Hunt launches.
    - Reading blog posts and documentation.
  - **API**: Requires Firecrawl API key (cloud service).
- **Alternative/Supplementary**: Crawl4AI (self-hosted option)
  - Open-source, runs locally without API costs.
  - Trade-off: Requires more infrastructure setup.
- **Reddit-Specific**: `praw` (Python Reddit API Wrapper)
  - For structured Reddit data (scores, timestamps, subreddit metadata).
  - Complements Firecrawl by providing additional context.
- **Google Trends**: `pytrends` (Unofficial Google Trends API)
  - Extract search volume data for keywords.

**Task Scheduling & Queue**
- **Primary**: Arq (async task queue for Python)
  - Built on Redis, async-native (integrates perfectly with FastAPI).
  - Lighter than Celery, simpler setup.
- **Alternative**: Celery + Redis
  - More mature, better for complex workflows.
  - Use if we need advanced features (task retries, priority queues).

**Core Python Dependencies (Backend)**
```
# API Framework
fastapi>=0.109.0
uvicorn[standard]>=0.27.0
pydantic>=2.5.0
pydantic-settings>=2.1.0

# Database
sqlalchemy[asyncio]>=2.0.25
alembic>=1.13.0
asyncpg>=0.29.0  # Async PostgreSQL driver
redis>=5.0.1

# AI & Agents
pydantic-ai>=0.0.13  # or langchain-core, langchain-anthropic
anthropic>=0.25.0
openai>=1.12.0  # Fallback LLM

# Web Scraping
firecrawl-py>=0.0.16
praw>=7.7.1  # Reddit API
pytrends>=4.9.2  # Google Trends

# Task Queue
arq>=0.25.0

# Utilities
python-dotenv>=1.0.0  # Environment variables
httpx>=0.26.0  # Async HTTP client
```

**Core Frontend Dependencies (Next.js)**
```json
{
  "dependencies": {
    "next": "^14.1.0",
    "react": "^18.2.0",
    "react-dom": "^18.2.0",
    "@tanstack/react-query": "^5.20.0",
    "tailwindcss": "^3.4.0",
    "recharts": "^2.10.0",
    "date-fns": "^3.3.0",
    "zod": "^3.22.0"
  },
  "devDependencies": {
    "typescript": "^5.3.0",
    "@types/react": "^18.2.0",
    "@types/node": "^20.11.0",
    "eslint": "^8.56.0",
    "prettier": "^3.2.0"
  }
}
```

**Notes on Frontend Dependencies:**
- **`zod`**: Used for runtime type validation of API responses and form data. Ensures type safety between frontend TypeScript and backend Pydantic schemas.
- **`shadcn/ui`**: NOT listed in `package.json` because it's installed via CLI (`npx shadcn-ui@latest add button card badge`). Components are copied directly into your codebase (`/components/ui/`), not installed as an npm package. See Phase 3.1 in `implementation-plan.md` for installation instructions.

---

## Environment Variable Conventions

**Backend (Python with Pydantic Settings):**
- **File Format**: Use UPPERCASE names in `.env` files
- **Auto-Conversion**: Pydantic Settings automatically converts UPPERCASE → lowercase Python properties
- **Example**:
  ```bash
  # .env file
  DATABASE_URL=postgresql+asyncpg://user:pass@localhost:5433/startinsight
  REDIS_URL=redis://localhost:6379
  ANTHROPIC_API_KEY=sk-ant-...
  API_HOST=0.0.0.0
  API_PORT=8000
  ```
  ```python
  # backend/app/core/config.py (auto-mapped)
  from pydantic_settings import BaseSettings

  class Settings(BaseSettings):
      database_url: PostgresDsn  # Maps from DATABASE_URL
      redis_url: RedisDsn         # Maps from REDIS_URL
      anthropic_api_key: str      # Maps from ANTHROPIC_API_KEY
      api_host: str               # Maps from API_HOST
      api_port: int               # Maps from API_PORT

      class Config:
          env_file = ".env"
  ```
- **Convention**: Always use UPPERCASE in `.env` files, lowercase in Python code

**Frontend (Next.js):**
- **Public Variables**: Prefix with `NEXT_PUBLIC_` to expose to browser
- **Example**:
  ```bash
  # frontend/.env.local
  NEXT_PUBLIC_API_URL=http://localhost:8000
  ```
- **Access**: Use `process.env.NEXT_PUBLIC_API_URL` in client components

---

6. Development Tools
Package Manager:

Frontend: pnpm (Fast, disk-efficient package manager).

Backend: uv (Blazing-fast Python package manager) or poetry.

Linting/Formatting:

Frontend: ESLint + Prettier

Backend: Ruff (Fast Python linter/formatter).

Version Control: Git

Decision Records (Why we chose this)
Why FastAPI over Django? StartInsight is an AI-heavy app. We need excellent asynchronous support for scraping multiple sources and streaming LLM responses simultaneously. Django is too heavy and synchronous by default. FastAPI provides a lighter, faster "glue" layer for AI agents.

Why PostgreSQL over Supabase? To maintain vendor independence and control over our data layer. Running a standard Postgres container ensures we can host this anywhere (AWS, GCP, DigitalOcean) without being locked into a BaaS ecosystem.

Why Firecrawl? Writing custom CSS selectors for scraping is brittle (websites change). Firecrawl uses AI/Heuristics to turn web pages into Markdown, which is the native language of our LLM agents.
