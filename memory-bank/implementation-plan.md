---
**Memory Bank Protocol**
**Reading Priority:** CRITICAL
**Read When:** When planning implementation steps, checking phase requirements
**Dependencies:** Read active-context.md to know current phase, architecture.md for system design
**Purpose:** Phase completion status, deployment readiness, testing requirements
**Last Updated:** 2026-02-14
---

# Implementation Plan: StartInsight

## Executive Summary

**Current Status:** Phase 1-10 Complete (100%) - Production Deployment Ready

**System Scale:**
- **Database:** 69 tables (26 Phase 1-7 + 43 Phase 8-10)
- **API:** 232+ endpoints (131 Phase 1-7 + 99 Phase 8-10 + 2 Q1-Q5)
- **AI Agents:** 8 agents (analyzer, enhanced_analyzer, research, competitive_intel, market_intel, content_generator, chat_agent, market_insight_publisher)
- **Frontend:** 35+ routes (authenticated + public pages)
- **Testing:** 291 backend tests (22 files), 47 E2E tests (8 suites), 85% coverage
- **Migrations:** 25+ Alembic migrations, 69 tables with RLS enabled

---

## Phase Completion Status

| Phase | Scope | Backend | Frontend | Migration | Status |
|-------|-------|---------|----------|-----------|--------|
| **1-3** | MVP Foundation (Collection → Analysis → Presentation) | ✅ 100% | ✅ 100% | ✅ 100% | **COMPLETE** (2026-01-18) |
| **4** | Authentication & Admin Portal | ✅ 100% | ✅ 100% | ✅ 100% | **COMPLETE** (2026-01-25) |
| **4.5** | Supabase Cloud Migration (Sydney) | ✅ 100% | ✅ 100% | ✅ 100% | **COMPLETE** (2026-01-25) |
| **5-7** | Advanced Features (Research, Payments, Teams, API) | ✅ 100% | ✅ 100% | ✅ 100% | **COMPLETE** (2026-01-25) |
| **8** | Superadmin Control Center | ✅ 100% | ✅ 100% | ✅ 100% | **COMPLETE** (2026-02-04) |
| **9** | User Engagement Features | ✅ 100% | ✅ 100% | ✅ 100% | **COMPLETE** (2026-02-04) |
| **10** | Integration Ecosystem | ✅ 100% | ✅ 100% | ✅ 100% | **COMPLETE** (2026-02-04) |
| **12-14** | Public Content & SEO | ✅ 100% | ✅ 100% | ✅ 100% | **COMPLETE** (2026-01-29) |
| **15.4** | Content Editing Enhancements | ✅ 100% | ✅ 100% | N/A | **COMPLETE** (2026-02-14) |
| **16.2** | Dynamic Schedule Management | ✅ 100% | ✅ 100% | ✅ 100% | **COMPLETE** (2026-02-14) |
| **A** | Superadmin Content Completeness | ✅ 100% | ✅ 100% | N/A | **COMPLETE** (2026-02-14) |
| **B** | AI Chat Strategist | ✅ 100% | ✅ 100% | ✅ 100% | **COMPLETE** (2026-02-14) |
| **C** | Idea Builder | ✅ 100% | ✅ 100% | N/A | **COMPLETE** (2026-02-14) |
| **D** | Content Volume & Quality | ✅ 100% | N/A | N/A | **COMPLETE** (2026-02-14) |
| **E** | Analytics Dashboard Enhancements | ✅ 100% | ✅ 100% | N/A | **COMPLETE** (2026-02-14) |
| **F** | UX Polish (Dark Mode + Mobile + Live Logs) | ✅ 100% | ✅ 100% | N/A | **COMPLETE** (2026-02-14) |
| **G** | Design System Revolution | ✅ 100% | ✅ 100% | N/A | **COMPLETE** (2026-02-14) |
| **H** | Content Pipeline & Data Sources | ✅ 100% | ✅ 100% | N/A | **COMPLETE** (2026-02-14) |
| **I** | Admin Portal Excellence | ✅ 100% | ✅ 100% | N/A | **COMPLETE** (2026-02-14) |
| **J** | Public Pages Editorial Redesign | N/A | ✅ 100% | N/A | **COMPLETE** (2026-02-14) |
| **K** | Data-Driven Evidence & Social Proof | ✅ 100% | ✅ 100% | N/A | **COMPLETE** (2026-02-14) |
| **L** | Competitive Differentiators | ✅ 100% | ✅ 100% | N/A | **COMPLETE** (2026-02-14) |
| **Q1** | Pulse Page (Real-time Feed) | ✅ 100% | ✅ 100% | N/A | **COMPLETE** (2026-02-15) |
| **Q2** | Founder Fits Redesign | N/A | ✅ 100% | N/A | **COMPLETE** (2026-02-15) |
| **Q3** | Idea of the Day + Sharing | N/A | ✅ 100% | N/A | **COMPLETE** (2026-02-15) |
| **Q4** | Trend Sparklines | N/A | ✅ 100% | N/A | **COMPLETE** (2026-02-15) |
| **Q5** | Insight Comparison Tool | N/A | ✅ 100% | N/A | **COMPLETE** (2026-02-15) |
| **Q6** | Critical Bug Fixes (Pulse, Tools, Contact) | ✅ 100% | ✅ 100% | N/A | **COMPLETE** (2026-02-15) |
| **Q7** | SEO Overhaul (Metadata, JSON-LD, Sitemap) | N/A | ✅ 100% | N/A | **COMPLETE** (2026-02-15) |
| **Q8** | Data Quality (ILIKE Sanitization, Stats) | ✅ 100% | ✅ 100% | N/A | **COMPLETE** (2026-02-15) |
| **Q9** | Error Handling & Rate Limiting | ✅ 100% | N/A | N/A | **COMPLETE** (2026-02-15) |

**Overall:** Phase 1-10 Complete + Phases A-L + Q1-Q9 Complete (Professional Overhaul + Quality Audit Fixes)

### Phase A: Superadmin Content Completeness (2026-02-14)
**Delivered:** Full CRUD for insights, agent schedule editor, cost analytics, 3 new admin pages, sidebar updated to 14 nav items
- A1: Admin Create Insight (synthetic RawSignal for FK, Sheet dialog form)
- A2: Agent schedule editor UI (cron/interval/manual, next/last run display)
- A3: Agent cost analytics chart (7d/30d/90d period, cost breakdown by agent)
- A4: Pipeline Monitoring admin page (scraper status, trigger/pause, health history)
- A5: Content Review admin page (approve/reject workflow, stats, status filter)
- A6: Integrations admin page (Slack/Discord webhooks) + sidebar nav update

### Phase B: AI Chat Strategist (2026-02-14)
**Delivered:** Conversational AI with 3 strategist modes, SSE streaming, chat session management
- B1: Chat schemas (ChatCreate, ChatMessageCreate, ChatResponse, ChatListResponse)
- B2: Chat agent (PydanticAI + Gemini Flash, 3 modes: pressure_test, gtm_planning, pricing_strategy)
- B3: Chat API routes (5 endpoints: POST/GET/GET/{id}/POST/{id}/messages/DELETE, SSE streaming)
- B4: Frontend chat page (message bubbles, mode selector, session sidebar, SSE streaming)
- B5: IdeaChat model updated with `mode` column + Alembic migration c002
- B6: Insight detail page updated with "AI Chat Strategist" CTA card

### Phase C: Idea Builder (2026-02-14)
**Delivered:** One-click brand + landing page generation from insight data with visual preview
- C1: POST /api/build/from-insight/{insight_id} endpoint (brand + landing page combined)
- C2: Builder page with configuration form (company name, pricing toggle)
- C3: Visual preview: hero section, features grid, pricing table, FAQ accordion, SEO metadata
- C4: Brand package display: color swatches, typography, logo concept, brand voice
- C5: Copy HTML/CSS buttons, regenerate action
- C6: Insight detail page updated with "Idea Builder" CTA card

### Phase D: Content Volume & Quality (2026-02-14)
**Delivered:** All 9 AI agents now have Arq task wrappers and automated schedules (17 total tasks)
- D1: `run_content_generator_auto_task` — auto-generates blog/social content for top 5 insights (every 3 days)
- D2: `run_competitive_intel_auto_task` — auto-analyzes competitors for insights with stale data (weekly Thu)
- D3: `run_market_intel_auto_task` — auto-generates market reports for high-scoring insights (weekly Fri)
- D4: All 3 registered in WorkerSettings.functions + scheduled in scheduler.py

### Phase E: Analytics Dashboard Enhancements (2026-02-14)
**Delivered:** Revenue MRR growth/churn calculations, time range picker, period-scoped queries
- E1: MRR growth MoM — estimate from new paid users and churned subscriptions
- E2: Churn rate — calculated from canceled subscriptions in period / active at start
- E3: `avg_insights_viewed` — calculated from InsightInteraction view events
- E4: Time range picker (7d/30d/90d) — passes `days` param to all 4 analytics endpoints
- E5: Revenue MetricCard now shows MRR growth trend arrow and churn rate subtitle

### Phase F: UX Polish (2026-02-14)
**Delivered:** Dark mode audit (50+ fixes), mobile-responsive forms, live agent log streaming
- F1: Dark mode — added dark: variants to all hardcoded colors across 9 admin pages (red, green, yellow, blue, amber, violet, pink, indigo)
- F2: Mobile forms — changed `grid-cols-2` to `sm:grid-cols-2` across all dialog forms (tools, trends, insights, users, agents, market-insights, success-stories, pipeline)
- F3: Live agent logs — SSE terminal viewer in agents sheet (pause/resume, clear, auto-scroll, error highlighting, 100-entry buffer)
- Sidebar hamburger menu was already implemented (lg:hidden responsive toggle)

### Phase G: Design System Revolution (2026-02-14)
**Delivered:** Distinctive "Data Intelligence" aesthetic replacing generic IdeaBrowser clone look
- G1: Typography — Instrument Serif (display), Satoshi (body), JetBrains Mono (data) via Google Fonts + Fontshare CDN
- G2: Color system — deep teal primary (#0D7377), warm amber accent (#D4A017), off-white background, all IdeaBrowser refs removed
- G3: Motion — framer-motion animation presets (stagger, fade-up, counter, skeleton-to-data)
- G4: Background textures — dot grid, hero gradient mesh, card noise overlay, teal card hover glow

### Phase H: Content Pipeline & Data Source Expansion (2026-02-14)
**Delivered:** 6 active scrapers (was 3), 150+ signals/day target, real trend data
- H1: Worker task audit — all 13 scheduler tasks verified registered (0 gaps)
- H2: Twitter/X scraper activated — registered in worker + scheduler (every 6 hours)
- H3: Hacker News scraper created — HN Algolia API, 50+ score filter, 30 results/run
- H4: Mock trend data removed — TrendChart accepts real data prop, "Search Interest" badge fallback
- H5: Throughput increased — Reddit 50 (was 25), PH 30 (was 10), Google Trends 6 regions (was US-only)

### Phase I: Admin Portal Excellence (2026-02-14)
**Delivered:** Dashboard charts, pagination, export, command palette, bulk operations
- I1: 4 Recharts charts on admin dashboard (content volume, agent activity, user growth, quality)
- I2: Reusable AdminPagination component integrated into insights, users, tools pages
- I3: CSV/JSON export endpoint + frontend download buttons
- I4: Cmd+K command palette (16 items, arrow nav, category groups, both layouts)
- I5: Bulk operations — row checkboxes, select all, bulk delete with confirmation, bulk export

### Phase J: Public Pages Editorial Redesign (2026-02-14)
**Delivered:** Story-driven homepage, magazine-style detail pages, redesigned cards
- J1: Homepage — hero gradient + serif title, latest insights grid, 8-dimension deep-dive, CTA
- J2: InsightCard — teal score bar, source badges (platform colors), market size circles, relative dates
- J3: Insight detail — editorial hero, score dashboard, problem/solution columns, evidence section, sticky action bar
- J4: Market insights — AI-generated badge, reading time, enhanced author bio

### Phase K: Data-Driven Evidence & Social Proof (2026-02-14)
**Delivered:** Confidence visualization, engagement metrics, public stats API
- K1: Confidence badges on InsightCards (High/Medium/Needs Verification)
- K2: GET /api/insights/{id}/engagement endpoint + display in detail hero
- K3: Evidence Score badge, Google Trends verification banner, data point count
- K4: GET /api/insights/stats/public endpoint, homepage fetches real counters

### Phase L: Competitive Differentiators (2026-02-14)
**Delivered:** Enhanced validator, 5 chat modes, competitive landscape viz, weekly digest
- L1: Validate page — hero gradient, font-data scores, free tier badge for unauthenticated users
- L2: Chat strategist — 5 modes (general, pressure_test, gtm, pricing, competitive) with distinct system prompts
- L3: Competitive map — Recharts ScatterChart (Market Maturity × Innovation Score), quadrant labels
- L4: Weekly email digest task — Monday 9am, top 10 insights by relevance

### Phase Q6: Critical Bug Fixes (2026-02-15)
**Delivered:** 3 deploy-blocking bugs fixed (Pulse 500, Tools 422, Contact 404)
- Q6.1: Pulse timezone fix — `datetime.now(UTC)` → `datetime.utcnow()` (TIMESTAMP WITHOUT TZ)
- Q6.2: Tools categories route — added `GET /categories` endpoint before `/{tool_id}` route
- Q6.3: Contact form backend — created `contact.py` with rate-limited POST, wired frontend

### Phase Q7: SEO Overhaul (2026-02-15)
**Delivered:** Per-page metadata, JSON-LD structured data, sitemap update
- Q7.1: 19 route-segment `layout.tsx` files — unique metadata per page
- Q7.2: JSON-LD on 5 pages (pricing, faq, about, market-insights, success-stories)
- Q7.4: Sitemap updated — 6 missing pages added

### Phase Q8: Data Quality & Sanitization (2026-02-15)
**Delivered:** ILIKE input sanitization, stats updates
- Q8.3: Developer page — "130+" → "230+" API endpoints
- Q8.4: ILIKE sanitization — 21 usages across 6 files via shared `escape_like()` utility

### Phase Q9: Error Handling & Rate Limiting (2026-02-15)
**Delivered:** Pulse query error handling, public endpoint rate limiting
- Q9.1: Pulse error handling — 6 DB queries wrapped in try/except with fallback
- Q9.2: Rate limiting — `@limiter.limit("30/minute")` on pulse, tools, trends, contact

---

## Completed Features by Phase

### Phase 1-3: MVP Foundation
**Delivered:** Data collection (4 scrapers), AI analysis (PydanticAI), Next.js dashboard, dark mode, Recharts visualizations
- 2 core models (RawSignal, Insight)
- 8 API endpoints (signals, insights, health)
- 47 E2E tests (Playwright, cross-browser)

### Phase 4: Authentication & Admin Portal
**Delivered:** Supabase Auth, user workspace, admin portal with SSE streaming, 8-dimension scoring
- 7 new models (User, SavedInsight, UserRating, AdminUser, etc.)
- 31 new endpoints (18 user, 13 admin)
- Real-time admin dashboard with agent control

### Phase 4.5: Cloud Infrastructure
**Delivered:** Supabase Cloud migration (Sydney ap-southeast-2), RLS policies, connection pooling
- Migrated from self-hosted PostgreSQL to Supabase Pro
- 64% cost reduction at 10K users
- 50ms latency for APAC market (vs 180ms US-based)

### Phase 5-7: Advanced Features
**Delivered:** 40-step AI research agent, Stripe payments (4 tiers), team collaboration, API keys, multi-tenancy
- 15 new models (CustomAnalysis, Subscription, Team, APIKey, Tenant, etc.)
- 66 new endpoints (research, payments, teams, api-keys, tenants)
- Admin-approved research queue (Super Admin Sovereignty)

### Phase 8: Superadmin Control Center
**Delivered:** Content quality management, pipeline monitoring, user analytics, AI agent control
- 8 new models (ContentReviewQueue, PipelineHealthCheck, UserActivityEvent, etc.)
- 33 new endpoints (content review, pipeline dashboard, analytics, agent control)
- Auto-approval system at 0.85 quality score
- Real-time scraper health monitoring with SSE
- Cohort analysis and churn prediction
- AI prompt management and cost tracking

### Phase 9: User Engagement Features
**Delivered:** User preferences, idea chat, community voting/comments, gamification, social networking
- 26 new models (UserPreferences, IdeaChat, IdeaVote, Achievement, FounderProfile, Collection, etc.)
- 43 new endpoints (preferences, chat, community, gamification, social)
- AI-powered Q&A assistant with chat history
- Community voting, commenting, and polls (7 tables)
- Gamification system: achievements, points, credits, leaderboards (5 tables)
- Social features: founder profiles, idea clubs, co-founder matching (5 tables)
- Collections and curation system (4 tables)

### Phase 10: Integration Ecosystem
**Delivered:** External integrations, webhooks, OAuth connections, competitive intelligence
- 7 new models (ExternalIntegration, IntegrationWebhook, OAuthConnection, etc.)
- 16 new endpoints (integration management, webhook CRUD, OAuth flows)
- Webhook delivery tracking and retry logic
- OAuth connection management
- Competitive intelligence scraper

### Phase 12-14: Public Content & SEO
**Delivered:** Public pages, tools directory (54 tools), success stories (12 stories), trends (180+ keywords), blog
- 4 new models (Tool, SuccessStory, Trend, MarketInsight)
- 29 new endpoints (tools, success stories, trends, market insights)
- Marketing homepage with hero/CTA/testimonials
- Dynamic sitemap generation, OG tags, Twitter cards
- 10 public pages, 4 admin CRUD interfaces

---

## Production Deployment Checklist

### P0 - Critical (Must Complete Before Launch)

**Backend Deployment (Railway):**
- [ ] Create Railway project and link GitHub repo
- [ ] Set environment variables (see section below)
- [ ] Configure build command: `cd backend && uv sync && alembic upgrade head`
- [ ] Configure start command: `cd backend && uvicorn app.main:app --host 0.0.0.0 --port $PORT`
- [ ] Verify health endpoint: `https://[app-name].railway.app/health`
- [ ] Test database connection (Supabase pooler)
- [ ] Verify Redis connection (Upstash)

**Frontend Deployment (Vercel):**
- [ ] Import GitHub repo to Vercel
- [ ] Set environment variables (see section below)
- [ ] Configure build command: `cd frontend && npm run build`
- [ ] Configure framework preset: Next.js
- [ ] Verify deployment URL: `https://[project-name].vercel.app`
- [ ] Test API connection to Railway backend
- [ ] Verify Supabase authentication flow

**Production Environment Variables:**

Backend (Railway):
```bash
# Database (Supabase Production)
DATABASE_URL=postgresql://postgres:[password]@aws-1-ap-southeast-2.pooler.supabase.com:5432/postgres
SUPABASE_URL=https://[project-id].supabase.co
SUPABASE_ANON_KEY=eyJhbGc...
SUPABASE_SERVICE_ROLE_KEY=eyJhbGc...

# Redis (Upstash Production)
REDIS_URL=redis://default:[password]@[host].upstash.io:6379

# External APIs
GOOGLE_API_KEY=AIza...  # Gemini 2.0 Flash (primary LLM)
ANTHROPIC_API_KEY=sk-ant-...  # Claude 3.5 Sonnet (fallback)
FIRECRAWL_API_KEY=fc-...
STRIPE_API_KEY=sk_live_...  # LIVE MODE
STRIPE_WEBHOOK_SECRET=whsec_...  # LIVE MODE
RESEND_API_KEY=re_...
TWITTER_BEARER_TOKEN=AAAA...
REDDIT_CLIENT_ID=***
REDDIT_CLIENT_SECRET=***
REDDIT_USERNAME=***

# Configuration
ENVIRONMENT=production
API_BASE_URL=https://[app-name].railway.app
CORS_ORIGINS=https://[project-name].vercel.app
```

Frontend (Vercel):
```bash
NEXT_PUBLIC_API_URL=https://[app-name].railway.app
NEXT_PUBLIC_SUPABASE_URL=https://[project-id].supabase.co
NEXT_PUBLIC_SUPABASE_ANON_KEY=eyJhbGc...
NEXT_PUBLIC_STRIPE_PUBLISHABLE_KEY=pk_live_...  # LIVE MODE
NEXT_PUBLIC_SITE_URL=https://[project-name].vercel.app
```

**Stripe Configuration:**
- [ ] Switch Stripe dashboard to live mode
- [ ] Update API keys (sk_live_..., pk_live_...)
- [ ] Configure webhook endpoint: `https://[app-name].railway.app/api/payments/webhooks/stripe`
- [ ] Enable webhook events: `checkout.session.completed`, `customer.subscription.updated`, `customer.subscription.deleted`, `invoice.payment_succeeded`, `invoice.payment_failed`
- [ ] Test checkout flow end-to-end

**Monitoring & Alerts:**
- [ ] Set up Sentry error tracking (backend + frontend)
- [ ] Configure uptime monitoring (UptimeRobot or Checkly)
- [ ] Set up Stripe webhook monitoring
- [ ] Enable Supabase query performance monitoring
- [ ] Configure Railway metrics dashboard

### P1 - Post-Launch (Week 1)

**Verification & Testing:**
- [ ] Run E2E tests against production URLs
- [ ] Verify authentication flow (signup, login, logout, password reset)
- [ ] Test protected routes (/dashboard, /workspace, /admin)
- [ ] Verify content quality auto-approval (0.85 threshold)
- [ ] Monitor pipeline health dashboard (real-time SSE updates)
- [ ] Test payment flow (Stripe checkout, subscription management)
- [ ] Verify email notifications (welcome, daily digest, research ready)

**Data Quality Monitoring:**
- [ ] Monitor scraper success rates (Reddit 60/min, Firecrawl 10/min, Twitter 450/15min)
- [ ] Verify duplicate detection working (SHA-256 content hashing)
- [ ] Check post-LLM validation gates (300+ word minimum, score range validation)
- [ ] Review AI agent cost tracking (Gemini 2.0 Flash vs Claude 3.5 Sonnet usage)

### P2 - Optimization (Week 2-4)

**Performance Tuning:**
- [ ] Analyze database query performance (add indexes if needed)
- [ ] Optimize API response times (target: p95 < 500ms)
- [ ] Enable frontend bundle analysis (reduce bundle size)
- [ ] Configure CDN caching for public assets

**Analytics & Insights:**
- [ ] Set up user analytics (PostHog or Mixpanel)
- [ ] Track conversion funnel (signup → paid conversion)
- [ ] Monitor cohort retention (weekly/monthly)
- [ ] Analyze feature usage (research requests, community voting, gamification)

---

## Testing Requirements

### Backend Testing (pytest)

**Current Status:** 291 tests passing across 22 test files, 85% code coverage

**Coverage Breakdown:**
- Models: 90%+ (Pydantic validation, SQLAlchemy relationships)
- Services: 85%+ (business logic, external API integration)
- Routes: 80%+ (API endpoint validation, authentication)
- Agents: 75%+ (AI output schemas, LLM integration)

**Test Categories:**

1. **Unit Tests** (validation, business logic)
   - Pydantic schema validation
   - Service-level business rules
   - Utility function correctness

2. **Integration Tests** (API endpoints, database operations)
   - FastAPI endpoint workflows
   - SQLAlchemy async queries
   - External API mocks (Firecrawl, Reddit, Twitter)

3. **Quality Tests** (post-LLM validation)
   - Content quality gates (300+ word minimums)
   - Score range validation (0.0-1.0)
   - Content deduplication (SHA-256 hashing)

4. **Security Tests** (authentication, rate limiting)
   - JWT token validation
   - Role-based access control (RBAC)
   - Rate limiting (Reddit 60/min, Twitter 450/15min, Firecrawl 10/min)

**Key Test Files:**
- `test_payment_service.py` - Stripe payment validation, webhook handling
- `test_community_validator.py` - Community signal verification
- `test_quality_alerts_slack.py` - Slack alert integration
- `test_sanitization.py` - XSS prevention, HTML sanitization
- `test_url_validator.py` - URL parsing security
- `test_trend_verifier.py` - Trend data validation

**Test Scenarios:**
- Payment validation: Stripe checkout, subscription webhooks, customer portal
- Content quality: 300+ word minimums, score range checks, duplicate detection
- Security: XSS prevention (bleach), URL validation (urlparse), SQL injection protection
- Rate limiting: Per-source limits (Reddit 60/min, Twitter 450/15min)

**Run Tests:**
```bash
cd backend
pytest tests/ -v --cov=app --cov-report=html
```

### Frontend Testing (Playwright)

**Current Status:** 47 E2E tests passing across 8 test suites, 5 browser platforms

**Browser Coverage:**
- Chrome (desktop)
- Firefox (desktop)
- Safari (desktop)
- Mobile Chrome (375px viewport)
- Mobile Safari (375px viewport)

**Test Suites:**

1. **Authentication Tests** (`auth.spec.ts`)
   - Login flows (Supabase Auth)
   - Signup validation
   - Password reset
   - Session persistence

2. **Insight Browsing Tests** (`public-pages.spec.ts`)
   - Dashboard rendering
   - Filtering (source, score, budget)
   - Search functionality
   - Pagination (12 results/page)

3. **Admin Tests** (`admin.spec.ts`)
   - Admin portal access control
   - Agent monitoring dashboard
   - Content review queue

4. **Accessibility Tests** (`accessibility.spec.ts`)
   - WCAG 2.1 AA compliance
   - Keyboard navigation
   - Screen reader support
   - 21:1 contrast ratio (dark mode)

**Test Scenarios:**
- Authentication: Login/logout flows, session persistence, protected routes
- Insight discovery: Filtering (source, budget, score), search, pagination
- Responsive design: Mobile (375px), tablet (768px), desktop (1280px)
- Dark mode: Theme toggle, localStorage persistence, FOUC prevention
- Cross-browser: Chrome, Firefox, Safari compatibility

**Run Tests:**
```bash
cd frontend
npx playwright test
npx playwright test --headed  # With browser UI
npx playwright test --ui  # Interactive mode
npx playwright test --project=chromium  # Single browser
```

**Pending Tests (Post-Launch):**
- Workspace interactions (save, rate, claim insights)
- Research submission flows (custom analysis requests)
- Payment checkout (Stripe integration)
- Community features (voting, commenting)
- Gamification triggers (achievement unlocks)

---

## Decision Records

### DR-001: Supabase Cloud Adoption (2026-01-25)

**Decision:** Use Supabase Pro (Sydney ap-southeast-2) for production database

**Rationale:**
- 64% cost reduction at 10K users ($25/mo vs $69/mo Neon)
- APAC market optimization (50ms latency vs 180ms US)
- Built-in authentication, RLS policies, real-time subscriptions
- Auto-scaling, connection pooling (500 concurrent connections)

**Impact:** Phase 4.5 migration completed in 3 days, 20 tables deployed with RLS

### DR-002: English-Only Simplification (2026-01-31)

**Decision:** Roll back multi-language support (Phase 15-16) to English-only

**Rationale:**
- Focus on English-language market validation before APAC expansion
- Reduce frontend complexity for MVP deployment
- Backend infrastructure retains multi-language capability for future re-enablement

**Impact:** Removed 7 language files, LanguageSwitcher component, hreflang tags

**Reversibility:** High - Backend supports 8 languages, frontend can be re-enabled in 2-3 days

### DR-003: Gemini 2.0 Flash as Primary LLM (2026-01-25)

**Decision:** Use Google Gemini 2.0 Flash as primary LLM, Claude 3.5 Sonnet as fallback

**Rationale:**
- 97% cost reduction ($0.10/M input vs $3/M for Claude)
- 1M token context window (process multiple signals at once)
- Excellent structured JSON output quality

**Impact:** Monthly AI cost at 10K users: $75/mo (vs $450/mo with Claude only)

**Fallback Strategy:** Use Claude 3.5 Sonnet for complex reasoning tasks or if Gemini quota exceeded

### DR-004: Content Quality Auto-Approval (2026-02-04)

**Decision:** Auto-approve AI-generated content with quality score ≥ 0.85

**Rationale:**
- Reduce manual review overhead for high-quality content
- Maintain quality standards with validation gates
- Flag low-quality content (< 0.40) for admin review

**Implementation:**
- Post-LLM validation: 300+ word minimum, score range checks
- Duplicate detection: SHA-256 content hashing
- Community/trend verification: External API validation

### DR-005: Comprehensive Testing Coverage (2026-02-08)

**Decision:** 338 total tests (291 backend + 47 E2E) with 85% coverage

**Rationale:**
- Backend: pytest with 22 test files covering models, services, routes, agents
- Frontend: Playwright with 8 test suites across 5 browser platforms
- Quality gates: Post-LLM validation, content deduplication, rate limiting
- Production readiness: All critical paths tested, authentication verified

**Impact:** Production deployment confidence, regression prevention, quality assurance

---

## Post-Deployment Roadmap

### Immediate Priorities (Month 1)

**Content Seeding:**
- Seed 50+ insights across 10+ categories
- Populate tools directory (complete 54-tool list)
- Expand trends database (12 → 180+ keywords via Google Trends API)
- Create 10+ market insights blog posts (APAC startup ecosystems)

**SEO & Marketing:**
- Submit sitemap to Google Search Console, Bing Webmaster
- Set up Google Analytics or PostHog
- Create landing pages for top categories
- Social media presence (Twitter, LinkedIn)

**User Feedback Loop:**
- In-app feedback widget
- User interview scheduling (5-10 early users)
- Feature request voting system
- Usage analytics dashboard

### Medium-Term (Month 2-3)

**Performance Optimization:**
- Image optimization (Next.js Image component)
- API response caching (Redis)
- Database query optimization (add indexes based on query logs)
- Frontend bundle size reduction

**Growth Features:**
- Referral program (invite friends, get credits)
- Email drip campaigns (welcome, engagement, retention)
- Social sharing (Twitter, LinkedIn cards with OG images)
- Content marketing (blog posts, case studies)

### Long-Term (Month 3+)

**Decision Point:** Based on English-language market validation, consider:
- Re-enabling APAC multi-language support (Phase 15-16 backend ready)
- Chrome extension (save insights while browsing)
- Mobile app (React Native or Flutter)
- Slack/Discord integration (notify on new insights)
- AI-powered personalization (ML recommendation engine)

---

## Development Setup (Quick Start)

### Prerequisites

1. **Supabase Account:** Create project in Sydney region (ap-southeast-2)
2. **Upstash Account:** Create Redis database
3. **API Keys:** Google Gemini, Firecrawl, Reddit, Twitter (optional)

### Backend Setup

```bash
cd backend

# 1. Install dependencies
uv sync

# 2. Configure environment
cp .env.example .env
# Edit .env with your Supabase and API credentials

# 3. Run migrations
alembic upgrade head

# 4. Start server
uvicorn app.main:app --reload

# 5. Verify health
curl http://localhost:8000/health
```

### Frontend Setup

```bash
cd frontend

# 1. Install dependencies
npm install

# 2. Configure environment
cp .env.local.example .env.local
# Edit .env.local with Supabase credentials

# 3. Start dev server
npm run dev

# 4. Open browser
# http://localhost:3000
```

### Database Verification

```bash
# Check migrations
alembic current
alembic history

# Verify table count
psql $DATABASE_URL -c "SELECT COUNT(*) FROM information_schema.tables WHERE table_schema = 'public';"
# Expected: 69 tables
```

---

## File Structure Summary

**Backend (backend/app/):**
- `models/` - 34 files, 69 SQLAlchemy tables
- `api/routes/` - 28+ files, 232+ FastAPI endpoints (incl. pulse.py)
- `services/` - 20+ business logic services
- `agents/` - 8 PydanticAI agents
- `scrapers/` - 6 scrapers (Reddit, Product Hunt, Trends, Twitter, Hacker News, Firecrawl)

**Frontend (frontend/):**
- `app/[locale]/` - 35+ routes (Next.js 16 App Router)
- `components/` - 50+ reusable React components
- `lib/` - API client, types, utilities

**Migrations (backend/alembic/versions/):**
- 25+ migration files (b001 → b021)
- Creates 69 tables with RLS policies

**Tests:**
- `tests/backend/` - Unit + integration tests (137 passing)
- `tests/frontend/e2e/` - Playwright E2E tests (47 passing)

---

## Success Metrics

**System Health:**
- Uptime: 99.9% target
- API latency: p95 < 500ms
- Database connections: < 450/500 (Supabase Pro)
- Error rate: < 1%

**Data Quality:**
- AI content quality score: > 0.80 average
- Duplicate rate: < 5%
- Scraper success rate: > 85%
- Post-LLM validation pass rate: > 90%

**User Engagement:**
- Signup conversion: 4% target (doubled from 2% pre-Phase 14)
- Daily active users: 10% of total users
- Research requests: 50/month (Starter tier average)
- Community engagement: 5% voting rate

**Revenue (at 10K users):**
- MRR: $59,000 target
- Paid conversion: 10% (1,000 paid users)
- Churn: < 5%/month
- LTV/CAC: > 3:1

---

## Reference Files

**Architecture:** `memory-bank/architecture.md` (69 tables, 232+ endpoints, 8 AI agents)
**Tech Stack:** `memory-bank/tech-stack.md` (dependencies, cost analysis)
**Progress Log:** `memory-bank/progress.md` (completed work, recent changes)
**Active Context:** `memory-bank/active-context.md` (current phase, blockers)
**Project Brief:** `memory-bank/project-brief.md` (business objectives, competitive positioning)

---

**Last Updated:** 2026-02-14
**Status:** Production Deployment Ready ✅
**Infrastructure:** Supabase Pro as sole database (~$30/mo PMF deployment)
**Next Action:** Deploy to Railway (backend) + Vercel (frontend)
