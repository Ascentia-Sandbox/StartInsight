'use client';

import { Suspense, useState, useCallback } from 'react';
import { useQuery } from '@tanstack/react-query';
import { useSearchParams } from 'next/navigation';
import { fetchInsights } from '@/lib/api';
import { InsightCard } from '@/components/InsightCard';
import { InsightFilters } from '@/components/InsightFilters';
import { Skeleton } from '@/components/ui/skeleton';
import { Button } from '@/components/ui/button';
import { AlertTriangle, Lightbulb, Loader2, RefreshCw, Search } from 'lucide-react';
import { Card, CardContent } from '@/components/ui/card';
import Link from 'next/link';
import type { Insight } from '@/lib/types';

// Valid sort options type
type SortOption = 'relevance' | 'founder_fit' | 'opportunity' | 'feasibility' | 'newest';
const validSortOptions: SortOption[] = ['relevance', 'founder_fit', 'opportunity', 'feasibility', 'newest'];
const PAGE_SIZE = 20;

function AllInsightsContent() {
  const searchParams = useSearchParams();
  const [allInsights, setAllInsights] = useState<Insight[]>([]);
  const [, setOffset] = useState(0);
  const [isLoadingMore, setIsLoadingMore] = useState(false);

  // Validate sort parameter — default to newest (latest insights = highest value)
  const sortParam = searchParams.get('sort');
  const validSort = sortParam && validSortOptions.includes(sortParam as SortOption)
    ? (sortParam as SortOption)
    : 'newest';

  const params = {
    min_score: searchParams.get('min_score') ? parseFloat(searchParams.get('min_score')!) : undefined,
    source: searchParams.get('source') || undefined,
    sort: validSort,
    search: searchParams.get('search') || undefined,
    featured: searchParams.get('featured') === 'true' ? true : undefined,
    limit: PAGE_SIZE,
    offset: 0,
  };

  const { data, isLoading, error, refetch } = useQuery({
    queryKey: ['insights', searchParams.toString()],
    queryFn: () => fetchInsights(params),
  });

  // Reset accumulated insights when filters change
  const filterKey = searchParams.toString();
  const [lastFilterKey, setLastFilterKey] = useState(filterKey);
  if (filterKey !== lastFilterKey) {
    setLastFilterKey(filterKey);
    setAllInsights([]);
    setOffset(0);
  }

  // Combine initial data with loaded-more data
  const displayInsights = allInsights.length > 0 ? allInsights : (data?.insights ?? []);
  const total = data?.total ?? 0;
  const hasMore = displayInsights.length < total;

  const handleLoadMore = useCallback(async () => {
    if (isLoadingMore || !hasMore) return;
    setIsLoadingMore(true);
    try {
      const nextOffset = displayInsights.length;
      const moreData = await fetchInsights({ ...params, offset: nextOffset });
      setAllInsights(prev => {
        const existing = prev.length > 0 ? prev : (data?.insights ?? []);
        return [...existing, ...moreData.insights];
      });
      setOffset(nextOffset);
    } finally {
      setIsLoadingMore(false);
    }
  }, [isLoadingMore, hasMore, displayInsights.length, params, data?.insights]);

  return (
    <div className="container mx-auto px-4 py-8">
      <header className="mb-8 flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold">All Insights</h1>
          <p className="text-muted-foreground">
            {total ? `${total} insights found` : 'Browse all insights'}
          </p>
        </div>
        <Button asChild variant="outline">
          <Link href="/">← Back to Home</Link>
        </Button>
      </header>

      <div className="grid grid-cols-1 lg:grid-cols-4 gap-6">
        {/* Filters Sidebar */}
        <div className="lg:col-span-1">
          <InsightFilters />
        </div>

        {/* Insights Grid */}
        <div className="lg:col-span-3">
          {isLoading ? (
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              {[...Array(6)].map((_, i) => (
                <Skeleton key={i} className="h-64" />
              ))}
            </div>
          ) : error ? (
            <Card className="border-destructive/50">
              <CardContent className="flex flex-col items-center py-12 text-center">
                <AlertTriangle className="h-10 w-10 text-destructive mb-4" />
                <h3 className="text-lg font-semibold mb-1">Unable to load insights</h3>
                <p className="text-sm text-muted-foreground mb-4 max-w-md">
                  {error instanceof Error && error.message.includes('fetch')
                    ? 'The server appears to be offline. Please try again in a moment.'
                    : error instanceof Error ? error.message : 'An unexpected error occurred.'}
                </p>
                <Button onClick={() => refetch()} variant="outline">
                  <RefreshCw className="h-4 w-4 mr-2" />
                  Try Again
                </Button>
              </CardContent>
            </Card>
          ) : displayInsights.length > 0 ? (
            <>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                {displayInsights.map((insight) => (
                  <InsightCard key={insight.id} insight={insight} />
                ))}
              </div>

              {hasMore ? (
                <div className="mt-8 flex justify-center">
                  <Button
                    variant="outline"
                    onClick={handleLoadMore}
                    disabled={isLoadingMore}
                  >
                    {isLoadingMore ? (
                      <>
                        <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                        Loading...
                      </>
                    ) : (
                      `Load More (${displayInsights.length} of ${total})`
                    )}
                  </Button>
                </div>
              ) : (
                <div className="mt-8 text-center">
                  <p className="text-sm text-muted-foreground">All insights loaded</p>
                </div>
              )}
            </>
          ) : searchParams.toString() ? (
            <div className="flex flex-col items-center justify-center py-16 text-center">
              <Search className="h-12 w-12 text-muted-foreground mb-4" />
              <h3 className="text-lg font-semibold mb-2">No insights found</h3>
              <p className="text-muted-foreground max-w-md mb-6">
                No insights match your current filters. Try adjusting your criteria or browse all insights.
              </p>
              <Button asChild variant="outline">
                <Link href="/insights">Clear Filters</Link>
              </Button>
            </div>
          ) : (
            <div className="flex flex-col items-center justify-center py-16 text-center">
              <Lightbulb className="h-12 w-12 text-muted-foreground mb-4" />
              <h3 className="text-lg font-semibold mb-2">No startup insights yet</h3>
              <p className="text-muted-foreground max-w-md mb-6">
                Our AI agents analyze signals from Reddit, Product Hunt, Hacker News, and more.
                New insights are generated daily.
              </p>
              <Button asChild variant="outline">
                <Link href="/features">Explore Features</Link>
              </Button>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

export default function AllInsightsPage() {
  return (
    <Suspense fallback={<div className="container mx-auto px-4 py-8"><Skeleton className="h-96" /></div>}>
      <AllInsightsContent />
    </Suspense>
  );
}
