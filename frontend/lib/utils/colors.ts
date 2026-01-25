/**
 * Color mapping utilities - Code simplification Phase 3.
 *
 * Centralizes color mapping logic currently duplicated in 3+ files.
 * Replaces 3 separate getTrendBadgeStyle(), getTrendIcon(), and color mapping functions
 * with a single TREND_CONFIG object.
 */

import { TrendingUp, TrendingDown, Minus } from 'lucide-react';

export type TrendDirection = 'rising' | 'falling' | 'stable' | 'unknown';

interface TrendConfig {
  color: string;
  bgColor: string;
  icon: typeof TrendingUp;
  label: string;
  badgeClass: string;
}

/**
 * Centralized trend configuration object.
 *
 * Single source of truth for all trend-related styling and icons.
 */
export const TREND_CONFIG: Record<TrendDirection, TrendConfig> = {
  rising: {
    color: 'text-green-600',
    bgColor: 'bg-green-100',
    icon: TrendingUp,
    label: 'Rising',
    badgeClass: 'bg-green-100 text-green-800',
  },
  falling: {
    color: 'text-red-600',
    bgColor: 'bg-red-100',
    icon: TrendingDown,
    label: 'Falling',
    badgeClass: 'bg-red-100 text-red-800',
  },
  stable: {
    color: 'text-gray-600',
    bgColor: 'bg-gray-100',
    icon: Minus,
    label: 'Stable',
    badgeClass: 'bg-gray-100 text-gray-800',
  },
  unknown: {
    color: 'text-gray-400',
    bgColor: 'bg-gray-50',
    icon: Minus,
    label: 'Unknown',
    badgeClass: 'bg-gray-50 text-gray-600',
  },
};

/**
 * Get trend color class for text or background.
 */
export function getTrendColor(direction: TrendDirection, type: 'text' | 'bg' = 'text'): string {
  const config = TREND_CONFIG[direction] || TREND_CONFIG.unknown;
  return type === 'text' ? config.color : config.bgColor;
}

/**
 * Get trend icon component.
 */
export function getTrendIcon(direction: TrendDirection) {
  const config = TREND_CONFIG[direction] || TREND_CONFIG.unknown;
  return config.icon;
}

/**
 * Get trend badge classes.
 */
export function getTrendBadgeClass(direction: TrendDirection): string {
  const config = TREND_CONFIG[direction] || TREND_CONFIG.unknown;
  return config.badgeClass;
}

/**
 * Get market size badge color.
 *
 * Replaces duplicate market size color logic.
 */
export function getMarketSizeBadge(marketSize: string): string {
  const size = marketSize.toLowerCase();

  if (size.includes('billion') || size.includes('large')) {
    return 'bg-purple-100 text-purple-800';
  }
  if (size.includes('million') || size.includes('medium')) {
    return 'bg-blue-100 text-blue-800';
  }
  return 'bg-gray-100 text-gray-800';
}
