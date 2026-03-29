import { z } from 'zod';

// Helper: flexible datetime validator (accepts ISO with or without timezone)
const datetimeValidator = z.string().refine(
  (val) => {
    const isoDatetimeRegex = /^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d+)?(?:Z|[+-]\d{2}:\d{2})?$/;
    return isoDatetimeRegex.test(val);
  },
  { message: 'Invalid datetime format' }
);

// Zod schemas for runtime validation
export const CompetitorSchema = z.object({
  name: z.string(),
  url: z.string(),
  description: z.string(),
  market_position: z.string().nullable().optional(),
});

export const RawSignalSummarySchema = z.object({
  id: z.string().uuid(),
  source: z.string(),
  url: z.string().url(),
  created_at: datetimeValidator,
  extra_metadata: z.record(z.string(), z.any()).nullable().optional(), // Flexible metadata (varies by source)
});

// Community Signal Schema (Phase 5.2: Visualization)
// Flexible: AI agents may produce varying field formats
export const CommunitySignalSchema = z.object({
  platform: z.string().nullable().optional(),
  community: z.string().nullable().optional(),
  score: z.number().min(0).max(10),
  members: z.union([z.string(), z.number()]),
  engagement_rate: z.number().min(0).max(1).nullable().optional(),
  top_url: z.string().nullable().optional(),
});

// Enhanced Score Schema (Phase 5.2: 8-Dimension Visualization)
export const EnhancedScoreSchema = z.object({
  dimension: z.string(),
  value: z.number().min(1).max(10),
  label: z.string(),
});

// Trend keyword schema
export const TrendKeywordSchema = z.object({
  keyword: z.string(),
  volume: z.string(),
  growth: z.string(),
});

export const InsightSchema = z.object({
  id: z.string().uuid(),
  raw_signal_id: z.string().uuid(),
  slug: z.string().nullable().optional(),
  title: z.string().nullable().optional(),
  problem_statement: z.string(),
  proposed_solution: z.string(),
  market_size_estimate: z.string(), // Any string (e.g., "$5B-$20B", "Small", "Large")
  relevance_score: z.number().min(0).max(1),
  competitor_analysis: z.array(CompetitorSchema),
  created_at: datetimeValidator,
  raw_signal: RawSignalSummarySchema.optional(),
  // Phase 5.2: Enhanced visualizations
  community_signals_chart: z.array(CommunitySignalSchema).nullable().optional(),
  enhanced_scores: z.array(EnhancedScoreSchema).nullable().optional(),
  trend_keywords: z.array(TrendKeywordSchema).nullable().optional(),
  // Market sizing (TAM/SAM/SOM) - AI output varies
  market_sizing: z.record(z.string(), z.any()).nullable().optional(),
  // Advanced frameworks - AI output varies in structure
  value_ladder: z.any().nullable().optional(),
  market_gap_analysis: z.string().nullable().optional(),
  why_now_analysis: z.string().nullable().optional(),
  proof_signals: z.array(z.record(z.string(), z.any())).nullable().optional(),
  execution_plan: z.array(z.record(z.string(), z.any())).nullable().optional(),
  // Individual score fields for ScoreRadar component
  opportunity_score: z.number().min(1).max(10).nullable().optional(),
  problem_score: z.number().min(1).max(10).nullable().optional(),
  feasibility_score: z.number().min(1).max(10).nullable().optional(),
  why_now_score: z.number().min(1).max(10).nullable().optional(),
  go_to_market_score: z.number().min(1).max(10).nullable().optional(),
  founder_fit_score: z.number().min(1).max(10).nullable().optional(),
  execution_difficulty_score: z.number().min(1).max(10).nullable().optional(),
  revenue_potential_score: z.union([z.string(), z.number()]).nullable().optional(),
  // Trend data: real timeseries data from backend (dates + values)
  trend_data: z.object({
    dates: z.array(z.string()),
    values: z.array(z.number()),
  }).nullable().optional(),
});

// Lightweight schema matching backend's InsightSummary (6 fields only)
export const InsightSummarySchema = z.object({
  id: z.string().uuid(),
  problem_statement: z.string(),
  proposed_solution: z.string(),
  market_size_estimate: z.string(),
  relevance_score: z.number().min(0).max(1),
  created_at: datetimeValidator,
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
export type InsightSummary = z.infer<typeof InsightSummarySchema>;
export type CommunitySignal = z.infer<typeof CommunitySignalSchema>;
export type EnhancedScore = z.infer<typeof EnhancedScoreSchema>;
export type TrendKeyword = z.infer<typeof TrendKeywordSchema>;
export type Insight = z.infer<typeof InsightSchema>;
export type InsightListResponse = z.infer<typeof InsightListResponseSchema>;

// API query parameters
export interface FetchInsightsParams {
  min_score?: number;
  source?: string;
  sort?: 'relevance' | 'founder_fit' | 'opportunity' | 'feasibility' | 'newest';
  search?: string;
  featured?: boolean;
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
  user_id: z.string().uuid().optional(),
  insight_id: z.string().uuid(),
  status: z.enum(['saved', 'interested', 'building', 'not_interested']),
  notes: z.string().nullable().optional(),
  tags: z.array(z.string()).nullable().optional(),
  shared_count: z.number().default(0),
  saved_at: datetimeValidator,
  claimed_at: datetimeValidator.nullable().optional(),
  insight: InsightSummarySchema.optional(),
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
  rated_at: datetimeValidator,
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

export const SubscriptionUsageSchema = z.object({
  insights_today: z.number().default(0),
  analyses_this_month: z.number().default(0),
  team_members: z.number().default(0),
});

export const SubscriptionStatusSchema = z.object({
  tier: z.string(),
  status: z.string(),
  current_period_end: z.string().nullable().optional(),
  cancel_at_period_end: z.boolean().optional(),
  limits: z.record(z.string(), z.number()),
  usage: SubscriptionUsageSchema.optional(),
  free_reports_used: z.number().optional(),
  free_reports_limit: z.number().optional(),
});

export type PricingTier = z.infer<typeof PricingTierSchema>;
export type PricingResponse = z.infer<typeof PricingResponseSchema>;
export type CheckoutResponse = z.infer<typeof CheckoutResponseSchema>;
export type SubscriptionUsage = z.infer<typeof SubscriptionUsageSchema>;
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
  state: z.enum(['running', 'paused', 'triggered', 'error']),
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

// ============================================
// Phase 15.1: Full Insight Admin Types
// ============================================

export const InsightAdminSchema = z.object({
  id: z.string(),
  title: z.string().nullable().optional(),
  problem_statement: z.string(),
  proposed_solution: z.string(),
  market_size_estimate: z.string(),
  relevance_score: z.number(),
  admin_status: z.string().nullable().optional(),
  admin_notes: z.string().nullable().optional(),
  admin_override_score: z.number().nullable().optional(),
  source: z.string(),
  created_at: z.string(),
  edited_at: z.string().nullable().optional(),
  opportunity_score: z.number().nullable().optional(),
  problem_score: z.number().nullable().optional(),
  feasibility_score: z.number().nullable().optional(),
  why_now_score: z.number().nullable().optional(),
  execution_difficulty: z.number().nullable().optional(),
  go_to_market_score: z.number().nullable().optional(),
  founder_fit_score: z.number().nullable().optional(),
  revenue_potential: z.string().nullable().optional(),
  market_gap_analysis: z.string().nullable().optional(),
  why_now_analysis: z.string().nullable().optional(),
  value_ladder: z.any().nullable().optional(),
  proof_signals: z.any().nullable().optional(),
  execution_plan: z.any().nullable().optional(),
  competitor_analysis: z.any().nullable().optional(),
});

export const InsightAdminListSchema = z.object({
  items: z.array(InsightAdminSchema),
  total: z.number(),
  pending_count: z.number(),
  approved_count: z.number(),
  rejected_count: z.number(),
});

export type InsightAdmin = z.infer<typeof InsightAdminSchema>;
export type InsightAdminList = z.infer<typeof InsightAdminListSchema>;

// ============================================
// Research Request Types (Phase 5.2: Admin Queue)
// ============================================

export const ResearchRequestSchema = z.object({
  id: z.string().uuid(),
  user_id: z.string().uuid(),
  admin_id: z.string().uuid().nullable().optional(),
  status: z.enum(['pending', 'approved', 'rejected', 'completed']),
  idea_description: z.string(),
  target_market: z.string().nullable().optional(),
  budget_range: z.string().nullable().optional(),
  admin_notes: z.string().nullable().optional(),
  analysis_id: z.string().uuid().nullable().optional(),
  created_at: datetimeValidator,
  reviewed_at: datetimeValidator.nullable().optional(),
  completed_at: datetimeValidator.nullable().optional(),
  user_email: z.string().email().nullable().optional(),
});

export const ResearchRequestSummarySchema = z.object({
  id: z.string().uuid(),
  user_id: z.string().uuid(),
  user_email: z.string().email().nullable().optional(),
  status: z.enum(['pending', 'approved', 'rejected', 'completed']),
  idea_description: z.string(),
  target_market: z.string().nullable().optional(),
  created_at: datetimeValidator,
  reviewed_at: datetimeValidator.nullable().optional(),
});

export const ResearchRequestListResponseSchema = z.object({
  items: z.array(ResearchRequestSummarySchema),
  total: z.number(),
});

export const ResearchRequestActionSchema = z.object({
  action: z.enum(['approve', 'reject']),
  notes: z.string().max(1000).nullable().optional(),
});

export type ResearchRequest = z.infer<typeof ResearchRequestSchema>;
export type ResearchRequestSummary = z.infer<typeof ResearchRequestSummarySchema>;
export type ResearchRequestListResponse = z.infer<typeof ResearchRequestListResponseSchema>;
export type ResearchRequestAction = z.infer<typeof ResearchRequestActionSchema>;

// ============================================
// Research Analysis Types (custom analysis results)
// ============================================

const MarketAnalysisSchema = z.object({
  tam: z.string(),
  sam: z.string(),
  som: z.string(),
  growth_rate: z.number(),
  market_maturity: z.enum(['nascent', 'growing', 'mature', 'declining']),
  key_trends: z.array(z.string()),
});

const CompetitorProfileSchema = z.object({
  name: z.string(),
  url: z.string(),
  funding: z.string(),
  unique_value_prop: z.string(),
  weakness: z.string(),
  market_share_estimate: z.number(),
  threat_level: z.enum(['low', 'medium', 'high']),
});

const ValueEquationSchema = z.object({
  dream_outcome_score: z.number(),
  perceived_likelihood_score: z.number(),
  time_delay_score: z.number(),
  effort_sacrifice_score: z.number(),
  value_score: z.number(),
  analysis: z.string(),
});

const MarketMatrixSchema = z.object({
  demand_score: z.number(),
  difficulty_score: z.number(),
  quadrant: z.enum(['star', 'cash_cow', 'question_mark', 'dog']),
  positioning_strategy: z.string(),
});

const ACPFrameworkSchema = z.object({
  awareness_score: z.number(),
  consideration_score: z.number(),
  purchase_score: z.number(),
  funnel_bottleneck: z.string(),
  recommended_channels: z.array(z.string()),
});

const ValidationSignalSchema = z.object({
  source: z.string(),
  signal_type: z.string(),
  description: z.string(),
  url: z.string().nullable().optional(),
  sentiment: z.enum(['positive', 'neutral', 'negative']),
  strength: z.enum(['weak', 'moderate', 'strong']),
});

const ExecutionPhaseSchema = z.object({
  phase_number: z.number(),
  name: z.string(),
  duration: z.string(),
  milestones: z.array(z.string()),
  budget_estimate: z.string(),
  key_risks: z.array(z.string()),
});

const RiskAssessmentSchema = z.object({
  technical_risk: z.number(),
  market_risk: z.number(),
  team_risk: z.number(),
  financial_risk: z.number(),
  overall_risk: z.number(),
  mitigation_strategies: z.array(z.string()),
});

export const ResearchAnalysisDetailSchema = z.object({
  id: z.string().uuid(),
  user_id: z.string().uuid(),
  status: z.enum(['pending', 'processing', 'completed', 'failed']),
  progress_percent: z.number(),
  current_step: z.string().nullable().optional(),
  idea_description: z.string(),
  target_market: z.string(),
  budget_range: z.string(),
  market_analysis: MarketAnalysisSchema.nullable().optional(),
  competitor_landscape: z.array(CompetitorProfileSchema).default([]),
  value_equation: ValueEquationSchema.nullable().optional(),
  market_matrix: MarketMatrixSchema.nullable().optional(),
  acp_framework: ACPFrameworkSchema.nullable().optional(),
  validation_signals: z.array(ValidationSignalSchema).default([]),
  execution_roadmap: z.array(ExecutionPhaseSchema).default([]),
  risk_assessment: RiskAssessmentSchema.nullable().optional(),
  opportunity_score: z.number().nullable().optional(),
  market_fit_score: z.number().nullable().optional(),
  execution_readiness: z.number().nullable().optional(),
  tokens_used: z.number().default(0),
  analysis_cost_usd: z.number().default(0),
  error_message: z.string().nullable().optional(),
  created_at: datetimeValidator,
  started_at: datetimeValidator.nullable().optional(),
  completed_at: datetimeValidator.nullable().optional(),
});

export type ResearchAnalysisDetail = z.infer<typeof ResearchAnalysisDetailSchema>;
export type MarketAnalysis = z.infer<typeof MarketAnalysisSchema>;
export type CompetitorProfile = z.infer<typeof CompetitorProfileSchema>;
export type ExecutionPhase = z.infer<typeof ExecutionPhaseSchema>;
export type RiskAssessment = z.infer<typeof RiskAssessmentSchema>;

export const ResearchAnalysisSummarySchema = z.object({
  id: z.string().uuid(),
  status: z.enum(['pending', 'processing', 'completed', 'failed']),
  progress_percent: z.number(),
  idea_description: z.string(),
  target_market: z.string(),
  opportunity_score: z.number().nullable().optional(),
  created_at: datetimeValidator,
  completed_at: datetimeValidator.nullable().optional(),
});

export const ResearchAnalysisListResponseSchema = z.object({
  items: z.array(ResearchAnalysisSummarySchema),
  total: z.number(),
});

export type ResearchAnalysisSummary = z.infer<typeof ResearchAnalysisSummarySchema>;
export type ResearchAnalysisListResponse = z.infer<typeof ResearchAnalysisListResponseSchema>;

// ============================================
// User Profile Types (Phase 4.1)
// ============================================

export const UserProfileSchema = z.object({
  id: z.string(),
  email: z.string().email(),
  display_name: z.string().nullable().optional(),
  avatar_url: z.string().nullable().optional(),
  subscription_tier: z.string(),
  preferences: z.record(z.string(), z.any()),
  created_at: z.string(),
});

export const UserUpdateSchema = z.object({
  display_name: z.string().optional(),
  avatar_url: z.string().optional(),
  preferences: z.record(z.string(), z.any()).optional(),
});

export type UserProfile = z.infer<typeof UserProfileSchema>;
export type UserUpdate = z.infer<typeof UserUpdateSchema>;

// ============================================
// Tenant Types (Phase 7.3)
// ============================================

export const TenantSchema = z.object({
  id: z.string(),
  name: z.string(),
  slug: z.string(),
  subdomain: z.string().nullable().optional(),
  custom_domain: z.string().nullable().optional(),
  custom_domain_verified: z.boolean(),
  app_name: z.string().nullable().optional(),
  logo_url: z.string().nullable().optional(),
  primary_color: z.string().nullable().optional(),
  status: z.string(),
  created_at: z.string(),
});

export const TenantBrandingSchema = z.object({
  logo_url: z.string().nullable().optional(),
  favicon_url: z.string().nullable().optional(),
  primary_color: z.string().nullable().optional(),
  secondary_color: z.string().nullable().optional(),
  accent_color: z.string().nullable().optional(),
  app_name: z.string().nullable().optional(),
  tagline: z.string().nullable().optional(),
  css_variables: z.string(),
});

export const DomainConfigSchema = z.object({
  custom_domain: z.string(),
  verified: z.boolean(),
  dns_instructions: z.record(z.string(), z.any()),
});

export type Tenant = z.infer<typeof TenantSchema>;
export type TenantBranding = z.infer<typeof TenantBrandingSchema>;
export type DomainConfig = z.infer<typeof DomainConfigSchema>;
