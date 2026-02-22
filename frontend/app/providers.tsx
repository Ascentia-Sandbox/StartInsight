'use client';

import { Suspense } from 'react';
import { QueryClientProvider } from '@tanstack/react-query';
import { ReactQueryDevtools } from '@tanstack/react-query-devtools';
import { queryClient } from '@/lib/query-client';
import { useReferral } from '@/hooks/useReferral';

/**
 * Mounts the referral tracking hook.
 * Must be wrapped in <Suspense> because useSearchParams() requires it
 * inside the App Router.
 */
function ReferralTracker(): null {
  useReferral();
  return null;
}

export function Providers({ children }: { children: React.ReactNode }) {
  return (
    <QueryClientProvider client={queryClient}>
      <Suspense fallback={null}>
        <ReferralTracker />
      </Suspense>
      {children}
      <ReactQueryDevtools initialIsOpen={false} />
    </QueryClientProvider>
  );
}
