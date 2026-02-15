'use client';

import { LineChart, Line, ResponsiveContainer } from 'recharts';
import { TrendingUp, TrendingDown } from 'lucide-react';

interface TrendSparklineProps {
  /** Array of numeric values representing the trend over time */
  data: number[];
  /** Optional growth percentage string (e.g., "+150%") */
  growth?: string;
  /** Width in pixels (default: 60) */
  width?: number;
  /** Height in pixels (default: 20) */
  height?: number;
}

export function TrendSparkline({ data, growth, width = 60, height = 20 }: TrendSparklineProps) {
  if (!data || data.length < 2) return null;

  const chartData = data.map((value, index) => ({ index, value }));
  const isPositive = data[data.length - 1] >= data[0];
  const color = isPositive ? '#10B981' : '#EF4444';

  // Parse growth percentage
  const growthNum = growth ? parseFloat(growth.replace(/[^-\d.]/g, '')) : null;

  return (
    <div className="inline-flex items-center gap-1.5">
      <div style={{ width, height }}>
        <ResponsiveContainer width="100%" height="100%">
          <LineChart data={chartData}>
            <Line
              type="monotone"
              dataKey="value"
              stroke={color}
              strokeWidth={1.5}
              dot={false}
              isAnimationActive={false}
            />
          </LineChart>
        </ResponsiveContainer>
      </div>
      {growthNum !== null && !isNaN(growthNum) && (
        <span className={`inline-flex items-center text-xs font-medium ${growthNum >= 0 ? 'text-green-600' : 'text-red-500'}`}>
          {growthNum >= 0 ? <TrendingUp className="h-3 w-3 mr-0.5" /> : <TrendingDown className="h-3 w-3 mr-0.5" />}
          {growth}
        </span>
      )}
    </div>
  );
}
