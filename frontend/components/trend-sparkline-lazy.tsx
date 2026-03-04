'use client';

import dynamic from 'next/dynamic';

// Lazy-load recharts to split it into a deferred chunk,
// reducing initial bundle size and TBT on the home page.
const TrendSparklineDynamic = dynamic(
  () => import('@/components/trend-sparkline').then((m) => m.TrendSparkline),
  { ssr: false, loading: () => <span className="inline-block w-20 h-6" /> }
);

export { TrendSparklineDynamic as TrendSparkline };
