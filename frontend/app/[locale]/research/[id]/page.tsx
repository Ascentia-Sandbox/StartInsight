'use client';

import { useState, useEffect } from 'react';
import { useRouter, useParams } from 'next/navigation';
import Link from 'next/link';
import { useQuery } from '@tanstack/react-query';
import {
  Loader2, AlertCircle, CheckCircle, ArrowLeft, TrendingUp,
  Users, Target, BarChart3, Zap, AlertTriangle, Map
} from 'lucide-react';
import { getSupabaseClient } from '@/lib/supabase/client';
import { fetchAnalysisById } from '@/lib/api';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Progress } from '@/components/ui/progress';
import { Breadcrumbs } from '@/components/ui/breadcrumbs';
import type { ResearchAnalysisDetail } from '@/lib/types';

export default function ResearchResultsPage() {
  const params = useParams();
  const locale = (params?.locale as string) || 'en';
  const id = params?.id as string;
  const router = useRouter();
  const [accessToken, setAccessToken] = useState<string | null>(null);
  const [isCheckingAuth, setIsCheckingAuth] = useState(true);
  const [activeTab, setActiveTab] = useState<string>('overview');

  useEffect(() => {
    const checkAuth = async () => {
      const supabase = getSupabaseClient();
      const { data: { session } } = await supabase.auth.getSession();
      if (!session) {
        router.push(`/auth/login?redirectTo=/${locale}/research/${id}`);
        return;
      }
      setAccessToken(session.access_token);
      setIsCheckingAuth(false);
    };
    checkAuth();
  }, [router, locale, id]);

  const { data: analysis, isLoading, error } = useQuery({
    queryKey: ['research-analysis', id, accessToken],
    queryFn: () => fetchAnalysisById(accessToken!, id),
    enabled: !!accessToken && !!id,
    refetchInterval: (query) => {
      if (query.state.data?.status === 'processing') return 5000;
      return false;
    },
  });

  if (isCheckingAuth || isLoading) {
    return (
      <div className="min-h-screen bg-background flex items-center justify-center">
        <div className="text-center">
          <Loader2 className="animate-spin h-8 w-8 text-primary mx-auto" />
          <p className="mt-2 text-muted-foreground">Loading analysis...</p>
        </div>
      </div>
    );
  }

  if (error || !analysis) {
    return (
      <div className="min-h-screen bg-background flex items-center justify-center">
        <Card className="max-w-md">
          <CardContent className="p-8 text-center">
            <AlertCircle className="h-12 w-12 text-red-500 mx-auto mb-4" />
            <h2 className="text-xl font-semibold mb-2">Analysis Not Found</h2>
            <p className="text-muted-foreground mb-4">
              This analysis could not be loaded. It may still be processing or no longer available.
            </p>
            <Button onClick={() => router.push(`/${locale}/workspace`)}>
              Back to Workspace
            </Button>
          </CardContent>
        </Card>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-background">
      <div className="max-w-5xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <Breadcrumbs items={[
          { label: 'Workspace', href: `/${locale}/workspace` },
          { label: 'Research', href: `/${locale}/workspace` },
          { label: 'Analysis Results' },
        ]} />

        {/* Header */}
        <div className="mt-4 mb-6">
          <div className="flex items-start justify-between gap-4">
            <div>
              <h1 className="text-2xl font-bold">Research Analysis</h1>
              <p className="text-muted-foreground mt-1 max-w-2xl line-clamp-2">
                {analysis.idea_description}
              </p>
            </div>
            <Link href={`/${locale}/workspace`}>
              <Button variant="outline" size="sm">
                <ArrowLeft className="h-4 w-4 mr-1" />
                Workspace
              </Button>
            </Link>
          </div>

          <div className="flex items-center gap-3 mt-3">
            <StatusBadge status={analysis.status} />
            {analysis.target_market && (
              <Badge variant="outline" className="text-xs">{analysis.target_market}</Badge>
            )}
            <span className="text-xs text-muted-foreground">
              {new Date(analysis.created_at).toLocaleDateString()}
            </span>
          </div>
        </div>

        {/* Processing State */}
        {analysis.status === 'processing' && (
          <Card className="mb-6">
            <CardContent className="p-4">
              <div className="flex items-center gap-3 mb-2">
                <Loader2 className="h-4 w-4 animate-spin text-blue-600" />
                <span className="text-sm font-medium">Analysis in progress...</span>
                <span className="text-xs text-muted-foreground ml-auto">{analysis.progress_percent}%</span>
              </div>
              <Progress value={analysis.progress_percent} className="h-2" />
              {analysis.current_step && (
                <p className="text-xs text-muted-foreground mt-2">{analysis.current_step}</p>
              )}
            </CardContent>
          </Card>
        )}

        {/* Failed State */}
        {analysis.status === 'failed' && (
          <Card className="mb-6 border-red-200">
            <CardContent className="p-4">
              <div className="flex items-center gap-3">
                <AlertCircle className="h-5 w-5 text-red-500" />
                <div>
                  <p className="text-sm font-medium text-red-700">Analysis failed</p>
                  {analysis.error_message && (
                    <p className="text-xs text-muted-foreground mt-0.5">{analysis.error_message}</p>
                  )}
                </div>
              </div>
            </CardContent>
          </Card>
        )}

        {/* Scores summary (completed only) */}
        {analysis.status === 'completed' && (
          <div className="grid grid-cols-3 gap-4 mb-6">
            <ScoreCard
              label="Opportunity"
              score={analysis.opportunity_score}
              icon={<TrendingUp className="h-4 w-4" />}
              color="text-emerald-600"
            />
            <ScoreCard
              label="Market Fit"
              score={analysis.market_fit_score}
              icon={<Target className="h-4 w-4" />}
              color="text-blue-600"
            />
            <ScoreCard
              label="Execution Readiness"
              score={analysis.execution_readiness}
              icon={<Zap className="h-4 w-4" />}
              color="text-purple-600"
            />
          </div>
        )}

        {/* Tabs */}
        {analysis.status === 'completed' && (
          <>
            <div className="flex gap-4 border-b mb-6 overflow-x-auto">
              {[
                { key: 'overview', label: 'Market' },
                { key: 'competitors', label: 'Competitors' },
                { key: 'value', label: 'Value & Positioning' },
                { key: 'roadmap', label: 'Roadmap' },
                { key: 'risks', label: 'Risks' },
              ].map(tab => (
                <button
                  key={tab.key}
                  onClick={() => setActiveTab(tab.key)}
                  className={`pb-2 px-1 whitespace-nowrap border-b-2 font-medium text-sm transition-colors ${
                    activeTab === tab.key
                      ? 'border-primary text-primary'
                      : 'border-transparent text-muted-foreground hover:text-foreground'
                  }`}
                >
                  {tab.label}
                </button>
              ))}
            </div>

            {activeTab === 'overview' && <MarketTab analysis={analysis} />}
            {activeTab === 'competitors' && <CompetitorsTab analysis={analysis} />}
            {activeTab === 'value' && <ValueTab analysis={analysis} />}
            {activeTab === 'roadmap' && <RoadmapTab analysis={analysis} />}
            {activeTab === 'risks' && <RisksTab analysis={analysis} />}
          </>
        )}
      </div>
    </div>
  );
}

function StatusBadge({ status }: { status: string }) {
  if (status === 'completed') return <Badge className="bg-green-100 text-green-800"><CheckCircle className="h-3 w-3 mr-1" />Completed</Badge>;
  if (status === 'processing') return <Badge className="bg-blue-100 text-blue-800"><Loader2 className="h-3 w-3 mr-1 animate-spin" />Processing</Badge>;
  if (status === 'failed') return <Badge variant="destructive"><AlertCircle className="h-3 w-3 mr-1" />Failed</Badge>;
  return <Badge variant="outline">Pending</Badge>;
}

function ScoreCard({ label, score, icon, color }: { label: string; score: number | null | undefined; icon: React.ReactNode; color: string }) {
  const pct = score !== null && score !== undefined ? Math.round(score * 100) : null;
  return (
    <Card>
      <CardContent className="p-4">
        <div className={`flex items-center gap-2 mb-1 ${color}`}>
          {icon}
          <span className="text-xs font-medium">{label}</span>
        </div>
        <div className="text-2xl font-bold">{pct !== null ? `${pct}%` : '—'}</div>
        {pct !== null && <Progress value={pct} className="h-1.5 mt-2" />}
      </CardContent>
    </Card>
  );
}

function MarketTab({ analysis }: { analysis: ResearchAnalysisDetail }) {
  const m = analysis.market_analysis;
  if (!m) return <p className="text-muted-foreground">Market data not available.</p>;

  return (
    <div className="space-y-4">
      <div className="grid grid-cols-3 gap-4">
        {[
          { label: 'Total Addressable Market (TAM)', value: m.tam },
          { label: 'Serviceable Addressable Market (SAM)', value: m.sam },
          { label: 'Serviceable Obtainable Market (SOM)', value: m.som },
        ].map(item => (
          <Card key={item.label}>
            <CardContent className="p-4">
              <p className="text-xs text-muted-foreground">{item.label}</p>
              <p className="text-xl font-bold mt-1">{item.value}</p>
            </CardContent>
          </Card>
        ))}
      </div>
      <Card>
        <CardHeader className="pb-2">
          <CardTitle className="text-sm flex items-center gap-2">
            <BarChart3 className="h-4 w-4" />
            Market Details
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-3">
          <div className="flex items-center gap-4">
            <span className="text-sm text-muted-foreground">Growth Rate:</span>
            <Badge variant="outline">{Math.round(m.growth_rate * 100)}% annually</Badge>
            <span className="text-sm text-muted-foreground ml-2">Maturity:</span>
            <Badge variant="outline" className="capitalize">{m.market_maturity}</Badge>
          </div>
          {m.key_trends.length > 0 && (
            <div>
              <p className="text-sm font-medium mb-2">Key Trends</p>
              <ul className="space-y-1">
                {m.key_trends.map((trend, i) => (
                  <li key={i} className="text-sm text-muted-foreground flex gap-2">
                    <span className="text-primary">•</span>{trend}
                  </li>
                ))}
              </ul>
            </div>
          )}
        </CardContent>
      </Card>

      {analysis.validation_signals.length > 0 && (
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm">Validation Signals</CardTitle>
          </CardHeader>
          <CardContent className="space-y-2">
            {analysis.validation_signals.map((sig, i) => (
              <div key={i} className="flex items-start gap-3 text-sm">
                <Badge variant="outline" className="shrink-0 text-xs capitalize">{sig.source}</Badge>
                <div className="flex-1">
                  <p className="text-sm">{sig.description}</p>
                  <div className="flex gap-2 mt-1">
                    <span className={`text-xs ${sig.sentiment === 'positive' ? 'text-green-600' : sig.sentiment === 'negative' ? 'text-red-600' : 'text-muted-foreground'}`}>
                      {sig.sentiment}
                    </span>
                    <span className="text-xs text-muted-foreground">• {sig.strength}</span>
                  </div>
                </div>
              </div>
            ))}
          </CardContent>
        </Card>
      )}
    </div>
  );
}

function CompetitorsTab({ analysis }: { analysis: ResearchAnalysisDetail }) {
  if (!analysis.competitor_landscape.length) return <p className="text-muted-foreground">No competitor data available.</p>;

  const threatColor: Record<string, string> = {
    low: 'text-green-600',
    medium: 'text-yellow-600',
    high: 'text-red-600',
  };

  return (
    <div className="space-y-4">
      {analysis.competitor_landscape.map((c, i) => (
        <Card key={i}>
          <CardContent className="p-4">
            <div className="flex items-start justify-between gap-4">
              <div className="flex-1 space-y-2">
                <div className="flex items-center gap-2">
                  <h3 className="font-semibold">{c.name}</h3>
                  <Badge variant="outline" className="text-xs">{c.funding}</Badge>
                  <span className={`text-xs font-medium ${threatColor[c.threat_level] ?? ''}`}>
                    {c.threat_level} threat
                  </span>
                </div>
                <p className="text-sm text-muted-foreground"><strong>Value Prop:</strong> {c.unique_value_prop}</p>
                <p className="text-sm text-muted-foreground"><strong>Weakness:</strong> {c.weakness}</p>
              </div>
              <div className="text-right">
                <p className="text-xs text-muted-foreground">Est. share</p>
                <p className="text-lg font-bold">{c.market_share_estimate}%</p>
              </div>
            </div>
          </CardContent>
        </Card>
      ))}
    </div>
  );
}

function ValueTab({ analysis }: { analysis: ResearchAnalysisDetail }) {
  return (
    <div className="space-y-4">
      {analysis.value_equation && (
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm">Value Equation (Hormozi Framework)</CardTitle>
            <CardDescription>Overall score: {analysis.value_equation.value_score.toFixed(1)}</CardDescription>
          </CardHeader>
          <CardContent className="space-y-3">
            {[
              { label: 'Dream Outcome', score: analysis.value_equation.dream_outcome_score },
              { label: 'Perceived Likelihood', score: analysis.value_equation.perceived_likelihood_score },
              { label: 'Time Delay (lower=better)', score: 11 - analysis.value_equation.time_delay_score },
              { label: 'Effort Required (lower=better)', score: 11 - analysis.value_equation.effort_sacrifice_score },
            ].map(item => (
              <div key={item.label}>
                <div className="flex justify-between text-xs mb-1">
                  <span>{item.label}</span>
                  <span className="font-medium">{item.score}/10</span>
                </div>
                <Progress value={item.score * 10} className="h-1.5" />
              </div>
            ))}
            <p className="text-sm text-muted-foreground pt-2">{analysis.value_equation.analysis}</p>
          </CardContent>
        </Card>
      )}

      {analysis.market_matrix && (
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm flex items-center gap-2"><Map className="h-4 w-4" />Market Matrix</CardTitle>
          </CardHeader>
          <CardContent className="space-y-2">
            <div className="flex items-center gap-4">
              <span className="text-sm text-muted-foreground">Quadrant:</span>
              <Badge className="capitalize">{analysis.market_matrix.quadrant.replace('_', ' ')}</Badge>
              <span className="text-sm text-muted-foreground ml-2">Demand:</span>
              <span className="text-sm font-medium">{analysis.market_matrix.demand_score}/10</span>
              <span className="text-sm text-muted-foreground ml-2">Difficulty:</span>
              <span className="text-sm font-medium">{analysis.market_matrix.difficulty_score}/10</span>
            </div>
            <p className="text-sm text-muted-foreground">{analysis.market_matrix.positioning_strategy}</p>
          </CardContent>
        </Card>
      )}

      {analysis.acp_framework && (
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm flex items-center gap-2"><Users className="h-4 w-4" />ACP Framework</CardTitle>
          </CardHeader>
          <CardContent className="space-y-3">
            {[
              { label: 'Awareness', score: analysis.acp_framework.awareness_score },
              { label: 'Consideration', score: analysis.acp_framework.consideration_score },
              { label: 'Purchase', score: analysis.acp_framework.purchase_score },
            ].map(item => (
              <div key={item.label}>
                <div className="flex justify-between text-xs mb-1">
                  <span>{item.label}</span>
                  <span className="font-medium">{item.score}/10</span>
                </div>
                <Progress value={item.score * 10} className="h-1.5" />
              </div>
            ))}
            <p className="text-sm text-muted-foreground"><strong>Bottleneck:</strong> {analysis.acp_framework.funnel_bottleneck}</p>
            <div>
              <p className="text-sm font-medium mb-1">Recommended Channels</p>
              <div className="flex flex-wrap gap-1">
                {analysis.acp_framework.recommended_channels.map((ch, i) => (
                  <Badge key={i} variant="outline" className="text-xs">{ch}</Badge>
                ))}
              </div>
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  );
}

function RoadmapTab({ analysis }: { analysis: ResearchAnalysisDetail }) {
  if (!analysis.execution_roadmap.length) return <p className="text-muted-foreground">No roadmap data available.</p>;

  return (
    <div className="space-y-4">
      {analysis.execution_roadmap.map((phase) => (
        <Card key={phase.phase_number}>
          <CardContent className="p-4">
            <div className="flex items-start gap-3">
              <div className="flex items-center justify-center w-8 h-8 rounded-full bg-primary text-primary-foreground text-sm font-bold shrink-0">
                {phase.phase_number}
              </div>
              <div className="flex-1">
                <div className="flex items-center gap-2 mb-1">
                  <h3 className="font-semibold">{phase.name}</h3>
                  <Badge variant="outline" className="text-xs">{phase.duration}</Badge>
                  <Badge variant="outline" className="text-xs">{phase.budget_estimate}</Badge>
                </div>
                {phase.milestones.length > 0 && (
                  <div className="mb-2">
                    <p className="text-xs font-medium text-muted-foreground mb-1">Milestones</p>
                    <ul className="space-y-0.5">
                      {phase.milestones.map((m, i) => (
                        <li key={i} className="text-sm flex gap-2"><CheckCircle className="h-3 w-3 text-green-500 mt-0.5 shrink-0" />{m}</li>
                      ))}
                    </ul>
                  </div>
                )}
                {phase.key_risks.length > 0 && (
                  <div>
                    <p className="text-xs font-medium text-muted-foreground mb-1">Risks</p>
                    <ul className="space-y-0.5">
                      {phase.key_risks.map((r, i) => (
                        <li key={i} className="text-sm flex gap-2 text-muted-foreground"><AlertTriangle className="h-3 w-3 text-yellow-500 mt-0.5 shrink-0" />{r}</li>
                      ))}
                    </ul>
                  </div>
                )}
              </div>
            </div>
          </CardContent>
        </Card>
      ))}
    </div>
  );
}

function RisksTab({ analysis }: { analysis: ResearchAnalysisDetail }) {
  const r = analysis.risk_assessment;
  if (!r) return <p className="text-muted-foreground">No risk data available.</p>;

  const riskColor = (score: number) => score >= 7 ? 'text-red-600' : score >= 5 ? 'text-yellow-600' : 'text-green-600';

  return (
    <div className="space-y-4">
      <div className="grid grid-cols-2 gap-4">
        {[
          { label: 'Technical Risk', score: r.technical_risk },
          { label: 'Market Risk', score: r.market_risk },
          { label: 'Team/Execution Risk', score: r.team_risk },
          { label: 'Financial Risk', score: r.financial_risk },
        ].map(item => (
          <Card key={item.label}>
            <CardContent className="p-4">
              <p className="text-xs text-muted-foreground">{item.label}</p>
              <p className={`text-2xl font-bold ${riskColor(item.score)}`}>{item.score}/10</p>
              <Progress value={item.score * 10} className="h-1.5 mt-2" />
            </CardContent>
          </Card>
        ))}
      </div>
      <Card>
        <CardHeader className="pb-2">
          <CardTitle className="text-sm">Overall Risk</CardTitle>
          <CardDescription>{Math.round(r.overall_risk * 100)}%</CardDescription>
        </CardHeader>
        {r.mitigation_strategies.length > 0 && (
          <CardContent>
            <p className="text-sm font-medium mb-2">Mitigation Strategies</p>
            <ul className="space-y-1">
              {r.mitigation_strategies.map((s, i) => (
                <li key={i} className="text-sm text-muted-foreground flex gap-2">
                  <span className="text-primary font-bold">{i + 1}.</span>{s}
                </li>
              ))}
            </ul>
          </CardContent>
        )}
      </Card>
    </div>
  );
}
