'use client';

import { useQuery } from '@tanstack/react-query';
import { useParams } from 'next/navigation';
import { useState } from 'react';
import { fetchInsightById } from '@/lib/api';
import { Card, CardContent } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Skeleton } from '@/components/ui/skeleton';
import { ChartLoadingSkeleton } from '@/components/ui/chart-loading-skeleton';
import { Button } from '@/components/ui/button';
import { formatDistanceToNow } from 'date-fns';
import Link from 'next/link';
import {
  DollarSign, Rocket, TrendingUp, Target, Zap,
  Clock, ArrowRight, CheckCircle2, BarChart3,
  Users, Globe, ChevronRight, Lightbulb, Search, MessageCircle,
  MessageSquare, BookmarkPlus, ArrowLeft, ExternalLink,
  Eye, Bookmark, Share2, ShieldCheck, Database, Info,
} from 'lucide-react';
import { Breadcrumbs } from '@/components/ui/breadcrumbs';
import { TrendChart } from '@/components/trend-chart';
import { ScoreRadar } from '@/components/evidence/score-radar';
import { config } from '@/lib/env';

// Trend data response type
interface TrendDataResponse {
  dates: string[];
  values: number[];
}

// Engagement metrics type
interface EngagementMetrics {
  view_count: number;
  save_count: number;
  share_count: number;
  claim_count: number;
  export_count: number;
  interested_count: number;
  evidence_count: number;
}

// Source badge color helper
function getSourceBadgeClass(source: string): string {
  switch (source?.toLowerCase()) {
    case 'reddit': return 'bg-orange-100 text-orange-800 dark:bg-orange-900/30 dark:text-orange-300 border-orange-200';
    case 'producthunt':
    case 'product_hunt': return 'bg-red-100 text-red-800 dark:bg-red-900/30 dark:text-red-300 border-red-200';
    case 'hackernews':
    case 'hacker_news': return 'bg-amber-100 text-amber-800 dark:bg-amber-900/30 dark:text-amber-300 border-amber-200';
    case 'twitter': return 'bg-sky-100 text-sky-800 dark:bg-sky-900/30 dark:text-sky-300 border-sky-200';
    case 'google_trends': return 'bg-blue-100 text-blue-800 dark:bg-blue-900/30 dark:text-blue-300 border-blue-200';
    default: return 'bg-gray-100 text-gray-800 dark:bg-gray-900/30 dark:text-gray-300 border-gray-200';
  }
}

// Confidence badge color
function getConfidenceColor(conf: string): string {
  if (conf === 'High') return 'bg-green-100 text-green-800';
  if (conf === 'Medium') return 'bg-amber-100 text-amber-800';
  return 'bg-gray-100 text-gray-800';
}

// Score label + color mapping (IdeaBrowser-style)
function getScoreLabel(score: number): { label: string; color: string } {
  if (score >= 9) return { label: 'Exceptional', color: 'bg-blue-500' };
  if (score >= 7) return { label: 'Great', color: 'bg-green-500' };
  if (score >= 5) return { label: 'Moderate', color: 'bg-amber-500' };
  return { label: 'Low', color: 'bg-red-500' };
}

// Platform icon helper
function getPlatformIcon(platform: string) {
  switch (platform?.toLowerCase()) {
    case 'reddit': return <Users className="h-5 w-5 text-orange-500" />;
    case 'facebook': return <Globe className="h-5 w-5 text-blue-600" />;
    case 'youtube': return <BarChart3 className="h-5 w-5 text-red-500" />;
    default: return <Globe className="h-5 w-5 text-gray-500" />;
  }
}

export default function InsightDetailPage() {
  const params = useParams();
  const slug = params.slug as string;
  const [saved, setSaved] = useState(false);

  const { data: insight, isLoading, error } = useQuery({
    queryKey: ['insight', slug],
    queryFn: () => fetchInsightById(slug),
    enabled: !!slug,
  });

  // Use the actual UUID for sub-resource API calls
  const insightId = insight?.id;

  // Fetch engagement metrics (non-blocking)
  const { data: engagement } = useQuery<EngagementMetrics | null>({
    queryKey: ['insight-engagement', insightId],
    queryFn: async () => {
      try {
        const res = await fetch(`${config.apiUrl}/api/insights/${insightId}/engagement`);
        if (!res.ok) return null;
        return res.json();
      } catch {
        return null;
      }
    },
    enabled: !!insightId,
  });

  // Fetch trend data from dedicated endpoint (non-blocking)
  const { data: trendDataResponse } = useQuery<TrendDataResponse | null>({
    queryKey: ['insight-trend-data', insightId],
    queryFn: async () => {
      try {
        const res = await fetch(`${config.apiUrl}/api/insights/${insightId}/trend-data`);
        if (!res.ok) return null;
        return res.json();
      } catch {
        return null;
      }
    },
    enabled: !!insightId,
  });

  if (isLoading) {
    return (
      <div className="min-h-screen">
        {/* Hero skeleton */}
        <div className="hero-gradient py-12 px-6">
          <div className="max-w-5xl mx-auto space-y-4">
            <Skeleton className="h-6 w-32" />
            <Skeleton className="h-12 w-full" />
            <Skeleton className="h-12 w-3/4" />
          </div>
        </div>
        <div className="max-w-5xl mx-auto px-6 py-8 space-y-8">
          <div className="grid lg:grid-cols-[1fr_320px] gap-6">
            <ChartLoadingSkeleton />
            <div className="space-y-3">
              <Skeleton className="h-24" />
              <Skeleton className="h-24" />
              <Skeleton className="h-24" />
              <Skeleton className="h-24" />
            </div>
          </div>
          <Skeleton className="h-48" />
        </div>
      </div>
    );
  }

  if (error || !insight) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="text-center max-w-sm">
          <div className="mx-auto mb-6 h-20 w-20 rounded-2xl bg-muted flex items-center justify-center">
            <Lightbulb className="h-10 w-10 text-muted-foreground/40" />
          </div>
          <h2 className="text-2xl font-bold mb-2">Insight not found</h2>
          <p className="text-muted-foreground mt-2 mb-8">
            {error instanceof Error ? error.message : 'This insight does not exist or could not be loaded.'}
          </p>
          <Button asChild>
            <Link href="/insights">
              <ArrowLeft className="h-4 w-4 mr-2" /> Back to All Insights
            </Link>
          </Button>
        </div>
      </div>
    );
  }

  // Calculate overall score
  const scoreFields = [
    insight.opportunity_score,
    insight.problem_score,
    insight.feasibility_score,
    insight.why_now_score,
    insight.go_to_market_score,
    insight.founder_fit_score,
    insight.execution_difficulty_score,
  ].filter((s): s is number => s != null);

  // Handle revenue_potential_score being string or number
  const revScore = insight.revenue_potential_score;
  const revenueMap: Record<string, number> = { '$': 3, '$$': 5, '$$$': 7, '$$$$': 9 };
  if (typeof revScore === 'number') {
    scoreFields.push(revScore);
  } else if (typeof revScore === 'string' && revenueMap[revScore]) {
    scoreFields.push(revenueMap[revScore]);
  }

  const overallScore = scoreFields.length > 0
    ? scoreFields.reduce((a, b) => a + b, 0) / scoreFields.length
    : 0;

  // Convert trend data from dedicated endpoint to chart format
  const trendChartData: { date: string; value: number }[] | null =
    trendDataResponse && trendDataResponse.dates.length > 0
      ? trendDataResponse.dates.map((date, i) => ({
          date,
          value: trendDataResponse.values[i] ?? 0,
        }))
      : null;

  // Extract primary keyword info for trend chart header
  const primaryKeyword = insight.trend_keywords?.[0];

  // Determine search interest level from relevance_score for badge fallback
  const getSearchInterest = (score: number) => {
    if (score >= 0.8) return { label: 'High Interest', color: 'bg-green-100 text-green-800 border-green-200' };
    if (score >= 0.5) return { label: 'Medium Interest', color: 'bg-amber-100 text-amber-800 border-amber-200' };
    return { label: 'Low Interest', color: 'bg-gray-100 text-gray-700 border-gray-200' };
  };

  const searchInterest = getSearchInterest(insight.relevance_score);
  const sourceName = insight.raw_signal?.source || 'Unknown';

  // Revenue display value
  const revenueDisplay = typeof insight.revenue_potential_score === 'string'
    ? insight.revenue_potential_score
    : insight.revenue_potential_score != null
      ? `${insight.revenue_potential_score}/10`
      : null;

  // All 8 score cards
  const scoreCards = [
    { label: 'Opportunity', score: insight.opportunity_score, icon: Target },
    { label: 'Problem', score: insight.problem_score, icon: Lightbulb },
    { label: 'Feasibility', score: insight.feasibility_score, icon: Zap },
    { label: 'Why Now', score: insight.why_now_score, icon: Clock },
    { label: 'Revenue', score: typeof insight.revenue_potential_score === 'string' ? revenueMap[insight.revenue_potential_score] : insight.revenue_potential_score, icon: DollarSign, display: revenueDisplay },
    { label: 'Difficulty', score: insight.execution_difficulty_score, icon: Database },
    { label: 'GTM', score: insight.go_to_market_score, icon: Rocket },
    { label: 'Founder Fit', score: insight.founder_fit_score, icon: Users },
  ].filter(c => c.score != null);

  return (
    <div className="min-h-screen pb-20">
      {/* ===== HERO (simplified) ===== */}
      <section className="hero-gradient py-12 px-6">
        <div className="max-w-5xl mx-auto">
          {/* Breadcrumbs */}
          <Breadcrumbs items={[
            { label: 'Insights', href: '/insights' },
            { label: (insight.title || insight.proposed_solution)?.slice(0, 50) || 'Detail' },
          ]} />

          {/* Source badge + date */}
          <div className="flex items-center gap-3 mb-4 mt-4">
            <Badge className={getSourceBadgeClass(sourceName)}>
              {sourceName.replace('_', ' ')}
            </Badge>
            <span className="text-sm text-muted-foreground">
              {formatDistanceToNow(new Date(insight.created_at), { addSuffix: true })}
            </span>
            {insight.why_now_score && insight.why_now_score >= 7 && (
              <Badge className="bg-red-100 text-red-800 border-red-200">
                <Clock className="h-3 w-3 mr-1" /> Perfect Timing
              </Badge>
            )}
          </div>

          {/* Large title */}
          <h1 className="text-4xl md:text-5xl leading-tight mb-3 max-w-4xl">
            {insight.title || insight.proposed_solution}
          </h1>

          {/* Disclaimer */}
          <p className="text-sm text-muted-foreground">
            Analysis, scores, and revenue estimates are educational and based on assumptions. Results vary by execution and market conditions.
          </p>
        </div>
      </section>

      {/* ===== TREND CHART + SCORE CARDS (2-column, IdeaBrowser-style) ===== */}
      <section className="py-8 px-6">
        <div className="max-w-5xl mx-auto">
          <div className="grid lg:grid-cols-[1fr_320px] gap-6">
            {/* Left: Trend Chart */}
            <Card>
              <CardContent className="p-6">
                {trendChartData ? (
                  <TrendChart
                    data={trendChartData}
                    keyword={primaryKeyword?.keyword}
                    volume={primaryKeyword?.volume}
                    growth={primaryKeyword?.growth}
                    allKeywords={insight.trend_keywords ?? undefined}
                  />
                ) : (
                  <div className="flex flex-col items-center justify-center py-12 gap-3">
                    <div className="flex items-center gap-2">
                      <Search className="h-5 w-5 text-muted-foreground" />
                      <span className="text-sm font-medium text-muted-foreground">Search Interest</span>
                    </div>
                    <Badge className={`text-sm px-4 py-1 ${searchInterest.color}`}>
                      <TrendingUp className="h-3.5 w-3.5 mr-1.5" />
                      {searchInterest.label}
                    </Badge>
                    <p className="text-xs text-muted-foreground mt-1">
                      Based on relevance score ({(insight.relevance_score * 100).toFixed(0)}%)
                    </p>
                  </div>
                )}
              </CardContent>
            </Card>

            {/* Right: All 8 Score Dimensions */}
            <div className="space-y-3">
              {/* Overall Score */}
              {scoreFields.length > 0 && (
                <div className="text-center p-4 bg-muted/30 rounded-xl border">
                  <div className="text-xs text-muted-foreground uppercase tracking-wider mb-1">Overall Score</div>
                  <div className="text-4xl font-bold font-data">{overallScore.toFixed(1)}<span className="text-lg text-muted-foreground">/10</span></div>
                </div>
              )}

              {/* 4x2 Score Cards (all 8 dimensions) */}
              {scoreCards.length > 0 && (
                <div className="grid grid-cols-2 gap-2">
                  {scoreCards.map((card) => {
                    const score = card.score!;
                    const { label, color } = getScoreLabel(score);
                    const Icon = card.icon;
                    return (
                      <div key={card.label} className="p-3 bg-background rounded-xl border">
                        <div className="flex items-center gap-1.5 text-xs text-muted-foreground mb-1">
                          <Icon className="h-3 w-3" />
                          {card.label}
                        </div>
                        <div className="text-2xl font-bold font-data">
                          {'display' in card && card.display ? card.display : score}
                        </div>
                        <div className="text-[11px] text-muted-foreground">{label}</div>
                        <div className={`mt-1.5 h-1 rounded-full ${color}`} />
                      </div>
                    );
                  })}
                </div>
              )}
            </div>
          </div>
        </div>
      </section>

      {/* ===== INTERACTIVE SCORE RADAR ===== */}
      {scoreCards.length >= 3 && (
        <section className="px-6 pb-8">
          <div className="max-w-5xl mx-auto">
            <ScoreRadar
              scores={{
                opportunity: insight.opportunity_score ?? undefined,
                problem: insight.problem_score ?? undefined,
                feasibility: insight.feasibility_score ?? undefined,
                why_now: insight.why_now_score ?? undefined,
                go_to_market: insight.go_to_market_score ?? undefined,
                founder_fit: insight.founder_fit_score ?? undefined,
                execution_difficulty: insight.execution_difficulty_score ?? undefined,
                revenue_potential: insight.revenue_potential_score ?? undefined,
              }}
              size="md"
            />
          </div>
        </section>
      )}

      {/* ===== DESCRIPTION (clean prose) ===== */}
      <section className="py-10 px-6">
        <div className="max-w-5xl mx-auto">
          <div className="max-w-3xl">
            <h2 className="text-2xl mb-4">The Problem</h2>
            <div className="space-y-4">
              {insight.problem_statement.split('\n\n').filter(Boolean).map((paragraph, idx) => (
                <p key={idx} className="text-lg leading-relaxed text-muted-foreground">
                  {paragraph}
                </p>
              ))}
            </div>
            {insight.proposed_solution && (
              <div className="mt-8">
                <h2 className="text-2xl mb-4">The Solution</h2>
                <p className="text-lg leading-relaxed text-muted-foreground">
                  {insight.proposed_solution}
                </p>
              </div>
            )}
            {/* Market Gap Analysis */}
            {insight.market_gap_analysis && (
              <div className="mt-6 p-4 bg-muted/30 rounded-lg border-l-4 border-primary/40">
                <h3 className="text-sm font-semibold uppercase tracking-wider text-muted-foreground mb-2">Market Gap</h3>
                <p className="text-sm leading-relaxed text-muted-foreground">{insight.market_gap_analysis}</p>
              </div>
            )}
          </div>
        </div>
      </section>

      {/* ===== MARKET OPPORTUNITY (TAM/SAM/SOM) ===== */}
      {(insight.market_sizing || insight.market_size_estimate) && (
        <section className="py-10 px-6 bg-secondary/20">
          <div className="max-w-5xl mx-auto">
            <h2 className="text-2xl mb-6">Market Opportunity</h2>
            {insight.market_sizing ? (
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4 p-6 bg-background rounded-xl border">
                <div className="text-center md:text-left">
                  <div className="text-xs font-medium text-muted-foreground uppercase tracking-wider mb-1">TAM (Total Addressable)</div>
                  <div className="text-2xl font-bold text-blue-600">{insight.market_sizing.tam}</div>
                </div>
                <div className="text-center md:text-left">
                  <div className="text-xs font-medium text-muted-foreground uppercase tracking-wider mb-1">SAM (Serviceable)</div>
                  <div className="text-2xl font-bold text-green-600">{insight.market_sizing.sam}</div>
                </div>
                <div className="text-center md:text-left">
                  <div className="text-xs font-medium text-muted-foreground uppercase tracking-wider mb-1">SOM (Obtainable)</div>
                  <div className="text-2xl font-bold text-violet-600">{insight.market_sizing.som}</div>
                </div>
              </div>
            ) : insight.market_size_estimate ? (
              <div className="flex items-center gap-4 p-5 bg-background rounded-xl border">
                <DollarSign className="h-6 w-6 text-green-600" />
                <div>
                  <span className="font-semibold text-lg">Estimated Market Size:</span>
                  <span className="ml-2 text-muted-foreground text-lg">{insight.market_size_estimate}</span>
                </div>
              </div>
            ) : null}
          </div>
        </section>
      )}

      {/* ===== EVIDENCE & SIGNALS ===== */}
      <section className="py-10 px-6">
        <div className="max-w-5xl mx-auto">
          {/* Evidence header */}
          <div className="flex items-center justify-between mb-6">
            <div className="flex items-center gap-3">
              <h2 className="text-2xl">Evidence & Signals</h2>
              {(() => {
                const evidenceScore = Math.round(insight.relevance_score * 10);
                const badgeColor = evidenceScore >= 8
                  ? 'bg-green-100 text-green-800 border-green-200'
                  : evidenceScore >= 5
                    ? 'bg-amber-100 text-amber-800 border-amber-200'
                    : 'bg-gray-100 text-gray-700 border-gray-200';
                return (
                  <Badge className={`text-sm px-3 py-0.5 ${badgeColor}`}>
                    <ShieldCheck className="h-3.5 w-3.5 mr-1" />
                    {evidenceScore}/10
                  </Badge>
                );
              })()}
            </div>
          </div>

          {/* Why Now? */}
          {insight.why_now_analysis && (
            <div className="mb-8 p-5 bg-muted/30 rounded-xl border-l-4 border-purple-400">
              <h3 className="text-lg font-semibold mb-2 flex items-center gap-2">
                <Clock className="h-5 w-5 text-purple-500" />
                Why Now?
              </h3>
              <p className="text-muted-foreground leading-relaxed">{insight.why_now_analysis}</p>
            </div>
          )}

          {/* Proof Signals */}
          {insight.proof_signals && insight.proof_signals.length > 0 && (
            <div className="space-y-3 mb-8">
              <h3 className="text-lg font-semibold mb-3">Proof Signals</h3>
              {insight.proof_signals.map((signal, idx) => (
                <div key={idx} className="flex items-start gap-3 p-4 bg-muted/20 rounded-lg border">
                  <div className="flex-shrink-0 mt-0.5">
                    {signal.signal_type === 'search_trend' && <TrendingUp className="h-5 w-5 text-blue-500" />}
                    {signal.signal_type === 'market_report' && <BarChart3 className="h-5 w-5 text-green-500" />}
                    {signal.signal_type === 'community_discussion' && <Users className="h-5 w-5 text-orange-500" />}
                    {signal.signal_type === 'competitor_growth' && <Target className="h-5 w-5 text-purple-500" />}
                  </div>
                  <div className="flex-1">
                    <p className="text-sm font-medium">{signal.description}</p>
                    <div className="flex items-center gap-2 mt-1">
                      <span className="text-xs text-muted-foreground">{signal.source}</span>
                      <Badge variant="outline" className={`text-xs ${getConfidenceColor(signal.confidence)}`}>
                        {signal.confidence}
                      </Badge>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}

          {/* Trend Keywords */}
          {insight.trend_keywords && insight.trend_keywords.length > 1 && (
            <div className="mb-8">
              <h3 className="text-lg font-semibold mb-4">Related Keywords</h3>
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                {insight.trend_keywords.slice(1).map((kw, idx) => (
                  <div key={idx} className="flex items-center justify-between p-3 bg-muted/20 rounded-lg border text-sm">
                    <span className="font-medium">{kw.keyword}</span>
                    <div className="flex items-center gap-3">
                      <span className="text-muted-foreground">{kw.volume}</span>
                      <span className="text-green-600 font-medium">{kw.growth}</span>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Community Signals */}
          {insight.community_signals_chart && insight.community_signals_chart.length > 0 && (
            <div className="mb-8">
              <h3 className="text-lg font-semibold mb-4">Community Signals</h3>
              <div className="grid sm:grid-cols-2 gap-3">
                {insight.community_signals_chart.map((signal, idx) => (
                  <div key={idx} className="flex items-center justify-between p-4 bg-muted/20 rounded-lg border">
                    <div className="flex items-center gap-3">
                      {getPlatformIcon(signal.platform || '')}
                      <div>
                        <div className="text-sm font-medium">{signal.platform || 'Other'}</div>
                        <div className="text-xs text-muted-foreground">{signal.members}</div>
                      </div>
                    </div>
                    <span className={`text-sm font-bold ${signal.score >= 7 ? 'text-green-600' : signal.score >= 5 ? 'text-amber-600' : 'text-gray-500'}`}>
                      {signal.score}/10
                    </span>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Source Info */}
          {insight.raw_signal && (
            <div className="p-4 bg-muted/20 rounded-lg border flex items-center justify-between">
              <div className="flex items-center gap-3 text-sm">
                <span className="text-muted-foreground">Original Signal:</span>
                <Badge variant="outline" className="capitalize">{sourceName.replace('_', ' ')}</Badge>
                <span className="text-muted-foreground">
                  {formatDistanceToNow(new Date(insight.created_at), { addSuffix: true })}
                </span>
              </div>
              <Button asChild variant="outline" size="sm">
                <a href={insight.raw_signal.url} target="_blank" rel="noopener noreferrer">
                  View Source <ExternalLink className="h-3 w-3 ml-1" />
                </a>
              </Button>
            </div>
          )}
        </div>
      </section>

      {/* ===== EXECUTION & STRATEGY ===== */}
      {(insight.execution_plan?.length || insight.value_ladder?.length || insight.competitor_analysis?.length) && (
        <section className="py-10 px-6 bg-secondary/20">
          <div className="max-w-5xl mx-auto space-y-10">

            {/* Value Ladder / Offer */}
            {insight.value_ladder && insight.value_ladder.length > 0 && (
              <div>
                <h2 className="text-2xl mb-6">Revenue Strategy</h2>
                <div className="space-y-4">
                  {insight.value_ladder.map((tier: { tier?: string | null; name: string; price: string; description?: string | null; features?: string[] }, idx: number) => (
                    <div key={idx} className="p-5 bg-background rounded-xl border">
                      <div className="flex gap-4">
                        <div className="flex-shrink-0 w-10 h-10 rounded-full bg-gradient-to-br from-blue-500 to-purple-500 text-white flex items-center justify-center font-bold">
                          {idx + 1}
                        </div>
                        <div className="flex-1">
                          <div className="text-xs font-medium text-muted-foreground uppercase tracking-wide">{tier.tier?.replace('_', ' ')}</div>
                          <div className="font-semibold text-lg">
                            {tier.name} <span className="text-muted-foreground font-normal text-sm">({tier.price})</span>
                          </div>
                          <p className="text-muted-foreground text-sm mt-1">{tier.description}</p>
                          {tier.features && tier.features.length > 0 && (
                            <ul className="mt-3 space-y-1">
                              {tier.features.map((f: string, fi: number) => (
                                <li key={fi} className="flex items-center gap-2 text-sm text-muted-foreground">
                                  <CheckCircle2 className="h-3.5 w-3.5 text-green-500 flex-shrink-0" />
                                  {f}
                                </li>
                              ))}
                            </ul>
                          )}
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Execution Plan */}
            {insight.execution_plan && insight.execution_plan.length > 0 && (
              <div>
                <h2 className="text-2xl mb-6">Execution Plan</h2>
                <div className="space-y-1">
                  {insight.execution_plan.map((step, idx) => (
                    <div key={idx} className="flex gap-4">
                      <div className="flex flex-col items-center">
                        <div className="w-10 h-10 rounded-full bg-gradient-to-br from-blue-500 to-purple-500 text-white flex items-center justify-center font-bold text-sm flex-shrink-0">
                          {step.step_number}
                        </div>
                        {idx < insight.execution_plan!.length - 1 && (
                          <div className="w-px flex-1 bg-border mt-2" />
                        )}
                      </div>
                      <div className="flex-1 pb-8">
                        <div className="flex items-center justify-between mb-1">
                          <h4 className="font-semibold text-lg">{step.title}</h4>
                          <Badge variant="outline" className="text-xs">
                            <Clock className="h-3 w-3 mr-1" />
                            {step.estimated_time}
                          </Badge>
                        </div>
                        <p className="text-sm text-muted-foreground">{step.description}</p>
                        {step.resources_needed && step.resources_needed.length > 0 && (
                          <div className="flex flex-wrap gap-1 mt-2">
                            {step.resources_needed.map((r: string, ri: number) => (
                              <Badge key={ri} variant="secondary" className="text-xs">{r}</Badge>
                            ))}
                          </div>
                        )}
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Competitive Landscape */}
            {insight.competitor_analysis && insight.competitor_analysis.length > 0 && (
              <div>
                <h2 className="text-2xl mb-6">Competitive Landscape</h2>
                <div className="grid gap-4">
                  {insight.competitor_analysis.map((competitor, idx) => (
                    <div key={idx} className="p-5 bg-background rounded-xl border">
                      <div className="flex items-start justify-between">
                        <div className="flex-1">
                          <h4 className="font-semibold text-lg">{competitor.name}</h4>
                          <p className="text-sm text-muted-foreground mt-1">{competitor.description}</p>
                          <a
                            href={competitor.url}
                            target="_blank"
                            rel="noopener noreferrer"
                            className="text-sm text-blue-600 hover:underline mt-2 inline-flex items-center gap-1"
                          >
                            Visit Website <ChevronRight className="h-3 w-3" />
                          </a>
                        </div>
                        {competitor.market_position && (
                          <Badge variant="outline" className="ml-4 shrink-0">{competitor.market_position}</Badge>
                        )}
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        </section>
      )}

      {/* ===== CTA BAR (Build + Chat) ===== */}
      <section className="py-10 px-6">
        <div className="max-w-5xl mx-auto">
          <div className="grid sm:grid-cols-2 gap-4">
            <Card className="border-purple-200 bg-purple-50/50 dark:border-purple-900 dark:bg-purple-950/30">
              <CardContent className="p-5">
                <div className="flex items-center gap-2 mb-3">
                  <MessageCircle className="h-5 w-5 text-purple-600" />
                  <h3 className="font-semibold">AI Chat Strategist</h3>
                </div>
                <p className="text-sm text-muted-foreground mb-4">
                  Pressure test your idea, plan go-to-market, or get pricing strategy advice
                </p>
                <Button asChild size="sm" className="bg-purple-600 hover:bg-purple-700">
                  <Link href={`/insights/${slug}/chat`}>
                    Start Chat <ArrowRight className="h-3 w-3 ml-1" />
                  </Link>
                </Button>
              </CardContent>
            </Card>

            <Card className="border-orange-200 bg-orange-50/50 dark:border-orange-900 dark:bg-orange-950/30">
              <CardContent className="p-5">
                <div className="flex items-center gap-2 mb-3">
                  <Rocket className="h-5 w-5 text-orange-600" />
                  <h3 className="font-semibold">Build This Idea</h3>
                </div>
                <p className="text-sm text-muted-foreground mb-4">
                  Generate a complete brand package and landing page in one click
                </p>
                <Button asChild size="sm" className="bg-orange-600 hover:bg-orange-700">
                  <Link href={`/insights/${slug}/build`}>
                    Build Now <ArrowRight className="h-3 w-3 ml-1" />
                  </Link>
                </Button>
              </CardContent>
            </Card>
          </div>
        </div>
      </section>

      {/* ===== ENGAGEMENT + ACTION BAR ===== */}
      <div className="fixed bottom-0 left-0 right-0 bg-background/80 backdrop-blur-md border-t py-3 px-6 z-40">
        <div className="max-w-5xl mx-auto flex items-center justify-between">
          <div className="flex items-center gap-3">
            {/* Engagement stats (compact) */}
            {engagement && (engagement.view_count > 0 || engagement.save_count > 0) && (
              <div className="hidden sm:flex items-center gap-3 text-xs text-muted-foreground mr-3">
                {engagement.view_count > 0 && (
                  <span className="flex items-center gap-1"><Eye className="h-3 w-3" />{engagement.view_count.toLocaleString()}</span>
                )}
                {engagement.save_count > 0 && (
                  <span className="flex items-center gap-1"><Bookmark className="h-3 w-3" />{engagement.save_count.toLocaleString()}</span>
                )}
              </div>
            )}
            <Button variant="outline" size="sm" asChild>
              <Link href={`/insights/${slug}/chat`}>
                <MessageSquare className="h-4 w-4 mr-2" /> Chat
              </Link>
            </Button>
            <Button
              variant="outline"
              size="sm"
              onClick={() => setSaved(!saved)}
            >
              {saved ? (
                <><CheckCircle2 className="h-4 w-4 mr-2 text-green-500" /> Saved</>
              ) : (
                <><BookmarkPlus className="h-4 w-4 mr-2" /> Save</>
              )}
            </Button>
          </div>
          <Button size="sm" className="bg-primary text-primary-foreground" asChild>
            <Link href={`/insights/${slug}/build`}>
              <Zap className="h-4 w-4 mr-2" /> Deep Research
            </Link>
          </Button>
        </div>
      </div>
    </div>
  );
}
