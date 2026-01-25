'use client';

import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Legend } from 'recharts';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { getTrendBadgeClass, getTrendIcon, TREND_CONFIG, type TrendDirection } from '@/lib/utils/colors';

interface TrendData {
  keyword?: string;
  avg_interest?: number;
  max_interest?: number;
  current_interest?: number;
  trend_direction?: string;
  timeframe?: string;
  geo?: string;
}

interface TrendChartProps {
  data: TrendData | Record<string, any> | null | undefined;
  source: string;
}

export function TrendChart({ data, source }: TrendChartProps) {
  // Only show chart for Google Trends data
  if (!data || source !== 'google_trends') {
    return null;
  }

  const { keyword, avg_interest, max_interest, current_interest, trend_direction, timeframe, geo } = data;

  // Get trend color from centralized config
  const trendDir = (trend_direction?.toLowerCase() || 'unknown') as TrendDirection;
  const trendColor = TREND_CONFIG[trendDir]?.color || '#94a3b8';

  // Prepare chart data
  const chartData = [
    {
      name: 'Current',
      value: current_interest || 0,
      fill: trendColor.replace('text-', '#'), // Convert to hex for chart
    },
    {
      name: 'Average',
      value: avg_interest || 0,
      fill: '#94a3b8',
    },
    {
      name: 'Peak',
      value: max_interest || 0,
      fill: '#3b82f6',
    },
  ];

  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-xl">Search Trend Analysis</CardTitle>
        <CardDescription>
          Google Trends data for "{keyword}" ({timeframe} • {geo})
        </CardDescription>
      </CardHeader>
      <CardContent>
        <div className="space-y-4">
          {/* Trend Direction Badge */}
          <div className="flex items-center gap-2">
            <span className="text-sm font-medium">Trend Direction:</span>
            <span className={`px-3 py-1 rounded-full text-sm font-medium ${getTrendBadgeClass(trendDir)}`}>
              {getTrendIcon(trendDir)} {trend_direction?.toUpperCase() || 'UNKNOWN'}
            </span>
          </div>

          {/* Bar Chart */}
          <ResponsiveContainer width="100%" height={250}>
            <BarChart data={chartData}>
              <CartesianGrid strokeDasharray="3 3" className="stroke-muted" />
              <XAxis
                dataKey="name"
                className="text-xs"
                tick={{ fill: 'currentColor' }}
              />
              <YAxis
                label={{ value: 'Search Interest (0-100)', angle: -90, position: 'insideLeft' }}
                className="text-xs"
                tick={{ fill: 'currentColor' }}
              />
              <Tooltip
                contentStyle={{
                  backgroundColor: 'hsl(var(--card))',
                  border: '1px solid hsl(var(--border))',
                  borderRadius: '0.5rem',
                }}
                labelStyle={{ color: 'hsl(var(--card-foreground))' }}
              />
              <Legend />
              <Bar dataKey="value" name="Search Interest" radius={[8, 8, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>

          {/* Summary Stats */}
          <div className="grid grid-cols-3 gap-4 pt-4 border-t">
            <div className="text-center">
              <div className="text-2xl font-bold text-blue-600 dark:text-blue-400">{current_interest}</div>
              <div className="text-xs text-muted-foreground">Current Interest</div>
            </div>
            <div className="text-center">
              <div className="text-2xl font-bold text-gray-600 dark:text-gray-400">{avg_interest}</div>
              <div className="text-xs text-muted-foreground">7-Day Average</div>
            </div>
            <div className="text-center">
              <div className="text-2xl font-bold text-blue-500">{max_interest}</div>
              <div className="text-xs text-muted-foreground">Peak Interest</div>
            </div>
          </div>
        </div>
      </CardContent>
    </Card>
  );
}

// Note: Helper functions removed - now using centralized utilities from @/lib/utils/colors
