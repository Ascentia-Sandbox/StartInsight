'use client';

import { useSearchParams } from 'next/navigation';
import { useEffect, useState, Suspense } from 'react';
import Link from 'next/link';
import { Button } from '@/components/ui/button';
import { Skeleton } from '@/components/ui/skeleton';
import { InsightComparison } from '@/components/insight-comparison';
import { config } from '@/lib/env';
import type { Insight } from '@/lib/types';
import { GitCompareArrows } from 'lucide-react';

function CompareContent() {
  const searchParams = useSearchParams();
  const [insights, setInsights] = useState<Insight[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const idsParam = searchParams.get('ids') ?? '';
  const ids = idsParam ? idsParam.split(',').filter(Boolean).slice(0, 3) : [];

  useEffect(() => {
    if (ids.length === 0) return;

    const fetchInsights = async () => {
      setLoading(true);
      setError(null);
      try {
        const results = await Promise.all(
          ids.map((id) =>
            fetch(`${config.apiUrl}/api/insights/${id}`).then((r) => {
              if (!r.ok) throw new Error(`Insight ${id} not found`);
              return r.json() as Promise<Insight>;
            })
          )
        );
        setInsights(results);
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Failed to load insights');
      } finally {
        setLoading(false);
      }
    };

    void fetchInsights();
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [idsParam]);

  if (ids.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center py-24 text-center px-4">
        <GitCompareArrows className="h-16 w-16 text-muted-foreground mb-6" />
        <h2 className="text-2xl font-bold mb-2">No Insights Selected</h2>
        <p className="text-muted-foreground max-w-md mb-6">
          Select two or three insights from the insights library to compare them side by side.
        </p>
        <Button asChild>
          <Link href="/insights">Browse Insights</Link>
        </Button>
      </div>
    );
  }

  if (loading) {
    return (
      <div className="max-w-5xl mx-auto px-4 py-12 space-y-4">
        <Skeleton className="h-10 w-64" />
        <Skeleton className="h-80 w-full" />
      </div>
    );
  }

  if (error) {
    return (
      <div className="flex flex-col items-center justify-center py-24 text-center px-4">
        <p className="text-destructive mb-4">{error}</p>
        <Button asChild variant="outline">
          <Link href="/insights">Back to Insights</Link>
        </Button>
      </div>
    );
  }

  if (insights.length < 2) {
    return (
      <div className="flex flex-col items-center justify-center py-24 text-center px-4">
        <GitCompareArrows className="h-16 w-16 text-muted-foreground mb-6" />
        <h2 className="text-2xl font-bold mb-2">Need at Least 2 Insights</h2>
        <p className="text-muted-foreground max-w-md mb-6">
          Pass at least two insight IDs via <code className="bg-muted px-1 rounded">?ids=id1,id2</code> to compare them.
        </p>
        <Button asChild>
          <Link href="/insights">Browse Insights</Link>
        </Button>
      </div>
    );
  }

  return (
    <div className="max-w-5xl mx-auto px-4 py-12">
      <div className="mb-8">
        <h1 className="text-3xl font-bold mb-2">Insight Comparison</h1>
        <p className="text-muted-foreground">
          Comparing {insights.length} startup ideas side by side.
        </p>
      </div>
      <InsightComparison insights={insights} />
      <div className="mt-8 text-center">
        <Button asChild variant="outline">
          <Link href="/insights">Back to Insights</Link>
        </Button>
      </div>
    </div>
  );
}

export default function ComparePage() {
  return (
    <Suspense
      fallback={
        <div className="max-w-5xl mx-auto px-4 py-12 space-y-4">
          <Skeleton className="h-10 w-64" />
          <Skeleton className="h-80 w-full" />
        </div>
      }
    >
      <CompareContent />
    </Suspense>
  );
}
