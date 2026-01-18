'use client';

import { Suspense } from 'react';
import { useQuery } from '@tanstack/react-query';
import { useSearchParams } from 'next/navigation';
import { fetchInsights } from '@/lib/api';
import { InsightCard } from '@/components/InsightCard';
import { InsightFilters } from '@/components/InsightFilters';
import { Skeleton } from '@/components/ui/skeleton';
import { Button } from '@/components/ui/button';
import Link from 'next/link';

function AllInsightsContent() {
  const searchParams = useSearchParams();

  const params = {
    min_score: searchParams.get('min_score') ? parseFloat(searchParams.get('min_score')!) : undefined,
    source: searchParams.get('source') || undefined,
    limit: 20,
    offset: 0,
  };

  const { data, isLoading, error } = useQuery({
    queryKey: ['insights', searchParams.toString()],
    queryFn: () => fetchInsights(params),
  });

  return (
    <div className="container mx-auto px-4 py-8">
      <header className="mb-8 flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold">All Insights</h1>
          <p className="text-muted-foreground">
            {data?.total ? `${data.total} insights found` : 'Browse all insights'}
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
            <div className="text-center py-12">
              <p className="text-red-600">Error loading insights</p>
              <p className="text-sm text-muted-foreground mt-2">
                {error instanceof Error ? error.message : 'An error occurred'}
              </p>
            </div>
          ) : data && data.insights.length > 0 ? (
            <>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                {data.insights.map((insight) => (
                  <InsightCard key={insight.id} insight={insight} />
                ))}
              </div>

              {/* Pagination (future enhancement) */}
              {data.total > data.limit && (
                <div className="mt-8 flex justify-center">
                  <Button variant="outline">Load More</Button>
                </div>
              )}
            </>
          ) : (
            <div className="text-center py-12">
              <p className="text-muted-foreground">
                No insights match your filters. Try adjusting your criteria.
              </p>
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
