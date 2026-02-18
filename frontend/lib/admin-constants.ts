/**
 * Shared admin constants — consistent status colors, badge variants, and status maps
 * across all admin pages.
 *
 * Status color convention:
 *   active/approved/healthy/completed → emerald/default
 *   paused/pending/draft             → amber/secondary
 *   failed/rejected/error            → red/destructive
 *   running/processing               → blue/outline
 */

export type StatusVariant = 'default' | 'secondary' | 'destructive' | 'outline';

/** Maps a status string to a shadcn Badge variant. */
export function getStatusBadgeVariant(status: string): StatusVariant {
  const normalized = status.toLowerCase();
  if (['active', 'approved', 'healthy', 'completed', 'published', 'enabled'].includes(normalized)) {
    return 'default';
  }
  if (['paused', 'pending', 'draft', 'inactive', 'disabled'].includes(normalized)) {
    return 'secondary';
  }
  if (['failed', 'rejected', 'error', 'unhealthy', 'deleted'].includes(normalized)) {
    return 'destructive';
  }
  // running, processing, in_progress, etc.
  return 'outline';
}

/** Maps a status string to a tailwind text color class for indicators. */
export function getStatusColor(status: string): string {
  const normalized = status.toLowerCase();
  if (['active', 'approved', 'healthy', 'completed', 'published'].includes(normalized)) {
    return 'text-emerald-600 dark:text-emerald-400';
  }
  if (['paused', 'pending', 'draft'].includes(normalized)) {
    return 'text-amber-600 dark:text-amber-400';
  }
  if (['failed', 'rejected', 'error', 'unhealthy'].includes(normalized)) {
    return 'text-red-600 dark:text-red-400';
  }
  return 'text-blue-600 dark:text-blue-400';
}
