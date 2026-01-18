# StartInsight Frontend

AI-powered startup market intelligence dashboard built with Next.js 16, TypeScript, and Tailwind CSS.

---

## 🚀 Quick Start

```bash
# Install dependencies
npm install

# Set up environment variables
cp .env.local.example .env.local
# Edit .env.local and add your backend API URL

# Run development server
npm run dev

# Open http://localhost:3000
```

---

## 📋 Table of Contents

- [Features](#features)
- [Tech Stack](#tech-stack)
- [Project Structure](#project-structure)
- [Setup Instructions](#setup-instructions)
- [Environment Variables](#environment-variables)
- [Development](#development)
- [Testing](#testing)
- [Deployment](#deployment)
- [API Integration](#api-integration)
- [Troubleshooting](#troubleshooting)

---

## ✨ Features

### Core Functionality
- 📊 **Daily Top Insights:** View the top 5 AI-analyzed startup opportunities
- 🔍 **Advanced Filtering:** Filter by source, relevance score, and keyword search
- 📈 **Trend Visualization:** Interactive charts for Google Trends data (Recharts)
- 💡 **Insight Details:** Comprehensive view with competitor analysis
- 🔗 **Shareable Links:** URL-based filter state for easy sharing

### UI/UX
- 🌓 **Dark Mode:** Toggle between light and dark themes with persistence
- 📱 **Responsive Design:** Mobile-first design (1/2/3 column grids)
- ⚡ **Loading States:** Skeleton loaders for better perceived performance
- 🛡️ **Error Boundaries:** Graceful error handling at multiple levels
- ♿ **Accessible:** Semantic HTML, ARIA labels, keyboard navigation

### Technical
- 🔄 **Real-time Updates:** React Query with automatic refetching
- 🎯 **Type Safety:** Full TypeScript with Zod runtime validation
- 🎨 **Modern UI:** shadcn/ui components with Tailwind CSS v4
- 🧪 **E2E Testing:** Playwright tests (47 scenarios, 5 browsers)
- 🚢 **Production Ready:** Optimized Next.js build with SSR/SSG

---

## 🛠 Tech Stack

### Framework & Core
- **Next.js 16.1.3** - React framework with App Router and Turbopack
- **React 19.2.3** - UI library
- **TypeScript 5.x** - Type safety
- **Tailwind CSS v4** - Utility-first CSS framework

### UI Components
- **shadcn/ui** - Radix UI component library
- **lucide-react** - Icon library
- **Recharts** - Data visualization charts

### Data Fetching & State
- **TanStack Query (React Query v5)** - Server state management
- **axios** - HTTP client
- **zod** - Runtime validation

### Development & Testing
- **Playwright** - E2E testing framework
- **ESLint** - Code linting
- **TypeScript** - Static type checking

---

## 📁 Project Structure

```
frontend/
├── app/                        # Next.js App Router pages
│   ├── layout.tsx             # Root layout with providers
│   ├── page.tsx               # Homepage (Daily Top 5)
│   ├── error.tsx              # Root error boundary
│   ├── global-error.tsx       # Global error boundary
│   ├── globals.css            # Global styles
│   ├── providers.tsx          # Client-side providers
│   └── insights/              # Insights pages
│       ├── page.tsx           # All Insights (with filters)
│       ├── error.tsx          # Insights error boundary
│       └── [id]/
│           └── page.tsx       # Insight Detail page
├── components/                 # React components
│   ├── ui/                    # shadcn/ui components
│   ├── Header.tsx             # Navigation header
│   ├── InsightCard.tsx        # Insight card component
│   ├── InsightFilters.tsx     # Filters sidebar
│   ├── trend-chart.tsx        # Recharts visualization
│   ├── theme-provider.tsx     # Dark mode provider
│   └── theme-toggle.tsx       # Dark mode toggle button
├── lib/                        # Utility libraries
│   ├── api.ts                 # API client functions
│   ├── types.ts               # TypeScript types & Zod schemas
│   ├── query-client.ts        # React Query config
│   └── utils.ts               # Utility functions
├── .env.local                 # Environment variables (not in git)
└── package.json               # Dependencies & scripts

Note: E2E tests moved to centralized ../tests/frontend/ directory
```

---

## 🔧 Setup Instructions

### Prerequisites
- **Node.js 18+** (v20.19.6 recommended)
- **npm 10+** (v10.8.2 recommended)
- **Backend API** running on http://localhost:8000

### Installation Steps

1. **Clone the repository**
   ```bash
   cd /path/to/StartInsight/frontend
   ```

2. **Install dependencies**
   ```bash
   npm install
   ```

3. **Set up environment variables**
   ```bash
   # Create .env.local file
   echo "NEXT_PUBLIC_API_URL=http://localhost:8000" > .env.local
   ```

4. **Verify backend is running**
   ```bash
   curl http://localhost:8000/health
   # Expected: {"status":"healthy","service":"StartInsight API"}
   ```

5. **Start development server**
   ```bash
   npm run dev
   ```

6. **Open browser**
   - Navigate to http://localhost:3000

---

## 🌍 Environment Variables

### `.env.local` (Local Development)

```env
NEXT_PUBLIC_API_URL=http://localhost:8000
```

### Production (Vercel)

Set in Vercel dashboard → Settings → Environment Variables:
```env
NEXT_PUBLIC_API_URL=https://your-backend.railway.app
```

---

## 💻 Development

### Available Scripts

```bash
npm run dev          # Development server
npm run build        # Production build
npm run start        # Start production server
npm run lint         # Run ESLint
npm run test         # Run Playwright tests
npm run test:ui      # Interactive test mode
npm run test:report  # Show test report
```

---

## 🧪 Testing

```bash
# Run all tests
npm run test

# Interactive mode
npm run test:ui

# Specific browser
npx playwright test --project=chromium

# Debug mode
npx playwright test --debug
```

**Test Coverage:** 47 E2E tests across 5 browser platforms

---

## 🚢 Deployment

### Deploy to Vercel

1. Connect GitHub repository to Vercel
2. Set root directory to `frontend/`
3. Add environment variable: `NEXT_PUBLIC_API_URL`
4. Deploy

See `../DEPLOYMENT.md` for detailed instructions.

---

## 🔌 API Integration

### API Client

```typescript
import { fetchInsights, fetchInsightById } from '@/lib/api';

// Fetch insights with filters
const insights = await fetchInsights({
  min_score: 0.7,
  source: 'reddit',
});

// Fetch single insight
const insight = await fetchInsightById('uuid');
```

### Endpoints

| Endpoint | Description |
|----------|-------------|
| `GET /api/insights` | List insights (filterable, paginated) |
| `GET /api/insights/{id}` | Get single insight |
| `GET /api/insights/daily-top` | Top 5 insights |
| `GET /health` | Health check |

---

## 🐛 Troubleshooting

### Network Error

**Problem:** Can't reach backend API

**Solution:**
```bash
# Check backend is running
curl http://localhost:8000/health

# Verify .env.local
cat .env.local

# Check CORS in backend
# CORS_ORIGINS should include http://localhost:3000
```

### Build Fails

**Problem:** TypeScript errors during build

**Solution:**
```bash
# Check for type errors
npx tsc --noEmit

# Fix imports and type definitions
```

### Tests Fail

**Problem:** Playwright tests not running

**Solution:**
```bash
# Install browsers
npx playwright install

# Ensure dev server is running
npm run dev

# Run in debug mode
npm run test:ui
```

---

## 📚 Resources

- **Next.js Docs:** https://nextjs.org/docs
- **Tailwind CSS:** https://tailwindcss.com/docs
- **shadcn/ui:** https://ui.shadcn.com
- **Playwright:** https://playwright.dev

---

## 🤝 Contributing

1. Create feature branch
2. Make changes
3. Run `npm run lint` and `npm run test`
4. Create pull request

---

**Built with ❤️ using Next.js, TypeScript, and Tailwind CSS**
