# StartInsight - Deployment Guide

## Overview

This guide covers deploying StartInsight to production using:
- **Backend:** Railway or Render (Docker container)
- **Frontend:** Vercel (Next.js)
- **Database:** Railway/Render PostgreSQL
- **Redis:** Railway/Render Redis or Upstash

---

## Prerequisites

- [x] GitHub account and repository
- [x] Railway/Render account
- [x] Vercel account
- [x] API Keys (Anthropic, OpenAI, Firecrawl, Reddit)

---

## Backend Deployment (Railway/Render)

### Option 1: Railway

#### 1. Create New Project
```bash
# Install Railway CLI
npm i -g @railway/cli

# Login
railway login

# Link project
cd backend
railway init
```

#### 2. Add PostgreSQL Database
- In Railway dashboard: `+ New` → `Database` → `PostgreSQL`
- Database URL is automatically added to environment variables

#### 3. Add Redis
- In Railway dashboard: `+ New` → `Database` → `Redis`
- Redis URL is automatically added to environment variables

#### 4. Configure Environment Variables
In Railway dashboard, add:
```env
ENVIRONMENT=production
LOG_LEVEL=info
ANTHROPIC_API_KEY=<your-key>
OPENAI_API_KEY=<your-key>
FIRECRAWL_API_KEY=<your-key>
REDDIT_CLIENT_ID=<your-client-id>
REDDIT_CLIENT_SECRET=<your-secret>
REDDIT_USER_AGENT=StartInsight Bot v1.0
SCRAPE_INTERVAL_HOURS=6
ANALYSIS_BATCH_SIZE=10
CORS_ORIGINS=https://your-frontend.vercel.app
```

#### 5. Deploy
```bash
# Deploy using Dockerfile
railway up

# Or connect GitHub repo for auto-deploy
# In Railway dashboard: Settings → Deploy → Connect GitHub
```

#### 6. Run Database Migrations
```bash
# Connect to Railway shell
railway run bash

# Run migrations
alembic upgrade head
```

---

### Option 2: Render

#### 1. Create New Web Service
- Go to Render dashboard → `New +` → `Web Service`
- Connect GitHub repository
- Select `backend/` as root directory

#### 2. Configure Service
- **Name:** startinsight-api
- **Runtime:** Docker
- **Dockerfile Path:** `./backend/Dockerfile`
- **Region:** Oregon (or nearest to you)
- **Plan:** Starter ($7/month) or Free

#### 3. Add PostgreSQL Database
- `New +` → `PostgreSQL`
- **Name:** startinsight-db
- **Plan:** Starter ($7/month) or Free
- Copy connection string

#### 4. Add Redis
- Use Render Redis addon or external service (Upstash)
- For Upstash:
  1. Create free account at upstash.com
  2. Create Redis database
  3. Copy connection string (starts with `redis://`)

#### 5. Configure Environment Variables
In Render dashboard (Environment tab):
```env
ENVIRONMENT=production
LOG_LEVEL=info
DATABASE_URL=<from-render-postgres>
REDIS_URL=<from-upstash-or-render>
ANTHROPIC_API_KEY=<your-key>
OPENAI_API_KEY=<your-key>
FIRECRAWL_API_KEY=<your-key>
REDDIT_CLIENT_ID=<your-client-id>
REDDIT_CLIENT_SECRET=<your-secret>
REDDIT_USER_AGENT=StartInsight Bot v1.0
SCRAPE_INTERVAL_HOURS=6
ANALYSIS_BATCH_SIZE=10
CORS_ORIGINS=https://your-frontend.vercel.app
```

#### 6. Deploy
- Click `Create Web Service`
- Render automatically builds and deploys
- Monitor logs in dashboard

#### 7. Run Database Migrations
- In Render dashboard: `Shell` tab
```bash
alembic upgrade head
```

---

## Frontend Deployment (Vercel)

### 1. Connect GitHub Repository
- Go to vercel.com → `Add New Project`
- Import your GitHub repository
- Select `frontend/` as root directory

### 2. Configure Project
- **Framework Preset:** Next.js
- **Root Directory:** `frontend/`
- **Build Command:** `npm run build`
- **Output Directory:** `.next`
- **Install Command:** `npm install`

### 3. Set Environment Variables
In Vercel dashboard (Settings → Environment Variables):
```env
NEXT_PUBLIC_API_URL=https://your-backend.railway.app
```
(Replace with your Railway/Render backend URL)

### 4. Deploy
- Click `Deploy`
- Vercel builds and deploys automatically
- Get production URL (e.g., `startinsight.vercel.app`)

### 5. Update Backend CORS
Update backend environment variable:
```env
CORS_ORIGINS=https://startinsight.vercel.app,http://localhost:3000
```

---

## Post-Deployment Configuration

### 1. Update Frontend API URL
If backend URL changes:
```bash
# In Vercel dashboard
Settings → Environment Variables → NEXT_PUBLIC_API_URL
# Update value and redeploy
```

### 2. Verify Health Checks
```bash
# Backend health
curl https://your-backend.railway.app/health

# Should return:
# {"status":"healthy","service":"StartInsight API","version":"0.1.0"}
```

### 3. Test End-to-End
- Visit frontend URL: `https://startinsight.vercel.app`
- Check homepage loads
- Verify insights display correctly
- Test filters and search
- Check detail pages
- Toggle dark mode

---

## Monitoring & Maintenance

### Application Logs

**Railway:**
- Dashboard → Deployments → View Logs
- Real-time log streaming
- Filter by service (web, postgres, redis)

**Render:**
- Dashboard → Logs tab
- Live tail or historical logs
- Download logs for analysis

**Vercel:**
- Dashboard → Deployments → Function Logs
- Real-time monitoring
- Error tracking

### Performance Monitoring

**Backend Metrics:**
- API response times (target: < 500ms)
- Database query performance
- LLM API costs (tracked in logs)
- Task scheduler execution

**Frontend Metrics:**
- Vercel Analytics (built-in)
- Lighthouse scores (target: > 90)
- Core Web Vitals
- Error rates

### Database Backups

**Railway:**
- Automatic daily backups (Pro plan)
- Manual snapshots available

**Render:**
- Automatic daily backups (Starter plan+)
- Point-in-time recovery available

---

## Cost Estimates

### Railway (Recommended for Beginners)
- **PostgreSQL:** $5/month (Starter)
- **Redis:** $5/month (Starter)
- **Web Service:** $5/month (Starter)
- **Total:** ~$15/month

### Render
- **PostgreSQL:** $7/month (Starter)
- **Web Service:** $7/month (Starter)
- **Redis (Upstash):** Free tier (10K requests/day)
- **Total:** ~$14-21/month

### Vercel
- **Hosting:** Free (Hobby plan)
- **Pro:** $20/month (optional, for team collaboration)

### API Costs
- **Anthropic Claude:** ~$0.003/1K input tokens, $0.015/1K output
- **OpenAI GPT-4:** ~$0.005/1K input, $0.015/1K output
- **Firecrawl:** Free tier: 500 credits/month
- **Reddit API:** Free (rate-limited)

**Estimated Monthly API Costs:** $5-20 (depends on usage)

**Total Estimated Costs:** $20-50/month

---

## Troubleshooting

### Backend Issues

**Problem:** Database connection fails
```bash
# Check DATABASE_URL format
# Should be: postgresql+asyncpg://user:pass@host:port/db
# Verify Alembic migrations ran: alembic current
```

**Problem:** Redis connection fails
```bash
# Check REDIS_URL format
# Should be: redis://host:port or rediss://host:port (SSL)
# Test: redis-cli -u $REDIS_URL ping
```

**Problem:** CORS errors in browser console
```bash
# Update backend CORS_ORIGINS to include frontend URL
# Restart backend service
# Clear browser cache
```

### Frontend Issues

**Problem:** API calls fail (Network Error)
```bash
# Verify NEXT_PUBLIC_API_URL is set correctly
# Check backend health endpoint
# Verify CORS configuration
```

**Problem:** Build fails on Vercel
```bash
# Check build logs for errors
# Verify all dependencies in package.json
# Test build locally: npm run build
```

---

## CI/CD Pipeline

### GitHub Actions Workflow
Located at: `.github/workflows/ci-cd.yml`

**Triggers:**
- Push to `main` or `develop` branches
- Pull requests to `main`

**Jobs:**
1. **Backend Tests:** Linting, pytest, coverage
2. **Frontend Tests:** Linting, TypeScript, build
3. **Docker Build:** Build production image
4. **Deploy:** Auto-deploy to production (main branch only)

**Setup:**
1. Add secrets in GitHub repo settings:
   - `RAILWAY_TOKEN` or `RENDER_API_KEY`
   - `VERCEL_TOKEN`
2. Configure deployment commands in workflow
3. Push to main to trigger deployment

---

## Scaling Considerations

### When to Scale

**Indicators:**
- API response time > 1 second (p95)
- Database CPU > 80%
- Redis memory > 80%
- Error rate > 5%

### Scaling Options

**Horizontal Scaling (Railway/Render):**
- Increase instance count (multiple replicas)
- Load balancer automatically configured

**Vertical Scaling:**
- Upgrade PostgreSQL plan (more RAM/CPU)
- Upgrade Redis plan
- Upgrade web service plan

**Optimization:**
- Add Redis caching for insights
- Optimize database queries (indexes)
- Implement CDN for static assets (Vercel automatic)

---

## Security Best Practices

### Environment Variables
- Never commit `.env` files
- Rotate API keys quarterly
- Use separate keys for dev/prod
- Store secrets in platform vaults (Railway/Render secrets)

### CORS Configuration
- Whitelist specific domains only
- Update when frontend URL changes
- Never use `allow_origins=["*"]` in production

### Database
- Use strong passwords (auto-generated)
- Enable SSL connections
- Regular backups enabled
- Restrict access to specific IPs (if possible)

### API Rate Limiting
- Implement rate limiting middleware
- Use Railway/Render built-in DDoS protection
- Monitor for unusual traffic patterns

---

## Support Resources

- **Railway Docs:** https://docs.railway.app
- **Render Docs:** https://render.com/docs
- **Vercel Docs:** https://vercel.com/docs
- **FastAPI Deployment:** https://fastapi.tiangolo.com/deployment/
- **Next.js Deployment:** https://nextjs.org/docs/deployment

---

## Quick Start Checklist

- [ ] Create Railway/Render account
- [ ] Create Vercel account
- [ ] Obtain all API keys
- [ ] Deploy backend (Railway/Render)
- [ ] Run database migrations
- [ ] Deploy frontend (Vercel)
- [ ] Update CORS configuration
- [ ] Test end-to-end functionality
- [ ] Set up monitoring/alerts
- [ ] Configure CI/CD pipeline
- [ ] Document production URLs
- [ ] Celebrate! 🎉

---

**Production URLs:**
- Frontend: `https://your-project.vercel.app`
- Backend API: `https://your-service.railway.app`
- API Docs: `https://your-service.railway.app/docs`
