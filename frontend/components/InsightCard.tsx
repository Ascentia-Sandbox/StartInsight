import { Card, CardContent, CardFooter, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import Link from 'next/link';
import { formatDistanceToNow } from 'date-fns';
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
};

export function InsightCard({ insight }: InsightCardProps) {
  const marketSizeColor = {
    Small: 'bg-yellow-100 text-yellow-800 dark:bg-yellow-900 dark:text-yellow-300',
    Medium: 'bg-blue-100 text-blue-800 dark:bg-blue-900 dark:text-blue-300',
    Large: 'bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-300',
  };

  // Get source from raw_signal if available
  const source = insight.raw_signal?.source;
  const sourceDisplay = source ? sourceConfig[source] : null;

  const relevanceStars = Math.round(insight.relevance_score * 5);

  return (
    <Card className="h-full flex flex-col hover:shadow-lg transition-shadow">
      <CardHeader>
        <div className="flex items-start justify-between gap-2">
          <CardTitle className="text-lg line-clamp-2">
            {insight.problem_statement}
          </CardTitle>
          <Badge className={marketSizeColor[insight.market_size_estimate]}>
            {insight.market_size_estimate}
          </Badge>
        </div>
      </CardHeader>

      <CardContent className="flex-1">
        <p className="text-sm text-muted-foreground line-clamp-3 mb-4">
          {insight.proposed_solution}
        </p>

        <div className="flex items-center gap-2 text-sm">
          <span className="font-medium">Relevance:</span>
          <div className="flex">
            {'⭐'.repeat(relevanceStars)}
            {'☆'.repeat(5 - relevanceStars)}
          </div>
          <span className="text-muted-foreground">
            ({insight.relevance_score.toFixed(2)})
          </span>
        </div>

        {insight.competitor_analysis && insight.competitor_analysis.length > 0 && (
          <div className="mt-3 text-sm text-muted-foreground">
            {insight.competitor_analysis.length} competitor{insight.competitor_analysis.length > 1 ? 's' : ''} identified
          </div>
        )}
      </CardContent>

      <CardFooter className="flex justify-between items-center">
        <div className="flex items-center gap-2">
          {sourceDisplay && (
            <Badge variant="outline" className={sourceDisplay.className}>
              {sourceDisplay.label}
            </Badge>
          )}
          <span className="text-xs text-muted-foreground">
            {formatDistanceToNow(new Date(insight.created_at), { addSuffix: true })}
          </span>
        </div>
        <Button asChild size="sm">
          <Link href={`/insights/${insight.id}`}>
            View Details
          </Link>
        </Button>
      </CardFooter>
    </Card>
  );
}
