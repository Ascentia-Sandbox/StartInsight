import Link from 'next/link';
import { Lock } from 'lucide-react';
import { Button } from '@/components/ui/button';

const TIER_ORDER: Record<string, number> = {
  free: 0,
  starter: 1,
  pro: 2,
  enterprise: 3,
};

const TIER_LABELS: Record<string, string> = {
  starter: 'Starter',
  pro: 'Pro',
  enterprise: 'Enterprise',
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
    <div className="relative">
      {/* Blurred content */}
      <div className="pointer-events-none select-none blur-sm opacity-50" aria-hidden>
        {children}
      </div>

      {/* Lock overlay */}
      <div className="absolute inset-0 flex items-center justify-center z-10">
        <div className="bg-background/95 border rounded-xl shadow-lg p-8 text-center max-w-sm mx-4">
          <div className="flex items-center justify-center w-12 h-12 rounded-full bg-muted mx-auto mb-4">
            <Lock className="h-6 w-6 text-muted-foreground" />
          </div>
          <h3 className="text-lg font-semibold mb-2">
            {featureName ? `${featureName} requires ${tierLabel}` : `${tierLabel} plan required`}
          </h3>
          <p className="text-sm text-muted-foreground mb-6">
            Upgrade to the {tierLabel} plan to unlock this feature and get access to more powerful tools.
          </p>
          <div className="flex flex-col sm:flex-row gap-3 justify-center">
            <Button asChild>
              <Link href="/billing">View Plans</Link>
            </Button>
          </div>
        </div>
      </div>
    </div>
  );
}
