'use client';

import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { getSupabaseClient } from '@/lib/supabase/client';

/**
 * Shared admin auth hook — replaces duplicated auth patterns across 16+ admin pages.
 *
 * Returns { accessToken, isLoading } and redirects to login if not authenticated.
 */
export function useAdminAuth(redirectPath?: string) {
  const router = useRouter();
  const [accessToken, setAccessToken] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    const checkAuth = async () => {
      try {
        const supabase = getSupabaseClient();
        const { data: { session } } = await supabase.auth.getSession();
        if (!session) {
          const redirect = redirectPath || window.location.pathname;
          router.push(`/auth/login?redirectTo=${redirect}`);
          return;
        }
        setAccessToken(session.access_token);
      } catch (error) {
        console.error('Admin auth check failed:', error);
      } finally {
        setIsLoading(false);
      }
    };
    checkAuth();
  }, [router, redirectPath]);

  return { accessToken, isLoading };
}
