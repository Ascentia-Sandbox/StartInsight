# StartInsight Backend

FastAPI backend for StartInsight - an AI-powered business intelligence engine that discovers, validates, and presents data-driven startup ideas.

## Tech Stack

- **Framework**: FastAPI (async)
- **Language**: Python 3.11+
- **Database**: PostgreSQL (AsyncPG driver)
- **ORM**: SQLAlchemy 2.0 (async mode)
- **Task Queue**: Arq (Redis-based)
- **Package Manager**: uv
- **Linter/Formatter**: Ruff
- **Type Checker**: mypy

## Prerequisites

- Python 3.11+
- Docker Desktop (for PostgreSQL and Redis)
- uv package manager (`pip install uv`)

## Setup Instructions

### 1. Install Dependencies

```bash
# Install dependencies using uv
uv sync

# Or install with dev dependencies
uv sync --all-extras
```

### 2. Start Infrastructure (Docker)

```bash
# Start PostgreSQL and Redis
docker-compose up -d

# Verify containers are running
docker ps

# View logs
docker-compose logs -f
```

### 3. Environment Variables

```bash
# Copy example env file
cp .env.example .env

# Edit .env and add your API keys
# Required for Phase 1:
# - DATABASE_URL
# - REDIS_URL
# - FIRECRAWL_API_KEY
# - REDDIT_CLIENT_ID
# - REDDIT_CLIENT_SECRET
```

### 4. Database Migrations

```bash
# Initialize Alembic (only needed once)
alembic init alembic

# Create a migration
alembic revision -m "Create raw_signals table"

# Run migrations
alembic upgrade head
```

### 5. Run the Backend

```bash
# Development mode (with auto-reload)
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Or using the default settings
python -m uvicorn app.main:app --reload
```

### 6. Run the Worker (Background Tasks)

```bash
# Start the Arq worker
arq app.worker.WorkerSettings
```

## Project Structure

```
backend/
├── app/
│   ├── __init__.py
│   ├── main.py                # FastAPI app entry point
│   ├── config.py              # Environment configuration
│   ├── database.py            # Database connection
│   ├── worker.py              # Arq worker settings
│   │
│   ├── models/                # SQLAlchemy models
│   │   ├── raw_signal.py
│   │   └── insight.py
│   │
│   ├── schemas/               # Pydantic schemas
│   │   ├── raw_signal.py
│   │   └── insight.py
│   │
│   ├── api/                   # API routes
│   │   └── routes/
│   │       ├── signals.py
│   │       └── insights.py
│   │
│   ├── scrapers/              # Web scraping logic
│   │   ├── firecrawl_client.py
│   │   └── sources/
│   │       ├── reddit_scraper.py
│   │       ├── product_hunt_scraper.py
│   │       └── trends_scraper.py
│   │
│   ├── agents/                # AI agents
│   │   └── analyzer.py
│   │
│   ├── tasks/                 # Background tasks
│   │   ├── scraping_tasks.py
│   │   └── analysis_tasks.py
│   │
│   └── monitoring/            # Metrics & logging
│       └── metrics.py
│
├── alembic/                   # Database migrations
├── tests/                     # Unit & integration tests
├── .env.example               # Example environment variables
├── pyproject.toml             # Project dependencies
└── README.md                  # This file
```

## Development Workflow

### Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=app tests/

# Run specific test file
pytest tests/test_scrapers.py
```

### Code Quality

```bash
# Format code
ruff format .

# Lint code
ruff check .

# Type checking
mypy app/
```

## API Documentation

Once the server is running, visit:

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

## Available Endpoints (Phase 1)

### Health
- `GET /health` - Health check

### Raw Signals
- `GET /api/signals` - List raw signals (paginated)
- `GET /api/signals/{id}` - Get single raw signal

## Docker Services

The `docker-compose.yml` provides:

- **PostgreSQL**: Port 5432
- **Redis**: Port 6379
- **pgAdmin** (optional): Port 5050 - Database GUI
- **Redis Commander** (optional): Port 8081 - Redis GUI

### Using Optional Tools

```bash
# Start with optional GUI tools
docker-compose --profile tools up -d

# Access pgAdmin: http://localhost:5050
# Access Redis Commander: http://localhost:8081
```

## Troubleshooting

### Database Connection Issues

```bash
# Check if PostgreSQL is running
docker-compose ps postgres

# View PostgreSQL logs
docker-compose logs postgres

# Restart PostgreSQL
docker-compose restart postgres
```

### Redis Connection Issues

```bash
# Test Redis connection
docker exec -it startinsight-redis redis-cli ping
# Should return: PONG
```

### Dependency Issues

```bash
# Clean install
rm -rf .venv
uv sync --all-extras
```

## Next Steps

After completing Phase 1.1 (Project Initialization), proceed to:

1. **Phase 1.2**: Database Setup - Create SQLAlchemy models and migrations
2. **Phase 1.3**: Firecrawl Integration - Build web scrapers
3. **Phase 1.4**: Task Queue Setup - Implement background tasks
4. **Phase 1.5**: FastAPI Endpoints - Create REST API

See `memory-bank/implementation-plan.md` for detailed roadmap.
