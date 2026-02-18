// Build-time validation of required environment variables
// NOTE: Next.js only inlines NEXT_PUBLIC_* vars when accessed as literal
// strings (e.g. process.env.NEXT_PUBLIC_API_URL). Dynamic access like
// process.env[name] does NOT work on the client side.

export const config = {
  apiUrl: process.env.NEXT_PUBLIC_API_URL!,
  supabaseUrl: process.env.NEXT_PUBLIC_SUPABASE_URL!,
  supabaseAnonKey: process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY!,
  supportEmail: process.env.NEXT_PUBLIC_SUPPORT_EMAIL || 'support@startinsight.ai',
  contactEmail: process.env.NEXT_PUBLIC_CONTACT_EMAIL || 'hello@startinsight.ai',
  enterpriseEmail: process.env.NEXT_PUBLIC_ENTERPRISE_EMAIL || 'enterprise@startinsight.ai',
  privacyEmail: process.env.NEXT_PUBLIC_PRIVACY_EMAIL || 'privacy@startinsight.ai',
} as const;

// Runtime validation (throws on server startup or first client load if missing)
if (!config.apiUrl) throw new Error('NEXT_PUBLIC_API_URL environment variable is required');
if (!config.supabaseUrl) throw new Error('NEXT_PUBLIC_SUPABASE_URL environment variable is required');
if (!config.supabaseAnonKey) throw new Error('NEXT_PUBLIC_SUPABASE_ANON_KEY environment variable is required');
