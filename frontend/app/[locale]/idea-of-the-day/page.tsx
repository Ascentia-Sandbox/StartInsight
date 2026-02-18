'use client';

import { useQuery } from '@tanstack/react-query';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader } from '@/components/ui/card';
import { Skeleton } from '@/components/ui/skeleton';
import Link from 'next/link';
import { Star, TrendingUp, Target, Wrench, Calendar, Sparkles, ArrowRight, Clock } from 'lucide-react';

// Helper to truncate title to a max length
function truncateTitle(title: string, maxLength: number = 100): string {
  if (!title) return '';
  if (title.length <= maxLength) return title;
  return title.substring(0, maxLength).trim() + '...';
}
import { formatDistanceToNow } from 'date-fns';
import { config } from '@/lib/env';

async function fetchIdeaOfTheDay() {
  const res = await fetch(`${config.apiUrl}/api/insights/idea-of-the-day`);
  if (!res.ok) throw new Error('Failed to fetch idea of the day');
  return res.json();
}

async function fetchPreviousIdeas() {
  const res = await fetch(`${config.apiUrl}/api/insights/featured-picks?limit=5`);
  if (!res.ok) throw new Error('Failed to fetch previous ideas');
  return res.json();
}

export default function IdeaOfTheDayPage() {
  const { data: idea, isLoading, error } = useQuery({
    queryKey: ['idea-of-the-day'],
    queryFn: fetchIdeaOfTheDay,
  });

  const { data: previousIdeas } = useQuery({
    queryKey: ['previous-ideas'],
    queryFn: fetchPreviousIdeas,
  });

  if (isLoading) {
    return (
      <div className="container mx-auto px-4 py-12">
        <Skeleton className="h-96 w-full" />
      </div>
    );
  }

  if (error || !idea) {
    return (
      <div className="min-h-screen bg-gradient-to-b from-amber-50 to-white dark:from-amber-950/20 dark:to-background">
        <div className="container mx-auto px-4 py-12">
          <div className="flex flex-col items-center justify-center py-16 text-center">
            <Sparkles className="h-12 w-12 text-muted-foreground mb-4" />
            <h3 className="text-lg font-semibold mb-2">Today&apos;s idea is being curated</h3>
            <p className="text-muted-foreground max-w-md mb-6">
              Every day, our AI selects the most promising startup idea. Check back after 8:00 AM UTC.
            </p>
            <Button asChild variant="outline">
              <Link href="/insights">Browse All Insights</Link>
            </Button>
          </div>
        </div>
      </div>
    );
  }

  const founderFit = idea.founder_fit_score || idea.enhanced_scores?.find((s: any) => s.dimension.includes('Founder'))?.value;
  const feasibility = idea.feasibility_score || idea.enhanced_scores?.find((s: any) => s.dimension.includes('Feasibility'))?.value;
  const opportunity = idea.opportunity_score || idea.enhanced_scores?.find((s: any) => s.dimension.includes('Opportunity'))?.value;

  return (
    <div className="min-h-screen bg-gradient-to-b from-amber-50 to-white dark:from-amber-950/20 dark:to-background">
      {/* Hero Section */}
      <section className="container mx-auto px-4 py-12">
        <div className="text-center mb-8">
          <Badge className="mb-4 bg-gradient-to-r from-amber-500 to-orange-500 text-white border-0 px-4 py-2 text-sm">
            <Sparkles className="h-4 w-4 mr-2" />
            Idea of the Day
          </Badge>
          <h1 className="text-4xl md:text-5xl font-bold mb-4">
            Today&apos;s Top Startup Opportunity
          </h1>
          <p className="text-muted-foreground text-lg max-w-2xl mx-auto">
            Hand-picked by our AI from thousands of market signals. Updated daily at midnight UTC.
          </p>
          <div className="flex items-center justify-center gap-2 mt-4 text-sm text-muted-foreground">
            <Calendar className="h-4 w-4" />
            <span>{new Date().toLocaleDateString('en-US', { weekday: 'long', year: 'numeric', month: 'long', day: 'numeric' })}</span>
          </div>
        </div>

        {/* Main Idea Card */}
        <Card className="max-w-4xl mx-auto shadow-2xl border-2 border-amber-200 dark:border-amber-800 overflow-hidden">
          <div className="bg-gradient-to-r from-amber-500 to-orange-500 p-4 text-white">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <Star className="h-6 w-6 fill-white" />
                <span className="font-bold text-lg">Today&apos;s Pick</span>
              </div>
              <Badge className="bg-white/20 text-white border-white/30 text-lg px-3 py-1">
                {founderFit}/10 Founder Fit
              </Badge>
            </div>
          </div>

          <CardHeader className="pb-4">
            <div className="flex items-start justify-between gap-4">
              <h2 className="text-2xl md:text-3xl font-bold leading-tight" title={idea.proposed_solution}>
                {idea.proposed_solution}
              </h2>
              <Badge className="bg-emerald-100 text-emerald-800 dark:bg-emerald-900 dark:text-emerald-300 text-lg px-3 py-1 shrink-0">
                {idea.market_size_estimate}
              </Badge>
            </div>
          </CardHeader>

          <CardContent className="space-y-6">
            {/* Problem Statement */}
            <div className="bg-muted/50 rounded-lg p-4">
              <h3 className="font-semibold mb-2 flex items-center gap-2">
                <TrendingUp className="h-5 w-5 text-primary" />
                Problem
              </h3>
              <p className="text-muted-foreground">{idea.problem_statement.split('.').slice(0, 2).join('.')}.</p>
            </div>

            {/* Score Cards */}
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
              <div className="text-center p-4 bg-violet-50 dark:bg-violet-950/30 rounded-lg">
                <Target className="h-6 w-6 mx-auto mb-2 text-violet-600" />
                <div className="text-2xl font-bold text-violet-600">{founderFit}/10</div>
                <div className="text-xs text-muted-foreground">Founder Fit</div>
              </div>
              <div className="text-center p-4 bg-emerald-50 dark:bg-emerald-950/30 rounded-lg">
                <Wrench className="h-6 w-6 mx-auto mb-2 text-emerald-600" />
                <div className="text-2xl font-bold text-emerald-600">{feasibility}/10</div>
                <div className="text-xs text-muted-foreground">Feasibility</div>
              </div>
              <div className="text-center p-4 bg-amber-50 dark:bg-amber-950/30 rounded-lg">
                <TrendingUp className="h-6 w-6 mx-auto mb-2 text-amber-600" />
                <div className="text-2xl font-bold text-amber-600">{opportunity}/10</div>
                <div className="text-xs text-muted-foreground">Opportunity</div>
              </div>
              <div className="text-center p-4 bg-blue-50 dark:bg-blue-950/30 rounded-lg">
                <Star className="h-6 w-6 mx-auto mb-2 text-blue-600" />
                <div className="text-2xl font-bold text-blue-600">{(idea.relevance_score * 10).toFixed(1)}/10</div>
                <div className="text-xs text-muted-foreground">Relevance</div>
              </div>
            </div>

            {/* CTA */}
            <div className="flex flex-col sm:flex-row gap-4 pt-4">
              <Button asChild size="lg" className="flex-1 bg-gradient-to-r from-amber-500 to-orange-500 hover:from-amber-600 hover:to-orange-600">
                <Link href={`/insights/${idea.slug || idea.id}`}>
                  View Full Analysis
                  <ArrowRight className="ml-2 h-5 w-5" />
                </Link>
              </Button>
              <Button asChild variant="outline" size="lg" className="flex-1">
                <Link href="/insights">
                  Browse All Ideas
                </Link>
              </Button>
            </div>
          </CardContent>
        </Card>
      </section>

      {/* Previous Featured Ideas */}
      {previousIdeas && previousIdeas.length > 0 && (
        <section className="container mx-auto px-4 py-12">
          <h2 className="text-2xl font-bold mb-6 flex items-center gap-2">
            <Clock className="h-6 w-6" />
            Recent Featured Ideas
          </h2>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {previousIdeas.slice(0, 6).map((item: any) => (
              <Card key={item.id} className="hover:shadow-lg transition-shadow">
                <CardHeader className="pb-2">
                  <div className="flex items-start justify-between gap-2">
                    <h3 className="font-semibold line-clamp-2" title={item.proposed_solution}>{truncateTitle(item.proposed_solution, 80)}</h3>
                    <Badge variant="outline">{item.market_size_estimate}</Badge>
                  </div>
                </CardHeader>
                <CardContent>
                  <p className="text-sm text-muted-foreground line-clamp-2 mb-4">{item.problem_statement.split('.')[0]}.</p>
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-2">
                      <Badge variant="outline" className="bg-violet-50 text-violet-700 border-violet-200">
                        <Target className="h-3 w-3 mr-1" />
                        {item.founder_fit_score || '?'}/10
                      </Badge>
                    </div>
                    <Button asChild size="sm" variant="ghost">
                      <Link href={`/insights/${item.slug || item.id}`}>View →</Link>
                    </Button>
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>
        </section>
      )}
    </div>
  );
}
