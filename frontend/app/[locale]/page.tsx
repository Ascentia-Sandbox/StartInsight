"use client";

import { useEffect, useState } from "react";
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
import { Skeleton } from "@/components/ui/skeleton";
import { InsightCard } from "@/components/InsightCard";
import { config } from "@/lib/env";
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

export default function HomePage() {
  const [insights, setInsights] = useState<Insight[]>([]);
  const [stats, setStats] = useState<PublicStats | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchHomeData();
  }, []);

  const fetchHomeData = async () => {
    const apiUrl = config.apiUrl;

    // Fetch insights and stats in parallel
    const [insightsResult, statsResult] = await Promise.allSettled([
      fetch(`${apiUrl}/api/insights?limit=6&sort=newest`).then((r) =>
        r.ok ? r.json() : null
      ),
      fetch(`${apiUrl}/api/insights/stats/public`).then((r) =>
        r.ok ? r.json() : null
      ),
    ]);

    // Process insights
    if (insightsResult.status === "fulfilled" && insightsResult.value) {
      const data = insightsResult.value;
      if (data.insights?.length > 0) {
        setInsights(data.insights.slice(0, 6));
      }
    }

    // Process stats
    if (statsResult.status === "fulfilled" && statsResult.value) {
      setStats(statsResult.value as PublicStats);
    }

    setLoading(false);
  };

  // Fallback values when stats not loaded
  const insightCount = stats
    ? stats.total_insights.toLocaleString()
    : "500+";
  const sourceCount = stats ? String(stats.active_sources) : "6";
  const dimensionCount = stats ? String(stats.scoring_dimensions) : "8";

  // Dimension cards data for the scoring deep-dive section
  const dimensionCards = [
    { key: 'opportunity', icon: Target, name: 'Opportunity', description: 'Size of the market opportunity and potential for disruption', bg: 'bg-blue-500/10' },
    { key: 'problem', icon: Lightbulb, name: 'Problem Clarity', description: 'How well-defined and validated the problem is', bg: 'bg-yellow-500/10' },
    { key: 'feasibility', icon: Wrench, name: 'Feasibility', description: 'Technical and business feasibility of the solution', bg: 'bg-green-500/10' },
    { key: 'why_now', icon: Clock, name: 'Why Now', description: 'Timing factors that make this the right moment', bg: 'bg-purple-500/10' },
    { key: 'go_to_market', icon: Megaphone, name: 'Go-to-Market', description: 'Clarity and viability of distribution strategy', bg: 'bg-orange-500/10' },
    { key: 'founder_fit', icon: User, name: 'Founder Fit', description: 'How well this matches typical founder strengths', bg: 'bg-pink-500/10' },
    { key: 'execution_difficulty', icon: TrendingUp, name: 'Execution', description: 'Complexity and resource requirements to build', bg: 'bg-red-500/10' },
    { key: 'revenue_potential', icon: DollarSign, name: 'Revenue', description: 'Near-term monetization potential', bg: 'bg-emerald-500/10' },
  ];

  return (
    <div className="min-h-screen">
      {/* ===== Hero Section ===== */}
      <section className="hero-gradient py-24 px-6">
        <div className="max-w-4xl mx-auto text-center">
          <h1 className="text-5xl md:text-6xl mb-6">
            Discover startup opportunities backed by data, not hype
          </h1>
          <p className="text-xl text-muted-foreground mb-8 max-w-2xl mx-auto">
            8-dimension AI analysis across {sourceCount}+ data sources.
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

          {/* Animated counters -- driven by /api/insights/stats/public */}
          <div className="flex items-center justify-center gap-8 text-sm text-muted-foreground flex-wrap">
            <div className="flex items-center gap-2">
              <span className="font-data text-2xl font-bold text-foreground">
                {insightCount}
              </span>
              <span>insights analyzed</span>
            </div>
            <div className="w-px h-8 bg-border hidden sm:block" />
            <div className="flex items-center gap-2">
              <span className="font-data text-2xl font-bold text-foreground">
                {dimensionCount}
              </span>
              <span>scoring dimensions</span>
            </div>
            <div className="w-px h-8 bg-border hidden sm:block" />
            <div className="flex items-center gap-2">
              <span className="font-data text-2xl font-bold text-foreground">
                {sourceCount}
              </span>
              <span>data sources</span>
            </div>
            {stats && stats.avg_quality_score > 0 && (
              <>
                <div className="w-px h-8 bg-border hidden sm:block" />
                <div className="flex items-center gap-2">
                  <span className="font-data text-2xl font-bold text-foreground">
                    {(stats.avg_quality_score * 100).toFixed(0)}%
                  </span>
                  <span>avg quality</span>
                </div>
              </>
            )}
          </div>
        </div>
      </section>

      {/* ===== Latest Insights Section ===== */}
      <section className="py-16 px-6">
        <div className="max-w-6xl mx-auto">
          <h2 className="text-3xl mb-2">Latest Insights</h2>
          <p className="text-muted-foreground mb-8">
            Fresh market intelligence from today&apos;s data analysis
          </p>

          {loading ? (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
              {Array.from({ length: 6 }).map((_, i) => (
                <Skeleton key={i} className="h-64 rounded-xl" />
              ))}
            </div>
          ) : insights.length > 0 ? (
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

      {/* ===== 8 Dimensions Scoring Deep-Dive ===== */}
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

      {/* ===== CTA Section ===== */}
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
    </div>
  );
}
