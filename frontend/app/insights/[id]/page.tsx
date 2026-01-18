'use client';

import { useQuery } from '@tanstack/react-query';
import { useParams } from 'next/navigation';
import { fetchInsightById } from '@/lib/api';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Separator } from '@/components/ui/separator';
import { Skeleton } from '@/components/ui/skeleton';
import { Button } from '@/components/ui/button';
import { formatDistanceToNow } from 'date-fns';
import Link from 'next/link';

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
      <div className="container mx-auto px-4 py-8 max-w-4xl">
        <Skeleton className="h-96" />
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
            <Link href="/insights">← Back to All Insights</Link>
          </Button>
        </div>
      </div>
    );
  }

  const marketSizeColor = {
    Small: 'bg-yellow-100 text-yellow-800',
    Medium: 'bg-blue-100 text-blue-800',
    Large: 'bg-green-100 text-green-800',
  };

  return (
    <div className="container mx-auto px-4 py-8 max-w-4xl">
      <div className="mb-4">
        <Button asChild variant="outline" size="sm">
          <Link href="/insights">← Back to All Insights</Link>
        </Button>
      </div>

      <Card>
        <CardHeader>
          <div className="flex items-start justify-between gap-4">
            <div className="flex-1">
              <CardTitle className="text-2xl mb-2">
                {insight.problem_statement}
              </CardTitle>
              <p className="text-sm text-muted-foreground">
                {formatDistanceToNow(new Date(insight.created_at), { addSuffix: true })}
              </p>
            </div>
            <Badge className={marketSizeColor[insight.market_size_estimate]}>
              {insight.market_size_estimate} Market
            </Badge>
          </div>
        </CardHeader>

        <CardContent className="space-y-6">
          {/* Proposed Solution */}
          <div>
            <h3 className="font-semibold mb-2">Proposed Solution</h3>
            <p className="text-muted-foreground">{insight.proposed_solution}</p>
          </div>

          <Separator />

          {/* Relevance Score */}
          <div>
            <h3 className="font-semibold mb-2">Relevance Score</h3>
            <div className="flex items-center gap-2">
              <div className="text-2xl">
                {'⭐'.repeat(Math.round(insight.relevance_score * 5))}
              </div>
              <span className="text-muted-foreground">
                {insight.relevance_score.toFixed(2)} / 1.00
              </span>
            </div>
          </div>

          {/* Competitors */}
          {insight.competitor_analysis && insight.competitor_analysis.length > 0 && (
            <>
              <Separator />
              <div>
                <h3 className="font-semibold mb-3">Competitor Analysis</h3>
                <div className="space-y-3">
                  {insight.competitor_analysis.map((competitor, idx) => (
                    <div key={idx} className="border rounded-lg p-4">
                      <div className="flex items-start justify-between">
                        <div className="flex-1">
                          <h4 className="font-medium">{competitor.name}</h4>
                          <p className="text-sm text-muted-foreground mt-1">
                            {competitor.description}
                          </p>
                          <a
                            href={competitor.url}
                            target="_blank"
                            rel="noopener noreferrer"
                            className="text-sm text-blue-600 hover:underline mt-2 inline-block"
                          >
                            Visit website →
                          </a>
                        </div>
                        {competitor.market_position && (
                          <Badge variant="outline">
                            {competitor.market_position}
                          </Badge>
                        )}
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            </>
          )}

          {/* Source Information */}
          {insight.raw_signal && (
            <>
              <Separator />
              <div>
                <h3 className="font-semibold mb-2">Source</h3>
                <div className="flex items-center gap-2">
                  <Badge variant="outline">{insight.raw_signal.source}</Badge>
                  <a
                    href={insight.raw_signal.url}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="text-sm text-blue-600 hover:underline"
                  >
                    View original signal →
                  </a>
                </div>
              </div>
            </>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
