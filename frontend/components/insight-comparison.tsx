'use client';

import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Trophy } from 'lucide-react';
import type { Insight } from '@/lib/types';

interface InsightComparisonProps {
  insights: Insight[];
}

type DimensionKey = 'opportunity_score' | 'problem_score' | 'feasibility_score' | 'why_now_score' | 'go_to_market_score' | 'founder_fit_score' | 'execution_difficulty_score';

const dimensions: { key: DimensionKey; label: string }[] = [
  { key: 'opportunity_score', label: 'Opportunity' },
  { key: 'problem_score', label: 'Problem Severity' },
  { key: 'feasibility_score', label: 'Feasibility' },
  { key: 'why_now_score', label: 'Why Now' },
  { key: 'go_to_market_score', label: 'Go-To-Market' },
  { key: 'founder_fit_score', label: 'Founder Fit' },
  { key: 'execution_difficulty_score', label: 'Execution' },
];

const colors = ['text-blue-600', 'text-emerald-600', 'text-purple-600'];
const bgColors = ['bg-blue-50 dark:bg-blue-950/30', 'bg-emerald-50 dark:bg-emerald-950/30', 'bg-purple-50 dark:bg-purple-950/30'];

export function InsightComparison({ insights }: InsightComparisonProps) {
  if (insights.length < 2) return null;
  const items = insights.slice(0, 3);

  return (
    <Card>
      <CardHeader>
        <CardTitle>Side-by-Side Comparison</CardTitle>
      </CardHeader>
      <CardContent>
        {/* Header row */}
        <div className="grid gap-3" style={{ gridTemplateColumns: `120px repeat(${items.length}, 1fr)` }}>
          <div />
          {items.map((insight, i) => (
            <div key={insight.id} className={`rounded-lg p-3 ${bgColors[i]}`}>
              <p className={`text-sm font-semibold ${colors[i]} line-clamp-2`}>
                {insight.proposed_solution}
              </p>
              <p className="text-xs text-muted-foreground mt-1">
                Score: {(insight.relevance_score * 10).toFixed(1)}
              </p>
            </div>
          ))}
        </div>

        {/* Dimension rows */}
        <div className="mt-4 space-y-1">
          {dimensions.map((dim) => {
            const scores = items.map((ins) => {
              const val = ins[dim.key];
              return typeof val === 'number' ? val : null;
            });
            const validScores = scores.filter((s): s is number => s !== null);
            const maxScore = validScores.length > 0 ? Math.max(...validScores) : 0;

            return (
              <div
                key={dim.key}
                className="grid gap-3 py-2 border-b border-border/50 last:border-0 items-center"
                style={{ gridTemplateColumns: `120px repeat(${items.length}, 1fr)` }}
              >
                <span className="text-xs font-medium text-muted-foreground">{dim.label}</span>
                {scores.map((score, i) => (
                  <div key={i} className="flex items-center gap-2">
                    {score !== null ? (
                      <>
                        <div className="flex-1 h-2 bg-muted rounded-full overflow-hidden">
                          <div
                            className={`h-full rounded-full ${colors[i].replace('text-', 'bg-').replace('-600', '-500')}`}
                            style={{ width: `${score * 10}%` }}
                          />
                        </div>
                        <span className={`text-sm font-bold w-6 text-right ${score === maxScore && validScores.length > 1 ? colors[i] : ''}`}>
                          {score}
                        </span>
                        {score === maxScore && validScores.length > 1 && (
                          <Trophy className="h-3 w-3 text-amber-500" />
                        )}
                      </>
                    ) : (
                      <span className="text-xs text-muted-foreground">N/A</span>
                    )}
                  </div>
                ))}
              </div>
            );
          })}
        </div>

        {/* Revenue potential row */}
        <div
          className="grid gap-3 py-2 items-center"
          style={{ gridTemplateColumns: `120px repeat(${items.length}, 1fr)` }}
        >
          <span className="text-xs font-medium text-muted-foreground">Revenue</span>
          {items.map((ins, i) => (
            <div key={i}>
              {ins.revenue_potential_score ? (
                <Badge variant="outline" className="text-xs">
                  {ins.revenue_potential_score}
                </Badge>
              ) : (
                <span className="text-xs text-muted-foreground">N/A</span>
              )}
            </div>
          ))}
        </div>
      </CardContent>
    </Card>
  );
}
