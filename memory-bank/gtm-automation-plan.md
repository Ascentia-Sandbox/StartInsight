---
**Memory Bank Protocol**
**Reading Priority:** CRITICAL
**Read When:** Before any marketing, distribution, or growth work
**Dependencies:** Read active-context.md and project-brief.md first
**Purpose:** Automated go-to-market system — PLG + GEO (Generative Engine Optimization)
**Last Updated:** 2026-04-04 (revised with Phase 5: GEO)
---

# Automated GTM System: Product-Led Marketing + GEO Plan

## Status: Phase 1-4 COMPLETE | Phase 5 (GEO) READY TO IMPLEMENT
## Revenue: $0 | Paying Customers: 0 | Product: Complete + GTM Automated

---

## The Problem (as of 2026-04-04)

StartInsight has a world-class content generation machine that produces 150+ signals/day, auto-generates blog articles every 3 days, creates social media posts, and has a full conviction funnel at RM49. But:

1. **Conviction funnel is INVISIBLE** — category report pages not linked in navigation, sitemap, or any internal page
2. **Zero PostHog tracking** on conviction funnel — kill criteria unmeasurable
3. **Content generator output goes NOWHERE** — social posts created but never published
4. **Daily email digest DISABLED** — set `enable_daily_digest: False` in config
5. **No social media posting** — Twitter scraper is READ-ONLY, no LinkedIn integration
6. **No email nurture sequence** — only a welcome email on signup
7. **No programmatic SEO** — only 3 hardcoded category pages
8. **No RSS feed** — missing standard distribution channel
9. **Referral program has no incentive** — tracking exists, no reward

---

## What Already Exists (Leverage, Don't Rebuild)

| Component | File | Status | Automation Gap |
|-----------|------|--------|----------------|
| Content Generator Agent | `backend/app/agents/content_generator_agent.py` | Built, scheduled every 3 days | Output not persisted or distributed |
| Market Insight Publisher | `backend/app/agents/market_insight_publisher.py` | ACTIVE — articles every 3 days | Working, auto-publishes to /market-insights |
| Email Service | `backend/app/services/email_service.py` | 12 templates, Resend integration | Daily digest disabled, no nurture |
| Newsletter | `backend/app/api/routes/newsletter.py` | Double opt-in working | No growth loop, no content cadence |
| Twitter Credentials | `backend/app/core/config.py:96-100` | OAuth 1.0a creds configured | Read-only scraper, no posting |
| Webhook System | `backend/app/api/routes/integrations.py` | Slack/Discord webhooks built | Not marketed to users |
| Public API | 40+ endpoints, no auth required | Live, cached, rate-limited | No developer marketing |
| Referral Program | `backend/app/api/routes/referrals.py` | Code gen + tracking working | No incentive defined |
| Notification Service | `backend/app/services/notification_service.py` | Triggers on new insights | Only for webhook subscribers |
| Conviction Funnel | `frontend/app/[locale]/reports/[category]/*` | 3 pages, Stripe, PDF delivery | Not linked anywhere |
| OG Images | `frontend/app/opengraph-image.tsx` | Dynamic 1200x630 generation | Working |
| Sitemap/SEO | `frontend/app/sitemap.ts`, `robots.txt` | 21 static + dynamic pages | Missing category pages, no RSS |
| PostHog | `frontend/lib/analytics.ts` | 12 events tracked | Missing funnel events |
| Scheduler | `backend/app/tasks/scheduler.py` | APScheduler with 10+ jobs | Has slots for new tasks |

---

## The 4-Phase Automated GTM System

### PHASE 1: Fix & Instrument (Week 1-2)
**Goal:** Make the conviction funnel findable and measurable
**Engineering: ~1 hour CC time | Founder: ~2 hours manual work**

| # | Task | File(s) | Type | Time |
|---|------|---------|------|------|
| 1.1 | Add "Category Reports" to mega-menu navigation | `frontend/components/navigation/mega-menu.tsx` | Code | 5 min |
| 1.2 | Add "Category Reports" to footer links | `frontend/components/Footer.tsx` | Code | 5 min |
| 1.3 | Add 3 category URLs to sitemap.ts | `frontend/app/sitemap.ts` | Code | 10 min |
| 1.4 | Create ReportAnalytics client component for PostHog | `frontend/app/[locale]/reports/[category]/ReportAnalytics.tsx` (NEW) | Code | 15 min |
| 1.5 | Add PostHog events to ReportCheckoutButton | `frontend/app/[locale]/reports/[category]/ReportCheckoutButton.tsx` | Code | 10 min |
| 1.6 | Add new events to analytics.ts Events object | `frontend/lib/analytics.ts` | Code | 5 min |
| 1.7 | Set ENABLE_DAILY_DIGEST=true in Railway env | Railway dashboard | Config | 5 min |
| 1.8 | Verify weekly digest is sending (trigger manually) | Admin API or Arq CLI | Verify | 30 min |
| 1.9 | Query newsletter subscriber count | DB query | Verify | 5 min |
| 1.10 | Submit sitemap.xml to Google Search Console | Google Search Console | Manual | 10 min |
| 1.11 | Share fintech-malaysia link in 5 Telegram groups | Telegram | Distribution | 1 hr |
| 1.12 | DM 10 MY/SG founders with category report link | WhatsApp/Telegram | Distribution | 2 hrs |

**New PostHog Events:**
```
report_category_viewed    — fires on category page load
report_checkout_started   — fires on "Unlock Full Report" click
newsletter_signup_report  — fires on newsletter signup from report page
```

**Kill Criteria:** If after 2 weeks: zero report page views in PostHog AND zero newsletter signups from report pages, reassess conviction funnel product-market fit.

---

### PHASE 2: Automated Content Distribution (Week 2-4)
**Goal:** Auto-distribute content to Twitter/X, LinkedIn, and email
**Engineering: ~5 hours CC time**

#### 2.1 Social Posting Agent (NEW)

**New file:** `backend/app/agents/social_posting_agent.py`

Architecture:
```
content_generator_agent (every 3 days)
    → generates social posts (Twitter 280 chars, LinkedIn 500-1300 chars)
    → saves to social_posts table (NEW, status="pending")
    
social_posting_agent (twice daily, 10am/4pm UTC)
    → reads pending social_posts
    → posts to Twitter/X via Tweepy v2 Client.create_tweet()
    → posts to LinkedIn via Marketing API (or Make.com webhook)
    → updates status to "posted" with external_post_id
    → rate limit: max 3 tweets/day, 2 LinkedIn posts/day
```

**New files:**
| File | Purpose |
|------|---------|
| `backend/app/agents/social_posting_agent.py` | Twitter/LinkedIn posting agent |
| `backend/app/models/social_post.py` | Social post tracking model |
| `backend/alembic/versions/c018_create_social_posts.py` | Migration |

**New model: `social_posts` table**
```
id (UUID PK)
insight_id (FK → insights, nullable)
platform ("twitter" | "linkedin")
content (text)
hashtags (JSONB)
link_url (text, nullable — insight/report page URL with UTM)
external_post_id (text, nullable — tweet ID or LinkedIn URN)
status ("pending" | "posted" | "failed")
posted_at (timestamptz)
engagement_metrics (JSONB — likes, retweets, impressions)
created_at (timestamptz)
```

**New scheduler job:**
```python
# Social posting: 10:00 and 16:00 UTC (MY 6pm and midnight)
CronTrigger(hour="10,16", minute=0)
```

**Config additions (Railway env vars):**
```
LINKEDIN_ACCESS_TOKEN=...       # LinkedIn Marketing API
LINKEDIN_COMPANY_ID=...         # Company page ID
TWITTER_DAILY_POST_LIMIT=3
LINKEDIN_DAILY_POST_LIMIT=2
```

**Twitter posting** uses existing OAuth 1.0a creds (`twitter_api_key`, `twitter_api_secret`, `twitter_access_token`, `twitter_access_secret` already in config.py).

**LinkedIn alternative:** If LinkedIn API setup is too complex, use Make.com free tier (1,000 ops/mo) with a webhook trigger. Social posting agent calls the webhook URL instead of LinkedIn API directly.

#### 2.2 Wire Content Generator Output

**File:** `backend/app/worker.py` — modify `run_content_generator_auto_task`

After `generate_all_content()` returns social posts, persist them as `SocialPost` records with `status="pending"`. The social posting agent picks them up on next run.

#### 2.3 Email Nurture Sequence (NEW)

**New file:** `backend/app/tasks/email_nurture.py`

Sequence for newsletter subscribers:
| Day | Email | Content | CTA |
|-----|-------|---------|-----|
| 0 | Welcome | Already exists (`newsletter_welcome`) | Browse insights |
| 1 | Top 5 This Week | Reuse weekly digest template, top 5 | View full analysis |
| 3 | How StartInsight Works | Platform tour highlights | Try the validate tool |
| 7 | Your Category Report | Teaser of fintech-malaysia insights | Unlock for RM49 |
| 14 | Founder Stories | Success stories + social proof | Share with a friend |
| 14+ | Weekly digest | Auto (already scheduled Monday 09:00 UTC) | Ongoing engagement |

**New scheduler job:**
```python
# Email nurture: daily at 10:00 UTC
CronTrigger(hour=10, minute=0)
```

Logic: query `newsletter_subscribers` where `confirmed=true`, calculate `days_since_confirmed`, check dedup, send appropriate template.

**New column on `newsletter_subscribers`:**
```
nurture_stage (int, default 0) — tracks which nurture email was last sent
```

**Email quota impact:** ~250 emails/mo total (well within Resend 3K free tier)

**Kill Criteria:**
- Social posting: if zero clicks from Twitter/LinkedIn after 2 weeks of posting (UTM tracking in PostHog), pause and revise content quality
- Email nurture: if open rate < 10% after 50 sends, revise subject lines and timing

---

### PHASE 3: Programmatic SEO (Week 4-6)
**Goal:** Auto-generate SEO landing pages for every insight category
**Engineering: ~4 hours CC time**

#### 3.1 Category Exploration Pages

**New route:** `frontend/app/[locale]/explore/[category]/page.tsx`

Server component that:
1. Fetches insights filtered by topic/keyword from new API endpoint
2. Renders SEO-optimized page:
   - H1: "[Category] Startup Ideas & Market Gaps — 2026"
   - Meta description: dynamically generated
   - JSON-LD: `CollectionPage` schema
   - 10-20 insight cards with expandable snippets
   - Internal links to related categories
   - Newsletter signup CTA
   - Link to paid report if available
3. ISR with 1-hour revalidation

**New backend endpoint:** `GET /api/insights/by-topic/{topic_slug}`
```python
@router.get("/api/insights/by-topic/{topic_slug}")
async def get_insights_by_topic(topic_slug: str, limit: int = 20):
    """Return insights matching a topic for programmatic SEO pages."""
```

**Seed categories (expand over time):**
```python
SEO_CATEGORIES = {
    "ai-saas-ideas": {"title": "AI SaaS Startup Ideas", "keywords": ["AI", "SaaS", "machine learning"]},
    "fintech-startup-ideas": {"title": "Fintech Startup Ideas", "keywords": ["fintech", "payment", "banking"]},
    "devtools-opportunities": {"title": "Developer Tools Opportunities", "keywords": ["developer", "API"]},
    "health-tech-ideas": {"title": "Health Tech Startup Ideas", "keywords": ["health", "medical", "wellness"]},
    "ecommerce-gaps": {"title": "E-Commerce Market Gaps", "keywords": ["ecommerce", "retail", "marketplace"]},
    "edtech-opportunities": {"title": "EdTech Startup Ideas", "keywords": ["education", "learning", "course"]},
    "remote-work-tools": {"title": "Remote Work Tool Ideas", "keywords": ["remote", "collaboration", "productivity"]},
    "sustainability-startups": {"title": "Sustainability Startup Ideas", "keywords": ["green", "sustainability", "climate"]},
    # Add MY/SG specific:
    "malaysia-startup-ideas": {"title": "Malaysia Startup Ideas", "keywords": ["Malaysia", "KL", "MY"]},
    "singapore-startup-ideas": {"title": "Singapore Startup Ideas", "keywords": ["Singapore", "SG"]},
}
```

**Sitemap:** Add dynamic explore pages to `sitemap.ts` by fetching categories from new `/api/seo/categories` endpoint.

#### 3.2 RSS Feed

**New file:** `backend/app/api/routes/rss.py`
```python
@router.get("/api/feed/rss", response_class=Response)
async def rss_feed(db: AsyncSession = Depends(get_db)):
    """RSS 2.0 feed of latest 20 insights + market insight articles."""
```

Standard RSS 2.0 XML. Add `<link rel="alternate" type="application/rss+xml">` to frontend layout.

#### 3.3 Internal Linking

- Add "Related Insights" section to insight detail pages
- Add cross-links from market insight articles to relevant explore pages
- Add "Explore More Categories" links on category report pages

**Kill Criteria:** After 4 weeks, if programmatic SEO pages receive < 100 organic impressions (Google Search Console), stop expanding and focus on top 3 performing.

---

### PHASE 4: Community & API Distribution (Week 6-8)
**Goal:** Activate network effects and external distribution
**Engineering: ~2 hours CC time | Founder: ~4 hours manual work**

#### 4.1 ProductHunt Launch
- Create ProductHunt maker profile
- Prepare assets: tagline, description, first comment, screenshots
- Use existing OG image generator for launch images
- Schedule for Tuesday (highest traffic)
- Hook: "AI-powered startup idea discovery with 8-dimension scoring"

#### 4.2 Developer API Activation
- Add quick-start code examples to `/api-docs` page (curl, Python, JS)
- Add "Get API Key" CTA linking to `/api-keys`
- Create embeddable widget endpoint: `GET /api/widgets/trending-ideas`
  - Returns top 5 trending ideas as JSON or HTML snippet
  - CORS: allow all origins for widget endpoint

#### 4.3 Referral Activation with Incentives

**Tiers (zero-cost to implement):**
| Referrals | Reward |
|-----------|--------|
| 1 | Unlock 1 free category report (normally RM49) |
| 3 | "Founder" badge + priority feature access |
| 5 | All 3 category reports free |

**New component:** `frontend/components/ReferralWidget.tsx`
- Referral link with copy button
- Progress bar toward next tier
- Share buttons: Twitter, LinkedIn, WhatsApp, Copy Link
- Show in dashboard sidebar + settings page

#### 4.4 Reddit/Community Seeding (Manual, Weekly)
- Post value-add content in r/startups, r/SaaS, r/Entrepreneur, r/smallbusiness
- Share market insight articles in relevant HN threads
- Join 5-10 MY/SG founder Telegram groups and share weekly report

**Kill Criteria:**
- ProductHunt: < 50 upvotes and < 20 signups → deprioritize launch marketing
- API: < 5 key registrations in 2 weeks → deprioritize developer audience
- Referral: < 3 referrals in 4 weeks → simplify to basic "share" button

---

## Complete Distribution Architecture

```
┌─────────────────────────────────────────────────────────┐
│                    CONTENT GENERATION                    │
│                                                         │
│  6 Scrapers (every 6h) → 150+ raw signals/day          │
│       ↓                                                 │
│  Enhanced Analyzer → 8-dimension scored insights        │
│       ↓                                                 │
│  Content Generator Agent (every 3 days):                │
│    → Blog posts (auto-published to /market-insights)    │
│    → Social posts (→ social_posts table → posting agent)│
│    → SEO recommendations                                │
│       ↓                                                 │
│  Market Insight Publisher (every 3 days):                │
│    → 1500-2500 word articles → quality review → publish │
└─────────────────────────────────────────────────────────┘
                         ↓
┌─────────────────────────────────────────────────────────┐
│                    DISTRIBUTION CHANNELS                 │
│                                                         │
│  1. SEO (Automated)                                     │
│     - 20+ public pages (existing)                       │
│     - Programmatic /explore/[category] pages (Phase 3)  │
│     - Market insight articles (auto, every 3 days)      │
│     - RSS feed (Phase 3)                                │
│     - Sitemap + JSON-LD (existing + fixes)              │
│                                                         │
│  2. Social Media (Automated)                            │
│     - Twitter/X: 3 tweets/day (Phase 2)                 │
│     - LinkedIn: 2 posts/day (Phase 2)                   │
│     - OG images for sharing (existing)                  │
│                                                         │
│  3. Email (Automated)                                   │
│     - Daily digest (re-enable, Phase 1)                 │
│     - Weekly digest (existing, Monday 09:00 UTC)        │
│     - Nurture sequence: Day 0/1/3/7/14 (Phase 2)       │
│     - Weekly PDF with UTM links (existing)              │
│                                                         │
│  4. Community (Semi-automated)                          │
│     - Telegram/WhatsApp groups (founder, weekly)        │
│     - Reddit/HN posts (founder, weekly)                 │
│     - ProductHunt launch (one-time, Phase 4)            │
│                                                         │
│  5. Developer/API (Automated)                           │
│     - Public API (40+ endpoints, existing)              │
│     - Embeddable widget (Phase 4)                       │
│     - API docs + quick-start (Phase 4)                  │
│     - Webhook subscriptions (existing)                  │
│                                                         │
│  6. Referral (Automated)                                │
│     - Referral codes + tracking (existing)              │
│     - Incentive tiers (Phase 4)                         │
│     - Share widget (Phase 4)                            │
└─────────────────────────────────────────────────────────┘
                         ↓
┌─────────────────────────────────────────────────────────┐
│                    CONVERSION FUNNEL                     │
│                                                         │
│  Visitor → Browse free insights → Newsletter signup     │
│    ↓ (nurture sequence)                                 │
│  Subscriber → Category report teaser → RM49 checkout    │
│    ↓ (conviction)                                       │
│  Customer → Pro subscription ($19/mo) → API tier ($49)  │
└─────────────────────────────────────────────────────────┘
```

---

## New Database Tables

| Table | Migration | Phase | Columns |
|-------|-----------|-------|---------|
| `social_posts` | c018 | 2 | id, insight_id, platform, content, hashtags, link_url, external_post_id, status, posted_at, engagement_metrics, created_at |

**Column additions:**
| Table | Column | Phase |
|-------|--------|-------|
| `newsletter_subscribers` | `nurture_stage` (int, default 0) | 2 |

---

## New Scheduler Tasks

| Task | Cron | Phase |
|------|------|-------|
| `post_social_content_task` | `0 10,16 * * *` (10am/4pm UTC) | 2 |
| `run_email_nurture_task` | `0 10 * * *` (daily 10am UTC) | 2 |

**Already scheduled (verify working):**
| Task | Cron | Status |
|------|------|--------|
| `run_content_generator_auto_task` | Every 3 days | Scheduled, output not persisted |
| `send_weekly_digest_task` | Monday 09:00 UTC | Scheduled, needs subscriber verification |
| `send_daily_digests_task` | Daily 09:00 UTC | Scheduled but DISABLED by config |

---

## New Files to Create

| File | Phase | Purpose |
|------|-------|---------|
| `backend/app/agents/social_posting_agent.py` | 2 | Twitter/LinkedIn posting |
| `backend/app/models/social_post.py` | 2 | Social post tracking model |
| `backend/alembic/versions/c018_create_social_posts.py` | 2 | Migration |
| `backend/app/tasks/email_nurture.py` | 2 | Email nurture sequence logic |
| `frontend/app/[locale]/reports/[category]/ReportAnalytics.tsx` | 1 | PostHog tracking for category pages |
| `frontend/app/[locale]/explore/[category]/page.tsx` | 3 | Programmatic SEO template |
| `backend/app/services/seo_categories.py` | 3 | SEO category definitions |
| `backend/app/api/routes/rss.py` | 3 | RSS 2.0 feed |
| `frontend/components/ReferralWidget.tsx` | 4 | Referral sharing component |
| `backend/app/api/routes/public_widgets.py` | 4 | Embeddable widget endpoint |

---

## Existing Files to Modify

| File | Phase | Change |
|------|-------|--------|
| `frontend/components/navigation/mega-menu.tsx` | 1 | Add "Category Reports" link |
| `frontend/components/Footer.tsx` | 1 | Add "Category Reports" link |
| `frontend/app/sitemap.ts` | 1, 3 | Add category URLs, explore pages |
| `frontend/lib/analytics.ts` | 1 | Add conviction funnel events |
| `frontend/app/[locale]/reports/[category]/page.tsx` | 1 | Import ReportAnalytics component |
| `frontend/app/[locale]/reports/[category]/ReportCheckoutButton.tsx` | 1 | Add PostHog events |
| `backend/app/worker.py` | 2 | Wire content generator → social_posts table |
| `backend/app/tasks/scheduler.py` | 2 | Add social posting + nurture jobs |
| `backend/app/core/config.py` | 2 | Add LinkedIn + social posting config |
| `backend/app/main.py` | 3 | Register RSS route |
| `frontend/app/[locale]/layout.tsx` | 3 | Add RSS link tag |

---

## Effort Summary

| Phase | CC Time | Founder Time | Calendar |
|-------|---------|-------------|----------|
| Phase 1: Fix & Instrument | ~1 hr | ~3 hrs (distribution) | Week 1-2 |
| Phase 2: Content Distribution | ~5 hrs | ~1 hr (LinkedIn setup) | Week 2-4 |
| Phase 3: Programmatic SEO | ~4 hrs | ~1 hr (GSC monitoring) | Week 4-6 |
| Phase 4: Community & API | ~2 hrs | ~4 hrs (ProductHunt, Reddit) | Week 6-8 |
| **Total** | **~12 hrs** | **~9 hrs** | **8 weeks** |

---

## Monthly Cost Impact

| Service | Current | After GTM | Notes |
|---------|---------|-----------|-------|
| Supabase Pro | $25 | $25 | No change |
| Gemini API | ~$5 | ~$8 | Social content generation |
| Railway | Free | Free | Within 500h/mo |
| Resend | Free | Free | ~250 emails/mo within 3K |
| Twitter API | Free | Free | Basic write access with OAuth 1.0a |
| LinkedIn | Free | Free | Marketing API free tier or Make.com free |
| **Total** | **~$30** | **~$33** | Negligible increase |

---

## PHASE 5: Generative Engine Optimization (GEO)

### Why GEO Matters More Than SEO for StartInsight

Traditional SEO gets you into Google search results. GEO gets you **cited by AI** when someone asks ChatGPT, Perplexity, Gemini, or Claude: "What are the best startup ideas in fintech?" or "What AI SaaS opportunities exist in Malaysia?"

The numbers are staggering:
- AI-referred sessions grew **527% YoY** in early 2025
- **50% of AI-cited content** is less than 13 weeks old (StartInsight publishes every 3 days)
- **86% of citations** come from sites with 5+ interconnected pages on a topic (we have 12 explore pages + insights + articles)
- Overlap between Google top links and AI citations has dropped below **20%** — GEO is a separate game

StartInsight is uniquely positioned because:
1. **Structured data IS the product** — 8-dimension scored insights with source attribution
2. **Freshness advantage** — new content every 6 hours, articles every 3 days
3. **Multi-source corroboration** — insights cite Reddit, PH, Google Trends, HN, Twitter
4. **Pillar-cluster architecture** — 12 explore pages + 500+ insight pages + articles

### Current GEO Gaps (Critical)

| Gap | Impact | Fix |
|-----|--------|-----|
| **No llms.txt** | AI models can't efficiently understand site structure | Create `/llms.txt` + `/llms-full.txt` |
| **robots.txt blocks /api/** | RSS feed + explore API invisible to crawlers | Allow `/api/feed/rss` + `/api/explore/` |
| **No AI crawler directives** | GPTBot, ClaudeBot, PerplexityBot not explicitly allowed | Add named crawler rules |
| **Cloudflare may block AI bots** | Cloudflare default changed to block AI crawlers | Check and whitelist |
| **No JSON-LD on insight pages** | AI can't parse structured insight data | Add Dataset + Review schema |
| **No JSON-LD on market insights** | Articles not structured for AI extraction | Add Article + BlogPosting schema |
| **Explore pages missing /explore/ in robots.txt** | 12 SEO pages not explicitly allowed | Add Allow: /explore/ |
| **No answer-first content** | AI prefers direct answers in first 200 words | Restructure page content |
| **No FAQ schema on explore pages** | Missing FAQPage markup that AI loves | Add FAQ sections |
| **Sitemap uses `new Date()`** | No real freshness signals | Use actual DB timestamps |

---

### Phase 5.1: AI Access Layer (CRITICAL — Day 1)

**Goal:** Make StartInsight's content accessible and parseable by AI crawlers.

#### 5.1A: Create llms.txt

**New file:** `frontend/public/llms.txt`

```markdown
# StartInsight

> AI-powered startup idea discovery platform. 8-dimension scoring from 6 real-time data sources (Reddit, Product Hunt, Google Trends, Twitter/X, Hacker News, Firecrawl). 500+ validated startup opportunities updated every 6 hours.

## Startup Ideas Database
- [Browse All Ideas](https://startinsight.co/insights): 500+ AI-scored startup ideas with problem statements, solutions, market sizing
- [Idea of the Day](https://startinsight.co/idea-of-the-day): Daily featured opportunity
- [Founder Fits](https://startinsight.co/founder-fits): Ideas scored for solo founders

## Explore by Category
- [AI SaaS Ideas](https://startinsight.co/explore/ai-saas-ideas): AI and SaaS opportunities
- [Fintech Ideas](https://startinsight.co/explore/fintech-startup-ideas): Payment, banking, lending gaps
- [Developer Tools](https://startinsight.co/explore/devtools-opportunities): API, SDK, infrastructure
- [Health Tech](https://startinsight.co/explore/health-tech-ideas): Telemedicine, wellness, digital health
- [E-Commerce](https://startinsight.co/explore/ecommerce-gaps): Marketplace and D2C opportunities
- [Malaysia Startups](https://startinsight.co/explore/malaysia-startup-ideas): MY-specific opportunities
- [Singapore Startups](https://startinsight.co/explore/singapore-startup-ideas): SG-specific opportunities

## Market Research
- [Market Insights](https://startinsight.co/market-insights): AI-generated market analysis articles (published every 3 days)
- [Trends](https://startinsight.co/trends): 180+ trending keywords with volume and growth data
- [Market Pulse](https://startinsight.co/pulse): Real-time signal feed

## Category Reports (Paid)
- [Fintech Malaysia Report](https://startinsight.co/reports/fintech-malaysia): RM49 deep-dive
- [F&B Malaysia Report](https://startinsight.co/reports/fnb-malaysia): RM49 deep-dive
- [Logistics Singapore Report](https://startinsight.co/reports/logistics-singapore): RM49 deep-dive

## About
- [Platform Tour](https://startinsight.co/platform-tour): How the platform works
- [Pricing](https://startinsight.co/pricing): Free tier + Pro ($19/mo) + API ($49/mo)
- [API Documentation](https://startinsight.co/api-docs): 40+ public endpoints
- [Success Stories](https://startinsight.co/success-stories): Founder case studies
- [RSS Feed](https://startinsight.co/api/feed/rss): Latest insights + articles

## API
- [Public API](https://api.startinsight.co/docs): Swagger documentation for 235+ endpoints
- [Trending Widget](https://api.startinsight.co/api/widgets/trending): Embeddable top 5 ideas (JSON, CORS: *)
- [Explore Categories](https://api.startinsight.co/api/explore/categories): Category listing
```

#### 5.1B: Update robots.txt for AI crawlers

**File:** `frontend/public/robots.txt`

Add explicit AI crawler rules + allow public API paths:

```
# AI Crawler Access (GEO — Generative Engine Optimization)
User-agent: GPTBot
Allow: /
Disallow: /dashboard/
Disallow: /workspace/
Disallow: /settings/
Disallow: /billing/
Disallow: /admin/

User-agent: ClaudeBot
Allow: /

User-agent: PerplexityBot
Allow: /

User-agent: Google-Extended
Allow: /

# Allow public API endpoints for AI crawlers
Allow: /api/feed/rss
Allow: /api/explore/
Allow: /api/widgets/
Allow: /explore/
Allow: /reports/
```

#### 5.1C: Check Cloudflare AI bot settings

**Manual action:** In Cloudflare dashboard → Security → Bots → ensure "AI Crawlers" are NOT blocked. Cloudflare recently changed default to block AI bots.

---

### Phase 5.2: Structured Data for AI (HIGH — Day 1-2)

**Goal:** Add rich JSON-LD markup so AI models can parse and cite StartInsight data.

#### 5.2A: JSON-LD on insight detail pages

**File:** `frontend/app/[locale]/insights/[slug]/page.tsx`

Add `Dataset` + `Article` schema:
```json
{
  "@context": "https://schema.org",
  "@type": ["Article", "Dataset"],
  "headline": "{title}",
  "description": "{problem_statement}",
  "datePublished": "{created_at}",
  "dateModified": "{updated_at}",
  "author": {"@type": "Organization", "name": "StartInsight"},
  "publisher": {"@type": "Organization", "name": "StartInsight", "url": "https://startinsight.co"},
  "about": {
    "@type": "CreativeWork",
    "name": "{title}",
    "description": "{proposed_solution}"
  },
  "variableMeasured": [
    {"@type": "PropertyValue", "name": "Opportunity Score", "value": "{opportunity_score}/10"},
    {"@type": "PropertyValue", "name": "Relevance Score", "value": "{relevance_score}"},
    {"@type": "PropertyValue", "name": "Market Size", "value": "{market_size_estimate}"},
    {"@type": "PropertyValue", "name": "Revenue Potential", "value": "{revenue_potential}"}
  ]
}
```

#### 5.2B: JSON-LD on market insight articles

**File:** `frontend/app/[locale]/market-insights/[slug]/page.tsx`

Add `BlogPosting` schema with `dateModified` for freshness.

#### 5.2C: ItemList schema on explore pages

**File:** `frontend/app/[locale]/explore/[category]/page.tsx`

Add `ItemList` + `FAQPage` schema:
```json
{
  "@context": "https://schema.org",
  "@type": "ItemList",
  "name": "{category_title} — {year}",
  "numberOfItems": "{count}",
  "itemListElement": [
    {"@type": "ListItem", "position": 1, "name": "{title}", "url": "{link}"}
  ]
}
```

Plus FAQ section with 3-5 common questions per category (e.g., "What are the best {category} startup ideas in 2026?").

---

### Phase 5.3: Content Structure for AI Citation (MEDIUM — Day 2-3)

**Goal:** Restructure content so AI models extract and cite it.

Key research findings:
- **44.2% of ChatGPT citations** come from the first 30% of a page
- **First 200 words** must directly answer the implied query
- Short paragraphs (2-3 sentences max)
- Tables > prose for comparison data

#### 5.3A: Answer-first explore pages

Each explore page should start with a direct answer paragraph:

> "The top {category} startup ideas in 2026, based on real-time analysis of Reddit, Product Hunt, and Google Trends data, include [top 3 ideas]. These opportunities are scored across 8 dimensions including market size, timing, and founder fit."

This goes ABOVE the insight cards, in the first visible section.

#### 5.3B: FAQ sections on explore pages

Add 3-5 FAQs per category at the bottom of each explore page:
- "What are the best {category} startup ideas in 2026?"
- "How are these {category} ideas validated?"
- "What data sources are used for {category} analysis?"

These match the exact queries people ask AI assistants.

#### 5.3C: Statistics and attribution in content

Market insight articles should include:
- Specific numbers ("Reddit discussions about X grew 340% in Q1 2026")
- Source attribution ("According to Google Trends data...")
- Tables for comparison data
- "Data shows..." and "Analysis reveals..." language

#### 5.3D: Update content generator agent prompts

**File:** `backend/app/agents/content_generator_agent.py`

Add to system prompt:
- "Start every blog post with a direct answer to the implied question in the first 200 words"
- "Include 2-3 data tables per article"
- "Cite specific sources: Reddit, Product Hunt, Google Trends"
- "Use 'data shows', 'analysis reveals', 'according to' phrasing"

---

### Phase 5.4: Freshness Signals (MEDIUM — Day 2)

**Goal:** Signal content freshness to AI crawlers.

#### 5.4A: Real timestamps in sitemap

**File:** `frontend/app/sitemap.ts`

Replace `new Date()` with actual `lastModified` timestamps from the API. Insights use `updated_at`, articles use `published_at`.

#### 5.4B: dateModified in JSON-LD

Every page with JSON-LD should include `dateModified` from actual DB timestamp.

#### 5.4C: Quarterly content refresh automation

**New scheduler task:** `refresh_top_content_task` — runs monthly, re-generates summaries for top 20 insights. This resets the "freshness clock" for AI citation decay (content >13 weeks old loses citations).

---

### Phase 5.5: Multi-Platform GEO Stacking (ONGOING)

**Goal:** Build citations across multiple platforms for corroboration.

Research shows AI engines use multi-source corroboration. If StartInsight is mentioned on Reddit, Twitter, ProductHunt, AND its own site, AI assigns higher confidence.

Strategy:
- Social posting agent (Phase 2) posts to Twitter/LinkedIn → creates external mentions
- ProductHunt launch (Phase 4) → creates review platform presence
- Reddit/HN community posts → creates discussion platform presence
- Each external mention reinforces AI confidence in citing startinsight.co

This is **already built** via Phase 2-4. The GEO stacking happens naturally when the social posting agent runs.

---

### GEO Implementation Priority

| # | Task | Files | CC Time | Impact |
|---|------|-------|---------|--------|
| 5.1A | Create llms.txt | `frontend/public/llms.txt` | 15 min | CRITICAL — AI site map |
| 5.1B | Update robots.txt for AI crawlers | `frontend/public/robots.txt` | 10 min | CRITICAL — unblock AI bots |
| 5.2A | JSON-LD on insight pages | `frontend/app/[locale]/insights/[slug]/page.tsx` | 30 min | HIGH — structured insight data |
| 5.2B | JSON-LD on market insight articles | `frontend/app/[locale]/market-insights/[slug]/page.tsx` | 20 min | HIGH — article citations |
| 5.2C | ItemList + FAQ on explore pages | `frontend/app/[locale]/explore/[category]/page.tsx` | 30 min | HIGH — category citations |
| 5.3A | Answer-first content on explore pages | `frontend/app/[locale]/explore/[category]/page.tsx` | 20 min | HIGH — first 200 words |
| 5.3D | Update content generator prompts | `backend/app/agents/content_generator_agent.py` | 15 min | MEDIUM — ongoing citation optimization |
| 5.4A | Real timestamps in sitemap | `frontend/app/sitemap.ts` | 20 min | MEDIUM — freshness signals |
| 5.1C | Check Cloudflare AI bot settings | Cloudflare dashboard | 5 min | CRITICAL — manual check |
| **Total** | | | **~3 hrs** | |

---

### GEO Success Metrics

| Metric | Target | Timeframe | How to Measure |
|--------|--------|-----------|----------------|
| llms.txt accessible | 200 OK | Day 1 | `curl startinsight.co/llms.txt` |
| AI crawlers in server logs | GPTBot, ClaudeBot hits | Week 1 | Railway logs |
| Perplexity citation | >= 1 mention | Month 1 | Search "startup ideas Malaysia" on Perplexity |
| ChatGPT citation | >= 1 mention | Month 2 | Ask ChatGPT about startup ideas |
| AI-referred traffic in PostHog | > 0 sessions from ai.* referrers | Month 1 | PostHog referrer filter |
| Explore page impressions | > 500 in GSC | Month 2 | Google Search Console |

---

### The GEO Flywheel

```
Content Generator (every 3 days)
    → New insights + articles with answer-first structure
    → JSON-LD structured data on every page
    → llms.txt maps the content for AI models
    ↓
Social Posting Agent (2x daily)
    → External mentions on Twitter/LinkedIn
    → Multi-source corroboration for AI confidence
    ↓
AI Crawlers (GPTBot, ClaudeBot, PerplexityBot)
    → Read llms.txt → understand site structure
    → Read structured pages → extract cited answers
    → Read RSS feed → discover fresh content
    ↓
AI Citations in ChatGPT/Perplexity/Gemini responses
    → "According to StartInsight, the top fintech ideas in Malaysia..."
    → Free, high-intent traffic from AI-native users
    → Higher conversion (AI users have higher purchase intent)
    ↓
More users → More signals → Better content → More citations
```

---

## 30/60/90 Day Success Metrics

### Day 30 (end of Phase 2)
| Metric | Target | Source |
|--------|--------|--------|
| Category page views | > 50 | PostHog |
| Checkout attempts | > 0 | report_requests table |
| Newsletter subscribers | > 20 | newsletter_subscribers table |
| Twitter followers | > 50 | Twitter analytics |
| Social post impressions | > 1000 | social_posts engagement_metrics |

### Day 60 (end of Phase 3)
| Metric | Target | Source |
|--------|--------|--------|
| Organic search impressions | > 500 | Google Search Console |
| SEO page views | > 200 | PostHog |
| First paying customer | >= 1 | Stripe |
| Email nurture open rate | > 20% | Resend analytics |
| RSS subscribers | > 5 | Server logs |

### Day 90 (end of Phase 4)
| Metric | Target | Source |
|--------|--------|--------|
| Monthly recurring revenue | > RM200 | Stripe |
| ProductHunt upvotes | > 100 | ProductHunt |
| API key registrations | > 10 | api_keys table |
| Referral conversions | > 5 | referrals table |
| Total signups | > 100 | users table |

---

## Decision Tree at Day 30

```
CHECK PostHog + report_requests + newsletter_subscribers
       │
 ┌─────┼───────────────────┐───────────────────┐
 │     │                   │                   │
 0 views    views > 0,     any checkout       paying
 │          0 checkouts    │                  customer
 │          │              │                  │
 DISTRIB    CONVERSION     SIGNAL             REVENUE
 FAILURE    FAILURE        EXISTS             │
 │          │              │                  Scale up:
 Push       A/B price      Double down        more categories
 harder     (RM29 vs 49)   on winning         Pro subscription
 │          Rewrite copy   channel            push
 │          │              │                  │
 If still   If still 0     Build Phase 3+4    Consider
 0 after    after 200      faster             B2B accelerator
 200 views: views:         │                  dashboard
 │          │              │
 PIVOT      PIVOT          Phase 2 → 3 → 4
 Approach C Approach C     continue
 (manual)   (manual)
```

---

## Key Principle: Automate Distribution, Not Just Generation

The existing system generates content on autopilot. The missing piece is automated DISTRIBUTION. Each phase adds a new automated distribution channel:

| Phase | Channel Added | Automation Level |
|-------|--------------|------------------|
| 1 | Navigation + PostHog | Permanent (one-time fix) |
| 2 | Twitter/X + LinkedIn + Email Nurture | Fully automated (scheduler) |
| 3 | SEO Pages + RSS | Fully automated (ISR + scheduler) |
| 4 | ProductHunt + API + Referral | Semi-automated (launch once, then passive) |

After Phase 4, the system runs on autopilot:
- Scrapers collect signals every 6h
- Analyzer produces insights every 6h
- Content generator creates social posts every 3 days
- Social posting agent publishes to Twitter/LinkedIn twice daily
- Market insight publisher creates blog posts every 3 days
- Email nurture sends to new subscribers daily
- Weekly digest sends every Monday
- SEO pages auto-update via ISR
- RSS feed updates automatically
- Referral rewards activate on triggers

**The founder's only manual work:** weekly community seeding (Telegram/Reddit/HN), checking metrics, and responding to paying customers.

---

**Last Updated:** 2026-04-04
**Status:** READY TO IMPLEMENT — Start with Phase 1 immediately
