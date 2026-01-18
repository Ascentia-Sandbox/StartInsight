'use client';

import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Legend } from 'recharts';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';

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

  // Prepare chart data
  const chartData = [
    {
      name: 'Current',
      value: current_interest || 0,
      fill: getTrendColor(trend_direction),
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
            <span className={`px-3 py-1 rounded-full text-sm font-medium ${getTrendBadgeStyle(trend_direction)}`}>
              {getTrendIcon(trend_direction)} {trend_direction?.toUpperCase() || 'UNKNOWN'}
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

// Helper functions
function getTrendColor(direction?: string): string {
  switch (direction?.toLowerCase()) {
    case 'rising':
      return '#22c55e'; // green
    case 'falling':
      return '#ef4444'; // red
    case 'stable':
      return '#f59e0b'; // amber
    default:
      return '#94a3b8'; // gray
  }
}

function getTrendBadgeStyle(direction?: string): string {
  switch (direction?.toLowerCase()) {
    case 'rising':
      return 'bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-300';
    case 'falling':
      return 'bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-300';
    case 'stable':
      return 'bg-amber-100 text-amber-800 dark:bg-amber-900 dark:text-amber-300';
    default:
      return 'bg-gray-100 text-gray-800 dark:bg-gray-900 dark:text-gray-300';
  }
}

function getTrendIcon(direction?: string): string {
  switch (direction?.toLowerCase()) {
    case 'rising':
      return '↗';
    case 'falling':
      return '↘';
    case 'stable':
      return '→';
    default:
      return '•';
  }
}
