'use client';

import { Badge } from '@/components/ui/badge';
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from '@/components/ui/tooltip';

// Platform configuration with icons and colors
const PLATFORM_CONFIG: Record<string, { icon: string; color: string; darkColor: string; label: string }> = {
  reddit: {
    icon: 'R',
    color: 'bg-orange-100 text-orange-800 border-orange-200',
    darkColor: 'dark:bg-orange-900 dark:text-orange-300 dark:border-orange-700',
    label: 'Reddit',
  },
  facebook: {
    icon: 'f',
    color: 'bg-blue-100 text-blue-800 border-blue-200',
    darkColor: 'dark:bg-blue-900 dark:text-blue-300 dark:border-blue-700',
    label: 'Facebook',
  },
  youtube: {
    icon: 'Y',
    color: 'bg-red-100 text-red-800 border-red-200',
    darkColor: 'dark:bg-red-900 dark:text-red-300 dark:border-red-700',
    label: 'YouTube',
  },
  twitter: {
    icon: 'X',
    color: 'bg-gray-100 text-gray-800 border-gray-200',
    darkColor: 'dark:bg-gray-800 dark:text-gray-300 dark:border-gray-600',
    label: 'Twitter/X',
  },
  hackernews: {
    icon: 'HN',
    color: 'bg-orange-100 text-orange-700 border-orange-200',
    darkColor: 'dark:bg-orange-900 dark:text-orange-400 dark:border-orange-700',
    label: 'Hacker News',
  },
  producthunt: {
    icon: 'PH',
    color: 'bg-amber-100 text-amber-800 border-amber-200',
    darkColor: 'dark:bg-amber-900 dark:text-amber-300 dark:border-amber-700',
    label: 'Product Hunt',
  },
  google_trends: {
    icon: 'GT',
    color: 'bg-green-100 text-green-800 border-green-200',
    darkColor: 'dark:bg-green-900 dark:text-green-300 dark:border-green-700',
    label: 'Google Trends',
  },
};

interface CommunitySignal {
  score?: number;
  subreddits?: string[];
  groups?: number;
  channels?: number;
  members?: number;
  views?: string;
  top_post_url?: string;
  engagement?: number;
}

interface CommunitySignalsBadgeProps {
  platform: string;
  signal: CommunitySignal;
  showTooltip?: boolean;
}

export function CommunitySignalsBadge({ platform, signal, showTooltip = true }: CommunitySignalsBadgeProps) {
  const config = PLATFORM_CONFIG[platform.toLowerCase()] || {
    icon: platform.charAt(0).toUpperCase(),
    color: 'bg-gray-100 text-gray-800 border-gray-200',
    darkColor: 'dark:bg-gray-800 dark:text-gray-300 dark:border-gray-600',
    label: platform,
  };

  const score = signal.score ?? 0;
  const scoreColor = score >= 7 ? 'text-green-600 dark:text-green-400' :
                     score >= 4 ? 'text-yellow-600 dark:text-yellow-400' :
                     'text-red-600 dark:text-red-400';

  // Build tooltip content based on available data
  const tooltipContent = () => {
    const details: string[] = [];
    if (signal.members) details.push(`${signal.members.toLocaleString()} members`);
    if (signal.subreddits?.length) details.push(`${signal.subreddits.length} subreddits`);
    if (signal.groups) details.push(`${signal.groups} groups`);
    if (signal.channels) details.push(`${signal.channels} channels`);
    if (signal.views) details.push(`${signal.views} views`);
    if (signal.engagement) details.push(`${signal.engagement}% engagement`);
    return details.length > 0 ? details.join(' | ') : `Score: ${score}/10`;
  };

  const badge = (
    <Badge
      variant="outline"
      className={`${config.color} ${config.darkColor} font-medium flex items-center gap-1.5 px-2 py-0.5`}
    >
      <span className="font-bold text-xs">{config.icon}</span>
      <span className={`font-semibold ${scoreColor}`}>{score}/10</span>
    </Badge>
  );

  if (!showTooltip) return badge;

  return (
    <TooltipProvider>
      <Tooltip>
        <TooltipTrigger asChild>
          {badge}
        </TooltipTrigger>
        <TooltipContent>
          <div className="text-sm">
            <p className="font-semibold">{config.label}</p>
            <p className="text-muted-foreground">{tooltipContent()}</p>
          </div>
        </TooltipContent>
      </Tooltip>
    </TooltipProvider>
  );
}

interface CommunitySignalsRowProps {
  signals: Record<string, CommunitySignal>;
}

export function CommunitySignalsRow({ signals }: CommunitySignalsRowProps) {
  if (!signals || Object.keys(signals).length === 0) return null;

  return (
    <div className="flex flex-wrap gap-2">
      {Object.entries(signals).map(([platform, signal]) => (
        <CommunitySignalsBadge key={platform} platform={platform} signal={signal} />
      ))}
    </div>
  );
}
