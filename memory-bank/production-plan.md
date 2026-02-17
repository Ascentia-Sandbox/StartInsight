# Plan: Complete Production Deployment — Staging, CI/CD, Real Data

## Context

StartInsight has completed all 10 phases and is 85% production-ready. The previous plan created env templates and deployment documentation. Now we need a comprehensive production deployment plan that includes:

1. **Staging environment** with separate Supabase database
2. **Real data migration** from dev to staging/production
3. **CI/CD enhancements** for automated staging/production deployments
4. **Security fixes** identified in the audit (frontend .dockerignore, CSP headers)
5. **Pre-deployment checklist** to commit uncommitted work

**Current State:**
- 24 modified files uncommitted (slug migration, route refactoring, env templates)
- 8 untracked files (3 new migrations: c006-c008, utility scripts, new routes)
- DB at head migration (c008)
- CI/CD pipeline exists (.github/workflows/ci-cd.yml) but needs staging support
- Single Supabase Pro instance shared across dev/staging/production ⚠️

**Cost Impact:**
- Current estimate: ~$30/mo (single Supabase Pro + Gemini)
- With staging/prod separation: ~$80-90/mo (3x Supabase Pro @ $25 each)

---

## Phase 1: Pre-Deployment Fixes (Blocking)

### 1.1 Create `frontend/.dockerignore`
**Why:** Frontend Dockerfile has no .dockerignore, risking .env.local leakage into Docker image
**File:** `frontend/.dockerignore` (NEW)
**Content:**
```
# Environment files
.env*
!.env.example
!.env.staging.example
!.env.production.example

# Dependencies
node_modules
.pnpm-store

# Build artifacts
.next
out
build
dist

# Testing
coverage
.nyc_output
playwright-report
test-results

# Development
.vscode
.idea
*.log
npm-debug.log*
.DS_Store

# Git
.git
.gitignore
```

### 1.2 Audit New Migrations (c006-c008)
**Why:** 3 untracked migrations need review before staging deployment
**Files:**
- `backend/alembic/versions/c006_add_insight_slug.py`
- `backend/alembic/versions/c007_fix_insight_slugs.py`
- `backend/alembic/versions/c008_purge_seed_data.py`

**Actions:**
1. Read each migration for correctness
2. Verify they chain properly (c005 → c006 → c007 → c008)
3. Check for data-destructive operations (c008 purges seed data — document this)
4. Ensure idempotency (safe to run twice)

### 1.3 Fix Hardcoded Contact Email (Medium Priority)
**Why:** `backend/app/api/routes/contact.py:50` has `"hello@startinsight.co"` hardcoded
**Change:**
```python
# Before
to_email = "hello@startinsight.co"

# After
to_email = settings.contact_email or settings.email_from_address
```
**Add to config.py:**
```python
contact_email: str = "hello@startinsight.ai"  # Configurable via env
```

### 1.4 Review CSP Headers (Production Only)
**Why:** `backend/app/middleware/security_headers.py` uses `'unsafe-inline'` in CSP
**Current (lines 44-50):**
```python
"script-src 'self' 'unsafe-inline'; "
"style-src 'self' 'unsafe-inline'; "
```
**Issue:** Reduces XSS protection
**Decision:** Document for staging validation, but accept for MVP (Next.js + Tailwind require it)
**Future:** Implement nonce-based CSP or CSS modules

### 1.5 Commit All Uncommitted Work
**Why:** 24 modified + 8 untracked files need to be committed before deployment
**Git workflow:**
```bash
# 1. Stage env templates and deployment configs
git add backend/.env.staging.example backend/.env.production.example
git add frontend/.env.staging.example frontend/.env.production.example
git add backend/railway.toml frontend/vercel.json
git add memory-bank/progress.md memory-bank/active-context.md README.md

# 2. Stage new migrations (after audit)
git add backend/alembic/versions/c006*.py
git add backend/alembic/versions/c007*.py
git add backend/alembic/versions/c008*.py

# 3. Stage new scripts and routes
git add backend/scripts/backfill_trend_data.py backend/scripts/reenrich_insights.py
git add frontend/app/[locale]/insights/[slug]/

# 4. Stage all other modified files
git add backend/app/agents/enhanced_analyzer.py
git add backend/app/api/routes/insights.py backend/app/api/routes/market_insights.py
git add backend/app/models/insight.py backend/app/schemas/insight.py
git add frontend/app/[locale]/founder-fits/page.tsx
git add frontend/app/[locale]/idea-of-the-day/page.tsx
git add frontend/app/[locale]/market-insights/[slug]/page.tsx
# ... (remaining 24 files)

# 5. Commit
git commit -m "feat: production deployment prep — env templates, slug migration, route refactoring"

# 6. Push to SI-Claude-vllm branch
git push origin SI-Claude-vllm
```

---

## Phase 2: Infrastructure Setup (Staging)

### 2.1 Create Separate Supabase Projects
**Why:** Prevent staging/production data contamination, enable safe migration testing
**Cost Impact:** +$50/mo (2 new Supabase Pro projects)

**Projects:**
```
Dev:        Existing Supabase Pro (ap-southeast-2, Sydney)
Staging:    NEW Supabase Pro (ap-southeast-2, Sydney)
Production: NEW Supabase Pro (ap-southeast-2, Sydney)
```

**Actions:**
1. Go to supabase.com > New Project
2. Create "StartInsight-Staging" (ap-southeast-2)
3. Create "StartInsight-Production" (ap-southeast-2)
4. Copy connection strings from each:
   - Dashboard > Settings > Database > Connection string (Connection Pooling mode)
5. Copy API keys from each:
   - Dashboard > Settings > API (URL, Anon key, Service role key)
6. Copy JWT secret from each:
   - Dashboard > Settings > API > JWT Settings > JWT Secret

### 2.2 Update Railway Configuration (Staging)
**Why:** Backend needs separate Railway service for staging
**Actions:**
1. Create new Railway service: "startinsight-backend-staging"
2. Link GitHub repo, set root directory to repo root
3. Add all env vars from `backend/.env.staging.example`:
   - `ENVIRONMENT=staging`
   - `DATABASE_URL=` (Staging Supabase connection string)
   - `SUPABASE_URL=` (Staging Supabase URL)
   - `SUPABASE_SERVICE_ROLE_KEY=` (Staging)
   - `JWT_SECRET=` (Staging Supabase JWT secret)
   - `REDIS_URL=` (Upstash Redis — rediss:// with SSL)
   - `GOOGLE_API_KEY=` (same as dev, pay-as-you-go)
   - `SENTRY_DSN=` (create separate Sentry project)
   - `REFRESH_TOKEN_SECRET=` (generate: `openssl rand -hex 32`)
   - `APP_URL=https://startinsight-staging.up.railway.app`
   - `CORS_ORIGINS=` (will update after Vercel URL known)
   - All other vars from template
4. Deploy and note Railway URL

### 2.3 Update Vercel Configuration (Staging)
**Why:** Frontend needs separate Vercel project for staging
**Actions:**
1. Create new Vercel project: "startinsight-frontend-staging"
2. Import GitHub repo, set root directory to `frontend/`
3. Set framework preset: Next.js
4. Add environment variables (Preview environment):
   - `NEXT_PUBLIC_API_URL=` (Railway staging URL from 2.2)
   - `NEXT_PUBLIC_SUPABASE_URL=` (Staging Supabase URL)
   - `NEXT_PUBLIC_SUPABASE_ANON_KEY=` (Staging anon key)
   - `NEXT_PUBLIC_ENVIRONMENT=staging`
   - `NEXT_PUBLIC_SENTRY_DSN=` (Sentry staging frontend project)

### 2.4 Configure Supabase Auth for Staging
**Why:** Auth redirects need correct URLs for staging
**Actions (Staging Supabase dashboard):**
1. Authentication > URL Configuration
2. Set Site URL: `https://startinsight-staging.vercel.app`
3. Add Redirect URLs:
   - `https://startinsight-staging.vercel.app/**`
   - `https://startinsight-staging.up.railway.app/**` (for API callbacks)
4. Enable Email confirmation (or disable for easier testing)
5. Configure SMTP (or use Supabase email, limit 4/hr on staging)

### 2.5 Run Staging Database Migrations
**Why:** Initialize staging database to c008
**Commands:**
```bash
export DATABASE_URL="postgresql+asyncpg://postgres.[STAGING_REF]:..."
cd backend
alembic upgrade head
alembic current  # Verify at c008
```

---

## Phase 3: Staging Data Seeding

### 3.1 Configure Agent System
**Why:** AI pipeline needs agent configs and prompts to function
**Scripts (run in order):**
```bash
cd backend

# 1. Agent configurations (8 agents)
uv run python scripts/seed_agent_configs.py

# 2. Agent prompts (8 prompts)
uv run python scripts/seed_agent_prompts.py

# 3. Create admin user for testing
uv run python scripts/create_admin.py
# Enter: admin@startinsight.ai / SecurePassword123!

# 4. Verify email (since staging has no email delivery)
uv run python scripts/confirm_user_email.py --email admin@startinsight.ai
```

### 3.2 Generate Test Insights (Staging)
**Why:** Validate end-to-end pipeline with representative data
**Options:**

**Option A: Synthetic Test Data (Fast)**
```bash
uv run python scripts/seed_test_insights.py
# Creates 10 synthetic insights with scores
```

**Option B: Real Scraping + Analysis (Slow, 2+ hours)**
```bash
# 1. Run full data collection (Reddit, Product Hunt, Trends, HN)
uv run python scripts/run_data_collection.py

# 2. Analyze collected signals (triggers AI agents)
# This runs automatically via Arq worker or:
uv run python scripts/backfill_enhanced.py
```

**Recommendation for Staging:** Option A (synthetic data) for speed

### 3.3 Verify Staging Data Integrity
**Why:** Ensure seeding succeeded before E2E tests
**Checks:**
```bash
# 1. Health check
curl https://startinsight-staging.up.railway.app/health
# Expected: {"status":"healthy","environment":"staging"}

# 2. Database health
curl https://startinsight-staging.up.railway.app/health/ready
# Expected: {"status":"healthy","database":"connected","redis":"connected"}

# 3. Insights API
curl https://startinsight-staging.up.railway.app/api/insights?limit=5
# Expected: JSON array with 5+ insights

# 4. Admin login (via frontend)
# Navigate to: https://startinsight-staging.vercel.app/login
# Login as: admin@startinsight.ai / SecurePassword123!
```

---

## Phase 4: CI/CD Enhancements

### 4.1 Update GitHub Actions Workflow
**Why:** Current CI/CD only deploys to production on main branch
**File:** `.github/workflows/ci-cd.yml`
**Changes:**

```yaml
# Add staging deployment trigger
deploy-staging:
  runs-on: ubuntu-latest
  needs: [backend-test, frontend-test, security-scan]
  if: github.ref == 'refs/heads/develop' && github.event_name == 'push'
  steps:
    - name: Deploy to Railway (Staging)
      run: railway up --service startinsight-backend-staging
      env:
        RAILWAY_TOKEN: ${{ secrets.RAILWAY_TOKEN_STAGING }}

    - name: Deploy to Vercel (Staging)
      run: vercel --prod --token ${{ secrets.VERCEL_TOKEN }} --scope staging
      env:
        VERCEL_TOKEN: ${{ secrets.VERCEL_TOKEN_STAGING }}

    - name: Staging health check
      run: |
        curl -f https://startinsight-staging.up.railway.app/health || exit 1
        curl -f https://startinsight-staging.vercel.app || exit 1

# Add Slack notifications (optional but recommended)
notify-failure:
  runs-on: ubuntu-latest
  needs: [deploy-staging, deploy]
  if: failure()
  steps:
    - name: Slack notification
      uses: 8398a7/action-slack@v3
      with:
        status: ${{ job.status }}
        webhook_url: ${{ secrets.SLACK_WEBHOOK_URL }}
```

### 4.2 Create GitHub Branch Protection Rules
**Why:** Prevent direct pushes to main, enforce reviews
**Actions:**
1. Go to GitHub > Settings > Branches > Add rule
2. Branch name pattern: `main`
3. Enable:
   - ✅ Require pull request reviews before merging (1 approval)
   - ✅ Require status checks to pass (backend-test, frontend-test, security-scan)
   - ✅ Require branches to be up to date before merging
   - ✅ Do not allow bypassing the above settings
4. Save

### 4.3 Create GitHub Secrets (Staging + Production)
**Why:** CI/CD needs secure access to Railway/Vercel/Slack
**Secrets:**
```
RAILWAY_TOKEN_STAGING    (Railway CLI token for staging service)
RAILWAY_TOKEN_PRODUCTION (Railway CLI token for production service)
VERCEL_TOKEN_STAGING     (Vercel CLI token, staging scope)
VERCEL_TOKEN_PRODUCTION  (Vercel CLI token, production scope)
SLACK_WEBHOOK_URL        (Optional: Slack incoming webhook for alerts)
```
**How to get:**
- Railway token: `railway login` → `railway whoami` → Copy token
- Vercel token: `vercel login` → Settings > Tokens > Create

### 4.4 Add Database Backup Step (Production Only)
**Why:** Prevent data loss during failed deployments
**Add to CI/CD before production deploy:**
```yaml
- name: Backup production database
  run: |
    curl -X POST https://api.supabase.com/v1/projects/${{ secrets.SUPABASE_PROJECT_ID }}/database/backup \
      -H "Authorization: Bearer ${{ secrets.SUPABASE_SERVICE_ROLE_KEY }}"
```
**Note:** Supabase Pro includes point-in-time recovery (PITR) — backups happen automatically

---

## Phase 5: Staging Validation & Testing

### 5.1 Run Backend Tests Against Staging
**Why:** Validate staging environment matches CI test results
**Commands:**
```bash
export DATABASE_URL="postgresql+asyncpg://postgres.[STAGING_REF]:..."
export REDIS_URL="rediss://default:...@...upstash.io:6379"

cd backend
pytest tests/ -v --cov=app --cov-report=term
# Expected: 233+ tests passing, 85%+ coverage
```

### 5.2 Run Frontend E2E Tests Against Staging
**Why:** Validate full user flows (auth, insights, payments)
**Commands:**
```bash
cd frontend
export NEXT_PUBLIC_API_URL=https://startinsight-staging.up.railway.app
export NEXT_PUBLIC_SUPABASE_URL=https://[STAGING_REF].supabase.co
export NEXT_PUBLIC_SUPABASE_ANON_KEY=...

npx playwright test
# Expected: 47 E2E tests passing across 5 browsers
```

### 5.3 Manual Smoke Tests (Critical Paths)
**Why:** Automated tests don't cover all edge cases
**Checklist:**
```
Frontend (https://startinsight-staging.vercel.app):
- [ ] Homepage loads, counters animate
- [ ] Insights page shows data from staging DB
- [ ] Click insight card → detail page loads
- [ ] Sign up flow (new user)
- [ ] Email verification (manual via Supabase dashboard)
- [ ] Login flow
- [ ] Dashboard page (authenticated)
- [ ] Founder Fits page
- [ ] Idea of the Day page
- [ ] Market Insights (blog) page
- [ ] Logout

Backend (https://startinsight-staging.up.railway.app):
- [ ] /health → 200 OK
- [ ] /health/ready → 200 OK (DB + Redis connected)
- [ ] /api/insights → 200 OK with data
- [ ] /api/insights/{id} → 200 OK
- [ ] /docs → 404 (disabled in staging)
- [ ] /admin/agents → 401 without auth, 200 with admin token
- [ ] POST /api/contact → 200 OK (rate limit check)

Payments (Stripe Test Mode):
- [ ] Checkout flow (card: 4242 4242 4242 4242)
- [ ] Webhook delivery (check Railway logs)
- [ ] Subscription status updates
```

### 5.4 Performance Testing (Optional)
**Why:** Validate Railway free tier (512MB RAM) handles load
**Tools:**
- **k6** (load testing): `k6 run load-test.js`
- **Artillery** (load testing): `artillery run scenario.yml`
**Metrics to watch:**
- Railway memory usage (should stay < 450MB)
- Response times (p95 < 500ms for /api/insights)
- Database connection pool exhaustion

---

## Phase 6: Production Deployment

### 6.1 Create Production Infrastructure
**Repeat Phase 2 steps for production:**
1. Supabase project already created (StartInsight-Production)
2. Create Railway service: "startinsight-backend-production"
   - Use `backend/.env.production.example` template
   - `ENVIRONMENT=production`
   - `APP_URL=https://api.startinsight.app`
   - All **[REQUIRED]** vars from template (see config.py validator)
3. Create Vercel project: "startinsight-frontend-production"
   - Production environment
   - `NEXT_PUBLIC_API_URL=https://api.startinsight.app`
   - `NEXT_PUBLIC_ENVIRONMENT=production`

### 6.2 Run Production Migrations
**Why:** Initialize production database
**Command:**
```bash
export DATABASE_URL="postgresql+asyncpg://postgres.[PROD_REF]:..."
cd backend
alembic upgrade head
alembic current  # Verify at c008
```

### 6.3 Seed Production Data
**Why:** Production needs agent configs but NO test data
**Scripts:**
```bash
cd backend

# 1. Agent configurations
uv run python scripts/seed_agent_configs.py

# 2. Agent prompts
uv run python scripts/seed_agent_prompts.py

# 3. Public content (tools, success stories, trends)
uv run python scripts/seed_public_content.py

# 4. Create admin user (SECURE PASSWORD)
uv run python scripts/create_admin.py
# Use strong password, store in 1Password/LastPass

# 5. Verify email manually
uv run python scripts/confirm_user_email.py --email admin@startinsight.ai
```

**DO NOT RUN:**
- `seed_test_insights.py` (test data only)
- `seed_insights_with_scores.py` (bulk synthetic data)

### 6.4 Configure DNS
**Why:** Point custom domains to Railway + Vercel
**Actions:**
1. **Backend API:**
   - Add CNAME: `api.startinsight.app` → Railway CNAME target
   - Railway dashboard: Add custom domain `api.startinsight.app`
   - Wait for SSL (auto-provisioned by Railway)

2. **Frontend:**
   - Add CNAME: `www.startinsight.app` → `cname.vercel-dns.com`
   - Add CNAME: `startinsight.app` → `cname.vercel-dns.com` (or A record to Vercel IP)
   - Vercel dashboard: Add custom domain `startinsight.app` and `www.startinsight.app`
   - Wait for SSL (auto-provisioned by Vercel)

### 6.5 Update CORS for Production
**Why:** Backend must allow production frontend origin
**Actions:**
1. Railway > startinsight-backend-production > Variables
2. Update `CORS_ORIGINS=https://startinsight.app,https://www.startinsight.app`
3. Redeploy

### 6.6 Production Smoke Tests
**Critical paths (same as staging 5.3 but on production URLs):**
- [ ] https://startinsight.app loads
- [ ] https://api.startinsight.app/health → 200 OK
- [ ] Auth flow works
- [ ] Insights page loads (empty initially — scraping will populate)
- [ ] Admin panel accessible
- [ ] /docs → 404 (production validator enforces)

### 6.7 Start Scraping & Analysis
**Why:** Populate production with real insights
**Actions:**
1. Arq worker auto-starts on Railway (via Dockerfile ENTRYPOINT)
2. Monitor first scrape cycle:
   - Railway logs: `railway logs --service startinsight-backend-production`
   - Expected: Reddit → Product Hunt → Google Trends → Analysis batch
3. Verify insights appear:
   - `curl https://api.startinsight.app/api/insights?limit=10`
4. Monitor Gemini API usage:
   - Google AI Studio > Usage & Billing

---

## Phase 7: Monitoring & Alerting

### 7.1 Configure Sentry Alerts
**Why:** Get notified of production errors
**Actions:**
1. Sentry > startinsight-backend > Alerts > New Alert Rule
   - Condition: 5xx errors > 5 in 5 minutes
   - Action: Email + Slack (if configured)
2. Sentry > startinsight-frontend > Alerts > New Alert Rule
   - Condition: JavaScript errors > 10 in 5 minutes

### 7.2 Set Up Uptime Monitoring (UptimeRobot)
**Why:** Get notified if site goes down
**Actions:**
1. Go to uptimerobot.com (free tier)
2. Add HTTP(s) monitor:
   - URL: `https://api.startinsight.app/health`
   - Interval: 5 minutes
   - Alert: Email when down
3. Add HTTP(s) monitor:
   - URL: `https://startinsight.app`
   - Interval: 5 minutes

### 7.3 Railway Resource Monitoring
**Why:** Avoid OOM crashes (512MB RAM limit on free tier)
**Actions:**
1. Railway dashboard > startinsight-backend-production > Metrics
2. Watch:
   - Memory usage (should stay < 450MB)
   - CPU usage (spikes during scraping are normal)
   - Network (egress for Gemini API calls)
3. If consistently > 450MB:
   - Reduce `WORKER_MAX_JOBS` from 10 to 5
   - Set `USE_CRAWL4AI=false` (removes Playwright/Chromium ~400MB)

### 7.4 Supabase Database Metrics
**Why:** Monitor connection pool usage and query performance
**Actions:**
1. Supabase dashboard > Database > Metrics
2. Watch:
   - Active connections (should stay < 50 of 200 limit)
   - Query duration (p95 < 100ms for indexed queries)
   - Disk usage (Pro tier: 8GB included)

---

## Phase 8: Post-Deployment Documentation

### 8.1 Update memory-bank/active-context.md
**Add:**
```markdown
## Deployment Status (2026-02-XX)

**Current State:** Production live at startinsight.app
**Infrastructure:**
- **Backend:** Railway production (https://api.startinsight.app)
- **Frontend:** Vercel production (https://startinsight.app)
- **Database:** 3x Supabase Pro (dev/staging/prod, ap-southeast-2)
- **Cache/Queue:** Upstash Redis (free tier, TLS)
**Environments:**
- Dev: Local + Supabase dev
- Staging: Railway staging + Vercel preview + Supabase staging
- Production: Railway prod + Vercel prod + Supabase prod
**Monthly Cost:** ~$80-90 (3x Supabase @ $25, Gemini ~$5-10, everything else free)
**Monitoring:**
- Sentry: 2 projects (backend, frontend)
- UptimeRobot: 2 monitors (API, frontend)
- Railway: Resource metrics dashboard
```

### 8.2 Update memory-bank/progress.md
**Add:**
```markdown
- [2026-02-XX] [DEPLOY]: Production deployment complete — 3-tier env separation
  - Files: .dockerignore, contact.py, ci-cd.yml, 24 committed files
  - Tech: Railway + Vercel + 3x Supabase Pro, CI/CD with staging, DNS CNAME setup
  - Status: [✓ Complete]
```

### 8.3 Create Runbook (NEW file)
**File:** `docs/RUNBOOK.md` (NEW)
**Contents:**
- Common operations (restart service, rollback deployment)
- Troubleshooting guide (OOM, connection pool exhaustion, CORS errors)
- Emergency contacts
- Rollback procedure
- Database backup/restore instructions

### 8.4 Document Rollback Procedure
**File:** `docs/ROLLBACK.md` (NEW)
**Steps:**
1. Identify bad deployment (Railway build ID or Vercel deployment ID)
2. Railway: `railway rollback [BUILD_ID]`
3. Vercel: `vercel rollback [DEPLOYMENT_URL]`
4. If database migration caused issue:
   - `alembic downgrade -1` (run against affected DB)
   - Restore from Supabase backup if needed

---

## Verification Checklist

### Pre-Deployment
- [ ] All 24 modified files committed
- [ ] 3 new migrations (c006-c008) audited
- [ ] `frontend/.dockerignore` created
- [ ] Contact email made configurable
- [ ] Backend tests passing (233+)
- [ ] Frontend E2E tests passing (47)

### Staging Infrastructure
- [ ] Supabase staging project created
- [ ] Railway staging service deployed
- [ ] Vercel staging project deployed
- [ ] CORS configured correctly
- [ ] Supabase Auth redirects set
- [ ] Staging smoke tests passed

### CI/CD
- [ ] GitHub Actions updated (staging trigger)
- [ ] Branch protection rules enabled
- [ ] GitHub secrets added (Railway + Vercel tokens)
- [ ] Slack notifications configured (optional)

### Production Infrastructure
- [ ] Supabase production project created
- [ ] Railway production service deployed
- [ ] Vercel production project deployed
- [ ] DNS CNAMEs configured
- [ ] SSL certificates provisioned
- [ ] CORS configured (production origins)

### Production Data
- [ ] Migrations applied (c008 head)
- [ ] Agent configs seeded
- [ ] Agent prompts seeded
- [ ] Public content seeded (tools, stories, trends)
- [ ] Admin user created (secure password)
- [ ] Scraping cycle started (Arq worker)

### Monitoring
- [ ] Sentry alerts configured
- [ ] UptimeRobot monitors active
- [ ] Railway metrics reviewed (memory < 450MB)
- [ ] Supabase connection pool healthy

### Documentation
- [ ] active-context.md updated
- [ ] progress.md updated
- [ ] RUNBOOK.md created
- [ ] ROLLBACK.md created

---

## Critical Files to Modify

| File | Action | Priority |
|------|--------|----------|
| `frontend/.dockerignore` | CREATE | Blocking |
| `backend/alembic/versions/c006*.py` | AUDIT | Blocking |
| `backend/alembic/versions/c007*.py` | AUDIT | Blocking |
| `backend/alembic/versions/c008*.py` | AUDIT | Blocking |
| `backend/app/core/config.py` | ADD contact_email field | Medium |
| `backend/app/api/routes/contact.py` | USE settings.contact_email | Medium |
| `.github/workflows/ci-cd.yml` | ADD staging deployment | Medium |
| `docs/RUNBOOK.md` | CREATE | Nice-to-have |
| `docs/ROLLBACK.md` | CREATE | Nice-to-have |

---

## Risk Assessment

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| Railway OOM (512MB limit) | Medium | High | Monitor metrics, reduce workers, disable Playwright if needed |
| Migration failure on prod | Low | Critical | Test on staging first, have rollback ready |
| CORS misconfiguration | Medium | High | Test staging thoroughly, have exact URLs ready |
| Scraping rate limits | Low | Medium | Use Crawl4AI (free), Reddit JSON API has 1s delay |
| Supabase connection exhaustion | Low | High | Pool size=10, max_overflow=15 (well within 200 limit) |
| DNS propagation delays | High | Low | Wait 1-24 hours for full propagation |
| Cost overrun | Low | Medium | Budget $80-90/mo, monitor Gemini API usage |

---

## Success Criteria

**Staging:**
- ✅ All services healthy (/health endpoints)
- ✅ Auth flow works end-to-end
- ✅ Insights API returns data
- ✅ Admin panel accessible
- ✅ No CORS errors in browser console
- ✅ Backend tests pass (233+)
- ✅ Frontend E2E tests pass (47)

**Production:**
- ✅ Custom domains resolve (startinsight.app, api.startinsight.app)
- ✅ SSL certificates valid
- ✅ Scraping cycle runs successfully
- ✅ Insights start appearing (within 6-12 hours)
- ✅ /docs returns 404 (production mode enforced)
- ✅ Sentry receiving events
- ✅ UptimeRobot shows 100% uptime
- ✅ Railway memory stays < 450MB

---

## Cost Breakdown

| Service | Quantity | Unit Cost | Total |
|---------|----------|-----------|-------|
| Supabase Pro | 3 projects | $25/mo | $75/mo |
| Gemini 2.0 Flash | pay-as-you-go | ~$5-10/mo | $10/mo |
| Railway | Free tier | $0 | $0 |
| Vercel | Hobby tier | $0 | $0 |
| Upstash Redis | Free tier | $0 | $0 |
| Sentry | Free tier | $0 | $0 |
| Resend | Free tier | $0 | $0 |
| UptimeRobot | Free tier | $0 | $0 |
| **Total** | | | **$85/mo** |

**Note:** If Railway free tier runs out of $5 credit, upgrade to Hobby ($5/mo) = **$90/mo total**
