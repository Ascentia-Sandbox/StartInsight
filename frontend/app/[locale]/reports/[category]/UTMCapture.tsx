'use client';

import { useEffect } from 'react';

interface UTMCaptureProps {
  /** utm_source value extracted from the URL on the server side. */
  utmSource: string | undefined;
}

/**
 * Invisible client component that stores utm_source in sessionStorage on mount.
 * The value is later read by ReportCheckoutButton to pass as metadata to the
 * Stripe Checkout session.
 */
export function UTMCapture({ utmSource }: UTMCaptureProps) {
  useEffect(() => {
    if (utmSource) {
      sessionStorage.setItem('report_source', utmSource);
    }
  }, [utmSource]);

  return null;
}
