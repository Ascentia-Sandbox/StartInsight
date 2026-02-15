"""Structured logging with correlation IDs for observability.

Sprint 2.3: Provides structured JSON logging with:
- Correlation IDs for request tracing
- Contextual logging (user_id, request_path, etc.)
- JSON format for log aggregation (ELK, Datadog, etc.)
- Performance timing helpers
"""

import json
import logging
import time
import uuid
from contextvars import ContextVar
from functools import wraps

from app.core.config import settings

# Context variable for correlation ID
correlation_id_var: ContextVar[str] = ContextVar("correlation_id", default="")
request_context_var: ContextVar[dict] = ContextVar("request_context", default={})


class JSONFormatter(logging.Formatter):
    """JSON log formatter for structured logging."""

    def format(self, record: logging.LogRecord) -> str:
        log_data = {
            "timestamp": self.formatTime(record, self.datefmt),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "correlation_id": correlation_id_var.get(""),
        }

        # Add request context if available
        request_ctx = request_context_var.get({})
        if request_ctx:
            log_data["request"] = request_ctx

        # Add extra fields from record
        if hasattr(record, "extra_data"):
            log_data.update(record.extra_data)

        # Add exception info if present
        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)

        # Add source location for debugging
        if settings.environment == "development":
            log_data["source"] = {
                "file": record.filename,
                "line": record.lineno,
                "function": record.funcName,
            }

        return json.dumps(log_data)


class StructuredLogger:
    """Logger with structured data support."""

    def __init__(self, name: str):
        self.logger = logging.getLogger(name)

    def _log(self, level: int, message: str, **extra) -> None:
        """Log with extra structured data."""
        record = self.logger.makeRecord(
            self.logger.name,
            level,
            "",
            0,
            message,
            (),
            None,
        )
        record.extra_data = extra
        self.logger.handle(record)

    def debug(self, message: str, **extra) -> None:
        self._log(logging.DEBUG, message, **extra)

    def info(self, message: str, **extra) -> None:
        self._log(logging.INFO, message, **extra)

    def warning(self, message: str, **extra) -> None:
        self._log(logging.WARNING, message, **extra)

    def error(self, message: str, **extra) -> None:
        self._log(logging.ERROR, message, **extra)

    def critical(self, message: str, **extra) -> None:
        self._log(logging.CRITICAL, message, **extra)


def get_logger(name: str) -> StructuredLogger:
    """Get a structured logger instance."""
    return StructuredLogger(name)


def generate_correlation_id() -> str:
    """Generate a new correlation ID."""
    return str(uuid.uuid4())[:8]


def set_correlation_id(correlation_id: str) -> None:
    """Set correlation ID for current context."""
    correlation_id_var.set(correlation_id)


def get_correlation_id() -> str:
    """Get correlation ID for current context."""
    return correlation_id_var.get("")


def set_request_context(
    method: str,
    path: str,
    user_id: str | None = None,
    client_ip: str | None = None,
) -> None:
    """Set request context for logging."""
    request_context_var.set({
        "method": method,
        "path": path,
        "user_id": user_id,
        "client_ip": client_ip,
    })


def clear_request_context() -> None:
    """Clear request context."""
    request_context_var.set({})


class Timer:
    """Context manager for timing operations."""

    def __init__(self, logger: StructuredLogger, operation: str):
        self.logger = logger
        self.operation = operation
        self.start_time = 0.0

    def __enter__(self) -> "Timer":
        self.start_time = time.perf_counter()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        duration_ms = (time.perf_counter() - self.start_time) * 1000
        self.logger.info(
            f"{self.operation} completed",
            operation=self.operation,
            duration_ms=round(duration_ms, 2),
            success=exc_type is None,
        )


def timed(operation: str | None = None):
    """
    Decorator to time function execution.

    Usage:
        @timed("fetch_insights")
        async def fetch_insights():
            ...
    """
    def decorator(func):
        op_name = operation or func.__name__

        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            logger = get_logger(func.__module__)
            start = time.perf_counter()
            try:
                result = await func(*args, **kwargs)
                duration_ms = (time.perf_counter() - start) * 1000
                logger.info(
                    f"{op_name} completed",
                    operation=op_name,
                    duration_ms=round(duration_ms, 2),
                    success=True,
                )
                return result
            except Exception as e:
                duration_ms = (time.perf_counter() - start) * 1000
                logger.error(
                    f"{op_name} failed",
                    operation=op_name,
                    duration_ms=round(duration_ms, 2),
                    success=False,
                    error=str(e),
                )
                raise

        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            logger = get_logger(func.__module__)
            start = time.perf_counter()
            try:
                result = func(*args, **kwargs)
                duration_ms = (time.perf_counter() - start) * 1000
                logger.info(
                    f"{op_name} completed",
                    operation=op_name,
                    duration_ms=round(duration_ms, 2),
                    success=True,
                )
                return result
            except Exception as e:
                duration_ms = (time.perf_counter() - start) * 1000
                logger.error(
                    f"{op_name} failed",
                    operation=op_name,
                    duration_ms=round(duration_ms, 2),
                    success=False,
                    error=str(e),
                )
                raise

        import asyncio
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        return sync_wrapper

    return decorator


def setup_logging():
    """
    Configure application logging.

    Call this at application startup.
    """
    # Determine log level
    log_level = getattr(logging, settings.log_level.upper(), logging.INFO)

    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)

    # Clear existing handlers
    root_logger.handlers.clear()

    # Create handler
    handler = logging.StreamHandler()
    handler.setLevel(log_level)

    # Use JSON formatter in production, simple in development
    if settings.environment == "production":
        handler.setFormatter(JSONFormatter())
    else:
        formatter = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        )
        handler.setFormatter(formatter)

    root_logger.addHandler(handler)

    # Reduce noise from third-party libraries
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("httpcore").setLevel(logging.WARNING)
    logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)
    logging.getLogger("uvicorn.access").setLevel(logging.INFO)

    return root_logger


# Log API request/response helper
def log_api_call(
    logger: StructuredLogger,
    method: str,
    url: str,
    status_code: int,
    duration_ms: float,
    request_size: int | None = None,
    response_size: int | None = None,
) -> None:
    """Log an API call with standardized fields."""
    logger.info(
        f"API {method} {url} -> {status_code}",
        api_method=method,
        api_url=url,
        status_code=status_code,
        duration_ms=round(duration_ms, 2),
        request_size=request_size,
        response_size=response_size,
    )


# Log database query helper
def log_db_query(
    logger: StructuredLogger,
    query_type: str,
    table: str,
    duration_ms: float,
    rows_affected: int | None = None,
) -> None:
    """Log a database query with standardized fields."""
    logger.debug(
        f"DB {query_type} on {table}",
        db_query_type=query_type,
        db_table=table,
        duration_ms=round(duration_ms, 2),
        rows_affected=rows_affected,
    )
