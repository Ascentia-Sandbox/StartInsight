#!/bin/sh
# Start arq worker in background (handles cron + on-demand analysis)
arq app.worker.WorkerSettings &
ARQ_PID=$!
echo "arq worker started (PID=$ARQ_PID)"

# Start uvicorn in foreground — Railway healthcheck targets /health
uvicorn app.main:app --host 0.0.0.0 --port "${PORT:-8000}"
EXIT_CODE=$?

# When uvicorn exits (crash or redeploy), also stop arq
echo "uvicorn exited ($EXIT_CODE), stopping arq..."
kill $ARQ_PID 2>/dev/null
exit $EXIT_CODE
