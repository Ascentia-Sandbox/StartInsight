# StartInsight Backend

FastAPI backend for StartInsight - an AI-powered business intelligence engine that discovers, validates, and presents data-driven startup ideas.

## Tech Stack

- **Framework**: FastAPI (async)
- **Language**: Python 3.11+
- **Database**: Supabase PostgreSQL (ap-southeast-2, Sydney)
- **ORM**: SQLAlchemy 2.0 (async mode)
- **Auth**: Supabase Auth (OAuth + email/password)
- **Task Queue**: Arq + Redis + APScheduler
- **Package Manager**: uv
- **Linter/Formatter**: Ruff
- **AI Framework**: PydanticAI + Gemini 2.0 Flash
- **Web Scraping**: Firecrawl, PRAW (Reddit), Tweepy (Twitter/X), pytrends (Google Trends), feedparser (RSS)
- **Services**: Stripe (payments), Resend (email), SlowAPI (rate limiting)

## Prerequisites

- Python 3.11+
- Docker Desktop (for Redis)
- uv package manager: `curl -LsSf https://astral.sh/uv/install.sh | sh`
- Supabase Pro account (database hosted on Supabase Cloud)

## Quick Start

### 1. Install Dependencies

```bash
# Install all dependencies
uv sync
```

### 2. Start Infrastructure

```bash
# Database: Supabase Pro (no local PostgreSQL needed)
# Start Redis from project root
cd ..
docker compose up -d

# Verify Redis is running
docker ps
# Should show: startinsight-redis (port 6379)
```

### 3. Environment Variables

```bash
# Copy example env file
cp .env.example .env

# Edit .env and add your API keys:
# Required:
# - DATABASE_URL (Supabase Pro connection string from Dashboard > Project Settings > Database)
# - REDIS_URL=redis://localhost:6379
# - FIRECRAWL_API_KEY (get from https://firecrawl.dev)
# - REDDIT_CLIENT_ID (create app at https://reddit.com/prefs/apps)
# - REDDIT_CLIENT_SECRET
# Optional:
# - ANTHROPIC_API_KEY (for Phase 2 AI analysis)
```

### 4. Run Database Migrations

```bash
# Migrations are already created, just run them
uv run alembic upgrade head
```

### 5. Run the Backend

```bash
# Development mode (with auto-reload and scheduler)
uv run uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

The API will be available at:
- **API**: http://localhost:8000
- **Swagger Docs**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

### 6. Run Background Worker (Optional)

For scraping tasks, start the Arq worker in a separate terminal:

```bash
# Start Arq worker
uv run arq app.worker.WorkerSettings
```

## Project Structure

```
backend/
├── app/
│   ├── main.py                    # FastAPI app entry point
│   ├── worker.py                  # Arq worker configuration
│   │
│   ├── core/                      # Core configuration
│   │   └── config.py              # Pydantic Settings
│   │
│   ├── db/                        # Database layer
│   │   ├── base.py                # SQLAlchemy declarative base
│   │   └── session.py             # Async session management
│   │
│   ├── models/                    # SQLAlchemy models
│   │   └── raw_signal.py          # RawSignal model (Phase 1)
│   │
│   ├── schemas/                   # Pydantic response schemas
│   │   └── signals.py             # Signal response models
│   │
│   ├── api/                       # API routes
│   │   └── routes/
│   │       └── signals.py         # /api/signals endpoints
│   │
│   ├── scrapers/                  # Web scraping logic
│   │   ├── base_scraper.py        # Abstract base scraper
│   │   ├── firecrawl_client.py    # Firecrawl wrapper
│   │   └── sources/
│   │       ├── reddit_scraper.py         # Reddit (r/startups, r/SaaS)
│   │       ├── product_hunt_scraper.py   # Product Hunt daily launches
│   │       └── trends_scraper.py         # Google Trends keywords
│   │
│   └── tasks/                     # Background tasks
│       └── scheduler.py           # APScheduler configuration
│
├── alembic/                       # Database migrations
│   ├── env.py                     # Async Alembic configuration
│   └── versions/                  # Migration files
│
├── tests/                         # Tests
│   ├── conftest.py                # Pytest fixtures
│   ├── test_scrapers.py           # Scraper unit tests
│   └── test_api.py                # API integration tests
│
├── .env.example                   # Example environment variables
├── pyproject.toml                 # Dependencies (managed by uv)
└── README.md                      # This file
```

## API Endpoints

**Total**: 105 endpoints across 9 route files

### Health & Info
- `GET /health` - Health check endpoint
- `GET /` - API information

### Signals (4 endpoints)
- `GET /api/signals` - List raw signals with pagination
- `GET /api/signals/{id}` - Get single signal by UUID
- `GET /api/signals/stats/summary` - Signal statistics
- `POST /api/signals/trigger-scraping` - Manually trigger scraping

### Insights (4 endpoints)
- `GET /api/insights` - List insights with filters (score, category, source)
- `GET /api/insights/{id}` - Get single insight by UUID
- `GET /api/insights/stats/summary` - Insight statistics
- `POST /api/insights/trigger-analysis` - Manually trigger analysis

### Users (18 endpoints)
- Authentication: signup, signin, signout, refresh, profile
- Workspace: saved insights, ratings, claims
- Preferences: notifications, settings

### Admin (13 endpoints)
- Dashboard: metrics, agent status/control (pause/resume/trigger)
- SSE streaming: real-time updates (5-second intervals)
- Review queue: moderate insights, manage users

### Research (12 endpoints)
- User: submit requests, view status, get results
- Admin: approval queue, approve/reject, manual trigger
- 40-step research agent with admin sovereignty

### Teams (15 endpoints)
- Team management: create, update, delete
- Member management: invite, remove, update roles
- Shared insights: share, unshare, permissions (RBAC)

### Payments (5 endpoints)
- Stripe checkout, subscription status, customer portal
- Webhook handling, payment history

### API Keys (8 endpoints)
- Create, list, revoke API keys
- Scoped permissions, usage tracking

### Tenants (11 endpoints)
- Multi-tenancy: subdomain routing, custom domains
- Tenant branding, settings, user management

### Export & Feed (11 endpoints)
- PDF/CSV/JSON exports with brand customization
- SSE real-time feed, build tools (brand/landing generators)

See `../memory-bank/architecture.md` for complete endpoint documentation.

### Example Request

```bash
# List all signals
curl http://localhost:8000/api/signals

# Filter by source
curl "http://localhost:8000/api/signals?source=reddit&limit=10"

# Get signal stats
curl http://localhost:8000/api/signals/stats/summary

# Trigger scraping manually
curl -X POST http://localhost:8000/api/signals/trigger-scraping
```

## Development Workflow

### Running Scrapers

Scrapers run automatically every 6 hours via the scheduler. To run manually:

```bash
# Option 1: Trigger via API
curl -X POST http://localhost:8000/api/signals/trigger-scraping

# Option 2: Run scraper directly in Python
uv run python -c "
import asyncio
from app.scrapers.sources import RedditScraper
from app.db.session import AsyncSessionLocal

async def test_scraper():
    scraper = RedditScraper()
    async with AsyncSessionLocal() as session:
        signals = await scraper.run(session)
        await session.commit()
        print(f'Saved {len(signals)} signals')

asyncio.run(test_scraper())
"
```

### Running Tests

```bash
# Run all tests
uv run pytest tests/ -v

# Run with coverage
uv run pytest --cov=app --cov-report=html tests/

# Run specific test file
uv run pytest tests/test_scrapers.py -v

# Run phase-specific tests
uv run python test_phase_1_4.py  # Task queue
uv run python test_phase_1_5.py  # API endpoints (requires running server)
uv run python test_phase_1_6.py  # Configuration
```

### Code Quality

```bash
# Format code
uv run ruff format .

# Lint code
uv run ruff check . --fix

# Type checking (if mypy is installed)
uv run mypy app/
```

### Database Management

```bash
# Create a new migration
uv run alembic revision --autogenerate -m "description"

# Run migrations
uv run alembic upgrade head

# Rollback one migration
uv run alembic downgrade -1

# View migration history
uv run alembic history

# Check database connection
uv run python check_db_connection.py
```

## Docker Services

The `docker-compose.yml` (in project root) provides Redis only. Database is hosted on **Supabase Pro**.

- **Redis 7**: Port **6379**
- **Redis Commander** (optional): Port **8081** - Redis GUI

### Using Optional Tools

```bash
# Start with optional GUI tools (from project root)
docker compose --profile tools up -d

# Access Redis Commander: http://localhost:8081
```

## Troubleshooting

### Database Connection Issues

```bash
# Database is hosted on Supabase Pro (no local PostgreSQL)
# Check your DATABASE_URL in .env points to Supabase

# Test connection from Python
uv run python check_db_connection.py

# Check Supabase connection pool
# Go to: Supabase Dashboard > Project Settings > Database > Connection Pooling
```

### Redis Connection Issues

```bash
# Test Redis connection
docker exec -it startinsight-redis redis-cli ping
# Should return: PONG

# View Redis logs
docker logs startinsight-redis
```

### Port Already in Use

```bash
# If port 8000 is in use, kill the process
lsof -ti:8000 | xargs kill -9

# Or use a different port
uv run uvicorn app.main:app --reload --port 8001
```

### Dependency Issues

```bash
# Clean install
rm -rf .venv
uv sync

# Update all dependencies
uv lock --upgrade
uv sync
```

### API Not Responding

```bash
# Check if FastAPI is running
curl http://localhost:8000/health

# View uvicorn logs (check terminal output)

# Ensure scheduler started (check logs for "Task scheduler initialized")
```

## Environment Variables Reference

See `.env.example` for all available environment variables.

### Required (Phase 1)
- `DATABASE_URL` - Supabase Pro PostgreSQL connection string
- `REDIS_URL` - Redis connection string
- `FIRECRAWL_API_KEY` - Firecrawl API key
- `REDDIT_CLIENT_ID` - Reddit OAuth app ID
- `REDDIT_CLIENT_SECRET` - Reddit OAuth secret

### Optional (Phase 2+)
- `ANTHROPIC_API_KEY` - Claude API key for AI analysis
- `OPENAI_API_KEY` - OpenAI API key (fallback)

### Configuration
- `SCRAPE_INTERVAL_HOURS` - Scraping frequency (default: 6)
- `ANALYSIS_BATCH_SIZE` - Batch size for analysis (default: 10)

## Development Status

### ✅ Phase 1-7 Complete (100%)

**Phase 1-3: MVP Foundation**
- ✅ Data collection: 7 scrapers (Reddit, Product Hunt, Google Trends, Hacker News, Twitter/X, RSS, custom)
- ✅ AI analysis: PydanticAI + Gemini 2.0 Flash (97% cost reduction)
- ✅ Database: 22 tables, 15 Supabase migrations, Row-Level Security
- ✅ API: 105 endpoints across 9 route files

**Phase 4: Authentication & Admin Portal**
- ✅ Supabase Auth integration (OAuth + email/password)
- ✅ Admin dashboard with SSE streaming (5-second updates)
- ✅ 8-dimension scoring (opportunity, problem, feasibility, why now, go-to-market, founder fit, execution difficulty, revenue potential)
- ✅ Workspace features: save, rate, claim insights

**Phase 5: AI Research Agent**
- ✅ 40-step research agent with comprehensive market analysis
- ✅ Admin approval queue (Free: manual, Starter/Pro/Enterprise: auto-approved)
- ✅ Brand generator, landing page generator
- ✅ PDF/CSV/JSON exports with customization
- ✅ SSE real-time feed

**Phase 6: Monetization**
- ✅ Stripe 4-tier subscriptions (Free, Starter $19/mo, Pro $49/mo, Enterprise $199/mo)
- ✅ Resend email integration (6 templates: welcome, digest, research results, payment receipts, team invitations, password reset)
- ✅ SlowAPI rate limiting with tier-based quotas
- ✅ Team collaboration: RBAC (owner/admin/member), shared insights

**Phase 7: Expansion**
- ✅ Twitter/X scraper (Tweepy integration)
- ✅ API key management: scoped permissions, usage tracking
- ✅ Multi-tenancy: subdomain routing, custom domains, tenant branding
- ✅ Advanced rate limiting and cost tracking

**Phase 5.2: Super Admin Sovereignty + Evidence Visualizations**
- ✅ Research request queue (admin approval system)
- ✅ Community signals radar chart (4-platform engagement)
- ✅ 8-dimension scoring KPI cards with color-coded badges
- ✅ Enhanced evidence panel with collapsible visualizations

### 🚀 Deployment Options

**For PMF Validation (<100 users, ~$30/month):**
- See [`docs/PMF-DEPLOYMENT.md`](docs/PMF-DEPLOYMENT.md) for minimal-cost deployment
- Uses: Railway Free ($5), Supabase Pro ($25), Resend Free, Crawl4AI (self-hosted)
- 94% cost reduction vs production config (~$30/mo vs $483/mo)

**For Production (>100 users, $300-500/month):**
- See [`../DEPLOYMENT-GUIDE.md`](../DEPLOYMENT-GUIDE.md) for full production setup
- Deploy backend to Railway Pro
- Deploy frontend to Vercel Pro
- Configure production environment variables
- Set up monitoring (Sentry, uptime checks)

### 🔧 Current Branch: SI-Claude-vllm

This branch is used for Claude vLLM integration testing.

See `../memory-bank/active-context.md` for deployment checklist and `../memory-bank/implementation-plan.md` for complete roadmap.

## Contributing

This project follows the "Glue Coding" philosophy:
- Use existing libraries and tools rather than building custom solutions
- Prioritize Firecrawl SDK over custom scrapers
- Ensure all database operations use async/await (SQLAlchemy 2.0)
- All AI agent outputs must be validated with Pydantic models

See `../CLAUDE.md` for development guidelines and `.claude/skills/` for code quality standards.

## License

MIT License - See LICENSE file for details.
