'use client';

import { useState } from 'react';
import { motion } from 'framer-motion';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle } from '@/components/ui/dialog';
import { Radar, RadarChart, PolarGrid, PolarAngleAxis, PolarRadiusAxis, ResponsiveContainer, Tooltip, Legend } from 'recharts';
import { Info, TrendingUp, TrendingDown, Minus } from 'lucide-react';

interface ScoreRadarProps {
  scores: {
    opportunity?: number;
    problem?: number;
    feasibility?: number;
    why_now?: number;
    go_to_market?: number;
    founder_fit?: number;
    execution_difficulty?: number;
    revenue_potential?: number | string;
  };
  size?: 'sm' | 'md' | 'lg';
}

// Helper function to map score names to readable labels
function getDimensionLabel(dimension: string): string {
  const labels: Record<string, string> = {
    opportunity: 'Opportunity',
    problem: 'Problem',
    feasibility: 'Feasibility',
    why_now: 'Timing',
    go_to_market: 'GTM',
    founder_fit: 'Founder Fit',
    execution_difficulty: 'Execution',
    revenue_potential: 'Revenue',
  };
  return labels[dimension] || dimension;
}

// Get detailed explanation for each dimension
function getDimensionExplanation(dimension: string, score: number): {
  description: string;
  recommendations: string[];
  interpretation: string;
} {
  const explanations: Record<string, any> = {
    opportunity: {
      description: 'Measures the market opportunity size and potential for growth',
      recommendations: score < 5
        ? ['Research market size more thoroughly', 'Look for adjacent markets', 'Consider pivoting to larger opportunity']
        : score < 8
        ? ['Validate TAM with market research', 'Identify key growth drivers', 'Map out expansion opportunities']
        : ['Prioritize market entry strategy', 'Build moat early', 'Scale aggressively'],
      interpretation: score < 5 ? 'Limited opportunity' : score < 8 ? 'Moderate opportunity' : 'Massive opportunity'
    },
    problem: {
      description: 'Assesses how critical and painful the problem is for users',
      recommendations: score < 5
        ? ['Conduct more user interviews', 'Find a more painful problem', 'Reframe the problem statement']
        : score < 8
        ? ['Quantify the pain points', 'Build urgency messaging', 'Create problem-first positioning']
        : ['Lead with problem in marketing', 'Build category leadership', 'Create emotional connection'],
      interpretation: score < 5 ? 'Nice-to-have problem' : score < 8 ? 'Important problem' : 'Critical problem'
    },
    feasibility: {
      description: 'Evaluates technical and operational feasibility',
      recommendations: score < 5
        ? ['Simplify the solution', 'Find existing tools/frameworks', 'Consider partnering with technical co-founder']
        : score < 8
        ? ['Build MVP quickly', 'Leverage no-code/low-code tools', 'Focus on core features only']
        : ['Prototype rapidly', 'Launch early beta', 'Iterate based on user feedback'],
      interpretation: score < 5 ? 'High technical risk' : score < 8 ? 'Moderate complexity' : 'Highly feasible'
    },
    why_now: {
      description: 'Identifies market timing and current trends favoring this solution',
      recommendations: score < 5
        ? ['Wait for market conditions to improve', 'Create the timing catalyst yourself', 'Pivot to better-timed opportunity']
        : score < 8
        ? ['Highlight recent changes in market', 'Build narrative around timing', 'Ride current trends']
        : ['Move fast before window closes', 'Lead the trend', 'Establish first-mover advantage'],
      interpretation: score < 5 ? 'Wrong timing' : score < 8 ? 'Good timing' : 'Perfect timing window'
    },
    go_to_market: {
      description: 'Analyzes distribution channels and customer acquisition strategy',
      recommendations: score < 5
        ? ['Identify clearer distribution channels', 'Build partnerships early', 'Find viral hooks']
        : score < 8
        ? ['Test multiple channels', 'Focus on highest-ROI channel', 'Build repeatable playbook']
        : ['Scale proven channels', 'Automate acquisition', 'Expand to new channels'],
      interpretation: score < 5 ? 'Unclear GTM path' : score < 8 ? 'Solid GTM strategy' : 'Clear path to scale'
    },
    founder_fit: {
      description: 'Measures founder expertise and passion for this specific problem',
      recommendations: score < 5
        ? ['Build domain expertise first', 'Partner with domain expert', 'Consider different problem space']
        : score < 8
        ? ['Leverage your unique insights', 'Build credibility publicly', 'Network in the space']
        : ['Lead with founder story', 'Build thought leadership', 'Create unfair advantage'],
      interpretation: score < 5 ? 'Weak founder-market fit' : score < 8 ? 'Good fit' : 'Exceptional fit'
    },
    execution_difficulty: {
      description: 'Estimates complexity of execution and time to market (lower is better)',
      recommendations: score > 7
        ? ['Simplify the solution significantly', 'Build in phases', 'Find shortcuts and existing tools']
        : score > 4
        ? ['Plan for longer timeline', 'Hire key expertise early', 'Build strong team']
        : ['Move fast', 'Launch scrappy MVP', 'Iterate rapidly'],
      interpretation: score > 7 ? 'Very complex execution' : score > 4 ? 'Moderate complexity' : 'Simple execution'
    },
    revenue_potential: {
      description: 'Projects potential revenue and monetization opportunities',
      recommendations: score < 5
        ? ['Explore new revenue streams', 'Increase pricing tier', 'Add premium features']
        : score < 8
        ? ['Optimize pricing strategy', 'Upsell existing customers', 'Expand to enterprise']
        : ['Focus on retention and expansion', 'Build multi-product strategy', 'Pursue strategic partnerships'],
      interpretation: score < 5 ? 'Limited revenue potential' : score < 8 ? 'Solid revenue model' : 'Massive revenue opportunity'
    },
  };

  return explanations[dimension.toLowerCase().replace(/\s+/g, '_')] || {
    description: 'No detailed explanation available',
    recommendations: ['Analyze this dimension further'],
    interpretation: 'Score: ' + score + '/10'
  };
}

export function ScoreRadar({ scores, size = 'md' }: ScoreRadarProps) {
  const [selectedDimension, setSelectedDimension] = useState<{ name: string; score: number; key: string } | null>(null);
  const [isDialogOpen, setIsDialogOpen] = useState(false);

  // Normalize revenue_potential from string ("$"/"$$"/"$$$"/"$$$$") to numeric
  const revenueMap: Record<string, number> = { '$': 3, '$$': 5, '$$$': 7, '$$$$': 9 };
  const normalizedScores = { ...scores };
  if (typeof normalizedScores.revenue_potential === 'string') {
    normalizedScores.revenue_potential = revenueMap[normalizedScores.revenue_potential] ?? 5;
  }

  // Transform data for radar chart
  const chartData = Object.entries(normalizedScores)
    .filter(([_, value]) => value !== undefined)
    .map(([dimension, value]) => ({
      dimension: getDimensionLabel(dimension),
      dimensionKey: dimension,
      score: value as number,
    }));

  // Calculate average score
  const avgScore = chartData.length > 0
    ? (chartData.reduce((sum, item) => sum + item.score, 0) / chartData.length).toFixed(1)
    : '0';

  // Calculate total dimensions
  const totalDimensions = chartData.length;

  // Handle dimension click
  const handleDimensionClick = (data: any) => {
    if (data && data.payload) {
      setSelectedDimension({
        name: data.payload.dimension,
        score: data.payload.score,
        key: data.payload.dimensionKey
      });
      setIsDialogOpen(true);
    }
  };

  // Get color based on score
  const getScoreColor = (score: number): string => {
    if (score >= 8) return 'text-green-600 dark:text-green-400';
    if (score >= 5) return 'text-amber-600 dark:text-amber-400';
    return 'text-red-600 dark:text-red-400';
  };

  // Get trend icon based on score
  const getScoreIcon = (score: number) => {
    if (score >= 8) return <TrendingUp className="h-4 w-4 inline" />;
    if (score >= 5) return <Minus className="h-4 w-4 inline" />;
    return <TrendingDown className="h-4 w-4 inline" />;
  };

  return (
    <motion.div
      initial={{ opacity: 0, scale: 0.95 }}
      animate={{ opacity: 1, scale: 1 }}
      transition={{ duration: 0.5, delay: 0.2 }}
    >
      <Card>
        <CardHeader>
          <CardTitle id="score-radar-title">8-Dimension Scoring Analysis</CardTitle>
          <CardDescription id="score-radar-description">
            {totalDimensions} dimensions analyzed • Average: {avgScore}/10
          </CardDescription>
        </CardHeader>
        <CardContent role="region" aria-labelledby="score-radar-title" aria-describedby="score-radar-description">
        <ResponsiveContainer width="100%" height={320}>
          <RadarChart
            data={chartData}
            onClick={handleDimensionClick}
            aria-label="8-dimension startup quality radar chart. Click on any dimension to see detailed breakdown."
            role="img"
          >
            <PolarGrid />
            <PolarAngleAxis dataKey="dimension" tick={{ fontSize: 12 }} />
            <PolarRadiusAxis angle={90} domain={[0, 10]} />
            <Radar
              name="Score"
              dataKey="score"
              stroke="#6366f1"
              fill="#6366f1"
              fillOpacity={0.6}
              style={{ cursor: 'pointer' }}
              aria-label="Startup quality scores"
            />
            <Tooltip
              content={({ active, payload }) => {
                if (active && payload && payload.length) {
                  const data = payload[0].payload;
                  return (
                    <div className="rounded-lg border bg-background p-3 shadow-md">
                      <div className="font-semibold">{data.dimension}</div>
                      <div className="mt-1 space-y-1 text-sm">
                        <div className="flex justify-between gap-4">
                          <span className="text-muted-foreground">Score:</span>
                          <span className="font-medium">{data.score}/10</span>
                        </div>
                        <div className="text-xs text-muted-foreground mt-2">
                          💡 Click to see detailed breakdown
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

        {chartData.length === 0 && (
          <div className="flex h-32 items-center justify-center text-sm text-muted-foreground">
            No scoring data available
          </div>
        )}

        {/* Screen Reader Data Table */}
        <details className="sr-only">
          <summary>Scoring data table for screen readers</summary>
          <table>
            <caption>8-dimension startup quality scores</caption>
            <thead>
              <tr>
                <th>Dimension</th>
                <th>Score (out of 10)</th>
                <th>Interpretation</th>
              </tr>
            </thead>
            <tbody>
              {chartData.map((item: { dimension: string; score: number; dimensionKey: string }, index: number) => {
                const details = getDimensionExplanation(item.dimensionKey, item.score);
                return (
                  <tr key={index}>
                    <td>{item.dimension}</td>
                    <td>{item.score}</td>
                    <td>{details.interpretation}</td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </details>

        {/* Dimension Details Dialog */}
        <Dialog open={isDialogOpen} onOpenChange={setIsDialogOpen}>
          <DialogContent className="max-w-2xl">
            <DialogHeader>
              <DialogTitle className="flex items-center gap-2">
                <Info className="h-5 w-5" />
                {selectedDimension?.name} Score Analysis
              </DialogTitle>
              <DialogDescription>
                Detailed breakdown and recommendations for this dimension
              </DialogDescription>
            </DialogHeader>

            {selectedDimension && (() => {
              const details = getDimensionExplanation(selectedDimension.key, selectedDimension.score);
              return (
                <div className="space-y-6">
                  {/* Score Display */}
                  <div className="flex items-center justify-between p-4 bg-muted rounded-lg">
                    <div>
                      <div className="text-sm font-medium text-muted-foreground">Current Score</div>
                      <div className={`text-3xl font-bold ${getScoreColor(selectedDimension.score)}`}>
                        {getScoreIcon(selectedDimension.score)} {selectedDimension.score}/10
                      </div>
                    </div>
                    <div className="text-right">
                      <div className="text-sm font-medium text-muted-foreground">Interpretation</div>
                      <div className="text-lg font-semibold">{details.interpretation}</div>
                    </div>
                  </div>

                  {/* Description */}
                  <div>
                    <h4 className="font-semibold mb-2">What This Measures</h4>
                    <p className="text-sm text-muted-foreground">{details.description}</p>
                  </div>

                  {/* Recommendations */}
                  <div>
                    <h4 className="font-semibold mb-2">Recommendations</h4>
                    <ul className="space-y-2">
                      {details.recommendations.map((rec, idx) => (
                        <li key={idx} className="flex items-start gap-2 text-sm">
                          <span className="text-blue-600 dark:text-blue-400 mt-0.5">•</span>
                          <span>{rec}</span>
                        </li>
                      ))}
                    </ul>
                  </div>

                  {/* Comparison with Average */}
                  <div className="p-4 bg-muted rounded-lg">
                    <h4 className="font-semibold mb-2">Comparison with Average</h4>
                    <div className="flex items-center gap-4">
                      <div>
                        <div className="text-xs text-muted-foreground">This Dimension</div>
                        <div className="text-xl font-bold">{selectedDimension.score}</div>
                      </div>
                      <div className="text-2xl text-muted-foreground">vs</div>
                      <div>
                        <div className="text-xs text-muted-foreground">Overall Average</div>
                        <div className="text-xl font-bold">{avgScore}</div>
                      </div>
                      <div className="flex-1 text-right">
                        <div className="text-sm">
                          {selectedDimension.score > parseFloat(avgScore) ? (
                            <span className="text-green-600 dark:text-green-400 font-medium">
                              +{(selectedDimension.score - parseFloat(avgScore)).toFixed(1)} above average
                            </span>
                          ) : selectedDimension.score < parseFloat(avgScore) ? (
                            <span className="text-red-600 dark:text-red-400 font-medium">
                              {(selectedDimension.score - parseFloat(avgScore)).toFixed(1)} below average
                            </span>
                          ) : (
                            <span className="text-muted-foreground font-medium">At average</span>
                          )}
                        </div>
                      </div>
                    </div>
                  </div>
                </div>
              );
            })()}
          </DialogContent>
        </Dialog>
      </CardContent>
    </Card>
    </motion.div>
  );
}