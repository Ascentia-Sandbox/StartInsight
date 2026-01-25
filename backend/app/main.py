"""FastAPI application entry point."""

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.tasks import schedule_scraping_tasks, stop_scheduler

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Lifespan context manager for FastAPI startup and shutdown events.

    Handles:
    - Startup: Initialize task scheduler
    - Shutdown: Stop task scheduler gracefully
    """
    # Startup
    logger.info("Starting StartInsight API")

    # Initialize task scheduler
    try:
        await schedule_scraping_tasks()
        logger.info("Task scheduler initialized")
    except Exception as e:
        logger.error(f"Failed to initialize task scheduler: {e}")

    yield

    # Shutdown
    logger.info("Shutting down StartInsight API")
    await stop_scheduler()


# Create FastAPI application
app = FastAPI(
    title="StartInsight API",
    description="AI-powered business intelligence engine for startup idea discovery",
    version="0.1.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health", tags=["Health"])
async def health_check():
    """
    Health check endpoint.

    Returns:
        Health status and service information
    """
    return {
        "status": "healthy",
        "service": "StartInsight API",
        "version": "0.1.0",
        "environment": settings.environment,
    }


@app.get("/", tags=["Root"])
async def root():
    """
    Root endpoint with API information.

    Returns:
        Welcome message and documentation links
    """
    return {
        "message": "Welcome to StartInsight API",
        "docs": "/docs",
        "health": "/health",
        "version": "0.1.0",
    }


# Import and include routers
from app.api.routes import (  # noqa: E402
    admin,
    api_keys,
    build_tools,
    export,
    feed,
    insights,
    payments,
    research,
    signals,
    teams,
    tenants,
    users,
)

app.include_router(signals.router, prefix="/api", tags=["Signals"])
app.include_router(insights.router, tags=["Insights"])
app.include_router(users.router, tags=["Users"])  # Phase 4.1
app.include_router(admin.router, tags=["Admin"])  # Phase 4.2
app.include_router(research.router, tags=["Research"])  # Phase 5.1
app.include_router(build_tools.router, tags=["Build Tools"])  # Phase 5.2
app.include_router(export.router, tags=["Export"])  # Phase 5.3
app.include_router(feed.router, tags=["Real-time Feed"])  # Phase 5.4
app.include_router(payments.router, tags=["Payments"])  # Phase 6.1
app.include_router(teams.router, tags=["Teams"])  # Phase 6.4
app.include_router(api_keys.router, tags=["API Keys"])  # Phase 7.2
app.include_router(tenants.router, tags=["Tenants"])  # Phase 7.3
