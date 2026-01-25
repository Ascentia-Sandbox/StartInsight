/**
 * Authentication redirect hook - Code simplification Phase 3.
 *
 * Centralizes auth redirect logic currently duplicated in 12+ components.
 * Replaces inline useEffect + useRouter patterns with reusable hook.
 */

'use client';

import { useEffect } from 'react';
import { useRouter } from 'next/navigation';

export function useAuthRedirect(isAuthenticated: boolean, redirectTo: string = '/login') {
  const router = useRouter();

  useEffect(() => {
    if (!isAuthenticated) {
      router.push(redirectTo);
    }
  }, [isAuthenticated, redirectTo, router]);
}
