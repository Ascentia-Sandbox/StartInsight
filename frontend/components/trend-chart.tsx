'use client';

import { useState } from 'react';
import { AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';
import { TrendingUp, TrendingDown, ChevronDown, Search } from 'lucide-react';

interface TrendDataPoint {
  date: string;
  value: number;
}

interface TrendKeyword {
  keyword: string;
  volume: string;
  growth: string;
}

interface TrendChartProps {
  data?: TrendDataPoint[];
  source?: string;
  keyword?: string;
  volume?: string;
  growth?: string;
  /** All trend keywords for the dropdown selector */
  allKeywords?: TrendKeyword[];
  /** Callback when keyword selection changes */
  onKeywordChange?: (keyword: TrendKeyword) => void;
}

export function TrendChart({ data, source, keyword, volume, growth, allKeywords, onKeywordChange }: TrendChartProps) {
  const [selectedIdx, setSelectedIdx] = useState(0);

  // Determine active keyword info (from dropdown or props)
  const activeKeyword = allKeywords?.[selectedIdx];
  const displayKeyword = activeKeyword?.keyword || keyword;
  const displayVolume = activeKeyword?.volume || volume;
  const displayGrowth = activeKeyword?.growth || growth;

  // Parse growth percentage for color coding
  const growthNum = displayGrowth ? parseFloat(displayGrowth.replace(/[^-\d.]/g, '')) : null;
  const isPositiveGrowth = growthNum !== null && growthNum > 0;

  // If no data provided, show placeholder
  if (!data || data.length === 0) {
    return (
      <div role="region" aria-label="Search interest trend chart">
        <div className="flex flex-col items-center justify-center h-[320px] gap-3">
          <Search className="h-8 w-8 text-muted-foreground/30" />
          <span className="text-muted-foreground text-sm">No trend data available</span>
        </div>
      </div>
    );
  }

  const handleKeywordChange = (idx: number) => {
    setSelectedIdx(idx);
    if (allKeywords?.[idx] && onKeywordChange) {
      onKeywordChange(allKeywords[idx]);
    }
  };

  return (
    <div role="region" aria-label="Search interest trend chart">
      {/* Header: Keyword selector + stats */}
      <div className="flex items-center justify-between mb-4 pb-3 border-b border-border/40">
        {/* Left: Keyword dropdown or static label */}
        <div className="flex items-center gap-2">
          <Search className="h-3.5 w-3.5 text-muted-foreground" />
          {allKeywords && allKeywords.length > 1 ? (
            <div className="relative">
              <select
                value={selectedIdx}
                onChange={(e) => handleKeywordChange(Number(e.target.value))}
                className="appearance-none bg-muted text-sm font-semibold pl-3 pr-7 py-1 rounded-lg border-none cursor-pointer focus:outline-none focus:ring-2 focus:ring-primary/30"
              >
                {allKeywords.map((kw, i) => (
                  <option key={i} value={i}>{kw.keyword}</option>
                ))}
              </select>
              <ChevronDown className="absolute right-2 top-1/2 -translate-y-1/2 h-3.5 w-3.5 text-muted-foreground pointer-events-none" />
            </div>
          ) : displayKeyword ? (
            <span className="text-sm font-semibold bg-muted px-2.5 py-0.5 rounded-md">{displayKeyword}</span>
          ) : null}
        </div>

        {/* Right: Volume + Growth stats */}
        <div className="flex items-center gap-5">
          {displayVolume && (
            <div className="text-right">
              <div className="text-[10px] text-muted-foreground uppercase tracking-wider font-medium">Volume</div>
              <div className="text-lg font-bold font-data leading-tight">{displayVolume}</div>
            </div>
          )}
          {displayGrowth && (
            <div className="text-right">
              <div className="text-[10px] text-muted-foreground uppercase tracking-wider font-medium">Growth</div>
              <div className={`text-lg font-bold font-data flex items-center justify-end gap-1 leading-tight ${
                isPositiveGrowth ? 'text-green-600' : 'text-red-500'
              }`}>
                {isPositiveGrowth ? (
                  <TrendingUp className="h-3.5 w-3.5" />
                ) : (
                  <TrendingDown className="h-3.5 w-3.5" />
                )}
                {displayGrowth}
              </div>
            </div>
          )}
        </div>
      </div>

      {/* Chart */}
      <ResponsiveContainer width="100%" height={300}>
        <AreaChart
          data={data}
          margin={{ top: 10, right: 10, left: 0, bottom: 0 }}
        >
          <defs>
            <linearGradient id="trendGradient" x1="0" y1="0" x2="0" y2="1">
              <stop offset="5%" stopColor="#0D7377" stopOpacity={0.35}/>
              <stop offset="95%" stopColor="#0D7377" stopOpacity={0.02}/>
            </linearGradient>
          </defs>
          <CartesianGrid strokeDasharray="3 3" stroke="currentColor" strokeOpacity={0.06} vertical={false} />
          <XAxis
            dataKey="date"
            tick={{ fill: '#9CA3AF', fontSize: 11 }}
            axisLine={false}
            tickLine={false}
            interval="preserveStartEnd"
            tickFormatter={(value) => {
              const parts = value.split('-');
              if (parts.length === 3) {
                const months = ['Jan','Feb','Mar','Apr','May','Jun','Jul','Aug','Sep','Oct','Nov','Dec'];
                const monthIdx = parseInt(parts[1], 10) - 1;
                return `${months[monthIdx] || parts[1]} ${parseInt(parts[2], 10)}`;
              }
              return value;
            }}
          />
          <YAxis
            tick={{ fill: '#9CA3AF', fontSize: 11 }}
            axisLine={false}
            tickLine={false}
            width={36}
          />
          <Tooltip
            contentStyle={{
              backgroundColor: 'hsl(var(--background))',
              border: '1px solid hsl(var(--border))',
              borderRadius: '10px',
              padding: '10px 14px',
              boxShadow: '0 8px 24px -4px rgba(0, 0, 0, 0.12)',
            }}
            labelStyle={{ color: 'hsl(var(--foreground))', fontWeight: 600, marginBottom: '4px', fontSize: '12px' }}
            itemStyle={{ color: '#0D7377', fontSize: '13px' }}
            formatter={(value: unknown) => [`${value}`, 'Search Interest']}
            labelFormatter={(label) => {
              const parts = String(label).split('-');
              if (parts.length === 3) {
                const months = ['Jan','Feb','Mar','Apr','May','Jun','Jul','Aug','Sep','Oct','Nov','Dec'];
                const monthIdx = parseInt(parts[1], 10) - 1;
                return `${months[monthIdx] || parts[1]} ${parseInt(parts[2], 10)}, ${parts[0]}`;
              }
              return label;
            }}
          />
          <Area
            type="monotone"
            dataKey="value"
            stroke="#0D7377"
            strokeWidth={2.5}
            fill="url(#trendGradient)"
            dot={false}
            activeDot={{ r: 5, stroke: '#0D7377', strokeWidth: 2, fill: '#FFFFFF' }}
          />
        </AreaChart>
      </ResponsiveContainer>
    </div>
  );
}
