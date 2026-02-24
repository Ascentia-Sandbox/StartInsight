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
# Set shared path so both root (build) and appuser (runtime) find the browsers
ENV PLAYWRIGHT_BROWSERS_PATH=/ms-playwright
RUN apt-get update && \
    apt-get install -y curl wget gnupg && \
    playwright install --with-deps chromium && \
    rm -rf /var/lib/apt/lists/* && \
    chmod -R 755 /ms-playwright

COPY app ./app
COPY alembic ./alembic
COPY alembic.ini ./
RUN useradd -m -u 1000 appuser && chown -R appuser:appuser /app
USER appuser
EXPOSE ${PORT:-8000}
COPY start.sh ./
CMD ["sh", "start.sh"]
