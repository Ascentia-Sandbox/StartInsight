#!/usr/bin/env bash
# StartInsight shutdown audit + backup script
# Runs the read-only Step 0 checks AND the Step 3 pg_dump from the shutdown plan.
# Plan: ~/.claude/plans/due-the-the-low-elegant-pudding.md
#
# Usage:
#   1. Get DATABASE_URL from Railway → backend service → Variables
#   2. export DATABASE_URL='postgresql://postgres.<REF>:<PASS>@aws-1-ap-southeast-2.pooler.supabase.com:5432/postgres'
#   3. bash scripts/shutdown_audit.sh
#
# Requires: psql, pg_dump, gzip (brew install postgresql / apt install postgresql-client)

set -euo pipefail

if [[ -z "${DATABASE_URL:-}" ]]; then
  echo "ERROR: DATABASE_URL is not set."
  echo
  echo "Get it from: Railway dashboard → backend service → Variables → DATABASE_URL"
  echo "Then run:   export DATABASE_URL='postgresql://...'"
  echo "Then re-run this script."
  exit 1
fi

# Sanity check tools
for tool in psql pg_dump gzip; do
  if ! command -v "$tool" >/dev/null 2>&1; then
    echo "ERROR: '$tool' not found. Install postgresql-client first."
    echo "  macOS:  brew install postgresql"
    echo "  Debian: sudo apt install postgresql-client"
    exit 1
  fi
done

DATE_STAMP="$(date +%Y-%m-%d)"
BACKUP_DIR="${BACKUP_DIR:-$HOME/StartInsight-Backup-$DATE_STAMP}"
mkdir -p "$BACKUP_DIR"
cd "$BACKUP_DIR"

echo "================================================================"
echo "StartInsight Shutdown Audit + Backup"
echo "Date:        $(date -u +%Y-%m-%dT%H:%M:%SZ)"
echo "Backup dir:  $BACKUP_DIR"
echo "================================================================"

# ---------------------------------------------------------------------
# Step 0.2 — Count active paying Stripe subscribers (read-only)
# ---------------------------------------------------------------------
echo
echo "── Step 0.2: Active Stripe subscribers (from subscriptions table) ──"
psql "$DATABASE_URL" -P pager=off <<'SQL' | tee subscribers_audit.txt
SELECT tier,
       status,
       COUNT(*) AS n,
       MIN(created_at)::date AS oldest,
       MAX(created_at)::date AS newest
FROM subscriptions
WHERE status IN ('active','trialing','past_due')
GROUP BY tier, status
ORDER BY tier, status;

-- Also count total users so we know the audience size
SELECT 'total_users' AS metric, COUNT(*)::text AS value FROM users
UNION ALL
SELECT 'subscriptions_total', COUNT(*)::text FROM subscriptions
UNION ALL
SELECT 'payment_history_total', COUNT(*)::text FROM payment_history;
SQL

echo
echo "→ Saved subscriber counts to: $BACKUP_DIR/subscribers_audit.txt"

# ---------------------------------------------------------------------
# Step 3.1 — Full pg_dump of production DB
# ---------------------------------------------------------------------
DUMP_FILE="startinsight-prod-${DATE_STAMP}.sql"
echo
echo "── Step 3.1: pg_dump production database ──"
echo "→ Dumping to: $BACKUP_DIR/$DUMP_FILE"
pg_dump "$DATABASE_URL" \
  --no-owner --no-acl --clean --if-exists \
  -f "$DUMP_FILE"

ORIGINAL_SIZE=$(du -h "$DUMP_FILE" | cut -f1)
gzip -f "$DUMP_FILE"
COMPRESSED_SIZE=$(du -h "${DUMP_FILE}.gz" | cut -f1)

# Verify dump
TABLE_COUNT=$(gunzip -c "${DUMP_FILE}.gz" | grep -c "^CREATE TABLE " || true)
echo "→ Dump size:    $ORIGINAL_SIZE uncompressed / $COMPRESSED_SIZE gzipped"
echo "→ Table count:  $TABLE_COUNT (expected ~70)"

if [[ "$TABLE_COUNT" -lt 50 ]]; then
  echo "WARNING: Table count ($TABLE_COUNT) is suspiciously low. Investigate before proceeding."
fi

# ---------------------------------------------------------------------
# Step 3.2 — Export critical tables to CSV (easier re-loading)
# ---------------------------------------------------------------------
echo
echo "── Step 3.2: CSV exports of critical tables ──"
for table in users subscriptions payment_history; do
  echo "→ Exporting $table.csv"
  psql "$DATABASE_URL" -c "\COPY $table TO '$BACKUP_DIR/$table.csv' CSV HEADER" || \
    echo "  (skipped: $table — may not exist or permission denied)"
done

# ---------------------------------------------------------------------
# Summary
# ---------------------------------------------------------------------
echo
echo "================================================================"
echo "DONE. Backup contents:"
ls -lh "$BACKUP_DIR"
echo "================================================================"
echo
echo "NEXT STEPS (from the shutdown plan):"
echo "  • Review subscribers_audit.txt — decide if subscriber notification is needed."
echo "  • Copy this directory to a second location (cloud drive / external disk)."
echo "  • Then proceed to Step 4 (cancel Supabase Pro)."
echo
echo "DO NOT commit this backup directory to git."
echo "================================================================"
