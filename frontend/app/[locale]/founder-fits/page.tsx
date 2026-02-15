'use client';

import { useQuery } from '@tanstack/react-query';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardFooter, CardHeader, CardTitle } from '@/components/ui/card';
import { Skeleton } from '@/components/ui/skeleton';
import Link from 'next/link';
import { Target, TrendingUp, Wrench, Star, Users, Rocket, ArrowRight, CheckCircle2 } from 'lucide-react';

// Helper to truncate title to a max length
function truncateTitle(title: string, maxLength: number = 80): string {
  if (!title) return '';
  if (title.length <= maxLength) return title;
  return title.substring(0, maxLength).trim() + '...';
}
import { formatDistanceToNow } from 'date-fns';
import { config } from '@/lib/env';

async function fetchFounderFitPicks() {
  const res = await fetch(`${config.apiUrl}/api/insights/founder-fit-picks?limit=12`);
  if (!res.ok) throw new Error('Failed to fetch founder fit picks');
  return res.json();
}

function getScoreColor(score: number) {
  if (score >= 9) return 'text-emerald-600 bg-emerald-50 dark:bg-emerald-950/30';
  if (score >= 8) return 'text-blue-600 bg-blue-50 dark:bg-blue-950/30';
  if (score >= 7) return 'text-violet-600 bg-violet-50 dark:bg-violet-950/30';
  return 'text-gray-600 bg-gray-50 dark:bg-gray-950/30';
}

function getScoreLabel(score: number) {
  if (score >= 9) return 'Perfect Fit';
  if (score >= 8) return 'Great Fit';
  if (score >= 7) return 'Good Fit';
  return 'Moderate';
}

export default function FounderFitsPage() {
  const { data: ideas, isLoading, error } = useQuery({
    queryKey: ['founder-fit-picks'],
    queryFn: fetchFounderFitPicks,
  });

  if (isLoading) {
    return (
      <div className="container mx-auto px-4 py-12">
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {[...Array(6)].map((_, i) => (
            <Skeleton key={i} className="h-80" />
          ))}
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="container mx-auto px-4 py-12 text-center">
        <p className="text-red-500">Failed to load founder fit ideas</p>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-b from-violet-50 to-white dark:from-violet-950/20 dark:to-background">
      {/* Hero Section */}
      <section className="container mx-auto px-4 py-12">
        <div className="text-center mb-12">
          <Badge className="mb-4 bg-gradient-to-r from-violet-500 to-purple-500 text-white border-0 px-4 py-2 text-sm">
            <Target className="h-4 w-4 mr-2" />
            Founder Fits
          </Badge>
          <h1 className="text-4xl md:text-5xl font-bold mb-4">
            Ideas Perfect for <span className="text-violet-600">Solo Founders</span>
          </h1>
          <p className="text-muted-foreground text-lg max-w-2xl mx-auto mb-8">
            Curated startup ideas scored for accessibility, low initial investment, and solo-founder viability.
            Build your next venture without a huge team or massive funding.
          </p>

          {/* Stats */}
          <div className="flex flex-wrap justify-center gap-8 mb-8">
            <div className="text-center">
              <div className="text-3xl font-bold text-violet-600">{ideas?.length || 0}</div>
              <div className="text-sm text-muted-foreground">High-Fit Ideas</div>
            </div>
            <div className="text-center">
              <div className="text-3xl font-bold text-emerald-600">8+</div>
              <div className="text-sm text-muted-foreground">Avg. Founder Fit</div>
            </div>
            <div className="text-center">
              <div className="text-3xl font-bold text-amber-600">$1B+</div>
              <div className="text-sm text-muted-foreground">Avg. Market Size</div>
            </div>
          </div>
        </div>

        {/* Why Founder Fit Matters */}
        <div className="max-w-4xl mx-auto mb-12 p-6 bg-white dark:bg-card rounded-xl shadow-lg border">
          <h2 className="text-xl font-bold mb-4 flex items-center gap-2">
            <Users className="h-5 w-5 text-violet-600" />
            Why Founder Fit Matters
          </h2>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div className="flex items-start gap-3">
              <CheckCircle2 className="h-5 w-5 text-emerald-500 mt-0.5 shrink-0" />
              <div>
                <div className="font-medium">Low Barrier to Entry</div>
                <div className="text-sm text-muted-foreground">Start with minimal capital and resources</div>
              </div>
            </div>
            <div className="flex items-start gap-3">
              <CheckCircle2 className="h-5 w-5 text-emerald-500 mt-0.5 shrink-0" />
              <div>
                <div className="font-medium">Solo-Friendly</div>
                <div className="text-sm text-muted-foreground">Build MVP without a large team</div>
              </div>
            </div>
            <div className="flex items-start gap-3">
              <CheckCircle2 className="h-5 w-5 text-emerald-500 mt-0.5 shrink-0" />
              <div>
                <div className="font-medium">Validated Demand</div>
                <div className="text-sm text-muted-foreground">Real pain points from market research</div>
              </div>
            </div>
          </div>
        </div>

        {/* Ideas Grid */}
        {(!ideas || ideas.length === 0) ? (
          <div className="flex flex-col items-center justify-center py-16 text-center">
            <Users className="h-12 w-12 text-muted-foreground mb-4" />
            <h3 className="text-lg font-semibold mb-2">Founder matches coming soon</h3>
            <p className="text-muted-foreground max-w-md mb-6">
              We&apos;re analyzing startup ideas to find the best matches for your skills and interests.
            </p>
            <Button asChild variant="outline">
              <Link href="/insights">Browse All Insights</Link>
            </Button>
          </div>
        ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {ideas?.map((idea: any, index: number) => {
            const founderFit = idea.founder_fit_score || idea.enhanced_scores?.find((s: any) => s.dimension.includes('Founder'))?.value || 7;
            const feasibility = idea.feasibility_score || idea.enhanced_scores?.find((s: any) => s.dimension.includes('Feasibility'))?.value;
            const opportunity = idea.opportunity_score || idea.enhanced_scores?.find((s: any) => s.dimension.includes('Opportunity'))?.value;

            return (
              <Card key={idea.id} className={`relative overflow-hidden hover:shadow-xl transition-all ${index === 0 ? 'md:col-span-2 lg:col-span-1' : ''}`}>
                {/* Top Badge */}
                {index === 0 && (
                  <div className="absolute top-0 right-0 bg-gradient-to-l from-violet-500 to-purple-500 text-white px-3 py-1 text-xs font-bold rounded-bl-lg">
                    #1 FOUNDER FIT
                  </div>
                )}

                <CardHeader className="pb-2">
                  <div className="flex items-start justify-between gap-2 mb-2">
                    <Badge className={`${getScoreColor(founderFit)} border-0`}>
                      <Target className="h-3 w-3 mr-1" />
                      {founderFit}/10 - {getScoreLabel(founderFit)}
                    </Badge>
                    <Badge variant="outline" className="bg-emerald-50 text-emerald-700 border-emerald-200 dark:bg-emerald-950 dark:text-emerald-300">
                      {idea.market_size_estimate}
                    </Badge>
                  </div>
                  <CardTitle className="text-lg line-clamp-2" title={idea.proposed_solution}>
                    {truncateTitle(idea.proposed_solution, 80)}
                  </CardTitle>
                </CardHeader>

                <CardContent className="pb-2">
                  <p className="text-sm text-muted-foreground line-clamp-3 mb-4">
                    {idea.problem_statement.split('.')[0]}.
                  </p>

                  {/* Mini Score Grid */}
                  <div className="grid grid-cols-3 gap-2 text-center">
                    <div className="p-2 bg-muted/50 rounded">
                      <div className="text-sm font-bold">{feasibility || '?'}</div>
                      <div className="text-xs text-muted-foreground">Build</div>
                    </div>
                    <div className="p-2 bg-muted/50 rounded">
                      <div className="text-sm font-bold">{opportunity || '?'}</div>
                      <div className="text-xs text-muted-foreground">Opp.</div>
                    </div>
                    <div className="p-2 bg-muted/50 rounded">
                      <div className="text-sm font-bold">{(idea.relevance_score * 10).toFixed(0)}</div>
                      <div className="text-xs text-muted-foreground">Score</div>
                    </div>
                  </div>
                </CardContent>

                <CardFooter className="pt-2">
                  <div className="w-full flex items-center justify-between">
                    <span className="text-xs text-muted-foreground">
                      {formatDistanceToNow(new Date(idea.created_at), { addSuffix: true })}
                    </span>
                    <Button asChild size="sm" className="bg-violet-600 hover:bg-violet-700">
                      <Link href={`/insights/${idea.id}`}>
                        Explore Idea
                        <ArrowRight className="ml-1 h-4 w-4" />
                      </Link>
                    </Button>
                  </div>
                </CardFooter>
              </Card>
            );
          })}
        </div>
        )}

        {/* CTA Section */}
        <div className="text-center mt-12">
          <p className="text-muted-foreground mb-4">Want to see all startup ideas?</p>
          <Button asChild size="lg" variant="outline">
            <Link href="/insights">
              <Rocket className="mr-2 h-5 w-5" />
              Browse All {ideas?.length || 15}+ Ideas
            </Link>
          </Button>
        </div>
      </section>
    </div>
  );
}
