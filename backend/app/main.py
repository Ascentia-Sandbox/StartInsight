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
from app.api.routes import signals  # noqa: E402

app.include_router(signals.router, prefix="/api", tags=["Signals"])
