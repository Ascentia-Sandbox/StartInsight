'use client';

import { useState, useEffect } from 'react';
import { useQuery } from '@tanstack/react-query';
import { getSupabaseClient } from '@/lib/supabase/client';
import { fetchSubscriptionStatus } from '@/lib/api';
import type { SubscriptionStatus } from '@/lib/types';

const TIER_ORDER: Record<string, number> = {
  free: 0,
  starter: 1,
  pro: 2,
  enterprise: 3,
};

/**
 * Shared subscription hook — fetches tier, limits, and usage for the authenticated user.
 *
 * Caches the result for 5 minutes via React Query.
 * Exposes helpers: `isFeatureAllowed(requiredTier)`, `atLimit(metric)`, `usagePercent(metric)`.
 */
export function useSubscription() {
  const [accessToken, setAccessToken] = useState<string | null>(null);

  useEffect(() => {
    const getToken = async () => {
      const supabase = getSupabaseClient();
      const { data: { session } } = await supabase.auth.getSession();
      if (session?.access_token) {
        setAccessToken(session.access_token);
      }
    };
    getToken();
  }, []);

  const { data, isLoading } = useQuery<SubscriptionStatus>({
    queryKey: ['subscription', accessToken],
    queryFn: () => fetchSubscriptionStatus(accessToken!),
    enabled: !!accessToken,
    staleTime: 5 * 60 * 1000, // 5 minutes
  });

  const tier = data?.tier ?? 'free';
  const limits = data?.limits ?? {};
  const usage = data?.usage ?? { insights_today: 0, analyses_this_month: 0, team_members: 0 };

  /**
   * Returns true if the current tier meets or exceeds the required tier.
   */
  const isFeatureAllowed = (requiredTier: string): boolean => {
    const current = TIER_ORDER[tier] ?? 0;
    const required = TIER_ORDER[requiredTier] ?? 0;
    return current >= required;
  };

  /**
   * Returns true if the user has reached or exceeded the limit for the given metric.
   * Returns false for unlimited metrics (limit === -1).
   */
  const atLimit = (metric: string): boolean => {
    const limit = limits[metric];
    if (limit === undefined || limit === -1) return false;
    const current = (usage as Record<string, number>)[metric] ?? 0;
    return current >= limit;
  };

  /**
   * Returns usage as a percentage of the limit (0-100).
   * Returns 0 for unlimited metrics or when limit is not defined.
   */
  const usagePercent = (metric: string): number => {
    const limit = limits[metric];
    if (!limit || limit === -1) return 0;
    const current = (usage as Record<string, number>)[metric] ?? 0;
    return Math.min(100, Math.round((current / limit) * 100));
  };

  return { tier, limits, usage, isFeatureAllowed, atLimit, usagePercent, isLoading };
}
