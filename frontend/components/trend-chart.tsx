'use client';

import { AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';

interface TrendChartProps {
  data?: any;
  source?: string;
}

export function TrendChart({ data, source }: TrendChartProps) {
  // Generate synthetic 30-day trend data (IdeaBrowser style)
  const today = new Date();
  const chartData = Array.from({ length: 30 }, (_, i) => {
    const date = new Date(today);
    date.setDate(date.getDate() - (29 - i));
    // Create realistic growth curve: low start, exponential growth
    const baseValue = 20 + Math.random() * 10;
    const growthFactor = Math.pow(1.15, i / 3); // 15% growth every 3 days
    const noise = (Math.random() - 0.5) * 10;
    return {
      date: date.toISOString().split('T')[0],
      value: Math.max(0, Math.round(baseValue * growthFactor + noise)),
    };
  });

  return (
    <div role="region" aria-label="Search interest trend chart">
      {/* IdeaBrowser-style clean chart */}
      <ResponsiveContainer width="100%" height={400}>
        <AreaChart
          data={chartData}
          margin={{ top: 10, right: 10, left: 0, bottom: 0 }}
        >
          <defs>
            {/* IdeaBrowser-style blue gradient */}
            <linearGradient id="ideaBrowserGradient" x1="0" y1="0" x2="0" y2="1">
              <stop offset="5%" stopColor="#3B82F6" stopOpacity={0.4}/>
              <stop offset="95%" stopColor="#3B82F6" stopOpacity={0.05}/>
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
            itemStyle={{ color: '#3B82F6', fontSize: '14px' }}
            formatter={(value: any) => [`${value}`, 'Search Volume']}
          />
          {/* Historical Data Area with smooth blue gradient */}
          <Area
            type="monotone"
            dataKey="value"
            stroke="#3B82F6"
            strokeWidth={3}
            fill="url(#ideaBrowserGradient)"
            dot={false}
            activeDot={{ r: 6, stroke: '#3B82F6', strokeWidth: 2, fill: '#FFFFFF' }}
          />
        </AreaChart>
      </ResponsiveContainer>
    </div>
  );
}
