'use client';

import { useEffect } from 'react';
import { useSearchParams } from 'next/navigation';

/**
 * Captures the `?ref=` query parameter on landing and persists it to
 * localStorage for up to 30 days so the backend can credit the referrer
 * when the visitor signs up.
 *
 * Storage keys:
 *   si_referral_code  – 8-char uppercase referral code
 *   si_referral_ts    – Unix timestamp (ms) of when the code was stored
 */
export function useReferral(): void {
  const searchParams = useSearchParams();

  useEffect(() => {
    const ref = searchParams.get('ref');
    if (ref && ref.length === 8) {
      const thirtyDaysMs = 30 * 24 * 60 * 60 * 1000;
      const storedTs = localStorage.getItem('si_referral_ts');
      const storedCode = localStorage.getItem('si_referral_code');

      // Only overwrite if there is no stored code, or the stored one is older than 30 days
      if (!storedCode || !storedTs || Date.now() - Number(storedTs) > thirtyDaysMs) {
        localStorage.setItem('si_referral_code', ref);
        localStorage.setItem('si_referral_ts', Date.now().toString());
      }
    }
  }, [searchParams]);
}
