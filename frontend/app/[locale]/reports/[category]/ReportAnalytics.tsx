'use client';

import { useEffect } from 'react';
import { analytics, Events } from '@/lib/analytics';

interface ReportAnalyticsProps {
  category: string;
}

export function ReportAnalytics({ category }: ReportAnalyticsProps) {
  useEffect(() => {
    analytics.track(Events.REPORT_CATEGORY_VIEWED, { category });
  }, [category]);

  return null;
}
