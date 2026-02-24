'use client';

import Link from 'next/link';
import { X, Zap } from 'lucide-react';
import { Button } from '@/components/ui/button';

interface UpgradeModalProps {
  /** Whether the modal is currently visible. */
  open: boolean;
  /** Called when the user dismisses the modal. */
  onClose: () => void;
  /** Optional message to display (e.g. the quota error detail from the server). */
  message?: string;
}

/**
 * Upgrade prompt modal shown when a user hits a hard limit (e.g. 429 quota exceeded).
 *
 * Hook into the global API error handler to trigger this when the server returns
 * a 429 with a detail containing "quota" or "limit exceeded".
 */
export function UpgradeModal({ open, onClose, message }: UpgradeModalProps) {
  if (!open) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
      {/* Backdrop */}
      <div
        className="absolute inset-0 bg-black/50 backdrop-blur-sm"
        onClick={onClose}
        aria-hidden
      />

      {/* Modal */}
      <div className="relative bg-background border rounded-xl shadow-xl max-w-md w-full p-6 z-10">
        <button
          onClick={onClose}
          className="absolute top-4 right-4 text-muted-foreground hover:text-foreground transition-colors"
          aria-label="Close"
        >
          <X className="h-5 w-5" />
        </button>

        <div className="flex items-center justify-center w-12 h-12 rounded-full bg-primary/10 mx-auto mb-4">
          <Zap className="h-6 w-6 text-primary" />
        </div>

        <h2 className="text-xl font-semibold text-center mb-2">You have reached your limit</h2>

        {message && (
          <p className="text-sm text-muted-foreground text-center mb-4">{message}</p>
        )}

        <div className="space-y-3 mb-6 text-sm text-muted-foreground">
          <p className="font-medium text-foreground">Upgrade to unlock:</p>
          <ul className="space-y-1.5 list-disc list-inside">
            <li>Unlimited insights and analyses</li>
            <li>Priority AI research processing</li>
            <li>Team collaboration features</li>
            <li>API access for integrations</li>
            <li>PDF & advanced export formats</li>
          </ul>
        </div>

        <div className="flex flex-col sm:flex-row gap-3">
          <Button asChild className="flex-1">
            <Link href="/billing" onClick={onClose}>View Plans</Link>
          </Button>
          <Button variant="outline" className="flex-1" onClick={onClose}>
            Maybe Later
          </Button>
        </div>
      </div>
    </div>
  );
}
