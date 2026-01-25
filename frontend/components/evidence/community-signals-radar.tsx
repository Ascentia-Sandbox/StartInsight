'use client';

import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Radar, RadarChart, PolarGrid, PolarAngleAxis, PolarRadiusAxis, ResponsiveContainer, Tooltip, Legend } from 'recharts';

interface CommunitySignal {
  platform: 'Reddit' | 'Facebook' | 'YouTube' | 'Other';
  score: number; // 1-10
  members: number;
  engagement_rate: number;
  top_url?: string | null;
}

interface CommunitySignalsRadarProps {
  signals: CommunitySignal[];
}

export function CommunitySignalsRadar({ signals }: CommunitySignalsRadarProps) {
  // Transform data for radar chart
  const chartData = signals.map(s => ({
    platform: s.platform,
    score: s.score,
    members: Math.round(s.members / 1000), // Convert to K
    engagementRate: Math.round(s.engagement_rate * 100), // Convert to percentage
  }));

  // Calculate total engagement metrics
  const totalMembers = signals.reduce((sum, s) => sum + s.members, 0);
  const avgScore = signals.length > 0
    ? (signals.reduce((sum, s) => sum + s.score, 0) / signals.length).toFixed(1)
    : '0';

  return (
    <Card>
      <CardHeader>
        <CardTitle>Community Engagement Strength</CardTitle>
        <CardDescription>
          {signals.length} platform{signals.length !== 1 ? 's' : ''} analyzed •{' '}
          {(totalMembers / 1000000).toFixed(1)}M total members •{' '}
          {avgScore}/10 avg score
        </CardDescription>
      </CardHeader>
      <CardContent>
        <ResponsiveContainer width="100%" height={320}>
          <RadarChart data={chartData}>
            <PolarGrid />
            <PolarAngleAxis dataKey="platform" />
            <PolarRadiusAxis angle={90} domain={[0, 10]} />
            <Radar
              name="Engagement Score"
              dataKey="score"
              stroke="#6366f1"
              fill="#6366f1"
              fillOpacity={0.6}
            />
            <Tooltip
              content={({ active, payload }) => {
                if (active && payload && payload.length) {
                  const data = payload[0].payload;
                  return (
                    <div className="rounded-lg border bg-background p-3 shadow-md">
                      <div className="font-semibold">{data.platform}</div>
                      <div className="mt-1 space-y-1 text-sm">
                        <div className="flex justify-between gap-4">
                          <span className="text-muted-foreground">Score:</span>
                          <span className="font-medium">{data.score}/10</span>
                        </div>
                        <div className="flex justify-between gap-4">
                          <span className="text-muted-foreground">Members:</span>
                          <span className="font-medium">{data.members}K</span>
                        </div>
                        <div className="flex justify-between gap-4">
                          <span className="text-muted-foreground">Engagement:</span>
                          <span className="font-medium">{data.engagementRate}%</span>
                        </div>
                      </div>
                    </div>
                  );
                }
                return null;
              }}
            />
            <Legend />
          </RadarChart>
        </ResponsiveContainer>

        {signals.length === 0 && (
          <div className="flex h-[320px] items-center justify-center text-sm text-muted-foreground">
            No community signals available
          </div>
        )}
      </CardContent>
    </Card>
  );
}
