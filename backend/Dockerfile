# StartInsight Backend - Production Multi-Stage Dockerfile

# Stage 1: Builder (includes build tools)
FROM python:3.12-slim AS builder
WORKDIR /app
RUN apt-get update && apt-get install -y curl build-essential && rm -rf /var/lib/apt/lists/*
RUN curl -LsSf https://astral.sh/uv/0.5.14/install.sh | sh
ENV PATH="/root/.local/bin:${PATH}"
COPY pyproject.toml .python-version* ./
RUN uv pip install --system -r pyproject.toml

# Stage 2: Runtime (no build tools)
FROM python:3.12-slim AS runtime
WORKDIR /app
COPY --from=builder /usr/local/lib/python3.12/site-packages /usr/local/lib/python3.12/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

# Install Playwright dependencies for Crawl4AI (PMF optimization)
RUN apt-get update && \
    apt-get install -y curl wget gnupg && \
    playwright install --with-deps chromium && \
    rm -rf /var/lib/apt/lists/*

COPY app ./app
COPY alembic ./alembic
COPY alembic.ini ./
RUN useradd -m -u 1000 appuser && chown -R appuser:appuser /app
USER appuser
EXPOSE 8000
HEALTHCHECK --interval=30s --timeout=10s --start-period=10s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "2"]
