import { z } from 'zod';

// Zod schemas for runtime validation
export const CompetitorSchema = z.object({
  name: z.string(),
  url: z.string().url(),
  description: z.string(),
  market_position: z.enum(['Small', 'Medium', 'Large']).nullable().optional(),
});

export const RawSignalSummarySchema = z.object({
  id: z.string().uuid(),
  source: z.string(),
  url: z.string().url(),
  created_at: z.string().refine(
    (val) => {
      // Accept both ISO datetime with Z (2020-01-01T00:00:00Z) and without Z (2020-01-01T00:00:00)
      const isoDatetimeRegex = /^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d+)?(?:Z|[+-]\d{2}:\d{2})?$/;
      return isoDatetimeRegex.test(val);
    },
    { message: 'Invalid datetime format' }
  ),
  extra_metadata: z.record(z.string(), z.any()).nullable().optional(), // Flexible metadata (varies by source)
});

export const InsightSchema = z.object({
  id: z.string().uuid(),
  raw_signal_id: z.string().uuid(),
  problem_statement: z.string(),
  proposed_solution: z.string(),
  market_size_estimate: z.enum(['Small', 'Medium', 'Large']),
  relevance_score: z.number().min(0).max(1),
  competitor_analysis: z.array(CompetitorSchema),
  created_at: z.string().datetime(),
  raw_signal: RawSignalSummarySchema.optional(),
});

export const InsightListResponseSchema = z.object({
  insights: z.array(InsightSchema),
  total: z.number(),
  limit: z.number(),
  offset: z.number(),
});

// TypeScript types derived from Zod schemas
export type Competitor = z.infer<typeof CompetitorSchema>;
export type RawSignalSummary = z.infer<typeof RawSignalSummarySchema>;
export type Insight = z.infer<typeof InsightSchema>;
export type InsightListResponse = z.infer<typeof InsightListResponseSchema>;

// API query parameters
export interface FetchInsightsParams {
  min_score?: number;
  source?: string;
  limit?: number;
  offset?: number;
}

// ============================================
// User Workspace Types (Phase 4)
// ============================================

export const WorkspaceStatusSchema = z.object({
  saved_count: z.number(),
  interested_count: z.number(),
  building_count: z.number(),
  ratings_count: z.number(),
});

export const SavedInsightSchema = z.object({
  id: z.string().uuid(),
  user_id: z.string().uuid(),
  insight_id: z.string().uuid(),
  status: z.enum(['saved', 'interested', 'building', 'not_interested']),
  notes: z.string().nullable().optional(),
  tags: z.array(z.string()).nullable().optional(),
  shared_count: z.number().default(0),
  saved_at: z.string().datetime(),
  claimed_at: z.string().datetime().nullable().optional(),
  insight: InsightSchema.optional(),
});

export const SavedInsightListResponseSchema = z.object({
  items: z.array(SavedInsightSchema),
  total: z.number(),
  limit: z.number(),
  offset: z.number(),
});

export const UserRatingSchema = z.object({
  id: z.string().uuid(),
  user_id: z.string().uuid(),
  insight_id: z.string().uuid(),
  rating: z.number().min(1).max(5),
  feedback: z.string().nullable().optional(),
  rated_at: z.string().datetime(),
});

export const RatingListResponseSchema = z.object({
  items: z.array(UserRatingSchema),
  total: z.number(),
});

// User workspace TypeScript types
export type WorkspaceStatus = z.infer<typeof WorkspaceStatusSchema>;
export type SavedInsight = z.infer<typeof SavedInsightSchema>;
export type SavedInsightListResponse = z.infer<typeof SavedInsightListResponseSchema>;
export type UserRating = z.infer<typeof UserRatingSchema>;
export type RatingListResponse = z.infer<typeof RatingListResponseSchema>;

// ============================================
// Teams Types (Phase 6.4)
// ============================================

export const TeamSchema = z.object({
  id: z.string(),
  name: z.string(),
  slug: z.string(),
  description: z.string().nullable().optional(),
  owner_id: z.string(),
  member_count: z.number(),
  created_at: z.string(),
});

export const TeamMemberSchema = z.object({
  id: z.string(),
  user_id: z.string(),
  email: z.string(),
  display_name: z.string().nullable().optional(),
  role: z.enum(['owner', 'admin', 'member', 'viewer']),
  joined_at: z.string(),
});

export const TeamInvitationSchema = z.object({
  id: z.string(),
  email: z.string(),
  role: z.string(),
  status: z.string(),
  expires_at: z.string(),
});

export type Team = z.infer<typeof TeamSchema>;
export type TeamMember = z.infer<typeof TeamMemberSchema>;
export type TeamInvitation = z.infer<typeof TeamInvitationSchema>;

// ============================================
// API Keys Types (Phase 7.2)
// ============================================

export const APIKeySchema = z.object({
  id: z.string(),
  name: z.string(),
  key_prefix: z.string(),
  description: z.string().nullable().optional(),
  scopes: z.array(z.string()),
  rate_limit_per_hour: z.number(),
  total_requests: z.number(),
  last_used_at: z.string().nullable().optional(),
  is_active: z.boolean(),
  expires_at: z.string().nullable().optional(),
  created_at: z.string(),
});

export const APIKeyCreateResponseSchema = z.object({
  id: z.string(),
  name: z.string(),
  key: z.string(), // Full key - only shown at creation
  key_prefix: z.string(),
  scopes: z.array(z.string()),
  rate_limit_per_hour: z.number(),
  expires_at: z.string().nullable().optional(),
  created_at: z.string(),
});

export const APIKeyListResponseSchema = z.object({
  keys: z.array(APIKeySchema),
  total: z.number(),
});

export const APIKeyUsageSchema = z.object({
  key_id: z.string(),
  period_days: z.number(),
  total_requests: z.number(),
  successful_requests: z.number(),
  failed_requests: z.number(),
  avg_response_time_ms: z.number(),
  requests_by_endpoint: z.record(z.string(), z.number()),
  requests_by_day: z.array(z.object({
    date: z.string(),
    count: z.number(),
  })).optional(),
});

export type APIKey = z.infer<typeof APIKeySchema>;
export type APIKeyCreateResponse = z.infer<typeof APIKeyCreateResponseSchema>;
export type APIKeyListResponse = z.infer<typeof APIKeyListResponseSchema>;
export type APIKeyUsage = z.infer<typeof APIKeyUsageSchema>;

// ============================================
// Payments Types (Phase 6.1)
// ============================================

export const PricingTierSchema = z.object({
  name: z.string(),
  price_monthly: z.number(),
  price_yearly: z.number(),
  features: z.array(z.string()),
  limits: z.record(z.string(), z.number()),
});

export const PricingResponseSchema = z.object({
  tiers: z.record(z.string(), PricingTierSchema),
});

export const CheckoutResponseSchema = z.object({
  session_id: z.string(),
  checkout_url: z.string(),
});

export const SubscriptionStatusSchema = z.object({
  tier: z.string(),
  status: z.string(),
  current_period_end: z.string().nullable().optional(),
  cancel_at_period_end: z.boolean().optional(),
  limits: z.record(z.string(), z.number()),
});

export type PricingTier = z.infer<typeof PricingTierSchema>;
export type PricingResponse = z.infer<typeof PricingResponseSchema>;
export type CheckoutResponse = z.infer<typeof CheckoutResponseSchema>;
export type SubscriptionStatus = z.infer<typeof SubscriptionStatusSchema>;

// ============================================
// Admin Dashboard Types (Phase 4.2)
// ============================================

export const ExecutionLogSchema = z.object({
  id: z.string(),
  agent_type: z.string(),
  source: z.string().nullable().optional(),
  status: z.string(),
  started_at: z.string(),
  completed_at: z.string().nullable().optional(),
  duration_ms: z.number().nullable().optional(),
  items_processed: z.number(),
  items_failed: z.number(),
  error_message: z.string().nullable().optional(),
  metadata: z.record(z.string(), z.any()).optional(),
});

export const AgentStatusSchema = z.object({
  agent_type: z.string(),
  state: z.enum(['running', 'paused', 'triggered']),
  last_run: z.string().nullable().optional(),
  last_status: z.string().nullable().optional(),
  items_processed_today: z.number(),
  errors_today: z.number(),
});

export const DashboardMetricsSchema = z.object({
  agent_states: z.record(z.string(), z.string()),
  recent_logs: z.array(ExecutionLogSchema),
  llm_cost_today: z.number(),
  pending_insights: z.number(),
  total_insights_today: z.number(),
  errors_today: z.number(),
  timestamp: z.string(),
});

export const InsightReviewSchema = z.object({
  id: z.string(),
  problem_statement: z.string(),
  proposed_solution: z.string(),
  relevance_score: z.number(),
  admin_status: z.string(),
  admin_notes: z.string().nullable().optional(),
  source: z.string(),
  created_at: z.string(),
});

export const ReviewQueueResponseSchema = z.object({
  items: z.array(InsightReviewSchema),
  total: z.number(),
  pending_count: z.number(),
  approved_count: z.number(),
  rejected_count: z.number(),
});

export type ExecutionLog = z.infer<typeof ExecutionLogSchema>;
export type AgentStatus = z.infer<typeof AgentStatusSchema>;
export type DashboardMetrics = z.infer<typeof DashboardMetricsSchema>;
export type InsightReview = z.infer<typeof InsightReviewSchema>;
export type ReviewQueueResponse = z.infer<typeof ReviewQueueResponseSchema>;
