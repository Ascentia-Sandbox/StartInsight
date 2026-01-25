'use client';

import { ExternalLink } from 'lucide-react';
import { Button } from '@/components/ui/button';

// Platform icons and styling
const PLATFORM_ICONS: Record<string, { icon: string; label: string }> = {
  reddit: { icon: 'R', label: 'Reddit' },
  product_hunt: { icon: 'PH', label: 'Product Hunt' },
  producthunt: { icon: 'PH', label: 'Product Hunt' },
  google_trends: { icon: 'GT', label: 'Google Trends' },
  twitter: { icon: 'X', label: 'Twitter/X' },
  hackernews: { icon: 'HN', label: 'Hacker News' },
  facebook: { icon: 'f', label: 'Facebook' },
  youtube: { icon: 'YT', label: 'YouTube' },
};

interface DataCitationLinkProps {
  url: string;
  platform: string;
  variant?: 'link' | 'button' | 'badge';
}

export function DataCitationLink({ url, platform, variant = 'link' }: DataCitationLinkProps) {
  const config = PLATFORM_ICONS[platform.toLowerCase()] || {
    icon: platform.charAt(0).toUpperCase(),
    label: platform,
  };

  if (variant === 'button') {
    return (
      <Button
        asChild
        variant="outline"
        size="sm"
        className="gap-2"
      >
        <a href={url} target="_blank" rel="noopener noreferrer">
          <span className="font-bold text-xs bg-muted px-1.5 py-0.5 rounded">
            {config.icon}
          </span>
          View on {config.label}
          <ExternalLink className="h-3 w-3" />
        </a>
      </Button>
    );
  }

  if (variant === 'badge') {
    return (
      <a
        href={url}
        target="_blank"
        rel="noopener noreferrer"
        className="inline-flex items-center gap-1.5 px-2 py-1 text-xs font-medium bg-muted rounded-md hover:bg-muted/80 transition-colors"
      >
        <span className="font-bold">{config.icon}</span>
        <span>View Source</span>
        <ExternalLink className="h-3 w-3" />
      </a>
    );
  }

  // Default: link variant
  return (
    <a
      href={url}
      target="_blank"
      rel="noopener noreferrer"
      className="inline-flex items-center gap-1 text-sm text-blue-600 hover:text-blue-800 dark:text-blue-400 dark:hover:text-blue-300 hover:underline"
    >
      <span className="font-semibold">{config.icon}</span>
      <span>View on {config.label}</span>
      <ExternalLink className="h-3 w-3" />
    </a>
  );
}

interface MultiSourceCitationsProps {
  sources: Array<{ url: string; platform: string; label?: string }>;
}

export function MultiSourceCitations({ sources }: MultiSourceCitationsProps) {
  if (!sources || sources.length === 0) return null;

  return (
    <div className="flex flex-wrap gap-2">
      {sources.map((source, idx) => (
        <DataCitationLink
          key={idx}
          url={source.url}
          platform={source.platform}
          variant="badge"
        />
      ))}
    </div>
  );
}
