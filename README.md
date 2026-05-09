# StartInsight

**An archived project. 2026-01-24 — 2026-05-10.**

> _"Solution in search of a problem. Technical demo dressed as a product. Engineering six months ahead of user discovery."_
> — /office-hours diagnostic, 2026-04-18

---

## What this repository is now

This is the archived source of an AI-powered startup-idea-discovery platform that ran in production at [startinsight.co](https://startinsight.co) for **80 days** and earned **$0**. The hosting has been shut down, the database is deleted, the Stripe products are archived, the CI/CD workflows are disabled, and the domain is set not to renew.

The repository is preserved as a record — for the founder, and for any other founder considering a project that begins with a capability rather than a person.

The live URL `startinsight.co` no longer hosts the original product. **It now hosts a single-page memorial** of the project's life and the lessons it cost.

---

## Where to read the lessons

| Where | What |
|---|---|
| [`memory-bank/post-mortem.md`](memory-bank/post-mortem.md) | Long-form post-mortem. Five root causes. Three lessons. The full timeline. |
| [`memorial/frontend/index.html`](memorial/frontend/index.html) | The public memorial site source — single HTML file, editorial typography, embedded CSS. |
| <https://startinsight.co> | The memorial, served live. |

If you only read one thing: read the three lessons at the bottom of the post-mortem. They cost a year to write.

---

## What was built (preserved here for reference)

The project did ship a complete, working product before it was shut down. The code remains useful as a template for the patterns it executed well.

| Layer | Stack |
|---|---|
| Frontend | Next.js 16, App Router, TypeScript, Tailwind 4, shadcn/ui, Recharts, PostHog |
| Backend | FastAPI (async), SQLAlchemy 2.0, Pydantic V2, arq (task queue), uv |
| Database | PostgreSQL via Supabase (70 tables, 16 Alembic migrations, ES256 JWT auth) |
| AI | PydanticAI v1.x + Gemini 2.0 Flash, 8 agents with 8-dimension scoring |
| Scrapers | Reddit (PRAW), Product Hunt, Google Trends (pytrends), Twitter/X (Tweepy), Hacker News, Firecrawl + Crawl4AI fallback |
| Infra | Railway (backend + Redis), Vercel (frontend), Supabase Pro (DB), Sentry, Resend |

**Numbers at the moment of freeze:**
398 backend tests at 47% coverage · 47 E2E tests across 5 browsers · 235+ FastAPI endpoints · 2,085 insights generated · 180 market articles auto-published · 12 programmatic SEO pages · clean Sentry · sub-100ms APAC latency.

---

## Repository map

```
.
├── backend/             # FastAPI app, 8 PydanticAI agents, 6 scrapers, 70-table schema
├── frontend/            # Next.js 16 app — UI, dashboards, validation flows
├── memory-bank/         # Strategic docs (read in this order)
│   ├── project-brief.md            # What it was meant to be
│   ├── tech-stack.md               # What it was built with (cost docs were wrong; see post-mortem)
│   ├── architecture.md             # 70-table schema, 235-endpoint surface
│   ├── implementation-plan.md      # Phase 1-10 + GTM 1-5 history
│   ├── progress.md                 # Build log
│   ├── active-context.md           # Final state at engineering freeze
│   ├── gtm-automation-plan.md      # The 90-day plan that shipped without execution
│   ├── improvement-plan.md         # Phase 6 resilience patterns (worth reusing)
│   ├── daily-operations.md         # Daily checklist (now defunct)
│   └── post-mortem.md              # ⭐ Read this if you read nothing else
├── memorial/            # Source for startinsight.co memorial site
│   ├── frontend/index.html         # Single-file editorial post-mortem (45KB)
│   ├── vercel.json
│   └── README.md                   # Redeploy instructions
├── scripts/
│   └── shutdown_audit.sh           # pg_dump helper used during shutdown
├── docs/                # Codemaps + guides
└── .github/workflows/   # CI/CD (all triggers disabled)
```

---

## Final state of services

| Service | State | Cost going forward |
|---|---|---|
| **Vercel** project `start-insight` | Hobby tier, serves `startinsight.co` memorial | $0 |
| **Railway** workspace | Hobby subscription cancelled, ends Jun 2 2026 | $0 after Jun 2 |
| **Supabase** StartInsight project | **Deleted 2026-05-10** (database, auth, storage all permanently gone) | $0 |
| **Stripe** products | All 3 archived, all 6 prices archived, 0 customers | $0 |
| **Sentry** projects | Free Developer plan retained for record | $0 |
| **Domain** `startinsight.co` | Auto-renew off at Namecheap; lapses on next anniversary | $0 |
| **GitHub Actions** | All scheduled workflows disabled (`workflow_dispatch` only) | $0 |
| **Google Cloud / Gemini** | No billing setup; free-tier-only the entire time | $0 |

Total monthly recurring cost from this project: **$0**.

---

## How to revive (if you ever decide to)

The repository is self-sufficient. Anyone with the `Ascentia-Sandbox/StartInsight` GitHub access can:

1. Provision a new Supabase project, run `alembic upgrade head` to recreate the 70-table schema.
2. Spin up Railway, set the env vars from `backend/.env.production.example`.
3. Reconnect Vercel Git integration; push to `main` to deploy.
4. Re-enable GitHub Actions workflows by uncommenting the `push:` triggers in `.github/workflows/`.

That said — if you find yourself reading this with the intent of reviving the project, please re-read [`memory-bank/post-mortem.md`](memory-bank/post-mortem.md) first. Specifically the three lessons at the end. The repo is reusable. The premise was not.

---

## Acknowledgements

The strongest part of this project was not the code. It was the founder's willingness to run an honest forcing-question diagnostic on himself on 2026-04-18 — and to name the project's actual disease in plain language while the build was still operating perfectly. Most founders cannot do that until much later, or at all.

The diagnosis was correct. The shutdown was the right move. This README, the post-mortem, and the memorial site exist so that the lesson outlives the loss.

---

## License

MIT — see [`LICENSE`](LICENSE).

The code is preserved as-is for reference. Use whatever pieces are useful for your own project. Just remember: start with a person, not a capability.

---

**Last updated:** 2026-05-10
**Status:** ARCHIVED. No further commits planned.
