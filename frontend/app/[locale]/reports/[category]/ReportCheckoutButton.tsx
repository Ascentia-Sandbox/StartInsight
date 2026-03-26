'use client';

import { useState, useEffect } from 'react';
import { Loader2 } from 'lucide-react';
import { Button } from '@/components/ui/button';

interface ReportCheckoutButtonProps {
  category: string;
  apiUrl: string;
}

/**
 * Handles the Stripe Checkout redirect for one-time report purchases.
 * Reads utm_source from sessionStorage (stored on page load) and passes
 * it to the backend create-checkout endpoint as metadata.
 */
export function ReportCheckoutButton({ category, apiUrl }: ReportCheckoutButtonProps) {
  const [loading, setLoading] = useState(false);
  const [sessionSource, setSessionSource] = useState('direct');

  useEffect(() => {
    const stored = sessionStorage.getItem('report_source');
    if (stored) {
      setSessionSource(stored);
    }
  }, []);

  const handleCheckout = async () => {
    setLoading(true);
    try {
      const url = new URL(`${apiUrl}/api/reports/create-checkout`);
      url.searchParams.set('category', category);
      url.searchParams.set('source', sessionSource);

      const res = await fetch(url.toString());

      if (!res.ok) {
        const data = await res.json().catch(() => ({}));
        throw new Error(data.detail ?? 'Failed to create checkout session');
      }

      const data = await res.json();
      if (data.checkout_url) {
        window.location.href = data.checkout_url;
      } else {
        throw new Error('No checkout URL returned');
      }
    } catch (err) {
      console.error('Checkout error:', err);
      // Re-enable button so user can retry
      setLoading(false);
    }
  };

  return (
    <button
      onClick={handleCheckout}
      disabled={loading}
      aria-label="Unlock full report for RM49"
      className="
        inline-flex items-center justify-center gap-2
        w-full rounded-xl px-6 py-3.5
        bg-white text-[#0D7377] font-semibold text-base
        hover:-translate-y-0.5 transition-transform duration-150
        focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2
        disabled:opacity-60 disabled:pointer-events-none
        min-h-[44px]
      "
    >
      {loading ? (
        <>
          <Loader2 className="h-4 w-4 animate-spin" />
          Redirecting to checkout…
        </>
      ) : (
        'Unlock Full Report →'
      )}
    </button>
  );
}
