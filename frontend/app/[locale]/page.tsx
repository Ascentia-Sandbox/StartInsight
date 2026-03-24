import { Suspense } from "react";
import Link from "next/link";
import {
  ArrowRight,
  Target,
  Lightbulb,
  Wrench,
  Clock,
  Megaphone,
  User,
  TrendingUp,
  DollarSign,
} from "lucide-react";
import { InsightCard } from "@/components/InsightCard";
import { NewsletterForm } from "@/components/NewsletterForm";
import type { Insight } from "@/lib/types";

interface PublicStats {
  total_insights: number;
  total_signals: number;
  avg_quality_score: number;
  active_sources: number;
  scored_insights: number;
  scoring_dimensions: number;
  evidence_validators: number;
}

const API_URL =
  process.env.NEXT_PUBLIC_API_URL || "https://api.startinsight.co";

async function getHomeData(): Promise<{ insights: Insight[]; stats: PublicStats | null }> {
  try {
    const [insightsResult, statsResult] = await Promise.allSettled([
      fetch(`${API_URL}/api/insights?limit=6&sort=newest`, {
        next: { revalidate: 300 },
      }).then((r) => (r.ok ? r.json() : null)),
      fetch(`${API_URL}/api/insights/stats/public`, {
        next: { revalidate: 300 },
      }).then((r) => (r.ok ? r.json() : null)),
    ]);

    const insights: Insight[] =
      insightsResult.status === "fulfilled" && insightsResult.value?.insights?.length > 0
        ? insightsResult.value.insights.slice(0, 6)
        : [];

    const stats: PublicStats | null =
      statsResult.status === "fulfilled" ? statsResult.value : null;

    return { insights, stats };
  } catch {
    return { insights: [], stats: null };
  }
}

const dimensionCards = [
  { key: "opportunity", icon: Target, name: "Opportunity", description: "Size of the market opportunity and potential for disruption", bg: "bg-blue-500/10" },
  { key: "problem", icon: Lightbulb, name: "Problem Clarity", description: "How well-defined and validated the problem is", bg: "bg-yellow-500/10" },
  { key: "feasibility", icon: Wrench, name: "Feasibility", description: "Technical and business feasibility of the solution", bg: "bg-green-500/10" },
  { key: "why_now", icon: Clock, name: "Why Now", description: "Timing factors that make this the right moment", bg: "bg-purple-500/10" },
  { key: "go_to_market", icon: Megaphone, name: "Go-to-Market", description: "Clarity and viability of distribution strategy", bg: "bg-orange-500/10" },
  { key: "founder_fit", icon: User, name: "Founder Fit", description: "How well this matches typical founder strengths", bg: "bg-pink-500/10" },
  { key: "execution_difficulty", icon: TrendingUp, name: "Execution", description: "Complexity and resource requirements to build", bg: "bg-red-500/10" },
  { key: "revenue_potential", icon: DollarSign, name: "Revenue", description: "Near-term monetization potential", bg: "bg-emerald-500/10" },
];

// Static parts — render instantly
function HeroSection() {
  return (
    <section className="hero-gradient py-24 px-6">
      <div className="max-w-4xl mx-auto text-center">
        <h1 className="text-5xl md:text-6xl mb-6">
          Discover startup opportunities backed by data, not hype
        </h1>
        <p className="text-xl text-muted-foreground mb-8 max-w-2xl mx-auto">
          8-dimension AI analysis across 7+ data sources.
          Find validated ideas before the market catches on.
        </p>
        <div className="flex items-center justify-center gap-4 mb-12 flex-wrap">
          <Link
            href="/insights"
            className="inline-flex items-center px-6 py-3 bg-primary text-primary-foreground rounded-lg font-medium hover:opacity-90 transition-opacity no-underline"
          >
            Explore Insights
            <ArrowRight className="ml-2 h-4 w-4" />
          </Link>
          <Link
            href="/validate"
            className="inline-flex items-center px-6 py-3 border rounded-lg font-medium hover:bg-secondary transition-colors no-underline"
          >
            Validate Your Idea
          </Link>
        </div>

        {/* Static placeholder stats — replaced by async section below */}
        <div className="flex items-center justify-center gap-8 text-sm text-muted-foreground flex-wrap">
          <div className="flex items-center gap-2">
            <span className="font-data text-2xl font-bold text-foreground">500+</span>
            <span>insights analyzed</span>
          </div>
          <div className="w-px h-8 bg-border hidden sm:block" />
          <div className="flex items-center gap-2">
            <span className="font-data text-2xl font-bold text-foreground">8</span>
            <span>scoring dimensions</span>
          </div>
          <div className="w-px h-8 bg-border hidden sm:block" />
          <div className="flex items-center gap-2">
            <span className="font-data text-2xl font-bold text-foreground">7</span>
            <span>data sources</span>
          </div>
        </div>
      </div>
    </section>
  );
}

function DimensionCardsSection() {
  return (
    <section className="py-16 px-6 bg-secondary/50">
      <div className="max-w-4xl mx-auto text-center">
        <h2 className="text-3xl mb-4">8 Dimensions of Analysis</h2>
        <p className="text-muted-foreground mb-12 max-w-2xl mx-auto">
          Every idea is evaluated across 8 critical dimensions &mdash; 2x more
          comprehensive than standard market analysis tools.
        </p>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-6">
          {dimensionCards.map((dim) => {
            const Icon = dim.icon;
            return (
              <div
                key={dim.key}
                className="flex flex-col items-center gap-3 p-4 rounded-xl bg-card border transition-colors hover:border-primary/30"
              >
                <div
                  className={`flex items-center justify-center w-12 h-12 rounded-full ${dim.bg}`}
                >
                  <Icon className="h-6 w-6 text-primary" />
                </div>
                <h3 className="text-sm font-semibold">{dim.name}</h3>
                <p className="text-xs text-muted-foreground leading-relaxed">
                  {dim.description}
                </p>
              </div>
            );
          })}
        </div>
      </div>
    </section>
  );
}

function CTASection() {
  return (
    <section className="py-16 px-6">
      <div className="max-w-3xl mx-auto text-center">
        <h2 className="text-3xl mb-4">Have an idea already?</h2>
        <p className="text-muted-foreground mb-6">
          Get instant 8-dimension validation with our AI analyzer.
        </p>
        <Link
          href="/validate"
          className="inline-flex items-center px-8 py-4 bg-primary text-primary-foreground rounded-lg font-medium text-lg hover:opacity-90 transition-opacity no-underline"
        >
          Validate Your Idea
          <ArrowRight className="ml-2 h-5 w-5" />
        </Link>
      </div>
    </section>
  );
}

function InsightsSkeleton() {
  return (
    <section className="py-16 px-6">
      <div className="max-w-6xl mx-auto">
        <h2 className="text-3xl mb-2">Latest Insights</h2>
        <p className="text-muted-foreground mb-8">
          Fresh market intelligence from today&apos;s data analysis
        </p>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {Array.from({ length: 6 }).map((_, i) => (
            <div key={i} className="rounded-xl border bg-card p-5 h-56 animate-pulse">
              <div className="h-4 bg-muted rounded w-3/4 mb-3" />
              <div className="h-3 bg-muted rounded w-full mb-2" />
              <div className="h-3 bg-muted rounded w-5/6 mb-4" />
              <div className="h-2 bg-muted rounded-full w-full" />
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}

async function LatestInsightsSection() {
  const { insights } = await getHomeData();

  return (
    <section className="py-16 px-6">
      <div className="max-w-6xl mx-auto">
        <h2 className="text-3xl mb-2">Latest Insights</h2>
        <p className="text-muted-foreground mb-8">
          Fresh market intelligence from today&apos;s data analysis
        </p>

        {insights.length > 0 ? (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {insights.map((insight) => (
              <InsightCard key={insight.id} insight={insight} />
            ))}
          </div>
        ) : (
          <div className="text-center py-12 text-muted-foreground">
            <Lightbulb className="h-12 w-12 mx-auto mb-4 opacity-40" />
            <p>No insights available yet. Check back soon!</p>
          </div>
        )}

        <div className="text-center mt-8">
          <Link
            href="/insights"
            className="text-primary font-medium hover:underline"
          >
            View all insights &rarr;
          </Link>
        </div>
      </div>
    </section>
  );
}

export default function HomePage() {
  return (
    <div className="min-h-screen">
      <HeroSection />
      <Suspense fallback={<InsightsSkeleton />}>
        <LatestInsightsSection />
      </Suspense>
      <DimensionCardsSection />
      {/* Newsletter signup */}
      <section className="py-16 px-6 bg-muted/30">
        <div className="max-w-2xl mx-auto text-center space-y-4">
          <h2 className="text-3xl font-semibold">Stay ahead of the market</h2>
          <p className="text-muted-foreground">
            Weekly insights on the most promising startup opportunities, backed by data — not hype.
          </p>
          <NewsletterForm source="homepage" />
        </div>
      </section>
      <CTASection />
    </div>
  );
}
