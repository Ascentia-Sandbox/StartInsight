# StartInsight

> **AI-Powered Business Intelligence Engine for Startup Idea Discovery**

StartInsight is a daily, automated intelligence platform that discovers, validates, and presents data-driven startup ideas by analyzing real-time market signals from social discussions, search trends, and product launches.

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.109+-00C7B7.svg)](https://fastapi.tiangolo.com)
[![Next.js 14+](https://img.shields.io/badge/Next.js-14+-black.svg)](https://nextjs.org)

---

## 🎯 What is StartInsight?

Unlike traditional brainstorming tools, StartInsight relies on **real-time market signals** to identify genuine market gaps and consumer pain points. The system operates on an automated **"Collect → Analyze → Present"** loop, functioning as an analyst that never sleeps.

### Core Philosophy

- **Signal over Noise**: Surface problems real people are complaining about or searching for
- **Data-Driven Intuition**: Every insight backed by source data (Reddit threads, search trends)
- **Automated Intelligence**: AI agents handle market research, leaving users with high-level decision-making

---

## ✨ Features

### Current (Phase 1 MVP)

- **Automated Data Collection**: Scrapes Reddit, Product Hunt, and Google Trends every 6 hours
- **AI-Powered Analysis**: Claude 3.5 Sonnet transforms raw signals into structured insights
- **Structured Insights**: Problem statements, market scores, competitor analysis, source attribution
- **PostgreSQL + Redis**: Robust data storage with task queue management

### Planned (Phase 2-4)

- **Visual Dashboard**: Next.js interface with top insights, trend graphs, and filters
- **Daily Digest**: Top 5 insights presented daily with deep-dive capabilities
- **Advanced Sources**: Twitter/X, Hacker News, custom RSS feeds
- **User Customization**: Track specific keywords, niches, or industries

---

## 🏗️ Architecture

```mermaid
graph LR
    A[Reddit/PH/Trends] -->|Firecrawl| B[Arq Worker]
    B -->|Raw Signals| C[(PostgreSQL)]
    C -->|Unprocessed| D[Claude 3.5]
    D -->|Insights| C
    C -->|API| E[FastAPI]
    E -->|JSON| F[Next.js Dashboard]
    G[Redis] -.->|Queue| B
```

### The Three Core Loops

1. **Loop 1: Data Collection** (Every 6 hours)
   - Scrapes content using Firecrawl (markdown format)
   - Stores raw signals in PostgreSQL with metadata

2. **Loop 2: Analysis** (After each collection)
   - Claude 3.5 Sonnet processes unprocessed signals
   - Validates output with Pydantic schemas
   - Scores relevance and market potential

3. **Loop 3: Presentation** (On-demand)
   - FastAPI serves ranked insights via REST
   - Next.js dashboard displays top insights

---

## 🛠️ Tech Stack

### Backend
- **Framework**: FastAPI (async-first)
- **Language**: Python 3.11+
- **Database**: PostgreSQL 16+ (AsyncPG driver)
- **ORM**: SQLAlchemy 2.0 (async)
- **Queue**: Redis + Arq (async task queue)
- **AI**: PydanticAI + Claude 3.5 Sonnet

### Frontend
- **Framework**: Next.js 14+ (App Router)
- **Language**: TypeScript
- **Styling**: Tailwind CSS
- **Components**: shadcn/ui
- **State**: TanStack Query (React Query)

### Data Pipeline
- **Scraping**: Firecrawl (web → markdown)
- **Reddit**: PRAW (Python Reddit API Wrapper)
- **Trends**: pytrends (Google Trends API)

### DevOps
- **Containers**: Docker + Docker Compose
- **Package Managers**: `uv` (Python), `pnpm` (Node.js)
- **Migrations**: Alembic
- **Linting**: Ruff (Python), ESLint + Prettier (TypeScript)

---

## 🚀 Quick Start

### Prerequisites

- **Python 3.11+**
- **Node.js 18+**
- **Docker & Docker Compose**
- **uv** (Python package manager): `curl -LsSf https://astral.sh/uv/install.sh | sh`
- **pnpm**: `npm install -g pnpm`

### 1. Clone the Repository

```bash
git clone https://github.com/Ascentia-Sandbox/StartInsight.git
cd StartInsight
```

### 2. Environment Setup

**Backend (.env)**:
```bash
cd backend
cp .env.example .env
```

Edit `backend/.env`:
```bash
DATABASE_URL=postgresql+asyncpg://startinsight:startinsight_dev_password@localhost:5433/startinsight
REDIS_URL=redis://localhost:6379
ANTHROPIC_API_KEY=your_claude_api_key_here
FIRECRAWL_API_KEY=your_firecrawl_api_key_here
API_HOST=0.0.0.0
API_PORT=8000
```

**Frontend (.env.local)**:
```bash
cd ../frontend
cp .env.example .env.local
```

Edit `frontend/.env.local`:
```bash
NEXT_PUBLIC_API_URL=http://localhost:8000
```

### 3. Start Infrastructure (PostgreSQL + Redis)

```bash
# From project root
docker-compose up -d
```

Verify containers are running:
```bash
docker ps
# Should show: startinsight-postgres, startinsight-redis
```

### 4. Initialize Database

```bash
cd backend

# Install dependencies
uv sync

# Run database setup
uv run python check_db_connection.py

# Run migrations
uv run alembic upgrade head
```

### 5. Start Backend

```bash
# From backend/ directory
uv run uvicorn app.main:app --reload
```

Backend runs at: **http://localhost:8000**
- API docs: http://localhost:8000/docs
- Health check: http://localhost:8000/health

### 6. Start Frontend (Phase 3)

```bash
# From frontend/ directory
pnpm install
pnpm dev
```

Frontend runs at: **http://localhost:3000**

---

## 📁 Project Structure

```
StartInsight/
├── backend/                    # FastAPI application
│   ├── app/
│   │   ├── core/              # Config, errors, dependencies
│   │   ├── db/                # Database session, base classes
│   │   ├── models/            # SQLAlchemy models
│   │   ├── schemas/           # Pydantic schemas
│   │   ├── api/               # API routes
│   │   ├── agents/            # AI agent definitions
│   │   ├── scrapers/          # Data collection modules
│   │   └── main.py            # FastAPI entry point
│   ├── alembic/               # Database migrations
│   ├── tests/                 # Pytest test suite
│   ├── pyproject.toml         # Python dependencies (uv)
│   └── README.md              # Backend-specific docs
│
├── frontend/                   # Next.js application (Phase 3)
│   ├── app/                   # Next.js 14+ App Router
│   ├── components/            # React components
│   ├── lib/                   # Utilities & API client
│   └── package.json           # Node dependencies
│
├── memory-bank/               # Project documentation
│   ├── project-brief.md       # Executive summary
│   ├── active-context.md      # Current phase & tasks
│   ├── implementation-plan.md # 3-phase roadmap
│   ├── architecture.md        # System design
│   ├── tech-stack.md          # Technology decisions
│   └── progress.md            # Development log
│
├── .claude/                   # Claude Code configuration
│   ├── agents/                # Custom Claude agents
│   └── skills/                # Code quality standards
│
├── docker-compose.yml         # PostgreSQL + Redis setup
├── CLAUDE.md                  # Claude Code guidelines
└── README.md                  # This file
```

---

## 🔄 Development Workflow

### Common Commands

```bash
# Backend Development
cd backend && uv run uvicorn app.main:app --reload

# Frontend Development
cd frontend && pnpm dev

# Database Migrations
cd backend && uv run alembic upgrade head

# Run Tests
cd backend && uv run pytest

# Lint & Format
cd backend && uv run ruff check . --fix
cd frontend && pnpm lint --fix
```

### Database Utilities

```bash
# Check database connection
uv run python backend/check_db_connection.py

# Create new migration
cd backend && uv run alembic revision --autogenerate -m "description"

# View migration history
cd backend && uv run alembic history

# Rollback migration
cd backend && uv run alembic downgrade -1
```

### Docker Management

```bash
# Start services
docker-compose up -d

# Stop services
docker-compose down

# View logs
docker-compose logs -f postgres
docker-compose logs -f redis

# Reset database (⚠️ destroys data)
docker-compose down -v
docker-compose up -d
```

---

## 📚 Documentation

Comprehensive documentation is maintained in the `memory-bank/` directory:

| File | Purpose |
|------|---------|
| **[project-brief.md](memory-bank/project-brief.md)** | Executive summary, business objectives, core philosophy |
| **[active-context.md](memory-bank/active-context.md)** | Current phase, immediate tasks, blockers |
| **[implementation-plan.md](memory-bank/implementation-plan.md)** | Step-by-step 3-phase roadmap |
| **[architecture.md](memory-bank/architecture.md)** | System design, data flows, database schema, API endpoints |
| **[tech-stack.md](memory-bank/tech-stack.md)** | Technology decisions, dependencies, library versions |
| **[progress.md](memory-bank/progress.md)** | Development log, completed tasks |

---

## 🧪 Testing

```bash
# Run all tests
cd backend && uv run pytest

# Run with coverage
uv run pytest --cov=app --cov-report=html

# Run specific test file
uv run pytest tests/test_scrapers.py

# Run with verbose output
uv run pytest -v
```

---

## 🤝 Contributing

This is a private development project. If you have access:

1. **Read Documentation First**: Check `memory-bank/active-context.md` for current phase
2. **Follow Coding Standards**: See `.claude/skills/` for quality guidelines
3. **Update Progress**: Log changes to `memory-bank/progress.md`
4. **Use Conventional Commits**: `feat:`, `fix:`, `docs:`, `chore:`

### Code Quality Standards

The project enforces 4 core skills via Claude Code:

- **async-alchemy**: Prevents blocking I/O in FastAPI/SQLAlchemy
- **firecrawl-glue**: Enforces Firecrawl SDK over brittle scrapers
- **pydantic-validator**: Ensures structured AI agent outputs
- **vibe-protocol**: Automates documentation synchronization

---

## 🔑 API Keys Required

| Service | Purpose | Get Key |
|---------|---------|---------|
| **Anthropic** | Claude 3.5 Sonnet (AI analysis) | [console.anthropic.com](https://console.anthropic.com) |
| **Firecrawl** | Web scraping (web → markdown) | [firecrawl.dev](https://firecrawl.dev) |
| **Reddit** | Reddit API (PRAW) | [reddit.com/prefs/apps](https://reddit.com/prefs/apps) |

Store keys in `backend/.env` (never commit `.env` files).

---

## 📊 Current Status

**Active Phase**: Phase 1 - Data Collection & Storage (Foundation)

**Completed**:
- ✅ Project structure setup
- ✅ PostgreSQL + Redis Docker configuration
- ✅ FastAPI backend foundation
- ✅ Database models and migrations
- ✅ Claude Code skills and agents

**In Progress**:
- 🔄 Reddit scraper implementation
- 🔄 Firecrawl integration
- 🔄 AI analysis pipeline

**Next**:
- ⏳ Product Hunt scraper
- ⏳ Google Trends integration
- ⏳ Arq task queue setup

See `memory-bank/active-context.md` for detailed status.

---

## 📄 License

MIT License - See [LICENSE](LICENSE) file for details.

---

## 🙏 Acknowledgments

- **FastAPI**: For the excellent async Python framework
- **Anthropic**: For Claude 3.5 Sonnet (the AI powering insights)
- **Firecrawl**: For making web scraping sane again
- **Next.js**: For the best React production framework

---

## 📞 Support

For questions or issues:
- Check `memory-bank/` documentation
- Review `backend/README.md` for backend-specific help
- See `CLAUDE.md` for development guidelines

---

**Built with the "Glue Coding" philosophy: Don't reinvent, integrate.**
