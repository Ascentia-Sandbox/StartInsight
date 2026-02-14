'use client';

import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import {
  ScatterChart,
  Scatter,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  Cell,
  Label,
} from 'recharts';
import { Target } from 'lucide-react';

interface Competitor {
  name: string;
  positioning_x: number;
  positioning_y: number;
  is_current?: boolean;  // highlight the current insight
  market_position?: string;
}

interface CompetitiveMapProps {
  competitors: Competitor[];
  insightName?: string;
  title?: string;
  description?: string;
}

export function CompetitiveMap({
  competitors,
  insightName,
  title = 'Competitive Landscape',
  description = 'Market Maturity vs Innovation positioning matrix',
}: CompetitiveMapProps) {
  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <Target className="h-5 w-5" />
          {title}
        </CardTitle>
        <CardDescription>{description}</CardDescription>
      </CardHeader>
      <CardContent>
        <ResponsiveContainer width="100%" height={400}>
          <ScatterChart margin={{ top: 20, right: 20, bottom: 40, left: 40 }}>
            <CartesianGrid strokeDasharray="3 3" stroke="var(--border)" />
            <XAxis type="number" dataKey="positioning_x" domain={[0, 10]} name="Market Maturity">
              <Label value="Market Maturity &#8594;" position="bottom" offset={20} style={{ fill: 'var(--muted-foreground)' }} />
            </XAxis>
            <YAxis type="number" dataKey="positioning_y" domain={[0, 10]} name="Innovation Score">
              <Label value="Innovation Score &#8594;" angle={-90} position="left" offset={20} style={{ fill: 'var(--muted-foreground)' }} />
            </YAxis>
            <Tooltip
              content={({ payload }) => {
                if (!payload?.[0]) return null;
                const data = payload[0].payload as Competitor;
                return (
                  <div className="bg-background border rounded-lg p-3 shadow-lg">
                    <p className="font-medium">{data.name}</p>
                    {data.market_position && (
                      <p className="text-xs text-muted-foreground capitalize mb-1">{data.market_position}</p>
                    )}
                    <p className="text-xs text-muted-foreground">
                      Maturity: {data.positioning_x.toFixed(1)} | Innovation: {data.positioning_y.toFixed(1)}
                    </p>
                    {data.is_current && (
                      <Badge className="mt-1 text-[10px] bg-[#0D7377]">Your Idea</Badge>
                    )}
                  </div>
                );
              }}
            />
            <Scatter data={competitors} name="Competitors">
              {competitors.map((comp, i) => (
                <Cell
                  key={i}
                  fill={comp.is_current ? '#0D7377' : '#94A3B8'}
                  stroke={comp.is_current ? '#0D7377' : '#94A3B8'}
                  r={comp.is_current ? 8 : 5}
                />
              ))}
            </Scatter>
          </ScatterChart>
        </ResponsiveContainer>

        {/* Quadrant legend */}
        <div className="grid grid-cols-2 gap-2 mt-4 text-xs text-muted-foreground">
          <div className="text-right">Emerging Niche</div>
          <div>Innovative Leader</div>
          <div className="text-right">Declining</div>
          <div>Mature Market</div>
        </div>

        {/* Legend */}
        <div className="flex flex-wrap gap-3 mt-4 justify-center">
          <Badge variant="outline" className="text-xs">
            <span className="w-2 h-2 rounded-full bg-slate-400 mr-1.5 inline-block" />
            Competitors
          </Badge>
          {competitors.some((c) => c.is_current) && (
            <Badge variant="outline" className="text-xs">
              <span className="w-2 h-2 rounded-full mr-1.5 inline-block" style={{ backgroundColor: '#0D7377' }} />
              {insightName || 'Your Idea'}
            </Badge>
          )}
        </div>
      </CardContent>
    </Card>
  );
}
