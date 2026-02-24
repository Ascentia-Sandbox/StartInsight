import { cn } from '@/lib/utils';

const TIER_STYLES: Record<string, string> = {
  free: 'bg-muted text-muted-foreground',
  starter: 'bg-blue-100 text-blue-700 dark:bg-blue-900/30 dark:text-blue-300',
  pro: 'bg-purple-100 text-purple-700 dark:bg-purple-900/30 dark:text-purple-300',
  enterprise: 'bg-amber-100 text-amber-700 dark:bg-amber-900/30 dark:text-amber-300',
};

interface TierBadgeProps {
  tier: string;
  className?: string;
}

/**
 * Colored pill badge showing the user's subscription tier.
 * Used in the header user menu next to the avatar.
 */
export function TierBadge({ tier, className }: TierBadgeProps) {
  const style = TIER_STYLES[tier] ?? TIER_STYLES.free;

  return (
    <span
      className={cn(
        'inline-flex items-center rounded-full px-1.5 py-0.5 text-xs font-medium uppercase tracking-wide',
        style,
        className,
      )}
    >
      {tier}
    </span>
  );
}
