import { Skeleton } from '@/components/ui/skeleton';

export default function IdeaOfTheDayLoading() {
  return (
    <div className="min-h-screen bg-gradient-to-b from-amber-50 to-white dark:from-amber-950/20 dark:to-background">
      <div className="container mx-auto px-4 py-12">
        {/* Header skeleton */}
        <div className="text-center mb-8">
          <Skeleton className="h-8 w-40 mx-auto mb-4 rounded-full" />
          <Skeleton className="h-12 w-3/4 mx-auto mb-4" />
          <Skeleton className="h-6 w-1/2 mx-auto" />
        </div>
        {/* Main card skeleton */}
        <div className="max-w-4xl mx-auto">
          <Skeleton className="h-[500px] w-full rounded-xl" />
        </div>
      </div>
    </div>
  );
}
