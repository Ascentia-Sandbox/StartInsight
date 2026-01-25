'use client';

import { Card, CardContent } from '@/components/ui/card';
import { cn } from '@/lib/utils';
import { ExternalLink } from 'lucide-react';

// Builder platform configurations
export const BUILDER_PLATFORMS = {
  lovable: {
    name: 'Lovable',
    description: 'AI-powered full-stack app builder',
    icon: 'L',
    color: 'bg-purple-500',
    url: 'https://lovable.dev',
    promptPrefix: 'Build me a web application for:',
  },
  v0: {
    name: 'v0',
    description: 'Vercel AI UI generator',
    icon: 'v0',
    color: 'bg-black dark:bg-white dark:text-black',
    url: 'https://v0.dev',
    promptPrefix: 'Create a React component for:',
  },
  replit: {
    name: 'Replit',
    description: 'Online IDE with AI assistant',
    icon: 'R',
    color: 'bg-orange-500',
    url: 'https://replit.com',
    promptPrefix: 'Create a Python/Node.js application for:',
  },
  chatgpt: {
    name: 'ChatGPT',
    description: 'OpenAI conversational AI',
    icon: 'GPT',
    color: 'bg-emerald-500',
    url: 'https://chat.openai.com',
    promptPrefix: 'Help me build:',
  },
  claude: {
    name: 'Claude',
    description: 'Anthropic AI assistant',
    icon: 'C',
    color: 'bg-amber-600',
    url: 'https://claude.ai',
    promptPrefix: 'Help me implement:',
  },
} as const;

export type BuilderPlatformId = keyof typeof BUILDER_PLATFORMS;

interface BuilderPlatformCardProps {
  platformId: BuilderPlatformId;
  isSelected?: boolean;
  onSelect?: (platformId: BuilderPlatformId) => void;
  size?: 'sm' | 'md' | 'lg';
}

export function BuilderPlatformCard({
  platformId,
  isSelected = false,
  onSelect,
  size = 'md',
}: BuilderPlatformCardProps) {
  const platform = BUILDER_PLATFORMS[platformId];

  const sizeConfig = {
    sm: { card: 'p-2', icon: 'w-6 h-6 text-xs', text: 'text-xs' },
    md: { card: 'p-3', icon: 'w-10 h-10 text-sm', text: 'text-sm' },
    lg: { card: 'p-4', icon: 'w-12 h-12 text-base', text: 'text-base' },
  };

  const { card: cardSize, icon: iconSize, text: textSize } = sizeConfig[size];

  return (
    <Card
      className={cn(
        'cursor-pointer transition-all hover:shadow-md',
        cardSize,
        isSelected
          ? 'border-2 border-primary ring-2 ring-primary/20'
          : 'border hover:border-primary/50'
      )}
      onClick={() => onSelect?.(platformId)}
    >
      <CardContent className="p-0 flex items-center gap-3">
        {/* Platform Icon */}
        <div
          className={cn(
            'flex items-center justify-center rounded-lg font-bold text-white',
            platform.color,
            iconSize
          )}
        >
          {platform.icon}
        </div>

        {/* Platform Info */}
        <div className="flex-1 min-w-0">
          <h4 className={cn('font-semibold truncate', textSize)}>{platform.name}</h4>
          {size !== 'sm' && (
            <p className="text-xs text-muted-foreground truncate">{platform.description}</p>
          )}
        </div>

        {/* Selection indicator */}
        {isSelected && (
          <div className="flex-shrink-0 w-5 h-5 rounded-full bg-primary flex items-center justify-center">
            <svg className="w-3 h-3 text-primary-foreground" fill="currentColor" viewBox="0 0 20 20">
              <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" />
            </svg>
          </div>
        )}
      </CardContent>
    </Card>
  );
}

interface BuilderPlatformGridProps {
  selectedPlatform?: BuilderPlatformId | null;
  onSelect?: (platformId: BuilderPlatformId) => void;
  size?: 'sm' | 'md' | 'lg';
}

export function BuilderPlatformGrid({ selectedPlatform, onSelect, size = 'md' }: BuilderPlatformGridProps) {
  return (
    <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-5 gap-3">
      {(Object.keys(BUILDER_PLATFORMS) as BuilderPlatformId[]).map((platformId) => (
        <BuilderPlatformCard
          key={platformId}
          platformId={platformId}
          isSelected={selectedPlatform === platformId}
          onSelect={onSelect}
          size={size}
        />
      ))}
    </div>
  );
}
