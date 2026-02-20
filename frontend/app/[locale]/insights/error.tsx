'use client';

import { useEffect } from 'react';
import * as Sentry from '@sentry/nextjs';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardFooter, CardHeader, CardTitle } from '@/components/ui/card';
import Link from 'next/link';

export default function InsightsError({
  error,
  reset,
}: {
  error: Error & { digest?: string };
  reset: () => void;
}) {
  useEffect(() => {
    Sentry.captureException(error);
    console.error('Insights page error:', error);
  }, [error]);

  return (
    <div className="container mx-auto px-4 py-8">
      <Card className="max-w-2xl mx-auto">
        <CardHeader>
          <CardTitle className="text-2xl text-red-600">Failed to load insights</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <p className="text-muted-foreground">
            We couldn&apos;t load the insights page. This might be due to:
          </p>
          <ul className="list-disc list-inside text-muted-foreground space-y-1">
            <li>Backend server not running</li>
            <li>Network connectivity issues</li>
            <li>Invalid data format</li>
          </ul>
          {error.message && (
            <div className="p-4 bg-muted rounded-lg">
              <p className="text-sm font-mono">{error.message}</p>
            </div>
          )}
          <div className="p-4 bg-blue-50 dark:bg-blue-950 rounded-lg">
            <p className="text-sm text-blue-800 dark:text-blue-200">
              <strong>Tip:</strong> Make sure the backend server is running and NEXT_PUBLIC_API_URL is configured
            </p>
          </div>
        </CardContent>
        <CardFooter className="flex gap-4">
          <Button onClick={reset}>
            Try again
          </Button>
          <Button variant="outline" asChild>
            <Link href="/">Go to Homepage</Link>
          </Button>
        </CardFooter>
      </Card>
    </div>
  );
}
