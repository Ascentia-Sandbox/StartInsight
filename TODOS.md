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

### ~~Stripe Webhook Backward Compatibility Window~~ ✅ Fixed by /plan on 2026-03-24

`TIER_COMPAT_MAP` already present (starter→pro, enterprise→api). Added tier sync to `_handle_subscription_updated` so status changes (canceled/unpaid/active) propagate to `user.subscription_tier` (commit 85d1b14). Remove `TIER_COMPAT_MAP` by 2026-04-23.

## Design

### ~~Premium Content Blur Treatment~~ ✅ Fixed by /plan on 2026-03-24

Replaced `blur-sm opacity-50` in `FeatureLock.tsx` with CSS gradient fade (transparent 0–55% → background 88%) and bottom-anchored upgrade CTA. No hard blur — editorial aesthetic (commit e0639db).

### Create DESIGN.md

**What:** Document the existing design system — oklch color tokens, Satoshi/JetBrains Mono/Instrument Serif fonts, spacing scale, component patterns, dark mode strategy.

**Why:** The design tokens exist in globals.css but aren't documented as a system. Without DESIGN.md, every new page or component risks inconsistency — different accent colors, wrong font pairings, ad-hoc spacing. This is especially important as the PLG plan adds 3+ new UI surfaces (newsletter forms, paywall gates, report counter).

**Context:** Identified during design review (2026-03-23). Current state: oklch tokens in globals.css (primary: deep teal `oklch(0.45 0.12 195)`, accent: warm amber `oklch(0.75 0.15 75)`, background: warm off-white `oklch(0.985 0.005 90)`), 3 custom fonts, shadcn/ui components, 0.625rem border-radius. Run `/design-consultation` to generate a comprehensive DESIGN.md.

**Effort:** S
**Priority:** P2
**Depends on:** None — can be done immediately

### Weekly AI Trend Report PDF Template

**What:** Design the visual template for the weekly AI trend report PDF — branded header, section layout, data visualization style, free vs paid content split.

**Why:** The PDF is the primary lead magnet and shareable asset in the PLG plan. A poorly designed PDF undermines the brand and reduces sharing. The free version (top 10 summaries) needs to look good enough to share while making the paid version (full analysis + BMC) clearly more valuable.

**Context:** Identified during design review (2026-03-23). The plan accepts the weekly AI trend report as scope but specifies zero visual design. Needs: (a) branded header with StartInsight logo + issue number, (b) section layout for trend summaries, (c) data viz style for scores/charts, (d) clear visual distinction between free summary and paid full analysis, (e) CTA placement for upgrade. Consider using existing oklch color tokens for brand consistency.

**Effort:** S
**Priority:** P2
**Depends on:** None — can start before Phase 2 content push
