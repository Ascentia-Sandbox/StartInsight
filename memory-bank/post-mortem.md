---
**Memory Bank Protocol**
**Reading Priority:** REFERENCE
**Read When:** After a project ends, before starting a new project, or whenever the engineering-avoidance-after-ship pattern feels familiar
**Dependencies:** project-brief.md (what was built), gtm-automation-plan.md (what was attempted), active-context.md (the freeze + sprint), `~/.gstack/projects/Ascentia-Sandbox-StartInsight/wysetime-pcc-main-design-20260418-142849.md` (the diagnosis)
**Purpose:** Honest cause-of-death record for StartInsight — written for the next project, not for closure
**Last Updated:** 2026-05-10
**Status:** SHUTDOWN COMPLETE
---

# Post-Mortem: Why startinsight.co Failed

**Project:** StartInsight (`startinsight.co`)
**Lifespan:** 2026-01-24 (Supabase project created) → 2026-05-10 (deleted)
**Production live:** 2026-02-20 → 2026-05-09 (~80 days)
**Final revenue:** $0
**Final paying customers:** 0
**Newsletter subscribers at shutdown:** 1 (anonymous, source unknown)
**External traffic:** ~0
**Verdict:** Solution in search of a problem.

---

## TL;DR

StartInsight died because the founder spent six months building a startup-idea-discovery platform without ever naming a single specific human who wanted it. When a forced diagnostic on 2026-04-18 surfaced this — and prescribed a 60-day engineering freeze with manual distribution + a 20-DM wedge test — the freeze was violated within 24 hours (with bug-fix commits), the wedge test never started, and the project was shut down on 2026-05-09 with the kill criteria still un-tested.

The root cause was not a build problem. The build was excellent: 70 tables, 235+ API endpoints, 8 AI agents, 6 scrapers, 398 backend tests at 47% coverage, clean Sentry, ~$34/mo burn. The root cause was that **the project began with a capability and tried to summon a user afterward**. The founder identified this themselves in their own `learnings.jsonl` on 2026-04-04 ("engineering-avoidance-after-ship") and again on 2026-04-18 ("AI/tech capability looking for a use case"). The shutdown three weeks later was an honest sunset, not a surprise.

---

## What Got Built

A genuinely capable product:

| Layer | What was built |
|---|---|
| **Data collection** | 6 scrapers (Reddit, Product Hunt, Google Trends, Twitter/X, Hacker News, Firecrawl) running every 6h via arq + Railway Redis |
| **AI analysis** | 8 PydanticAI agents on Gemini 2.0 Flash, 8-dimension scoring, Pydantic V2 schema validation |
| **Database** | 70 tables, 16 Alembic migrations (head: c016), Supabase Pro Sydney region |
| **API** | 235+ FastAPI endpoints, async SQLAlchemy 2.0, Stripe webhooks, Resend email |
| **Frontend** | Next.js 16 App Router, Tailwind 4, shadcn/ui, 25 components, Recharts, PostHog |
| **GTM automation** | Conviction funnel (RM49 reports), social posting agent, 4-stage email nurture, 12 programmatic SEO pages, RSS, llms.txt, JSON-LD on every page, GEO-optimized content prompts |
| **Content** | 2,085 insights generated, 180 market articles auto-published, 54-tool directory, 12 founder case studies |
| **Ops** | UptimeRobot, Sentry daily triage automation, auto-fix workflow, 35% coverage gate, 47 E2E tests across 5 browsers, CI/CD splitting fast/integration jobs |

This is a year of senior-engineer work compressed into ~6 months. The product was not the problem.

---

## What Did Not Get Built

In ~80 days of live production, before the freeze:

| Activity | Done |
|---|---|
| Specific named user identified | 0 |
| Personalized cold DMs sent | 0 |
| Telegram founder groups joined | 0 |
| Reddit r/startups posts | 0 |
| Customer interview calls | 0 |
| Reports sold | 0 |
| Subscriptions sold | 0 |
| Inbound DMs received | 0 |

The asymmetry is the post-mortem.

---

## The Verdict (Self-Diagnosed, 2026-04-18)

The founder ran a `/office-hours` diagnostic on Day 6 of the 90-day GTM sprint and answered four forcing questions with the hardest-true option each time. Direct quotes from `wysetime-pcc-main-design-20260418-142849.md`:

> **Q1 Demand Reality:** "I cannot name a single person" — no specific human has shown pull toward StartInsight. The newsletter subscriber is anonymous.
>
> **Q2 Status Quo:** "There is no real status quo" — no current workflow is being escaped. Success requires creating new behavior, the hardest kind of GTM.
>
> **Q3 Origin:** "AI/tech capability looking for a use case" — the platform came first, the user second.
>
> **Q4 Narrowest Wedge:** "All my offerings assume the platform exists" — the founder cannot currently conceive of the product without the automation.

The diagnostic's one-line summary:

> **"Solution in search of a problem. Technical demo dressed as a product. Engineering six months ahead of user discovery."**

That diagnosis was correct on 2026-04-18 and is still correct on 2026-05-10. Nothing in the next three weeks changed it, because the prescribed test was never run.

---

## The Five Root Causes

### 1. Capability-First Origin

StartInsight started with the question *"what can I build with PydanticAI + Gemini + Firecrawl?"* and worked outward to *"who would want this?"*. The user was a category ("MY/SG founders + aspiring founders + global curious builders"), not a person. Every architectural decision after that point — 8-dimension scoring, 6-source ingestion, 235+ endpoints, branching environments — added capability without adding conviction.

**Evidence:** Project-brief.md Section 8 (Competitive Positioning vs IdeaBrowser) is feature/price comparison. There is no "who specifically buys this and why" section in any memory-bank document, before or after launch.

### 2. No Existing Workflow to Replace

> *"There is no real status quo — 'nothing' is the alternative."*

Founders looking for startup ideas in 2026 use Twitter scrolling, Product Hunt browsing, ChatGPT prompts, friend conversations, or — the largest cohort — they don't actively research at all and stumble into ideas via job pain. None of those workflows are painful enough that switching to a new tool would be net-positive for the user. StartInsight required creating a *research-first idea discovery* behavior that mostly does not exist.

Creating new behavior is the hardest type of GTM. It is harder than feature parity at lower cost (the IdeaBrowser comparison) and harder than 10x speed (50ms APAC latency vs 180ms). New-behavior products need viral mechanics or a forcing function. StartInsight had neither.

### 3. The 90-Day Plan Front-Loaded Engineering, Back-Loaded Distribution

`gtm-automation-plan.md` shows the structure clearly:

- **Apr 4–5 (4 commits, 54 files, 3,818 lines):** built the entire automated GTM stack — conviction funnel, social posting agent, email nurture, 12 SEO pages, llms.txt, RSS, GEO content prompts.
- **Apr 6–17 (Day 1–13 of "operational mode"):** founder pending list never moved. From `active-context.md`, the only manual GTM action attempted in 12 days was *"Twitter creds verified in Railway"*.
- **Apr 18 (Day 13):** /office-hours session. *"As of Day 13 (2026-04-18), zero community distribution has actually happened."*

The plan was 80% automation, 20% founder-manual. The 20% never executed. By the time the diagnosis ran, the founder had built the marketing system instead of doing the marketing.

### 4. Engineering-Avoidance-After-Ship (a Pattern the Founder Named Themselves)

From the office-hours design doc:

> *"Your learnings.jsonl already named 'engineering-avoidance-after-ship' as your failure pattern on 2026-04-04. You wrote the warning to yourself two weeks ago. The fact that today's question was 'what gstack skill should I use next?' is your own system trying to route you back to engineering. Recognize the loop."*

Two weeks before the diagnostic, the founder had already identified the pattern. The pattern was: **when sales gets uncomfortable, return to code.** The 60-day engineering freeze was an attempt to break the loop by making engineering literally unavailable as a coping mechanism.

It didn't hold. Within 24 hours of the freeze declaration, commits to `main` resumed:

```
6330756 docs(ops): /office-hours pivot — engineering freeze + wedge test       [Apr 18]
7b0e3e5 fix(sentry): replace datetime.utcnow() with datetime.now(UTC) in compliance_service
2a62730 fix(sentry): 4 bugs — null competitor_analysis crash, naive datetime ...
2b96277 fix(sentry): use UTC-aware timestamps in realtime feed to prevent TypeError
042b3c5 fix(sentry): replace non-existent settings.secret_key with settings.jwt_secret
2b01ab7 fix(sentry): replace func.distinct() with distinct() in analytics.py
1be6aa5 fix(sentry): suppress 3 unused selectin loads on Insight list endpoints
... (8 more sentry fix commits before shutdown)
```

Each of these is, in isolation, a defensible bug fix. Collectively, they are the pattern repeating. **The freeze rules said one violation triggered Approach C (sunset).** It was triggered immediately and ignored for three weeks. The May 9 shutdown is what Approach C looked like after the delay.

### 5. The Wedge Test Never Ran

The /office-hours assignment, due Sunday 2026-04-20, was three concrete actions:

1. Regenerate Twitter OAuth tokens.
2. Open a Google Doc with **20 real MY/SG founder names** by Sunday.
3. Send the **first DM** by end of Sunday and screenshot it into `memory-bank/daily-operations.md`.

Failure on any of three would auto-escalate the next session to Approach C.

There is no Google Sheet artifact in the repo. There is no DM screenshot in `daily-operations.md`. There are no commits between Apr 18 and the shutdown that touch wedge-test artifacts. The git history shows only Sentry-fix commits and `chore(ops): disable CI/CD ...` from the shutdown itself. **The 20 DMs were not sent.** The wedge test that would have produced binary demand evidence within 7 days was deferred indefinitely.

This is the proximate cause of death. Distribution was the un-falsified hypothesis at the moment of shutdown — not because it had been disproven, but because it had never actually been tested.

---

## Why The Cost Picture Was Misleading

Until shutdown the docs claimed `~$30/mo total burn`. The real picture, surfaced during deletion:

| Service | Documented | Actual | Note |
|---|---|---|---|
| Supabase Pro | $25/mo (org) | $25/mo (org-shared with 2 other Wyse projects) | StartInsight's marginal share: $0 (Pro plan) + $10 (Micro compute) + $8.83 (staging branch compute) = **$18.83/mo** |
| Railway | $0 (free 500h) | **$15.13–$15.99/mo** (Hobby plan + usage) | Docs assumed Hobby was free. Hobby is $5/mo + usage. |
| Gemini API | $1–5/mo | **$0** (no billing setup, free-tier-only) | Never crossed the free quota in 80 days. |
| Stripe | 2.9% per txn | **$0** (zero transactions) | — |
| Domain | (uncosted) | ~$10–15/yr Namecheap | Auto-renew disabled on shutdown. |
| **Total marginal StartInsight cost** | ~$30/mo | **~$34/mo** | $360–408/yr |

The cost was small in absolute terms but **the documentation was wrong by a factor of ~3 on the controllable variables (Railway + Gemini)**. This is a minor finding, but it matters because cost-tracking accuracy is a leading indicator of whether the founder has talked to a real customer recently — accurate per-unit economics requires having seen a unit.

---

## Timeline

| Date | Event |
|---|---|
| 2026-01-24 | Supabase project created. |
| 2026-02-20 | Phase 1–10 complete. Production live at startinsight.co. |
| 2026-02-22 | Domain wired (Vercel + Railway + Cloudflare DNS). |
| 2026-03-20 | Phase 6 complete (resilience + intelligence). 47% test coverage. Sentry automation. |
| 2026-04-04 | Founder records "engineering-avoidance-after-ship" pattern in `learnings.jsonl`. |
| 2026-04-05 | 4-commit GTM build sprint: 54 files, 3,818 lines. Marketing automation shipped. |
| 2026-04-06 | "GTM operational mode" begins. 90-day clock starts. |
| 2026-04-12 | Day 6 status: 2,085 insights, 0 external traffic, 1 newsletter subscriber, 0 social posts published, 0 conviction funnel events fired. |
| **2026-04-18** | **/office-hours diagnostic. 60-day engineering freeze declared. Wedge test prescribed.** |
| 2026-04-19 onward | Freeze violated daily with `fix(sentry): ...` commits. Wedge test not started. |
| 2026-04-25 | Next /office-hours never held (no Google Sheet to bring). |
| 2026-05-09 | Founder declares shutdown. /office-hours pivot artifact (`docs(ops):`) committed two weeks late. |
| 2026-05-10 | Supabase StartInsight project deleted. Railway subscription cancelled. Stripe products archived. Vercel Git disconnected. Domain auto-renew off. |

The 60-day kill criteria date was 2026-06-17. Actual shutdown was 2026-05-09 — **38 days before the test would have completed**. This is consistent with the freeze having already been violated; the kill criteria were superseded by the rule the founder set themselves: *"Violation of the freeze triggers Approach C (honest sunset)."*

---

## What Worked

Worth recording, because the next project should reuse what worked:

- **Glue-coding philosophy.** Standard libraries, pydantic-ai, firecrawl-py, Crawl4AI as Firecrawl alternative. Zero custom-LLM-orchestration debt. The build was lean for what it delivered.
- **Resilience patterns adapted from World Monitor.** Per-scraper circuit breakers, stale-on-error caching, negative caching, source health registry, Welford anomaly detection, AI fallback chain. These survive as patterns the founder now knows how to ship in <2 weeks.
- **Sentry-driven self-healing.** The 14 `fix(sentry):` commits show that Sentry + the daily-triage workflow + auto-fix patterns kept production clean with near-zero manual triage overhead. This is reusable infrastructure for any future product.
- **Office-hours discipline at the right moment.** The 2026-04-18 diagnostic surfaced the truth two weeks before the founder would have hit it from another angle. Forcing-question process beats founder intuition under sunk-cost pressure.
- **Self-honesty under pressure.** Picking the hardest-true answer four times in a row. Most founders cannot do that about a product they shipped.

---

## What Did Not Work

- **Building the marketing system before doing any marketing.** GEO + SEO + social posting + email nurture all shipped before a single Telegram post was sent.
- **Relying on automated distribution to surface manual demand.** llms.txt and RSS feeds and JSON-LD do not produce a first customer; a human conversation does. The plan implicitly assumed the inverse.
- **A 90-day plan with kill criteria at Day 30/60/90 but no Day 7 binary test.** The wedge test added on 2026-04-18 was the missing structure — it should have been Day 1 of the original plan.
- **Treating "engineering freeze" as a calendar rule instead of a hard interlock.** No git hook blocked commits to main during the freeze. The rule existed as a sentence in `improvement-plan.md`. It was not enforceable.
- **Letting Sentry bug-fix urgency override the freeze.** Each fix was a 1–4 line change. None were customer-impacting (because there were no customers). All of them were a decision to *not* send a DM.

---

## What's Preserved (Not Lost in the Shutdown)

- **Code:** Git repo `Ascentia-Sandbox/StartInsight` on GitHub. Last commit `4f6c193`. Fully reusable as a template.
- **Patterns:** Memory-bank docs (this file, `architecture.md`, `tech-stack.md`, `gtm-automation-plan.md`, `improvement-plan.md`) are intact.
- **Stripe history:** Archived products + 6 archived prices remain in Stripe Dashboard for tax/audit.
- **Sentry projects:** `ascentia-km/backend`, `ascentia-km/frontend` remain (free tier, $0).
- **Domain:** `startinsight.co` lives until next Namecheap renewal lapses. No auto-renewal charge.
- **Stripe customers:** Zero ever existed. Nothing to refund or notify.
- **Founder learnings:** `~/.gstack/projects/Ascentia-Sandbox-StartInsight/learnings.jsonl`. Preserve this file forever.

## What's Gone (Permanently)

- **Supabase StartInsight project** (`mxduetfcsgttwwgszjae`): deleted 2026-05-10. Database, auth users, storage, branches all permanently destroyed. No pg_dump was taken.
- **Railway services:** backend + Redis deployments removed. Hobby subscription cancels Jun 2 2026.
- **Vercel Git integration:** disconnected; no auto-deploys.
- **GitHub Actions schedules:** ci-cd.yml + release.yml + sentry-daily-triage.yml triggers commented out (commit `4f6c193`).

---

## The Three Lessons (For The Next Project)

These are the only three lessons worth carrying forward. Everything else is a special case of these.

### 1. Begin with a person, not a capability.

The founder wrote this themselves: *"It also means the next project you start should begin with a user in pain, not a capability you want to use. Write that down somewhere you will see it again."*

For the next project, before any code: name the human, name their current workflow, name the moment of pain in that workflow, name what they are willing to pay today to make that pain stop. If those four answers cannot be written down, the project is not ready to start.

### 2. The wedge test belongs on Day 1, not Day 90.

Sell the manual version of the product before automating it. RM49, hand-written, 48-hour turnaround, three slots. If three humans cannot be persuaded to pay for the manual version in seven days, no amount of automation will sell the automated version. This is a one-week test that prevents one-year sunk costs.

### 3. Make engineering freezes interlocked, not voluntary.

A pre-commit hook that blocks pushes to `main` is enforceable. A sentence in a markdown file is not. If a freeze is the right tool, install the lock at the same moment the freeze is declared. Otherwise the freeze is just a stronger feeling about not committing — and feelings lose to the comfort of typing `git commit` when sales gets hard.

---

## Closing

StartInsight was not a failure of competence. The build was good. The architecture was good. The cost discipline was reasonable. The self-honesty during the office-hours diagnostic was rare.

It was a failure of *sequence*. The founder built first, then asked who it was for; the right order is the inverse, and that inversion is the only lesson that needs to survive.

The next project earns the right to be coded only after a specific human has paid cash for the manual version of what it does.

---

**Last Updated:** 2026-05-10
**Status:** Project sunset. Repository preserved. Founder-attention freed.
