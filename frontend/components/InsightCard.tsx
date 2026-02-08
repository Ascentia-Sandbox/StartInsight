import { Card, CardContent, CardFooter, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import Link from 'next/link';
import { formatDistanceToNow, format } from 'date-fns';
import { Target, Wrench, TrendingUp } from 'lucide-react';
import type { Insight } from '@/lib/types';

interface InsightCardProps {
  insight: Insight;
}

// Source display configuration with colors matching platform branding
const sourceConfig: Record<string, { label: string; className: string }> = {
  reddit: { label: 'Reddit', className: 'bg-orange-100 text-orange-800 dark:bg-orange-900 dark:text-orange-300' },
  product_hunt: { label: 'Product Hunt', className: 'bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-300' },
  google_trends: { label: 'Google Trends', className: 'bg-blue-100 text-blue-800 dark:bg-blue-900 dark:text-blue-300' },
  twitter: { label: 'Twitter/X', className: 'bg-sky-100 text-sky-800 dark:bg-sky-900 dark:text-sky-300' },
  hacker_news: { label: 'Hacker News', className: 'bg-amber-100 text-amber-800 dark:bg-amber-900 dark:text-amber-300' },
  seed_data: { label: 'Curated', className: 'bg-purple-100 text-purple-800 dark:bg-purple-900 dark:text-purple-300' },
};

// Helper to get score from enhanced_scores array
function getEnhancedScore(insight: Insight, dimension: string): number | null {
  if (!insight.enhanced_scores) return null;
  const score = insight.enhanced_scores.find(
    (s) => s.dimension.toLowerCase().includes(dimension.toLowerCase())
  );
  return score?.value ?? null;
}

// Helper to truncate title to a max length
function truncateTitle(title: string, maxLength: number = 80): string {
  if (title.length <= maxLength) return title;
  return title.substring(0, maxLength).trim() + '...';
}

export function InsightCard({ insight }: InsightCardProps) {
  const marketSizeColor: Record<string, string> = {
    Small: 'bg-yellow-100 text-yellow-800 dark:bg-yellow-900 dark:text-yellow-300',
    Medium: 'bg-blue-100 text-blue-800 dark:bg-blue-900 dark:text-blue-300',
    Large: 'bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-300',
  };

  // Get source from raw_signal if available
  const source = insight.raw_signal?.source;
  const sourceDisplay = source ? sourceConfig[source] : null;

  const relevanceStars = Math.round(insight.relevance_score * 5);

  // Get dimension scores
  const founderFit = insight.founder_fit_score ?? getEnhancedScore(insight, 'founder');
  const feasibility = insight.feasibility_score ?? getEnhancedScore(insight, 'feasibility');
  const opportunity = insight.opportunity_score ?? getEnhancedScore(insight, 'opportunity');

  return (
    <Card className="h-full flex flex-col hover:shadow-lg transition-shadow touch-manipulation">
      <CardHeader className="pb-3">
        <div className="flex items-start justify-between gap-2">
          <CardTitle className="text-lg line-clamp-2 leading-relaxed" title={insight.proposed_solution}>
            {truncateTitle(insight.proposed_solution, 80)}
          </CardTitle>
          <Badge className={marketSizeColor[insight.market_size_estimate] || 'bg-emerald-100 text-emerald-800 dark:bg-emerald-900 dark:text-emerald-300'}>
            {insight.market_size_estimate}
          </Badge>
        </div>
      </CardHeader>

      <CardContent className="flex-1 pt-0">
        <p className="text-sm text-muted-foreground line-clamp-3 mb-4">
          {insight.problem_statement.split('.')[0]}.
        </p>

        <div className="flex items-center gap-2 text-sm mb-3">
          <span className="font-medium">Relevance:</span>
          <div className="flex">
            {'⭐'.repeat(relevanceStars)}
            {'☆'.repeat(5 - relevanceStars)}
          </div>
          <span className="text-muted-foreground">
            ({insight.relevance_score.toFixed(2)})
          </span>
        </div>

        {/* Dimension Score Badges */}
        <div className="flex flex-wrap gap-2 mb-3">
          {founderFit !== null && founderFit >= 7 && (
            <Badge variant="outline" className="bg-violet-50 text-violet-700 border-violet-200 dark:bg-violet-950 dark:text-violet-300 dark:border-violet-800">
              <Target className="h-3 w-3 mr-1" />
              Founder Fit: {founderFit}/10
            </Badge>
          )}
          {feasibility !== null && feasibility >= 8 && (
            <Badge variant="outline" className="bg-emerald-50 text-emerald-700 border-emerald-200 dark:bg-emerald-950 dark:text-emerald-300 dark:border-emerald-800">
              <Wrench className="h-3 w-3 mr-1" />
              Easy Build
            </Badge>
          )}
          {opportunity !== null && opportunity >= 8 && (
            <Badge variant="outline" className="bg-amber-50 text-amber-700 border-amber-200 dark:bg-amber-950 dark:text-amber-300 dark:border-amber-800">
              <TrendingUp className="h-3 w-3 mr-1" />
              High Opportunity
            </Badge>
          )}
        </div>

        {insight.competitor_analysis && insight.competitor_analysis.length > 0 && (
          <div className="text-sm text-muted-foreground">
            {insight.competitor_analysis.length} competitor{insight.competitor_analysis.length > 1 ? 's' : ''} identified
          </div>
        )}
      </CardContent>

      <CardFooter className="flex justify-between items-center pt-3">
        <div className="flex items-center gap-2 flex-wrap">
          {sourceDisplay && (
            <Badge variant="outline" className={sourceDisplay.className}>
              {sourceDisplay.label}
            </Badge>
          )}
          <span className="text-xs text-muted-foreground" title={format(new Date(insight.created_at), 'PPP p')}>
            {format(new Date(insight.created_at), 'MMM d, yyyy')} · {formatDistanceToNow(new Date(insight.created_at), { addSuffix: true })}
          </span>
        </div>
        <Button asChild size="sm" className="min-h-[44px] min-w-[44px] active:scale-95 transition-transform">
          <Link href={`/insights/${insight.id}`}>
            View Details
          </Link>
        </Button>
      </CardFooter>
    </Card>
  );
}
