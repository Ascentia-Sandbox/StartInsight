'use client';

import { TrendingUp, TrendingDown, Minus, Activity } from 'lucide-react';
import { Badge } from '@/components/ui/badge';

interface TrendIndicatorProps {
  growth: string | number;
  volume?: string | number;
  size?: 'sm' | 'md' | 'lg';
  showVolume?: boolean;
}

export function TrendIndicator({ growth, volume, size = 'md', showVolume = false }: TrendIndicatorProps) {
  // Parse growth value
  const growthStr = String(growth);
  const growthNum = parseFloat(growthStr.replace(/[+%,]/g, ''));
  const isPositive = growthNum > 0;
  const isNegative = growthNum < 0;
  const isStable = growthNum === 0;

  // Size configurations
  const sizeConfig = {
    sm: { icon: 'h-3 w-3', text: 'text-xs', badge: 'px-1.5 py-0.5' },
    md: { icon: 'h-4 w-4', text: 'text-sm', badge: 'px-2 py-1' },
    lg: { icon: 'h-5 w-5', text: 'text-base', badge: 'px-3 py-1.5' },
  };

  const { icon: iconSize, text: textSize, badge: badgeSize } = sizeConfig[size];

  // Color and icon based on trend
  const getConfig = () => {
    if (isPositive) {
      return {
        color: 'bg-green-100 text-green-700 dark:bg-green-900 dark:text-green-300',
        Icon: TrendingUp,
        prefix: '+',
      };
    }
    if (isNegative) {
      return {
        color: 'bg-red-100 text-red-700 dark:bg-red-900 dark:text-red-300',
        Icon: TrendingDown,
        prefix: '',
      };
    }
    return {
      color: 'bg-gray-100 text-gray-600 dark:bg-gray-800 dark:text-gray-400',
      Icon: Minus,
      prefix: '',
    };
  };

  const { color, Icon, prefix } = getConfig();

  // Format the growth display
  const formatGrowth = () => {
    if (growthStr.includes('%')) return growthStr;
    return `${prefix}${Math.abs(growthNum).toLocaleString()}%`;
  };

  return (
    <div className="inline-flex items-center gap-2">
      <Badge variant="outline" className={`${color} ${badgeSize} font-medium flex items-center gap-1`}>
        <Icon className={iconSize} />
        <span className={textSize}>{formatGrowth()}</span>
      </Badge>
      {showVolume && volume && (
        <span className={`${textSize} text-muted-foreground`}>
          Volume: {typeof volume === 'number' ? volume.toLocaleString() : volume}
        </span>
      )}
    </div>
  );
}

interface TrendStatsProps {
  currentInterest?: number;
  avgInterest?: number;
  peakInterest?: number;
  growth?: string | number;
}

export function TrendStats({ currentInterest, avgInterest, peakInterest, growth }: TrendStatsProps) {
  return (
    <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
      {currentInterest !== undefined && (
        <div className="text-center">
          <div className="text-xl font-bold text-blue-600 dark:text-blue-400">
            {currentInterest}
          </div>
          <div className="text-xs text-muted-foreground">Current</div>
        </div>
      )}
      {avgInterest !== undefined && (
        <div className="text-center">
          <div className="text-xl font-bold text-gray-600 dark:text-gray-400">
            {avgInterest}
          </div>
          <div className="text-xs text-muted-foreground">Average</div>
        </div>
      )}
      {peakInterest !== undefined && (
        <div className="text-center">
          <div className="text-xl font-bold text-purple-600 dark:text-purple-400">
            {peakInterest}
          </div>
          <div className="text-xs text-muted-foreground">Peak</div>
        </div>
      )}
      {growth !== undefined && (
        <div className="text-center">
          <TrendIndicator growth={growth} size="md" />
          <div className="text-xs text-muted-foreground mt-1">Growth</div>
        </div>
      )}
    </div>
  );
}
