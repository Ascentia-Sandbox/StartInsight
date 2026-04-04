# TODOS

## Growth Features

### Startup Failure Cemetery

**What:** Failory-style failure postmortems and root cause analysis for MY/SG startups.

**Why:** Strong SEO asset and content marketing driver — "here's what to build AND here's what killed companies that tried before." Complements opportunity discovery.

**Context:** Deferred from CEO review (2026-03-23). Good for organic traffic but not essential for first 100 paid customers. Build after core freemium proves traction. Would need a new data pipeline for public startup death data (Crunchbase, news archives). AI agents can draft from public data, founder reviews and publishes.

**Effort:** M
**Priority:** P3
**Depends on:** Core freemium proving traction (Phase 1-2 complete)

### B2B Accelerator Dashboard

**What:** Dashboard for accelerators/angel groups to discover and connect with founders on the platform.

**Why:** Potential B2B revenue stream ($300-$1,000/mo per accelerator). Codex's cold read suggested this as the strongest monetization path — a localized B2B scouting feed for accelerator managers.

**Context:** Deferred from CEO review (2026-03-23). Requires 100 signed-up founders as supply side before this has value. The founder chose community-first (B2C) over B2B-first, but this should be revisited after 20 customer conversations confirm/deny whether accelerator managers would pay.

**Effort:** L
**Priority:** P3
**Depends on:** 100 signed-up founders (supply side)

## Compliance

### ~~Privacy Policy PDPA Update~~ ✅ Fixed by /plan on 2026-03-24

All 5 PDPA sections (13–17) were already present from a prior commit. Added explicit consent statement to NewsletterForm.tsx with Privacy Policy link (commit e0639db).

## Infrastructure

### ~~Newsletter Merge-on-Signup~~ ✅ Fixed by /plan on 2026-03-24

Added `user_id` FK to `newsletter_subscribers` (migration c016), and linked the subscriber record in `_verify_and_get_user` after JIT user upsert (commit 215cf9c).

### ~~Stripe Webhook Backward Compatibility Window~~ ✅ Fully removed 2026-04-04

`TIER_COMPAT_MAP` removed from `payment_service.py`. Tier sync in `_handle_subscription_updated` remains. Original compat window deadline was 2026-04-23.

## Design

### ~~Premium Content Blur Treatment~~ ✅ Fixed by /plan on 2026-03-24

Replaced `blur-sm opacity-50` in `FeatureLock.tsx` with CSS gradient fade (transparent 0–55% → background 88%) and bottom-anchored upgrade CTA. No hard blur — editorial aesthetic (commit e0639db).

### ~~Create DESIGN.md~~ ✅ Fixed by /design-consultation on 2026-03-23, committed 2026-03-24

234-line design system reference covering oklch color tokens, typography (Instrument Serif/Satoshi/JetBrains Mono), spacing scale, border radius hierarchy, shadow scale, motion tokens, textures, accessibility, and component patterns.

### ~~Weekly AI Trend Report PDF Template~~ ✅ Done 2026-03-29

**Backend:** `backend/app/services/weekly_report_pdf.py` — WeasyPrint HTML template.
**Endpoint:** `GET /api/reports/weekly-pdf` (reports.py) — free/pro tiers, auth-optional.
**Frontend:** "Export PDF" button in `frontend/app/[locale]/reports/page.tsx` wired to endpoint.
- Free tier: top 10 summaries + upgrade CTA page
- Pro tier: full detail (market size, revenue potential, opportunity score, solution)

## QA Issues (2026-03-29)

### ~~ISSUE-001: Grammar — "1 saved insights"~~ ✅ Fixed 2026-03-29

Singular/plural logic added to `dashboard/page.tsx` line 331. Commit 6028bad.

### ~~ISSUE-004: Admin Pipeline/Settings stuck on spinner (Mixed Content)~~ ✅ Fixed 2026-03-29

`fetchSystemSettings` in `lib/api.ts` was calling `/api/admin/settings` (no trailing slash). FastAPI redirects to `/api/admin/settings/` but Railway strips HTTPS from the Location header → Mixed Content blocks the request. Fix: use trailing slash. Commit 6028bad.

### ISSUE-002: Validate page — Similar Ideas always show "100% match" (P2)

All 5 similar ideas on the validate result page show "100% match" regardless of actual semantic similarity. Irrelevant ideas (pet game dev, XSS protection, theme park rides) match an HR onboarding SaaS at 100%. Likely the similarity score field is being populated incorrectly by the backend.

### ISSUE-003: Chat UX — no auto-focus after sending first message (P2)

After sending a message in the chat (when no session is active), the UI creates a session and sends the message, but doesn't auto-navigate to the newly-active session. User must manually click the session in the sidebar to see the AI response.

### ISSUE-005: Market Insights article cards not keyboard-accessible (P3)

Cards use `cursor:pointer` divs instead of `<a>` elements. Not keyboard-navigable or screen-reader friendly.

### ISSUE-006: Select controlled/uncontrolled warning in console (P3)

`[warning] Select is changing from uncontrolled to controlled` appears on validate page when dropdowns are used. Radix Select initialized without a value then set. Low priority but noisy in console.
