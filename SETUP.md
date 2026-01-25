# StartInsight - Cloud-First Setup Guide

> **IMPORTANT:** StartInsight uses cloud services by default. NO local database/Redis required.

This guide will help you set up StartInsight for development and production. The entire stack runs on cloud services to ensure consistency between development and production environments.

## Architecture Overview

```
Frontend (Next.js 14) → Backend (FastAPI) → Supabase PostgreSQL
                                          ↓
                                    Upstash Redis
```

- **Database**: Supabase Cloud PostgreSQL (Asia Pacific - Singapore)
- **Authentication**: Supabase Auth (JWT-based)
- **Cache/Queue**: Upstash Redis (Asia Pacific)
- **Backend**: FastAPI (Python 3.12)
- **Frontend**: Next.js 14 (TypeScript, React 19)

---

## Prerequisites

### 1. Supabase Account (Database + Authentication)

1. Sign up at https://supabase.com
2. Create a new project:
   - **Region**: Asia Pacific (Southeast) - ap-southeast-1 Singapore
   - **Database Password**: Save this securely (you'll need it for DATABASE_URL)
3. After creation, navigate to **Project Settings > API**:
   - Copy **Project URL** (e.g., `https://abcdefgh.supabase.co`)
   - Copy **anon public** key (safe to expose in frontend)
   - Copy **service_role** key (keep secret, backend only)
4. Navigate to **Project Settings > Database > Connection string**:
   - Select **Connection Pooling** mode
   - Copy the connection string (use this for DATABASE_URL)

### 2. Upstash Account (Redis)

1. Sign up at https://upstash.com
2. Create a new Redis database:
   - **Region**: Asia Pacific Southeast (Singapore) - for lowest latency
   - **Type**: Regional (not Global)
3. After creation:
   - Copy the **REST API > UPSTASH_REDIS_REST_URL** (format: `redis://default:[password]@[endpoint].upstash.io:6379`)

### 3. API Keys (Development)

You'll need these for full functionality:

- **Google Gemini API**: https://makersuite.google.com/app/apikey (Primary LLM)
- **Firecrawl API**: https://firecrawl.dev/ (Web scraping to Markdown)
- **Reddit API**: https://www.reddit.com/prefs/apps (PRAW credentials)
  - Create an application (script type)
  - Note Client ID, Client Secret, and your username

---

## Backend Setup

### Step 1: Environment Configuration

```bash
cd backend

# Copy environment template
cp .env.example .env

# Edit .env with your credentials
nano .env  # or use your preferred editor
```

**Required Environment Variables:**

```bash
# Database (Supabase)
DATABASE_URL=postgresql+asyncpg://postgres.[PROJECT_REF]:[DB_PASSWORD]@aws-0-ap-southeast-1.pooler.supabase.com:6543/postgres?pgbouncer=true

# Supabase Authentication
SUPABASE_URL=https://[PROJECT_REF].supabase.co
SUPABASE_ANON_KEY=your_supabase_anon_key_here
SUPABASE_SERVICE_ROLE_KEY=your_supabase_service_role_key_here

# JWT Secret (from Supabase Dashboard > Project Settings > API > JWT Settings)
JWT_SECRET=your_jwt_secret_from_supabase_min_32_chars

# Redis (Upstash)
REDIS_URL=redis://default:[PASSWORD]@[ENDPOINT].upstash.io:6379

# AI APIs
GOOGLE_API_KEY=your_google_gemini_api_key
FIRECRAWL_API_KEY=your_firecrawl_api_key

# Reddit API (PRAW)
REDDIT_CLIENT_ID=your_reddit_client_id
REDDIT_CLIENT_SECRET=your_reddit_client_secret
REDDIT_USER_AGENT=StartInsight Bot v1.0 (by /u/your_username)
REDDIT_USERNAME=your_reddit_username
```

### Step 2: Install Dependencies

```bash
# Install uv (if not already installed)
curl -LsSf https://astral.sh/uv/install.sh | sh

# Install project dependencies
uv sync
```

### Step 3: Run Database Migrations

```bash
# Run all pending migrations
alembic upgrade head

# Verify migration success
alembic current
```

**Expected Output:**
```
INFO  [alembic.runtime.migration] Running upgrade  -> a001_initial_schema
INFO  [alembic.runtime.migration] Running upgrade a001 -> a002_add_users_table
...
INFO  [alembic.runtime.migration] Running upgrade b004 -> b005_add_rls_policies
```

### Step 4: Start Backend Server

```bash
# Development mode (auto-reload on code changes)
uvicorn app.main:app --reload

# Or using uv
uv run uvicorn app.main:app --reload
```

**Expected Output:**
```
INFO:     Uvicorn running on http://0.0.0.0:8000 (Press CTRL+C to quit)
INFO:     Started reloader process [12345] using WatchFiles
INFO:     Started server process [12346]
INFO:     Waiting for application startup.
INFO:     Application startup complete.
```

### Step 5: Verify Backend

Open http://localhost:8000/health in your browser. You should see:

```json
{
  "status": "healthy",
  "version": "1.0.0",
  "environment": "development"
}
```

---

## Frontend Setup

### Step 1: Environment Configuration

```bash
cd frontend

# Copy environment template
cp .env.example .env.local

# Edit .env.local with your credentials
nano .env.local  # or use your preferred editor
```

**Required Environment Variables:**

```bash
# Backend API URL (local development)
NEXT_PUBLIC_API_URL=http://localhost:8000

# Supabase Configuration
NEXT_PUBLIC_SUPABASE_URL=https://[PROJECT_REF].supabase.co
NEXT_PUBLIC_SUPABASE_ANON_KEY=your_supabase_anon_key_here
```

### Step 2: Install Dependencies

```bash
npm install
```

### Step 3: Start Frontend Server

```bash
npm run dev
```

**Expected Output:**
```
▲ Next.js 16.1.3 (Turbopack)
- Local:        http://localhost:3000
- Network:      http://192.168.x.x:3000

✓ Starting...
✓ Ready in 1.2s
```

### Step 4: Verify Frontend

Open http://localhost:3000 in your browser. You should see the StartInsight homepage with:
- Navigation bar (Home, All Insights, Sign in)
- "Top 5 Insights of the Day" heading
- Insight cards (if sample data exists) or empty state

---

## Database Initialization

### Creating Sample Data (Optional)

After running migrations, you can add sample data for testing:

```bash
cd backend

# Create sample insights via SQL
cat << 'EOF' | psql $DATABASE_URL
-- Insert sample raw signals
INSERT INTO raw_signals (id, source, content, url, created_at, processed, extra_metadata) VALUES
(gen_random_uuid(), 'reddit', 'Looking for better project management tool', 'https://reddit.com/r/startups/example1', NOW(), true, '{}'::jsonb);

-- Insert sample insights
INSERT INTO insights (
  id, raw_signal_id, title, problem_statement, proposed_solution,
  market_size_estimate, relevance_score, created_at,
  community_signals_chart, enhanced_scores, trend_keywords, competitor_analysis
) VALUES
(gen_random_uuid(), (SELECT id FROM raw_signals LIMIT 1),
 'AI-Powered Project Management',
 'Teams struggle with task coordination',
 'AI assistant that auto-organizes tasks',
 '$1B-$5B', 0.9, NOW(),
 '[{"platform": "Reddit", "score": 8, "members": 50000, "engagement_rate": 0.15}]'::jsonb,
 '[{"dimension": "Opportunity", "value": 9, "label": "Very Strong"}]'::jsonb,
 '{"keywords": ["AI", "project management", "productivity"]}'::jsonb,
 '[]'::jsonb);
EOF
```

### Creating Admin User

1. Sign up via the frontend at http://localhost:3000/auth/login
2. In Supabase Dashboard:
   - Go to **Authentication > Users**
   - Find your user
   - Copy the User ID
3. Run SQL to make yourself admin:

```sql
INSERT INTO admin_users (id, user_id, role, created_at)
VALUES (gen_random_uuid(), '[YOUR_USER_ID]', 'admin', NOW());
```

---

## Verification Checklist

### Backend Health Checks

- [ ] Backend starts without errors
- [ ] Health endpoint responds: `curl http://localhost:8000/health`
- [ ] Supabase connection working (check console logs for database queries)
- [ ] Insights API responds: `curl http://localhost:8000/api/insights`

### Frontend Health Checks

- [ ] Frontend starts without errors
- [ ] Homepage loads at http://localhost:3000
- [ ] Backend API calls work (check Network tab in browser DevTools)
- [ ] No console errors in browser

### Database Health Checks

- [ ] Migrations completed successfully
- [ ] Tables created (20 tables expected)
- [ ] RLS policies enabled (check Supabase Dashboard > Authentication > Policies)

---

## Common Issues & Troubleshooting

### Database Connection Errors

**Error:** `asyncpg.exceptions.ConnectionDoesNotExistError`

**Solution:**
1. Verify DATABASE_URL format in `.env`:
   ```
   postgresql+asyncpg://postgres.[REF]:[PASSWORD]@aws-0-ap-southeast-1.pooler.supabase.com:6543/postgres?pgbouncer=true
   ```
2. Check Supabase project is not paused:
   - Free tier projects pause after 7 days of inactivity
   - Go to Supabase Dashboard and wake up your project
3. Verify IP whitelisting:
   - Go to Supabase Dashboard > Settings > Database > Connection Pooling
   - Ensure "Allow connections from anywhere" is enabled (or add your IP)

### Redis Connection Errors

**Error:** `redis.exceptions.ConnectionError`

**Solution:**
1. Verify REDIS_URL format in `.env`:
   ```
   redis://default:[PASSWORD]@[ENDPOINT].upstash.io:6379
   ```
2. Check Upstash database status (should be "Active")
3. Test connection: `redis-cli -u $REDIS_URL ping`

### Migration Errors

**Error:** `alembic.util.exc.CommandError: Can't locate revision identified by 'xxxx'`

**Solution:**
```bash
# Reset alembic version table
psql $DATABASE_URL -c "TRUNCATE alembic_version;"

# Rerun migrations
alembic upgrade head
```

### Frontend API Errors

**Error:** `CORS policy: No 'Access-Control-Allow-Origin' header`

**Solution:**
1. Verify `CORS_ORIGINS` in backend `.env` includes `http://localhost:3000`
2. Restart backend server
3. Clear browser cache and reload

### JWT Authentication Errors

**Error:** `Invalid JWT signature`

**Solution:**
1. Ensure `JWT_SECRET` in backend `.env` matches the JWT Secret from Supabase Dashboard
2. JWT Secret must be at least 32 characters
3. Restart backend server after changing JWT_SECRET

---

## Production Deployment

### Railway (Backend)

1. **Connect Repository:**
   - Go to Railway Dashboard
   - Click "New Project" > "Deploy from GitHub repo"
   - Select `StartInsight` repository

2. **Configure Environment Variables:**
   - Go to your service > Variables
   - Add all variables from `.env` (use production values)
   - **IMPORTANT**: Set `ENVIRONMENT=production`

3. **Deploy:**
   - Railway will auto-deploy from `main` branch
   - Note your backend URL (e.g., `https://startinsight-backend.railway.app`)

### Vercel (Frontend)

1. **Connect Repository:**
   - Go to Vercel Dashboard
   - Click "New Project" > Import Git Repository
   - Select `StartInsight` repository
   - Set Root Directory: `frontend`

2. **Configure Environment Variables:**
   - Add variables from `.env.local`
   - **IMPORTANT**: Update `NEXT_PUBLIC_API_URL` to your Railway backend URL

3. **Deploy:**
   - Vercel will auto-deploy from `main` branch
   - Custom domain can be configured in project settings

### Post-Deployment Checklist

- [ ] Backend health check: `curl https://your-backend.railway.app/health`
- [ ] Frontend loads: Open https://your-app.vercel.app
- [ ] Authentication works (sign up, sign in, sign out)
- [ ] RLS policies active (users can only access their own data)
- [ ] Stripe configured (if using payments)
- [ ] Error tracking setup (Sentry recommended)

---

## Development Workflow

### Running Tests

```bash
# Backend tests
cd backend
uv run pytest tests/ -v

# Frontend tests (when implemented)
cd frontend
npm test
```

### Database Migrations

```bash
# Create new migration
alembic revision --autogenerate -m "description of changes"

# Review generated migration file
cat alembic/versions/xxxx_description_of_changes.py

# Apply migration
alembic upgrade head

# Rollback migration
alembic downgrade -1
```

### Code Quality

```bash
# Backend linting
cd backend
uv run ruff check . --fix

# Frontend linting
cd frontend
npm run lint
```

---

## Support

- **Documentation**: See `memory-bank/` directory for architecture and implementation details
- **GitHub Issues**: Report bugs or request features
- **Supabase Docs**: https://supabase.com/docs
- **FastAPI Docs**: https://fastapi.tiangolo.com
- **Next.js Docs**: https://nextjs.org/docs

---

## License

StartInsight is built for market intelligence and startup ideation.
