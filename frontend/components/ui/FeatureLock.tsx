import Link from 'next/link';
import { Button } from '@/components/ui/button';

const TIER_ORDER: Record<string, number> = {
  free: 0,
  starter: 1, // Backward compat — remove after 2026-04-23
  pro: 1,
  api: 2,
};

const TIER_LABELS: Record<string, string> = {
  pro: 'Pro',
  api: 'API',
};

interface FeatureLockProps {
  /** The minimum tier required to access this feature. */
  requiredTier: string;
  /** The current user's subscription tier. */
  currentTier: string;
  /** Human-readable name of the locked feature, shown in the overlay. */
  featureName?: string;
  /** Content to render when unlocked. */
  children: React.ReactNode;
}

/**
 * Wraps content with a locked overlay when the user's tier is insufficient.
 *
 * Usage:
 *   <FeatureLock requiredTier="pro" currentTier={tier} featureName="API Access">
 *     <APIKeysContent />
 *   </FeatureLock>
 */
export function FeatureLock({ requiredTier, currentTier, featureName, children }: FeatureLockProps) {
  const currentOrder = TIER_ORDER[currentTier] ?? 0;
  const requiredOrder = TIER_ORDER[requiredTier] ?? 0;
  const isLocked = currentOrder < requiredOrder;

  if (!isLocked) {
    return <>{children}</>;
  }

  const tierLabel = TIER_LABELS[requiredTier] ?? requiredTier;

  return (
    <div className="relative overflow-hidden">
      {/* Content — no blur, editorial fade replaces hard obscure */}
      <div className="pointer-events-none select-none" aria-hidden>
        {children}
      </div>

      {/* Gradient fade starting at 60% */}
      <div
        className="absolute inset-0 pointer-events-none"
        style={{ background: 'linear-gradient(to bottom, transparent 0%, transparent 55%, hsl(var(--background)) 88%)' }}
      />

      {/* CTA anchored at the bottom of the fade */}
      <div className="absolute bottom-0 left-0 right-0 z-10 flex flex-col items-center gap-3 pb-8 pt-12">
        <p className="text-sm font-medium text-foreground/80">
          {featureName ? `${featureName} requires the ${tierLabel} plan` : `${tierLabel} plan required`}
        </p>
        <Button asChild size="sm">
          <Link href="/billing">Upgrade to {tierLabel}</Link>
        </Button>
      </div>
    </div>
  );
}
