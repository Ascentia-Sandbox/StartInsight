'use client'
import { useEffect } from 'react'

export function PostHogProvider({ children }: { children: React.ReactNode }) {
  useEffect(() => {
    const key = process.env.NEXT_PUBLIC_POSTHOG_KEY
    const host = process.env.NEXT_PUBLIC_POSTHOG_HOST || 'https://app.posthog.com'
    if (!key) return

    // Defer posthog-js import until after hydration to keep it out of main bundle
    import('posthog-js').then(({ default: posthog }) => {
      posthog.init(key, {
        api_host: host,
        capture_pageview: true,
        capture_pageleave: true,
        persistence: 'localStorage',
        autocapture: false, // manual event tracking only
      })
      // Expose for feature flag checks via isFeatureFlagEnabled()
      ;(window as unknown as Record<string, unknown>).__ph = posthog
    })
  }, [])

  return <>{children}</>
}
