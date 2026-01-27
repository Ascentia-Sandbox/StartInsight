import { z } from 'zod';

// Datetime validator
const datetimeValidator = z.string().refine(
  (val) => {
    const isoDatetimeRegex = /^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d+)?(?:Z|[+-]\d{2}:\d{2})?$/;
    return isoDatetimeRegex.test(val);
  },
  { message: 'Invalid datetime format' }
);

const CompetitorSchema = z.object({
  name: z.string(),
  url: z.string().url(),
  description: z.string(),
  market_position: z.enum(['Small', 'Medium', 'Large']).nullable().optional(),
});

const RawSignalSummarySchema = z.object({
  id: z.string().uuid(),
  source: z.string(),
  url: z.string().url(),
  created_at: datetimeValidator,
  extra_metadata: z.record(z.string(), z.any()).nullable().optional(),
});

const CommunitySignalSchema = z.object({
  platform: z.enum(['Reddit', 'Facebook', 'YouTube', 'Other']),
  score: z.number().min(1).max(10),
  members: z.number().min(0),
  engagement_rate: z.number().min(0).max(1),
  top_url: z.string().url().nullable().optional(),
});

const EnhancedScoreSchema = z.object({
  dimension: z.string(),
  value: z.number().min(1).max(10),
  label: z.string(),
});

const InsightSchema = z.object({
  id: z.string().uuid(),
  raw_signal_id: z.string().uuid(),
  problem_statement: z.string(),
  proposed_solution: z.string(),
  market_size_estimate: z.string(),
  relevance_score: z.number().min(0).max(1),
  competitor_analysis: z.array(CompetitorSchema),
  created_at: datetimeValidator,
  raw_signal: RawSignalSummarySchema.optional(),
  community_signals_chart: z.array(CommunitySignalSchema).nullable().optional(),
  enhanced_scores: z.array(EnhancedScoreSchema).nullable().optional(),
  value_ladder: z.record(z.string(), z.any()).optional(),
  market_gap_analysis: z.string().optional(),
  why_now_analysis: z.string().optional(),
});

// New test data with valid UUIDs from actual API
const testData = [{
  "id": "e5f6a7b8-9c0d-4e1f-2a3b-4c5d6e7f8a9b",
  "raw_signal_id": "102b58da-bd8e-4458-8b06-7a113a950493",
  "problem_statement": "Customer support teams are overwhelmed with repetitive questions and slow response times",
  "proposed_solution": "AI ticketing system that auto-categorizes, suggests responses, and escalates complex issues",
  "market_size_estimate": "$5B-$20B",
  "relevance_score": 0.95,
  "competitor_analysis": [],
  "created_at": "2026-01-25T12:52:29.823828Z",
  "raw_signal": {
    "id": "102b58da-bd8e-4458-8b06-7a113a950493",
    "source": "reddit",
    "url": "https://reddit.com/r/startups/example5",
    "created_at": "2026-01-25T12:52:29.814756"
  },
  "community_signals_chart": [
    {
      "platform": "Reddit",
      "score": 9,
      "members": 75000,
      "engagement_rate": 0.22,
      "top_url": "https://reddit.com/r/startups"
    }
  ],
  "enhanced_scores": [
    {
      "dimension": "Opportunity",
      "value": 9,
      "label": "Very Strong"
    }
  ]
}];

const result = z.array(InsightSchema).safeParse(testData);

if (!result.success) {
  console.error('Validation failed:');
  console.error(JSON.stringify(result.error.format(), null, 2));
} else {
  console.log('✓ Validation passed!');
}
