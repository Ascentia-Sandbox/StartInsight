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
} as const
