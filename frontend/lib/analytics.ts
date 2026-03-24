import posthog from 'posthog-js'

export const analytics = {
  track: (event: string, properties?: Record<string, unknown>) => {
    if (typeof window !== 'undefined') {
      posthog.capture(event, properties)
    }
  },
  identify: (userId: string, properties?: Record<string, unknown>) => {
    if (typeof window !== 'undefined') {
      posthog.identify(userId, properties)
    }
  },
  reset: () => {
    if (typeof window !== 'undefined') {
      posthog.reset()
    }
  },
}

// Typed event names to avoid typos
export const Events = {
  INSIGHT_VIEWED: 'insight_viewed',
  INSIGHT_SAVED: 'insight_saved',
  INSIGHT_COMPARED: 'comparison_started',
  VALIDATE_SUBMITTED: 'validate_submitted',
  UPGRADE_CLICKED: 'upgrade_clicked',
  SEARCH_PERFORMED: 'search_performed',
  FILTER_APPLIED: 'filter_applied',
  ONBOARDING_DISMISSED: 'onboarding_dismissed',
  // PLG freemium events
  REPORT_VIEWED: 'report_viewed',
  PAYWALL_HIT: 'paywall_hit',
  NEWSLETTER_SIGNUP: 'newsletter_signup',
  REFERRAL_SHARED: 'referral_shared',
} as const

/**
 * Check if a PostHog feature flag is enabled.
 * Returns false if PostHog is not loaded or the flag doesn't exist.
 */
export function isFeatureFlagEnabled(flag: string): boolean {
  if (typeof window === 'undefined') return false
  try {
    const posthog = (window as Record<string, unknown>).__ph as { isFeatureEnabled?: (flag: string) => boolean } | undefined
    return posthog?.isFeatureEnabled?.(flag) ?? false
  } catch {
    return false
  }
}
