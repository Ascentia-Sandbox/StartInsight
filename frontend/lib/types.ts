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
