'use client';

import type { LucideIcon } from 'lucide-react';

/**
 * Consistent admin page header component.
 *
 * Usage:
 *   <AdminPageHeader
 *     icon={Activity}
 *     title="Pipeline Monitoring"
 *     description="Monitor scraper health, quotas, and pipeline status"
 *     actions={<Button>Action</Button>}
 *   />
 */
export function AdminPageHeader({
  icon: Icon,
  title,
  description,
  actions,
}: {
  icon: LucideIcon;
  title: string;
  description?: string;
  actions?: React.ReactNode;
}) {
  return (
    <div className="flex items-center justify-between">
      <div>
        <h1 className="text-2xl font-bold flex items-center gap-2">
          <Icon className="h-6 w-6" />
          {title}
        </h1>
        {description && (
          <p className="text-muted-foreground text-sm mt-1">{description}</p>
        )}
      </div>
      {actions && <div className="flex items-center gap-3">{actions}</div>}
    </div>
  );
}
