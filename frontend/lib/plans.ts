// Single source of truth for plan features
// Used by both /pricing and /billing pages

export const PLAN_FEATURES = {
  free: [
    'Browse global startup ideas',
    'Basic 4-dimension scoring',
    '3 free premium reports',
    'Community trends access',
    'Save up to 10 insights',
  ],
  pro: [
    'Unlimited premium reports',
    '8-dimension AI scoring',
    'Full trends + 7-day forecast',
    'AI research agent (10/month)',
    'Asia-specific intelligence',
    'Accelerator matching',
    'Export to PDF/CSV',
    'Priority support',
  ],
  api: [
    'Everything in Pro',
    '1,000 API calls per month',
    'Programmatic access to idea data',
    'Webhook integrations',
    'Team collaboration (10 seats)',
    'Dedicated support',
  ],
} as const;

export type PlanTier = keyof typeof PLAN_FEATURES;

export const PLAN_PRICES = {
  free: { price: '$0', period: 'forever' },
  pro: { price: '$19', period: '/month' },
  api: { price: '$49', period: '/month' },
} as const;
