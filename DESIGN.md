# Design System — StartInsight

## Product Context
- **What this is:** AI-powered startup idea discovery and analysis platform
- **Who it's for:** Founders, aspiring entrepreneurs, and startup ecosystem participants (MY/SG/Asia focus)
- **Space/industry:** Startup intelligence, competitive analysis, opportunity discovery
- **Project type:** Data-heavy web app with editorial content

## Aesthetic Direction
- **Direction:** Editorial Data Intelligence — a research publication meets Bloomberg terminal sensibility
- **Decoration level:** Intentional — subtle textures (dot grid backgrounds, SVG noise on cards, gradient mesh heroes) add depth without distraction
- **Mood:** Authoritative yet approachable. The warm paper-tone background and serif display headings create a research publication feel; the teal/amber palette keeps it from feeling cold or clinical
- **Reference:** The Information, Crunchbase, Bloomberg — editorial typography with data density

## Typography

All fonts loaded in `frontend/app/layout.tsx`. CSS variables defined in `globals.css`.

- **Display/Hero:** Instrument Serif (Google Fonts, weight 400) — `var(--font-display)`
  - Used for: h1 (36px), h2 (24px), `.text-display` (48px hero text)
  - Letter-spacing: -0.02em (display), -0.01em (h2)
  - Rationale: Serif display font creates editorial authority; single weight keeps it clean
- **Body/UI:** Satoshi (self-hosted woff2, weights 400/500/700) — `var(--font-satoshi)`
  - Used for: body text (16px/1.6), h3 (18px/600), buttons, labels, navigation
  - Loaded from `public/fonts/satoshi-{400,500,700}.woff2`
  - Rationale: Geometric sans with personality; self-hosted for performance
- **Data/Code:** JetBrains Mono (Google Fonts) — `var(--font-mono)`
  - Used for: scores, metrics, IDs, code blocks via `.font-data` utility class
  - Features: `font-variant-numeric: tabular-nums` for aligned number columns
  - Rationale: Clear distinction between editorial content and data; tabular figures for score alignment

### Type Scale
| Level | Size | Font | Weight | Line-height | Letter-spacing |
|-------|------|------|--------|-------------|----------------|
| Display | 48px (3rem) | Instrument Serif | 400 | 1.1 | -0.02em |
| H1 | 36px (2.25rem) | Instrument Serif | 400 | 1.2 | -0.02em |
| H2 | 24px (1.5rem) | Instrument Serif | 400 | 1.3 | -0.01em |
| H3 | 18px (1.125rem) | Satoshi | 600 | 1.4 | — |
| Body | 16px (1rem) | Satoshi | 400 | 1.6 | — |
| Data | inherit | JetBrains Mono | inherit | inherit | -0.01em |

### Font Loading Strategy
All fonts use `display: 'optional'` — prioritizes performance over FOIT. If fonts don't load in time, the fallback stack renders immediately.

Fallback stacks:
- Satoshi → `ui-sans-serif, system-ui, sans-serif`
- Instrument Serif → `"Instrument Serif", Georgia, serif`
- JetBrains Mono → `"JetBrains Mono", ui-monospace, monospace`

## Color

All colors use **oklch** — a perceptually uniform color space. This means equal lightness values look equally bright regardless of hue.

- **Approach:** Restrained — one primary (teal) + one accent (amber) + warm neutrals. Color is meaningful, not decorative.

### Core Palette

| Token | Light | Dark | Usage |
|-------|-------|------|-------|
| `--primary` | `oklch(0.45 0.12 195)` ~#0D7377 | `oklch(0.65 0.12 195)` | Deep teal — CTAs, links, focus rings, interactive elements |
| `--primary-foreground` | `oklch(1 0 0)` white | `oklch(0.15 0.01 250)` | Text on primary backgrounds |
| `--accent` | `oklch(0.75 0.15 75)` ~#D4A017 | `oklch(0.70 0.15 75)` | Warm amber — highlights, badges, secondary CTAs |
| `--accent-foreground` | `oklch(1 0 0)` white | `oklch(0.15 0.01 250)` | Text on accent backgrounds |
| `--background` | `oklch(0.985 0.005 90)` warm off-white | `oklch(0.15 0.01 250)` deep slate | Page background |
| `--foreground` | `oklch(0.20 0.01 250)` ink black | `oklch(0.95 0.005 90)` off-white | Primary text |
| `--card` | `oklch(0.98 0.003 90)` | `oklch(0.20 0.01 250)` | Card surfaces (slightly darker than bg) |
| `--muted` | `oklch(0.94 0.005 90)` | `oklch(0.25 0.01 250)` | Muted backgrounds |
| `--muted-foreground` | `oklch(0.50 0.01 250)` | `oklch(0.65 0.005 90)` | Secondary/caption text |
| `--secondary` | `oklch(0.96 0.005 90)` | `oklch(0.25 0.01 250)` | Secondary backgrounds |
| `--border` | `oklch(0.90 0.005 90)` | `oklch(1 0 0 / 10%)` | Borders, dividers |
| `--input` | `oklch(0.90 0.005 90)` | `oklch(1 0 0 / 15%)` | Input borders |
| `--ring` | `oklch(0.45 0.12 195)` | `oklch(0.55 0.10 195)` | Focus rings |

### Semantic Colors

| Token | Value | Usage |
|-------|-------|-------|
| `--destructive` | Light: `oklch(0.577 0.245 27.325)`, Dark: `oklch(0.704 0.191 22.216)` | Error states, delete actions |
| `--info` (new) | Light: `oklch(0.55 0.12 250)`, Dark: `oklch(0.65 0.10 250)` | Informational states, notices |

Note: Success and warning states currently use Tailwind utility classes (`text-green-600`, `text-amber-600`). These are not yet tokenized as CSS variables.

### Chart Colors

5-color palette for data visualization, designed for distinguishability:

| Token | Value | Name |
|-------|-------|------|
| `--chart-1` | `oklch(0.45 0.12 195)` | Primary teal |
| `--chart-2` | `oklch(0.696 0.17 162.48)` | Emerald |
| `--chart-3` | `oklch(0.75 0.15 75)` | Warm amber |
| `--chart-4` | `oklch(0.65 0.18 25)` | Coral |
| `--chart-5` | `oklch(0.55 0.10 250)` | Slate blue |

### Dark Mode Strategy
- Primary teal lightened from 0.45 → 0.65 lightness (same chroma and hue)
- Accent amber lightened slightly from 0.75 → 0.70
- Background inverted to deep slate `oklch(0.15 0.01 250)`
- Cards elevated to `oklch(0.20 0.01 250)`
- Borders use `oklch(1 0 0 / 10%)` — white at 10% opacity
- All theme transitions: `150ms ease` on background-color, border-color, color
- Toggle: `className="dark"` on `<html>` element

## Spacing

- **Base unit:** 8px
- **Density:** Comfortable — generous whitespace befitting editorial/data aesthetic

| Token | Value | Usage |
|-------|-------|-------|
| `--space-2xs` (new) | 4px | Tight padding: badges, inline spacing, icon gaps |
| `--space-xs` | 8px | Small padding, gap between related elements |
| `--space-sm` | 16px | Standard padding, card internal spacing |
| `--space-md` | 24px | Section padding, larger card gaps |
| `--space-lg` | 32px | Section margins |
| `--space-xl` | 48px | Page section spacing |
| `--space-2xl` | 64px | Hero section vertical padding |

### Content Width
| Token | Value | Usage |
|-------|-------|-------|
| `--content-width` | 1200px | Max width for main content areas |
| `--narrow-width` | 800px | Max width for reading-optimized content (articles, detail pages) |

## Layout
- **Approach:** Grid-disciplined — consistent column layouts per breakpoint
- **Grid:** Tailwind responsive utilities (`md:grid-cols-2`, `lg:grid-cols-3`, etc.)
- **Max content width:** 1200px (general), 800px (reading content)
- **Component library:** shadcn/ui — all primitives in `frontend/components/ui/`

### Border Radius

Base: `--radius: 0.625rem` (10px)

| Token | Computed | Usage |
|-------|----------|-------|
| `--radius-sm` | 6px | Small elements: badges, chips, tags |
| `--radius-md` | 8px | Inputs, small cards |
| `--radius-lg` | 10px (base) | Standard cards, dialogs |
| `--radius-xl` | 14px | Large cards, modals |
| `--radius-2xl` | 18px | Hero cards, prominent surfaces |
| `--radius-3xl` | 22px | Feature panels |
| `--radius-4xl` | 26px | Full-width banners |
| `rounded-full` | 9999px | Avatars, circular buttons, pills |

### Shadow Scale (documented from existing usage)

| Level | Value | Usage |
|-------|-------|-------|
| Resting | `0 1px 3px rgba(0,0,0,0.08)` | Default card state |
| Hover | `0 4px 16px oklch(0.45 0.12 195 / 0.12), 0 1px 3px rgba(0,0,0,0.08)` | Card hover — teal-tinted glow |
| Elevated | `0 8px 24px rgba(0,0,0,0.12)` | Modals, popovers, dropdowns |

## Motion
- **Approach:** Minimal-functional — motion aids comprehension, never decorates

### Transition Tokens (documented from existing patterns)

| Token | Value | Usage |
|-------|-------|-------|
| `--transition-fast` (new) | `150ms ease` | Theme switching, border/color changes, button states |
| `--transition-normal` (new) | `200ms ease` | Card hover transforms, layout shifts |

### Interactive Patterns

| Element | Behavior |
|---------|----------|
| Buttons | `translateY(-2px)` on hover, 150ms ease-out |
| Cards (`.card-hover`) | `scale(1.01)` + teal border glow + shadow elevation on hover |
| Links | Underline on hover |
| Theme switch | 150ms ease on background-color, border-color, color (all elements) |

## Textures & Backgrounds

Distinctive visual elements that give StartInsight its editorial character:

| Class | Description | Usage |
|-------|-------------|-------|
| `.dot-grid-bg` | Radial gradient dots at 24px intervals using `--border` color | Main content backgrounds, subtle visual texture |
| `.hero-gradient` | 135deg gradient: teal (8%) → background → amber (5%) | Hero sections, feature highlights |
| `.card-texture` | SVG noise overlay at 3% opacity via `::after` pseudo-element | Cards that need subtle depth/materiality |

All textures have dark mode variants with adjusted opacity/colors.

## Accessibility

### Keyboard Navigation
- All interactive elements have `outline: 2px` focus ring using `--ring` color with `2px offset`
- Skip-to-content link: `.skip-to-content` — visually hidden until focused
- Screen reader utility: `.sr-only` with proper clip-path hiding

### Touch Targets
- Minimum 44x44px on coarse pointer devices (`@media (pointer: coarse)`)
- Applied to: buttons, links, `[role="button"]`, select, checkbox, radio
- Select triggers specifically targeted: `[data-slot="select-trigger"]`

### Mobile Optimizations
- `-webkit-tap-highlight-color` on interactive elements
- `user-select: none` on buttons to prevent text selection
- `-webkit-overflow-scrolling: touch` for smooth momentum scrolling

## Component Patterns

### Source of Truth
- CSS tokens: `frontend/app/globals.css`
- Font loading: `frontend/app/layout.tsx`
- UI primitives: `frontend/components/ui/` (shadcn/ui)
- Custom components: `frontend/components/`

### Key Custom Components
| Component | Purpose | Key Design Patterns |
|-----------|---------|-------------------|
| InsightCard | Core data card showing startup idea scores | Platform-specific source badges with branded colors; 8-dimension score display; confidence levels (green/amber/red) |
| Header | Main navigation | Auth-aware, tier badge, mega menu, mobile menu, theme toggle |
| FeatureLock | Paywall gate | CSS gradient fade (transparent→background) + bottom-anchored upgrade CTA — no hard blur (editorial aesthetic) |
| TrendChart / TrendSparkline | Data visualization | Uses chart color tokens |
| ScoreRadar | Radar chart for 8 dimensions | Canvas-based, responsive |
| CommandPalette | Quick search/navigate | Dialog pattern with keyboard shortcuts |

### Data Display Conventions
- Scores and metrics: Always use `.font-data` (JetBrains Mono, tabular-nums)
- Platform sources: Color-coded badges (Reddit=orange, ProductHunt=red, HackerNews=amber, Twitter=sky)
- Confidence levels: High (green, >=0.8), Medium (amber), Low (red)
- Percentages: Show one decimal place for scores

## Decisions Log
| Date | Decision | Rationale |
|------|----------|-----------|
| 2026-03-23 | Initial DESIGN.md created | Documents existing design system from globals.css. Created by /design-consultation. |
| 2026-03-23 | Added `--space-2xs: 4px` token | Fills gap in spacing scale for tight badge/chip padding |
| 2026-03-23 | Added `--info` semantic color | Completes semantic color set (destructive had no info counterpart) |
| 2026-03-23 | Documented shadow scale | Formalized 3 existing shadow levels (resting/hover/elevated) to prevent drift |
| 2026-03-23 | Documented transition tokens | Named existing 150ms/200ms patterns to ensure consistency |
| 2026-03-23 | Documented border-radius hierarchy | Clarified 7-tier radius scale derived from base `--radius` |
| 2026-03-24 | FeatureLock: blur → gradient fade | Replaced `blur-sm opacity-50` with CSS gradient fade for editorial aesthetic consistency (commit e0639db) |
