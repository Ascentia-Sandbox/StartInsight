---
**Memory Bank Protocol**
**Reading Priority:** HIGH
**Read When:** Daily check-in, monitoring, or when troubleshooting GTM systems
**Dependencies:** Read gtm-automation-plan.md for strategy context
**Purpose:** Daily operations checklist, health check commands, and troubleshooting guide
**Last Updated:** 2026-04-18
---

# Daily Operations Checklist

## Status: ENGINEERING FREEZE — WEDGE TEST WEEK (2026-04-18)
## Day Count: 13 of 90 (original 90-day plan: 2026-04-06 → 2026-07-05; Day 30 = 2026-05-06, Day 60 = 2026-06-05, Day 90 = 2026-07-05)
## Freeze Calendar: 2026-04-18 (Day 0) → 2026-06-17 (Day 60); wedge test Week 1 ends 2026-04-25; next /office-hours on 2026-04-25

## /office-hours Diagnostic Update (2026-04-18)

**Diagnosis:** Solution in search of a problem. No specific user, no current workflow replaced, tech-first origin. Pivot to user discovery.

**Approach A (Days 14-20):** 7-day wedge test — 20 DMs → 3 RM49 memo sales → 1 named human.
**Approach B (Days 14-60):** Zero-engineering distribution sprint — 5 community posts/day + 10 cold DMs/day + 1 user interview/day.

**Engineering freeze:** 2026-04-18 → 2026-06-17. No commits to main. Violation triggers Approach C.

**The assignment (by Sunday 2026-04-20):**
1. Regenerate Twitter OAuth tokens at developer.x.com (Read+Write), update Railway env. ~15 min.
2. Google Doc "StartInsight Wedge Test — Week 1" with 20 real MY/SG founder names.
3. Send first DM. Screenshot as evidence below.

## Wedge Test Tracker (Week 1: 2026-04-18 → 2026-04-25)

| Founder | Segment | DM sent | Replied | Paid (RM49) | Delivered | NPS | Notes |
|---------|---------|---------|---------|-------------|-----------|-----|-------|
| _pending_ | | | | | | | Fill in 20 rows here. If you can't fill 20 names, that's Data Point 1. |

**Wedge offer script (reference):**
> "Hey [name], I built an AI platform that ingests 6 startup-idea sources every 6h. I'll hand-write you a 3-page validated idea memo for your industry (market size, competitors, the wedge I'd pick, first-10-users plan) for RM49 cash. 48h turnaround. 3 slots this week. Want one?"

**Kill criteria Week 1:**
- 3+ paid → design follow-on around THAT segment on 2026-04-25
- 0 paid, 20 DMs sent → pivot segment, not product
- Fewer than 20 DMs sent → honesty check in next /office-hours

---

---

## Quick Health Check (run these commands)

```bash
# === Full system health check (copy-paste into terminal) ===

echo "=== 1. BACKEND HEALTH ===" && \
curl -s https://api.startinsight.co/health/ready | python3 -c "import json,sys; print(json.dumps(json.load(sys.stdin), indent=2))" 2>/dev/null && \

echo "\n=== 2. SITEMAP ===" && \
curl -s https://startinsight.co/sitemap.xml | python3 -c "
import sys
from xml.etree.ElementTree import fromstring
root = fromstring(sys.stdin.read())
ns = {'s': 'http://www.sitemaps.org/schemas/sitemap/0.9'}
urls = root.findall('.//s:url', ns) or root.findall('.//url')
print(f'{len(urls)} URLs in sitemap')
" 2>/dev/null && \

echo "\n=== 3. RSS FEED ===" && \
curl -s https://api.startinsight.co/api/feed/rss | python3 -c "
import sys
from xml.etree.ElementTree import fromstring
root = fromstring(sys.stdin.read())
items = root.findall('.//item')
print(f'{len(items)} items in RSS')
if items:
    latest = items[0].find('title').text
    date = items[0].find('pubDate').text
    print(f'Latest: {latest[:60]}')
    print(f'Date: {date}')
" 2>/dev/null && \

echo "\n=== 4. EXPLORE PAGES ===" && \
curl -s https://api.startinsight.co/api/explore/categories | python3 -c "
import json,sys
cats = json.load(sys.stdin)
print(f'{len(cats)} categories')
" 2>/dev/null && \

echo "\n=== 5. GEO ===" && \
curl -s -o /dev/null -w '%{http_code}' https://startinsight.co/llms.txt && echo " llms.txt" && \
curl -s -o /dev/null -w '%{http_code}' https://startinsight.co/robots.txt && echo " robots.txt" && \

echo "\n=== 6. WIDGET API ===" && \
curl -s https://api.startinsight.co/api/widgets/trending | python3 -c "
import json,sys
d = json.load(sys.stdin)
print(f'{len(d.get(\"ideas\",[]))} trending ideas')
" 2>/dev/null

echo "\n=== HEALTH CHECK COMPLETE ==="
```

---

## Daily Checklist

### Check 1: PostHog Events
**What:** Are users visiting the site? Are conviction funnel events firing?
**How:** Log in to us.posthog.com > Events > filter last 24h
**Look for:**
- `$pageview` events (any traffic at all?)
- `report_category_viewed` (someone found the category reports?)
- `report_checkout_started` (someone clicked checkout?)
- `newsletter_signup` (someone subscribed?)
**Action if zero:** Normal for first week. Push distribution harder (Telegram/Reddit).

### Check 2: Social Posts (Twitter/X)
**What:** Is the social posting agent creating and publishing tweets?
**How:** Check your Twitter/X profile — are automated posts appearing?
**Look for:**
- Posts about startup ideas with #startup #SaaS hashtags
- Posts linking to startinsight.co/insights/{slug}
- 2-3 posts per day (10am + 4pm UTC schedule)
**Action if zero posts:**
1. Check Railway logs for `post_social_content_task` errors
2. Verify ENABLE_SOCIAL_POSTING=true is set
3. Verify Twitter creds are valid (test with: `curl -s https://api.startinsight.co/health`)
4. Check if content generator has run: Railway logs for `run_content_generator_auto_task`
5. The content generator must run first (every 3 days) to create pending social posts

### Check 3: Newsletter Subscribers
**What:** Are people signing up for the newsletter?
**How:** DB query via Railway console or admin API
```sql
SELECT count(*) as total,
       count(*) FILTER (WHERE confirmed = true) as confirmed,
       count(*) FILTER (WHERE unsubscribed_at IS NOT NULL) as unsubscribed,
       max(created_at) as latest_signup
FROM newsletter_subscribers;
```
**Look for:** Any growth in confirmed subscribers
**Action if zero:** Newsletter form exists on homepage footer, explore pages, and report pages. Traffic is the bottleneck, not the form.

### Check 4: Google Search Console
**What:** Is Google indexing the site? Are there impressions?
**How:** Log in to search.google.com/search-console > Performance
**Look for:**
- Total impressions (takes 2-3 days to start showing)
- Total clicks
- Indexed pages count (Coverage > Valid)
- Any crawl errors
**Action if no data:** Normal for first 3-5 days after sitemap submission. GSC takes time to process.

### Check 5: AI Citation Test (GEO)
**What:** Are AI models citing StartInsight?
**How:** Ask these queries on Perplexity (perplexity.ai):
- "best startup ideas Malaysia 2026"
- "AI SaaS startup opportunities"
- "fintech market gaps Southeast Asia"
**Look for:** Any mention or citation of startinsight.co
**Action if not cited:** Normal for first 2-4 weeks. AI indexing takes time. The llms.txt and structured data are working in the background.

---

## Troubleshooting Guide

### Social posts not appearing on Twitter
```
Possible causes:
1. ENABLE_SOCIAL_POSTING not set to true → check Railway env vars
2. Twitter Access Token generated with read-only scope → MUST regenerate after changing app permissions
   Fix: developer.x.com → App Settings → Read+Write → Keys & Tokens → Regenerate Access Token + Secret
   Then update Railway: TWITTER_ACCESS_TOKEN + TWITTER_ACCESS_SECRET
3. Twitter creds invalid/expired → test by checking Railway worker logs
4. Content generator hasn't run yet → runs every 3 days, check scheduler
5. social_posts table empty → content generator creates pending posts
6. Rate limit hit → max 3 tweets/day, check social_posts table for "failed" status

Debug: Check Railway logs for "post_social_content_task" or "social_posting"
Note (2026-04-12): OAuth 1.0a Access Token scope is baked at generation time.
Changing app permissions does NOT retroactively update existing tokens — always regenerate.
```

### Email nurture not sending
```
Possible causes:
1. No confirmed subscribers → check newsletter_subscribers table
2. Resend API key invalid → check RESEND_API_KEY in Railway
3. Nurture task not running → check Railway logs for "run_email_nurture_task"

Debug: Check Railway logs for "email_nurture" or "nurture"
```

### Explore pages showing empty/404
```
Possible causes:
1. Backend API down → check health endpoint
2. No insights match category keywords → check /api/explore/{slug} directly
3. Insights have low scores → explore pages filter relevance_score >= 0.5

Debug: curl https://api.startinsight.co/api/explore/ai-saas-ideas
```

### RSS feed returning 500
```
Fixed 2026-04-05: Was filtering by non-existent "status" column.
Now filters by published_at IS NOT NULL.
If 500 recurs: check MarketInsight model for schema changes.
```

---

## Automated Systems Reference

| System | Schedule | What It Does | Where to Check |
|--------|----------|-------------|----------------|
| Scrapers | Every 6h (00/06/12/18 UTC) | Collect 150+ signals from 6 sources | Railway logs: `scrape_all_sources_task` |
| Analyzer | Every 6h (:30 past) | Score signals, create insights | Railway logs: `analyze_signals_task` |
| Content generator | Every 3 days | Create blog + social posts | Railway logs: `run_content_generator_auto_task` |
| Social posting | 10am + 4pm UTC daily | Post pending tweets | Railway logs: `post_social_content_task` |
| Market articles | Every 3 days (Wed 6am) | Auto-generate market analysis | Railway logs: `market_insight_publisher_task` |
| Email nurture | Daily 10am UTC | Send drip emails (Day 1/3/7/14) | Railway logs: `run_email_nurture_task` |
| Daily digest | Daily 9am UTC | Top insights to opted-in users | Railway logs: `send_daily_digests_task` |
| Weekly digest | Monday 9am UTC | Weekly roundup | Railway logs: `send_weekly_digest_task` |
| Quality audit | Every 6h (+1h) | Insight quality review | Railway logs: `insight_quality_audit_task` |

---

## Daily Log Template

Use this template to log daily observations:

```
### [DATE] Daily Check
- PostHog events (24h): pageviews=__, report_views=__, checkouts=__
- Social posts: tweets_today=__, engagement=__
- Newsletter: total_confirmed=__, new_today=__
- GSC: impressions=__, clicks=__, indexed=__
- AI citation: [not yet / found on Perplexity / found on ChatGPT]
- Issues: [none / describe]
- Action taken: [none / describe]
```

---

## Key Metrics Dashboard

Track these numbers daily. The trend matters more than the absolute number.

| Metric | Day 1 (Apr 6) | Day 5 (Apr 11) | Day 6 (Apr 12) | Day 14 | Day 30 Target |
|--------|---------------|----------------|----------------|--------|---------------|
| Total insights | 1,845 | 2,085 (+240) | ~2,085 | | growing |
| Market articles | ~170 | 180 published | ~180 | | growing |
| PostHog pageviews (24h) | 0 | ~0 external | ~0 | | > 10 |
| report_category_viewed | 0 | 0 | 0 | | > 50 |
| report_checkout_started | 0 | 0 | 0 | | > 0 |
| Newsletter subscribers | 0 | 1 confirmed | 1 confirmed | | > 20 |
| Social posts created | 0 | 20 (10 tw + 10 li) | 20 | | > 30 |
| Social posts POSTED | 0 | 0 (all failed) | 0 (fix pending) | | > 30 |
| New user signups | 0 | 0 | 0 | | > 10 |
| GSC impressions | 0 | pending | check manually | | > 500 |
| AI citations | 0 | pending | pending | | >= 1 |
| Revenue (RM) | 0 | 0 | 0 | | > 0 |
| Sentry errors (24h) | — | 0 | 0 ✅ (live confirmed) | | 0 |

### Day 6 Review Notes (2026-04-12)
- **Sentry:** 0 unresolved issues confirmed via live MCP query (both backend + frontend projects clean).
- **Twitter fix in progress:** X Premium $5 purchased. Root cause confirmed: Access Token was generated under read-only scope. Must regenerate tokens after enabling Read+Write in developer.x.com. Railway env vars need update (TWITTER_ACCESS_TOKEN + TWITTER_ACCESS_SECRET).
- **GSC:** Could not check headlessly (AppArmor sandbox). Check manually at search.google.com/search-console. Expect near-zero data at Day 6 — normal.
- **Distribution still zero:** No Telegram/Reddit/WhatsApp posts done. This remains the primary bottleneck for traffic.
- **Next action:** Fix Twitter first, then push manual distribution (Telegram/Reddit/WhatsApp).

### Day 13 Review Notes (2026-04-18) — /office-hours Pivot
- **Diagnostic run:** /office-hours session produced the uncomfortable-but-correct answer. Founder admitted (1) no specific user, (2) no current workflow being replaced, (3) tech-first origin, (4) cannot conceive of product without the platform. Textbook solution-in-search-of-a-problem.
- **Accepted premises:** engineering is done, $33/mo burn is cheap, attention is the scarce resource, no named user exists.
- **Pushed back with reasoning:** distribution hasn't actually been tested manually; GSC + AI-citation windows aren't open yet at Day 6. Earned the 60-day test.
- **Pivot chosen:** Approach A + B in parallel — 7-day RM49 wedge test + 60-day distribution sprint, zero engineering.
- **Twitter still pending:** token regen is Day 0 of the pivot (permitted engineering exception). Must happen by Sunday 2026-04-20.
- **The real bottleneck:** named human. Not traffic, not SEO, not content velocity. One human who will pay RM49 and quote their name in next session.
- **Design doc:** `~/.gstack/projects/Ascentia-Sandbox-StartInsight/wysetime-pcc-main-design-20260418-142849.md`
- **Next action:** Send the first DM before end of Sunday 2026-04-20. Screenshot as evidence in this file.

---

**Last Updated:** 2026-04-18
