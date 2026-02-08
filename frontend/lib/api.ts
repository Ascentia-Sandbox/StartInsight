import axios from 'axios';
import { z } from 'zod';
import {
  InsightSchema,
  InsightListResponseSchema,
  WorkspaceStatusSchema,
  SavedInsightSchema,
  SavedInsightListResponseSchema,
  RatingListResponseSchema,
  UserRatingSchema,
  TeamSchema,
  TeamMemberSchema,
  TeamInvitationSchema,
  APIKeySchema,
  APIKeyCreateResponseSchema,
  APIKeyListResponseSchema,
  APIKeyUsageSchema,
  PricingResponseSchema,
  CheckoutResponseSchema,
  SubscriptionStatusSchema,
  DashboardMetricsSchema,
  AgentStatusSchema,
  ReviewQueueResponseSchema,
  InsightReviewSchema,
  UserProfileSchema,
  TenantSchema,
  TenantBrandingSchema,
  DomainConfigSchema,
  ResearchRequestSchema,
  ResearchRequestSummarySchema,
  ResearchRequestListResponseSchema,
  ResearchRequestActionSchema,
  type Insight,
  type InsightListResponse,
  type FetchInsightsParams,
  type WorkspaceStatus,
  type SavedInsight,
  type SavedInsightListResponse,
  type UserRating,
  type RatingListResponse,
  type Team,
  type TeamMember,
  type TeamInvitation,
  type APIKey,
  type APIKeyCreateResponse,
  type APIKeyListResponse,
  type APIKeyUsage,
  type PricingResponse,
  type CheckoutResponse,
  type SubscriptionStatus,
  type DashboardMetrics,
  type AgentStatus,
  type ReviewQueueResponse,
  type InsightReview,
  type ResearchRequest,
  type ResearchRequestSummary,
  type ResearchRequestListResponse,
  type ResearchRequestAction,
  type UserProfile,
  type UserUpdate,
  type Tenant,
  type TenantBranding,
  type DomainConfig,
} from './types';

import { config } from './env';

const API_BASE_URL = config.apiUrl;

const apiClient = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
  timeout: 10000,
});

/**
 * Fetch paginated list of insights with optional filters
 */
export async function fetchInsights(
  params: FetchInsightsParams = {}
): Promise<InsightListResponse> {
  const { data } = await apiClient.get('/api/insights', { params });
  return InsightListResponseSchema.parse(data);
}

/**
 * Fetch single insight by ID
 */
export async function fetchInsightById(id: string): Promise<Insight> {
  const { data } = await apiClient.get(`/api/insights/${id}`);
  return InsightSchema.parse(data);
}

/**
 * Fetch daily top 5 insights
 */
export async function fetchDailyTop(limit: number = 5): Promise<Insight[]> {
  const { data } = await apiClient.get('/api/insights/daily-top', {
    params: { limit },
  });

  // Use safeParse to get detailed validation errors
  const result = z.array(InsightSchema).safeParse(data);

  if (!result.success) {
    console.error('Validation errors:', JSON.stringify(result.error.format(), null, 2));
    throw new Error(result.error.message);
  }

  return result.data;
}

/**
 * Check API health
 */
export async function checkHealth(): Promise<{ status: string; version: string }> {
  const { data } = await apiClient.get('/health');
  return data;
}

// ============================================
// User Workspace API (Phase 4)
// ============================================

/**
 * Create authenticated API client with Supabase token
 */
export function createAuthenticatedClient(accessToken: string) {
  return axios.create({
    baseURL: API_BASE_URL,
    headers: {
      'Content-Type': 'application/json',
      Authorization: `Bearer ${accessToken}`,
    },
    timeout: 10000,
  });
}

/**
 * Fetch user's workspace status (saved, interested, building counts)
 */
export async function fetchWorkspaceStatus(accessToken: string): Promise<WorkspaceStatus> {
  const client = createAuthenticatedClient(accessToken);
  const { data } = await client.get('/api/users/me/status');
  return WorkspaceStatusSchema.parse(data);
}

/**
 * Fetch user's saved insights
 */
export async function fetchSavedInsights(
  accessToken: string,
  params: { status?: string; limit?: number; offset?: number } = {}
): Promise<SavedInsightListResponse> {
  const client = createAuthenticatedClient(accessToken);
  const { data } = await client.get('/api/users/me/saved', { params });
  return SavedInsightListResponseSchema.parse(data);
}

/**
 * Fetch user's ratings
 */
export async function fetchUserRatings(
  accessToken: string,
  params: { limit?: number; offset?: number } = {}
): Promise<RatingListResponse> {
  const client = createAuthenticatedClient(accessToken);
  const { data } = await client.get('/api/users/me/ratings', { params });
  return RatingListResponseSchema.parse(data);
}

/**
 * Save an insight to user's workspace
 */
export async function saveInsight(
  accessToken: string,
  insightId: string,
  payload?: { notes?: string; tags?: string[] }
): Promise<SavedInsight> {
  const client = createAuthenticatedClient(accessToken);
  const { data } = await client.post(`/api/users/insights/${insightId}/save`, payload || {});
  return SavedInsightSchema.parse(data);
}

/**
 * Unsave an insight from user's workspace
 */
export async function unsaveInsight(accessToken: string, insightId: string): Promise<void> {
  const client = createAuthenticatedClient(accessToken);
  await client.delete(`/api/users/insights/${insightId}/save`);
}

/**
 * Mark an insight as interested
 */
export async function markInterested(accessToken: string, insightId: string): Promise<SavedInsight> {
  const client = createAuthenticatedClient(accessToken);
  const { data } = await client.post(`/api/users/insights/${insightId}/interested`);
  return SavedInsightSchema.parse(data);
}

/**
 * Claim an insight (mark as building)
 */
export async function claimInsight(
  accessToken: string,
  insightId: string
): Promise<{ status: string; claimed_at: string; insight_id: string }> {
  const client = createAuthenticatedClient(accessToken);
  const { data } = await client.post(`/api/users/insights/${insightId}/claim`);
  return data;
}

/**
 * Rate an insight
 */
export async function rateInsight(
  accessToken: string,
  insightId: string,
  payload: { rating: number; feedback?: string }
): Promise<UserRating> {
  const client = createAuthenticatedClient(accessToken);
  const { data } = await client.post(`/api/users/insights/${insightId}/rate`, payload);
  return UserRatingSchema.parse(data);
}

/**
 * Get user's rating for a specific insight
 */
export async function getMyRating(accessToken: string, insightId: string): Promise<UserRating | null> {
  const client = createAuthenticatedClient(accessToken);
  try {
    const { data } = await client.get(`/api/users/insights/${insightId}/rate`);
    return data ? UserRatingSchema.parse(data) : null;
  } catch {
    return null;
  }
}

// ============================================
// Teams API (Phase 6.4)
// ============================================

/**
 * List user's teams
 */
export async function fetchTeams(accessToken: string): Promise<Team[]> {
  const client = createAuthenticatedClient(accessToken);
  const { data } = await client.get('/api/teams');
  return z.array(TeamSchema).parse(data);
}

/**
 * Get team details
 */
export async function fetchTeam(accessToken: string, teamId: string): Promise<Team> {
  const client = createAuthenticatedClient(accessToken);
  const { data } = await client.get(`/api/teams/${teamId}`);
  return TeamSchema.parse(data);
}

/**
 * Create a new team
 */
export async function createTeam(
  accessToken: string,
  payload: { name: string; description?: string }
): Promise<Team> {
  const client = createAuthenticatedClient(accessToken);
  const { data } = await client.post('/api/teams', payload);
  return TeamSchema.parse(data);
}

/**
 * Update team
 */
export async function updateTeam(
  accessToken: string,
  teamId: string,
  payload: { name?: string; description?: string }
): Promise<Team> {
  const client = createAuthenticatedClient(accessToken);
  const { data } = await client.patch(`/api/teams/${teamId}`, payload);
  return TeamSchema.parse(data);
}

/**
 * Delete team
 */
export async function deleteTeam(accessToken: string, teamId: string): Promise<void> {
  const client = createAuthenticatedClient(accessToken);
  await client.delete(`/api/teams/${teamId}`);
}

/**
 * List team members
 */
export async function fetchTeamMembers(accessToken: string, teamId: string): Promise<TeamMember[]> {
  const client = createAuthenticatedClient(accessToken);
  const { data } = await client.get(`/api/teams/${teamId}/members`);
  return z.array(TeamMemberSchema).parse(data);
}

/**
 * Invite member to team
 */
export async function inviteTeamMember(
  accessToken: string,
  teamId: string,
  payload: { email: string; role?: string }
): Promise<TeamInvitation> {
  const client = createAuthenticatedClient(accessToken);
  const { data } = await client.post(`/api/teams/${teamId}/invitations`, payload);
  return TeamInvitationSchema.parse(data);
}

/**
 * Remove member from team
 */
export async function removeTeamMember(
  accessToken: string,
  teamId: string,
  userId: string
): Promise<void> {
  const client = createAuthenticatedClient(accessToken);
  await client.delete(`/api/teams/${teamId}/members/${userId}`);
}

// ============================================
// API Keys API (Phase 7.2)
// ============================================

/**
 * List user's API keys
 */
export async function fetchAPIKeys(accessToken: string): Promise<APIKeyListResponse> {
  const client = createAuthenticatedClient(accessToken);
  const { data } = await client.get('/api/keys');
  return APIKeyListResponseSchema.parse(data);
}

/**
 * Create a new API key
 */
export async function createAPIKey(
  accessToken: string,
  payload: { name: string; description?: string; scopes?: string[]; expires_in_days?: number }
): Promise<APIKeyCreateResponse> {
  const client = createAuthenticatedClient(accessToken);
  const { data } = await client.post('/api/keys', payload);
  return APIKeyCreateResponseSchema.parse(data);
}

/**
 * Get API key details
 */
export async function fetchAPIKey(accessToken: string, keyId: string): Promise<APIKey> {
  const client = createAuthenticatedClient(accessToken);
  const { data } = await client.get(`/api/keys/${keyId}`);
  return APIKeySchema.parse(data);
}

/**
 * Revoke (delete) an API key
 */
export async function revokeAPIKey(accessToken: string, keyId: string, reason?: string): Promise<void> {
  const client = createAuthenticatedClient(accessToken);
  await client.delete(`/api/keys/${keyId}`, { params: { reason } });
}

/**
 * Get API key usage statistics
 */
export async function fetchAPIKeyUsage(
  accessToken: string,
  keyId: string,
  days: number = 7
): Promise<APIKeyUsage> {
  const client = createAuthenticatedClient(accessToken);
  const { data } = await client.get(`/api/keys/${keyId}/usage`, { params: { days } });
  return APIKeyUsageSchema.parse(data);
}

/**
 * Get available API scopes
 */
export async function fetchAPIScopes(): Promise<Record<string, string>> {
  const { data } = await apiClient.get('/api/keys/scopes');
  return data.scopes;
}

// ============================================
// Payments API (Phase 6.1)
// ============================================

/**
 * Get pricing tiers (public)
 */
export async function fetchPricing(): Promise<PricingResponse> {
  const { data } = await apiClient.get('/api/payments/pricing');
  return PricingResponseSchema.parse(data);
}

/**
 * Create Stripe checkout session
 */
export async function createCheckoutSession(
  accessToken: string,
  payload: {
    tier: 'starter' | 'pro' | 'enterprise';
    billing_cycle?: 'monthly' | 'yearly';
    success_url: string;
    cancel_url: string;
  }
): Promise<CheckoutResponse> {
  const client = createAuthenticatedClient(accessToken);
  const { data } = await client.post('/api/payments/checkout', payload);
  return CheckoutResponseSchema.parse(data);
}

/**
 * Create customer portal session for subscription management
 */
export async function createPortalSession(
  accessToken: string,
  returnUrl: string
): Promise<{ portal_url: string }> {
  const client = createAuthenticatedClient(accessToken);
  const { data } = await client.post('/api/payments/portal', { return_url: returnUrl });
  return data;
}

/**
 * Get user's subscription status
 */
export async function fetchSubscriptionStatus(accessToken: string): Promise<SubscriptionStatus> {
  const client = createAuthenticatedClient(accessToken);
  const { data } = await client.get('/api/payments/subscription');
  return SubscriptionStatusSchema.parse(data);
}

// ============================================
// Admin API (Phase 4.2)
// ============================================

/**
 * Get admin dashboard metrics
 */
export async function fetchAdminDashboard(accessToken: string): Promise<DashboardMetrics> {
  const client = createAuthenticatedClient(accessToken);
  const { data } = await client.get('/api/admin/dashboard');
  return DashboardMetricsSchema.parse(data);
}

/**
 * List all agents with status
 */
export async function fetchAgentStatus(accessToken: string): Promise<AgentStatus[]> {
  const client = createAuthenticatedClient(accessToken);
  const { data } = await client.get('/api/admin/agents');
  return z.array(AgentStatusSchema).parse(data);
}

/**
 * Pause agent execution
 */
export async function pauseAgent(
  accessToken: string,
  agentType: string
): Promise<{ status: string; agent_type: string }> {
  const client = createAuthenticatedClient(accessToken);
  const { data } = await client.post(`/api/admin/agents/${agentType}/pause`);
  return data;
}

/**
 * Resume agent execution
 */
export async function resumeAgent(
  accessToken: string,
  agentType: string
): Promise<{ status: string; agent_type: string }> {
  const client = createAuthenticatedClient(accessToken);
  const { data } = await client.post(`/api/admin/agents/${agentType}/resume`);
  return data;
}

/**
 * Trigger agent execution manually
 */
export async function triggerAgent(
  accessToken: string,
  agentType: string
): Promise<{ status: string; agent_type: string; job_id?: string }> {
  const client = createAuthenticatedClient(accessToken);
  const { data } = await client.post(`/api/admin/agents/${agentType}/trigger`);
  return data;
}

/**
 * Get insight review queue
 */
export async function fetchReviewQueue(
  accessToken: string,
  params: { status?: string; limit?: number; offset?: number } = {}
): Promise<ReviewQueueResponse> {
  const client = createAuthenticatedClient(accessToken);
  const { data } = await client.get('/api/admin/insights', { params });
  return ReviewQueueResponseSchema.parse(data);
}

/**
 * Update insight admin status
 */
export async function updateInsightStatus(
  accessToken: string,
  insightId: string,
  payload: { admin_status?: string; admin_notes?: string; admin_override_score?: number }
): Promise<InsightReview> {
  const client = createAuthenticatedClient(accessToken);
  const { data } = await client.patch(`/api/admin/insights/${insightId}`, payload);
  return InsightReviewSchema.parse(data);
}

// ============================================
// Admin User Management
// ============================================

export interface AdminUserListItem {
  id: string;
  email: string;
  display_name: string | null;
  subscription_tier: string;
  created_at: string;
  last_active: string | null;
  admin_role: string | null;
  is_suspended: boolean;
  language: string;
  last_login_at: string | null;
}

export interface AdminUserDetail {
  id: string;
  email: string;
  display_name: string | null;
  avatar_url: string | null;
  subscription_tier: string;
  created_at: string;
  insights_saved: number;
  research_count: number;
  total_sessions: number;
  admin_role: string | null;
  is_suspended: boolean;
  language: string;
  last_login_at: string | null;
}

export async function fetchAdminUsers(
  accessToken: string,
  params: { search?: string; tier?: string; limit?: number; offset?: number } = {}
): Promise<AdminUserListItem[]> {
  const client = createAuthenticatedClient(accessToken);
  const { data } = await client.get('/admin/analytics/users/list', { params });
  return data;
}

export async function fetchAdminUserDetail(
  accessToken: string,
  userId: string
): Promise<AdminUserDetail> {
  const client = createAuthenticatedClient(accessToken);
  const { data } = await client.get(`/admin/analytics/users/${userId}`);
  return data;
}

export async function createAdminUser(
  accessToken: string,
  payload: { email: string; display_name?: string; subscription_tier?: string; language?: string }
): Promise<{ status: string; user_id: string }> {
  const client = createAuthenticatedClient(accessToken);
  const { data } = await client.post('/admin/analytics/users', payload);
  return data;
}

export async function updateAdminUser(
  accessToken: string,
  userId: string,
  updates: { subscription_tier?: string; is_suspended?: boolean; display_name?: string; language?: string }
): Promise<{ status: string; user_id: string }> {
  const client = createAuthenticatedClient(accessToken);
  const { data } = await client.patch(`/admin/analytics/users/${userId}`, updates);
  return data;
}

export async function deleteAdminUser(
  accessToken: string,
  userId: string,
  reason: string = ''
): Promise<{ status: string; user_id: string }> {
  const client = createAuthenticatedClient(accessToken);
  const { data } = await client.delete(`/admin/analytics/users/${userId}`, { params: { reason } });
  return data;
}

export async function bulkAdminUserAction(
  accessToken: string,
  payload: { user_ids: string[]; action: string; tier?: string; reason?: string }
): Promise<{ status: string; affected: number }> {
  const client = createAuthenticatedClient(accessToken);
  const { data } = await client.post('/admin/analytics/users/bulk', payload);
  return data;
}

// ============================================
// Audit Logs API
// ============================================

export interface AuditLogEntry {
  id: string;
  user_id: string | null;
  action: string;
  resource_type: string;
  resource_id: string | null;
  details: Record<string, unknown> | null;
  ip_address: string | null;
  created_at: string;
}

export interface AuditLogStats {
  total_events: number;
  by_action: Record<string, number>;
  by_resource: Record<string, number>;
  period_days: number;
}

export async function fetchAuditLogs(
  accessToken: string,
  params: { action?: string; resource_type?: string; days?: number; limit?: number } = {}
): Promise<AuditLogEntry[]> {
  const client = createAuthenticatedClient(accessToken);
  const { data } = await client.get('/admin/agents/audit-logs', { params });
  return data;
}

export async function fetchAuditLogStats(
  accessToken: string,
  days: number = 7
): Promise<AuditLogStats> {
  const client = createAuthenticatedClient(accessToken);
  const { data } = await client.get('/admin/agents/audit-logs/stats', { params: { days } });
  return data;
}

export async function fetchAuditLogActions(
  accessToken: string
): Promise<{ action: string; count: number }[]> {
  const client = createAuthenticatedClient(accessToken);
  const { data } = await client.get('/admin/agents/audit-logs/actions');
  return data;
}

// ============================================
// Agent Configuration API (Phase 8.4-8.5 - Admin Only)
// ============================================

export interface AgentConfig {
  id: string;
  agent_name: string;
  is_enabled: boolean;
  model_name: string;
  temperature: number;
  max_tokens: number;
  rate_limit_per_hour: number;
  cost_limit_daily_usd: number;
  custom_prompts: Record<string, unknown> | null;
  updated_at: string;
}

export interface AgentStats {
  agent_name: string;
  executions_24h: number;
  success_rate: number;
  avg_duration_ms: number;
  tokens_used_24h: number;
  cost_24h_usd: number;
}

/**
 * List all agent configurations (admin only)
 */
export async function fetchAgentConfigurations(accessToken: string): Promise<AgentConfig[]> {
  const client = createAuthenticatedClient(accessToken);
  const { data } = await client.get('/admin/agents/configurations');
  return data;
}

/**
 * Get a specific agent configuration (admin only)
 */
export async function fetchAgentConfiguration(accessToken: string, agentName: string): Promise<AgentConfig> {
  const client = createAuthenticatedClient(accessToken);
  const { data } = await client.get(`/admin/agents/configurations/${agentName}`);
  return data;
}

/**
 * Update agent configuration (admin only)
 */
export async function updateAgentConfiguration(
  accessToken: string,
  agentName: string,
  payload: {
    is_enabled?: boolean;
    model_name?: string;
    temperature?: number;
    max_tokens?: number;
    rate_limit_per_hour?: number;
    cost_limit_daily_usd?: number;
    custom_prompts?: Record<string, unknown>;
  }
): Promise<AgentConfig> {
  const client = createAuthenticatedClient(accessToken);
  const { data } = await client.patch(`/admin/agents/configurations/${agentName}`, payload);
  return data;
}

/**
 * Toggle agent on/off (admin only)
 */
export async function toggleAgentEnabled(
  accessToken: string,
  agentName: string
): Promise<{ agent_name: string; is_enabled: boolean }> {
  const client = createAuthenticatedClient(accessToken);
  const { data } = await client.post(`/admin/agents/configurations/${agentName}/toggle`);
  return data;
}

/**
 * Create a new agent configuration (admin only)
 */
export async function createAgentConfiguration(
  accessToken: string,
  payload: {
    agent_name: string;
    is_enabled?: boolean;
    model_name?: string;
    temperature?: number;
    max_tokens?: number;
    rate_limit_per_hour?: number;
    cost_limit_daily_usd?: number;
    custom_prompts?: Record<string, unknown>;
  }
): Promise<AgentConfig> {
  const client = createAuthenticatedClient(accessToken);
  const { data } = await client.post('/admin/agents/configurations', payload);
  return data;
}

/**
 * Delete an agent configuration (admin only)
 */
export async function deleteAgentConfiguration(
  accessToken: string,
  agentName: string
): Promise<void> {
  const client = createAuthenticatedClient(accessToken);
  await client.delete(`/admin/agents/configurations/${agentName}`);
}

/**
 * Get agent execution statistics (admin only)
 */
export async function fetchAgentExecutionStats(accessToken: string): Promise<AgentStats[]> {
  const client = createAuthenticatedClient(accessToken);
  const { data } = await client.get('/admin/agents/stats');
  return data;
}

/**
 * Get execution logs for a specific agent (admin only)
 */
export interface AgentExecutionLog {
  id: string;
  agent_type: string;
  source: string | null;
  status: string;
  started_at: string;
  completed_at: string | null;
  duration_ms: number | null;
  items_processed: number;
  items_failed: number;
  error_message: string | null;
  extra_metadata: Record<string, unknown>;
  created_at: string;
}

export async function fetchAgentLogs(
  accessToken: string,
  agentType: string,
  limit = 20,
  offset = 0
): Promise<{ items: AgentExecutionLog[]; total: number }> {
  const client = createAuthenticatedClient(accessToken);
  const { data } = await client.get(`/api/admin/agents/${agentType}/logs`, {
    params: { limit, offset },
  });
  return data;
}

// ============================================
// User Profile API (Phase 4.1)
// ============================================

/**
 * Get current user profile
 */
export async function fetchUserProfile(accessToken: string): Promise<UserProfile> {
  const client = createAuthenticatedClient(accessToken);
  const { data } = await client.get('/api/users/me');
  return UserProfileSchema.parse(data);
}

/**
 * Update user profile
 */
export async function updateUserProfile(
  accessToken: string,
  payload: UserUpdate
): Promise<UserProfile> {
  const client = createAuthenticatedClient(accessToken);
  const { data } = await client.patch('/api/users/me', payload);
  return UserProfileSchema.parse(data);
}

// ============================================
// Tenant API (Phase 7.3)
// ============================================

/**
 * Create a new tenant
 */
export async function createTenant(
  accessToken: string,
  payload: { name: string; subdomain?: string }
): Promise<Tenant> {
  const client = createAuthenticatedClient(accessToken);
  const { data } = await client.post('/api/tenants', payload);
  return TenantSchema.parse(data);
}

/**
 * Get current user's tenant
 */
export async function fetchCurrentTenant(accessToken: string): Promise<Tenant | null> {
  const client = createAuthenticatedClient(accessToken);
  try {
    const { data } = await client.get('/api/tenants/current');
    return TenantSchema.parse(data);
  } catch {
    return null;
  }
}

/**
 * Get tenant by ID
 */
export async function fetchTenant(accessToken: string, tenantId: string): Promise<Tenant> {
  const client = createAuthenticatedClient(accessToken);
  const { data } = await client.get(`/api/tenants/${tenantId}`);
  return TenantSchema.parse(data);
}

/**
 * Get tenant branding
 */
export async function fetchTenantBranding(accessToken: string, tenantId: string): Promise<TenantBranding> {
  const client = createAuthenticatedClient(accessToken);
  const { data } = await client.get(`/api/tenants/${tenantId}/branding`);
  return TenantBrandingSchema.parse(data);
}

/**
 * Update tenant branding
 */
export async function updateTenantBranding(
  accessToken: string,
  tenantId: string,
  payload: {
    logo_url?: string;
    favicon_url?: string;
    primary_color?: string;
    secondary_color?: string;
    accent_color?: string;
    app_name?: string;
    tagline?: string;
  }
): Promise<TenantBranding> {
  const client = createAuthenticatedClient(accessToken);
  const { data } = await client.patch(`/api/tenants/${tenantId}/branding`, payload);
  return TenantBrandingSchema.parse(data);
}

/**
 * Configure custom domain for tenant
 */
export async function configureTenantDomain(
  accessToken: string,
  tenantId: string,
  customDomain: string
): Promise<DomainConfig> {
  const client = createAuthenticatedClient(accessToken);
  const { data } = await client.post(`/api/tenants/${tenantId}/domain`, { custom_domain: customDomain });
  return DomainConfigSchema.parse(data);
}

/**
 * Verify custom domain DNS configuration
 */
export async function verifyTenantDomain(
  accessToken: string,
  tenantId: string
): Promise<{ domain: string; verified: boolean; ssl_status: string }> {
  const client = createAuthenticatedClient(accessToken);
  const { data } = await client.post(`/api/tenants/${tenantId}/domain/verify`);
  return data;
}

/**
 * Remove custom domain
 */
export async function removeTenantDomain(accessToken: string, tenantId: string): Promise<void> {
  const client = createAuthenticatedClient(accessToken);
  await client.delete(`/api/tenants/${tenantId}/domain`);
}

// ============================================
// Email Preferences API (Phase 9.1)
// ============================================

/**
 * Fetch user's email preferences
 */
export async function fetchEmailPreferences(accessToken: string) {
  const client = createAuthenticatedClient(accessToken);
  const { data } = await client.get('/api/preferences/email');
  return data as { daily_digest: boolean; weekly_digest: boolean; instant_alerts: boolean };
}

/**
 * Update user's email preferences
 */
export async function updateEmailPreferences(
  accessToken: string,
  payload: { daily_digest?: boolean; weekly_digest?: boolean; instant_alerts?: boolean }
) {
  const client = createAuthenticatedClient(accessToken);
  const { data } = await client.patch('/api/preferences/email', payload);
  return data;
}

// ============================================
// Research Request API (Phase 5.2: Admin Queue)
// ============================================

/**
 * Submit a research request (user endpoint)
 */
export async function createResearchRequest(
  accessToken: string,
  data: {
    idea_description: string;
    target_market: string;
    budget_range?: string;
  }
): Promise<ResearchRequest> {
  const client = createAuthenticatedClient(accessToken);
  const { data: response } = await client.post('/api/research/request', data);
  return ResearchRequestSchema.parse(response);
}

/**
 * List user's research requests
 */
export async function fetchUserResearchRequests(
  accessToken: string,
  params?: { limit?: number; offset?: number }
): Promise<ResearchRequestListResponse> {
  const client = createAuthenticatedClient(accessToken);
  const { data } = await client.get('/api/research/requests', { params });
  return ResearchRequestListResponseSchema.parse(data);
}

/**
 * Admin: List all research requests with optional status filter
 */
export async function fetchAdminResearchRequests(
  accessToken: string,
  params?: { status?: 'pending' | 'approved' | 'rejected' | 'completed'; limit?: number; offset?: number }
): Promise<ResearchRequestListResponse> {
  const client = createAuthenticatedClient(accessToken);
  const { data } = await client.get('/api/research/admin/requests', { params });
  return ResearchRequestListResponseSchema.parse(data);
}

/**
 * Admin: Approve or reject a research request
 */
export async function updateResearchRequest(
  accessToken: string,
  requestId: string,
  action: ResearchRequestAction
): Promise<ResearchRequest> {
  const client = createAuthenticatedClient(accessToken);
  const { data } = await client.patch(`/api/research/admin/requests/${requestId}`, action);
  return ResearchRequestSchema.parse(data);
}

/**
 * Admin: Manually trigger analysis (bypass request queue)
 */
export async function adminTriggerAnalysis(
  accessToken: string,
  data: {
    idea_description: string;
    target_market: string;
    budget_range?: string;
  }
): Promise<any> {
  const client = createAuthenticatedClient(accessToken);
  const { data: response } = await client.post('/api/research/admin/analyze', data);
  return response;
}

/**
 * Admin: List all analyses (all users)
 */
export async function fetchAdminAnalyses(
  accessToken: string,
  params?: { limit?: number; offset?: number }
): Promise<any> {
  const client = createAuthenticatedClient(accessToken);
  const { data } = await client.get('/api/research/admin/analyses', { params });
  return data;
}
