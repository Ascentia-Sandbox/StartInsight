import { Card, CardContent, CardFooter, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import Link from 'next/link';
import { formatDistanceToNow } from 'date-fns';
import type { Insight } from '@/lib/types';

interface InsightCardProps {
  insight: Insight;
}

export function InsightCard({ insight }: InsightCardProps) {
  const marketSizeColor = {
    Small: 'bg-yellow-100 text-yellow-800 dark:bg-yellow-900 dark:text-yellow-300',
    Medium: 'bg-blue-100 text-blue-800 dark:bg-blue-900 dark:text-blue-300',
    Large: 'bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-300',
  };

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
        <span className="text-xs text-muted-foreground">
          {formatDistanceToNow(new Date(insight.created_at), { addSuffix: true })}
        </span>
        <Button asChild size="sm">
          <Link href={`/insights/${insight.id}`}>
            View Details
          </Link>
        </Button>
      </CardFooter>
    </Card>
  );
}
