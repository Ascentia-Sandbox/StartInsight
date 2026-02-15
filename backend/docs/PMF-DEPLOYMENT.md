# StartInsight: Minimal-Cost PMF Validation Deployment Guide

**Last Updated:** 2026-02-08
**Status:** Production Ready
**Target:** <100 users, ~$30/month infrastructure cost

## Overview

This guide explains how to deploy StartInsight with **~$30/month** infrastructure costs for Product-Market Fit validation, down from the original $483/month production configuration. Uses Supabase Pro ($25/mo) as the single database source of truth.

**Cost Breakdown:**
- **Supabase Pro:** $25/month (8GB storage, 200 connections)
- **Railway:** $5/month ($5 starter credit)
- **Everything else:** $0 (free tiers)
- **Total:** ~$30/month (94% reduction from $483/mo)

---

## What Changed from Production Config

### 1. Web Scraping ($149/mo → $0)
- **Before:** Firecrawl Pro API
- **After:** Crawl4AI (self-hosted, open-source)
- **Trade-off:** 20-30% slower scraping (acceptable for PMF)
- **Config:** `USE_CRAWL4AI=true` in `.env`

### 2. Container Hosting ($100/mo → $5)
- **Before:** Railway Pro (2 containers: backend + worker, 24/7)
- **After:** Railway Free tier (1 container, reduced hours)
- **Optimization:** Merged scheduler into backend, reduced scraping from 6h → 12h
- **Free Tier Limits:** $5 credit/month, ~300 execution hours

### 3. Database ($25/mo -- kept as-is)
- **Supabase Pro:** $25/mo (8GB, 200 connections) -- already paid
- **Connection pool:** 20 pool + 30 overflow = 50 max (out of 200 available)
- **SSL:** Required (`DB_SSL=true`)

### 4. Email Service ($35/mo → $0)
- **Before:** Resend Pro (50K emails/month)
- **After:** Resend Free (3K emails/month)
- **Optimization:** Daily digest emails disabled by default
- **Keep:** Welcome, analysis_ready, password_reset (critical only)
- **Expected Usage:** ~800 emails/month (100 users × 2 emails/week = 27% of limit)

### 5. Monitoring ($46/mo → $0)
- **Sentry:** Team tier → Free tier (5K events/month)
- **Vercel:** Pro → Hobby tier (100GB bandwidth)
- **Config:** `SENTRY_TRACES_SAMPLE_RATE=0.01` (reduced from 0.1)

### 6. AI/LLM ($15-75/mo → $0)
- **Before:** Gemini API (paid tier)
- **After:** Gemini Free tier (1,500 requests/day)
- **Optimization:** Scraping frequency 6h → 12h (50% fewer AI calls)
- **Expected Usage:** ~51 AI calls/day (96% within free limit)

---

## Environment Configuration

### .env File for PMF Deployment

```bash
# ============================================
# PMF VALIDATION MODE
# ============================================
ENVIRONMENT=production

# ============================================
# Database (Supabase Pro -- single source of truth)
# ============================================
DATABASE_URL=postgresql+asyncpg://postgres.[REF]:[PASSWORD]@aws-0-ap-southeast-2.pooler.supabase.com:5432/postgres
DB_POOL_SIZE=20  # Supabase Pro: 200 connections available
DB_MAX_OVERFLOW=30
DB_SSL=true

# ============================================
# Redis (Railway Free Addon)
# ============================================
# Auto-configured by Railway Redis addon
REDIS_URL=${{Redis.REDIS_URL}}

# ============================================
# Web Scraping (Crawl4AI - $0 cost)
# ============================================
USE_CRAWL4AI=true  # Use self-hosted scraper
# FIRECRAWL_API_KEY removed (not needed for PMF)

# Reddit API (still required for PRAW)
REDDIT_CLIENT_ID=your_reddit_client_id
REDDIT_CLIENT_SECRET=your_reddit_secret
REDDIT_USERNAME=your_username

# ============================================
# AI/LLM (Gemini Free Tier)
# ============================================
GOOGLE_API_KEY=your_free_tier_key  # 1,500 requests/day

# ============================================
# Task Scheduling (Reduced Frequency)
# ============================================
SCRAPE_INTERVAL_HOURS=12  # Reduced from 6h (save 50% AI calls)
ANALYSIS_BATCH_SIZE=50  # Increased from 10 (process more per run)

# ============================================
# Email (Resend Free Tier)
# ============================================
RESEND_API_KEY=your_free_tier_key
ENABLE_DAILY_DIGEST=false  # Disable to save email quota

# ============================================
# Monitoring (Sentry Free Tier)
# ============================================
SENTRY_DSN=your_dsn
SENTRY_TRACES_SAMPLE_RATE=0.01  # Reduced from 0.1 (save quota)
```

---

## Deployment Steps

### 1. Install Dependencies

```bash
cd backend
uv sync  # Install dependencies including crawl4ai and playwright

# Install Playwright browsers (required for Crawl4AI)
playwright install chromium --with-deps
```

### 2. Local Testing

```bash
# Test Crawl4AI scraper
pytest tests/scrapers/test_crawl4ai_client.py -v

# Test merged scheduler
uvicorn app.main:app --reload
# Verify logs: "Initializing task scheduler"

# Test email service (daily digest disabled)
pytest tests/services/test_email_service.py::test_daily_digest_disabled -v
```

### 3. Railway Deployment

#### A. Add Railway Redis Addon
1. Railway dashboard → Add → Database → Redis
2. Environment variable `REDIS_URL` auto-generated

#### B. Update Environment Variables
```bash
railway link  # Link to your Railway project
railway variables set DATABASE_URL="postgresql+asyncpg://..."
railway variables set USE_CRAWL4AI=true
railway variables set ENABLE_DAILY_DIGEST=false
railway variables set SCRAPE_INTERVAL_HOURS=12
railway variables set ANALYSIS_BATCH_SIZE=50
```

#### C. Deploy
```bash
railway up  # Deploy to Railway

# Verify deployment
curl https://your-app.up.railway.app/health
# Expected: {"status": "healthy"}

# Check logs
railway logs
# Verify: "Initializing task scheduler", "Using Crawl4AI client"
```

### 4. Verify Supabase Pro Connection

```bash
# Verify connection pool works against Supabase Pro
psql $DATABASE_URL -c "SELECT count(*) FROM pg_stat_activity;"
# Should be <50 connections (out of 200 available on Pro)

# Monitor storage
psql $DATABASE_URL -c "SELECT pg_size_pretty(pg_database_size('postgres'));"
# Expected: <100MB for fresh deployment (8GB available on Pro)
```

### 5. Vercel Deployment (Frontend)

```bash
cd frontend

# Downgrade to Hobby tier (Vercel dashboard → Billing)
# Update environment variables
vercel env add NEXT_PUBLIC_API_URL production
vercel env add NEXT_PUBLIC_SUPABASE_URL production
vercel env add NEXT_PUBLIC_SUPABASE_ANON_KEY production

# Deploy
vercel --prod
```

---

## Monitoring Free Tier Limits

### Daily Monitoring Queries

```bash
# Railway execution hours (alert at 320/month = 80% of 400 limit)
# Check in Railway dashboard → Usage

# Supabase storage (alert at 6.4GB = 80% of 8GB Pro limit)
psql $DATABASE_URL -c "SELECT pg_size_pretty(pg_database_size('postgres'));"

# Supabase connections (alert at 160 = 80% of 200 Pro limit)
psql $DATABASE_URL -c "SELECT count(*) FROM pg_stat_activity;"

# Gemini API usage (alert at 1200/day = 80% of 1500 limit)
# Check in Google Cloud Console → APIs & Services → Gemini API

# Resend emails (alert at 2500/month = 85% of 3K limit)
# Check in Resend dashboard → Usage
```

---

## Upgrade Triggers

**When to upgrade back to paid tiers:**

| Metric | Limit | Alert (80%) | Upgrade Action | New Cost |
|--------|-------|-------------|----------------|----------|
| **Users** | ~100 | 80 users | Optimize first, then scale | - |
| **Railway hours** | 400/mo | 320/mo | Upgrade to Hobby | $5 → $20 |
| **Supabase storage** | 8GB (Pro) | 6.4GB | Already on Pro | $25 (current) |
| **Supabase connections** | 200 (Pro) | 160 | Already on Pro | $25 (current) |
| **Gemini requests** | 1500/day | 1200/day | Upgrade to paid | $0 → $15-75 |
| **Resend emails** | 3K/mo | 2.5K/mo | Upgrade to Pro | $0 → $20 |
| **Sentry events** | 5K/mo | 4K/mo | Upgrade to Team | $0 → $26 |

**Cost Progression:**
- Month 1: ~$25 (Supabase Pro + Railway starter credit)
- Month 2+: ~$30 (Supabase Pro + Railway renewal)
- Month 3-4: $30-55 (add services as limits hit)
- Month 5+: $100-300 (confirmed PMF, scale normally)

**Breakeven:** Month 2 (2 paid users @ $19/mo = $38 revenue > $30 infrastructure)

---

## Troubleshooting

### Crawl4AI Issues

**Error: "Playwright not installed"**
```bash
playwright install chromium --with-deps
```

**Slow scraping (>2min per page)**
- Expected: Crawl4AI is 20-30% slower than Firecrawl
- Mitigation: Reduce scraping frequency further (12h → 24h)

**Fallback to Firecrawl:**
```bash
# If Crawl4AI fails, switch back temporarily
railway variables set USE_CRAWL4AI=false
railway variables set FIRECRAWL_API_KEY="your_key"
```

### Railway Free Tier Exhausted

**Symptom:** Service downtime before month end

**Solution 1:** Reduce scraping frequency
```bash
railway variables set SCRAPE_INTERVAL_HOURS=24  # From 12h to 24h (save 50% CPU)
```

**Solution 2:** Upgrade to Hobby ($5/mo → $20/mo)
```bash
# Railway dashboard → Settings → Plan → Upgrade to Hobby
```

### Gemini API Quota Hit

**Symptom:** Analysis jobs failing with 429 errors

**Solution 1:** Reduce AI calls (already at 50% with 12h scraping)
```bash
# Disable automated analysis, keep only user-requested research
railway variables set SCRAPE_INTERVAL_HOURS=24
```

**Solution 2:** Upgrade to paid tier ($15-75/mo)
```bash
# Google Cloud Console → Billing → Enable Billing
```

### Supabase Connection Pool Exhausted

**Symptom:** "Too many connections" database errors

**Check current connections:**
```bash
psql $DATABASE_URL -c "SELECT count(*) FROM pg_stat_activity;"
```

**Solution 1:** Optimize pool
- Current: pool_size=20, max_overflow=30 (50 max connections)
- Supabase Pro allows 200 connections -- plenty of headroom

**Solution 2:** Reduce pool size temporarily
```bash
railway variables set DB_POOL_SIZE=10
railway variables set DB_MAX_OVERFLOW=15
```

---

## Success Metrics (PMF Validation)

**Infrastructure Health:**
- ✅ Monthly cost: ~$30 (94% reduction from $483)
- ✅ All 230 API endpoints functional
- ✅ Core user flows working (scraping, analysis, research)

**Product-Market Fit:**
- ✅ Activation rate: >40% (users save at least 1 insight)
- ✅ 7-day retention: >30% (users return after 1 week)
- ✅ Research conversion: >20% (users request AI analysis)

**Validation Period:** 2-3 months to confirm PMF before scaling

---

## Rollback Plan

**If PMF validation fails or costs exceed budget:**

1. **Stop Railway deployment**
   ```bash
   railway down
   ```

2. **Keep or downgrade Supabase** (Pro $25/mo or downgrade to Free)

3. **Cancel paid services:**
   - Resend Pro → Free
   - Sentry Team → Free
   - Vercel Pro → Hobby

4. **Total Monthly Cost After Rollback:** $0-25 (depending on Supabase tier)

---

## Next Steps After PMF Confirmation

Once you've validated product-market fit (>30% retention, >40% activation):

1. **Scale Infrastructure**
   - Upgrade Railway to Hobby ($20/mo)
   - Supabase Pro already active ($25/mo)
   - Re-enable Firecrawl Pro ($149/mo)
   - Upgrade monitoring services ($46/mo)

2. **Optimize for Growth**
   - Reduce scraping frequency back to 6h
   - Re-enable daily digest emails
   - Add CDN for static assets

3. **Revenue Milestones**
   - 5 paid users ($95/mo): Cover infrastructure costs
   - 50 paid users ($950/mo): Sustainable profitability
   - 100+ paid users: Scale to production config ($483/mo)

---

## Support & Documentation

- **Production Deployment:** See `DEPLOYMENT-GUIDE.md` for full production setup
- **Architecture:** See `memory-bank/architecture.md` for system design
- **Cost Analysis:** See `memory-bank/tech-stack.md` for detailed cost breakdown
- **Implementation Plan:** See `memory-bank/implementation-plan.md` for feature roadmap

**Questions?** Open an issue at https://github.com/anthropics/claude-code/issues
