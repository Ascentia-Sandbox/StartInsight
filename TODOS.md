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

### Privacy Policy PDPA Update

**What:** Update existing privacy/page.tsx to add PDPA (Malaysia Personal Data Protection Act) compliance, newsletter consent tracking, and referral data usage sections.

**Why:** P1 BLOCKER for newsletter launch. Malaysia's PDPA requires explicit consent for data collection and processing. The existing privacy page covers GDPR basics but lacks PDPA-specific sections, newsletter consent language, and referral data disclosure.

**Context:** Privacy page already exists at frontend/app/[locale]/privacy/page.tsx with 10+ sections covering data collection, AI processing, Stripe, and basic GDPR. Needs additions for: (a) PDPA compliance sections, (b) newsletter email collection consent, (c) referral code tracking disclosure, (d) PostHog analytics opt-out, (e) cookie consent if not already present.

**Effort:** S
**Priority:** P1
**Depends on:** None — can be done immediately

## Infrastructure

### Newsletter Merge-on-Signup

**What:** When a newsletter subscriber creates an account, merge their subscriber record with their user record.

**Why:** Without merge logic, a person who subscribed to the newsletter before signing up will have two separate records — their newsletter preferences won't carry over, and they may receive duplicate emails or lose their subscription status.

**Context:** Identified during eng review (2026-03-23) by Codex outside voice. The plan creates a separate newsletter_subscribers table for lead-gen (allowing non-registered visitors to subscribe). When these visitors later create accounts, the system needs to: (a) detect matching email, (b) link subscriber record to user, (c) carry over preferences. Existing user_preferences.py has email preference infrastructure that should be the target state.

**Effort:** S
**Priority:** P2
**Depends on:** Newsletter subscriber table implementation (Phase 1)

### Stripe Webhook Backward Compatibility Window

**What:** Handle in-flight Stripe webhooks that reference old tier names (starter, enterprise) during the pricing migration.

**Why:** If any webhook events are queued by Stripe before the tier rename and arrive after deployment, they'll reference old tier names that no longer exist in the codebase. With zero customers this is extremely unlikely, but the webhook handler should gracefully map old→new tier names rather than failing.

**Context:** Identified during eng review (2026-03-23). The _handle_checkout_completed function reads tier from webhook metadata. During migration, add a simple mapping: {"starter": "pro", "enterprise": "pro"} as a fallback in the webhook handler. Can be removed after 30 days.

**Effort:** S
**Priority:** P2
**Depends on:** Pricing tier consolidation (Phase 1)

## Design

### Premium Content Blur Treatment

**What:** Design the exact blur/gate treatment for premium content on insight detail pages — gradient fade vs hard blur, teaser text visibility, visual hierarchy of the gate overlay.

**Why:** The plan says "blurred preview of full report" but doesn't specify the exact visual treatment. Without a spec, the implementer will default to a generic blur-sm that doesn't communicate value or create urgency. The blur treatment directly affects conversion — users need to see enough to want more, but not so much that they feel cheated.

**Context:** Identified during design review (2026-03-23). Existing FeatureLock.tsx uses `blur-sm opacity-50` with a centered lock overlay. Options to explore: (a) gradient fade (content visible at top, progressively blurred), (b) hard blur with teaser headline visible, (c) partial content visible with "Continue reading with Pro" inline gate. The gradient fade pattern (used by Medium, The Athletic) has the strongest conversion evidence.

**Effort:** S
**Priority:** P2
**Depends on:** Sectioned paywall implementation (Phase 1)

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
