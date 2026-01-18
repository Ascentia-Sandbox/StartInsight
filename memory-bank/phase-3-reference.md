# Phase 3 Reference Guide: Frontend Implementation

**Quick Reference for Phase 3 (The "Presenter" - Frontend & Visualization)**

This document provides detailed, copy-paste-ready implementation instructions for Phase 3.
Created: 2026-01-18 | Version: 1.0

---

## Table of Contents
1. [Phase 3 Overview](#phase-3-overview)
2. [Phase 3.1: Next.js Project Setup](#phase-31-nextjs-project-setup)
3. [Phase 3.2: API Client & Data Fetching](#phase-32-api-client--data-fetching)
4. [Phase 3.3: Insights Dashboard UI](#phase-33-insights-dashboard-ui)
5. [Phase 3.4: Filtering & Search](#phase-34-filtering--search)
6. [Phase 3.5: Polish & Deploy](#phase-35-polish--deploy)
7. [Testing Requirements](#testing-requirements)
8. [Success Criteria](#success-criteria)

---

## Phase 3 Overview

**Goal**: Build a modern Next.js frontend to display AI-analyzed startup insights with filtering, search, and an intuitive dashboard.

**Tech Stack**:
- **Framework**: Next.js 14+ (App Router)
- **Language**: TypeScript
- **Styling**: Tailwind CSS
- **Components**: shadcn/ui (Radix UI primitives)
- **Data Fetching**: TanStack Query (React Query)
- **Validation**: Zod
- **HTTP Client**: Axios
- **Date Formatting**: date-fns
- **Charts**: Recharts

**Architecture**:
```
frontend/
├── app/                  # Next.js 14 App Router
│   ├── layout.tsx       # Root layout
│   ├── page.tsx         # Homepage (daily top insights)
│   └── insights/
│       ├── page.tsx     # All insights (with filters)
│       └── [id]/
│           └── page.tsx # Insight detail page
├── components/
│   ├── ui/              # shadcn/ui components
│   ├── InsightCard.tsx  # Reusable insight card
│   ├── InsightFilters.tsx
│   ├── InsightDetail.tsx
│   └── DailyTopHeader.tsx
├── lib/
│   ├── api.ts           # API client functions
│   ├── types.ts         # TypeScript types
│   └── utils.ts         # Utility functions
├── public/              # Static assets
└── .env.local           # Environment variables
```

---

## Phase 3.1: Next.js Project Setup

### Step 1: Initialize Next.js Project

```bash
# From project root
npx create-next-app@latest frontend --typescript --tailwind --app --eslint --src-dir=false --import-alias="@/*"

# Answer prompts:
# ✔ Would you like to use TypeScript? Yes
# ✔ Would you like to use ESLint? Yes
# ✔ Would you like to use Tailwind CSS? Yes
# ✔ Would you like to use `src/` directory? No
# ✔ Would you like to use App Router? Yes
# ✔ Would you like to customize the default import alias (@/*)? No
```

### Step 2: Install Core Dependencies

```bash
cd frontend

# Data fetching and state management
npm install @tanstack/react-query axios zod

# Date formatting
npm install date-fns

# Charts (optional, for Phase 3.5)
npm install recharts

# shadcn/ui setup (interactive CLI)
npx shadcn-ui@latest init

# Answer prompts:
# ✔ Which style would you like to use? › Default
# ✔ Which color would you like to use as base color? › Slate
# ✔ Would you like to use CSS variables for colors? › Yes
```

### Step 3: Install shadcn/ui Components

```bash
# Install required components
npx shadcn-ui@latest add button
npx shadcn-ui@latest add card
npx shadcn-ui@latest add badge
npx shadcn-ui@latest add skeleton
npx shadcn-ui@latest add select
npx shadcn-ui@latest add input
npx shadcn-ui@latest add dialog
npx shadcn-ui@latest add separator
```

### Step 4: Configure Environment Variables

Create `frontend/.env.local`:

```env
# Backend API URL (local development)
NEXT_PUBLIC_API_URL=http://localhost:8000

# Production URL (update when deploying)
# NEXT_PUBLIC_API_URL=https://your-backend.railway.app
```

### Step 5: Create TypeScript Types

Create `frontend/lib/types.ts`:

```typescript
import { z } from 'zod';

// Zod schemas for runtime validation
export const CompetitorSchema = z.object({
  name: z.string(),
  url: z.string().url(),
  description: z.string(),
  market_position: z.enum(['Small', 'Medium', 'Large']).nullable().optional(),
});

export const RawSignalSummarySchema = z.object({
  id: z.string().uuid(),
  source: z.string(),
  url: z.string().url(),
  created_at: z.string().datetime(),
});

export const InsightSchema = z.object({
  id: z.string().uuid(),
  raw_signal_id: z.string().uuid(),
  problem_statement: z.string(),
  proposed_solution: z.string(),
  market_size_estimate: z.enum(['Small', 'Medium', 'Large']),
  relevance_score: z.number().min(0).max(1),
  competitor_analysis: z.array(CompetitorSchema),
  created_at: z.string().datetime(),
  raw_signal: RawSignalSummarySchema.optional(),
});

export const InsightListResponseSchema = z.object({
  insights: z.array(InsightSchema),
  total: z.number(),
  limit: z.number(),
  offset: z.number(),
});

// TypeScript types derived from Zod schemas
export type Competitor = z.infer<typeof CompetitorSchema>;
export type RawSignalSummary = z.infer<typeof RawSignalSummarySchema>;
export type Insight = z.infer<typeof InsightSchema>;
export type InsightListResponse = z.infer<typeof InsightListResponseSchema>;

// API query parameters
export interface FetchInsightsParams {
  min_score?: number;
  source?: string;
  limit?: number;
  offset?: number;
}
```

### Step 6: Verify Setup

```bash
# Start development server
npm run dev

# Open http://localhost:3000
# Should see default Next.js welcome page
```

**Success Criteria**:
- ✓ Next.js runs on http://localhost:3000
- ✓ TypeScript compiles without errors
- ✓ Tailwind CSS styles are applied
- ✓ shadcn/ui components directory exists (`components/ui/`)
- ✓ Environment variables load correctly

---

## Phase 3.2: API Client & Data Fetching

### Step 1: Create API Client

Create `frontend/lib/api.ts`:

```typescript
import axios from 'axios';
import {
  InsightSchema,
  InsightListResponseSchema,
  type Insight,
  type InsightListResponse,
  type FetchInsightsParams,
} from './types';

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

const apiClient = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
  timeout: 10000,
});

/**
 * Fetch paginated list of insights with optional filters
 */
export async function fetchInsights(
  params: FetchInsightsParams = {}
): Promise<InsightListResponse> {
  const { data } = await apiClient.get('/api/insights', { params });
  return InsightListResponseSchema.parse(data);
}

/**
 * Fetch single insight by ID
 */
export async function fetchInsightById(id: string): Promise<Insight> {
  const { data } = await apiClient.get(`/api/insights/${id}`);
  return InsightSchema.parse(data);
}

/**
 * Fetch daily top 5 insights
 */
export async function fetchDailyTop(limit: number = 5): Promise<Insight[]> {
  const { data } = await apiClient.get('/api/insights/daily-top', {
    params: { limit },
  });
  return z.array(InsightSchema).parse(data);
}

/**
 * Check API health
 */
export async function checkHealth(): Promise<{ status: string; version: string }> {
  const { data } = await apiClient.get('/health');
  return data;
}
```

### Step 2: Configure React Query

Create `frontend/lib/query-client.ts`:

```typescript
import { QueryClient } from '@tanstack/react-query';

export const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 60 * 1000, // 1 minute
      retry: 2,
      refetchOnWindowFocus: false,
    },
  },
});
```

### Step 3: Add Query Provider to Root Layout

Update `frontend/app/layout.tsx`:

```typescript
import type { Metadata } from 'next';
import { Inter } from 'next/font/google';
import './globals.css';
import { Providers } from './providers';

const inter = Inter({ subsets: ['latin'] });

export const metadata: Metadata = {
  title: 'StartInsight - AI-Powered Startup Market Intelligence',
  description: 'Discover emerging startup opportunities through AI-analyzed market signals',
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <body className={inter.className}>
        <Providers>{children}</Providers>
      </body>
    </html>
  );
}
```

Create `frontend/app/providers.tsx`:

```typescript
'use client';

import { QueryClientProvider } from '@tanstack/react-query';
import { ReactQueryDevtools } from '@tanstack/react-query-devtools';
import { queryClient } from '@/lib/query-client';

export function Providers({ children }: { children: React.ReactNode }) {
  return (
    <QueryClientProvider client={queryClient}>
      {children}
      <ReactQueryDevtools initialIsOpen={false} />
    </QueryClientProvider>
  );
}
```

**Success Criteria**:
- ✓ API client functions are type-safe
- ✓ Zod validation catches invalid API responses
- ✓ React Query is configured with proper caching
- ✓ No TypeScript errors

---

## Phase 3.3: Insights Dashboard UI

### Step 1: Create InsightCard Component

Create `frontend/components/InsightCard.tsx`:

```typescript
import { Card, CardContent, CardFooter, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import Link from 'next/link';
import { formatDistanceToNow } from 'date-fns';
import type { Insight } from '@/lib/types';

interface InsightCardProps {
  insight: Insight;
}

export function InsightCard({ insight }: InsightCardProps) {
  const marketSizeColor = {
    Small: 'bg-yellow-100 text-yellow-800 dark:bg-yellow-900 dark:text-yellow-300',
    Medium: 'bg-blue-100 text-blue-800 dark:bg-blue-900 dark:text-blue-300',
    Large: 'bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-300',
  };

  const relevanceStars = Math.round(insight.relevance_score * 5);

  return (
    <Card className="h-full flex flex-col hover:shadow-lg transition-shadow">
      <CardHeader>
        <div className="flex items-start justify-between gap-2">
          <CardTitle className="text-lg line-clamp-2">
            {insight.problem_statement}
          </CardTitle>
          <Badge className={marketSizeColor[insight.market_size_estimate]}>
            {insight.market_size_estimate}
          </Badge>
        </div>
      </CardHeader>

      <CardContent className="flex-1">
        <p className="text-sm text-muted-foreground line-clamp-3 mb-4">
          {insight.proposed_solution}
        </p>

        <div className="flex items-center gap-2 text-sm">
          <span className="font-medium">Relevance:</span>
          <div className="flex">
            {'⭐'.repeat(relevanceStars)}
            {'☆'.repeat(5 - relevanceStars)}
          </div>
          <span className="text-muted-foreground">
            ({insight.relevance_score.toFixed(2)})
          </span>
        </div>

        {insight.competitor_analysis && insight.competitor_analysis.length > 0 && (
          <div className="mt-3 text-sm text-muted-foreground">
            {insight.competitor_analysis.length} competitor{insight.competitor_analysis.length > 1 ? 's' : ''} identified
          </div>
        )}
      </CardContent>

      <CardFooter className="flex justify-between items-center">
        <span className="text-xs text-muted-foreground">
          {formatDistanceToNow(new Date(insight.created_at), { addSuffix: true })}
        </span>
        <Button asChild size="sm">
          <Link href={`/insights/${insight.id}`}>
            View Details
          </Link>
        </Button>
      </CardFooter>
    </Card>
  );
}
```

### Step 2: Create Homepage with Daily Top Insights

Update `frontend/app/page.tsx`:

```typescript
'use client';

import { useQuery } from '@tanstack/react-query';
import { fetchDailyTop } from '@/lib/api';
import { InsightCard } from '@/components/InsightCard';
import { Skeleton } from '@/components/ui/skeleton';

export default function HomePage() {
  const { data: insights, isLoading, error } = useQuery({
    queryKey: ['daily-top'],
    queryFn: () => fetchDailyTop(5),
  });

  if (error) {
    return (
      <div className="container mx-auto px-4 py-8">
        <div className="text-center">
          <h2 className="text-2xl font-bold text-red-600">Error loading insights</h2>
          <p className="text-muted-foreground mt-2">
            {error instanceof Error ? error.message : 'An error occurred'}
          </p>
        </div>
      </div>
    );
  }

  return (
    <div className="container mx-auto px-4 py-8">
      <header className="mb-8">
        <h1 className="text-4xl font-bold mb-2">StartInsight</h1>
        <p className="text-xl text-muted-foreground">
          Top 5 Insights of the Day
        </p>
        <p className="text-sm text-muted-foreground mt-1">
          AI-powered startup market intelligence
        </p>
      </header>

      {isLoading ? (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {[...Array(5)].map((_, i) => (
            <Skeleton key={i} className="h-64" />
          ))}
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {insights?.map((insight) => (
            <InsightCard key={insight.id} insight={insight} />
          ))}
        </div>
      )}

      {!isLoading && insights && insights.length === 0 && (
        <div className="text-center py-12">
          <p className="text-muted-foreground">
            No insights available yet. Run the analysis task to generate insights.
          </p>
        </div>
      )}
    </div>
  );
}
```

**Success Criteria**:
- ✓ Homepage displays top 5 daily insights
- ✓ InsightCard component shows all key data
- ✓ Loading skeletons appear while fetching
- ✓ Error states are handled gracefully
- ✓ Responsive grid layout works on mobile/desktop

---

## Phase 3.4: Filtering & Search

### Step 1: Create Filters Component

Create `frontend/components/InsightFilters.tsx`:

```typescript
'use client';

import { useSearchParams, useRouter, usePathname } from 'next/navigation';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Input } from '@/components/ui/input';
import { Button } from '@/components/ui/button';
import { X } from 'lucide-react';

export function InsightFilters() {
  const searchParams = useSearchParams();
  const router = useRouter();
  const pathname = usePathname();

  const updateFilter = (key: string, value: string | null) => {
    const params = new URLSearchParams(searchParams.toString());
    if (value) {
      params.set(key, value);
    } else {
      params.delete(key);
    }
    router.push(`${pathname}?${params.toString()}`);
  };

  const clearFilters = () => {
    router.push(pathname);
  };

  const hasFilters = searchParams.toString().length > 0;

  return (
    <div className="space-y-4 p-4 border rounded-lg">
      <div className="flex items-center justify-between">
        <h3 className="font-semibold">Filters</h3>
        {hasFilters && (
          <Button variant="ghost" size="sm" onClick={clearFilters}>
            <X className="h-4 w-4 mr-1" />
            Clear
          </Button>
        )}
      </div>

      <div className="space-y-3">
        {/* Source Filter */}
        <div>
          <label className="text-sm font-medium mb-1 block">Source</label>
          <Select
            value={searchParams.get('source') || 'all'}
            onValueChange={(value) => updateFilter('source', value === 'all' ? null : value)}
          >
            <SelectTrigger>
              <SelectValue placeholder="All sources" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="all">All sources</SelectItem>
              <SelectItem value="reddit">Reddit</SelectItem>
              <SelectItem value="product_hunt">Product Hunt</SelectItem>
              <SelectItem value="google_trends">Google Trends</SelectItem>
            </SelectContent>
          </Select>
        </div>

        {/* Min Score Filter */}
        <div>
          <label className="text-sm font-medium mb-1 block">Minimum Relevance</label>
          <Select
            value={searchParams.get('min_score') || '0'}
            onValueChange={(value) => updateFilter('min_score', value === '0' ? null : value)}
          >
            <SelectTrigger>
              <SelectValue placeholder="Any score" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="0">Any score</SelectItem>
              <SelectItem value="0.5">0.5+ (Moderate)</SelectItem>
              <SelectItem value="0.7">0.7+ (Good)</SelectItem>
              <SelectItem value="0.9">0.9+ (Excellent)</SelectItem>
            </SelectContent>
          </Select>
        </div>

        {/* Search */}
        <div>
          <label className="text-sm font-medium mb-1 block">Search</label>
          <Input
            placeholder="Search insights..."
            defaultValue={searchParams.get('search') || ''}
            onChange={(e) => {
              const value = e.target.value;
              // Debounce search
              setTimeout(() => updateFilter('search', value || null), 500);
            }}
          />
        </div>
      </div>
    </div>
  );
}
```

### Step 2: Create All Insights Page with Filters

Create `frontend/app/insights/page.tsx`:

```typescript
'use client';

import { useQuery } from '@tanstack/react-query';
import { useSearchParams } from 'next/navigation';
import { fetchInsights } from '@/lib/api';
import { InsightCard } from '@/components/InsightCard';
import { InsightFilters } from '@/components/InsightFilters';
import { Skeleton } from '@/components/ui/skeleton';
import { Button } from '@/components/ui/button';

export default function AllInsightsPage() {
  const searchParams = useSearchParams();

  const params = {
    min_score: searchParams.get('min_score') ? parseFloat(searchParams.get('min_score')!) : undefined,
    source: searchParams.get('source') || undefined,
    limit: 20,
    offset: 0,
  };

  const { data, isLoading, error } = useQuery({
    queryKey: ['insights', searchParams.toString()],
    queryFn: () => fetchInsights(params),
  });

  return (
    <div className="container mx-auto px-4 py-8">
      <header className="mb-8">
        <h1 className="text-3xl font-bold">All Insights</h1>
        <p className="text-muted-foreground">
          {data?.total ? `${data.total} insights found` : 'Browse all insights'}
        </p>
      </header>

      <div className="grid grid-cols-1 lg:grid-cols-4 gap-6">
        {/* Filters Sidebar */}
        <div className="lg:col-span-1">
          <InsightFilters />
        </div>

        {/* Insights Grid */}
        <div className="lg:col-span-3">
          {isLoading ? (
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              {[...Array(6)].map((_, i) => (
                <Skeleton key={i} className="h-64" />
              ))}
            </div>
          ) : error ? (
            <div className="text-center py-12">
              <p className="text-red-600">Error loading insights</p>
            </div>
          ) : data && data.insights.length > 0 ? (
            <>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                {data.insights.map((insight) => (
                  <InsightCard key={insight.id} insight={insight} />
                ))}
              </div>

              {/* Pagination (future enhancement) */}
              {data.total > data.limit && (
                <div className="mt-8 flex justify-center">
                  <Button variant="outline">Load More</Button>
                </div>
              )}
            </>
          ) : (
            <div className="text-center py-12">
              <p className="text-muted-foreground">
                No insights match your filters. Try adjusting your criteria.
              </p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
```

**Success Criteria**:
- ✓ Filters update URL search params
- ✓ Back/forward browser buttons work
- ✓ Filter state persists on page refresh
- ✓ Insights update when filters change
- ✓ Clear filters button works

---

## Phase 3.5: Polish & Deploy

### Step 1: Create Insight Detail Page

Create `frontend/app/insights/[id]/page.tsx`:

```typescript
import { Suspense } from 'react';
import { notFound } from 'next/navigation';
import { fetchInsightById } from '@/lib/api';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Separator } from '@/components/ui/separator';
import { Skeleton } from '@/components/ui/skeleton';
import { formatDistanceToNow } from 'date-fns';

async function InsightDetailContent({ id }: { id: string }) {
  let insight;

  try {
    insight = await fetchInsightById(id);
  } catch (error) {
    notFound();
  }

  const marketSizeColor = {
    Small: 'bg-yellow-100 text-yellow-800',
    Medium: 'bg-blue-100 text-blue-800',
    Large: 'bg-green-100 text-green-800',
  };

  return (
    <div className="container mx-auto px-4 py-8 max-w-4xl">
      <Card>
        <CardHeader>
          <div className="flex items-start justify-between gap-4">
            <div className="flex-1">
              <CardTitle className="text-2xl mb-2">
                {insight.problem_statement}
              </CardTitle>
              <p className="text-sm text-muted-foreground">
                {formatDistanceToNow(new Date(insight.created_at), { addSuffix: true })}
              </p>
            </div>
            <Badge className={marketSizeColor[insight.market_size_estimate]}>
              {insight.market_size_estimate} Market
            </Badge>
          </div>
        </CardHeader>

        <CardContent className="space-y-6">
          {/* Proposed Solution */}
          <div>
            <h3 className="font-semibold mb-2">Proposed Solution</h3>
            <p className="text-muted-foreground">{insight.proposed_solution}</p>
          </div>

          <Separator />

          {/* Relevance Score */}
          <div>
            <h3 className="font-semibold mb-2">Relevance Score</h3>
            <div className="flex items-center gap-2">
              <div className="text-2xl">
                {'⭐'.repeat(Math.round(insight.relevance_score * 5))}
              </div>
              <span className="text-muted-foreground">
                {insight.relevance_score.toFixed(2)} / 1.00
              </span>
            </div>
          </div>

          {/* Competitors */}
          {insight.competitor_analysis && insight.competitor_analysis.length > 0 && (
            <>
              <Separator />
              <div>
                <h3 className="font-semibold mb-3">Competitor Analysis</h3>
                <div className="space-y-3">
                  {insight.competitor_analysis.map((competitor, idx) => (
                    <div key={idx} className="border rounded-lg p-4">
                      <div className="flex items-start justify-between">
                        <div className="flex-1">
                          <h4 className="font-medium">{competitor.name}</h4>
                          <p className="text-sm text-muted-foreground mt-1">
                            {competitor.description}
                          </p>
                          <a
                            href={competitor.url}
                            target="_blank"
                            rel="noopener noreferrer"
                            className="text-sm text-blue-600 hover:underline mt-2 inline-block"
                          >
                            Visit website →
                          </a>
                        </div>
                        {competitor.market_position && (
                          <Badge variant="outline">
                            {competitor.market_position}
                          </Badge>
                        )}
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            </>
          )}

          {/* Source Information */}
          {insight.raw_signal && (
            <>
              <Separator />
              <div>
                <h3 className="font-semibold mb-2">Source</h3>
                <div className="flex items-center gap-2">
                  <Badge variant="outline">{insight.raw_signal.source}</Badge>
                  <a
                    href={insight.raw_signal.url}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="text-sm text-blue-600 hover:underline"
                  >
                    View original signal →
                  </a>
                </div>
              </div>
            </>
          )}
        </CardContent>
      </Card>
    </div>
  );
}

export default function InsightDetailPage({
  params,
}: {
  params: { id: string };
}) {
  return (
    <Suspense fallback={<Skeleton className="h-96" />}>
      <InsightDetailContent id={params.id} />
    </Suspense>
  );
}
```

### Step 2: Add Navigation Header

Create `frontend/components/Header.tsx`:

```typescript
import Link from 'next/link';
import { Button } from '@/components/ui/button';

export function Header() {
  return (
    <header className="border-b">
      <div className="container mx-auto px-4 py-4 flex items-center justify-between">
        <Link href="/" className="text-2xl font-bold">
          StartInsight
        </Link>
        <nav className="flex gap-4">
          <Button variant="ghost" asChild>
            <Link href="/">Home</Link>
          </Button>
          <Button variant="ghost" asChild>
            <Link href="/insights">All Insights</Link>
          </Button>
        </nav>
      </div>
    </header>
  );
}
```

Update `frontend/app/layout.tsx` to include header:

```typescript
import { Header } from '@/components/Header';

// ... inside body
<body className={inter.className}>
  <Providers>
    <Header />
    <main>{children}</main>
  </Providers>
</body>
```

### Step 3: Deploy to Vercel

```bash
# Install Vercel CLI (optional)
npm i -g vercel

# From frontend directory
vercel

# Follow prompts to link project
# Set environment variable: NEXT_PUBLIC_API_URL=https://your-backend-url.com
```

**Success Criteria**:
- ✓ Insight detail page displays all information
- ✓ Navigation header works across all pages
- ✓ Application is responsive on all screen sizes
- ✓ Production build completes without errors
- ✓ Deployed to Vercel and accessible

---

## Testing Requirements

### Manual Testing Checklist

**Homepage (/)**:
- [ ] Top 5 insights load correctly
- [ ] Insights display all fields (problem, solution, score, market size)
- [ ] "View Details" button navigates to detail page
- [ ] Loading skeletons appear while fetching
- [ ] Error message shows if API is unavailable

**All Insights (/insights)**:
- [ ] Insights list loads with pagination
- [ ] Filters update URL and results
- [ ] Source filter works (Reddit, Product Hunt, Trends)
- [ ] Min score filter works (0.5, 0.7, 0.9)
- [ ] Search input filters results
- [ ] Clear filters button resets all filters
- [ ] Back button preserves filter state

**Insight Detail (/insights/[id])**:
- [ ] Full insight details display
- [ ] Competitor analysis shown (if available)
- [ ] Source link opens in new tab
- [ ] 404 page shows for invalid ID
- [ ] Back button returns to previous page

**Responsive Design**:
- [ ] Mobile (375px): Single column layout
- [ ] Tablet (768px): 2-column grid
- [ ] Desktop (1024px+): 3-column grid
- [ ] Navigation collapses on mobile

### E2E Testing (Optional - Phase 4)

Use Playwright for automated testing:

```bash
npm install -D @playwright/test
npx playwright install

# Create tests/e2e/insights.spec.ts
```

---

## Success Criteria

### Phase 3.1: Next.js Project Setup
- ✓ Next.js 14+ installed with App Router
- ✓ TypeScript configured and compiling
- ✓ Tailwind CSS working
- ✓ shadcn/ui components installed
- ✓ Environment variables configured

### Phase 3.2: API Client & Data Fetching
- ✓ API client functions implemented
- ✓ Zod schemas validate responses
- ✓ React Query configured with caching
- ✓ All API endpoints accessible

### Phase 3.3: Insights Dashboard UI
- ✓ Homepage shows daily top 5 insights
- ✓ InsightCard component reusable
- ✓ Responsive grid layout
- ✓ Loading and error states handled

### Phase 3.4: Filtering & Search
- ✓ Filters update URL search params
- ✓ Filter state persists on refresh
- ✓ All filters work correctly
- ✓ Clear filters functionality

### Phase 3.5: Polish & Deploy
- ✓ Insight detail page complete
- ✓ Navigation header on all pages
- ✓ Responsive on all devices
- ✓ Deployed to Vercel
- ✓ Production environment variables set

---

## Common Issues & Solutions

### Issue: API CORS Error
**Solution**: Ensure FastAPI CORS middleware allows frontend origin:
```python
# backend/app/main.py
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "https://your-vercel-domain.vercel.app"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

### Issue: Environment Variables Not Loading
**Solution**: Restart dev server after changing `.env.local`
```bash
# Kill server (Ctrl+C) and restart
npm run dev
```

### Issue: shadcn/ui Components Not Found
**Solution**: Re-run shadcn init and add components:
```bash
npx shadcn-ui@latest init
npx shadcn-ui@latest add button card badge
```

### Issue: Build Fails on Vercel
**Solution**: Check build logs, ensure all dependencies in package.json:
```bash
# Test production build locally
npm run build
```

---

**Phase 3 Reference Guide Complete** ✓

Next: Start with Phase 3.1 (Next.js Project Setup)
