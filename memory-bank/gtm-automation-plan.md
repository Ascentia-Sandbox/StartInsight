---
**Memory Bank Protocol**
**Reading Priority:** CRITICAL
**Read When:** Before any marketing, distribution, or growth work
**Dependencies:** Read active-context.md and project-brief.md first
**Purpose:** Complete GTM + GEO operational playbook — 90-day strategy for first paying customer
**Last Updated:** 2026-04-18
---

# StartInsight — Complete GTM + GEO Strategy

**Status:** ENGINEERING FREEZE (2026-04-18 → 2026-06-17). /office-hours diagnosed solution-in-search-of-problem on 2026-04-18. Wedge test + distribution sprint only, no code.
**Revenue:** $0 | Paying Customers: 0 | Traffic: ~0 external visitors

---

## 2026-04-18 PIVOT — Wedge Test + Engineering Freeze

The original operational playbook below (Week 1-2 activation, Week 2-4 monitoring, Day 30/60/90 decisions) was written on 2026-04-05 on the assumption that distribution into founder communities would surface demand. As of Day 13 (2026-04-18), zero community distribution has actually happened — and the `/office-hours` diagnostic surfaced the deeper issue: there is no specific named user, no current workflow being replaced, and the origin was "AI/tech capability looking for a use case." The plan below is still the correct 90-day scaffolding. This section adds the Week-1 wedge test that runs inside it.

**Full design doc:** `~/.gstack/projects/Ascentia-Sandbox-StartInsight/wysetime-pcc-main-design-20260418-142849.md`

### Approach A — Narrowest Wedge (Days 13-20, 2026-04-18 → 2026-04-25)

| # | Action | Target | By |
|---|--------|--------|-----|
| 1 | Identify 5 MY/SG founder Telegram groups | 5 groups | 2026-04-19 |
| 2 | Google Doc "StartInsight Wedge Test — Week 1" with 20 real names | 20 named founders | 2026-04-20 |
| 3 | First DM sent (screenshot → `memory-bank/daily-operations.md`) | 1 sent | 2026-04-20 |
| 4 | 20 personalized DMs sent | 20 sent | 2026-04-22 |
| 5 | 3 paid RM49 memo sales | 3 paid | 2026-04-25 |
| 6 | 3 memos delivered (48h SLA each) | 3 delivered | 2026-04-25 |

**Wedge offer script:** "Hey [name], I built an AI platform that ingests 6 startup-idea sources every 6h. I'll hand-write you a 3-page validated idea memo for your industry (market size, competitors, the wedge I'd pick, first-10-users plan) for RM49 cash. 48h turnaround. 3 slots this week."

**Post-delivery question (record verbatim):** "If I built a product that did this automatically for RM49/month, would you pay?"

### Approach B — 60-Day Distribution Sprint (Days 13-73, 2026-04-18 → 2026-06-17)

Zero engineering. Human work only. Daily rhythm:
- 5 community posts (value-add, not sales) — Telegram, Reddit, WhatsApp, LinkedIn
- 10 cold DMs to named founders
- 1 user interview call (30 min, free)
- Weekly: update `memory-bank/daily-operations.md` metrics table honestly

### Engineering Freeze (2026-04-18 → 2026-06-17)

- **No commits to `main`** for 60 days. Violation triggers Approach C (sunset).
- **One-time exception:** regenerate Twitter OAuth tokens at developer.x.com (Read+Write scope), update Railway `TWITTER_ACCESS_TOKEN` + `TWITTER_ACCESS_SECRET`. Must be done by 2026-04-20. No other engineering permitted.
- **Automation continues running unchanged:** scrapers (every 6h), analyzer, content generator, social posting, email nurture, digests. All autopilot.
- **If urge to code returns:** re-read office-hours design doc "What I noticed about how you think" section. `learnings.jsonl` named "engineering-avoidance-after-ship" pattern on 2026-04-04.

### Kill Criteria (strict, non-negotiable)

| Marker | Date | Trigger | Action |
|--------|------|---------|--------|
| Week 1 end | 2026-04-25 | 0 paid memos after 20 DMs | Pivot segment (max 3 pivots) |
| Week 1 end | 2026-04-25 | Fewer than 20 DMs sent | Honesty check in next /office-hours |
| Freeze Day 30 | 2026-05-18 | 0 paying + 0 `report_category_viewed` + 0 inbound DMs | Pivot B's targeting OR Approach C |
| Freeze Day 60 | 2026-06-17 | <5 paying customers total | Approach C (honest sunset). No extensions. |

### Next /office-hours — 2026-04-25

First question: "Show me the Google Sheet." Outcomes:
- 20 names + 3+ paid → design follow-on around the segment you found
- 20 names + 0 paid → design segment pivot
- Fewer than 20 names → design Approach C honestly

---

## Original 90-Day Playbook (archived 2026-04-06 → now, still the scaffolding)

---

## Context

StartInsight is a live AI-powered startup idea discovery platform (startinsight.co). 70 tables, 235+ API endpoints, 8 AI agents, 6 scrapers, 500+ insights. The product works. The engineering is done.

Between April 4-5, we shipped 54 files / 3,818 lines of GTM + GEO automation code in 4 commits. The automated marketing system is built. But zero external traffic, zero paying customers. This document is the operational playbook for the next 90 days.

**What's been built (all deployed):**
- Conviction funnel: 3 category reports at RM49 with Stripe checkout, now linked in nav/footer/sitemap
- PostHog instrumentation: report_category_viewed, report_checkout_started, report_checkout_error events
- Social posting agent: auto-posts to Twitter/X (3/day) from content generator output
- Email nurture: Day 1/3/7/14 drip sequence for newsletter subscribers
- 12 programmatic SEO pages: /explore/{category} with ISR, ItemList + FAQPage JSON-LD
- RSS feed: /api/feed/rss with 12 insights + 8 articles
- GEO: llms.txt, AI crawler robots.txt rules, structured data on all content pages, answer-first paragraphs, FAQ sections, GEO-optimized content generator prompts
- Embeddable widget API: /api/widgets/trending (CORS: *)
- Referral incentives: 3-tier rewards (1=free report, 3=founder badge, 5=all reports)
- Google Search Console verification meta tag (pending verification + sitemap submission)

---

## The Strategy: Three Engines

StartInsight's GTM is three self-reinforcing engines. All three run on autopilot once activated. The founder's job is to (1) activate each engine, (2) monitor metrics weekly, and (3) make pivot decisions at day 30/60/90.

```
ENGINE 1: CONTENT + DISTRIBUTION (already automated)
  Scrapers (6 sources, every 6h)
    -> AI analysis (8 agents, every 6h)
    -> Content generator (every 3 days)
    -> Social posts to Twitter/X (2x daily)
    -> Email nurture to subscribers (daily)
    -> Weekly digest (Monday 9am UTC)
    -> Market articles (every 3 days)

ENGINE 2: SEO + GEO (already deployed, needs time to index)
  12 explore pages (ISR, hourly revalidation)
    -> JSON-LD structured data (ItemList, FAQPage, Dataset, Blog)
    -> llms.txt (AI site map)
    -> robots.txt (GPTBot, ClaudeBot, PerplexityBot allowed)
    -> RSS feed (auto-updated)
    -> Sitemap with 35+ pages (submitted to GSC)
    -> Answer-first content + FAQ sections
    -> GEO-optimized content generator prompts

ENGINE 3: CONVERSION FUNNEL (built, needs traffic)
  Visitor -> Browse free insights -> Newsletter signup
    -> Nurture sequence (Day 1/3/7/14)
    -> Category report teaser -> RM49 checkout
    -> Referral program (1/3/5 tier rewards)
    -> Pro subscription ($19/mo) -> API tier ($49/mo)
```

---

## How SEO and GEO Work Together

SEO and GEO are not competing strategies. They feed each other.

```
TRADITIONAL SEO                    GEO (Generative Engine Optimization)
------                             ------
Target: Google Search              Target: ChatGPT, Perplexity, Gemini, Claude
Goal: Rank in search results       Goal: Get CITED in AI-generated answers
Metric: Impressions, clicks, CTR   Metric: AI mentions, citation frequency
Content: Keyword-optimized         Content: Answer-first, structured, attributed
Timeline: 3-6 months for results   Timeline: 2-8 weeks for AI index
What wins: Backlinks + authority   What wins: Freshness + structured data + corroboration
```

**StartInsight's unique advantages for both:**

| Advantage | SEO Impact | GEO Impact |
|-----------|-----------|-----------|
| New content every 6 hours | Fresh sitemap signals | 50% of AI citations are <13 weeks old |
| 12 explore category pages | Long-tail keyword clusters | 86% of AI citations come from 5+ interconnected pages |
| 8-dimension structured scores | Rich snippets potential | AI models love structured, citable data |
| Multi-source attribution | E-E-A-T signals (Experience) | Multi-source corroboration = higher AI confidence |
| 500+ insight pages | Massive content surface area | More pages = more chances to be cited |
| Market articles every 3 days | Content velocity | Freshness beats authority in AI citation |

**The flywheel:**
1. Content generator creates GEO-optimized articles with source attribution
2. Social posting agent creates external mentions (Twitter/X) for corroboration
3. AI models crawl llms.txt, read structured pages, extract answers, cite StartInsight
4. AI-referred visitors land on explore/insight pages, newsletter signup, nurture, conversion
5. Google indexes the same pages, organic search traffic compounds
6. More users, more signals, better content, more citations

---

## 90-Day Operational Playbook

### WEEK 1-2: Activate (Founder Work)

Everything below is manual founder work. No engineering needed.

| # | Action | Time | Status |
|---|--------|------|--------|
| 1 | **Google Search Console:** Verify property using HTML tag method, submit sitemap.xml | 10 min | Pending |
| 2 | **Railway:** Set `ENABLE_SOCIAL_POSTING=true` | 1 min | Pending |
| 3 | **Railway:** Verify Twitter creds are set (TWITTER_API_KEY, TWITTER_API_SECRET, TWITTER_ACCESS_TOKEN, TWITTER_ACCESS_SECRET) | 5 min | Pending |
| 4 | **Cloudflare:** Security, Bots, ensure AI crawlers (GPTBot, ClaudeBot) NOT blocked | 5 min | Pending |
| 5 | **Verify llms.txt:** `curl https://startinsight.co/llms.txt` should return markdown | 1 min | Pending |
| 6 | **Verify RSS:** `curl https://api.startinsight.co/api/feed/rss` should return XML | 1 min | Pending |
| 7 | **Telegram:** Share startinsight.co/explore/fintech-startup-ideas in 5 MY/SG founder groups | 1 hr | Pending |
| 8 | **WhatsApp:** Share weekly report link in 3 founder groups | 30 min | Pending |
| 9 | **Reddit:** Post value-add content in r/startups, r/SaaS linking to explore pages (1-2 posts) | 1 hr | Pending |
| 10 | **Test conviction funnel:** Visit /reports/fintech-malaysia, check PostHog fires `report_category_viewed` | 5 min | Pending |

### WEEK 2-4: Monitor + Push Distribution

| # | Action | Frequency | What to Check |
|---|--------|-----------|---------------|
| 11 | Check PostHog events | Weekly | report_category_viewed, report_checkout_started counts |
| 12 | Check social_posts table | Weekly | `SELECT status, count(*) FROM social_posts GROUP BY status` |
| 13 | Check newsletter subscribers | Weekly | `SELECT count(*) FROM newsletter_subscribers WHERE confirmed=true` |
| 14 | Check Google Search Console | Weekly | Impressions, clicks, indexed pages |
| 15 | Post in Telegram/WhatsApp | 2x per week | Share explore pages + market insight articles |
| 16 | Test AI citation | Weekly | Ask Perplexity "best startup ideas Malaysia 2026" -- does it cite startinsight.co? |
| 17 | Check report_requests | Weekly | Any rows = someone interacted with the funnel |

### DAY 30: First Decision Point

```
CHECK: PostHog + report_requests + social_posts + GSC impressions
       |
 +-----+----------------------+----------------------+
 |     |                      |                      |
 0 views       views > 0,      any checkout          AI citation
 on reports    0 checkouts     attempt               found
 |             |               |                      |
 DISTRIBUTION  CONVERSION      DEMAND                 GEO
 FAILURE       FAILURE         SIGNAL                 WORKING
 |             |               |                      |
 Actions:      Actions:        Actions:               Actions:
 - More        - A/B price     - Double down          - Create more
   community     (RM29 vs 49)    on winning             explore pages
   posts       - Rewrite         channel             - Expand
 - Try           copy/CTA     - Add more               categories
   ProductHunt - Different       categories           - Write articles
   launch        category     - Push Pro               targeting cited
 - Direct DMs    reports        subscription           queries
   (10 more)   |               |                      |
 |             If still 0      If 3+ checkouts:       If cited by
 If still 0    after 200       consider raising        2+ AI engines:
 after 200     views:          price to RM99           double content
 views:        |                                       velocity
 PIVOT to      PIVOT to
 Approach C    Approach C
 (manual DMs,  (manual DMs)
 RM49 cash)
```

### DAY 60: Scale or Pivot

| Signal | Action |
|--------|--------|
| **>5 checkouts, >0 paid** | Scale: add 3 more category reports, push Pro subscription, consider ProductHunt |
| **>100 GSC impressions, growing** | SEO working: add more explore pages, expand keyword coverage |
| **AI citation found** | GEO working: create more structured content, expand FAQ sections, write AI-query-targeted articles |
| **Social posts getting engagement** | Channel works: increase post frequency, add hashtag strategy |
| **Email nurture >20% open rate** | Nurture works: extend sequence (Day 21, 30), add case study emails |
| **Zero across everything** | Pivot: Approach C (manual founder outreach, cash payments, validate demand person-to-person) |

### DAY 90: Revenue Target

| Metric | Target | Source |
|--------|--------|--------|
| Monthly recurring revenue | > RM500 | Stripe dashboard |
| Total signups | > 100 | users table |
| Newsletter subscribers | > 50 confirmed | newsletter_subscribers table |
| GSC impressions | > 2,000 | Google Search Console |
| AI citations | >= 3 confirmed | Manual checks on Perplexity/ChatGPT |
| Social media followers | > 100 (Twitter) | Twitter analytics |
| Explore page organic traffic | > 500 pageviews | PostHog |

---

## What Runs on Autopilot (No Founder Action)

| System | Schedule | What Happens |
|--------|----------|--------------|
| 6 scrapers | Every 6h | Collect 150+ signals from Reddit, PH, Google Trends, Twitter/X, HN |
| Enhanced analyzer | Every 6h | Score signals across 8 dimensions, create insights |
| Content generator | Every 3 days | Generate blog posts + social posts, persist to social_posts table |
| Social posting agent | 10am + 4pm UTC daily | Post pending content to Twitter/X (3/day max) |
| Market insight publisher | Every 3 days | Auto-generate 1500-2500 word market article, quality review, publish |
| Email nurture | Daily 10am UTC | Send drip emails (Day 1/3/7/14) to new subscribers |
| Daily digest | Daily 9am UTC | Top insights to opted-in users |
| Weekly digest | Monday 9am UTC | Weekly roundup to all subscribers |
| SEO pages | ISR (hourly) | 12 explore pages auto-refresh with latest insights |
| RSS feed | On request | Always fresh (queries DB on each request, 1h cache) |
| GEO (llms.txt) | Static | AI models read on crawl, update when site structure changes |

**The founder's only recurring work:** weekly community posts (Telegram/Reddit), checking metrics, responding to customers.

---

## GEO Technical Details (What's Deployed)

### llms.txt (startinsight.co/llms.txt)
- AI site map per llmstxt.org spec
- Lists all content sections, explore categories, API endpoints, paid reports
- 50+ linked resources for AI models to understand site structure
- Updated: when site structure changes (static file)

### robots.txt AI Crawler Rules
- GPTBot: explicit Allow for all public content, Disallow for admin/dashboard
- ClaudeBot: full Allow with private page exclusions
- PerplexityBot: full Allow with private page exclusions
- Google-Extended: full Allow
- Public API paths unblocked: /api/feed/rss, /api/explore/, /api/widgets/

### JSON-LD Structured Data
| Page Type | Schema | What AI Extracts |
|-----------|--------|------------------|
| Insights layout | Dataset | 8-dimension scoring dimensions, temporal coverage |
| Market insights layout | Blog | Article metadata, publisher info |
| Explore pages | ItemList + FAQPage | Ranked idea list + Q&A pairs for direct citation |
| Pricing | FAQPage | Pricing questions and answers |
| About | Organization | Company entity info |
| Category reports | Article | Report metadata, publisher |

### Answer-First Content (GEO)
- Every explore page starts with a direct-answer paragraph in the first 200 words
- Format: "The top {category} in {year}, based on real-time analysis of {sources}, include {top ideas}..."
- Research: 44.2% of ChatGPT citations come from the first 30% of a page

### FAQ Sections (GEO)
- 3 FAQs per explore page matching exact AI queries:
  1. "What are the best {category} in {year}?"
  2. "How are these ideas validated?"
  3. "How often is this data updated?"
- Each answer is 2-3 sentences with specific data points

### Content Generator GEO Prompts
- Content generator agent now includes GEO rules in system prompt
- Answer-first structure, 2-3 data tables per article
- Source attribution: "According to Reddit...", "Google Trends data shows..."
- Specific numbers over vague claims

---

## Monthly Cost

| Service | Cost | Notes |
|---------|------|-------|
| Supabase Pro | $25 | Database + auth |
| Gemini API | ~$8 | Analysis + content generation + social posts |
| Railway | Free | Backend + Redis (within 500h/mo) |
| Vercel | Free | Frontend hosting |
| Resend | Free | ~250 emails/mo within 3K free tier |
| Twitter API | Free | Basic write access with OAuth 1.0a |
| PostHog | Free | <1M events/mo |
| **Total** | **~$33/mo** | |

---

## Key URLs

| URL | Purpose | Status |
|-----|---------|--------|
| startinsight.co | Homepage | Live |
| startinsight.co/insights | Idea database | Live |
| startinsight.co/explore/{category} | 12 programmatic SEO pages | Live |
| startinsight.co/reports/fintech-malaysia | Conviction funnel (RM49) | Live |
| startinsight.co/market-insights | AI-generated articles | Live |
| startinsight.co/llms.txt | AI model site map | Live |
| api.startinsight.co/api/feed/rss | RSS feed | Live |
| api.startinsight.co/api/widgets/trending | Embeddable widget | Live |
| api.startinsight.co/api/explore/categories | Category listing | Live |
| api.startinsight.co/docs | Swagger API docs | Live |

---

## Pending Manual Actions (Founder Checklist)

- [ ] Verify GSC property (HTML tag method) + submit sitemap.xml
- [ ] Set ENABLE_SOCIAL_POSTING=true in Railway
- [ ] Verify Twitter creds in Railway env vars
- [ ] Check Cloudflare AI bot blocking settings
- [ ] Verify llms.txt accessible: `curl startinsight.co/llms.txt`
- [ ] Share explore pages in 5 Telegram/WhatsApp groups
- [ ] Post 1-2 value-add posts on Reddit r/startups
- [ ] Test conviction funnel: visit /reports/fintech-malaysia, check PostHog
- [ ] ProductHunt launch preparation (when ready)

---

## Kill Criteria

| Condition | Threshold | Action |
|-----------|-----------|--------|
| Zero report page views | 0 views after 2 weeks of distribution | Push harder on community, try ProductHunt |
| Views but zero checkouts | 100+ views, 0 checkouts | A/B test price (RM29 vs RM49), rewrite copy |
| Zero AI citations at day 60 | Not cited by any AI engine | Expand structured content, add more FAQ pages |
| Zero signups at day 30 | 0 new users | Distribution channels are wrong, try different communities |
| Social posts zero engagement | 50+ posts, 0 interactions | Revise content style, change hashtags, adjust posting times |
| Email nurture <5% open rate | After 50+ sends | Revise subject lines, change send time |

**Ultimate pivot trigger:** If 0 checkout attempts after 200+ teaser views across all 3 categories, pivot to Approach C (manual DM outreach, RM49 cash payments, 1:1 founder conversations).

---

## NOT Building (Deferred)

| Item | Why Deferred | Trigger to Reconsider |
|------|-------------|----------------------|
| New features | Product is complete for validation | First 10 paying customers |
| Startup Failure Cemetery | SEO asset, not needed for first customer | After 100 signups |
| B2B Accelerator Dashboard | Needs supply side (100 founders) | After 100 founder signups |
| Mobile app | Web-first | After 1K monthly active users |
| LinkedIn posting | Deferred per founder decision | When LinkedIn audience identified |
| More category reports | Validate existing 3 first | After first RM49 payment |
| Test coverage expansion | 47% is fine for validation | Before Series A |

---

**Last Updated:** 2026-04-18 (pivot added)
