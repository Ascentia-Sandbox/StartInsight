import { notFound } from 'next/navigation';
import type { Metadata } from 'next';
import Link from 'next/link';
import { ArrowRight, BarChart2, TrendingUp } from 'lucide-react';
import { NewsletterForm } from '@/components/NewsletterForm';
import { config } from '@/lib/env';

// ============================================================
// Types
// ============================================================

interface ExploreInsight {
  id: string;
  slug: string | null;
  title: string | null;
  problem_statement: string;
  proposed_solution: string;
  market_size_estimate: string;
  relevance_score: number;
  opportunity_score: number | null;
  created_at: string | null;
}

interface ExploreResponse {
  category: {
    slug: string;
    title: string;
    description: string;
    meta_description: string;
  };
  insights: ExploreInsight[];
  total: number;
}

// ============================================================
// Data fetching
// ============================================================

async function fetchExploreData(
  category: string,
): Promise<ExploreResponse | null> {
  const apiUrl = config.apiUrl;
  try {
    const res = await fetch(
      `${apiUrl}/api/explore/${encodeURIComponent(category)}`,
      { next: { revalidate: 3600 } },
    );
    if (!res.ok) return null;
    return await res.json();
  } catch {
    return null;
  }
}

// ============================================================
// generateMetadata
// ============================================================

export async function generateMetadata({
  params,
}: {
  params: Promise<{ category: string }>;
}): Promise<Metadata> {
  const { category } = await params;
  const data = await fetchExploreData(category);
  if (!data) return { title: 'Not Found' };

  const { title, meta_description, slug } = data.category;
  const year = new Date().getFullYear();
  const fullTitle = `${title} ${year} — StartInsight`;

  const jsonLd = {
    '@context': 'https://schema.org',
    '@type': 'CollectionPage',
    name: fullTitle,
    description: meta_description,
    url: `https://startinsight.co/explore/${slug}`,
    publisher: {
      '@type': 'Organization',
      name: 'StartInsight',
      url: 'https://startinsight.co',
    },
  };

  return {
    title: fullTitle,
    description: meta_description,
    openGraph: {
      title: fullTitle,
      description: meta_description,
      url: `https://startinsight.co/explore/${slug}`,
      type: 'website',
    },
    twitter: {
      card: 'summary_large_image',
      title: fullTitle,
      description: meta_description,
    },
    other: {
      'script:ld+json': JSON.stringify(jsonLd),
    },
  };
}

// ============================================================
// Page
// ============================================================

export default async function ExploreCategoryPage({
  params,
}: {
  params: Promise<{ category: string }>;
}) {
  const { category } = await params;
  const data = await fetchExploreData(category);

  if (!data) notFound();

  const { category: cat, insights } = data;
  const year = new Date().getFullYear();

  return (
    <main className="min-h-screen">
      {/* Hero */}
      <section className="bg-gradient-to-b from-[#0D7377]/5 to-transparent py-16">
        <div className="max-w-[1000px] mx-auto px-4 sm:px-6">
          <div className="flex items-center gap-2 text-sm text-muted-foreground mb-4">
            <Link href="/explore" className="hover:text-foreground transition-colors">
              Explore
            </Link>
            <span>/</span>
            <span className="text-foreground">{cat.title}</span>
          </div>

          <h1 className="font-serif text-3xl md:text-4xl font-bold tracking-tight mb-4">
            {cat.title} — {year}
          </h1>
          <p className="text-lg text-muted-foreground max-w-2xl">
            {cat.description} Scored across 8 dimensions by our AI, sourced from
            Reddit, Product Hunt, Google Trends, and more.
          </p>

          <div className="flex items-center gap-4 mt-6 text-sm text-muted-foreground">
            <span className="flex items-center gap-1">
              <BarChart2 className="h-4 w-4" />
              {insights.length} ideas found
            </span>
            <span className="flex items-center gap-1">
              <TrendingUp className="h-4 w-4" />
              Updated hourly
            </span>
          </div>
        </div>
      </section>

      {/* Insight Cards */}
      <section className="max-w-[1000px] mx-auto px-4 sm:px-6 py-10">
        {insights.length === 0 ? (
          <div className="text-center py-20">
            <p className="text-lg text-muted-foreground">
              We&apos;re still analyzing this category. Check back soon.
            </p>
          </div>
        ) : (
          <div className="grid gap-4">
            {insights.map((insight) => {
              const title = insight.title ?? insight.proposed_solution;
              const href = `/insights/${insight.slug ?? insight.id}`;
              const score = insight.relevance_score?.toFixed(1) ?? '—';

              return (
                <Link
                  key={insight.id}
                  href={href}
                  className="group block rounded-xl border bg-card p-5 hover:shadow-md transition-shadow"
                >
                  <div className="flex items-start justify-between gap-4">
                    <div className="flex-1 min-w-0">
                      <h2 className="font-semibold text-base group-hover:text-[#0D7377] transition-colors line-clamp-2">
                        {title}
                      </h2>
                      <p className="text-sm text-muted-foreground mt-1 line-clamp-2">
                        {insight.problem_statement}
                      </p>
                      {insight.market_size_estimate && (
                        <p className="text-xs text-muted-foreground mt-2">
                          Market: {insight.market_size_estimate}
                        </p>
                      )}
                    </div>
                    <div className="flex flex-col items-center shrink-0">
                      <div className="text-lg font-bold text-[#0D7377]">
                        {score}
                      </div>
                      <div className="text-[10px] text-muted-foreground uppercase tracking-wider">
                        Score
                      </div>
                    </div>
                  </div>
                  <div className="flex items-center gap-1 text-xs text-[#0D7377] mt-3 opacity-0 group-hover:opacity-100 transition-opacity">
                    View full analysis <ArrowRight className="h-3 w-3" />
                  </div>
                </Link>
              );
            })}
          </div>
        )}
      </section>

      {/* CTA: Newsletter */}
      <section className="bg-muted/30 py-12 mt-8">
        <div className="max-w-lg mx-auto px-4 text-center">
          <h2 className="font-serif text-xl font-semibold mb-2">
            Get weekly {cat.title.toLowerCase()} insights
          </h2>
          <p className="text-sm text-muted-foreground mb-4">
            AI-sourced opportunities delivered to your inbox every Monday.
          </p>
          <NewsletterForm source={`explore-${category}`} />
        </div>
      </section>

      {/* Related Categories */}
      <section className="max-w-[1000px] mx-auto px-4 sm:px-6 py-10">
        <h2 className="font-semibold text-lg mb-4">Explore more categories</h2>
        <div className="flex flex-wrap gap-2">
          {[
            'ai-saas-ideas',
            'fintech-startup-ideas',
            'devtools-opportunities',
            'health-tech-ideas',
            'ecommerce-gaps',
            'malaysia-startup-ideas',
            'singapore-startup-ideas',
          ]
            .filter((slug) => slug !== category)
            .slice(0, 5)
            .map((slug) => (
              <Link
                key={slug}
                href={`/explore/${slug}`}
                className="px-3 py-1.5 rounded-full border text-sm hover:bg-muted transition-colors"
              >
                {slug.replace(/-/g, ' ').replace(/\b\w/g, (c) => c.toUpperCase())}
              </Link>
            ))}
        </div>
      </section>
    </main>
  );
}
