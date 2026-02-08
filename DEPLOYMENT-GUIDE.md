# StartInsight Production Deployment Guide

**Quick Reference for deploying to production after implementing production readiness fixes.**

---

## Pre-Flight Checklist (30 minutes)

### 1. Rotate ALL Secrets (15 min)

```bash
# Generate new secrets
openssl rand -hex 64  # Copy to JWT_SECRET (128 chars)
openssl rand -hex 32  # Copy to REFRESH_TOKEN_SECRET (64 chars)

# Regenerate API keys:
# 1. Anthropic: https://console.anthropic.com
# 2. Google: https://console.cloud.google.com
# 3. Stripe: https://dashboard.stripe.com (create restricted keys)
# 4. Firecrawl: https://firecrawl.dev
# 5. Reddit: https://reddit.com/prefs/apps (create new app)
# 6. Supabase: https://supabase.com/dashboard (rotate service role key)
```

### 2. Create Sentry Projects (5 min)

```bash
# Go to: https://sentry.io
# Create 2 new projects:
# - "startinsight-backend" (Platform: Python/FastAPI)
# - "startinsight-frontend" (Platform: Next.js)
# Copy DSNs from: Settings → Client Keys (DSN)
```

### 3. Set Environment Variables (10 min)

**Railway (Backend):**
```bash
# Production Infrastructure (NEW)
SENTRY_DSN=https://xxx@xxx.ingest.sentry.io/xxx
REFRESH_TOKEN_SECRET=<from step 1>
ENVIRONMENT=production

# Security (ROTATED)
JWT_SECRET=<from step 1>
SUPABASE_SERVICE_ROLE_KEY=<from Supabase>
STRIPE_SECRET_KEY=<from Stripe>
STRIPE_WEBHOOK_SECRET=<from new Stripe webhook endpoint>
GOOGLE_API_KEY=<from Google Cloud>
FIRECRAWL_API_KEY=<from Firecrawl>
REDDIT_CLIENT_ID=<from Reddit>
REDDIT_CLIENT_SECRET=<from Reddit>

# CORS (Production domains only)
CORS_ORIGINS=https://startinsight.app,https://www.startinsight.app,https://app.startinsight.app
```

**Vercel (Frontend):**
```bash
# Production Infrastructure (NEW)
SENTRY_DSN=https://yyy@yyy.ingest.sentry.io/yyy  # Server
NEXT_PUBLIC_SENTRY_DSN=https://yyy@yyy.ingest.sentry.io/yyy  # Client
NEXT_PUBLIC_ENVIRONMENT=production
ENVIRONMENT=production

# Backend API
NEXT_PUBLIC_API_URL=https://api.startinsight.app
```

### 4. Upgrade Supabase (Optional - Recommended)

```bash
# Go to: https://supabase.com/dashboard
# Project → Settings → Billing → Upgrade to Pro
# Cost: $25/mo
# Benefit: 60 → 500 connections (prevents pool exhaustion)
```

---

## Deployment (10 minutes)

### Step 1: Run Database Migration

```bash
# Connect to production database
cd backend
export DATABASE_URL="<your_production_database_url>"
alembic upgrade head  # Applies b010_add_production_indexes.py

# Verify indexes created (8 new indexes)
psql $DATABASE_URL -c "SELECT schemaname, tablename, indexname FROM pg_indexes WHERE schemaname = 'public' AND indexname LIKE 'idx_%' ORDER BY tablename;"
```

### Step 2: Deploy Backend (Railway)

```bash
cd backend
git add .
git commit -m "feat: Production readiness fixes (security + infrastructure + performance)"
git push origin main  # Railway auto-deploys

# Wait 2-3 minutes for deployment
```

### Step 3: Verify Backend Health

```bash
# Test health endpoint
curl https://api.startinsight.app/health/ready

# Expected response:
# {
#   "status": "ready",
#   "checks": {
#     "database": "healthy",
#     "redis": "healthy"
#   }
# }

# If not ready, check Railway logs:
# railway logs --environment production
```

### Step 4: Deploy Frontend (Vercel)

```bash
cd frontend
vercel --prod

# Wait 1-2 minutes for deployment
```

### Step 5: Smoke Tests

```bash
# 1. Frontend loads
curl -I https://startinsight.app
# Expected: 200 OK

# 2. API responds with request ID
curl -I https://api.startinsight.app/api/insights
# Expected: X-Request-ID header present

# 3. Rate limiting works
for i in {1..101}; do curl -s https://api.startinsight.app/api/insights > /dev/null; done
# Request #101 should return 429 Too Many Requests

# 4. Sentry receives errors
curl https://api.startinsight.app/api/test-sentry-error
# Check Sentry dashboard for event
```

---

## Post-Deployment Monitoring (First 24 Hours)

### Hour 1: Critical Monitoring

**Check every 15 minutes:**

1. **Sentry Dashboard** (https://sentry.io)
   - Backend project: <5 errors/hour expected
   - Frontend project: <10 errors/hour expected (mostly 404s)

2. **Railway Logs** (https://railway.app)
   ```bash
   railway logs --environment production --filter ERROR
   ```
   - Expected: No connection pool timeouts
   - Expected: No 500 errors

3. **Supabase Dashboard** (https://supabase.com/dashboard)
   - Database → Connection pooling
   - Expected: <50/500 connections (<10%)
   - Alert if >400/500 (>80%)

### Hour 2-24: Regular Monitoring

**Check every 2 hours:**

1. **Error Rate** (Sentry)
   - Threshold: <1% error rate
   - Alert if >5% error rate

2. **Response Time** (Railway metrics)
   - Threshold: p95 <1s
   - Alert if p95 >3s

3. **Cache Hit Rate** (Upstash dashboard)
   - Expected: >80% cache hit rate after first hour

---

## Rollback Procedure (If Critical Issues)

### Backend Rollback

```bash
# Option 1: Rollback via Railway UI
# Dashboard → Deployments → Click previous deployment → "Redeploy"

# Option 2: Rollback database migration
cd backend
export DATABASE_URL="<production_url>"
alembic downgrade b009  # Rollback to previous migration

# Option 3: Git revert
git revert HEAD
git push origin main  # Railway auto-deploys
```

### Frontend Rollback

```bash
# Vercel UI: Deployments → Previous deployment → "Promote to Production"
# OR via CLI:
vercel rollback
```

---

## Common Issues & Solutions

### Issue: Health check returns "not_ready"

**Symptoms:** `/health/ready` returns 503

**Diagnosis:**
```bash
# Check which service is unhealthy
curl https://api.startinsight.app/health/ready | jq
# Response shows: "database": "unhealthy" or "redis": "unhealthy"
```

**Solutions:**
- **Database unhealthy:** Check Supabase dashboard for outages, verify DATABASE_URL is correct
- **Redis unhealthy:** Check Upstash dashboard for outages, verify REDIS_URL is correct

---

### Issue: Connection pool exhausted

**Symptoms:** Railway logs show `sqlalchemy.exc.TimeoutError: QueuePool limit exceeded`

**Diagnosis:**
```bash
# Check active connections
psql $DATABASE_URL -c "SELECT count(*) FROM pg_stat_activity WHERE datname = 'postgres';"
# If >45/50, pool is near exhaustion
```

**Solutions:**
1. **Immediate:** Restart Railway service (frees connections)
2. **Short-term:** Upgrade Supabase to Pro tier (500 connections)
3. **Long-term:** Identify and optimize slow queries holding connections

---

### Issue: Rate limiting too aggressive

**Symptoms:** Users report "429 Too Many Requests" errors

**Diagnosis:**
```bash
# Check rate limit settings
grep "limiter.limit" backend/app/api/routes/insights.py
# Current: list_insights (100/min), get_insight (200/min), stream (5/min)
```

**Solutions:**
1. **Temporary:** Increase limits in code and redeploy
   ```python
   @limiter.limit("200/minute")  # Increased from 100/minute
   async def list_insights(...):
   ```
2. **Permanent:** Implement per-user rate limiting (not IP-based)

---

### Issue: Sentry not receiving errors

**Symptoms:** Sentry dashboard shows no events after 1 hour

**Diagnosis:**
```bash
# Check Sentry DSN is set
railway variables | grep SENTRY_DSN
vercel env ls | grep SENTRY_DSN

# Test Sentry manually
curl -X POST https://api.startinsight.app/api/test-sentry-error
```

**Solutions:**
- Verify SENTRY_DSN is correct (check project settings in Sentry)
- Verify ENVIRONMENT=production (Sentry only initializes in production)
- Check Railway logs for "Sentry initialized" message

---

## Success Metrics (First Week)

| Metric | Target | Alert If |
|--------|--------|----------|
| Error Rate | <1% | >5% |
| Uptime | >99.9% | <99.5% |
| Response Time (p95) | <1s | >3s |
| Connection Pool Usage | <50/500 | >400/500 |
| Cache Hit Rate | >80% | <60% |
| Sentry Events | <100/day | >500/day |

---

## Support Contacts

- **Railway Support:** https://railway.app/help
- **Vercel Support:** https://vercel.com/support
- **Supabase Support:** https://supabase.com/support
- **Sentry Support:** https://sentry.io/support

---

**Last Updated:** 2026-01-31
**Document Owner:** DevOps Team
**Review Frequency:** After each production deployment
