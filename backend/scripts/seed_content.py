#!/usr/bin/env python3
"""
StartInsight Content Seeding Script.

Drives the content pipeline via the admin API to grow the insight count
from the current baseline toward the 600+ target.

Usage:
    # Show current status (insight count, signals, pending)
    python backend/scripts/seed_content.py status

    # Trigger all scrapers (enqueues arq scrape_all_sources_task)
    python backend/scripts/seed_content.py scrape

    # Trigger signal analysis (enqueues arq analyze_signals_task)
    python backend/scripts/seed_content.py analyze

    # Run full pipeline: scrape -> wait 30s -> analyze -> wait 60s -> status
    python backend/scripts/seed_content.py pipeline

    # Bulk-approve pending insights with quality_score > 0.75
    python backend/scripts/seed_content.py approve-pending [--min-score 0.75]

Environment variables:
    BACKEND_URL     Base URL of the backend API.
                    Default: http://localhost:8000
    ADMIN_JWT_TOKEN Full Supabase JWT Bearer token for an admin user.
                    Required for scrape, analyze, pipeline, approve-pending.
                    Obtain by logging in as an admin and copying the access token.

Authentication note:
    The admin endpoints use Supabase JWT authentication (ES256 / JWKS).
    Set ADMIN_JWT_TOKEN to the raw JWT access token (without "Bearer " prefix).
    You can get this token from the browser DevTools (Network tab -> Authorization
    header on any API request) or via the Supabase dashboard -> Authentication ->
    Users -> your admin account -> copy access token.

Endpoints used:
    GET  /api/admin/dashboard              - dashboard metrics (pending count)
    GET  /api/signals/stats/summary        - raw signal stats
    POST /api/admin/agents/scrape_all/trigger   - trigger all scrapers
    POST /api/admin/agents/analyzer/trigger     - trigger signal analysis
    GET  /api/admin/insights?status=pending     - list pending insights
    PATCH /api/admin/insights/{id}             - update insight admin_status
"""

import argparse
import asyncio
import os
import sys
import time
from typing import Any

import httpx

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

BACKEND_URL: str = os.environ.get("BACKEND_URL", "http://localhost:8000").rstrip("/")
ADMIN_JWT_TOKEN: str = os.environ.get("ADMIN_JWT_TOKEN", "")

# Pagination page size when fetching pending insights
_PAGE_SIZE = 50

# Symbol helpers
OK = "\u2713"   # ✓
FAIL = "\u2717"  # ✗
WAIT = "\u23f3"  # ⏳


# ---------------------------------------------------------------------------
# HTTP client helpers
# ---------------------------------------------------------------------------


def _build_headers() -> dict[str, str]:
    """Build request headers including Bearer token if configured."""
    headers: dict[str, str] = {
        "Content-Type": "application/json",
        "Accept": "application/json",
    }
    if ADMIN_JWT_TOKEN:
        headers["Authorization"] = f"Bearer {ADMIN_JWT_TOKEN}"
    return headers


def _require_token() -> None:
    """Exit with an error if ADMIN_JWT_TOKEN is not set."""
    if not ADMIN_JWT_TOKEN:
        print(
            f"{FAIL}  ADMIN_JWT_TOKEN environment variable is not set.\n"
            "     Set it to your Supabase admin JWT access token and retry."
        )
        sys.exit(1)


async def _get(client: httpx.AsyncClient, path: str, **kwargs: Any) -> httpx.Response:
    """Perform a GET request against the backend API."""
    return await client.get(
        f"{BACKEND_URL}{path}",
        headers=_build_headers(),
        timeout=30.0,
        **kwargs,
    )


async def _post(
    client: httpx.AsyncClient,
    path: str,
    json: dict[str, Any] | None = None,
    **kwargs: Any,
) -> httpx.Response:
    """Perform a POST request against the backend API."""
    return await client.post(
        f"{BACKEND_URL}{path}",
        headers=_build_headers(),
        json=json or {},
        timeout=30.0,
        **kwargs,
    )


async def _patch(
    client: httpx.AsyncClient,
    path: str,
    json: dict[str, Any],
    **kwargs: Any,
) -> httpx.Response:
    """Perform a PATCH request against the backend API."""
    return await client.patch(
        f"{BACKEND_URL}{path}",
        headers=_build_headers(),
        json=json,
        timeout=30.0,
        **kwargs,
    )


# ---------------------------------------------------------------------------
# Command: status
# ---------------------------------------------------------------------------


async def cmd_status() -> None:
    """
    Print current content pipeline status.

    Fetches:
    - Total insight count and pending count from /api/admin/dashboard
    - Raw signal totals and unprocessed count from /api/signals/stats/summary
    """
    async with httpx.AsyncClient() as client:
        # Dashboard metrics (requires admin auth)
        dashboard_data: dict[str, Any] = {}
        if ADMIN_JWT_TOKEN:
            resp = await _get(client, "/api/admin/dashboard")
            if resp.status_code == 200:
                dashboard_data = resp.json()
            else:
                print(
                    f"{FAIL}  Dashboard fetch failed: HTTP {resp.status_code} - {resp.text[:200]}"
                )
        else:
            print(
                "  (Skipping dashboard metrics - ADMIN_JWT_TOKEN not set)"
            )

        # Signal stats (public endpoint)
        signal_data: dict[str, Any] = {}
        resp = await _get(client, "/api/signals/stats/summary")
        if resp.status_code == 200:
            signal_data = resp.json()
        else:
            print(
                f"{FAIL}  Signal stats fetch failed: HTTP {resp.status_code} - {resp.text[:200]}"
            )

    print()
    print("=" * 55)
    print("  StartInsight Content Pipeline - Status")
    print("=" * 55)
    print(f"  Backend:  {BACKEND_URL}")
    print()

    # Insight counts from dashboard
    if dashboard_data:
        pending = dashboard_data.get("pending_insights", "?")
        today = dashboard_data.get("total_insights_today", "?")
        print(f"  Insights pending review:   {pending}")
        print(f"  Insights created today:    {today}")
    else:
        print("  Insights:                  (dashboard unavailable)")

    # Signal stats
    if signal_data:
        total_signals = signal_data.get("total_signals", "?")
        processed = signal_data.get("processed_count", "?")
        unprocessed = signal_data.get("unprocessed_count", "?")
        by_source = signal_data.get("signals_by_source", {})
        print()
        print(f"  Raw signals (total):       {total_signals}")
        print(f"  Processed signals:         {processed}")
        print(f"  Unprocessed signals:       {unprocessed}")
        if by_source:
            print()
            print("  Signals by source:")
            for source, count in sorted(by_source.items(), key=lambda x: -x[1]):
                print(f"    {source:<30} {count}")
    else:
        print("  Signals:                   (stats unavailable)")

    print()
    print("=" * 55)
    print()


# ---------------------------------------------------------------------------
# Command: scrape
# ---------------------------------------------------------------------------


async def cmd_scrape() -> None:
    """
    Trigger the full scrape-all-sources task via the admin agent trigger endpoint.

    Uses: POST /api/admin/agents/scrape_all/trigger
    The agent_type 'scrape_all' maps to 'scrape_all_sources_task' in worker.py.
    """
    _require_token()

    print(f"\n{WAIT}  Triggering all scrapers (scrape_all agent)...")
    async with httpx.AsyncClient() as client:
        resp = await _post(client, "/api/admin/agents/scrape_all/trigger")

    if resp.status_code == 200:
        data = resp.json()
        job_id = data.get("job_id", "unknown")
        ts = data.get("timestamp", "")
        print(f"{OK}  Scrape task enqueued successfully")
        print(f"    Status:   {data.get('status')}")
        print(f"    Job ID:   {job_id}")
        print(f"    Time:     {ts}")
        print()
        print(
            "  The Arq worker will run scrape_all_sources_task (Reddit, Product Hunt,\n"
            "  Google Trends multi-region, Twitter/X, Hacker News) in the background.\n"
            "  Check Railway logs for progress: railway logs --filter=scrape"
        )
    else:
        print(
            f"{FAIL}  Failed to trigger scrape: HTTP {resp.status_code}\n"
            f"    {resp.text[:400]}"
        )
        _print_auth_hint(resp.status_code)

    print()


# ---------------------------------------------------------------------------
# Command: analyze
# ---------------------------------------------------------------------------


async def cmd_analyze() -> None:
    """
    Trigger the signal analysis task via the admin agent trigger endpoint.

    Uses: POST /api/admin/agents/analyzer/trigger
    The agent_type 'analyzer' maps to 'analyze_signals_task' in worker.py.
    """
    _require_token()

    print(f"\n{WAIT}  Triggering signal analysis (analyzer agent)...")
    async with httpx.AsyncClient() as client:
        resp = await _post(client, "/api/admin/agents/analyzer/trigger")

    if resp.status_code == 200:
        data = resp.json()
        job_id = data.get("job_id", "unknown")
        ts = data.get("timestamp", "")
        print(f"{OK}  Analyze task enqueued successfully")
        print(f"    Status:   {data.get('status')}")
        print(f"    Job ID:   {job_id}")
        print(f"    Time:     {ts}")
        print()
        print(
            "  The Arq worker will run analyze_signals_task using the enhanced\n"
            "  PydanticAI analyzer (Gemini 2.0 Flash). Each unprocessed signal\n"
            "  generates a full insight with 8-dimension scoring.\n"
            "  Check Railway logs: railway logs --filter=analyz"
        )
    else:
        print(
            f"{FAIL}  Failed to trigger analysis: HTTP {resp.status_code}\n"
            f"    {resp.text[:400]}"
        )
        _print_auth_hint(resp.status_code)

    print()


# ---------------------------------------------------------------------------
# Command: pipeline
# ---------------------------------------------------------------------------


async def cmd_pipeline(scrape_wait: int = 30, analyze_wait: int = 60) -> None:
    """
    Run the full content pipeline end-to-end.

    Steps:
    1. Show pre-pipeline status
    2. Trigger scrape_all -> wait scrape_wait seconds
    3. Trigger analyze -> wait analyze_wait seconds
    4. Show post-pipeline status to see growth

    Args:
        scrape_wait:   Seconds to wait after triggering scrape before triggering analyze.
        analyze_wait:  Seconds to wait after triggering analyze before showing results.
    """
    _require_token()

    print("\n" + "=" * 55)
    print("  StartInsight Full Content Pipeline")
    print("=" * 55)

    # Step 1 - baseline
    print("\n[Step 1/4] Pre-pipeline status:")
    await cmd_status()

    # Step 2 - scrape
    print("[Step 2/4] Triggering scrapers...")
    await cmd_scrape()

    # Wait for scraping to begin producing signals
    print(
        f"{WAIT}  Waiting {scrape_wait}s for scrapers to collect signals "
        f"before triggering analysis..."
    )
    _countdown(scrape_wait)

    # Step 3 - analyze
    print("\n[Step 3/4] Triggering signal analysis...")
    await cmd_analyze()

    # Wait for analysis to produce insights
    print(
        f"{WAIT}  Waiting {analyze_wait}s for analysis to produce insights..."
    )
    _countdown(analyze_wait)

    # Step 4 - results
    print("\n[Step 4/4] Post-pipeline status (insights added since pipeline start):")
    await cmd_status()

    print("Pipeline complete. Note: Arq jobs are async - full results")
    print("may take several minutes. Re-run 'status' later to see final counts.")
    print()


# ---------------------------------------------------------------------------
# Command: approve-pending
# ---------------------------------------------------------------------------


async def cmd_approve_pending(min_score: float = 0.75) -> None:
    """
    Bulk-approve pending insights with quality/relevance score above min_score.

    Fetches all insights with admin_status=pending from GET /api/admin/insights,
    then PATCHes each eligible insight to admin_status=approved.

    Args:
        min_score: Minimum relevance_score threshold (0.0-1.0). Default 0.75.
    """
    _require_token()

    print(f"\n{WAIT}  Fetching pending insights (min_score >= {min_score})...")

    all_pending: list[dict[str, Any]] = []

    async with httpx.AsyncClient() as client:
        # Paginate through all pending insights
        offset = 0
        total_fetched = 0
        while True:
            resp = await _get(
                client,
                "/api/admin/insights",
                params={"status": "pending", "limit": _PAGE_SIZE, "offset": offset},
            )
            if resp.status_code != 200:
                print(
                    f"{FAIL}  Failed to fetch pending insights: HTTP {resp.status_code}\n"
                    f"    {resp.text[:400]}"
                )
                _print_auth_hint(resp.status_code)
                return

            data = resp.json()
            items: list[dict[str, Any]] = data.get("items", [])
            total_in_db: int = data.get("total", 0)

            all_pending.extend(items)
            total_fetched += len(items)

            print(
                f"  Fetched {total_fetched}/{total_in_db} pending insights "
                f"(page offset={offset})..."
            )

            # Stop if we have all items or got an empty page
            if len(items) < _PAGE_SIZE or total_fetched >= total_in_db:
                break

            offset += _PAGE_SIZE

    print(f"\n  Total pending: {len(all_pending)}")

    # Filter by score
    eligible = [
        insight for insight in all_pending
        if (insight.get("relevance_score") or 0.0) >= min_score
    ]
    skipped = len(all_pending) - len(eligible)

    print(f"  Eligible (score >= {min_score}): {len(eligible)}")
    print(f"  Skipped  (score <  {min_score}): {skipped}")

    if not eligible:
        print("\n  No insights meet the score threshold. Done.")
        return

    print(f"\n{WAIT}  Approving {len(eligible)} insights...")

    approved = 0
    failed = 0
    failed_ids: list[str] = []

    async with httpx.AsyncClient() as client:
        for insight in eligible:
            insight_id: str = str(insight.get("id", ""))
            score: float = insight.get("relevance_score") or 0.0

            resp = await _patch(
                client,
                f"/api/admin/insights/{insight_id}",
                json={"admin_status": "approved"},
            )

            if resp.status_code == 200:
                approved += 1
                print(
                    f"  {OK}  {insight_id[:8]}...  score={score:.2f}  "
                    f"approved"
                )
            else:
                failed += 1
                failed_ids.append(insight_id)
                print(
                    f"  {FAIL}  {insight_id[:8]}...  score={score:.2f}  "
                    f"HTTP {resp.status_code}"
                )

    print()
    print(f"  Approved: {approved}")
    print(f"  Failed:   {failed}")
    if failed_ids:
        print(f"  Failed IDs: {', '.join(id[:8] for id in failed_ids[:10])}")
    print()


# ---------------------------------------------------------------------------
# Utilities
# ---------------------------------------------------------------------------


def _countdown(seconds: int) -> None:
    """Print a live countdown to stdout, overwriting each line."""
    for remaining in range(seconds, 0, -1):
        sys.stdout.write(f"\r  {remaining:3d}s remaining...  ")
        sys.stdout.flush()
        time.sleep(1)
    sys.stdout.write("\r  Done waiting.            \n")
    sys.stdout.flush()


def _print_auth_hint(status_code: int) -> None:
    """Print contextual auth help for 401 / 403 responses."""
    if status_code == 401:
        print(
            "\n  Hint: HTTP 401 = token invalid or expired.\n"
            "  Refresh your ADMIN_JWT_TOKEN by logging into the app and\n"
            "  copying the current access token from DevTools -> Network -> Authorization."
        )
    elif status_code == 403:
        print(
            "\n  Hint: HTTP 403 = authenticated but not admin.\n"
            "  Ensure the account you are using has an admin_users record in the DB.\n"
            "  Run: python backend/scripts/create_admin.py --email your@email.com"
        )
    elif status_code == 404:
        print(
            "\n  Hint: HTTP 404 = agent not found in agent_configurations table.\n"
            "  The trigger endpoint validates agent names against that table.\n"
            "  Run: python backend/scripts/seed_agent_configs.py to populate it."
        )


# ---------------------------------------------------------------------------
# CLI entrypoint
# ---------------------------------------------------------------------------


def build_parser() -> argparse.ArgumentParser:
    """Build the argument parser."""
    parser = argparse.ArgumentParser(
        prog="seed_content.py",
        description=(
            "StartInsight content seeding script. "
            "Drives the pipeline via the admin API to grow insight count."
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    # status
    subparsers.add_parser(
        "status",
        help="Show current insight count, signal stats, and pending count.",
    )

    # scrape
    subparsers.add_parser(
        "scrape",
        help="Trigger all scrapers via admin API (enqueues arq scrape_all_sources_task).",
    )

    # analyze
    subparsers.add_parser(
        "analyze",
        help="Trigger signal analysis via admin API (enqueues arq analyze_signals_task).",
    )

    # pipeline
    pipeline_parser = subparsers.add_parser(
        "pipeline",
        help="Run full pipeline: scrape -> wait -> analyze -> wait -> show results.",
    )
    pipeline_parser.add_argument(
        "--scrape-wait",
        type=int,
        default=30,
        metavar="SECONDS",
        help="Seconds to wait after scrape trigger before triggering analyze. Default: 30",
    )
    pipeline_parser.add_argument(
        "--analyze-wait",
        type=int,
        default=60,
        metavar="SECONDS",
        help="Seconds to wait after analyze trigger before showing results. Default: 60",
    )

    # approve-pending
    approve_parser = subparsers.add_parser(
        "approve-pending",
        help="Bulk-approve pending insights with relevance_score above threshold.",
    )
    approve_parser.add_argument(
        "--min-score",
        type=float,
        default=0.75,
        metavar="SCORE",
        help="Minimum relevance_score to approve (0.0-1.0). Default: 0.75",
    )

    return parser


def main() -> None:
    """Parse CLI arguments and dispatch to the appropriate command function."""
    parser = build_parser()
    args = parser.parse_args()

    if args.command == "status":
        asyncio.run(cmd_status())

    elif args.command == "scrape":
        asyncio.run(cmd_scrape())

    elif args.command == "analyze":
        asyncio.run(cmd_analyze())

    elif args.command == "pipeline":
        asyncio.run(
            cmd_pipeline(
                scrape_wait=args.scrape_wait,
                analyze_wait=args.analyze_wait,
            )
        )

    elif args.command == "approve-pending":
        if not 0.0 <= args.min_score <= 1.0:
            print(f"{FAIL}  --min-score must be between 0.0 and 1.0")
            sys.exit(1)
        asyncio.run(cmd_approve_pending(min_score=args.min_score))


if __name__ == "__main__":
    main()
