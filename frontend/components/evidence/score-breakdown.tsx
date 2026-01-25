'use client';

import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';

interface Score {
  dimension: string;
  value: number; // 1-10
  label: string;
}

interface ScoreBreakdownProps {
  scores: Score[];
}

// Helper function to get score color and variant
function getScoreVariant(value: number): {
  color: string;
  label: string;
} {
  if (value >= 8) return { color: 'bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-300', label: 'Excellent' };
  if (value >= 7) return { color: 'bg-blue-100 text-blue-800 dark:bg-blue-900 dark:text-blue-300', label: 'Strong' };
  if (value >= 5) return { color: 'bg-yellow-100 text-yellow-800 dark:bg-yellow-900 dark:text-yellow-300', label: 'Moderate' };
  if (value >= 3) return { color: 'bg-orange-100 text-orange-800 dark:bg-orange-900 dark:text-orange-300', label: 'Weak' };
  return { color: 'bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-300', label: 'Critical' };
}

export function ScoreBreakdown({ scores }: ScoreBreakdownProps) {
  // Calculate average score
  const avgScore = scores.length > 0
    ? (scores.reduce((sum, s) => sum + s.value, 0) / scores.length).toFixed(1)
    : '0';

  // Count strong scores (7+)
  const strongScores = scores.filter(s => s.value >= 7).length;

  return (
    <Card>
      <CardHeader>
        <CardTitle>8-Dimension Scoring Analysis</CardTitle>
        <CardDescription>
          Average: {avgScore}/10 • {strongScores}/{scores.length} strong dimensions (7+)
        </CardDescription>
      </CardHeader>
      <CardContent>
        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
          {scores.map(({ dimension, value, label }) => {
            const { color, label: autoLabel } = getScoreVariant(value);
            const displayLabel = label || autoLabel;

            return (
              <Card key={dimension} className="border-2">
                <CardContent className="p-4">
                  <div className="flex items-start justify-between gap-2">
                    <div className="flex-1">
                      <div className="text-sm font-medium text-muted-foreground">
                        {dimension}
                      </div>
                      <div className="mt-2 flex items-baseline gap-2">
                        <div className="text-3xl font-bold">
                          {value}
                        </div>
                        <div className="text-sm text-muted-foreground">/10</div>
                      </div>
                    </div>
                    <Badge className={color}>
                      {displayLabel}
                    </Badge>
                  </div>

                  {/* Visual bar indicator */}
                  <div className="mt-3">
                    <div className="h-2 w-full rounded-full bg-muted">
                      <div
                        className={`h-2 rounded-full transition-all ${
                          value >= 8 ? 'bg-green-500' :
                          value >= 7 ? 'bg-blue-500' :
                          value >= 5 ? 'bg-yellow-500' :
                          value >= 3 ? 'bg-orange-500' :
                          'bg-red-500'
                        }`}
                        style={{ width: `${(value / 10) * 100}%` }}
                      />
                    </div>
                  </div>
                </CardContent>
              </Card>
            );
          })}
        </div>

        {scores.length === 0 && (
          <div className="flex h-32 items-center justify-center text-sm text-muted-foreground">
            No scoring data available
          </div>
        )}
      </CardContent>
    </Card>
  );
}
