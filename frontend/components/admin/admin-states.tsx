'use client';

import { Loader2, AlertCircle, Inbox } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Card, CardContent } from '@/components/ui/card';

/**
 * Loading skeleton for admin pages — skeleton cards matching typical admin layout.
 */
export function AdminLoading() {
  return (
    <div className="flex items-center justify-center h-64">
      <Loader2 className="h-6 w-6 animate-spin text-muted-foreground" />
    </div>
  );
}

/**
 * Empty state for admin pages — icon + title + description + optional CTA.
 */
export function AdminEmpty({
  icon: Icon = Inbox,
  title = 'No data found',
  description,
  actionLabel,
  onAction,
}: {
  icon?: React.ElementType;
  title?: string;
  description?: string;
  actionLabel?: string;
  onAction?: () => void;
}) {
  return (
    <Card>
      <CardContent className="py-12 text-center">
        <Icon className="h-10 w-10 mx-auto mb-3 text-muted-foreground/50" />
        <p className="font-medium">{title}</p>
        {description && (
          <p className="text-sm text-muted-foreground mt-1">{description}</p>
        )}
        {actionLabel && onAction && (
          <Button variant="outline" size="sm" className="mt-4" onClick={onAction}>
            {actionLabel}
          </Button>
        )}
      </CardContent>
    </Card>
  );
}

/**
 * Error state for admin pages — red alert with retry button.
 */
export function AdminError({
  message = 'Something went wrong',
  onRetry,
}: {
  message?: string;
  onRetry?: () => void;
}) {
  return (
    <Card className="border-destructive/50">
      <CardContent className="py-8 text-center">
        <AlertCircle className="h-8 w-8 mx-auto mb-2 text-destructive" />
        <p className="text-sm text-destructive font-medium">{message}</p>
        {onRetry && (
          <Button variant="outline" size="sm" className="mt-3" onClick={onRetry}>
            Retry
          </Button>
        )}
      </CardContent>
    </Card>
  );
}
