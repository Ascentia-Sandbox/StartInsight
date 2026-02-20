// Single source of truth for plan features
// Used by both /pricing and /billing pages

export const PLAN_FEATURES = {
  free: [
    '5 idea generations/month',
    'Basic 4-dimension scoring',
    'Community trends access',
    'Save up to 10 insights',
    'Email support',
  ],
  starter: [
    '50 idea generations/month',
    '8-dimension AI scoring',
    'Full trends database',
    'AI research agent (10/month)',
    'Export to PDF/CSV',
    'Priority support',
  ],
  pro: [
    'Unlimited idea generations',
    '8-dimension scoring + predictions',
    'Full trends + 7-day forecast',
    'AI research agent (50/month)',
    'Builder integrations (5 platforms)',
    'Team collaboration (5 seats)',
    'API access (10K calls/month)',
    '24/7 priority support',
  ],
  enterprise: [
    'Everything in Pro',
    'Unlimited team members',
    'Unlimited API access',
    'Custom AI model fine-tuning',
    'Dedicated account manager',
    'SLA guarantee (99.9% uptime)',
    'White-label options',
    'SSO & SAML support',
  ],
} as const;

export type PlanTier = keyof typeof PLAN_FEATURES;

export const PLAN_PRICES = {
  free: { price: '$0', period: 'forever' },
  starter: { price: '$19', period: '/month' },
  pro: { price: '$49', period: '/month' },
  enterprise: { price: '$299', period: '/month' },
} as const;
