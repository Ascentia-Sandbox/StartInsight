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
  created_at: z.string().datetime({ offset: false }), // Backend returns datetime without Z suffix
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
