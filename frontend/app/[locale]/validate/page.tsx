'use client';

import { useState, useEffect } from 'react';
import { useRouter, useParams } from 'next/navigation';
import { useMutation } from '@tanstack/react-query';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Label } from '@/components/ui/label';
import { Textarea } from '@/components/ui/textarea';
import { Badge } from '@/components/ui/badge';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import { ScoreRadar } from '@/components/evidence/score-radar';
import { getSupabaseClient } from '@/lib/supabase/client';
import { config } from '@/lib/env';
import { saveInsight } from '@/lib/api';
import { toast } from 'sonner';
import {
  Loader2,
  Sparkles,
  Target,
  Users,
  DollarSign,
  TrendingUp,
  ArrowRight,
  Lightbulb,
  AlertTriangle,
  Lock,
  Bookmark,
  CheckCircle,
} from 'lucide-react';

const TARGET_MARKETS = [
  'B2B SaaS',
  'B2C Consumer',
  'Enterprise',
  'SMB',
  'Developer Tools',
  'Fintech',
  'Healthcare',
  'Education',
  'E-commerce',
  'AI/ML',
  'Climate Tech',
  'Creator Economy',
];

const BUDGET_RANGES = [
  '$0 - $5K (Bootstrap)',
  '$5K - $25K (Pre-seed)',
  '$25K - $100K (Seed)',
  '$100K - $500K (Series A)',
  '$500K+ (Growth)',
];

interface SimilarIdea {
  id: string;
  title: string | null;
  proposed_solution: string;
  relevance_score: number;
  opportunity_score: number | null;
  market_size_estimate: string;
}

interface MarketSizing {
  tam: string;
  sam: string;
  som: string;
  growth_rate: string;
}

interface ValueLadderTier {
  tier_name: string;
  price: string;
  description: string;
  features: string[];
}

interface ValidationResult {
  insight_id: string | null;
  relevance_score: number;
  opportunity_score: number | null;
  problem_score: number | null;
  feasibility_score: number | null;
  why_now_score: number | null;
  execution_difficulty: number | null;
  go_to_market_score: number | null;
  founder_fit_score: number | null;
  revenue_potential: string | null;
  radar_data: { dimension: string; value: number; max: number }[];
  problem_statement: string;
  proposed_solution: string;
  market_size_estimate: string;
  market_gap_analysis: string | null;
  why_now_analysis: string | null;
  market_sizing: MarketSizing | null;
  value_ladder: ValueLadderTier[] | null;
  similar_ideas: SimilarIdea[];
  competition_overlap: number;
}

async function validateIdea(
  accessToken: string,
  body: { idea_description: string; target_market: string | null; budget: string | null }
): Promise<ValidationResult> {
  const res = await fetch(`${config.apiUrl}/api/validate`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      Authorization: `Bearer ${accessToken}`,
    },
    body: JSON.stringify(body),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: 'Validation failed' }));
    throw new Error(err.detail || 'Validation failed');
  }
  return res.json();
}

function getOverallRating(score: number) {
  if (score >= 0.8) return { label: 'Excellent', color: 'bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-300' };
  if (score >= 0.6) return { label: 'Good', color: 'bg-blue-100 text-blue-800 dark:bg-blue-900 dark:text-blue-300' };
  if (score >= 0.4) return { label: 'Fair', color: 'bg-yellow-100 text-yellow-800 dark:bg-yellow-900 dark:text-yellow-300' };
  return { label: 'Weak', color: 'bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-300' };
}

export default function ValidatePage() {
  const router = useRouter();
  const params = useParams();
  const locale = (params?.locale as string) || 'en';
  const [accessToken, setAccessToken] = useState<string | null>(null);
  const [authLoading, setAuthLoading] = useState(true);
  const [ideaDescription, setIdeaDescription] = useState('');
  const [targetMarket, setTargetMarket] = useState('');
  const [budget, setBudget] = useState('');
  const [saved, setSaved] = useState(false);
  const [saving, setSaving] = useState(false);

  // Get auth token on mount
  useEffect(() => {
    const supabase = getSupabaseClient();
    supabase.auth.getSession().then(({ data }: { data: { session: { access_token: string } | null } }) => {
      setAccessToken(data.session?.access_token ?? null);
      setAuthLoading(false);
    });
  }, []);

  const mutation = useMutation({
    mutationFn: () =>
      validateIdea(accessToken!, {
        idea_description: ideaDescription,
        target_market: targetMarket || null,
        budget: budget || null,
      }),
    onMutate: () => setSaved(false),
  });

  const result = mutation.data;
  const rating = result ? getOverallRating(result.relevance_score) : null;

  const handleSave = async () => {
    if (!accessToken || !result?.insight_id) return;
    setSaving(true);
    try {
      await saveInsight(accessToken, result.insight_id);
      setSaved(true);
      toast.success('Saved to your workspace');
    } catch {
      toast.error('Failed to save insight');
    } finally {
      setSaving(false);
    }
  };

  const handleDeepResearch = () => {
    const searchParams = new URLSearchParams();
    if (ideaDescription) searchParams.set('idea', ideaDescription);
    if (targetMarket) searchParams.set('market', targetMarket);
    router.push(`/${locale}/research?${searchParams.toString()}`);
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-background via-background to-muted/30">
      {/* Hero Section */}
      <div className="hero-gradient border-b">
        <div className="container mx-auto max-w-5xl px-4 pt-16 pb-12">
          <div className="text-center">
            <div className="inline-flex items-center gap-2 bg-primary/10 text-primary rounded-full px-4 py-1.5 text-sm font-medium mb-4">
              <Sparkles className="h-4 w-4" />
              AI-Powered Idea Validation
            </div>
            <h1 className="text-4xl md:text-5xl tracking-tight mb-3">
              Validate Your Startup Idea
            </h1>
            <p className="text-muted-foreground text-lg max-w-2xl mx-auto">
              Get instant 8-dimension scoring, market analysis, and competitive landscape.
              More comprehensive than any other idea validation tool.
            </p>
            {!authLoading && (
              <div className="mt-4 inline-flex items-center gap-2 bg-amber-100 dark:bg-amber-900/30 text-amber-800 dark:text-amber-300 rounded-full px-4 py-1.5 text-sm font-medium">
                {!accessToken && <Lock className="h-3.5 w-3.5" />}
                Free tier: 3 validations/month
              </div>
            )}
          </div>
        </div>
      </div>

      <div className="container mx-auto max-w-5xl px-4 py-10">

        {/* Input Form */}
        <Card className="mb-8">
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Lightbulb className="h-5 w-5" />
              Describe Your Idea
            </CardTitle>
            <CardDescription>
              Be specific about the problem, solution, and target audience for the most accurate analysis.
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div>
              <Label htmlFor="idea">Idea Description *</Label>
              <Textarea
                id="idea"
                placeholder="E.g., An AI-powered tool that automatically generates personalized meal plans based on dietary restrictions, health goals, and local grocery store availability. Targets busy professionals who want to eat healthier but don't have time to plan meals..."
                value={ideaDescription}
                onChange={(e) => setIdeaDescription(e.target.value)}
                rows={5}
                className="mt-1.5"
                minLength={20}
                maxLength={5000}
              />
              <p className="text-xs text-muted-foreground mt-1">
                {ideaDescription.length}/5000 characters (min 20)
              </p>
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              <div>
                <Label>Target Market</Label>
                <Select onValueChange={setTargetMarket} value={targetMarket || undefined}>
                  <SelectTrigger className="mt-1.5">
                    <SelectValue placeholder="Select market..." />
                  </SelectTrigger>
                  <SelectContent>
                    {TARGET_MARKETS.map((m) => (
                      <SelectItem key={m} value={m}>{m}</SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
              <div>
                <Label>Budget Range</Label>
                <Select onValueChange={setBudget} value={budget || undefined}>
                  <SelectTrigger className="mt-1.5">
                    <SelectValue placeholder="Select budget..." />
                  </SelectTrigger>
                  <SelectContent>
                    {BUDGET_RANGES.map((b) => (
                      <SelectItem key={b} value={b}>{b}</SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
            </div>

            <Button
              onClick={() => mutation.mutate()}
              disabled={
                mutation.isPending ||
                authLoading ||
                !accessToken ||
                ideaDescription.length < 20
              }
              size="lg"
              className="w-full bg-[#0D7377] hover:bg-[#0B6163] text-white"
            >
              {mutation.isPending ? (
                <>
                  <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                  Analyzing your idea...
                </>
              ) : (
                <>
                  <Target className="mr-2 h-4 w-4" />
                  Validate Idea
                </>
              )}
            </Button>

            {!authLoading && !accessToken && (
              <p className="text-sm text-muted-foreground text-center">
                Sign in to validate your idea.
              </p>
            )}

            {mutation.isError && (
              <div className="flex items-center gap-2 p-3 bg-destructive/10 text-destructive rounded-lg text-sm">
                <AlertTriangle className="h-4 w-4 flex-shrink-0" />
                {mutation.error.message}
              </div>
            )}
          </CardContent>
        </Card>

        {/* Results */}
        {result && (
          <div className="space-y-6 animate-in fade-in slide-in-from-bottom-4 duration-500">
            {/* Overall Score + Save Button */}
            <Card>
              <CardContent className="pt-6">
                <div className="flex flex-col sm:flex-row items-center justify-between gap-4">
                  <div>
                    <p className="text-sm text-muted-foreground">Overall Viability Score</p>
                    <div className="flex items-center gap-3 mt-1">
                      <span className="text-4xl font-bold font-data">
                        {(result.relevance_score * 100).toFixed(0)}%
                      </span>
                      <Badge className={rating!.color}>{rating!.label}</Badge>
                    </div>
                  </div>
                  <div className="flex items-center gap-6">
                    <div className="flex gap-6 text-center">
                      <div>
                        <p className="text-2xl font-bold font-data">{result.revenue_potential || 'N/A'}</p>
                        <p className="text-xs text-muted-foreground">Revenue Potential</p>
                      </div>
                      <div>
                        <p className="text-2xl font-bold font-data">{result.competition_overlap}</p>
                        <p className="text-xs text-muted-foreground">Competing Ideas</p>
                      </div>
                    </div>
                    {result.insight_id && (
                      <Button
                        variant={saved ? 'secondary' : 'outline'}
                        size="sm"
                        onClick={handleSave}
                        disabled={saving || saved}
                      >
                        {saved ? (
                          <><CheckCircle className="mr-1.5 h-4 w-4" /> Saved</>
                        ) : saving ? (
                          <><Loader2 className="mr-1.5 h-4 w-4 animate-spin" /> Saving...</>
                        ) : (
                          <><Bookmark className="mr-1.5 h-4 w-4" /> Save to Workspace</>
                        )}
                      </Button>
                    )}
                  </div>
                </div>
              </CardContent>
            </Card>

            {/* Radar Chart */}
            <ScoreRadar
              scores={{
                opportunity: result.opportunity_score ?? undefined,
                problem: result.problem_score ?? undefined,
                feasibility: result.feasibility_score ?? undefined,
                why_now: result.why_now_score ?? undefined,
                go_to_market: result.go_to_market_score ?? undefined,
                founder_fit: result.founder_fit_score ?? undefined,
                execution_difficulty: result.execution_difficulty ?? undefined,
                revenue_potential: result.revenue_potential ?? undefined,
              }}
            />

            {/* Analysis Cards */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {result.problem_statement && (
                <Card>
                  <CardHeader className="pb-2">
                    <CardTitle className="text-base flex items-center gap-2">
                      <AlertTriangle className="h-4 w-4 text-yellow-500" />
                      Problem Statement
                    </CardTitle>
                  </CardHeader>
                  <CardContent>
                    <p className="text-sm text-muted-foreground">{result.problem_statement}</p>
                  </CardContent>
                </Card>
              )}
              {result.proposed_solution && (
                <Card>
                  <CardHeader className="pb-2">
                    <CardTitle className="text-base flex items-center gap-2">
                      <Lightbulb className="h-4 w-4 text-blue-500" />
                      Proposed Solution
                    </CardTitle>
                  </CardHeader>
                  <CardContent>
                    <p className="text-sm font-medium">{result.proposed_solution}</p>
                    {result.value_ladder && result.value_ladder.length > 0 && (
                      <div className="mt-3 space-y-2">
                        <p className="text-xs font-medium text-muted-foreground uppercase tracking-wide">Pricing Tiers</p>
                        {result.value_ladder.map((tier, i) => (
                          <div key={i} className="flex items-baseline gap-2 text-sm">
                            <span className="font-semibold text-primary shrink-0">{tier.price}</span>
                            <span className="text-muted-foreground">
                              {tier.tier_name} — {tier.description}
                            </span>
                          </div>
                        ))}
                      </div>
                    )}
                  </CardContent>
                </Card>
              )}
              {result.market_size_estimate && (
                <Card>
                  <CardHeader className="pb-2">
                    <CardTitle className="text-base flex items-center gap-2">
                      <DollarSign className="h-4 w-4 text-green-500" />
                      Market Size
                    </CardTitle>
                  </CardHeader>
                  <CardContent>
                    {result.market_sizing ? (
                      <div className="space-y-2">
                        <div className="flex justify-between text-sm">
                          <span className="text-muted-foreground">TAM</span>
                          <span className="font-medium">{result.market_sizing.tam}</span>
                        </div>
                        <div className="flex justify-between text-sm">
                          <span className="text-muted-foreground">SAM</span>
                          <span className="font-medium">{result.market_sizing.sam}</span>
                        </div>
                        <div className="flex justify-between text-sm">
                          <span className="text-muted-foreground">SOM</span>
                          <span className="font-medium">{result.market_sizing.som}</span>
                        </div>
                        <div className="flex justify-between text-sm">
                          <span className="text-muted-foreground">Growth</span>
                          <span className="font-medium">{result.market_sizing.growth_rate}</span>
                        </div>
                      </div>
                    ) : (
                      <p className="text-sm text-muted-foreground">{result.market_size_estimate}</p>
                    )}
                  </CardContent>
                </Card>
              )}
              {result.why_now_analysis && (
                <Card>
                  <CardHeader className="pb-2">
                    <CardTitle className="text-base flex items-center gap-2">
                      <TrendingUp className="h-4 w-4 text-purple-500" />
                      Why Now
                    </CardTitle>
                  </CardHeader>
                  <CardContent>
                    <p className="text-sm text-muted-foreground">{result.why_now_analysis}</p>
                  </CardContent>
                </Card>
              )}
            </div>

            {result.market_gap_analysis && (
              <Card>
                <CardHeader className="pb-2">
                  <CardTitle className="text-base">Market Gap Analysis</CardTitle>
                </CardHeader>
                <CardContent>
                  <p className="text-sm text-muted-foreground">{result.market_gap_analysis}</p>
                </CardContent>
              </Card>
            )}

            {/* Similar Ideas */}
            {result.similar_ideas.length > 0 && (
              <Card>
                <CardHeader>
                  <CardTitle className="flex items-center gap-2">
                    <Users className="h-5 w-5" />
                    Similar Ideas in Our Database ({result.similar_ideas.length})
                  </CardTitle>
                  <CardDescription>
                    Existing ideas that overlap with your concept
                  </CardDescription>
                </CardHeader>
                <CardContent>
                  <div className="space-y-3">
                    {result.similar_ideas.map((idea) => (
                      <div
                        key={idea.id}
                        className="flex items-start justify-between p-3 rounded-lg border bg-muted/30 hover:bg-muted/50 transition-colors"
                      >
                        <div className="flex-1 mr-4">
                          <p className="font-medium text-sm">
                            {idea.title || idea.proposed_solution.slice(0, 80)}
                          </p>
                          <p className="text-xs text-muted-foreground mt-1 line-clamp-2">
                            {idea.proposed_solution}
                          </p>
                          <div className="flex gap-2 mt-2">
                            {idea.opportunity_score && (
                              <Badge variant="outline" className="text-xs">
                                Opportunity: {idea.opportunity_score}/10
                              </Badge>
                            )}
                            {idea.market_size_estimate && (
                              <Badge variant="outline" className="text-xs">
                                {idea.market_size_estimate}
                              </Badge>
                            )}
                          </div>
                        </div>
                        <div className="text-right shrink-0">
                          <p className="text-lg font-bold font-data">
                            {(idea.relevance_score * 100).toFixed(0)}%
                          </p>
                          <p className="text-xs text-muted-foreground">match</p>
                        </div>
                      </div>
                    ))}
                  </div>
                </CardContent>
              </Card>
            )}

            {/* CTA for Deep Research */}
            <Card className="border-[#0D7377]/20 bg-[#0D7377]/5">
              <CardContent className="pt-6">
                <div className="flex flex-col sm:flex-row items-center justify-between gap-4">
                  <div>
                    <h3 className="font-semibold text-lg">Want a 40-step deep research report?</h3>
                    <p className="text-sm text-muted-foreground mt-1">
                      Our AI Research Agent performs comprehensive market analysis, competitive intelligence,
                      and feasibility assessment. Available for Starter and Pro plans.
                    </p>
                  </div>
                  <Button
                    variant="default"
                    className="shrink-0 bg-[#0D7377] hover:bg-[#0B6163]"
                    onClick={handleDeepResearch}
                  >
                    Get Deep Research
                    <ArrowRight className="ml-2 h-4 w-4" />
                  </Button>
                </div>
              </CardContent>
            </Card>
          </div>
        )}
      </div>
    </div>
  );
}
