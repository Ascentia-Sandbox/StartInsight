import { notFound } from 'next/navigation';
import type { Metadata } from 'next';
import Link from 'next/link';
import { BarChart2, ChevronRight, Lock } from 'lucide-react';
import { NewsletterForm } from '@/components/NewsletterForm';
import { ReportCheckoutButton } from './ReportCheckoutButton';
import { UTMCapture } from './UTMCapture';
import { ReportAnalytics } from './ReportAnalytics';

// Minimum insights guaranteed in the full paid report (used in copy)
const FULL_REPORT_SIGNAL_COUNT = 10;

// ============================================================
// Category configuration — add new verticals here
// ============================================================

const CATEGORY_CONFIG: Record<
  string,
  { title: string; description: string; ogDescription: string }
> = {
  'fintech-malaysia': {
    title: 'Fintech Malaysia — Market Gaps',
    description:
      'AI-powered analysis of 47 signals across Reddit, Product Hunt, HN, and Google Trends.',
    ogDescription:
      'Discover the biggest fintech market gaps in Malaysia. AI-analyzed from 6 data sources.',
  },
  'fnb-malaysia': {
    title: 'F&B Malaysia — Market Gaps',
    description:
      'AI-powered analysis of food & beverage market opportunities in Malaysia.',
    ogDescription:
      'Discover F&B market gaps in Malaysia. AI-analyzed from 6 data sources.',
  },
  'logistics-singapore': {
    title: 'Logistics Singapore — Market Gaps',
    description:
      'AI-powered analysis of logistics and supply chain gaps in Singapore.',
    ogDescription:
      'Discover logistics market gaps in Singapore. AI-analyzed from 6 data sources.',
  },
};

// ============================================================
// Types — must match CategoryInsightTeaser / CategoryTeaserResponse in reports.py
// ============================================================

interface TeaserInsight {
  id: string;
  title: string | null;
  problem_statement: string;
  proposed_solution: string;
  market_size_estimate: string;
  relevance_score: number;
  opportunity_score: number | null;
  revenue_potential: string | null;
}

interface CategoryInsightsResponse {
  category: string;
  category_title: string;
  category_description: string;
  insights: TeaserInsight[];
  partial: boolean;
}

// ============================================================
// generateMetadata
// ============================================================

export async function generateMetadata({
  params,
}: {
  params: Promise<{ category: string; locale: string }>;
}): Promise<Metadata> {
  const { category } = await params;
  const config = CATEGORY_CONFIG[category];

  if (!config) {
    return { title: 'Not Found' };
  }

  const jsonLd = {
    '@context': 'https://schema.org',
    '@type': 'Article',
    headline: config.title,
    description: config.ogDescription,
    publisher: {
      '@type': 'Organization',
      name: 'StartInsight',
      url: 'https://startinsight.co',
    },
  };

  return {
    title: `${config.title} | StartInsight`,
    description: config.ogDescription,
    openGraph: {
      title: `${config.title} | StartInsight`,
      description: config.ogDescription,
      url: `https://startinsight.co/reports/${category}`,
      type: 'article',
    },
    twitter: {
      card: 'summary_large_image',
      title: `${config.title} | StartInsight`,
      description: config.ogDescription,
    },
    other: {
      'script:ld+json': JSON.stringify(jsonLd),
    },
  };
}

// ============================================================
// Data fetching (server-side)
// ============================================================

async function fetchCategoryInsights(
  category: string,
): Promise<CategoryInsightsResponse> {
  const apiUrl = process.env.NEXT_PUBLIC_API_URL;
  const cfg = CATEGORY_CONFIG[category];

  const empty: CategoryInsightsResponse = {
    category,
    category_title: cfg?.title ?? category,
    category_description: cfg?.description ?? '',
    insights: [],
    partial: true,
  };

  try {
    const res = await fetch(
      `${apiUrl}/api/insights/category/${encodeURIComponent(category)}`,
      {
        next: { revalidate: 300 }, // ISR: revalidate every 5 minutes
      },
    );

    if (!res.ok) {
      return empty;
    }

    return await res.json();
  } catch {
    return empty;
  }
}

// ============================================================
// Sub-components (server)
// ============================================================

function TeaserInsightCard({ insight }: { insight: TeaserInsight }) {
  const scoreDisplay = insight.relevance_score.toFixed(1);
  const title = insight.title ?? insight.proposed_solution;

  return (
    <div className="rounded-xl border bg-card p-5 flex flex-col gap-3 shadow-[0_1px_3px_rgba(0,0,0,0.08)]">
      {/* Title */}
      <h3 className="text-base font-semibold leading-snug line-clamp-2">
        {title}
      </h3>

      {/* Problem statement as snippet */}
      <p className="text-sm text-muted-foreground line-clamp-2">
        {insight.problem_statement}
      </p>

      {/* Score */}
      <div className="flex items-center gap-2 mt-auto pt-2 border-t border-border/50">
        <span className="text-xs text-muted-foreground font-medium">
          Signal Score
        </span>
        <span className="font-mono text-sm font-bold tabular-nums text-foreground">
          {scoreDisplay}
          <span className="text-muted-foreground font-normal">/10</span>
        </span>
      </div>
    </div>
  );
}

function LockedInsightCard({ index }: { index: number }) {
  // Varying heights give a natural staggered look
  const heights = ['h-[116px]', 'h-[128px]', 'h-[110px]'];
  return (
    <div
      className={`rounded-xl border bg-card p-5 ${heights[index % 3]} opacity-40 select-none pointer-events-none`}
      aria-hidden
    >
      <div className="h-4 bg-muted rounded w-3/4 mb-3" />
      <div className="h-3 bg-muted rounded w-full mb-2" />
      <div className="h-3 bg-muted rounded w-4/5" />
    </div>
  );
}

// ============================================================
// Page (server component)
// ============================================================

interface PageProps {
  params: Promise<{ category: string; locale: string }>;
  searchParams: Promise<{ [key: string]: string | string[] | undefined }>;
}

export default async function CategoryReportPage({
  params,
  searchParams,
}: PageProps) {
  const { category } = await params;
  const resolvedSearch = await searchParams;

  const config = CATEGORY_CONFIG[category];
  if (!config) {
    notFound();
  }

  const { insights, partial } = await fetchCategoryInsights(category);

  // Category display label (e.g. "Fintech Malaysia")
  const categoryLabel = config.title.split(' — ')[0];

  // UTM source from URL — captured client-side into sessionStorage
  const utmSource =
    typeof resolvedSearch.utm_source === 'string'
      ? resolvedSearch.utm_source
      : undefined;

  const apiUrl = process.env.NEXT_PUBLIC_API_URL ?? '';

  return (
    <>
      {/* Client components — analytics + UTM capture */}
      <ReportAnalytics category={category} />
      <UTMCapture utmSource={utmSource} />

      <a href="#main-content" className="skip-to-content">
        Skip to content
      </a>

      <main id="main-content" className="min-h-screen">
        {/* ── Hero ──────────────────────────────────────────── */}
        <section className="hero-gradient py-16 md:py-20">
          <div className="max-w-[1200px] mx-auto px-4 sm:px-6 lg:px-8">
            {/* Breadcrumb */}
            <nav
              aria-label="Breadcrumb"
              className="flex items-center gap-1.5 text-sm text-muted-foreground mb-6"
            >
              <Link
                href="/"
                className="hover:text-foreground transition-colors"
              >
                Home
              </Link>
              <ChevronRight className="h-3.5 w-3.5" />
              <Link
                href="/reports"
                className="hover:text-foreground transition-colors"
              >
                Reports
              </Link>
              <ChevronRight className="h-3.5 w-3.5" />
              <span className="text-foreground">{categoryLabel}</span>
            </nav>

            <h1
              className="font-display text-[24px] md:text-[36px] leading-[1.2] tracking-[-0.02em] mb-4"
            >
              {config.title}
            </h1>
            <p className="text-base md:text-lg text-muted-foreground max-w-[640px]">
              {config.description}
            </p>

            {/* Signal count pill */}
            <div className="mt-6 inline-flex items-center gap-2 bg-primary/8 text-primary text-sm font-medium px-3 py-1.5 rounded-full">
              <BarChart2 className="h-3.5 w-3.5" />
              <span>
                {insights.length > 0 ? `${insights.length}+ signals analyzed` : 'Analysis in progress'}
              </span>
            </div>
          </div>
        </section>

        <div className="max-w-[1200px] mx-auto px-4 sm:px-6 lg:px-8 py-12 space-y-16">
          {insights.length === 0 ? (
            /* ── Empty state ───────────────────────────────── */
            <section
              className="flex flex-col items-center justify-center py-20 text-center"
              aria-label="No insights available"
            >
              <div
                className="w-16 h-16 rounded-full bg-muted flex items-center justify-center mb-6"
                aria-hidden
              >
                <BarChart2 className="h-8 w-8 text-muted-foreground" />
              </div>
              <h2 className="font-display text-[24px] leading-[1.3] tracking-[-0.01em] mb-3">
                We&apos;re analyzing {categoryLabel}
              </h2>
              <p className="text-muted-foreground max-w-[400px] text-base">
                Our AI pipeline is processing signals for this vertical. Check
                back soon — or subscribe to get notified when the report is
                ready.
              </p>
              <div className="mt-8 w-full max-w-sm">
                <NewsletterForm source={`report-empty-${category}`} />
              </div>
            </section>
          ) : (
            <>
              {/* ── Free teasers ──────────────────────────── */}
              <section aria-labelledby="free-signals-heading">
                <div className="flex items-center gap-3 mb-6">
                  <span className="text-xs font-semibold tracking-widest uppercase text-primary">
                    Top 3 Signals This Week
                  </span>
                  <div className="flex-1 h-px bg-border" />
                </div>
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                  {insights.slice(0, 3).map((insight) => (
                    <TeaserInsightCard key={insight.id} insight={insight} />
                  ))}
                </div>
                {partial && (
                  <p className="mt-4 text-sm text-muted-foreground text-center">
                    {insights.length} signal{insights.length !== 1 ? 's' : ''}{' '}
                    available — more signals coming soon.
                  </p>
                )}
              </section>

              {/* ── Email capture ─────────────────────────── */}
              <section
                aria-labelledby="email-capture-heading"
                className="rounded-2xl border bg-muted/40 p-8 text-center"
              >
                <h2
                  id="email-capture-heading"
                  className="font-display text-[24px] leading-[1.3] tracking-[-0.01em] mb-2"
                >
                  Get 2 more free signals
                </h2>
                <p className="text-muted-foreground mb-6 text-sm">
                  Subscribe to our weekly digest and we&apos;ll send you 2
                  additional market gap signals for {categoryLabel}.
                </p>
                <div className="max-w-md mx-auto">
                  <NewsletterForm source={`report-${category}`} />
                </div>
              </section>

              {/* ── Paywall section ───────────────────────── */}
              <section
                aria-labelledby="paywall-heading"
                className="relative"
              >
                <div className="flex items-center gap-3 mb-6">
                  <span className="text-xs font-semibold tracking-widest uppercase text-muted-foreground">
                    Full Report Preview
                  </span>
                  <div className="flex-1 h-px bg-border" />
                  <Lock className="h-3.5 w-3.5 text-muted-foreground shrink-0" />
                </div>

                {/* Locked cards with gradient fade */}
                <div className="relative overflow-hidden rounded-xl">
                  {/* Blurred/faded locked cards */}
                  <div
                    className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4"
                    aria-hidden
                  >
                    {[0, 1, 2].map((i) => (
                      <LockedInsightCard key={i} index={i} />
                    ))}
                  </div>

                  {/* Gradient fade overlay */}
                  <div
                    className="absolute inset-0 pointer-events-none"
                    style={{
                      background:
                        'linear-gradient(to bottom, transparent 0%, transparent 55%, var(--background) 88%)',
                    }}
                  />
                </div>

                {/* CTA card */}
                <div
                  className="mt-6 rounded-2xl p-8 text-center text-white"
                  style={{ backgroundColor: '#0D7377' }}
                >
                  <h2
                    id="paywall-heading"
                    className="font-display text-[24px] leading-[1.3] tracking-[-0.01em] mb-1"
                  >
                    Full {categoryLabel} Report
                  </h2>
                  <p className="text-white/80 text-sm mb-5">
                    {FULL_REPORT_SIGNAL_COUNT}+ signals, ranked by opportunity score. One-time
                    purchase, instant access.
                  </p>

                  <div className="mb-6">
                    <span
                      className="font-mono text-[24px] font-bold tabular-nums"
                      aria-label="Price: RM 49"
                    >
                      RM 49
                    </span>
                    <span className="text-white/70 text-sm ml-1">
                      one-time
                    </span>
                  </div>

                  <div className="max-w-xs mx-auto">
                    <ReportCheckoutButton
                      category={category}
                      apiUrl={apiUrl}
                    />
                  </div>

                  <p className="mt-4 text-white/60 text-xs">
                    Secure checkout via Stripe. No subscription.
                  </p>
                </div>
              </section>
            </>
          )}
        </div>
      </main>
    </>
  );
}
