---
**Memory Bank Protocol**
**Reading Priority:** CRITICAL
**Read When:** Before implementing features, designing database models, creating APIs
**Dependencies:** Read active-context.md for current phase, implementation-plan.md for tasks
**Purpose:** System architecture, 21 database tables, 97 API endpoints, auth, RLS, deployment
**Last Updated:** 2026-01-25
---

# System Architecture: StartInsight

## 1. System Overview

**Architecture**: Modular monolith with decoupled frontend/backend
**Core Loops**: Collect → Analyze → Present (3 independent data flows)
**Deployment**: Railway (backend), Vercel (frontend), Supabase (database - Singapore ap-southeast-1)

### Stack

| Component | Technology | Port/URL | Purpose |
|-----------|-----------|----------|---------|
| **Frontend** | Next.js 16.1.3 (App Router) | 3000 | User dashboard, admin portal |
| **Backend** | FastAPI + Uvicorn ASGI | 8000 | REST API (97 endpoints), SSE streaming |
| **Database** | PostgreSQL 16 (Supabase) | 5433 | 21 tables with RLS enabled |
| **Cache/Queue** | Redis 7 | 6379 | Arq task queue, rate limiting |
| **Worker** | Arq + APScheduler | N/A | Background scraping (6-hour intervals) |
| **AI** | Claude 3.5 Sonnet (Anthropic) | API | PydanticAI agents (analysis, research) |
| **Scraper** | Firecrawl, PRAW, pytrends, Tweepy | API | Reddit, Product Hunt, Trends, Twitter/X |
| **Auth** | Supabase Auth | API | JWT-based, RLS integration |
| **Payments** | Stripe | API | Checkout, subscriptions, webhooks |
| **Email** | Resend | API | Transactional emails (6 templates) |

**Connection String**: `postgresql://postgres:[password]@aws-0-ap-southeast-1.pooler.supabase.com:5432/postgres`

---

## 2. System Architecture Diagram

```mermaid
graph TD
    User[User Browser] -->|HTTPS| Frontend[Next.js Frontend]
    Frontend -->|REST API| Backend[FastAPI Backend]
    Frontend -->|Auth/RLS| Supabase[Supabase Auth + DB]

    Backend -->|SQL| Supabase
    Backend -->|Cache| Redis[Redis Cache/Queue]
    Backend -->|Tasks| Worker[Arq Worker]

    Worker -->|Scrape| Reddit[Reddit PRAW]
    Worker -->|Scrape| PH[Product Hunt]
    Worker -->|Scrape| Trends[Google Trends]
    Worker -->|Scrape| Twitter[Twitter/X Tweepy]

    Worker -->|Analyze| Claude[Claude 3.5 Sonnet]
    Worker -->|Store| Supabase

    Backend -->|Payments| Stripe[Stripe API]
    Backend -->|Email| Resend[Resend API]
    Backend -->|SSE| Frontend

    Stripe -->|Webhooks| Backend

    style Frontend fill:#4CAF50
    style Backend fill:#2196F3
    style Supabase fill:#3ECF8E
    style Redis fill:#DC382D
    style Worker fill:#9C27B0
    style Claude fill:#FF5722
```

---

## 3. Data Flow: Three Core Loops

### Loop 1: Collection (Every 6 hours)
```
Scheduler → Arq Worker → [Reddit|PH|Trends|Twitter] → Firecrawl → raw_signals table
```

### Loop 2: Analysis (After collection)
```
Scheduler → Arq Worker → SELECT unprocessed signals → Claude 3.5 Sonnet → insights table → UPDATE signals.processed=true
```

### Loop 3: Presentation (On user request)
```
User → Next.js → GET /api/insights → FastAPI → PostgreSQL → JSON response → Render UI
```

---

## 4. Database Schema (21 Tables)

### 4.1 Core Tables (Phase 1-3)

**`raw_signals`** (Data collection)
- id (UUID PK), source (varchar), url (text), content (text), metadata (JSONB), processed (bool), created_at

**`insights`** (AI analysis output)
- id (UUID PK), raw_signal_id (UUID FK), problem_statement (text), proposed_solution (text), market_size_estimate (enum: Small/Medium/Large), relevance_score (float 0-1), competitor_analysis (JSONB array), created_at
- Enhanced scoring (Phase 4.3): opportunity_score, problem_score, feasibility_score, why_now_score, go_to_market_score, founder_fit_score, execution_difficulty_score (all 1-10)
- Framework fields: value_ladder (JSONB), market_gap_analysis (text), why_now_analysis (text), revenue_potential (text)

### 4.2 User & Auth Tables (Phase 4.1)

**`users`**
- id (UUID PK), supabase_user_id (UUID unique), email, display_name, avatar_url, subscription_tier (enum: free/starter/pro/enterprise), preferences (JSONB), created_at, updated_at

**`saved_insights`** (User workspace)
- id (UUID PK), user_id (UUID FK users), insight_id (UUID FK insights), status (enum: saved/interested/building/not_interested), notes (text), tags (text[]), shared_count (int), saved_at, claimed_at

**`user_ratings`**
- id (UUID PK), user_id (UUID FK), insight_id (UUID FK), rating (int 1-5), feedback (text), rated_at

**`insight_interactions`** (Click tracking)
- id (UUID PK), user_id (UUID FK), insight_id (UUID FK), interaction_type (enum: view/share/export/click), metadata (JSONB), created_at

### 4.3 Admin Tables (Phase 4.2)

**`admin_users`**
- id (UUID PK), user_id (UUID FK users), role (enum: admin/moderator/viewer), permissions (JSONB), created_at

**`agent_execution_logs`**
- id (UUID PK), agent_type (varchar), source (varchar), status (enum: running/success/failed), started_at, completed_at, duration_ms (int), items_processed (int), items_failed (int), error_message (text), metadata (JSONB)

**`system_metrics`**
- id (UUID PK), metric_type (varchar), value (float), unit (varchar), timestamp, metadata (JSONB)

### 4.4 Research & Build Tables (Phase 5.1-5.2)

**`custom_analyses`**
- id (UUID PK), user_id (UUID FK), market_type (varchar), status (enum: pending/processing/completed/failed), result_data (JSONB 40-step output), cost_usd (decimal), created_at, completed_at

### 4.5 Payment Tables (Phase 6.1)

**`subscriptions`**
- id (UUID PK), user_id (UUID FK), stripe_subscription_id (varchar unique), tier (enum: free/starter/pro/enterprise), status (enum: active/canceled/past_due), current_period_end (timestamptz), cancel_at_period_end (bool), created_at, updated_at

**`payment_history`**
- id (UUID PK), user_id (UUID FK), subscription_id (UUID FK), stripe_payment_id (varchar), amount_usd (decimal), status (enum: succeeded/failed/pending), paid_at

**`webhook_events`** (Stripe webhook log)
- id (UUID PK), event_type (varchar), payload (JSONB), processed (bool), created_at

### 4.6 Team Tables (Phase 6.4)

**`teams`**
- id (UUID PK), name (varchar), slug (varchar unique), description (text), owner_id (UUID FK users), member_count (int), created_at

**`team_members`**
- id (UUID PK), team_id (UUID FK teams), user_id (UUID FK users), role (enum: owner/admin/member/viewer), joined_at

**`team_invitations`**
- id (UUID PK), team_id (UUID FK), email (varchar), role (enum), status (enum: pending/accepted/expired), token (varchar unique), expires_at, created_at

**`shared_insights`**
- id (UUID PK), team_id (UUID FK), insight_id (UUID FK insights), shared_by (UUID FK users), notes (text), shared_at

### 4.7 API & Tenant Tables (Phase 7.2-7.3)

**`api_keys`**
- id (UUID PK), user_id (UUID FK), key_prefix (varchar 15), key_hash (varchar 64), name (varchar), description (text), scopes (JSONB array), rate_limit_per_hour (int default 1000), rate_limit_per_day (int default 10000), total_requests (int), last_used_at, expires_at, is_active (bool), created_at, updated_at

**`api_key_usage_logs`**
- id (UUID PK), api_key_id (UUID FK), endpoint (varchar), status_code (int), response_time_ms (int), created_at

**`tenants`** (Multi-tenancy white-label)
- id (UUID PK), name (varchar), subdomain (varchar unique), custom_domain (varchar nullable), logo_url (varchar), primary_color (varchar), app_name (varchar), settings (JSONB), created_at

**`tenant_users`**
- id (UUID PK), tenant_id (UUID FK), user_id (UUID FK users), role (enum: admin/member), joined_at

### 4.8 Indexes

**Critical indexes** (all tables):
- `raw_signals`: idx_source, idx_processed, idx_created_at
- `insights`: idx_relevance_score, idx_created_at, idx_raw_signal_id, idx_opportunity_score
- `saved_insights`: idx_user_id, idx_status
- `user_ratings`: idx_user_id, idx_insight_id
- `api_keys`: idx_user_id, idx_key_prefix, idx_is_active
- `subscriptions`: idx_user_id, idx_stripe_subscription_id
- `teams`: idx_owner_id, idx_slug

---

## 5. API Endpoints (97 Total)

### 5.1 Phase 1-3 (MVP - 8 endpoints)

**Health & Signals**
- `GET /health` - Health check
- `GET /api/signals` - List raw signals (paginated)
- `GET /api/signals/{id}` - Get single signal
- `POST /api/signals/trigger-scrape` - Manual scrape trigger

**Insights**
- `GET /api/insights` - List insights (filters: min_score, source, limit, offset)
- `GET /api/insights/{id}` - Get single insight with raw signal
- `GET /api/insights/daily-top` - Top 5 insights (limit param)
- `GET /api/insights/stats` - Aggregate statistics

### 5.2 Phase 4 (Foundation - 31 endpoints)

**User Workspace** (18 endpoints)
- `GET /api/users/me` - Get current user profile
- `PATCH /api/users/me` - Update profile
- `GET /api/users/me/status` - Workspace status (saved/interested/building counts)
- `GET /api/users/me/saved` - List saved insights (filter: status)
- `GET /api/users/me/ratings` - List user ratings
- `POST /api/users/insights/{id}/save` - Save insight
- `DELETE /api/users/insights/{id}/save` - Unsave insight
- `POST /api/users/insights/{id}/interested` - Mark interested
- `POST /api/users/insights/{id}/claim` - Claim (mark as building)
- `POST /api/users/insights/{id}/rate` - Rate insight
- `GET /api/users/insights/{id}/rate` - Get user's rating
- `POST /api/users/insights/{id}/interact` - Track interaction
- `GET /api/users/insights/{id}/stats` - Get insight interaction stats
- `GET /api/users/idea-of-day` - Get daily recommended insight
- `GET /api/users/recommendations` - Get personalized recommendations
- `POST /api/users/insights/{id}/share` - Share insight (Twitter, LinkedIn, email)
- `GET /api/users/shared-by-me` - List shared insights
- `GET /api/users/shared-with-me` - List insights shared with user

**Admin Portal** (13 endpoints)
- `GET /api/admin/dashboard` - Dashboard metrics (LLM cost, pending insights, errors)
- `GET /api/admin/agents` - List agent statuses
- `POST /api/admin/agents/{type}/pause` - Pause agent
- `POST /api/admin/agents/{type}/resume` - Resume agent
- `POST /api/admin/agents/{type}/trigger` - Manual trigger
- `GET /api/admin/logs` - Agent execution logs (filter: agent_type, status)
- `GET /api/admin/metrics` - System metrics time series
- `GET /api/admin/insights` - Insight review queue (filter: admin_status)
- `PATCH /api/admin/insights/{id}` - Update insight admin status
- `DELETE /api/admin/insights/{id}` - Delete insight
- `GET /api/admin/users` - List users (admin only)
- `PATCH /api/admin/users/{id}` - Update user subscription tier
- `GET /api/admin/stream` - SSE stream (5-second updates)

### 5.3 Phase 5 (Advanced Analysis - 19 endpoints)

**AI Research** (4 endpoints)
- `POST /api/research/analyze` - Start 40-step analysis (async)
- `GET /api/research/{id}` - Get analysis result
- `GET /api/research/my` - List user's analyses
- `DELETE /api/research/{id}` - Delete analysis

**Build Tools** (6 endpoints)
- `POST /api/build/brand` - Generate brand package
- `GET /api/build/brands` - List brand packages
- `GET /api/build/brands/{id}` - Get brand package
- `POST /api/build/landing-page` - Generate landing page
- `GET /api/build/landing-pages` - List landing pages
- `GET /api/build/landing-pages/{id}` - Get landing page

**Export** (5 endpoints)
- `GET /api/export/pdf/{id}` - Export insight to PDF
- `GET /api/export/csv` - Export insights to CSV (filter: date range)
- `GET /api/export/json` - Export insights to JSON
- `GET /api/export/research/{id}/pdf` - Export research report to PDF
- `GET /api/export/brand/{id}/zip` - Export brand package

**Real-time Feed** (4 endpoints)
- `GET /api/feed/stream` - SSE stream for new insights
- `GET /api/feed/latest` - Latest insights (polling fallback)
- `GET /api/feed/filtered` - Filtered feed (score, source)
- `POST /api/feed/subscribe` - Subscribe to feed notifications

### 5.4 Phase 6 (Payments & Teams - 20 endpoints)

**Payments** (5 endpoints)
- `GET /api/payments/pricing` - Get pricing tiers (public)
- `POST /api/payments/checkout` - Create Stripe checkout session
- `POST /api/payments/portal` - Create customer portal session
- `GET /api/payments/subscription` - Get user subscription status
- `POST /api/payments/webhooks/stripe` - Stripe webhook handler

**Teams** (15 endpoints)
- `GET /api/teams` - List user's teams
- `POST /api/teams` - Create team
- `GET /api/teams/{id}` - Get team details
- `PATCH /api/teams/{id}` - Update team
- `DELETE /api/teams/{id}` - Delete team
- `GET /api/teams/{id}/members` - List team members
- `POST /api/teams/{id}/invitations` - Invite member
- `GET /api/teams/{id}/invitations` - List invitations
- `DELETE /api/teams/{id}/invitations/{invitation_id}` - Cancel invitation
- `POST /api/teams/invitations/{token}/accept` - Accept invitation
- `DELETE /api/teams/{id}/members/{user_id}` - Remove member
- `PATCH /api/teams/{id}/members/{user_id}` - Update member role
- `POST /api/teams/{id}/insights/{insight_id}/share` - Share insight to team
- `GET /api/teams/{id}/insights` - List team shared insights
- `DELETE /api/teams/{id}/insights/{insight_id}` - Unshare insight

### 5.5 Phase 7 (API Keys & Multi-tenancy - 19 endpoints)

**API Keys** (8 endpoints)
- `GET /api/keys` - List user's API keys
- `POST /api/keys` - Create API key
- `GET /api/keys/{id}` - Get key details
- `DELETE /api/keys/{id}` - Revoke key
- `GET /api/keys/{id}/usage` - Get usage stats (filter: days)
- `PATCH /api/keys/{id}` - Update key (name, scopes)
- `POST /api/keys/{id}/regenerate` - Regenerate key
- `GET /api/keys/scopes` - List available scopes

**Tenants** (11 endpoints)
- `GET /api/tenants` - List tenants (admin only)
- `POST /api/tenants` - Create tenant (admin only)
- `GET /api/tenants/{id}` - Get tenant details
- `PATCH /api/tenants/{id}` - Update tenant
- `DELETE /api/tenants/{id}` - Delete tenant
- `POST /api/tenants/{id}/users` - Add user to tenant
- `GET /api/tenants/{id}/users` - List tenant users
- `DELETE /api/tenants/{id}/users/{user_id}` - Remove user from tenant
- `PATCH /api/tenants/{id}/branding` - Update branding
- `POST /api/tenants/{id}/domain` - Configure custom domain
- `GET /api/tenants/by-domain/{domain}` - Get tenant by domain

### 5.6 Authentication

**All Phase 4+ endpoints require**:
- `Authorization: Bearer <supabase_jwt>` header
- JWT verified via Supabase Auth

**Public endpoints** (no auth):
- `/health`, `/api/insights` (read-only), `/api/payments/pricing`, `/api/payments/webhooks/stripe`

---

## 6. Authentication & Security

### 6.1 Supabase Auth Flow

```
User → Supabase Auth UI → Email/Password → JWT Token → Frontend Storage (localStorage)
Frontend → API Request → Authorization: Bearer <jwt> → FastAPI Middleware → Supabase verify JWT → Extract user_id → RLS enforcement
```

**Token Structure**:
- Access token: 1-hour expiry
- Refresh token: 7-day expiry (auto-refresh)
- Payload: `{ sub: user_id, email, role }`

### 6.2 Row Level Security (RLS) Policies

**All 20 user-data tables have RLS enabled**:

1. **User-owned data** (users, saved_insights, user_ratings, custom_analyses, subscriptions, api_keys):
   ```sql
   SELECT: user_id = auth.uid()
   INSERT/UPDATE/DELETE: user_id = auth.uid()
   ```

2. **Admin-only** (admin_users, agent_execution_logs, system_metrics, webhook_events):
   ```sql
   SELECT/INSERT/UPDATE/DELETE: auth.uid() IN (SELECT user_id FROM admin_users WHERE role = 'admin')
   ```

3. **Team-based** (teams, team_members, shared_insights):
   ```sql
   SELECT: user_id IN (SELECT user_id FROM team_members WHERE team_id = teams.id)
   INSERT/UPDATE/DELETE: role IN ('owner', 'admin')
   ```

4. **Public read** (insights, raw_signals):
   ```sql
   SELECT: true (public)
   INSERT/UPDATE/DELETE: auth.uid() IN (SELECT user_id FROM admin_users)
   ```

### 6.3 Rate Limiting

**Redis-based sliding window** (SlowAPI middleware):
- Free: 100 req/hour, 1K req/day
- Starter: 500 req/hour, 5K req/day
- Pro: 2K req/hour, 20K req/day
- Enterprise: 10K req/hour, 100K req/day

**API Key rate limits** (separate from user tier):
- Default: 1K req/hour, 10K req/day
- Configurable per key

### 6.4 Security Measures

- HTTPS only (enforced in production)
- CORS whitelist (frontend domain only)
- SQL injection: SQLAlchemy parameterized queries
- XSS: React auto-escaping
- CSRF: SameSite cookies
- Secrets: Environment variables (never committed)
- API keys: SHA256 hashed storage
- Password: Supabase bcrypt hashing

---

## 7. Server-Sent Events (SSE)

**Admin Dashboard Real-time Updates**:
```
Frontend → EventSource('/api/admin/stream') → Backend sends JSON every 5s → Frontend updates metrics
```

**Payload**:
```json
{
  "agent_states": {"collector": "running", "analyzer": "running"},
  "pending_insights": 42,
  "llm_cost_today": 12.50,
  "total_insights_today": 87,
  "errors_today": 3,
  "timestamp": "2026-01-25T10:30:00Z"
}
```

**Real-time Feed** (Phase 5.4):
```
Frontend → EventSource('/api/feed/stream') → New insights → Toast notification
```

---

## 8. Deployment Architecture

### 8.1 Production Stack

| Service | Platform | Region | Specs |
|---------|----------|--------|-------|
| **Frontend** | Vercel | Global CDN | Edge runtime, ISR |
| **Backend** | Railway | US/Singapore | 2 vCPU, 4GB RAM |
| **Database** | Supabase | Singapore (ap-southeast-1) | Pro tier, connection pooling |
| **Redis** | Upstash | Global | 1GB memory, persistent |
| **Worker** | Railway | Same as backend | Background process |

### 8.2 Environment Variables

**Backend (.env)**:
```bash
# Database
DATABASE_URL=postgresql://postgres:[password]@aws-0-ap-southeast-1.pooler.supabase.com:5432/postgres
SUPABASE_URL=https://mxduetfcsgttwwgszjae.supabase.co
SUPABASE_ANON_KEY=eyJhbGc...

# Redis
REDIS_URL=redis://[host]:6379

# External APIs
ANTHROPIC_API_KEY=sk-ant-...
FIRECRAWL_API_KEY=fc-...
STRIPE_API_KEY=sk_live_...
STRIPE_WEBHOOK_SECRET=whsec_...
RESEND_API_KEY=re_...
TWITTER_BEARER_TOKEN=AAAA...

# Config
ENVIRONMENT=production
API_BASE_URL=https://api.startinsight.ai
CORS_ORIGINS=https://startinsight.ai
```

**Frontend (.env.local)**:
```bash
NEXT_PUBLIC_API_URL=https://api.startinsight.ai
NEXT_PUBLIC_SUPABASE_URL=https://mxduetfcsgttwwgszjae.supabase.co
NEXT_PUBLIC_SUPABASE_ANON_KEY=eyJhbGc...
```

### 8.3 Database Connection Pooling

**Supabase Pooler** (Supavisor):
- Mode: Transaction pooling
- Max connections: 500 (Pro tier)
- Connection string: `*.pooler.supabase.com:5432`
- Backend uses: AsyncPG with `pool_size=20, max_overflow=10`

**Direct connection** (for migrations only):
```
postgresql://postgres:[password]@db.mxduetfcsgttwwgszjae.supabase.co:5432/postgres
```

---

## 9. AI Architecture

### 9.1 PydanticAI Agents

**Basic Analyzer** (Phase 2):
- Model: Claude 3.5 Sonnet
- Input: RawSignal content (markdown)
- Output: InsightSchema (problem, solution, market_size, relevance_score, competitor_analysis)
- Cost: $0.003/insight

**Enhanced Analyzer** (Phase 4.3):
- Additional output: 7-dimension scores, value_ladder, market_gap_analysis, why_now_analysis
- Cost: $0.05/insight

**Research Agent** (Phase 5.1):
- 40-step iterative analysis (market sizing, competitor deep-dive, frameworks)
- Cost: $2.50-$5.00/research
- Async execution with webhook callback

### 9.2 Prompt Engineering

**System Prompt** (Enhanced Analyzer):
```
You are a startup idea analyst. Analyze the provided market signal and extract:
1. Problem statement (2-3 sentences, specific pain point)
2. Proposed solution (2-3 sentences, clear value prop)
3. Market size estimate (Small <$100M, Medium $100M-$1B, Large >$1B)
4. Relevance score (0.0-1.0, how actionable is this opportunity)
5. Top 3 competitors (name, URL, market position)
6. 7-dimension scoring (1-10 scale):
   - Opportunity: Market size, growth rate
   - Problem: Severity, frequency, willingness to pay
   - Feasibility: Technical complexity, resource requirements
   - Why Now: Market timing, regulatory changes, tech enablers
   - Go-to-Market: Customer acquisition cost, viral potential
   - Founder Fit: Required expertise, network, credibility
   - Execution Difficulty: Time to market, defensibility
7. Value Ladder: 3-tier pricing strategy
8. Market Gap Analysis: What competitors miss
9. Why Now Analysis: 3 timing factors
```

**Output Schema** (Pydantic):
```python
class Competitor(BaseModel):
    name: str
    url: HttpUrl
    description: str
    market_position: Literal["Small", "Medium", "Large"]

class InsightSchema(BaseModel):
    problem_statement: str
    proposed_solution: str
    market_size_estimate: Literal["Small", "Medium", "Large"]
    relevance_score: float = Field(ge=0, le=1)
    competitor_analysis: list[Competitor]
    opportunity_score: int = Field(ge=1, le=10)
    problem_score: int = Field(ge=1, le=10)
    feasibility_score: int = Field(ge=1, le=10)
    why_now_score: int = Field(ge=1, le=10)
    go_to_market_score: int = Field(ge=1, le=10)
    founder_fit_score: int = Field(ge=1, le=10)
    execution_difficulty_score: int = Field(ge=1, le=10)
    value_ladder: dict  # Free, Starter, Pro tiers
    market_gap_analysis: str
    why_now_analysis: str
    revenue_potential: str
```

### 9.3 Cost Tracking

**MetricsTracker** (singleton service):
```python
# LLM API usage logging
MetricsTracker.track_llm_usage(
    model="claude-3-5-sonnet-20241022",
    input_tokens=1500,
    output_tokens=800,
    cost_usd=0.05
)

# Query system_metrics table for daily cost
SELECT SUM(value) FROM system_metrics
WHERE metric_type = 'llm_cost_usd'
AND timestamp >= CURRENT_DATE
```

**Rate limit handling**:
- Tenacity retry: 3 attempts, exponential backoff (2s, 4s, 8s)
- Fallback: GPT-4o if Claude rate-limited (not implemented in Phase 1-3)

---

## 10. Performance Optimizations

### 10.1 Caching Strategy

**Redis cache layers**:
1. **API response cache** (60-second TTL):
   - `/api/insights/daily-top` → Cache key: `insights:daily-top:2026-01-25`
   - `/api/users/idea-of-day` → Cache key: `idea-of-day:{user_id}`

2. **Database query cache** (5-minute TTL):
   - Trending insights, user stats

3. **Rate limit counters** (sliding window):
   - Key: `ratelimit:{tier}:{user_id}:{hour}`

### 10.2 Database Query Optimization

**Efficient queries**:
```python
# BAD: N+1 query problem
insights = await session.execute(select(Insight))
for insight in insights:
    raw_signal = await session.execute(select(RawSignal).where(RawSignal.id == insight.raw_signal_id))

# GOOD: Eager loading with selectinload
insights = await session.execute(
    select(Insight).options(selectinload(Insight.raw_signal))
)
```

**Indexes**:
- `insights.relevance_score` (DESC) - Most queries sort by score
- `insights.created_at` (DESC) - Daily top queries
- `saved_insights.user_id` - User workspace lookups
- Composite: `(user_id, status)` on saved_insights

### 10.3 Frontend Optimization

**React Query caching**:
```typescript
{
  staleTime: 60000,  // 1 minute
  cacheTime: 300000, // 5 minutes
  refetchOnWindowFocus: false
}
```

**Next.js ISR** (Incremental Static Regeneration):
- `/insights/[id]` → Revalidate every 60 seconds
- Static generation for public insight pages

---

## 11. Glue Coding Architecture

**Philosophy**: Prefer integration over implementation. Use battle-tested libraries instead of custom code.

### 11.1 Key Integrations

| Feature | Library | Why Not Custom |
|---------|---------|----------------|
| Web scraping | Firecrawl SDK | AI-powered, handles JS rendering, anti-bot bypass |
| AI agents | PydanticAI | Type-safe LLM outputs, built-in validation |
| Task queue | Arq | Redis-based, async, cron support |
| Auth | Supabase Auth | JWT + RLS, managed service |
| Payments | Stripe | PCI compliance, webhook handling |
| Email | Resend | High deliverability, templates |
| Rate limiting | SlowAPI | Redis-backed, proven algorithm |

### 11.2 Custom Code (Minimal)

**Only custom logic**:
1. Business rules (scoring thresholds, tier limits)
2. Domain models (Insight, SavedInsight schemas)
3. API route handlers (FastAPI endpoints)
4. Frontend components (InsightCard, Dashboard)

**No custom**:
- Authentication system (Supabase)
- Payment processing (Stripe)
- Email delivery (Resend)
- Web scraping engine (Firecrawl)
- LLM interaction (PydanticAI)

---

## 12. Monitoring & Error Handling

### 12.1 Logging Strategy

**Structured logging** (JSON format):
```python
logger.info(
    "insight_created",
    extra={
        "insight_id": insight.id,
        "relevance_score": insight.relevance_score,
        "llm_cost_usd": 0.05,
        "processing_time_ms": 1250
    }
)
```

**Log levels**:
- DEBUG: Development only (query logging)
- INFO: Business events (insight created, user signup)
- WARNING: Recoverable errors (rate limit hit, retry attempt)
- ERROR: Failed operations (LLM timeout, webhook failure)
- CRITICAL: System failures (database unreachable)

### 12.2 Error Handling

**Retry logic** (Tenacity):
```python
@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=2, min=2, max=10),
    retry=retry_if_exception_type(httpx.TimeoutException)
)
async def analyze_signal(signal: RawSignal) -> Insight:
    ...
```

**Error responses** (FastAPI):
```json
{
  "detail": "Rate limit exceeded",
  "error_code": "RATE_LIMIT_EXCEEDED",
  "retry_after": 3600
}
```

### 12.3 Key Metrics

**Track in system_metrics table**:
- `llm_cost_usd` - Daily AI spend
- `insights_created` - Daily insight count
- `api_response_time_ms` - P50/P95/P99 latency
- `error_rate` - Failed requests / total requests
- `active_users` - Daily/monthly active users

**Alerting thresholds**:
- LLM cost > $50/day
- Error rate > 5%
- P95 latency > 500ms
- Database connections > 450

---

## 13. Testing Strategy

### 13.1 Backend Tests (pytest)

**Unit tests** (137 passing):
- Model validation (Pydantic schemas)
- Service logic (user_service, payment_service)
- Agent output (PydanticAI schema validation)

**Integration tests** (45 passing):
- API endpoints (FastAPI TestClient)
- Database operations (async SQLAlchemy)
- External APIs (mocked Firecrawl, Stripe, Anthropic)

**Test fixtures**:
```python
@pytest.fixture
async def db_session():
    async with async_sessionmaker() as session:
        yield session
        await session.rollback()

@pytest.fixture
def mock_claude():
    with patch("anthropic.Anthropic.messages.create") as mock:
        mock.return_value = Mock(content=[{"text": "..."}])
        yield mock
```

### 13.2 Frontend Tests (Playwright)

**E2E tests** (47 passing for Phase 1-3):
- Cross-browser (Chrome, Firefox, Safari, Mobile)
- User flows (browse insights, filter, detail view)
- Dark mode toggle
- Responsive design (mobile, tablet, desktop)

**Test pending** (Phase 4-7):
- Authentication flows (login, logout, session refresh)
- Workspace interactions (save, rate, claim)
- Admin dashboard (agent control, moderation)
- Payment flows (Stripe checkout, portal)

---

## Conclusion

StartInsight architecture prioritizes:
1. **Simplicity**: Glue coding over custom implementation
2. **Reliability**: Battle-tested libraries (Supabase, Stripe, Firecrawl)
3. **Scalability**: Async Python, connection pooling, Redis caching
4. **Security**: RLS policies, JWT auth, HTTPS enforcement
5. **Performance**: Query optimization, eager loading, ISR

**Next action**: Production deployment (Railway + Vercel + Supabase)
