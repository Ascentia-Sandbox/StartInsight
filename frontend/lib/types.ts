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
