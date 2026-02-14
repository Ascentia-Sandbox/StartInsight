'use client';

import { AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';

interface TrendDataPoint {
  date: string;
  value: number;
}

interface TrendChartProps {
  data?: TrendDataPoint[];
  source?: string;
}

export function TrendChart({ data, source }: TrendChartProps) {
  // If no data provided, show placeholder
  if (!data || data.length === 0) {
    return (
      <div role="region" aria-label="Search interest trend chart">
        <div className="flex items-center justify-center h-[400px] text-muted-foreground text-sm">
          No trend data available
        </div>
      </div>
    );
  }

  return (
    <div role="region" aria-label="Search interest trend chart">
      {/* Search interest trend chart */}
      <ResponsiveContainer width="100%" height={400}>
        <AreaChart
          data={data}
          margin={{ top: 10, right: 10, left: 0, bottom: 0 }}
        >
          <defs>
            {/* Teal gradient fill */}
            <linearGradient id="trendGradient" x1="0" y1="0" x2="0" y2="1">
              <stop offset="5%" stopColor="#0D7377" stopOpacity={0.4}/>
              <stop offset="95%" stopColor="#0D7377" stopOpacity={0.05}/>
            </linearGradient>
          </defs>
          <CartesianGrid strokeDasharray="3 3" stroke="#E5E7EB" strokeOpacity={0.3} />
          <XAxis
            dataKey="date"
            tick={{ fill: '#6B7280', fontSize: 12 }}
            axisLine={{ stroke: '#E5E7EB' }}
            tickLine={false}
            tickFormatter={(value) => {
              // Format date to show only day for cleaner look
              const parts = value.split('-');
              return parts.length === 3 ? `${parts[1]}/${parts[2]}` : value;
            }}
          />
          <YAxis
            tick={{ fill: '#6B7280', fontSize: 12 }}
            axisLine={{ stroke: '#E5E7EB' }}
            tickLine={false}
            width={40}
          />
          <Tooltip
            contentStyle={{
              backgroundColor: '#FFFFFF',
              border: '1px solid #E5E7EB',
              borderRadius: '8px',
              padding: '12px',
              boxShadow: '0 4px 6px -1px rgba(0, 0, 0, 0.1)',
            }}
            labelStyle={{ color: '#1F2937', fontWeight: 600, marginBottom: '4px' }}
            itemStyle={{ color: '#0D7377', fontSize: '14px' }}
            formatter={(value: any) => [`${value}`, 'Search Volume']}
          />
          {/* Historical Data Area with smooth teal gradient */}
          <Area
            type="monotone"
            dataKey="value"
            stroke="#0D7377"
            strokeWidth={3}
            fill="url(#trendGradient)"
            dot={false}
            activeDot={{ r: 6, stroke: '#0D7377', strokeWidth: 2, fill: '#FFFFFF' }}
          />
        </AreaChart>
      </ResponsiveContainer>
    </div>
  );
}
