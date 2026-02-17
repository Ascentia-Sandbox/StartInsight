import Link from 'next/link';
import { formatDistanceToNow } from 'date-fns';
import { ShieldCheck, ShieldAlert, ShieldQuestion, Database } from 'lucide-react';
import type { Insight } from '@/lib/types';
import { TrendSparkline } from '@/components/trend-sparkline';

interface InsightCardProps {
  insight: Insight;
}

// Source display configuration with platform-branded colors
const sourceConfig: Record<string, { label: string; className: string }> = {
  reddit: { label: 'Reddit', className: 'bg-orange-100 text-orange-700 dark:bg-orange-900/40 dark:text-orange-300' },
  product_hunt: { label: 'Product Hunt', className: 'bg-red-100 text-red-700 dark:bg-red-900/40 dark:text-red-300' },
  hacker_news: { label: 'Hacker News', className: 'bg-amber-100 text-amber-700 dark:bg-amber-900/40 dark:text-amber-300' },
  twitter: { label: 'Twitter/X', className: 'bg-sky-100 text-sky-700 dark:bg-sky-900/40 dark:text-sky-300' },
  google_trends: { label: 'Google Trends', className: 'bg-blue-100 text-blue-700 dark:bg-blue-900/40 dark:text-blue-300' },
  seed_data: { label: 'Curated', className: 'bg-purple-100 text-purple-700 dark:bg-purple-900/40 dark:text-purple-300' },
};

// Helper to get score from enhanced_scores array
function getEnhancedScore(insight: Insight, dimension: string): number | null {
  if (!insight.enhanced_scores) return null;
  const score = insight.enhanced_scores.find(
    (s) => s.dimension.toLowerCase().includes(dimension.toLowerCase())
  );
  return score?.value ?? null;
}

// Calculate overall score from all available 8-dimension scores
function getOverallScore(insight: Insight): number {
  const scores: number[] = [];

  const dimensions = [
    { field: 'opportunity_score' as const, fallback: 'opportunity' },
    { field: 'problem_score' as const, fallback: 'problem' },
    { field: 'feasibility_score' as const, fallback: 'feasibility' },
    { field: 'why_now_score' as const, fallback: 'why_now' },
    { field: 'go_to_market_score' as const, fallback: 'go_to_market' },
    { field: 'founder_fit_score' as const, fallback: 'founder_fit' },
    { field: 'execution_difficulty_score' as const, fallback: 'execution' },
  ];

  for (const dim of dimensions) {
    const val = insight[dim.field] ?? getEnhancedScore(insight, dim.fallback);
    if (val !== null && val !== undefined) scores.push(typeof val === 'number' ? val : 0);
  }

  // Also check revenue_potential (can be string or number)
  const rev = insight.revenue_potential_score;
  if (rev !== null && rev !== undefined) {
    const revNum = typeof rev === 'number' ? rev : parseFloat(rev);
    if (!isNaN(revNum)) scores.push(revNum);
  }

  if (scores.length === 0) {
    // Fallback to relevance_score (0-1 range, scale to 0-10)
    return insight.relevance_score * 10;
  }

  return scores.reduce((a, b) => a + b, 0) / scores.length;
}

// Confidence level derived from relevance_score
function getConfidenceLevel(insight: Insight): {
  label: string;
  className: string;
  icon: typeof ShieldCheck;
} {
  const score = insight.relevance_score;
  if (score >= 0.8) {
    return {
      label: 'High Confidence',
      className: 'bg-green-100 text-green-700 dark:bg-green-900/40 dark:text-green-300',
      icon: ShieldCheck,
    };
  }
  if (score >= 0.5) {
    return {
      label: 'Medium',
      className: 'bg-amber-100 text-amber-700 dark:bg-amber-900/40 dark:text-amber-300',
      icon: ShieldAlert,
    };
  }
  return {
    label: 'Needs Verification',
    className: 'bg-gray-100 text-gray-600 dark:bg-gray-800/40 dark:text-gray-400',
    icon: ShieldQuestion,
  };
}

// Count data points backing this insight
function getDataPointCount(insight: Insight): number {
  let count = 0;
  if (insight.proof_signals?.length) count += insight.proof_signals.length;
  if (insight.community_signals_chart?.length) count += insight.community_signals_chart.length;
  if (insight.trend_keywords?.length) count += insight.trend_keywords.length;
  if (insight.enhanced_scores?.length) count += 1; // scoring itself is a data point
  if (insight.raw_signal) count += 1; // the source signal
  return count;
}

// Market size visual indicator using circles
function MarketSizeIndicator({ size }: { size: string }) {
  const normalized = size.toLowerCase();
  let filled = 1; // default small
  if (normalized.includes('large') || normalized.includes('billion') || normalized.includes('$1b') || normalized.includes('$5b') || normalized.includes('$10b') || normalized.includes('$20b') || normalized.includes('$50b') || normalized.includes('$100b')) {
    filled = 3;
  } else if (normalized.includes('medium') || normalized.includes('million') || normalized.includes('$100m') || normalized.includes('$500m')) {
    filled = 2;
  }

  return (
    <div className="flex items-center gap-1" title={`Market: ${size}`}>
      {[1, 2, 3].map((i) => (
        <div
          key={i}
          className={`rounded-full ${
            i <= filled
              ? 'bg-primary'
              : 'bg-muted-foreground/20'
          }`}
          style={{ width: 6 + i * 2, height: 6 + i * 2 }}
        />
      ))}
      <span className="text-xs text-muted-foreground ml-1">{size}</span>
    </div>
  );
}

export function InsightCard({ insight }: InsightCardProps) {
  const source = insight.raw_signal?.source;
  const sourceDisplay = source ? sourceConfig[source] : null;
  const overallScore = getOverallScore(insight);
  const scorePercent = Math.min(100, Math.max(0, overallScore * 10));
  const confidence = getConfidenceLevel(insight);
  const dataPoints = getDataPointCount(insight);
  const ConfidenceIcon = confidence.icon;

  return (
    <Link href={`/insights/${insight.slug || insight.id}`} className="block group">
      <div className="card-hover h-full flex flex-col rounded-xl border bg-card p-5 transition-all">
        {/* Header: Title + Source badge */}
        <div className="flex items-start justify-between gap-3 mb-3">
          <h3 className="text-base font-semibold leading-snug line-clamp-2 group-hover:text-primary transition-colors">
            {insight.title || insight.proposed_solution}
          </h3>
          {sourceDisplay && (
            <span className={`shrink-0 text-xs font-medium px-2 py-0.5 rounded-full ${sourceDisplay.className}`}>
              {sourceDisplay.label}
            </span>
          )}
        </div>

        {/* Problem statement excerpt */}
        <p className="text-sm text-muted-foreground line-clamp-2 mb-3">
          {insight.problem_statement.split('.')[0]}.
        </p>

        {/* Confidence badge + data points */}
        <div className="flex items-center gap-2 mb-3">
          <span className={`inline-flex items-center gap-1 text-xs font-medium px-2 py-0.5 rounded-full ${confidence.className}`}>
            <ConfidenceIcon className="h-3 w-3" />
            {confidence.label}
          </span>
          {dataPoints > 0 && (
            <span className="inline-flex items-center gap-1 text-xs text-muted-foreground">
              <Database className="h-3 w-3" />
              {dataPoints} data points
            </span>
          )}
        </div>

        {/* Score bar */}
        <div className="mb-4">
          <div className="flex items-center justify-between mb-1.5">
            <span className="text-xs text-muted-foreground font-medium">Overall Score</span>
            <span className="font-data text-sm font-bold">{overallScore.toFixed(1)}<span className="text-muted-foreground font-normal">/10</span></span>
          </div>
          <div className="w-full h-2 bg-muted rounded-full overflow-hidden">
            <div
              className="h-full rounded-full transition-all duration-500"
              style={{
                width: `${scorePercent}%`,
                background: 'linear-gradient(90deg, #0D7377, #10B981)',
              }}
            />
          </div>
        </div>

        {/* Trend sparkline */}
        {insight.trend_data && insight.trend_data.values.length >= 2 && (
          <div className="mb-3">
            <TrendSparkline
              data={insight.trend_data.values}
              growth={insight.trend_keywords?.[0]?.growth}
              width={80}
              height={24}
            />
          </div>
        )}

        {/* Footer: Market size + date */}
        <div className="mt-auto flex items-center justify-between pt-2 border-t border-border/50">
          <MarketSizeIndicator size={insight.market_size_estimate} />
          <span className="text-xs text-muted-foreground">
            {formatDistanceToNow(new Date(insight.created_at), { addSuffix: true })}
          </span>
        </div>
      </div>
    </Link>
  );
}
