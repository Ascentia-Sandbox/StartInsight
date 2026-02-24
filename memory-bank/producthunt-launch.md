# ProductHunt Launch Plan — StartInsight

**Target date:** Tuesday or Wednesday (peak upvote days, aim for 12:01 AM PT)
**Tagline:** *"AI finds startup ideas before the market catches on"*
**Category:** Artificial Intelligence, Productivity

---

## Pre-Launch Checklist

### Account Setup (Do once)
- [ ] Create/verify ProductHunt maker account for founder
- [ ] Follow 20+ active hunters to build credibility
- [ ] Engage with 5+ products in the week before launch (genuine comments)
- [ ] Connect Twitter/X to ProductHunt profile

### Assets to Prepare

| Asset | Spec | Notes |
|-------|------|-------|
| Logo | 240×240 PNG | Use `icon.svg` exported at 240px, teal bg |
| Thumbnail | 630×400 PNG | OG image cropped, or new "product shot" |
| Gallery images | 1270×760 PNG × 5 | See list below |
| Demo video | 60s MP4 or GIF | Screen recording with voiceover |

**5 Gallery Screenshots (in order):**
1. **Dashboard** — Insights feed with teal score bars, radar chart preview, amber badges
2. **Insight Detail** — Full 8-dimension radar, problem/solution columns, evidence section
3. **Pulse Page** — Real-time signal counter, live SSE feed, source breakdown
4. **Insight Comparison** — Side-by-side 2-insight radar + table
5. **Validate Tool** — Hero gradient, free tier badge, form submit → results

### Copy

**Tagline (60 chars max):**
> AI finds startup ideas before the market catches on

**Description (260 chars):**
> StartInsight scans Reddit, Product Hunt, Hacker News & Google Trends every 6 hours. 8-dimension AI scoring surfaces the ideas with real traction — not random brainstorming. Free to start. No credit card.

**First Comment (post immediately after launch — boosts algorithm):**
```
Hey PH! 👋 We built StartInsight because we were tired of startup ideas that sound great but have no real market signal.

Every 6 hours our AI scrapes Reddit complaints, trending searches, and product launches — then scores each idea across 8 dimensions: market size, competition, timing, technical feasibility, monetisation and more.

What makes it different from IdeaBrowser or other tools:
→ Real signals, not LLM hallucinations
→ 8-dimension radar chart (they do 4)
→ Pulse page: live real-time signal stream
→ Side-by-side idea comparison
→ Public API with 232 endpoints
→ 50–70% cheaper than alternatives

Free tier gets you 5 ideas/month. No credit card needed.

Happy to answer any questions about the tech stack (FastAPI + Gemini 2.0 Flash + Next.js) or the signal pipeline 🙏
```

### FAQ Prep (anticipate these)

| Question | Answer |
|----------|--------|
| How is this different from IdeaBrowser? | Real-time signals every 6h, 8-dimension scoring vs 4, Pulse live stream, public API, 50-70% lower pricing |
| Is the data real or AI-generated? | Data is scraped from Reddit/PH/HN/Google Trends. AI scores and analyzes — not invents |
| What's the free tier? | 5 idea generations/month, basic scoring, no card required |
| Self-hostable? | Not currently, but public API available with API keys |
| What LLM? | Gemini 2.0 Flash (cost-efficient) with Claude fallback for quality review |
| GDPR compliant? | Yes — data deletion, export, privacy controls in settings |

---

## Launch Day Playbook

### 48h Before
- [ ] Notify your network (email list, Twitter, LinkedIn, Slack communities)
- [ ] Message 20+ connections asking for upvotes **on launch day** (not before)
- [ ] Prepare 10 personalised DMs for high-follower PH hunters to reshare
- [ ] Schedule Twitter/X thread to post at 12:05 AM PT

### At Launch (12:01 AM PT)
- [ ] Submit product on ProductHunt
- [ ] Post first comment immediately (copy above)
- [ ] Share on Twitter/X, LinkedIn, relevant Slack/Discord communities
- [ ] Post in IndieHackers, r/SideProject, r/startups

### During the Day
- [ ] Reply to every comment within 30 minutes
- [ ] Post progress update tweets ("We're #X on PH today!")
- [ ] Ask 5 early users to leave honest reviews
- [ ] Monitor Sentry for any traffic-induced errors

### Metrics to Track
- ProductHunt rank (target: top 5 of the day)
- Unique visitors to startinsight.co (Vercel Analytics)
- Signups in Supabase Auth dashboard
- New Sentry errors

---

## Post-Launch (48h After)
- [ ] Post "we launched" recap on Twitter/LinkedIn
- [ ] Reply to any remaining PH comments
- [ ] Email new signups with a personal welcome note
- [ ] Check Supabase Auth for signup spike
- [ ] Analyse which traffic source converted best (PostHog funnel)

---

## Success Targets

| Metric | Minimum | Stretch |
|--------|---------|---------|
| Upvotes | 100 | 300+ |
| PH rank | Top 10 | Top 5 |
| Site visitors | 500 | 2,000+ |
| Signups | 50 | 200+ |
| Paying conversions (D+7) | 2 | 10 |

---

*Last updated: 2026-02-22*
