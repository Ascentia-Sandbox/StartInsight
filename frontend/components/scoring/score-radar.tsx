'use client';

import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from '@/components/ui/tooltip';
import { Target, TrendingUp, Lightbulb, Clock, Megaphone, User, Wrench, DollarSign, Info } from 'lucide-react';

// 8-dimension scoring system — StartInsight's comprehensive analysis
export const SCORING_DIMENSIONS = {
  opportunity: {
    name: 'Opportunity',
    description: 'Size of the market opportunity and potential for disruption',
    icon: Target,
    color: 'bg-blue-500',
  },
  problem: {
    name: 'Problem Clarity',
    description: 'How well-defined and validated the problem is',
    icon: Lightbulb,
    color: 'bg-yellow-500',
  },
  feasibility: {
    name: 'Feasibility',
    description: 'Technical and business feasibility of the solution',
    icon: Wrench,
    color: 'bg-green-500',
  },
  why_now: {
    name: 'Why Now',
    description: 'Timing factors that make this the right moment',
    icon: Clock,
    color: 'bg-purple-500',
  },
  // StartInsight exclusive dimensions
  go_to_market: {
    name: 'Go-to-Market',
    description: 'Clarity and viability of distribution strategy',
    icon: Megaphone,
    color: 'bg-orange-500',
  },
  founder_fit: {
    name: 'Founder Fit',
    description: 'How well this matches typical founder strengths',
    icon: User,
    color: 'bg-pink-500',
  },
  execution_difficulty: {
    name: 'Execution',
    description: 'Complexity and resource requirements to build',
    icon: TrendingUp,
    color: 'bg-red-500',
  },
  revenue_potential: {
    name: 'Revenue',
    description: 'Near-term monetization potential',
    icon: DollarSign,
    color: 'bg-emerald-500',
  },
} as const;

export type ScoringDimensionId = keyof typeof SCORING_DIMENSIONS;

interface ScoreData {
  opportunity?: number;
  problem?: number;
  feasibility?: number;
  why_now?: number;
  go_to_market?: number;
  founder_fit?: number;
  execution_difficulty?: number;
  revenue_potential?: number;
}

interface ScoreRadarProps {
  scores: ScoreData;
  showLabels?: boolean;
  size?: 'sm' | 'md' | 'lg';
}

function ScoreBar({
  dimensionId,
  score,
  size = 'md'
}: {
  dimensionId: ScoringDimensionId;
  score: number;
  size?: 'sm' | 'md' | 'lg';
}) {
  const dimension = SCORING_DIMENSIONS[dimensionId];
  const Icon = dimension.icon;

  const sizeConfig = {
    sm: { bar: 'h-1.5', icon: 'h-3 w-3', text: 'text-xs' },
    md: { bar: 'h-2', icon: 'h-4 w-4', text: 'text-sm' },
    lg: { bar: 'h-3', icon: 'h-5 w-5', text: 'text-base' },
  };

  const { bar, icon, text } = sizeConfig[size];
  const percentage = Math.min(100, Math.max(0, score * 10));

  const getScoreColor = (score: number) => {
    if (score >= 8) return 'bg-green-500';
    if (score >= 6) return 'bg-blue-500';
    if (score >= 4) return 'bg-yellow-500';
    return 'bg-red-500';
  };

  return (
    <TooltipProvider>
      <Tooltip>
        <TooltipTrigger asChild>
          <div className="space-y-1">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-1.5">
                <Icon className={`${icon} text-muted-foreground`} />
                <span className={`${text} font-medium truncate`}>{dimension.name}</span>
              </div>
              <span className={`${text} font-bold`}>{score.toFixed(1)}</span>
            </div>
            <div className={`w-full bg-muted rounded-full ${bar}`}>
              <div
                className={`${bar} rounded-full transition-all duration-500 ${getScoreColor(score)}`}
                style={{ width: `${percentage}%` }}
              />
            </div>
          </div>
        </TooltipTrigger>
        <TooltipContent>
          <p className="font-medium">{dimension.name}</p>
          <p className="text-xs text-muted-foreground max-w-[200px]">
            {dimension.description}
          </p>
        </TooltipContent>
      </Tooltip>
    </TooltipProvider>
  );
}

export function ScoreRadar({ scores, showLabels = true, size = 'md' }: ScoreRadarProps) {
  // Calculate overall score
  const scoreValues = Object.values(scores).filter((s): s is number => s !== undefined);
  const overallScore = scoreValues.length > 0
    ? scoreValues.reduce((a, b) => a + b, 0) / scoreValues.length
    : 0;

  const getOverallRating = (score: number) => {
    if (score >= 8) return { label: 'Excellent', color: 'bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-300' };
    if (score >= 6) return { label: 'Good', color: 'bg-blue-100 text-blue-800 dark:bg-blue-900 dark:text-blue-300' };
    if (score >= 4) return { label: 'Fair', color: 'bg-yellow-100 text-yellow-800 dark:bg-yellow-900 dark:text-yellow-300' };
    return { label: 'Weak', color: 'bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-300' };
  };

  const rating = getOverallRating(overallScore);

  return (
    <Card>
      <CardHeader className="pb-3">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <Target className="h-5 w-5 text-muted-foreground" />
            <CardTitle className="text-lg">8-Dimension Score</CardTitle>
            <TooltipProvider>
              <Tooltip>
                <TooltipTrigger>
                  <Info className="h-4 w-4 text-muted-foreground" />
                </TooltipTrigger>
                <TooltipContent className="max-w-[280px]">
                  <p className="font-medium">StartInsight Advantage</p>
                  <p className="text-xs text-muted-foreground">
                    Our 8-dimension scoring provides 2x more comprehensive market analysis
                    than competitors who only use 4 dimensions (Opportunity, Problem, Feasibility, Why Now).
                  </p>
                </TooltipContent>
              </Tooltip>
            </TooltipProvider>
          </div>
          <div className="flex items-center gap-2">
            <span className="text-2xl font-bold">{overallScore.toFixed(1)}</span>
            <Badge className={rating.color}>{rating.label}</Badge>
          </div>
        </div>
      </CardHeader>
      <CardContent>
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
          {/* Core dimensions (4) */}
          <div className="space-y-3">
            <p className="text-xs text-muted-foreground uppercase tracking-wider">Core Dimensions</p>
            {(['opportunity', 'problem', 'feasibility', 'why_now'] as ScoringDimensionId[]).map((dim) => (
              scores[dim] !== undefined && (
                <ScoreBar key={dim} dimensionId={dim} score={scores[dim]!} size={size} />
              )
            ))}
          </div>

          {/* StartInsight-exclusive dimensions (4) */}
          <div className="space-y-3">
            <p className="text-xs text-muted-foreground uppercase tracking-wider">
              StartInsight Exclusive
              <Badge variant="outline" className="ml-2 text-[10px] py-0">+4 dimensions</Badge>
            </p>
            {(['go_to_market', 'founder_fit', 'execution_difficulty', 'revenue_potential'] as ScoringDimensionId[]).map((dim) => (
              scores[dim] !== undefined && (
                <ScoreBar key={dim} dimensionId={dim} score={scores[dim]!} size={size} />
              )
            ))}
          </div>
        </div>
      </CardContent>
    </Card>
  );
}

// Simple inline score display for cards
interface InlineScoreProps {
  scores: ScoreData;
}

export function InlineScore({ scores }: InlineScoreProps) {
  const scoreValues = Object.values(scores).filter((s): s is number => s !== undefined);
  const overallScore = scoreValues.length > 0
    ? scoreValues.reduce((a, b) => a + b, 0) / scoreValues.length
    : 0;

  const getColor = (score: number) => {
    if (score >= 8) return 'text-green-600 dark:text-green-400';
    if (score >= 6) return 'text-blue-600 dark:text-blue-400';
    if (score >= 4) return 'text-yellow-600 dark:text-yellow-400';
    return 'text-red-600 dark:text-red-400';
  };

  return (
    <div className="flex items-center gap-1">
      <Target className="h-4 w-4 text-muted-foreground" />
      <span className={`font-bold ${getColor(overallScore)}`}>
        {overallScore.toFixed(1)}/10
      </span>
      <span className="text-xs text-muted-foreground">
        ({scoreValues.length} dimensions)
      </span>
    </div>
  );
}
