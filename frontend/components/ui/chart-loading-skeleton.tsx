'use client';

import { Card, CardContent, CardHeader } from '@/components/ui/card';
import { Skeleton } from '@/components/ui/skeleton';

export function ChartLoadingSkeleton() {
  return (
    <Card>
      <CardHeader>
        <Skeleton className="h-6 w-48" />
        <Skeleton className="h-4 w-64 mt-2" />
      </CardHeader>
      <CardContent>
        <div className="space-y-4">
          {/* Controls skeleton */}
          <div className="flex items-center justify-between">
            <Skeleton className="h-8 w-32" />
            <div className="flex gap-2">
              <Skeleton className="h-8 w-24" />
              <Skeleton className="h-8 w-24" />
              <Skeleton className="h-8 w-24" />
            </div>
          </div>

          {/* Chart skeleton */}
          <div className="h-[300px] flex items-end gap-2 px-4">
            {[60, 80, 55, 90, 70, 85, 65, 75, 95, 50, 70, 80].map((h, i) => (
              <Skeleton
                key={i}
                className="flex-1"
                style={{ height: `${h}%` }}
              />
            ))}
          </div>

          {/* Stats skeleton */}
          <div className="grid grid-cols-3 gap-4 pt-4 border-t">
            {Array.from({ length: 3 }).map((_, i) => (
              <div key={i} className="text-center space-y-2">
                <Skeleton className="h-8 w-16 mx-auto" />
                <Skeleton className="h-3 w-24 mx-auto" />
              </div>
            ))}
          </div>
        </div>
      </CardContent>
    </Card>
  );
}
