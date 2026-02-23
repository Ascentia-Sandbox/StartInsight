---
**Memory Bank Protocol**
**Reading Priority:** CRITICAL
**Read When:** Before implementing features, designing database models, creating APIs
**Dependencies:** Read active-context.md for current phase, implementation-plan.md for tasks
**Purpose:** System architecture, 69 database tables, 232+ API endpoints, auth, RLS, deployment
**Last Updated:** 2026-02-19
---

# System Architecture: StartInsight

## 1. System Overview

**Architecture**: Modular monolith with decoupled frontend/backend
**Core Loops**: Collect → Analyze → Present (3 independent data flows)
**Deployment**: Railway (backend), Vercel (frontend), Supabase Pro (database - sole source for dev + prod, ~$30/mo PMF)

### Stack

| Component | Technology | Port/URL | Purpose |
|-----------|-----------|----------|---------|
| **Frontend** | Next.js 16.1.3 (App Router) | 3000 | User dashboard, admin portal, public pages (34 routes) |
| **Backend** | FastAPI + Uvicorn ASGI | 8000 | REST API (232+ endpoints), SSE streaming |
| **Database** | PostgreSQL 16 (Supabase Pro) | 5432 | 69 tables with RLS enabled, single source for dev + prod |
| **Cache/Queue** | Redis 7 | 6379 | Arq task queue, rate limiting |
| **Worker** | Arq + APScheduler | N/A | Background scraping (6-hour intervals) |
| **AI** | Gemini 2.0 Flash (Google) | API | PydanticAI agents (8 agents: analysis, enhanced analysis, research, competitive intel, market intel, content generation, chat strategist, market insight publisher) |
| **Scraper** | Crawl4AI, PRAW, pytrends | API | Reddit, Product Hunt, Trends (self-hosted, $0 cost) |
| **Auth** | Supabase Auth | API | JWT-based, RLS integration |
| **Payments** | Stripe | API | Checkout, subscriptions, webhooks |
| **Email** | Resend | API | Transactional emails (6 templates) |

**Connection String**: `postgresql+asyncpg://postgres.[REF]:[PASSWORD]@aws-1-ap-southeast-2.pooler.supabase.com:5432/postgres`
**Pool Config**: 20 size, 30 max overflow, SSL required (Supabase Pro: 200 connections, 8GB storage)

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

    Worker -->|Analyze| Claude[Gemini 2.0 Flash]
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

## 4. Database Schema (69 Tables)

### 4.1 Core Tables (Phase 1-3)

**`raw_signals`** (Data collection)
- id (UUID PK), source (varchar), url (text), content (text), metadata (JSONB), processed (bool), created_at

**`insights`** (AI analysis output)
- id (UUID PK), raw_signal_id (UUID FK), problem_statement (text), proposed_solution (text), market_size_estimate (enum: Small/Medium/Large), relevance_score (float 0-1), competitor_analysis (JSONB array), created_at
- Enhanced scoring (Phase 4.3): opportunity_score, problem_score, feasibility_score, why_now_score, go_to_market_score, founder_fit_score, execution_difficulty_score (all 1-10)
- Framework fields: value_ladder (JSONB), market_gap_analysis (text), why_now_analysis (text), revenue_potential (text)
- **slug** (varchar 255, unique, nullable) — SEO-friendly URL slug added via migrations c006-c008; auto-generated from problem_statement; used by frontend route `/insights/[slug]/` (replaced `/insights/[id]/`)

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

**`research_requests` (New - Phase 5.2: Admin Queue)**
- id (UUID PK), user_id (UUID FK users), admin_id (UUID FK users nullable)
- status (enum: pending/approved/rejected/completed)
- idea_description (text), target_market (varchar 255), budget_range (varchar 100)
- admin_notes (text), analysis_id (UUID FK custom_analyses nullable)
- created_at (timestamptz indexed DESC), reviewed_at (timestamptz), completed_at (timestamptz)
- **Indexes**: idx_research_requests_user_id, idx_research_requests_status, idx_research_requests_created_at
- **RLS**: Users see own requests only, admins see all requests
- **Purpose**: Admin approval queue for user-submitted research requests (Super Admin Sovereignty)

**`custom_analyses` (Modified - Phase 5.2)**
- id (UUID PK), user_id (UUID FK nullable), admin_id (UUID FK users nullable), request_id (UUID FK research_requests nullable)
- idea_description (text), target_market (text), budget_range (varchar 20)
- status (enum: pending/processing/completed/failed), progress_percent (int), current_step (varchar 100)
- market_analysis (JSONB), competitor_landscape (JSONB), value_equation (JSONB), market_matrix (JSONB)
- acp_framework (JSONB), validation_signals (JSONB), execution_roadmap (JSONB), risk_assessment (JSONB)
- opportunity_score (numeric 4,2), market_fit_score (numeric 4,2), execution_readiness (numeric 4,2)
- tokens_used (int), analysis_cost_usd (numeric 6,4), error_message (text)
- created_at (timestamptz indexed), started_at (timestamptz), completed_at (timestamptz)
- **Changes**: user_id now nullable (admin can trigger without user), added admin_id, request_id

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

### 4.8 Public Content Tables (Phase 12-14)

**`tools`** (54-tool directory)
- id (UUID PK), name (varchar 255), tagline (varchar 500), description (text), category (varchar 100)
- pricing (varchar 100), website_url (varchar 500), logo_url (varchar 500)
- features (JSONB array), is_featured (bool default false), sort_order (int default 0)
- created_at, updated_at
- **Indexes**: idx_tools_category, idx_tools_featured_sort (composite: is_featured DESC, sort_order ASC)
- **RLS**: Public SELECT (no auth required), Admin INSERT/UPDATE/DELETE
- **Purpose**: Public-facing tool directory (/tools page)
- **Sample Data**: 54 tools seeded across 6 categories (Design, Development, Marketing, Analytics, Productivity, AI)

**`success_stories`** (Founder case studies)
- id (UUID PK), founder_name (varchar 255), company_name (varchar 255), tagline (varchar 500)
- idea_summary (text), journey_narrative (text 3000+ words)
- metrics (JSONB: revenue, users, growth_rate, funding), timeline (JSONB array: year, milestone)
- avatar_url (varchar 500), company_logo_url (varchar 500)
- is_featured (bool default false), sort_order (int default 0)
- created_at, updated_at
- **Indexes**: idx_success_stories_featured_sort (composite: is_featured DESC, sort_order ASC)
- **RLS**: Public SELECT, Admin INSERT/UPDATE/DELETE
- **Purpose**: Founder validation stories (/success-stories page)
- **Sample Data**: 12 success stories seeded (SaaS, E-commerce, Marketplace verticals)

**`trends`** (180+ trending keywords)
- id (UUID PK), keyword (varchar 255 unique), search_volume (varchar 20), growth_percentage (varchar 20)
- category (varchar 100), business_implications (text), trend_data (JSONB: chart_points, related_keywords)
- source (varchar 100 default 'google_trends'), is_featured (bool default false)
- created_at, updated_at
- **Indexes**: idx_trends_keyword (unique), idx_trends_volume DESC, idx_trends_growth DESC, idx_trends_category
- **RLS**: Public SELECT, Admin INSERT/UPDATE/DELETE
- **Purpose**: Trending keyword discovery (/trends page)
- **Sample Data**: 12 trends seeded (expandable to 180+ via Google Trends API)

**`market_insights`** (Blog articles)
- id (UUID PK), title (varchar 500), slug (varchar 255 unique), summary (varchar 1000)
- content (text Markdown), category (varchar 100), author_name (varchar 255)
- author_avatar_url (varchar 500), cover_image_url (varchar 500)
- reading_time_minutes (int), published_at (timestamptz nullable)
- created_at, updated_at
- **Indexes**: idx_market_insights_slug (unique), idx_market_insights_published DESC, idx_market_insights_category
- **RLS**: Public SELECT WHERE published_at IS NOT NULL, Admin SELECT/INSERT/UPDATE/DELETE (all records)
- **Purpose**: Marketing blog (/market-insights page)
- **Sample Data**: 6 blog articles seeded (industry trends, startup guides, case studies)

### 4.9 Indexes

**Critical indexes** (all tables):
- `raw_signals`: idx_source, idx_processed, idx_created_at
- `insights`: idx_relevance_score, idx_created_at, idx_raw_signal_id, idx_opportunity_score, **idx_slug** (unique, c006-c008)
- `saved_insights`: idx_user_id, idx_status
- `user_ratings`: idx_user_id, idx_insight_id
- `api_keys`: idx_user_id, idx_key_prefix, idx_is_active
- `subscriptions`: idx_user_id, idx_stripe_subscription_id
- `teams`: idx_owner_id, idx_slug

### 4.10 Phase 8-10 Tables (43 new tables)

#### Phase 8.1: Content Quality Management (2 tables)

**`content_review_queue`** (AI content review workflow)
- id (UUID PK), content_type (varchar 50 NOT NULL), content_id (UUID NOT NULL)
- status (varchar 20 default 'pending': pending/approved/rejected/flagged)
- quality_score (numeric 3,2: 0.00-1.00), auto_approved (bool default false)
- reviewer_id (UUID FK users nullable), review_notes (text), rejection_reason (varchar 255)
- created_at (timestamptz), reviewed_at (timestamptz nullable)
- **Constraints**: UNIQUE(content_type, content_id)
- **Indexes**: idx_review_queue_status, idx_review_queue_type_status (composite)
- **RLS**: Admin access only
- **Auto-Approval Rules**: score >= 0.85 auto-approve, score <= 0.40 auto-flag

**`content_similarity`** (Duplicate detection)
- id (UUID PK), source_insight_id (UUID FK insights), similar_insight_id (UUID FK insights)
- similarity_score (numeric 4,3: 0.000-1.000), similarity_type (varchar 20: exact/near/thematic)
- created_at (timestamptz), resolved (bool default false), resolution (varchar 20: keep_both/merge/delete_newer)
- **Constraints**: UNIQUE(source_insight_id, similar_insight_id)
- **Thresholds**: exact >= 0.95, near >= 0.85, thematic >= 0.70

#### Phase 8.2: Data Pipeline Command Center (4 tables)

**`pipeline_health_checks`** (Scraper health tracking)
- id (UUID PK), scraper_name (varchar 50 NOT NULL indexed)
- status (varchar 20 NOT NULL: healthy/degraded/down)
- response_time_ms (int), items_fetched (int), error_message (text)
- checked_at (timestamptz default NOW)
- **Indexes**: idx_health_checks_scraper_time (composite: scraper_name, checked_at DESC)

**`api_quota_usage`** (API quota monitoring)
- id (UUID PK), api_name (varchar 50 NOT NULL indexed)
- metric_name (varchar 50 NOT NULL: requests/tokens/cost_usd)
- value (numeric 12,4 NOT NULL), period_start (timestamptz), period_end (timestamptz)
- recorded_at (timestamptz default NOW)

**`admin_alerts`** (Alert configurations)
- id (UUID PK), alert_name (varchar 100), alert_type (varchar 50: threshold/anomaly/failure)
- metric_name (varchar 100), condition (JSONB NOT NULL: {"operator": "lt", "value": 0.8})
- severity (varchar 20 default 'warning': info/warning/critical)
- notification_channels (JSONB: ["email", "slack", "pagerduty"])
- is_active (bool default true indexed), created_by (UUID FK users), created_at (timestamptz)
- **Default Alerts**: Scraper failure >20%, API quota >80%, Queue >100 pending, Zero insights in 12h, Cost >$50/day

**`admin_alert_incidents`** (Alert incident tracking)
- id (UUID PK), alert_id (UUID FK admin_alerts CASCADE)
- triggered_value (numeric 12,4), status (varchar 20 default 'open': open/acknowledged/resolved)
- acknowledged_by (UUID FK users nullable), resolved_at (timestamptz nullable)
- created_at (timestamptz default NOW)

#### Phase 8.3: User & Revenue Intelligence (2 tables)

**`user_activity_events`** (User behavior tracking)
- id (UUID PK), user_id (UUID FK users CASCADE indexed)
- event_type (varchar 50 NOT NULL indexed: page_view/feature_use/insight_save/insight_view/research_start/export/upgrade)
- event_data (JSONB), session_id (varchar 100 indexed)
- created_at (timestamptz default NOW)
- **Indexes**: idx_activity_events_user_time (user_id, created_at DESC), idx_activity_events_type_time (event_type, created_at DESC)

**`user_sessions`** (Session analytics)
- id (UUID PK), user_id (UUID FK users CASCADE indexed)
- session_id (varchar 100 UNIQUE), started_at (timestamptz default NOW)
- ended_at (timestamptz nullable), duration_seconds (int nullable)
- page_views (int default 0), events_count (int default 0)
- device_type (varchar 20), referrer (varchar 500)

#### Phase 8.4-8.5: AI Agent Control & Security (2 tables)

**`agent_configurations`** (AI agent settings)
- id (UUID PK), agent_name (varchar 50 UNIQUE)
- is_enabled (bool default true), model_name (varchar 100 default 'gemini-1.5-flash')
- temperature (numeric 3,2 default 0.7), max_tokens (int default 4096)
- rate_limit_per_hour (int default 100), cost_limit_daily_usd (numeric 10,2 default 50.00)
- custom_prompts (JSONB nullable)
- updated_by (UUID FK users nullable), updated_at (timestamptz default NOW)

**`audit_logs`** (Security audit trail)
- id (UUID PK), user_id (UUID FK users nullable)
- action (varchar 100 NOT NULL indexed: user.login/user.logout/resource.create/resource.update/resource.delete/data.export/admin.impersonate/config.change)
- resource_type (varchar 50), resource_id (UUID nullable)
- details (JSONB nullable), ip_address (varchar 45), user_agent (varchar 500)
- created_at (timestamptz default NOW)
- **Indexes**: idx_audit_logs_actor_time (user_id, created_at DESC), idx_audit_logs_action_time (action, created_at DESC), idx_audit_logs_resource (resource_type, resource_id)

#### Phase 9.1: User Preferences & Email (3 tables)

**`user_preferences`** (Idea matching & personalization)
- id (UUID PK), user_id (UUID FK users CASCADE UNIQUE)
- background (varchar 50: tech/business/creative/other)
- budget_range (varchar 20: 0-1k/1k-10k/10k+)
- time_commitment (varchar 20: nights_weekends/part_time/full_time)
- market_preference (varchar 10: b2b/b2c/both)
- risk_tolerance (varchar 10: low/medium/high)
- skills (JSONB array), interests (JSONB array)
- completed_quiz (bool default false), created_at, updated_at

**`email_preferences`** (Digest & alert settings)
- id (UUID PK), user_id (UUID FK users CASCADE UNIQUE)
- daily_digest (bool default true), weekly_digest (bool default true), instant_alerts (bool default false)
- tracked_keywords (JSONB array), min_score_alert (numeric 3,2 default 0.85)
- digest_time_utc (varchar 5 default '09:00'), timezone (varchar 50 default 'UTC')
- unsubscribed_at (timestamptz nullable), created_at, updated_at

**`email_sends`** (Email delivery tracking)
- id (UUID PK), user_id (UUID FK users CASCADE)
- email_type (varchar 50: daily_digest/weekly_digest/instant_alert)
- subject (varchar 255), content_hash (varchar 64: prevent duplicate sends)
- sent_at (timestamptz default NOW), opened_at (timestamptz), clicked_at (timestamptz)

#### Phase 9.2: AI Idea Chat (2 tables)

**`idea_chats`** (Chat sessions)
- id (UUID PK), user_id (UUID FK users CASCADE), insight_id (UUID FK insights CASCADE)
- title (varchar 255 nullable), message_count (int default 0), total_tokens (int default 0)
- created_at, updated_at
- **Quota Limits**: Free 5 msg/day, Starter 50 msg/day, Pro unlimited

**`idea_chat_messages`** (Individual messages)
- id (UUID PK), chat_id (UUID FK idea_chats CASCADE)
- role (varchar 20: user/assistant), content (text NOT NULL), tokens_used (int nullable)
- created_at (timestamptz default NOW)

#### Phase 9.3: Community Validation (7 tables)

**`idea_votes`** (Idea upvote/downvote)
- id (UUID PK), user_id (UUID FK users CASCADE), insight_id (UUID FK insights CASCADE)
- vote_type (varchar 10: up/down), created_at (timestamptz default NOW)
- **Constraints**: UNIQUE(user_id, insight_id)

**`idea_comments`** (Threaded discussion on ideas)
- id (UUID PK), user_id (UUID FK users CASCADE), insight_id (UUID FK insights CASCADE)
- parent_id (UUID FK idea_comments CASCADE nullable - threading)
- content (text NOT NULL), upvotes (int default 0)
- is_expert (bool default false), is_pinned (bool default false), is_deleted (bool default false)
- created_at, updated_at

**`comment_upvotes`** (Comment upvotes)
- id (UUID PK), user_id (UUID FK users CASCADE), comment_id (UUID FK idea_comments CASCADE)
- created_at (timestamptz default NOW)

**`idea_polls`** (Quick validation polls)
- id (UUID PK), insight_id (UUID FK insights CASCADE), created_by (UUID FK users nullable)
- question (varchar 255 NOT NULL), poll_type (varchar 20 default 'yes_no': yes_no/scale/multiple)
- options (JSONB nullable), is_active (bool default true), expires_at (timestamptz nullable)
- created_at (timestamptz default NOW)

**`poll_responses`** (User poll responses)
- id (UUID PK), poll_id (UUID FK idea_polls CASCADE), user_id (UUID FK users CASCADE)
- response (varchar 100 NOT NULL), created_at (timestamptz default NOW)
- **Constraints**: UNIQUE(poll_id, user_id)

**`comments`** (General insight comments with full moderation)
- id (UUID PK), content (text NOT NULL), insight_id (UUID FK insights CASCADE indexed)
- user_id (UUID FK users CASCADE indexed), parent_id (UUID FK comments CASCADE nullable indexed)
- depth (int default 0), vote_score (int default 0 indexed), upvote_count (int default 0), downvote_count (int default 0)
- status (varchar 20 default 'active': active/hidden/deleted/flagged indexed)
- flagged (bool default false), flag_reason (varchar 255 nullable)
- created_at (indexed), updated_at, edited_at (nullable)

**`comment_votes`** (Comment vote tracking)
- id (UUID PK), comment_id (UUID FK comments CASCADE indexed), user_id (UUID FK users CASCADE indexed)
- vote_type (varchar 10: up/down), created_at (timestamptz default NOW)

#### Phase 9.5: Social & Community (5 tables)

**`founder_profiles`** (Public founder profiles)
- id (UUID PK), user_id (UUID FK users CASCADE UNIQUE)
- username (varchar 50 UNIQUE), display_name (varchar 100), bio (text)
- avatar_url (varchar 500), location (varchar 100)
- skills (JSONB array), interests (JSONB array), social_links (JSONB: {twitter, linkedin, github})
- is_public (bool default false), accepting_connections (bool default true)
- connection_count (int default 0), created_at, updated_at

**`founder_connections`** (Connection requests)
- id (UUID PK), requester_id (UUID FK users CASCADE), recipient_id (UUID FK users CASCADE)
- status (varchar 20 default 'pending': pending/accepted/rejected)
- message (text nullable), created_at, responded_at (nullable)
- **Constraints**: UNIQUE(requester_id, recipient_id)

**`idea_clubs`** (Topic-based communities)
- id (UUID PK), name (varchar 100 UNIQUE), slug (varchar 100 UNIQUE)
- description (text), category (varchar 50), cover_image_url (varchar 500)
- member_count (int default 0), post_count (int default 0)
- is_public (bool default true), is_official (bool default false)
- created_by (UUID FK users nullable), created_at

**`club_members`** (Club membership)
- id (UUID PK), club_id (UUID FK idea_clubs CASCADE), user_id (UUID FK users CASCADE)
- role (varchar 20 default 'member': admin/moderator/member)
- joined_at (timestamptz default NOW)
- **Constraints**: UNIQUE(club_id, user_id)

**`club_posts`** (Club discussion posts)
- id (UUID PK), club_id (UUID FK idea_clubs CASCADE), user_id (UUID FK users CASCADE)
- title (varchar 255 nullable), content (text NOT NULL)
- post_type (varchar 20 default 'discussion': discussion/idea_share/question)
- insight_id (UUID FK insights nullable - for idea sharing)
- upvotes (int default 0), comment_count (int default 0)
- is_pinned (bool default false), is_deleted (bool default false)
- created_at, updated_at

#### Phase 9.6: Gamification (5 tables)

**`achievements`** (Achievement definitions)
- id (UUID PK), name (varchar 100 UNIQUE), description (text), badge_icon (varchar 500)
- points (int NOT NULL), criteria (JSONB NOT NULL: {"type": "count", "metric": "ideas_saved", "threshold": 10})
- category (varchar 50: explorer/curator/analyst/builder/social/community/engagement)
- is_active (bool default true), created_at

**`user_achievements`** (Earned achievements)
- id (UUID PK), user_id (UUID FK users CASCADE), achievement_id (UUID FK achievements CASCADE)
- earned_at (timestamptz default NOW)
- **Constraints**: UNIQUE(user_id, achievement_id)

**`user_points`** (Points & level tracking)
- id (UUID PK), user_id (UUID FK users CASCADE UNIQUE)
- total_points (int default 0), level (int default 1), achievements_count (int default 0)
- current_streak (int default 0), longest_streak (int default 0), last_activity_date (date nullable)
- updated_at (timestamptz default NOW)
- **Level Formula**: Level n requires n*(n+1)*50 points

**`user_credits`** (Credit balance for premium features)
- id (UUID PK), user_id (UUID FK users CASCADE UNIQUE)
- balance (int default 0), lifetime_earned (int default 0), lifetime_spent (int default 0)
- updated_at (timestamptz default NOW)
- **Earning**: Daily login 5cr, Save idea 2cr, Vote 1cr, Comment 3cr, Refer 50cr
- **Spending**: AI Chat 5cr, Research 500cr, Export 100cr, Landing page 200cr

**`credit_transactions`** (Credit transaction history)
- id (UUID PK), user_id (UUID FK users CASCADE)
- amount (int NOT NULL: positive=earn, negative=spend)
- transaction_type (varchar 50: earn_daily_login/earn_save_idea/earn_vote/earn_comment/earn_referral/earn_purchase/spend_chat/spend_research/spend_export/spend_landing_page)
- description (varchar 255 nullable)
- reference_id (UUID nullable), reference_type (varchar 50 nullable)
- created_at (timestamptz default NOW)

#### Collections & Reputation (4 tables)

**`collections`** (User-curated insight lists)
- id (UUID PK), title (varchar 200 NOT NULL), slug (varchar 250 UNIQUE indexed)
- description (text nullable - Markdown), cover_image_url (varchar 500), emoji_icon (varchar 10)
- owner_id (UUID FK users CASCADE indexed)
- is_public (bool default true indexed), is_featured (bool default false indexed)
- insight_count (int default 0), follower_count (int default 0), view_count (int default 0)
- tags (JSONB array), settings (JSONB: {allow_comments, allow_suggestions})
- created_at (indexed), updated_at

**`collection_items`** (Collection-insight association)
- id (UUID PK), collection_id (UUID FK collections CASCADE indexed)
- insight_id (UUID FK insights CASCADE indexed)
- added_by_id (UUID FK users nullable), sort_order (int default 0 indexed)
- note (text nullable - curator note), added_at (timestamptz default NOW)

**`collection_followers`** (Collection followers)
- id (UUID PK), collection_id (UUID FK collections CASCADE indexed)
- user_id (UUID FK users CASCADE indexed)
- notify_on_add (bool default true)
- followed_at (timestamptz default NOW)

**`user_reputation`** (Karma tracking)
- id (UUID PK), user_id (UUID FK users CASCADE UNIQUE indexed)
- total_karma (int default 0 indexed), insight_karma (int default 0)
- comment_karma (int default 0), collection_karma (int default 0)
- is_verified_expert (bool default false), expert_badge (varchar 100 nullable)
- verified_at (timestamptz nullable)
- insights_created (int default 0), comments_created (int default 0), collections_created (int default 0)
- created_at, updated_at

#### Competitive Intelligence (2 tables)

**`competitor_profiles`** (Competitor tracking per insight)
- id (UUID PK), insight_id (UUID FK insights CASCADE indexed)
- name (varchar 200 indexed), url (varchar 500), description (text)
- market_position (varchar 50: leader/challenger/niche/startup)
- metrics (JSONB: {funding, team_size, pricing, monthly_traffic, social_proof, alexa_rank, founded_year})
- features (JSONB: {ai_powered, real_time_updates, api_access, white_label, sso, advanced_analytics})
- value_proposition (text), target_audience (varchar 500)
- strengths (JSONB array), weaknesses (JSONB array)
- positioning_x (int: 1-10 price), positioning_y (int: 1-10 features)
- last_scraped_at, scrape_status, scrape_error, analysis_generated_at, analysis_model
- created_at (indexed), updated_at
- **Indexes**: ix_competitor_profiles_insight_id_name, ix_competitor_profiles_market_position, ix_competitor_profiles_last_scraped_at

**`competitor_snapshots`** (Historical competitor data)
- id (UUID PK), competitor_id (UUID FK competitor_profiles CASCADE indexed)
- snapshot_data (JSONB NOT NULL: full competitor state)
- changes_detected (JSONB array: [{field, old_value, new_value, change_type}])
- scraped_at (timestamptz indexed), scrape_method (varchar 50: firecrawl/manual/api)
- **Indexes**: ix_competitor_snapshots_competitor_id_scraped_at

#### Phase 10: Integration Ecosystem (5 tables)

**`external_integrations`** (Connected services)
- id (UUID PK), user_id (UUID FK users CASCADE)
- service_type (varchar 50: notion/airtable/slack/discord/linear/jira)
- service_name (varchar 100 nullable)
- access_token (text nullable - encrypted), refresh_token (text nullable), token_expires_at (timestamptz nullable)
- workspace_id (varchar 255), workspace_name (varchar 255)
- config (JSONB nullable), is_active (bool default true)
- last_sync_at (timestamptz nullable), sync_error (text nullable)
- created_at, updated_at

**`integration_webhooks`** (Webhook endpoints)
- id (UUID PK), integration_id (UUID FK external_integrations CASCADE)
- webhook_type (varchar 50: new_insight/insight_update/research_complete/trending_alert)
- webhook_url (varchar 500), secret (varchar 255 nullable)
- is_active (bool default true), last_triggered_at (timestamptz nullable), failure_count (int default 0)
- created_at (timestamptz default NOW)

**`integration_syncs`** (Sync operation logs)
- id (UUID PK), integration_id (UUID FK external_integrations CASCADE)
- sync_type (varchar 50: full/incremental/webhook)
- status (varchar 20: started/completed/failed)
- items_synced (int default 0), items_failed (int default 0), error_message (text nullable)
- started_at (timestamptz default NOW), completed_at (timestamptz nullable)

**`browser_extension_tokens`** (Chrome extension auth)
- id (UUID PK), user_id (UUID FK users CASCADE)
- token_hash (varchar 64 UNIQUE), device_name (varchar 100), browser (varchar 50: chrome/firefox/edge/safari)
- last_used_at (timestamptz nullable), last_ip (varchar 45 nullable)
- is_active (bool default true), created_at, expires_at (timestamptz nullable)

**`bot_subscriptions`** (Slack/Discord bot subscriptions)
- id (UUID PK), integration_id (UUID FK external_integrations CASCADE)
- channel_id (varchar 100 NOT NULL), channel_name (varchar 100 nullable)
- subscription_type (varchar 50: keyword/trending/new_insights/high_score)
- keywords (JSONB array nullable), min_score (numeric 3,2 nullable)
- frequency (varchar 20 default 'instant': instant/daily/weekly)
- is_active (bool default true), last_notified_at (timestamptz nullable)
- created_at (timestamptz default NOW)

### 4.11 Table Count Summary

| Phase | Tables | Count |
|-------|--------|-------|
| Phase 1-3 (Core) | raw_signals, insights | 2 |
| Phase 4.1 (Auth) | users, saved_insights, user_ratings, insight_interactions | 4 |
| Phase 4.2 (Admin) | admin_users, agent_execution_logs, system_metrics | 3 |
| Phase 5 (Research) | research_requests, custom_analyses | 2 |
| Phase 6.1 (Payments) | subscriptions, payment_history, webhook_events | 3 |
| Phase 6.4 (Teams) | teams, team_members, team_invitations, shared_insights | 4 |
| Phase 7 (API/Tenant) | api_keys, api_key_usage_logs, tenants, tenant_users | 4 |
| Phase 12-14 (Public) | tools, success_stories, trends, market_insights | 4 |
| **Phase 1-7/12-14 Subtotal** | | **26** |
| Phase 8.1 (Content Quality) | content_review_queue, content_similarity | 2 |
| Phase 8.2 (Pipeline) | pipeline_health_checks, api_quota_usage, admin_alerts, admin_alert_incidents | 4 |
| Phase 8.3 (Analytics) | user_activity_events, user_sessions | 2 |
| Phase 8.4-8.5 (Agent/Audit) | agent_configurations, audit_logs | 2 |
| Phase 9.1 (Preferences) | user_preferences, email_preferences, email_sends | 3 |
| Phase 9.2 (Chat) | idea_chats, idea_chat_messages | 2 |
| Phase 9.3 (Community) | idea_votes, idea_comments, comment_upvotes, idea_polls, poll_responses, comments, comment_votes | 7 |
| Phase 9.5 (Social) | founder_profiles, founder_connections, idea_clubs, club_members, club_posts | 5 |
| Phase 9.6 (Gamification) | achievements, user_achievements, user_points, user_credits, credit_transactions | 5 |
| Collections/Reputation | collections, collection_items, collection_followers, user_reputation | 4 |
| Competitive Intel | competitor_profiles, competitor_snapshots | 2 |
| Phase 10 (Integrations) | external_integrations, integration_webhooks, integration_syncs, browser_extension_tokens, bot_subscriptions | 5 |
| **Phase 8-10 Subtotal** | | **43** |
| **Grand Total** | | **69** |

---

## 5. API Endpoints (230 Total)

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

### 5.3 Phase 5 (Advanced Analysis - 28 endpoints)

**AI Research - User Endpoints** (7 endpoints)
- `POST /api/research/request` - Submit research request (queued for admin approval)
- `GET /api/research/requests` - List user's research requests
- `GET /api/research/requests/{id}` - Get request status
- `POST /api/research/analyze` - DEPRECATED: Direct analysis (use /request instead)
- `GET /api/research/analysis/{id}` - Get analysis result
- `GET /api/research/analyses` - List user's analyses
- `GET /api/research/quota` - Get quota status

**AI Research - Admin Endpoints** (5 endpoints)
- `GET /api/research/admin/requests` - List all research requests (filter: status)
- `PATCH /api/research/admin/requests/{id}` - Approve/reject request
- `POST /api/research/admin/analyze` - Manually trigger analysis (bypass request system)
- `GET /api/research/admin/analyses` - List all analyses (all users)
- `DELETE /api/research/admin/analyses/{id}` - Delete analysis

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

### 5.6 Phase 12-14: Public Content APIs (26 endpoints)

**Tools API** (6 endpoints - Public)
- `GET /api/tools` - List all tools (filter: category, limit, offset)
- `GET /api/tools/featured` - Get featured tools (limit param)
- `GET /api/tools/{id}` - Get single tool details
- `POST /api/tools` - Create tool (admin only)
- `PATCH /api/tools/{id}` - Update tool (admin only)
- `DELETE /api/tools/{id}` - Delete tool (admin only)

**Success Stories API** (6 endpoints - Public)
- `GET /api/success-stories` - List all success stories (filter: featured, limit, offset)
- `GET /api/success-stories/featured` - Get featured stories (limit param)
- `GET /api/success-stories/{id}` - Get single story details
- `POST /api/success-stories` - Create story (admin only)
- `PATCH /api/success-stories/{id}` - Update story (admin only)
- `DELETE /api/success-stories/{id}` - Delete story (admin only)

**Trends API** (5 endpoints - Public)
- `GET /api/trends` - List all trends (filter: category, sort: volume|growth, limit, offset)
- `GET /api/trends/featured` - Get featured trends (limit param)
- `GET /api/trends/{keyword}` - Get trend details by keyword
- `POST /api/trends` - Create/update trend (admin only)
- `DELETE /api/trends/{id}` - Delete trend (admin only)

**Market Insights API** (6 endpoints - Public)
- `GET /api/market-insights` - List published articles (filter: category, limit, offset)
- `GET /api/market-insights/featured` - Get featured articles (limit param)
- `GET /api/market-insights/{slug}` - Get single article by slug
- `POST /api/market-insights` - Create article (admin only)
- `PATCH /api/market-insights/{id}` - Update article (admin only)
- `DELETE /api/market-insights/{id}` - Delete article (admin only)

**Idea of the Day API** (3 endpoints - Public)
- `GET /api/idea-of-day` - Get today's featured idea (anonymous access)
- `GET /api/idea-of-day/history` - Get past ideas (limit: 7 days)
- `POST /api/idea-of-day/refresh` - Manually refresh (admin only)

### 5.7 Authentication

**All Phase 4+ endpoints require**:
- `Authorization: Bearer <supabase_jwt>` header
- JWT verified via Supabase Auth

**Public endpoints** (no auth):
- `/health`, `/api/insights` (read-only), `/api/payments/pricing`, `/api/payments/webhooks/stripe`

### 5.8 Phase 8-10 Endpoints (99 new endpoints)

#### Content Quality API (7 endpoints - Admin)
- `GET /api/admin/content/review-queue` - List pending content (filters: status, content_type, quality_score_lt)
- `PATCH /api/admin/content/review-queue/{id}` - Approve/reject/flag with notes
- `POST /api/admin/content/review-queue/bulk` - Bulk approve/reject multiple items
- `GET /api/admin/content/review-queue/stats` - Queue statistics (pending, approved, rejected, auto-approval rate)
- `GET /api/admin/content/duplicates` - List potential duplicates (filters: resolved, similarity_type)
- `POST /api/admin/content/duplicates/{id}/resolve` - Resolve duplicate (keep_both/merge/delete_newer)
- `GET /api/admin/content/duplicates/stats` - Duplicate rate metrics

#### Pipeline Dashboard API (11 endpoints - Admin)
- `GET /api/admin/pipeline/status` - Real-time pipeline status (all scrapers, quotas, processing queue)
- `GET /api/admin/pipeline/health-history` - Historical health data (filter: scraper, hours)
- `POST /api/admin/pipeline/scrapers/{name}/trigger` - Manual scraper trigger
- `POST /api/admin/pipeline/scrapers/{name}/pause` - Pause scraper
- `GET /api/admin/pipeline/quotas` - API quota usage history (filter: api_name, days)
- `GET /api/admin/pipeline/alerts` - List configured alerts (filter: active_only)
- `POST /api/admin/pipeline/alerts` - Create alert configuration
- `PATCH /api/admin/pipeline/alerts/{id}` - Update alert (name, condition, severity, channels)
- `DELETE /api/admin/pipeline/alerts/{id}` - Delete alert
- `GET /api/admin/pipeline/incidents` - List alert incidents (filter: status)
- `PATCH /api/admin/pipeline/incidents/{id}` - Acknowledge/resolve incident

#### User Analytics API (7 endpoints - Admin)
- `GET /api/admin/analytics/users` - User analytics overview (total, active, by tier, engagement)
- `GET /api/admin/analytics/users/cohorts` - Cohort retention analysis (weeks parameter)
- `GET /api/admin/analytics/revenue` - Revenue metrics (MRR, ARR, subscriptions, churn)
- `GET /api/admin/analytics/users/list` - List users (search, filter by tier, pagination)
- `GET /api/admin/analytics/users/{id}` - User detail (saved insights, research count, sessions)
- `PATCH /api/admin/analytics/users/{id}` - Update user (tier, suspension)
- `GET /api/admin/analytics/users/export` - Export user list (CSV/JSON)

#### Agent Control API (8 endpoints - Admin)
- `GET /api/admin/agents/configurations` - List all agent configurations
- `GET /api/admin/agents/configurations/{agent_name}` - Get specific agent configuration
- `PATCH /api/admin/agents/configurations/{agent_name}` - Update agent config (model, temperature, limits)
- `POST /api/admin/agents/configurations/{agent_name}/toggle` - Enable/disable agent
- `GET /api/admin/agents/stats` - Agent execution statistics (24h: success rate, duration, tokens, cost)
- `GET /api/admin/agents/audit-logs` - List security audit logs (filter: action, user, resource, days)
- `GET /api/admin/agents/audit-logs/actions` - List distinct audit actions with counts
- `GET /api/admin/agents/audit-logs/stats` - Audit log statistics (by action, by resource type)

#### Preferences API (7 endpoints - Authenticated)
- `GET /api/preferences/user` - Get user preferences (creates default if not exists)
- `PATCH /api/preferences/user` - Update user preferences (background, budget, skills)
- `POST /api/preferences/quiz` - Submit idea match quiz (5 questions, instant results)
- `GET /api/preferences/email` - Get email preferences (creates default if not exists)
- `PATCH /api/preferences/email` - Update email preferences (digest, alerts, keywords)
- `POST /api/preferences/email/unsubscribe` - Unsubscribe from all emails
- `POST /api/preferences/email/resubscribe` - Resubscribe with default settings

#### Community API (10 endpoints - Authenticated)
- `POST /api/community/insights/{id}/vote` - Vote on idea (up/down, toggle off)
- `GET /api/community/insights/{id}/votes` - Get vote summary (upvotes, downvotes, user vote)
- `POST /api/community/insights/{id}/comments` - Add comment (threaded with parent_id)
- `GET /api/community/insights/{id}/comments` - List comments (filter: parent_id, pagination)
- `PATCH /api/community/comments/{id}` - Update own comment
- `DELETE /api/community/comments/{id}` - Soft delete own comment
- `POST /api/community/comments/{id}/upvote` - Upvote comment (toggle)
- `POST /api/community/insights/{id}/polls` - Create validation poll
- `GET /api/community/insights/{id}/polls` - List polls with results
- `POST /api/community/polls/{id}/respond` - Submit poll response

#### Gamification API (10 endpoints - Mixed auth)
- `GET /api/gamification/achievements` - List all achievements (filter: category, public)
- `GET /api/gamification/achievements/mine` - Get earned achievements (authenticated)
- `GET /api/gamification/points` - Get user points & level (authenticated)
- `POST /api/gamification/points/check-in` - Daily check-in, earn credits (authenticated)
- `GET /api/gamification/credits` - Get credit balance (authenticated)
- `GET /api/gamification/credits/transactions` - Get credit transaction history (authenticated)
- `GET /api/gamification/leaderboard/points` - Top users by points (public)
- `GET /api/gamification/leaderboard/streak` - Top users by streak (public)
- `POST /api/gamification/admin/grant-credits/{user_id}` - Admin: grant credits
- `POST /api/gamification/admin/grant-achievement/{user_id}/{achievement_id}` - Admin: grant achievement

#### Integration API (16 endpoints - Authenticated)
- `GET /api/integrations` - List user's integrations (filter: service_type)
- `POST /api/integrations` - Create integration (notion/airtable/slack/discord/linear/jira)
- `GET /api/integrations/{id}` - Get integration details
- `PATCH /api/integrations/{id}` - Update integration (name, active, config)
- `DELETE /api/integrations/{id}` - Delete integration (cascade webhooks, syncs)
- `POST /api/integrations/{id}/webhooks` - Create webhook (new_insight/insight_update/research_complete/trending_alert)
- `GET /api/integrations/{id}/webhooks` - List webhooks for integration
- `DELETE /api/integrations/webhooks/{id}` - Delete webhook
- `POST /api/integrations/extension/token` - Create browser extension token
- `GET /api/integrations/extension/tokens` - List extension tokens
- `DELETE /api/integrations/extension/tokens/{id}` - Revoke extension token
- `POST /api/integrations/{id}/subscriptions` - Create bot subscription (Slack/Discord)
- `GET /api/integrations/{id}/subscriptions` - List bot subscriptions
- `DELETE /api/integrations/subscriptions/{id}` - Delete bot subscription
- `GET /api/integrations/{id}/syncs` - List sync history
- `POST /api/integrations/{id}/sync` - Trigger manual sync (full/incremental)

#### Idea Chat API (2 endpoints - Authenticated)
- `POST /api/ideas/{id}/chat` - Start or continue chat on an insight
- `GET /api/ideas/{id}/chat` - Get chat history for an insight

#### Health API (1 endpoint - Public)
- `GET /api/health` - Application health check (database, redis, services)

### 5.9 Endpoint Count Summary

| Phase | Category | Count |
|-------|----------|-------|
| Phase 1-3 | Health, Signals, Insights | 8 |
| Phase 4 | User Workspace, Admin | 31 |
| Phase 5 | Research, Build, Export, Feed | 28 |
| Phase 6 | Payments, Teams | 20 |
| Phase 7 | API Keys, Tenants | 19 |
| Phase 12-14 | Tools, Stories, Trends, Blog, Idea of Day | 26 |
| **Phase 1-7/12-14 Subtotal** | | **132** |
| Phase 8.1 | Content Quality (Admin) | 7 |
| Phase 8.2 | Pipeline Dashboard (Admin) | 11 |
| Phase 8.3 | User Analytics (Admin) | 7 |
| Phase 8.4-8.5 | Agent Control & Audit (Admin) | 8 |
| Phase 9.1 | Preferences & Email | 7 |
| Phase 9.2 | Idea Chat | 2 |
| Phase 9.3 | Community (Votes, Comments, Polls) | 10 |
| Phase 9.6 | Gamification | 10 |
| Phase 10 | Integrations | 16 |
| Health | Application health check | 1 |
| **Phase 8-10 Subtotal** | | **79** |
| **Unspecified/Cross-cutting** | | **19** |
| **Grand Total** | | **232+** |

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

## 7.5 Frontend Routes (34 Total)

### Phase 1-7 Routes (18 routes)

**Core Application** (8 routes):
- `/` - Homepage/dashboard
- `/insights` - Browse insights (filter, search)
- `/insights/[id]` - Insight detail page
- `/workspace` - User workspace (saved, building, interested)
- `/research` - AI research request form
- `/research/[id]` - Research analysis results
- `/build` - Build tools (brand packages, landing pages)
- `/profile` - User profile settings

**Admin Portal** (4 routes):
- `/admin` - Admin dashboard (metrics, agent control)
- `/admin/insights` - Insight moderation queue
- `/admin/users` - User management
- `/admin/research` - Research request queue

**Authentication** (3 routes):
- `/sign-in` - Clerk sign-in page
- `/sign-up` - Clerk sign-up page
- `/sign-out` - Logout handler

**Team Collaboration** (3 routes):
- `/teams` - Teams list
- `/teams/[id]` - Team workspace
- `/teams/[id]/settings` - Team settings

### Phase 12-14 Routes (16 routes)

**Public Pages** (10 routes):
- `/tools` - 54-tool directory (paginated, category filters)
- `/success-stories` - Founder case studies (12 stories)
- `/trends` - Trending keywords (180+ trends, search volume charts)
- `/market-insights` - Blog articles (6 articles)
- `/market-insights/[slug]` - Single blog article
- `/about` - Company story, mission, team
- `/contact` - Contact form (Resend email integration)
- `/faq` - Frequently asked questions
- `/pricing` - Pricing tiers (Free, Starter, Pro, Enterprise)
- `/platform-tour` - Product walkthrough

**Admin Content Management** (4 routes):
- `/admin/tools` - CRUD for tools directory
- `/admin/success-stories` - CRUD for success stories
- `/admin/trends` - CRUD for trends
- `/admin/market-insights` - CRUD for blog articles

**SEO Routes** (2 special routes):
- `/sitemap.xml` - Dynamic sitemap generation (app/sitemap.ts)
- `/robots.txt` - Crawler directives (public/robots.txt)

### Route Patterns

**Public vs Authenticated:**
- Public (no auth): `/`, `/tools`, `/success-stories`, `/trends`, `/market-insights`, `/about`, `/contact`, `/faq`, `/pricing`, `/platform-tour`, `/sitemap.xml`, `/robots.txt`
- Authenticated: `/workspace`, `/research`, `/build`, `/profile`, `/teams`
- Admin only: `/admin/*`

**Pagination:**
- `/insights?page=2&limit=12` (12 insights per page)
- `/tools?category=design&page=1` (12 tools per page)
- `/trends?sort=volume&page=3` (12 trends per page)
- `/market-insights?category=guides&page=1` (6 articles per page)

**SEO Optimization:**
- All public pages: Server-side rendering (SSR)
- Metadata: Dynamic Open Graph tags, Twitter cards
- Structured data: JSON-LD for articles, tools, success stories

---

## 7.6 Navigation Architecture (Phase 12-14)

### Mega-Menu Structure

**Main Navigation Bar** (desktop):
- **Browse Ideas** (dropdown)
  - All Insights
  - Trending Now
  - Success Stories
  - Idea of the Day
- **Tools** (dropdown)
  - All Tools (54 tools)
  - By Category (6 categories)
  - Featured Tools
- **Resources** (dropdown)
  - Market Insights (blog)
  - Trending Keywords
  - Platform Tour
  - FAQ
- **Company** (dropdown)
  - About
  - Pricing
  - Contact
- **Sign In** / **Dashboard** (auth-dependent)

**Mobile Navigation** (sheet drawer):
- Accordion sections for dropdowns
- Collapsible categories
- Touch-optimized tap targets

**Component Implementation:**
```typescript
// components/navigation/main-nav.tsx
import { NavigationMenu, NavigationMenuItem, NavigationMenuTrigger, NavigationMenuContent } from '@/components/ui/navigation-menu'

<NavigationMenu>
  <NavigationMenuItem>
    <NavigationMenuTrigger>Browse Ideas</NavigationMenuTrigger>
    <NavigationMenuContent>
      {/* 4 links */}
    </NavigationMenuContent>
  </NavigationMenuItem>
  {/* 3 more menus */}
</NavigationMenu>
```

**Keyboard Navigation:**
- Arrow keys: Navigate menu items
- Enter: Activate link
- Escape: Close dropdown
- Tab: Skip to next section

**Accessibility:**
- ARIA labels on all menu items
- Focus indicators (Tailwind ring utilities)
- Screen reader announcements

---

## 7.7 SEO Infrastructure (Phase 14)

### Dynamic Sitemap Generation

**File:** `frontend/app/sitemap.ts`

```typescript
import { MetadataRoute } from 'next'

export default async function sitemap(): Promise<MetadataRoute.Sitemap> {
  const baseUrl = 'https://startinsight.app'

  // Static pages
  const routes = ['', '/tools', '/success-stories', '/trends', '/market-insights', '/about', '/contact', '/faq', '/pricing', '/platform-tour']

  // Dynamic pages (fetch from API)
  const insights = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/api/insights`).then(r => r.json())
  const articles = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/api/market-insights`).then(r => r.json())

  return [
    ...routes.map(route => ({
      url: `${baseUrl}${route}`,
      lastModified: new Date(),
      changeFrequency: 'weekly',
      priority: route === '' ? 1.0 : 0.8
    })),
    ...insights.map(insight => ({
      url: `${baseUrl}/insights/${insight.id}`,
      lastModified: new Date(insight.created_at),
      changeFrequency: 'monthly',
      priority: 0.6
    })),
    ...articles.map(article => ({
      url: `${baseUrl}/market-insights/${article.slug}`,
      lastModified: new Date(article.updated_at),
      changeFrequency: 'monthly',
      priority: 0.7
    }))
  ]
}
```

### Metadata Configuration

**Global Metadata** (`app/layout.tsx`):
```typescript
export const metadata: Metadata = {
  metadataBase: new URL('https://startinsight.app'),
  title: {
    default: 'StartInsight - AI-Powered Startup Idea Discovery',
    template: '%s | StartInsight'
  },
  description: 'Discover data-driven startup ideas with AI analysis. 180+ trending keywords, 54 tools, founder success stories, and daily insights.',
  openGraph: {
    type: 'website',
    locale: 'en_US',
    url: 'https://startinsight.app',
    siteName: 'StartInsight',
    images: [{ url: '/og-image.png', width: 1200, height: 630 }]
  },
  twitter: {
    card: 'summary_large_image',
    site: '@startinsight',
    creator: '@startinsight'
  },
  robots: {
    index: true,
    follow: true,
    googleBot: {
      index: true,
      follow: true,
      'max-image-preview': 'large',
      'max-snippet': -1
    }
  }
}
```

**Page-Specific Metadata:**
- `/insights/[id]`: Dynamic OG images with insight title, problem statement
- `/market-insights/[slug]`: Article cover image, author, reading time
- `/tools`: List of 54 tools, category filters
- `/success-stories`: Founder names, company logos

### Structured Data (Schema.org)

**Article Schema** (blog posts):
```json
{
  "@context": "https://schema.org",
  "@type": "Article",
  "headline": "{{ article.title }}",
  "description": "{{ article.summary }}",
  "author": {
    "@type": "Person",
    "name": "{{ article.author_name }}"
  },
  "datePublished": "{{ article.published_at }}",
  "dateModified": "{{ article.updated_at }}",
  "image": "{{ article.cover_image_url }}"
}
```

**Product Schema** (tools):
```json
{
  "@context": "https://schema.org",
  "@type": "Product",
  "name": "{{ tool.name }}",
  "description": "{{ tool.description }}",
  "category": "{{ tool.category }}",
  "offers": {
    "@type": "Offer",
    "price": "{{ tool.pricing }}"
  }
}
```

### robots.txt

```txt
User-agent: *
Allow: /

# Disallow admin routes
Disallow: /admin/
Disallow: /api/

# Sitemap
Sitemap: https://startinsight.app/sitemap.xml
```

---

## 8. Deployment Architecture

### 8.1 Production Stack

| Service | Platform | Region | Specs |
|---------|----------|--------|-------|
| **Frontend** | Vercel | Global CDN | Edge runtime, ISR |
| **Backend** | Railway | US/Sydney | 2 vCPU, 4GB RAM |
| **Database** | Supabase | Sydney (ap-southeast-2) | Pro tier, connection pooling |
| **Redis** | Upstash | Global | 1GB memory, persistent |
| **Worker** | Railway | Same as backend | Background process |

### 8.2 Environment Variables

**Backend (.env)**:
```bash
# Database (Supabase Pro - Session Pooler)
DATABASE_URL=postgresql+asyncpg://postgres.[PROJECT_REF]:[PASSWORD]@aws-1-ap-southeast-2.pooler.supabase.com:5432/postgres
DB_POOL_SIZE=20
DB_MAX_OVERFLOW=30
DB_SSL=true
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
API_BASE_URL=https://api.startinsight.co
CORS_ORIGINS=https://startinsight.co
```

**Frontend (.env.local)**:
```bash
NEXT_PUBLIC_API_URL=https://api.startinsight.co
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

### 9.1 PydanticAI Agents (6 Agents)

**1. Basic Analyzer** (`analyzer.py` - Phase 2):
- Model: Claude 3.5 Sonnet
- Input: RawSignal content (markdown)
- Output: InsightSchema (problem, solution, market_size, relevance_score, competitor_analysis)
- Cost: $0.003/insight

**2. Enhanced Analyzer** (`enhanced_analyzer.py` - Phase 4.3, expanded):
- 8-dimension scoring (opportunity, problem, feasibility, why_now, go_to_market, founder_fit, execution_difficulty, revenue_potential)
- 500+ word character-driven narratives
- Community signals chart with 4-platform engagement data
- Trend keywords with volume and growth metrics
- Cost: $0.05/insight

**3. Research Agent** (`research_agent.py` - Phase 5.1):
- 40-step iterative analysis (market sizing, competitor deep-dive, frameworks)
- Cost: $2.50-$5.00/research
- Async execution with webhook callback

**4. Competitive Intelligence Agent** (`competitive_intel_agent.py`):
- Market positioning analysis with 2x2 matrix
- Competitor strengths/weaknesses assessment
- Feature comparison matrix generation
- Strategic recommendations and market gap identification

**5. Market Intelligence Agent** (`market_intel_agent.py`):
- TAM/SAM/SOM market sizing calculations
- Industry benchmark analysis
- Weekly market digest generation
- Trend-to-opportunity mapping

**6. Content Generator Agent** (`content_generator_agent.py`):
- Blog post generation from insight data
- Social media content (Twitter/X, LinkedIn)
- SEO-optimized meta descriptions
- Content calendar suggestions

### 9.2 Prompt Engineering

**System Prompt** (Enhanced Analyzer):
```
You are a startup idea analyst. Analyze the provided market signal and extract:
1. Problem statement (2-3 sentences, specific pain point)
2. Proposed solution (2-3 sentences, clear value prop)
3. Market size estimate (Small <$100M, Medium $100M-$1B, Large >$1B)
4. Relevance score (0.0-1.0, how actionable is this opportunity)
5. Top 3 competitors (name, URL, market position)
6. 8-dimension scoring (1-10 scale):
   - Opportunity: Market size, growth rate
   - Problem: Severity, frequency, willingness to pay
   - Feasibility: Technical complexity, resource requirements
   - Why Now: Market timing, regulatory changes, tech enablers
   - Go-to-Market: Customer acquisition cost, viral potential
   - Founder Fit: Required expertise, network, credibility
   - Execution Difficulty: Time to market, defensibility
   - Revenue Potential: Pricing power, recurring revenue viability
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

### 9.4 Super Admin Agent Controller Architecture

**Purpose:** Real-time monitoring and control dashboard for AI agents, scrapers, and system metrics

**Components:**

1. **Agent Execution Logs Table**
   - Schema: agent_name, status, started_at, completed_at, tokens_used, cost, error_message
   - Indexes: idx_agent_name, idx_status, idx_started_at DESC
   - Retention: 90 days (configurable)

2. **System Metrics Table**
   - Schema: metric_name, value, unit, timestamp
   - Metrics: llm_cost_daily, scraper_success_rate, insight_generation_rate, api_response_time_p95
   - Aggregation: 5-minute intervals

3. **Agent Control Endpoints** (backend/app/api/routes/admin.py)
   - GET /admin/dashboard - System overview
   - GET /admin/agents/logs - Agent execution history
   - POST /admin/agents/{agent_name}/pause - Pause agent execution
   - POST /admin/agents/{agent_name}/resume - Resume agent execution
   - POST /admin/agents/{agent_name}/trigger - Manually trigger agent
   - GET /admin/metrics/stream - SSE streaming (5-second interval)

4. **Frontend Implementation**
   - Real-time charts (agent execution timeline, cost trends)
   - Pause/resume controls (one-click agent management)
   - Alert notifications (high cost, scraper failures)
   - Audit log viewer

**Competitive Advantage:**
- IdeaBrowser: Inferred admin tools (no public documentation)
- StartInsight: 13 admin endpoints, SSE real-time streaming, documented architecture
- Impact: Transparent system control, cost management, operational visibility

### 9.5 Evidence Engine Architecture (Updated 2026-01-25 - Post-Ralph-Loop)

**VISUALIZATION MANDATE:**
Every insight MUST include data-driven visualizations. Evidence MUST be visual. Text narratives support charts, not replace them.

**Data Visualization Pipeline (Scraper → AI → Database → Frontend):**

```mermaid
graph LR
    A[Reddit Scraper] -->|PRAW API| B[Raw Signals Table]
    C[Firecrawl Scraper] -->|Web to Markdown| B
    D[Google Trends] -->|pytrends| B
    B -->|Triggers| E[Enhanced Analyzer Agent]
    E -->|Gemini 2.0 Flash| F[Insight Analysis]
    F -->|JSONB| G[(Insights Table)]
    G -->|API Response| H[Frontend Next.js]
    H -->|TrendChart.tsx| I[Recharts Line Chart]
    H -->|CommunitySignalsRadar.tsx| J[Tremor AreaChart]
    H -->|ScoreRadar.tsx| K[Recharts Radar]
    H -->|TrendKeywordCards.tsx| L[shadcn/ui Cards]
    I -->|Rendered| M[User Browser]
    J -->|Rendered| M
    K -->|Rendered| M
    L -->|Rendered| M
```

**Frontend Component Strategy:**

| Evidence Type | Backend Storage | Frontend Component | Library | Status |
|--------------|----------------|-------------------|---------|--------|
| Search volume trends | trend_keywords JSONB | TrendChart.tsx | Recharts LineChart | Complete |
| Community engagement | community_signals_chart JSONB | CommunitySignalsRadar.tsx | Tremor AreaChart | Planned |
| 8-dimension scores | enhanced_scores JSONB | ScoreRadar.tsx | Recharts RadarChart | Planned |
| Keyword volume/growth | trend_keywords JSONB | TrendKeywordCards.tsx | shadcn/ui Badge + Card | Planned |
| Evidence citations | source_urls array | DataCitationLink.tsx | shadcn/ui Link | Complete |

**Quality Parity Achievement:**
- Ralph Loop Iteration 1: STARTINSIGHT_WINS (2026-01-25)
- Content quality: 9/10 (matches IdeaBrowser)
- Problem statements: 500+ words with character-driven storytelling
- Community platforms: 3-4 (PARITY with IdeaBrowser)
- Trend keywords: 3 (EXCEEDS IdeaBrowser's 1-2)
- Scoring depth: 8 dimensions (EXCEEDS IdeaBrowser's 4)

**Data Layer (Backend - 100% Complete):**

1. **Signal Aggregation**
   - Input: 7 data sources (Reddit, Product Hunt, Google Trends, Twitter/X, Hacker News, Facebook, YouTube)
   - Processing: Firecrawl markdown conversion, PydanticAI analysis with Gemini 2.0 Flash
   - Storage: insights table with JSONB columns (community_signals_chart, enhanced_scores, trend_keywords)

2. **Insights Table Schema (JSONB Columns)**
```sql
-- community_signals_chart: Array of platform engagement data
[
  {
    "platform": "Reddit",
    "communities": "4 subreddits",
    "members": "2.5M+ members",
    "score": 8,
    "top_community": "r/legaltech"
  },
  {
    "platform": "Facebook",
    "communities": "4 groups",
    "members": "150K+ members",
    "score": 7,
    "top_community": "Legal Tech Innovators"
  },
  {
    "platform": "YouTube",
    "communities": "15 channels",
    "members": "N/A",
    "score": 7,
    "top_community": "LegalEagle"
  }
]

-- enhanced_scores: 8-dimension scoring object
{
  "opportunity": 8,
  "problem": 8,
  "feasibility": 8,
  "why_now": 9,
  "revenue_potential": 8,
  "execution_difficulty": 6,
  "go_to_market": 8,
  "founder_fit": 7
}

-- trend_keywords: Array of trending search terms
[
  {
    "keyword": "legal document automation",
    "volume": "1.0K",
    "growth": "+1900%"
  },
  {
    "keyword": "contract analysis AI",
    "volume": "27.1K",
    "growth": "+86%"
  },
  {
    "keyword": "law firm software",
    "volume": "74.0K",
    "growth": "+514%"
  }
]
```

**Visualization Layer (Frontend - 40% Complete):**

1. **TrendChart.tsx** (IMPLEMENTED - Phase 3)
   - Recharts LineChart for search volume over time
   - X-axis: Date range (2022-2025)
   - Y-axis: Search volume (0-100 normalized)
   - Tooltip: Volume + date on hover
   - Status: Production-ready

2. **CommunitySignalsRadar.tsx** (PLANNED - Phase 5.2)
   - Recharts RadarChart or AreaChart for 4-platform engagement
   - Data: Platform name + engagement score (1-10)
   - Visual: Radar overlay showing relative strength
   - Status: Backend data ready, component not built

3. **ScoreRadar.tsx** (PLANNED - Phase 5.2)
   - Recharts RadarChart for 8-dimension scoring
   - Dimensions: Opportunity, Problem, Feasibility, Why Now, Revenue, Execution, GTM, Founder Fit
   - Color-coded: 8-10 (green), 5-7 (amber), 1-4 (red)
   - Status: Backend data ready, component not built

4. **TrendKeywordCards.tsx** (PLANNED - Phase 5.2)
   - shadcn/ui Card grid for trending keywords
   - Display: Keyword, volume, growth percentage
   - Badges: Volume size (1K, 27K, 74K), Growth color-coded by percentage
   - Status: Backend data ready, component not built

5. **EvidencePanel.tsx** (ENHANCEMENT NEEDED)
   - Current: Basic collapsible sections
   - Planned: Integrate all visualization components (CommunitySignalsRadar, ScoreRadar, TrendKeywordCards)
   - Layout: Accordion sections per data source type
   - Status: Exists but needs chart integration

**Frontend Component Stack:**

| Component | Library | Status | Purpose |
|-----------|---------|--------|---------|
| TrendChart | Recharts v3.6.0 | IMPLEMENTED | Search volume line chart |
| CommunitySignalsRadar | Recharts RadarChart | PLANNED | 4-platform engagement visualization |
| ScoreRadar | Recharts RadarChart | PLANNED | 8-dimension scoring visualization |
| TrendKeywordCards | shadcn/ui Card + Badge | PLANNED | Keyword volume + growth cards |
| EvidencePanel | shadcn/ui Accordion | PARTIAL | Container for all evidence components |

**Competitive Advantage:**
- **IdeaBrowser**: Google Trends embedded, 4 platform badges (no charts)
- **StartInsight**: Multi-chart evidence stack (3 chart types minimum per insight)
- **Data Depth**: IdeaBrowser 4 dimensions, StartInsight 8 dimensions (+100%)
- **Keyword Coverage**: IdeaBrowser 1-2 keywords, StartInsight 3 keywords (+50-200%)
- **Verdict**: STARTINSIGHT_WINS on analytical depth (post-Ralph-Loop), GAP on visualization (60% remaining)

### 9.6 Builder Integration Architecture

**Purpose:** One-click deployment to external builder platforms (Lovable, v0, Replit, ChatGPT, Claude)

**Current Implementation (Phase 5.2):**
- Brand Package Generator: backend/app/services/brand_generator.py
- Landing Page Generator: backend/app/services/landing_page.py
- Export endpoints: GET /build/brands/{id}, GET /build/landing-pages/{id}

**Planned Integration Points:**

1. **Pre-filled Prompt Generation**
   - Generate contextual prompts from insight data
   - Support types: landing_page, brand_package, ad_creative, email_sequence

2. **API Endpoints (PLANNED)**
   - GET /build/insights/{id}/prompts/{type} - Get pre-filled prompt
   - POST /build/insights/{id}/deploy - Generate deployment URL

3. **Frontend Implementation (PLANNED)**
   - Builder platform selection UI (5 platforms)
   - Prompt type selector (4 types)
   - Pre-filled prompt preview modal
   - 1-click build workflow

**Data Flow:**
```
User clicks "Build This Idea"
  |
Select builder platform (Lovable, v0, etc.)
  |
Select prompt type (landing page, brand, ad creative)
  |
Backend generates pre-filled prompt with insight data
  |
Open builder platform in new tab with pre-filled context
```

**Competitive Positioning:**
- IdeaBrowser: 5 builder integrations (Lovable, v0, Replit, ChatGPT, Claude)
- StartInsight: Same 5 platforms + context-rich prompts (8-dimension scoring)
- Advantage: 40-step research agent provides deeper market insights for builder prompts

**Implementation Status:**
- Backend: Brand and landing page generators complete (Phase 5.2)
- Frontend: Build tools UI planned (not implemented)
- Integration: Builder URL generation planned (not implemented)

---

## 10. Phase 8-10 Architecture

### 10.1 Content Quality Management System (Phase 8.1)

**Purpose:** Human oversight of AI-generated content to maintain quality and trust.

**Architecture:**
```
AI generates content → ContentReviewQueue (auto-scored)
  |
  ├── Score >= 0.85 → Auto-approve
  ├── Score <= 0.40 → Auto-flag for review
  └── 0.40 < Score < 0.85 → Pending review
  |
Admin reviews → Approve/Reject/Flag with notes
  |
ContentSimilarity → TF-IDF duplicate detection (cosine >= 0.85)
  └── Resolution: keep_both / merge / delete_newer
```

**Key Features:**
- Quality score assignment (0.00-1.00) for all AI-generated content
- Auto-approval thresholds reduce admin workload
- Bulk approve/reject for efficient moderation
- Duplicate detection via TF-IDF cosine similarity
- "Human Verified" badge system for reviewed content

**Backend Files:**
- Model: `backend/app/models/content_review.py` (ContentReviewQueue, ContentSimilarity)
- Routes: `backend/app/api/routes/content_review.py` (7 endpoints)
- Migration: `backend/alembic/versions/b012_phase_8_1_content_quality.py`

### 10.2 Data Pipeline Command Center (Phase 8.2)

**Purpose:** Real-time visibility into data collection health for superadmins.

**Architecture:**
```
Scrapers (5) → PipelineHealthCheck (status per scraper)
  |
API Quotas (3) → APIQuotaUsage (tracking per service)
  |
Thresholds → AdminAlert → AdminAlertIncident
  |
SSE → Admin Dashboard (real-time updates)
```

**Monitored Services:**
- Scrapers: Reddit, Product Hunt, Hacker News, Twitter, Google Trends
- APIs: Anthropic (tokens/cost), Firecrawl (requests), Reddit (rate limit)

**Default Alert Thresholds:**
1. Scraper failure rate > 20% - Critical
2. API quota > 80% used - Warning
3. Processing queue > 100 pending - Warning
4. Zero insights generated in 12 hours - Critical
5. Anthropic cost > $50/day - Warning

**Backend Files:**
- Model: `backend/app/models/pipeline_monitoring.py` (PipelineHealthCheck, APIQuotaUsage, AdminAlert, AdminAlertIncident)
- Routes: `backend/app/api/routes/pipeline.py` (11 endpoints)
- Migration: `backend/alembic/versions/b013_phase_8_2_pipeline_dashboard.py`

### 10.3 User Analytics & Revenue Intelligence (Phase 8.3)

**Purpose:** Understand user behavior, retention, and revenue health.

**Metrics Tracked:**
- User overview: total, active (7d/30d), new, churn rate
- By tier: count, active rate, MRR per tier
- Engagement: avg session duration, insights viewed/saved, feature usage
- Cohort retention: week 1, week 4, conversion to paid
- Revenue: MRR, ARR, active subscriptions, growth

**User Management Console:**
- Search by email, name, tier
- View activity timeline with session data
- Actions: upgrade/downgrade tier, suspend
- Export user list (CSV/JSON)

**Backend Files:**
- Model: `backend/app/models/user_analytics.py` (UserActivityEvent, UserSession)
- Routes: `backend/app/api/routes/analytics.py` (7 endpoints)
- Migration: `backend/alembic/versions/b014_phase_8_3_user_analytics.py`

### 10.4 User Engagement Features (Phase 9)

**Preferences & Idea Matching (Phase 9.1):**
- 5-question idea match quiz (background, budget, time, market, risk)
- Personalized recommendations based on quiz results
- Email digest system (daily/weekly/instant alerts)
- Keyword tracking with min score threshold

**AI Idea Chat (Phase 9.2):**
- Context-aware Q&A about any insight
- Chat history persistence per user/insight
- Quota limits: Free 5 msg/day, Starter 50, Pro unlimited
- Pre-built prompts: "What are the risks?", "How to validate?"

**Community Voting & Comments (Phase 9.3):**
- Upvote/downvote ideas (toggle, one per user)
- Threaded comment system with parent_id
- Comment upvotes and expert badges
- Validation polls (yes/no, scale, multiple choice)

**Backend Files:**
- Models: `user_preferences.py`, `idea_chat.py`, `community.py`, `comment.py`
- Routes: `preferences.py` (7), `community.py` (10)
- Migrations: `b016_phase_9_1`, `b017_phase_9_2`, `b018_phase_9_3`

### 10.5 Gamification Framework (Phase 9.6)

**Achievement System:**
- 10 achievement categories (Explorer, Curator, Analyst, Builder, Networker, etc.)
- Points awarded per achievement (10-200 points)
- Level progression: Level n requires n*(n+1)*50 points

**Credit Economy:**
- Earning: Daily login 5cr, Save idea 2cr, Vote 1cr, Comment 3cr, Refer 50cr
- Spending: AI Chat 5cr, Research 500cr, Premium export 100cr, Landing page 200cr

**Leaderboards:**
- Top users by total points
- Top users by current login streak
- Per-category rankings

**Daily Check-in Flow:**
```
User visits app → POST /gamification/points/check-in
  |
  ├── Already checked in today → return streak
  └── First visit today:
      ├── Update streak (consecutive day check)
      ├── Award 5 credits
      └── Record CreditTransaction
```

**Backend Files:**
- Model: `backend/app/models/gamification.py` (Achievement, UserAchievement, UserPoints, UserCredits, CreditTransaction)
- Routes: `backend/app/api/routes/gamification.py` (10 endpoints)
- Migration: `backend/alembic/versions/b020_phase_9_6_gamification.py`

### 10.6 Community & Social Features (Phase 9.5)

**Founder Profiles:**
- Public profile page with bio, skills, interests
- Social links (Twitter, LinkedIn, GitHub)
- Connection count and public/private toggle
- "Accepting connections" flag

**Co-Founder Matching:**
- Connection requests with status tracking (pending/accepted/rejected)
- Message with connection request
- Complementary skill matching

**Idea Clubs:**
- Topic-based communities (AI SaaS, Fintech, Healthcare, etc.)
- Roles: admin, moderator, member
- Discussion posts with types: discussion, idea_share, question
- Link insights to club posts for idea sharing

**Collections & Reputation:**
- User-curated insight lists with public/private toggle
- Featured collections on explore page
- Collection followers with notification preferences
- Karma system: insight_karma, comment_karma, collection_karma
- Verified expert badges

**Backend Files:**
- Models: `social.py` (FounderProfile, FounderConnection, IdeaClub, ClubMember, ClubPost), `collection.py` (Collection, CollectionItem, CollectionFollower, UserReputation), `competitor_profile.py` (CompetitorProfile, CompetitorSnapshot)
- Migrations: `b019_phase_9_5_social.py`

### 10.7 Integration Ecosystem (Phase 10)

**External Integrations:**
- Supported services: Notion, Airtable, Slack, Discord, Linear, Jira
- OAuth token management (access_token, refresh_token, expiry)
- Workspace-level configuration
- Status tracking with sync error reporting

**Webhook System:**
- Types: new_insight, insight_update, research_complete, trending_alert
- Auto-generated webhook secrets
- Failure tracking with retry counts
- Per-integration webhook management

**Browser Extension:**
- Token-based authentication (SHA256 hashed)
- Multi-browser support (Chrome, Firefox, Edge, Safari)
- 1-year token expiry
- IP tracking for security

**Bot Subscriptions (Slack/Discord):**
- Keyword-based alerts
- Trending idea notifications
- High-score idea alerts
- Configurable frequency (instant/daily/weekly)

**Sync Operations:**
- Full and incremental sync support
- Operation logging with item counts
- Error tracking per sync attempt

**Backend Files:**
- Model: `backend/app/models/integrations.py` (ExternalIntegration, IntegrationWebhook, IntegrationSync, BrowserExtensionToken, BotSubscription)
- Routes: `backend/app/api/routes/integrations.py` (16 endpoints)
- Migration: `backend/alembic/versions/b021_phase_10_integrations.py`

---

## 11. Performance Optimizations

### 11.1 Caching Strategy

**Redis cache layers**:
1. **API response cache** (60-second TTL):
   - `/api/insights/daily-top` - Cache key: `insights:daily-top:2026-01-25`
   - `/api/users/idea-of-day` - Cache key: `idea-of-day:{user_id}`

2. **Database query cache** (5-minute TTL):
   - Trending insights, user stats

3. **Rate limit counters** (sliding window):
   - Key: `ratelimit:{tier}:{user_id}:{hour}`

### 11.2 Database Query Optimization

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

### 11.3 Frontend Optimization

**React Query caching**:
```typescript
{
  staleTime: 60000,  // 1 minute
  cacheTime: 300000, // 5 minutes
  refetchOnWindowFocus: false
}
```

**Next.js ISR** (Incremental Static Regeneration):
- `/insights/[id]` - Revalidate every 60 seconds
- Static generation for public insight pages

---

## 12. Glue Coding Architecture

**Philosophy**: Prefer integration over implementation. Use battle-tested libraries instead of custom code.

### 12.1 Key Integrations

| Feature | Library | Why Not Custom |
|---------|---------|----------------|
| Web scraping | Firecrawl SDK | AI-powered, handles JS rendering, anti-bot bypass |
| AI agents | PydanticAI | Type-safe LLM outputs, built-in validation |
| Task queue | Arq | Redis-based, async, cron support |
| Auth | Supabase Auth | JWT + RLS, managed service |
| Payments | Stripe | PCI compliance, webhook handling |
| Email | Resend | High deliverability, templates |
| Rate limiting | SlowAPI | Redis-backed, proven algorithm |

### 12.2 Custom Code (Minimal)

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

## 13. Monitoring & Error Handling

### 13.0 Sentry Observability Architecture (Production Active)

**Configuration** (`backend/app/main.py`):
```python
if settings.sentry_dsn and settings.environment in ("production", "staging"):
    sentry_sdk.init(
        dsn=settings.sentry_dsn,
        environment=settings.environment,
        release=os.environ.get("RAILWAY_GIT_COMMIT_SHA", "local"),
        traces_sample_rate=settings.sentry_traces_sample_rate,  # 0.1 prod / 1.0 staging
        enable_logs=True,
        integrations=[
            FastApiIntegration(transaction_style="url"),
            SqlalchemyIntegration(),
            LoggingIntegration(level=logging.INFO, event_level=logging.ERROR, sentry_logs_level=logging.WARNING),
        ],
        before_send=lambda event, hint: None if event.get("request", {}).get("url", "").endswith("/health") else event,
    )
```

**User Context** (`backend/app/api/deps.py`):
```python
sentry_sdk.set_user({"id": str(user.id), "email": user.email})  # after JWT verification
```

**AI Agent Spans** (`backend/app/agents/sentry_tracing.py`):
```python
@contextlib.asynccontextmanager
async def trace_agent_run(agent_name: str, model: str = "google-gla:gemini-2.0-flash"):
    with sentry_sdk.start_span(op="gen_ai.request", name=agent_name) as span:
        span.set_data("gen_ai.request.model", model)
        yield span
```
Wrapped in: `enhanced_analyzer.py`, `research_agent.py`, `market_intel_agent.py`

**Frontend** (`frontend/`):
- `instrumentation.ts` — Next.js App Router registration hook
- `sentry.client.config.ts` — `browserTracingIntegration()` + `replayIntegration(maskAllText)` + `consoleLoggingIntegration(["warn","error"])`
- `sentry.server.config.ts` — server-side traces + `enable_logs: true`
- `sentry.edge.config.ts` — middleware and edge API routes
- 3x `error.tsx` — `Sentry.captureException(error)` before `console.error`

**Sentry Projects**:
- Backend: `ascentia-km` org, backend project, DSN in `SENTRY_DSN` (Railway env var)
- Frontend: `NEXT_PUBLIC_SENTRY_DSN` (Vercel env var), `SENTRY_AUTH_TOKEN` (GitHub secret for source maps)

### 13.1 Logging Strategy

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

### 13.2 Error Handling

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

### 13.3 Key Metrics

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

## 14. Testing Strategy

### 14.1 Backend Tests (pytest)

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

### 14.2 Frontend Tests (Playwright)

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

---

## 15. Phase A-L & Q1-Q9 Feature Enhancements
**Last Updated**: 2026-02-17

### 15.1 Admin Portal (Phase A-L)

**System Settings** (`/admin/settings`)
- `system_settings` table — JSONB store for admin-configurable runtime values
- Grouped by category; GET `/api/admin/settings` returns `{ settings: { [group]: { [key]: value } } }`
- PUT `/api/admin/settings/{key}` — upsert (creates if not exists)
- Alembic revision `c003` adds the table (revision IDs must be ≤32 chars)

**Content Review workflow** (`/admin/content`)
- Approve/reject/edit AI-generated insights before publication
- Bulk moderation actions with audit trail

**Agent Management** (`/admin/agents`)
- Live status panel showing all 8 registered agents
- Enable/disable, trigger manual runs, view last-run timestamps

**Shared Admin Components**:
- `hooks/useAdminAuth.ts` — admin-only auth guard
- `components/admin/admin-page-header.tsx` — consistent admin header
- `components/admin/admin-states.tsx` — loading/error/empty states

### 15.2 Quality Improvements (Q1-Q9)

**Q1 — Live Pulse Page** (`/pulse`)
- New route: `backend/app/api/routes/pulse.py`
- SSE endpoint: `GET /api/pulse/live` — real-time market signal stream
- Frontend: streaming EventSource component with auto-reconnect

**Q2 — Founder Fits Redesign**
- Teal/amber design system replacing default gray
- Score bars (visual progress indicators) for each fit dimension
- Data fetched from existing `/api/insights/{id}` scoring fields

**Q3 — Idea of the Day Sharing**
- Copy-to-clipboard share button with formatted text
- Social meta tags (OpenGraph + Twitter Card) per idea
- Route: `/idea-of-the-day`

**Q4 — Trend Sparklines**
- Inline SVG mini-charts on `InsightCard` component
- Renders trend data from `insights.metadata.trend_data[]` (7-point array)
- Zero dependency — pure SVG path generation

**Q5 — Insight Comparison Tool**
- Side-by-side comparison of 2 insights
- Radar chart (Chart.js) overlaying both score profiles
- Comparison table: 7 scoring dimensions × 2 insights

**Q6 — Critical Bug Fixes**
- Pulse SSE endpoint: fixed connection leak on client disconnect
- Tools page: fixed broken filter state after navigation
- Contact form: fixed rate limiting bypass via header spoofing

**Q7 — SEO Overhaul**
- JSON-LD structured data on insight detail pages
- OpenGraph + Twitter Card meta on all public pages
- `sitemap.ts` generating dynamic sitemap for all published insights
- `hreflang` tags for en/ja locale variants

**Q8 — Data Quality**
- ILIKE query sanitization (escape `%` and `_` in user search input)
- Stats API validation — null-safe aggregation queries
- Insight slug backfill script (`scripts/backfill_trend_data.py`)

**Q9 — Rate Limiting**
- Per-endpoint limits via SlowAPI decorators
- Per-user limits using JWT `sub` claim as key
- Graceful degradation: 429 response with `Retry-After` header
- Config in `app/core/rate_limits.py` (active implementation)

### 15.3 API Endpoint Count Update

| Phase | Endpoints Added | Running Total |
|-------|----------------|---------------|
| Phase 1-7 | 133 | 133 |
| Phase 8-10 | 99 | 232 |
| Q1 (Pulse SSE) | 1 | 233 |
| Q6-Q9 (bugfixes/hardening) | ~2 | 235+ |

**Current total: 235+ endpoints**, 35+ route files

---

## 16. Security Architecture (Phase S, 2026-02-19)

### 16.1 HTTP Security Headers (Middleware)

**File**: `backend/app/middleware/security.py`
```
Strict-Transport-Security: max-age=31536000; includeSubDomains
Content-Security-Policy: default-src 'self'; script-src 'self' 'unsafe-inline'; ...
X-Frame-Options: DENY
X-Content-Type-Options: nosniff
Referrer-Policy: strict-origin-when-cross-origin
```

### 16.2 JWT Authentication (ES256)

**Algorithm**: ES256 (ECDSA P-256) — matches Supabase's actual JWT signing algorithm
**JWKS Endpoint**: `{SUPABASE_URL}/auth/v1/.well-known/jwks.json`
**Issuer**: `{SUPABASE_URL}/auth/v1`
**Validation**: `python-jose[cryptography]` with JWK dict keys (not shared HS256 secret)
**User Role**: from `app_metadata.role` in JWT payload

### 16.3 XSS Prevention

- `bleach` library: sanitizes all user-controlled text inputs before storage
- `markupsafe.escape()`: escapes output in HTML contexts
- Next.js: React's built-in JSX escaping; `rehype-sanitize` on markdown rendering

### 16.4 Auth Recovery Flow

1. User requests password reset → Supabase sends recovery email with token
2. Supabase redirects to `/auth/callback?type=recovery&...`
3. Frontend middleware detects recovery type → redirects to `/auth/update-password`
4. User submits new password → `supabase.auth.updateUser({ password })` → session update

### 16.5 Rate Limiting Tiers

| Endpoint | Limit | Storage |
|----------|-------|---------|
| Public API | 30/minute | Redis (prod) / memory (staging) |
| Login | 5/minute | Redis (prod) / memory (staging) |
| Signup | 3/minute | Redis (prod) / memory (staging) |
| Contact form | 5/hour | Redis (prod) / memory (staging) |

## 17. Production Deployment Architecture (Phase P, 2026-02-18)

### 17.1 Infrastructure Topology

```
GitHub (main) → CI/CD Pipeline → Railway (backend) + Vercel (frontend)
                                        ↓                    ↓
                              Supabase Pro PostgreSQL   Supabase Auth
                              Upstash Redis (TLS)       CORS: Vercel URL
                              Sentry (errors+traces)    Sentry (frontend)
```

### 17.2 Railway Configuration

- **Dockerfile**: `backend/Dockerfile` — `uv sync` + `uvicorn`
- **Start command**: `sh -c 'bash /app/start.sh'` (runs both uvicorn + arq worker)
- **Port**: `$PORT` (Railway injects 8080 — target port in domain settings must match)
- **Watch paths**: `/backend/**` triggers rebuild
- **Env vars**: Set via Railway MCP; `RAILWAY_GIT_COMMIT_SHA` auto-injected for Sentry releases

### 17.3 Vercel Configuration

- **Framework**: Next.js (auto-detected)
- **Root dir**: `frontend/`
- **Build command**: `npm run build` (Next.js 16, App Router)
- **NEXT_PUBLIC_* env vars**: Build-time — requires redeploy to take effect
- **Sentry env vars**: Set via GitHub Actions `set-vercel-sentry-env.yml` (uses `VERCEL_TOKEN_STAGING` secret)

### 17.4 CI/CD Pipeline (`.github/workflows/ci-cd.yml`)

| Job | Trigger | Action |
|-----|---------|--------|
| Security Scan | push | Trivy container scan |
| Backend Tests | push | pytest (291 tests) |
| Frontend Tests | push | ESLint + Next.js build |
| Migrate Production DB | main push | `alembic upgrade head` via Railway |
| Build Docker Image | main push | Build + push to GHCR |
| Deploy to Production | main push | Railway deploy |
| Migrate Staging DB | develop push | `alembic upgrade head` via Railway staging |
| Deploy to Staging | develop push | Railway staging + Vercel preview deploy |

---

## Conclusion

StartInsight architecture prioritizes:
1. **Simplicity**: Glue coding over custom implementation
2. **Reliability**: Battle-tested libraries (Supabase, Stripe, Firecrawl, Sentry)
3. **Scalability**: Async Python, connection pooling, Redis caching
4. **Security**: HSTS/CSP headers, JWT ES256 JWKS, RLS policies, XSS prevention
5. **Performance**: Query optimization, eager loading, ISR, p95 < 500ms target
6. **Observability**: Sentry errors + traces + logs + AI agent spans on production + staging
7. **Extensibility**: Phase 8-10 adds 43 tables and 99 endpoints for enterprise features

**Current status**: ✅ Production live (Railway + Vercel + Supabase Pro). Phase A-L + Q1-Q9 + Security + Sentry complete. Deployed 2026-02-18/19.
