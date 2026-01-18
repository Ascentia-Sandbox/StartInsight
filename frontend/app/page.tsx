'use client';

import { useQuery } from '@tanstack/react-query';
import { fetchDailyTop } from '@/lib/api';
import { InsightCard } from '@/components/InsightCard';
import { Skeleton } from '@/components/ui/skeleton';
import Link from 'next/link';
import { Button } from '@/components/ui/button';

export default function HomePage() {
  const { data: insights, isLoading, error } = useQuery({
    queryKey: ['daily-top'],
    queryFn: () => fetchDailyTop(5),
  });

  if (error) {
    return (
      <div className="container mx-auto px-4 py-8">
        <div className="text-center">
          <h2 className="text-2xl font-bold text-red-600">Error loading insights</h2>
          <p className="text-muted-foreground mt-2">
            {error instanceof Error ? error.message : 'An error occurred'}
          </p>
          <p className="text-sm text-muted-foreground mt-4">
            Make sure the backend server is running on http://localhost:8000
          </p>
        </div>
      </div>
    );
  }

  return (
    <div className="container mx-auto px-4 py-8">
      <header className="mb-8">
        <h1 className="text-4xl font-bold mb-2">StartInsight</h1>
        <p className="text-xl text-muted-foreground">
          Top 5 Insights of the Day
        </p>
        <p className="text-sm text-muted-foreground mt-1">
          AI-powered startup market intelligence
        </p>
        <div className="mt-4">
          <Button asChild variant="outline">
            <Link href="/insights">View All Insights</Link>
          </Button>
        </div>
      </header>

      {isLoading ? (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {[...Array(5)].map((_, i) => (
            <Skeleton key={i} className="h-64" />
          ))}
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {insights?.map((insight) => (
            <InsightCard key={insight.id} insight={insight} />
          ))}
        </div>
      )}

      {!isLoading && insights && insights.length === 0 && (
        <div className="text-center py-12">
          <p className="text-muted-foreground">
            No insights available yet. Run the analysis task to generate insights.
          </p>
          <p className="text-sm text-muted-foreground mt-2">
            From the backend directory, run:
            <code className="block mt-2 p-2 bg-muted rounded">
              uv run python -c "import asyncio; from app.worker import analyze_signals_task; asyncio.run(analyze_signals_task({}))"
            </code>
          </p>
        </div>
      )}
    </div>
  );
}
