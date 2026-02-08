'use client';

import { useQuery } from '@tanstack/react-query';
import { useParams } from 'next/navigation';
import { fetchInsightById } from '@/lib/api';
import { Card, CardContent, CardHeader } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Skeleton } from '@/components/ui/skeleton';
import { ChartLoadingSkeleton } from '@/components/ui/chart-loading-skeleton';
import { Button } from '@/components/ui/button';
import { formatDistanceToNow } from 'date-fns';
import Link from 'next/link';
import { BuilderIntegration } from '@/components/builder/builder-integration';
import { ScoreRadar } from '@/components/evidence/score-radar';
import {
  DollarSign, Rocket, TrendingUp, Target, Zap, Shield,
  Clock, ArrowRight, CheckCircle2, AlertCircle, BarChart3,
  Users, Globe, ChevronRight, Lightbulb, Search
} from 'lucide-react';
import { Breadcrumbs } from '@/components/ui/breadcrumbs';
import {
  AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip,
  ResponsiveContainer
} from 'recharts';

// Generate mock trend chart data from trend keywords
function generateTrendChartData(keywords: Array<{ keyword: string; volume: string; growth: string }>) {
  if (!keywords || keywords.length === 0) return [];
  // Parse volume string like "27.1K" -> 27100
  const parseVolume = (vol: string) => {
    const num = parseFloat(vol.replace(/[^0-9.]/g, ''));
    if (vol.includes('K')) return num * 1000;
    if (vol.includes('M')) return num * 1000000;
    return num;
  };
  const currentVol = parseVolume(keywords[0].volume);
  // Generate monthly data points going back 3 years
  const months = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'];
  const data = [];
  const growthPct = parseFloat(keywords[0].growth.replace(/[^0-9.-]/g, '')) / 100;
  const yearsBack = 3;
  for (let y = 0; y < yearsBack; y++) {
    const year = 2026 - yearsBack + y;
    for (let m = 0; m < 12; m++) {
      const progress = (y * 12 + m) / (yearsBack * 12);
      // Exponential growth curve
      const base = currentVol * Math.pow(1 + growthPct, progress - 1);
      const noise = 1 + (Math.sin(m * 2.1 + y * 3.7) * 0.15);
      data.push({
        date: `${months[m]} ${year}`,
        volume: Math.max(0, Math.round(base * noise)),
      });
    }
  }
  return data;
}

// Format number for display
function formatNumber(num: number): string {
  if (num >= 1000000) return (num / 1000000).toFixed(1) + 'M';
  if (num >= 1000) return (num / 1000).toFixed(1) + 'K';
  return num.toString();
}

// Score label helper
function getScoreLabel(score: number): string {
  if (score >= 9) return 'Exceptional';
  if (score >= 7) return 'Strong';
  if (score >= 5) return 'Moderate';
  if (score >= 3) return 'Developing';
  return 'Low';
}

// Score color helper
function getScoreColor(score: number): string {
  if (score >= 8) return 'text-green-600 border-green-500';
  if (score >= 6) return 'text-blue-600 border-blue-500';
  if (score >= 4) return 'text-amber-600 border-amber-500';
  return 'text-red-600 border-red-500';
}

// Confidence badge color
function getConfidenceColor(conf: string): string {
  if (conf === 'High') return 'bg-green-100 text-green-800';
  if (conf === 'Medium') return 'bg-amber-100 text-amber-800';
  return 'bg-gray-100 text-gray-800';
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
  const id = params.id as string;

  const { data: insight, isLoading, error } = useQuery({
    queryKey: ['insight', id],
    queryFn: () => fetchInsightById(id),
    enabled: !!id,
  });

  if (isLoading) {
    return (
      <div className="container mx-auto px-4 py-8 max-w-6xl space-y-6">
        <Skeleton className="h-10 w-3/4" />
        <Skeleton className="h-6 w-1/2" />
        <div className="grid grid-cols-3 gap-6">
          <div className="col-span-2 space-y-4">
            <Skeleton className="h-64" />
            <Skeleton className="h-48" />
          </div>
          <div className="space-y-4">
            <Skeleton className="h-32" />
            <Skeleton className="h-48" />
          </div>
        </div>
        <ChartLoadingSkeleton />
      </div>
    );
  }

  if (error || !insight) {
    return (
      <div className="container mx-auto px-4 py-8 max-w-4xl">
        <div className="text-center">
          <h2 className="text-2xl font-bold text-red-600">Insight not found</h2>
          <p className="text-muted-foreground mt-2">
            {error instanceof Error ? error.message : 'This insight does not exist or could not be loaded.'}
          </p>
          <Button asChild className="mt-4">
            <Link href="/insights">Back to All Insights</Link>
          </Button>
        </div>
      </div>
    );
  }

  // Generate trend data from trend_keywords, or fallback from insight scores
  const hasTrendKeywords = insight.trend_keywords && insight.trend_keywords.length > 0;
  const fallbackKeyword = !hasTrendKeywords ? {
    keyword: insight.proposed_solution?.split(/\s+/).slice(0, 3).join(' ') || 'Market Trend',
    volume: formatNumber(((insight.opportunity_score || 5) * 3000) + 5000),
    growth: `+${((insight.why_now_score || 5) * 5) + 10}%`,
  } : null;
  const trendChartData = generateTrendChartData(
    hasTrendKeywords ? insight.trend_keywords! : fallbackKeyword ? [fallbackKeyword] : []
  );
  const firstKeyword = hasTrendKeywords ? insight.trend_keywords![0] : fallbackKeyword;

  return (
    <div className="container mx-auto px-4 py-8 max-w-6xl">
      <Breadcrumbs items={[
        { label: 'Insights', href: '/insights' },
        { label: insight.proposed_solution?.slice(0, 50) || 'Detail' },
      ]} />

      {/* Hero Header */}
      <div className="mb-8">
        <div className="flex flex-wrap items-center gap-2 mb-4">
          {insight.raw_signal && (
            <Badge variant="secondary" className="text-xs font-medium uppercase">
              {insight.raw_signal.source}
            </Badge>
          )}
          {insight.why_now_score && insight.why_now_score >= 7 && (
            <Badge className="bg-red-100 text-red-800 border-red-200">
              <Clock className="h-3 w-3 mr-1" /> Perfect Timing
            </Badge>
          )}
          {insight.opportunity_score && insight.opportunity_score >= 8 && (
            <Badge className="bg-green-100 text-green-800 border-green-200">
              <TrendingUp className="h-3 w-3 mr-1" /> Massive Market
            </Badge>
          )}
          {insight.feasibility_score && insight.feasibility_score >= 7 && (
            <Badge className="bg-blue-100 text-blue-800 border-blue-200">
              <Zap className="h-3 w-3 mr-1" /> Highly Feasible
            </Badge>
          )}
        </div>
        <h1 className="text-3xl md:text-4xl font-bold leading-tight mb-3">
          {insight.proposed_solution}
        </h1>
        <p className="text-muted-foreground text-sm">
          *Analysis, scores, and revenue estimates are educational and based on assumptions. Results vary by execution and market conditions.
        </p>
      </div>

      {/* Two-column layout: Content (left) + Sidebar (right) */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">

        {/* ===== LEFT COLUMN (2/3 width) ===== */}
        <div className="lg:col-span-2 space-y-8">

          {/* Search Trend Chart + Score Cards row */}
          <div className="grid grid-cols-1 md:grid-cols-5 gap-6">
            {/* Trend Line Chart (left 3/5) */}
            <div className="md:col-span-3">
              <Card>
                <CardContent className="p-6">
                  {firstKeyword && (
                    <div className="flex items-center justify-between mb-4">
                      <div className="flex items-center gap-2">
                        <Search className="h-4 w-4 text-muted-foreground" />
                        <span className="text-sm text-muted-foreground">Keyword:</span>
                        <span className="font-medium">{firstKeyword.keyword}</span>
                      </div>
                      <div className="flex items-center gap-4">
                        <div className="text-right">
                          <div className="text-2xl font-bold text-blue-600">{firstKeyword.volume}</div>
                          <div className="text-xs text-muted-foreground">Volume</div>
                        </div>
                        <div className="text-right">
                          <div className="text-2xl font-bold text-green-600">{firstKeyword.growth}</div>
                          <div className="text-xs text-muted-foreground">Growth</div>
                        </div>
                      </div>
                    </div>
                  )}
                  {trendChartData.length > 0 ? (
                    <ResponsiveContainer width="100%" height={240}>
                      <AreaChart data={trendChartData}>
                        <defs>
                          <linearGradient id="trendGradient" x1="0" y1="0" x2="0" y2="1">
                            <stop offset="5%" stopColor="#3b82f6" stopOpacity={0.3} />
                            <stop offset="95%" stopColor="#3b82f6" stopOpacity={0} />
                          </linearGradient>
                        </defs>
                        <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
                        <XAxis
                          dataKey="date"
                          tick={{ fontSize: 11 }}
                          interval={5}
                          stroke="#9ca3af"
                        />
                        <YAxis
                          tick={{ fontSize: 11 }}
                          tickFormatter={(v) => formatNumber(v)}
                          stroke="#9ca3af"
                        />
                        <Tooltip
                          formatter={(value) => [formatNumber(Number(value)), 'Search Volume']}
                          contentStyle={{ borderRadius: '8px', border: '1px solid #e5e7eb' }}
                        />
                        <Area
                          type="monotone"
                          dataKey="volume"
                          stroke="#3b82f6"
                          strokeWidth={2}
                          fill="url(#trendGradient)"
                        />
                      </AreaChart>
                    </ResponsiveContainer>
                  ) : (
                    <div className="flex items-center justify-center h-60 text-muted-foreground text-sm">
                      Loading trend data...
                    </div>
                  )}
                  {!hasTrendKeywords && trendChartData.length > 0 && (
                    <p className="text-[10px] text-muted-foreground mt-1 text-center">Estimated based on opportunity and timing scores</p>
                  )}
                </CardContent>
              </Card>
            </div>

            {/* Score Cards (right 2/5) */}
            <div className="md:col-span-2 grid grid-cols-2 gap-3">
              {insight.opportunity_score != null && (
                <Card className={`border-b-4 ${getScoreColor(insight.opportunity_score)}`}>
                  <CardContent className="p-4">
                    <div className="text-xs font-medium text-muted-foreground mb-1">Opportunity</div>
                    <div className="text-3xl font-bold">{insight.opportunity_score}</div>
                    <div className="text-xs text-muted-foreground">{getScoreLabel(insight.opportunity_score)}</div>
                  </CardContent>
                </Card>
              )}
              {insight.problem_score != null && (
                <Card className={`border-b-4 ${getScoreColor(insight.problem_score)}`}>
                  <CardContent className="p-4">
                    <div className="text-xs font-medium text-muted-foreground mb-1">Problem</div>
                    <div className="text-3xl font-bold">{insight.problem_score}</div>
                    <div className="text-xs text-muted-foreground">{getScoreLabel(insight.problem_score)}</div>
                  </CardContent>
                </Card>
              )}
              {insight.feasibility_score != null && (
                <Card className={`border-b-4 ${getScoreColor(insight.feasibility_score)}`}>
                  <CardContent className="p-4">
                    <div className="text-xs font-medium text-muted-foreground mb-1">Feasibility</div>
                    <div className="text-3xl font-bold">{insight.feasibility_score}</div>
                    <div className="text-xs text-muted-foreground">{getScoreLabel(insight.feasibility_score)}</div>
                  </CardContent>
                </Card>
              )}
              {insight.why_now_score != null && (
                <Card className={`border-b-4 ${getScoreColor(insight.why_now_score)}`}>
                  <CardContent className="p-4">
                    <div className="text-xs font-medium text-muted-foreground mb-1">Why Now</div>
                    <div className="text-3xl font-bold">{insight.why_now_score}</div>
                    <div className="text-xs text-muted-foreground">{getScoreLabel(insight.why_now_score)}</div>
                  </CardContent>
                </Card>
              )}
            </div>
          </div>

          {/* Problem Statement */}
          <div>
            <div className="space-y-4">
              {insight.problem_statement.split('\n\n').filter(Boolean).map((paragraph, idx) => (
                <p key={idx} className="text-muted-foreground leading-relaxed">
                  {paragraph}
                </p>
              ))}
            </div>
          </div>

          {/* Market size */}
          {insight.market_sizing ? (
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4 p-5 bg-muted/30 rounded-lg border">
              <div>
                <div className="text-xs font-medium text-muted-foreground mb-1">TAM (Total Addressable)</div>
                <div className="text-xl font-bold text-blue-600">{insight.market_sizing.tam}</div>
              </div>
              <div>
                <div className="text-xs font-medium text-muted-foreground mb-1">SAM (Serviceable)</div>
                <div className="text-xl font-bold text-green-600">{insight.market_sizing.sam}</div>
              </div>
              <div>
                <div className="text-xs font-medium text-muted-foreground mb-1">SOM (Obtainable)</div>
                <div className="text-xl font-bold text-violet-600">{insight.market_sizing.som}</div>
              </div>
            </div>
          ) : insight.market_size_estimate ? (
            <div className="flex items-center gap-4 p-4 bg-muted/30 rounded-lg border">
              <DollarSign className="h-5 w-5 text-green-600" />
              <div>
                <span className="font-semibold">Market Size:</span>
                <span className="ml-2 text-muted-foreground">{insight.market_size_estimate}</span>
              </div>
            </div>
          ) : null}

          {/* Value Ladder / Offer */}
          {insight.value_ladder && insight.value_ladder.length > 0 && (
            <Card>
              <CardContent className="p-6">
                <h2 className="text-2xl font-semibold mb-6">Offer</h2>
                <div className="space-y-6">
                  {insight.value_ladder.map((tier: { tier?: string | null; name: string; price: string; description?: string | null; features?: string[] }, idx: number) => (
                    <div key={idx} className="flex gap-4">
                      <div className="flex-shrink-0 w-8 h-8 rounded-full bg-blue-100 text-blue-700 flex items-center justify-center font-bold text-sm">
                        {idx + 1}
                      </div>
                      <div className="flex-1">
                        <div className="text-xs font-medium text-muted-foreground uppercase tracking-wide">{tier.tier?.replace('_', ' ')}</div>
                        <div className="font-semibold text-lg">
                          {tier.name} <span className="text-muted-foreground font-normal text-sm">({tier.price})</span>
                        </div>
                        <p className="text-muted-foreground text-sm mt-1">{tier.description}</p>
                        {tier.features && tier.features.length > 0 && (
                          <ul className="mt-2 space-y-1">
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
                  ))}
                </div>
              </CardContent>
            </Card>
          )}

          {/* Why Now? */}
          {insight.why_now_analysis && (
            <Card>
              <CardContent className="p-6">
                <h2 className="text-2xl font-semibold mb-4">Why Now?</h2>
                <p className="text-muted-foreground leading-relaxed">{insight.why_now_analysis}</p>
              </CardContent>
            </Card>
          )}

          {/* Proof & Signals */}
          {insight.proof_signals && insight.proof_signals.length > 0 && (
            <Card>
              <CardContent className="p-6">
                <h2 className="text-2xl font-semibold mb-4">Proof & Signals</h2>
                <div className="space-y-4">
                  {insight.proof_signals.map((signal, idx) => (
                    <div key={idx} className="flex items-start gap-3 p-3 bg-muted/30 rounded-lg">
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
              </CardContent>
            </Card>
          )}

          {/* The Market Gap */}
          {insight.market_gap_analysis && (
            <Card>
              <CardContent className="p-6">
                <h2 className="text-2xl font-semibold mb-4">The Market Gap</h2>
                <p className="text-muted-foreground leading-relaxed">{insight.market_gap_analysis}</p>
              </CardContent>
            </Card>
          )}

          {/* Execution Plan */}
          {insight.execution_plan && insight.execution_plan.length > 0 && (
            <Card>
              <CardContent className="p-6">
                <h2 className="text-2xl font-semibold mb-6">Execution Plan</h2>
                <div className="space-y-4">
                  {insight.execution_plan.map((step, idx) => (
                    <div key={idx} className="flex gap-4">
                      <div className="flex-shrink-0">
                        <div className="w-8 h-8 rounded-full bg-gradient-to-br from-blue-500 to-purple-500 text-white flex items-center justify-center font-bold text-sm">
                          {step.step_number}
                        </div>
                        {idx < insight.execution_plan!.length - 1 && (
                          <div className="w-px h-full bg-border mx-auto mt-1" />
                        )}
                      </div>
                      <div className="flex-1 pb-4">
                        <div className="flex items-center justify-between">
                          <h4 className="font-semibold">{step.title}</h4>
                          <Badge variant="outline" className="text-xs">
                            <Clock className="h-3 w-3 mr-1" />
                            {step.estimated_time}
                          </Badge>
                        </div>
                        <p className="text-sm text-muted-foreground mt-1">{step.description}</p>
                        {step.resources_needed && step.resources_needed.length > 0 && (
                          <div className="flex flex-wrap gap-1 mt-2">
                            {step.resources_needed.map((r, ri) => (
                              <Badge key={ri} variant="secondary" className="text-xs">{r}</Badge>
                            ))}
                          </div>
                        )}
                      </div>
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>
          )}

          {/* Competitive Landscape */}
          {insight.competitor_analysis && insight.competitor_analysis.length > 0 && (
            <Card>
              <CardContent className="p-6">
                <h2 className="text-2xl font-semibold mb-6">Competitive Landscape</h2>
                <div className="space-y-4">
                  {insight.competitor_analysis.map((competitor, idx) => (
                    <div key={idx} className="flex items-start justify-between p-4 bg-muted/30 rounded-lg">
                      <div className="flex-1">
                        <h4 className="font-semibold">{competitor.name}</h4>
                        <p className="text-sm text-muted-foreground mt-1">{competitor.description}</p>
                        <a
                          href={competitor.url}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="text-sm text-blue-600 hover:underline mt-1 inline-flex items-center gap-1"
                        >
                          Visit Website <ChevronRight className="h-3 w-3" />
                        </a>
                      </div>
                      {competitor.market_position && (
                        <Badge variant="outline" className="ml-4 shrink-0">{competitor.market_position}</Badge>
                      )}
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>
          )}

          {/* 8-Dimension Radar Chart */}
          {(insight.opportunity_score || insight.problem_score || insight.feasibility_score) && (
            <Card>
              <CardContent className="p-6">
                <div className="max-w-lg mx-auto">
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
                    size="lg"
                  />
                </div>
              </CardContent>
            </Card>
          )}
        </div>

        {/* ===== RIGHT SIDEBAR (1/3 width) ===== */}
        <div className="space-y-6">

          {/* Business Fit Card */}
          <Card>
            <CardContent className="p-5">
              <h3 className="font-semibold mb-4">Business Fit</h3>
              <div className="space-y-4">
                {insight.revenue_potential_score && (
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-2">
                      <DollarSign className="h-4 w-4 text-green-500" />
                      <div>
                        <div className="text-sm font-medium">Revenue Potential</div>
                        <div className="text-xs text-muted-foreground">
                          {insight.revenue_potential_score === '$' && 'Up to $10K/mo'}
                          {insight.revenue_potential_score === '$$' && '$10K-$50K/mo'}
                          {insight.revenue_potential_score === '$$$' && '$50K-$200K/mo'}
                          {insight.revenue_potential_score === '$$$$' && '$200K+/mo'}
                        </div>
                      </div>
                    </div>
                    <span className="text-lg font-bold text-green-600">{insight.revenue_potential_score}</span>
                  </div>
                )}
                {insight.execution_difficulty_score != null && (
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-2">
                      <Zap className="h-4 w-4 text-amber-500" />
                      <div>
                        <div className="text-sm font-medium">Execution Difficulty</div>
                        <div className="text-xs text-muted-foreground">
                          {insight.execution_difficulty_score <= 3 ? 'Solo-friendly build' :
                           insight.execution_difficulty_score <= 6 ? 'Small team needed' : 'Complex build'}
                        </div>
                      </div>
                    </div>
                    <span className="text-lg font-bold text-amber-600">{insight.execution_difficulty_score}/10</span>
                  </div>
                )}
                {insight.go_to_market_score != null && (
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-2">
                      <Rocket className="h-4 w-4 text-blue-500" />
                      <div>
                        <div className="text-sm font-medium">Go-To-Market</div>
                        <div className="text-xs text-muted-foreground">
                          {insight.go_to_market_score >= 8 ? 'Viral potential' :
                           insight.go_to_market_score >= 6 ? 'Strong channels' : 'Needs strategy'}
                        </div>
                      </div>
                    </div>
                    <span className="text-lg font-bold text-blue-600">{insight.go_to_market_score}/10</span>
                  </div>
                )}
                {insight.founder_fit_score != null && (
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-2">
                      <Target className="h-4 w-4 text-purple-500" />
                      <div>
                        <div className="text-sm font-medium">Founder Fit</div>
                        <div className="text-xs text-muted-foreground">
                          {insight.founder_fit_score >= 8 ? 'Anyone can build' :
                           insight.founder_fit_score >= 6 ? 'Some expertise needed' : 'Domain expert required'}
                        </div>
                      </div>
                    </div>
                    <span className="text-lg font-bold text-purple-600">{insight.founder_fit_score}/10</span>
                  </div>
                )}
              </div>
            </CardContent>
          </Card>

          {/* Start Building in 1-click */}
          <Card>
            <CardContent className="p-5">
              <div className="flex items-center gap-2 mb-3">
                <Rocket className="h-5 w-5 text-blue-600" />
                <h3 className="font-semibold">Start Building in 1-click</h3>
              </div>
              <p className="text-sm text-muted-foreground mb-4">Turn this idea into your business with pre-built prompts</p>
              <BuilderIntegration insight={insight} compact />
            </CardContent>
          </Card>

          {/* Community Signals */}
          {insight.community_signals_chart && insight.community_signals_chart.length > 0 && (
            <Card>
              <CardContent className="p-5">
                <h3 className="font-semibold mb-4">Community Signals</h3>
                <div className="space-y-3">
                  {insight.community_signals_chart.map((signal, idx) => (
                    <div key={idx} className="flex items-center justify-between">
                      <div className="flex items-center gap-3">
                        {getPlatformIcon(signal.platform || '')}
                        <div>
                          <div className="text-sm font-medium">{signal.platform || 'Other'}</div>
                          <div className="text-xs text-muted-foreground">{signal.members}</div>
                        </div>
                      </div>
                      <span className={`text-sm font-bold ${signal.score >= 7 ? 'text-green-600' : signal.score >= 5 ? 'text-amber-600' : 'text-gray-500'}`}>
                        {signal.score} / 10
                      </span>
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>
          )}

          {/* Trend Keywords */}
          {insight.trend_keywords && insight.trend_keywords.length > 1 && (
            <Card>
              <CardContent className="p-5">
                <h3 className="font-semibold mb-4">Related Keywords</h3>
                <div className="space-y-3">
                  {insight.trend_keywords.slice(1).map((kw, idx) => (
                    <div key={idx} className="flex items-center justify-between text-sm">
                      <span className="font-medium">{kw.keyword}</span>
                      <div className="flex items-center gap-2">
                        <span className="text-muted-foreground">{kw.volume}</span>
                        <span className="text-green-600 font-medium">{kw.growth}</span>
                      </div>
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>
          )}

          {/* Source Info */}
          {insight.raw_signal && (
            <Card>
              <CardContent className="p-5">
                <h3 className="font-semibold mb-3">Source</h3>
                <div className="space-y-2 text-sm">
                  <div className="flex justify-between">
                    <span className="text-muted-foreground">Platform</span>
                    <span className="font-medium capitalize">{insight.raw_signal.source.replace('_', ' ')}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-muted-foreground">Discovered</span>
                    <span>{formatDistanceToNow(new Date(insight.created_at), { addSuffix: true })}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-muted-foreground">Market</span>
                    <Badge variant="outline">{insight.market_size_estimate}</Badge>
                  </div>
                </div>
                <Button asChild variant="outline" size="sm" className="w-full mt-4">
                  <a href={insight.raw_signal.url} target="_blank" rel="noopener noreferrer">
                    View Original Signal <ArrowRight className="h-3 w-3 ml-1" />
                  </a>
                </Button>
              </CardContent>
            </Card>
          )}
        </div>
      </div>
    </div>
  );
}
