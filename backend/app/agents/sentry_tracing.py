"""Thin wrapper to add Sentry gen_ai.request spans around PydanticAI agent runs."""

import contextlib
from typing import Any


@contextlib.asynccontextmanager
async def trace_agent_run(agent_name: str, model: str = "google-gla:gemini-2.0-flash"):
    """Async context manager that wraps an agent run in a Sentry gen_ai.request span.

    Usage:
        async with trace_agent_run("enhanced_analyzer") as span:
            result = await asyncio.wait_for(agent.run(prompt), timeout=60)

    No-op when Sentry is not initialised (ImportError or DSN not set).
    """
    try:
        import sentry_sdk

        with sentry_sdk.start_span(op="gen_ai.request", name=agent_name) as span:
            span.set_data("gen_ai.request.model", model)
            yield span
    except ImportError:
        yield None
