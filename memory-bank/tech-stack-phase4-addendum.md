# Tech Stack Addendum: Phase 4+ Dependencies

**Version:** 2.0
**Last Updated:** 2026-01-24
**Base Document:** `tech-stack.md`
**Status:** Active Development

---

## Overview

This document extends `tech-stack.md` with all new dependencies and technology decisions for Phases 4-7+.

---

## Phase 4 Dependencies

### Backend (Python)

```toml
# backend/pyproject.toml

[project]
dependencies = [
    # ============================================
    # PHASE 1-3 (Existing - v0.1)
    # ============================================
    "fastapi>=0.109.0",
    "uvicorn[standard]>=0.27.0",
    "pydantic>=2.5.0",
    "pydantic-settings>=2.1.0",
    "sqlalchemy[asyncio]>=2.0.25",
    "alembic>=1.13.0",
    "asyncpg>=0.29.0",
    "redis>=5.0.1",
    "pydantic-ai>=0.0.13",
    "anthropic>=0.25.0",
    "openai>=1.12.0",
    "firecrawl-py>=0.0.16",
    "praw>=7.7.1",
    "pytrends>=4.9.2",
    "arq>=0.25.0",
    "python-dotenv>=1.0.0",
    "httpx>=0.26.0",
    "tenacity>=8.2.3",

    # ============================================
    # PHASE 4.1: USER AUTHENTICATION
    # ============================================
    "clerk-backend-api>=2.0.0",  # Clerk SDK for JWT verification

    # ============================================
    # PHASE 4.2: ADMIN PORTAL
    # ============================================
    "sse-starlette>=2.0.0",  # Server-Sent Events for real-time updates

    # ============================================
    # PHASE 5: EXPORT FEATURES
    # ============================================
    "reportlab>=4.0.0",  # PDF generation (better quality)
    # OR
    "weasyprint>=60.0",  # Alternative PDF (HTML → PDF)

    # ============================================
    # PHASE 6: PAYMENTS & EMAIL
    # ============================================
    "stripe>=7.0.0",  # Payment processing
    "resend>=0.8.0",  # Email notifications
    # OR
    "sendgrid>=6.11.0",  # Alternative email service

    # ============================================
    # PHASE 6: RATE LIMITING
    # ============================================
    "fastapi-limiter>=0.1.6",  # Redis-based rate limiting

    # ============================================
    # PHASE 7: ADDITIONAL SCRAPERS
    # ============================================
    "tweepy>=4.14.0",  # Twitter/X API
    # OR
    "twikit>=2.0.0",  # Alternative Twitter scraper (no API key)

    # ============================================
    # UTILITIES (Phase 4+)
    # ============================================
    "tiktoken>=0.5.2",  # Accurate token counting for LLM costs
    "pillow>=10.0.0",  # Image generation for brand packages
    "jinja2>=3.1.2",  # Template engine for landing pages/emails
]

[project.optional-dependencies]
dev = [
    "pytest>=7.4.0",
    "pytest-asyncio>=0.21.0",
    "pytest-cov>=4.1.0",
    "ruff>=0.1.0",
    "mypy>=1.7.0",
    "httpx>=0.26.0",  # For testing
]
```

**Dependency Justification:**

| Dependency | Purpose | Why Chosen | Alternatives Rejected |
|------------|---------|------------|----------------------|
| **clerk-backend-api** | JWT verification | Next.js native, generous free tier (10K MAU) | Auth0 ($240/yr), NextAuth (more setup) |
| **sse-starlette** | Real-time updates | Simple HTTP-based streaming for admin portal | WebSocket (overkill), Polling (inefficient) |
| **reportlab** | PDF export | Industry standard, high quality | PyPDF2 (no generation), wkhtmltopdf (deprecated) |
| **stripe** | Payments | Best developer experience, 2.9% + $0.30 | PayPal (higher fees), Paddle (complex) |
| **resend** | Email | Modern API, free 3K emails/month | SendGrid (complex), Mailgun (expensive) |
| **tiktoken** | Token counting | Official OpenAI library, accurate | Approximation (4 chars/token) |

---

### Frontend (JavaScript/TypeScript)

```json
{
  "name": "startinsight-frontend",
  "version": "0.2.0",
  "dependencies": {
    // ============================================
    // PHASE 1-3 (Existing - v0.1)
    // ============================================
    "next": "^16.1.3",
    "react": "^19.2.3",
    "react-dom": "^19.2.3",
    "@tanstack/react-query": "^5.20.0",
    "tailwindcss": "^4.0.0",
    "recharts": "^2.10.0",
    "date-fns": "^3.3.0",
    "zod": "^3.22.0",
    "axios": "^1.6.0",
    "lucide-react": "^0.263.1",

    // ============================================
    // PHASE 4.1: USER AUTHENTICATION
    // ============================================
    "@clerk/nextjs": "^5.0.0",  // Clerk SDK for Next.js

    // ============================================
    // PHASE 4.2: ADMIN PORTAL
    // ============================================
    "@tanstack/react-table": "^8.11.0",  // Advanced tables for logs
    // Note: SSE uses built-in EventSource API (no package needed)

    // ============================================
    // PHASE 4.4: SHARING & INTERACTIONS
    // ============================================
    "react-share": "^5.0.0",  // Social sharing components
    // Note: Optional, can implement custom share buttons

    // ============================================
    // PHASE 5: BUILD TOOLS
    // ============================================
    "html2canvas": "^1.4.0",  // Screenshot generation
    "jspdf": "^2.5.0",  // Client-side PDF generation (optional)

    // ============================================
    // PHASE 6: RICH TEXT EDITOR
    // ============================================
    "@tiptap/react": "^2.1.0",  // Rich text editor (for custom analyses)
    "@tiptap/starter-kit": "^2.1.0",

    // ============================================
    // PHASE 6: CHARTS & VISUALIZATION
    // ============================================
    // (recharts already included from Phase 3)
    "d3": "^7.8.0",  // Optional: Advanced visualizations
  },
  "devDependencies": {
    "typescript": "^5.3.0",
    "@types/react": "^19.0.0",
    "@types/node": "^20.11.0",
    "eslint": "^8.56.0",
    "prettier": "^3.2.0",
    "@playwright/test": "^1.57.0",  // E2E testing
    "eslint-config-next": "^16.1.3"
  }
}
```

**Frontend Dependency Justification:**

| Dependency | Purpose | Why Chosen | Alternatives |
|------------|---------|------------|-------------|
| **@clerk/nextjs** | Authentication | Best Next.js integration, free tier | NextAuth (DIY), Auth0 (expensive) |
| **@tanstack/react-table** | Admin logs table | Feature-rich, headless UI | Material Table (bloated), Custom (time-consuming) |
| **react-share** | Social sharing | Pre-built share buttons | Custom implementation |
| **@tiptap/react** | Rich text editor | Modern, extensible, React-native | Slate (complex), Quill (jQuery), Draft.js (deprecated) |

---

## Environment Variables (Phase 4+)

### Backend Environment Variables

```bash
# backend/.env

# ============================================
# PHASE 1-3 (Existing)
# ============================================
DATABASE_URL=postgresql+asyncpg://user:pass@localhost:5433/startinsight
REDIS_URL=redis://localhost:6379
FIRECRAWL_API_KEY=fc-***
REDDIT_CLIENT_ID=***
REDDIT_CLIENT_SECRET=***
REDDIT_USERNAME=***
ANTHROPIC_API_KEY=sk-ant-***
OPENAI_API_KEY=sk-***
API_HOST=0.0.0.0
API_PORT=8000

# ============================================
# PHASE 4.1: CLERK AUTHENTICATION
# ============================================
CLERK_SECRET_KEY=sk_test_...  # Backend JWT verification key
CLERK_FRONTEND_API=clerk.startinsight.app  # Clerk domain

# ============================================
# PHASE 6.2: STRIPE PAYMENTS
# ============================================
STRIPE_SECRET_KEY=sk_test_...  # Test key for development
STRIPE_WEBHOOK_SECRET=whsec_...  # For webhook verification
STRIPE_PUBLISHABLE_KEY=pk_test_...  # Frontend key (NOT secret)

# ============================================
# PHASE 6.3: EMAIL (RESEND)
# ============================================
RESEND_API_KEY=re_...  # Resend API key
RESEND_FROM_EMAIL=noreply@startinsight.app  # Verified sender

# ============================================
# PHASE 7.1: TWITTER/X API
# ============================================
TWITTER_BEARER_TOKEN=...  # Twitter API v2 bearer token
# OR (for twikit)
TWITTER_USERNAME=...
TWITTER_PASSWORD=...

# ============================================
# MONITORING & ALERTS
# ============================================
SENTRY_DSN=https://...  # Error tracking (optional)
SLACK_WEBHOOK_URL=https://hooks.slack.com/...  # Admin alerts
```

### Frontend Environment Variables

```bash
# frontend/.env.local

# ============================================
# PHASE 1-3 (Existing)
# ============================================
NEXT_PUBLIC_API_URL=http://localhost:8000

# ============================================
# PHASE 4.1: CLERK AUTHENTICATION
# ============================================
NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY=pk_test_...
CLERK_SECRET_KEY=sk_test_...
NEXT_PUBLIC_CLERK_SIGN_IN_URL=/sign-in
NEXT_PUBLIC_CLERK_SIGN_UP_URL=/sign-up
NEXT_PUBLIC_CLERK_SIGN_IN_FORCE_REDIRECT_URL=/workspace
NEXT_PUBLIC_CLERK_SIGN_UP_FORCE_REDIRECT_URL=/workspace

# ============================================
# PHASE 6.2: STRIPE PAYMENTS (Frontend)
# ============================================
NEXT_PUBLIC_STRIPE_PUBLISHABLE_KEY=pk_test_...

# ============================================
# ANALYTICS (Optional)
# ============================================
NEXT_PUBLIC_GA_MEASUREMENT_ID=G-...  # Google Analytics
NEXT_PUBLIC_POSTHOG_KEY=phc_...  # PostHog analytics
```

---

## Technology Decisions & Rationale

### Authentication: Clerk vs Alternatives

**Decision: Clerk ✅**

**Comparison:**

| Feature | Clerk | Auth0 | NextAuth |
|---------|-------|-------|----------|
| **Free Tier** | 10K MAU | 7K MAU (then $35/mo) | Unlimited |
| **Next.js Integration** | Excellent (native) | Good | Excellent |
| **JWT Support** | Built-in | Built-in | Manual |
| **Social Logins** | 20+ providers | 30+ providers | OAuth 2.0 |
| **Setup Time** | 15 minutes | 30 minutes | 60 minutes |
| **Cost at 50K users** | $125/mo | $240/mo | $0 (self-hosted) |
| **Security** | Managed | Managed | Self-managed |

**Why Clerk:**
1. Best Next.js developer experience
2. Generous free tier (10K MAU vs 7K for Auth0)
3. No server setup needed (vs NextAuth self-hosting)
4. Industry-standard JWT security
5. Built-in user management UI

**When to Migrate:** If users exceed 100K MAU, consider self-hosted solution (cost: $1,250/mo with Clerk vs $0 with self-hosted)

---

### Real-Time Updates: SSE vs WebSocket

**Decision: Server-Sent Events (SSE) ✅**

**Comparison:**

| Feature | SSE | WebSocket | Polling |
|---------|-----|-----------|---------|
| **Direction** | Server → Client | Bidirectional | Request → Response |
| **Protocol** | HTTP | WebSocket | HTTP |
| **Complexity** | Low | High | Very Low |
| **Browser Support** | All modern | All modern | All |
| **Auto-Reconnect** | Yes | No (manual) | N/A |
| **Latency** | ~100ms | <50ms | >1000ms |
| **Use Case** | Admin dashboard | Chat, gaming | Low-frequency updates |

**Why SSE:**
1. Admin portal is read-heavy (metrics, logs)
2. Simple HTTP-based implementation
3. Built-in browser reconnection
4. Commands use regular POST (no need for bidirectional)

**When to Use WebSocket:** If we add real-time chat or collaborative editing (Phase 7+)

---

### PDF Generation: ReportLab vs WeasyPrint

**Decision: ReportLab ✅ (primary), WeasyPrint (fallback)**

**Comparison:**

| Feature | ReportLab | WeasyPrint | PyPDF2 |
|---------|-----------|------------|--------|
| **API Style** | Programmatic (Python) | HTML → PDF | Merge only |
| **Quality** | Excellent | Good | N/A |
| **Flexibility** | High (full control) | Medium (CSS limits) | N/A |
| **Learning Curve** | Steep | Easy (HTML/CSS) | Easy |
| **Performance** | Fast | Medium | Fast |
| **Dependencies** | Minimal | Heavy (cairo, pango) | Minimal |

**Implementation Strategy:**
1. Use ReportLab for professional reports (insights, analyses)
2. Use WeasyPrint for HTML-based exports (landing pages, email templates)
3. Both in dependencies, choose based on use case

---

### Email Service: Resend vs SendGrid

**Decision: Resend ✅**

**Comparison:**

| Feature | Resend | SendGrid | Mailgun |
|---------|--------|----------|---------|
| **Free Tier** | 3K emails/month | 100 emails/day | 5K emails/month |
| **Pricing** | $20/mo (50K emails) | $20/mo (100K emails) | $35/mo (50K emails) |
| **API Simplicity** | Excellent | Complex | Good |
| **Templates** | React components | HTML | HTML |
| **Deliverability** | Excellent | Excellent | Good |
| **Setup Time** | 5 minutes | 20 minutes | 15 minutes |

**Why Resend:**
1. Modern API (send emails with React components)
2. Generous free tier (3K/month vs 100/day for SendGrid)
3. Better developer experience
4. Excellent deliverability rates

**Migration Path:** If volume exceeds 500K emails/month, SendGrid becomes cheaper ($89/mo vs Resend $240/mo)

---

## Cost Analysis (Phase 4+)

### Monthly Infrastructure Costs

**Baseline (v0.1 - 100 users, 50 insights/day):**
- Database (Neon): $0 (Free tier)
- Redis (Upstash): $0 (Free tier)
- Backend (Railway): $5/mo (Hobby plan)
- Frontend (Vercel): $0 (Free tier)
- LLM API (Anthropic): $75/mo (50 insights × $0.05 × 30 days)
- **Total: $80/month**

**With Phase 4+ (1,000 users, 50 insights/day + features):**
- Database (Neon): $19/mo (Pro tier - increased storage)
- Redis (Upstash): $10/mo (increased cache usage)
- Backend (Railway): $20/mo (Pro plan - more resources)
- Frontend (Vercel): $20/mo (Pro tier - custom domain)
- LLM API (Anthropic): $75/mo (same insight volume)
- Clerk (Auth): $0 (within 10K MAU free tier)
- Resend (Email): $0 (within 3K emails/month free tier)
- Stripe (Payments): 2.9% + $0.30 per transaction (variable)
- **Total: $144/month** (fixed) + transaction fees

**At Scale (10,000 users, 200 insights/day):**
- Database: $69/mo (Neon Scale tier)
- Redis: $40/mo (Upstash Pro)
- Backend: $100/mo (Railway Pro+ or dedicated server)
- Frontend: $20/mo (Vercel Pro)
- LLM API: $300/mo (200 insights × $0.05 × 30 days)
- Clerk: $125/mo (10K MAU exceeded, now 50K MAU)
- Resend: $20/mo (50K emails/month)
- **Total: $674/month**

**Revenue Projections (at 10,000 users):**
- Free: 9,000 users × $0 = $0
- Starter ($19): 500 users × $19 = $9,500/mo
- Pro ($49): 400 users × $49 = $19,600/mo
- Enterprise ($299): 100 users × $299 = $29,900/mo
- **Total Revenue: $59,000/month**
- **Profit Margin: $58,326/month (98.6%)**

---

## Version Pinning Strategy

### Semantic Versioning Policy

```
Major.Minor.Patch (e.g., 2.5.3)

- Major: Breaking changes (manual upgrade required)
- Minor: New features (backward compatible)
- Patch: Bug fixes (automatic updates)
```

**Pinning Strategy:**

```toml
# Critical dependencies (pin major version)
fastapi = "^0.109.0"  # Allow minor/patch updates
clerk-backend-api = "^2.0.0"  # Stay on v2.x

# Less critical (allow minor updates)
pydantic = ">=2.5.0,<3.0.0"

# Lock for reproducible builds
alembic = "==1.13.0"  # Exact version for migrations
```

**Update Policy:**
1. **Weekly:** Check for security updates (patch versions)
2. **Monthly:** Review minor version updates
3. **Quarterly:** Major version upgrade planning
4. **Before production:** Lock all versions in `pyproject.toml`

### Dependency Update Workflow

```bash
# Check for outdated packages
cd backend
uv pip list --outdated

# Update to latest compatible versions
uv pip install --upgrade fastapi

# Test thoroughly before deploying
pytest
ruff check .

# Lock dependencies
uv pip freeze > requirements-lock.txt
```

---

## Development vs Production Dependencies

### Backend

```toml
# Development only
[project.optional-dependencies]
dev = [
    "pytest>=7.4.0",        # Testing framework
    "pytest-asyncio>=0.21.0",  # Async test support
    "pytest-cov>=4.1.0",    # Coverage reporting
    "ruff>=0.1.0",          # Linting & formatting
    "mypy>=1.7.0",          # Type checking
    "ipdb>=0.13.0",         # Debugging
    "faker>=20.0.0",        # Test data generation
]

# Production only (not in dev)
[project]
dependencies = [
    "gunicorn>=21.0.0",     # Production WSGI server
    "sentry-sdk>=1.40.0",   # Error tracking
]
```

### Frontend

```json
{
  "devDependencies": {
    // Development tools
    "@playwright/test": "^1.57.0",  // E2E testing
    "eslint": "^8.56.0",            // Linting
    "prettier": "^3.2.0",           // Code formatting
    "@types/node": "^20.11.0",      // TypeScript types

    // Build tools (used in production builds)
    "typescript": "^5.3.0",
    "tailwindcss": "^4.0.0"
  }
}
```

---

## Security Dependencies

### Dependency Scanning

**Tools:**

1. **npm audit** (Frontend):
   ```bash
   cd frontend
   npm audit                    # Check for vulnerabilities
   npm audit fix                # Auto-fix if possible
   npm audit fix --force        # Force fix (breaking changes)
   ```

2. **Safety** (Backend):
   ```bash
   cd backend
   pip install safety
   safety check                 # Scan for known vulnerabilities
   ```

3. **Dependabot** (GitHub):
   ```yaml
   # .github/dependabot.yml
   version: 2
   updates:
     - package-ecosystem: "pip"
       directory: "/backend"
       schedule:
         interval: "weekly"
       open-pull-requests-limit: 5

     - package-ecosystem: "npm"
       directory: "/frontend"
       schedule:
         interval: "weekly"
       open-pull-requests-limit: 5
   ```

### Known Vulnerabilities Policy

**Severity Levels:**
- **Critical:** Fix immediately (same day)
- **High:** Fix within 3 days
- **Medium:** Fix within 2 weeks
- **Low:** Fix in next sprint

**Process:**
1. Automated scan runs daily (GitHub Actions)
2. Dependabot creates PR for security updates
3. Review and test PR in staging
4. Deploy to production after validation

---

## Future Dependencies (Phase 5-7)

### Phase 5: Advanced Analysis

```toml
# Market research tools
"langsmith>=0.0.70"  # LLM monitoring (optional)
"instructor>=0.4.0"  # Structured LLM outputs (alternative to PydanticAI)

# Web automation
"playwright>=1.40.0"  # Browser automation for complex scraping
```

### Phase 6: Engagement Features

```toml
# WebSocket support (if needed beyond SSE)
"websockets>=12.0"

# Advanced email templates
"premailer>=3.10.0"  # Inline CSS for email compatibility

# SMS notifications (optional)
"twilio>=8.10.0"
```

### Phase 7: Data Source Expansion

```toml
# Additional scrapers
"beautifulsoup4>=4.12.0"  # HTML parsing
"selenium>=4.15.0"  # Browser automation (fallback for Playwright)
"feedparser>=6.0.0"  # RSS feed parsing

# Patent database access
"epo-ops>=3.4.0"  # European Patent Office API
```

---

## Conclusion

This document comprehensively covers all technology additions for Phase 4+ development. Key highlights:

1. **Minimal dependency bloat:** Only 10 new backend dependencies, 5 new frontend packages
2. **Cost-effective choices:** Prioritized free tiers and lower-cost options
3. **Security-first:** Automated scanning and update policies
4. **Scalability path:** Clear migration strategies for higher usage tiers

**Total Dependencies:**
- Backend: 28 packages (18 Phase 1-3 + 10 Phase 4+)
- Frontend: 20 packages (15 Phase 1-3 + 5 Phase 4+)

**Next Steps:**
1. Install Phase 4.1 dependencies (Clerk)
2. Configure environment variables
3. Set up Dependabot for automated security updates

---

**Document Version:** 2.0
**Last Updated:** 2026-01-24
**Author:** Lead Architect (Claude)
**Related Documents:** `tech-stack.md`, `implementation-plan-phase4-detailed.md`
