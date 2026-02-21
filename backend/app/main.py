"""FastAPI application entry point."""

import logging
import os
import uuid
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from jwt.exceptions import InvalidTokenError
from slowapi.errors import RateLimitExceeded
from sqlalchemy.exc import IntegrityError, OperationalError
from starlette.middleware.base import BaseHTTPMiddleware

from app.core.config import settings
from app.core.rate_limits import limiter
from app.middleware.api_version import APIVersionMiddleware
from app.middleware.request_size_limit import RequestSizeLimitMiddleware
from app.middleware.security_headers import SecurityHeadersMiddleware
from app.tasks import schedule_scraping_tasks, stop_scheduler

# Sentry error tracking (production + staging)
if settings.sentry_dsn and settings.environment in ("production", "staging"):
    import logging as _logging

    import sentry_sdk
    from sentry_sdk.integrations.fastapi import FastApiIntegration
    from sentry_sdk.integrations.logging import LoggingIntegration
    from sentry_sdk.integrations.sqlalchemy import SqlalchemyIntegration

    sentry_sdk.init(
        dsn=settings.sentry_dsn,
        environment=settings.environment,
        release=os.environ.get("RAILWAY_GIT_COMMIT_SHA", "local"),
        traces_sample_rate=settings.sentry_traces_sample_rate,
        profiles_sample_rate=settings.sentry_profiles_sample_rate,
        enable_logs=True,
        integrations=[
            FastApiIntegration(transaction_style="url"),
            SqlalchemyIntegration(),
            LoggingIntegration(
                level=_logging.INFO,          # Breadcrumbs from INFO+
                event_level=_logging.ERROR,   # Sentry issues from ERROR+
                sentry_logs_level=_logging.WARNING,  # Sentry Logs tab from WARNING+
            ),
        ],
        before_send=lambda event, hint:
            None if event.get("request", {}).get("url", "").endswith("/health") else event,
    )

# Configure structured logging
from app.core.logging import setup_logging

setup_logging()

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Lifespan context manager for FastAPI startup and shutdown events.

    Handles:
    - Startup: Initialize task scheduler
    - Shutdown: Stop task scheduler, close DB pool, close Redis
    """
    # Startup
    logger.info(f"Starting StartInsight API v{settings.app_version} ({settings.environment})")

    # Initialize task scheduler
    try:
        await schedule_scraping_tasks()
        logger.info("Task scheduler initialized")
    except Exception as e:
        logger.error(f"Failed to initialize task scheduler: {e}")

    yield

    # Graceful shutdown
    logger.info("Initiating graceful shutdown...")

    # 1. Stop accepting new scheduled tasks
    try:
        await stop_scheduler()
        logger.info("Task scheduler stopped")
    except Exception as e:
        logger.error(f"Error stopping scheduler: {e}")

    # 2. Close Redis connections
    try:
        from app.core.cache import close_redis
        await close_redis()
        logger.info("Redis connections closed")
    except Exception as e:
        logger.error(f"Error closing Redis: {e}")

    # 3. Close database connection pool
    try:
        from app.db.session import close_db
        await close_db()
        logger.info("Database connections closed")
    except Exception as e:
        logger.error(f"Error closing database: {e}")

    logger.info("Shutdown complete")


# Create FastAPI application
app = FastAPI(
    title="StartInsight API",
    description="AI-powered business intelligence engine for startup idea discovery",
    version=settings.app_version,
    lifespan=lifespan,
    docs_url=None if settings.environment == "production" else "/docs",
    redoc_url=None if settings.environment == "production" else "/redoc",
)

# Request ID middleware for correlation (add BEFORE CORS)
class RequestIDMiddleware(BaseHTTPMiddleware):
    """Add X-Request-ID to all requests for log correlation."""

    async def dispatch(self, request: Request, call_next):
        # Generate or extract request ID
        request_id = request.headers.get("X-Request-ID") or str(uuid.uuid4())
        request.state.request_id = request_id

        # Process request
        response = await call_next(request)

        # Add request ID to response headers
        response.headers["X-Request-ID"] = request_id
        return response


from app.middleware.dlp_monitoring import DLPMonitoringMiddleware
from app.middleware.session_security import SessionSecurityMiddleware
from app.middleware.tracing import TracingMiddleware
from app.middleware.zero_trust_security import ZeroTrustSecurityMiddleware

app.add_middleware(TracingMiddleware)
app.add_middleware(RequestIDMiddleware)
app.add_middleware(ZeroTrustSecurityMiddleware)
app.add_middleware(DLPMonitoringMiddleware)
app.add_middleware(SessionSecurityMiddleware)

# Security headers and API version (BEFORE CORS)
app.add_middleware(SecurityHeadersMiddleware)
app.add_middleware(RequestSizeLimitMiddleware)
app.add_middleware(APIVersionMiddleware)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_origin_regex=settings.cors_origin_regex or None,
    allow_credentials=True,
    allow_methods=[m.strip() for m in settings.cors_allowed_methods.split(",")],
    allow_headers=[h.strip() for h in settings.cors_allowed_headers.split(",")],
)

# Register SlowAPI limiter (Phase 2: Code Simplification)
app.state.limiter = limiter

# Add rate limiting middleware for sensitive endpoints
from app.middleware.rate_limiter import RateLimiterMiddleware

app.add_middleware(RateLimiterMiddleware, max_requests=100, window_seconds=3600)


# ============================================================================
# Global Exception Handlers (Production Security)
# ============================================================================

@app.exception_handler(Exception)
async def generic_exception_handler(request: Request, exc: Exception):
    """
    Handle all unhandled exceptions (500 errors).
    Logs full error details but returns generic message to prevent information leakage.
    """
    logger.error(
        f"Unhandled exception: {exc}",
        extra={
            "path": request.url.path,
            "method": request.method,
            "error_type": type(exc).__name__
        },
        exc_info=True  # Includes stack trace in logs
    )

    # Send to Sentry if configured
    if settings.sentry_dsn:
        import sentry_sdk
        sentry_sdk.capture_exception(exc)

    # Return generic error (DO NOT expose implementation details)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "detail": "Internal server error. Our team has been notified.",
            "request_id": getattr(request.state, "request_id", None)
        }
    )


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """Handle Pydantic validation errors (422 errors)."""
    errors = []
    for error in exc.errors():
        errors.append({
            "field": ".".join(str(loc) for loc in error["loc"]),
            "message": error["msg"],
            "type": error["type"]
        })

    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "detail": "Validation error",
            "errors": errors
        }
    )


@app.exception_handler(IntegrityError)
async def integrity_error_handler(request: Request, exc: IntegrityError):
    """Handle database integrity errors (duplicate keys, constraint violations)."""
    logger.warning(f"Database integrity error: {exc.orig}", exc_info=True)

    # Parse error message to provide user-friendly feedback
    error_msg = str(exc.orig).lower()
    if "unique" in error_msg or "duplicate" in error_msg:
        detail = "A record with this information already exists"
    elif "foreign key" in error_msg:
        detail = "Referenced record not found"
    else:
        detail = "Database constraint violation"

    return JSONResponse(
        status_code=status.HTTP_409_CONFLICT,
        content={"detail": detail}
    )


@app.exception_handler(OperationalError)
async def operational_error_handler(request: Request, exc: OperationalError):
    """Handle database connection errors (503 errors)."""
    logger.error(f"Database operational error: {exc}", exc_info=True)

    if settings.sentry_dsn:
        import sentry_sdk
        sentry_sdk.capture_exception(exc)

    return JSONResponse(
        status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
        content={
            "detail": "Service temporarily unavailable. Please try again.",
            "request_id": getattr(request.state, "request_id", None)
        }
    )


@app.exception_handler(InvalidTokenError)
async def jwt_error_handler(request: Request, exc: InvalidTokenError):
    """Handle JWT authentication errors (401 errors)."""
    logger.warning(f"JWT error on {request.url.path}: {exc}")

    return JSONResponse(
        status_code=status.HTTP_401_UNAUTHORIZED,
        content={"detail": "Invalid or expired authentication token"}
    )


@app.exception_handler(RateLimitExceeded)
async def rate_limit_handler(request: Request, exc: RateLimitExceeded):
    """
    Handle rate limit exceeded errors from SlowAPI.

    Returns 429 Too Many Requests with retry-after header.
    """
    return JSONResponse(
        status_code=status.HTTP_429_TOO_MANY_REQUESTS,
        content={
            "error": "Rate limit exceeded",
            "detail": str(exc.detail),
        },
        headers=exc.headers or {},
    )


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
        "version": settings.app_version,
        "api_version": "v1",
    }


# Import and include routers
from app.api.routes import (  # noqa: E402
    admin,
    agent_control,
    analytics,
    api_keys,
    build,
    build_tools,
    chat,
    community,
    contact,
    content_review,
    export,
    feed,
    gamification,
    health,
    insights,
    integrations,
    market_insights,
    payments,
    pipeline,
    preferences,
    pulse,
    research,
    signals,
    success_stories,
    teams,
    tenants,
    tools,
    trends,
    users,
    validator,
)
from app.api.routes import (
    settings as settings_routes,
)

app.include_router(health.router, tags=["Health"])  # Production monitoring
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
app.include_router(content_review.router, tags=["Content Review"])  # Phase 8.1
app.include_router(pipeline.router, tags=["Pipeline Monitoring"])  # Phase 8.2
app.include_router(analytics.router, tags=["Analytics"])  # Phase 8.3
app.include_router(agent_control.router, tags=["Agent Control"])  # Phase 8.4-8.5
app.include_router(preferences.router, tags=["User Preferences"])  # Phase 9.1
app.include_router(preferences.email_router)  # CAN-SPAM unsubscribe
app.include_router(community.router, tags=["Community"])  # Phase 9.3
app.include_router(gamification.router, tags=["Gamification"])  # Phase 9.6
app.include_router(integrations.router, tags=["Integrations"])  # Phase 10
app.include_router(build.router, tags=["Builder Integration"])  # Phase 9.3
app.include_router(tools.router, tags=["Tools"])  # Phase 12.3
app.include_router(success_stories.router, tags=["Success Stories"])  # Phase 12.3
app.include_router(trends.router, tags=["Trends"])  # Phase 12.3
app.include_router(market_insights.router, tags=["Market Insights"])  # Phase 12.3
app.include_router(validator.router, tags=["Idea Validator"])  # Phase 19.1
app.include_router(chat.router, tags=["Chat Strategist"])  # Phase B
app.include_router(settings_routes.router, tags=["System Settings"])  # Phase G
app.include_router(pulse.router, tags=["Market Pulse"])  # Phase Q5.1
app.include_router(contact.router, tags=["Contact"])  # Phase Q6.3

# Static file serving for uploaded images (Phase 20.1)
os.makedirs("uploads/images", exist_ok=True)
app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")
