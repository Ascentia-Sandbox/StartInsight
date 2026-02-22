'use client';

import { useEffect, useState } from 'react';
import Link from 'next/link';
import { X, Lightbulb, Bookmark, FlaskConical } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';

const DISMISS_KEY = 'si_onboarding_dismissed';

interface OnboardingBannerProps {
  insightsSaved: number;
}

interface Step {
  number: number;
  label: string;
  description: string;
  icon: React.ReactNode;
  href: string;
}

const STEPS: Step[] = [
  {
    number: 1,
    label: 'Browse Ideas',
    description: 'Discover AI-analyzed opportunities',
    icon: <Lightbulb className="h-4 w-4" />,
    href: '/insights',
  },
  {
    number: 2,
    label: 'Save an Insight',
    description: 'Bookmark ideas that resonate',
    icon: <Bookmark className="h-4 w-4" />,
    href: '/insights',
  },
  {
    number: 3,
    label: 'Validate Your Idea',
    description: 'Run AI-powered market research',
    icon: <FlaskConical className="h-4 w-4" />,
    href: '/validate',
  },
];

export function OnboardingBanner({ insightsSaved }: OnboardingBannerProps) {
  const [dismissed, setDismissed] = useState<boolean | null>(null);

  useEffect(() => {
    setDismissed(localStorage.getItem(DISMISS_KEY) === 'true');
  }, []);

  const handleDismiss = () => {
    localStorage.setItem(DISMISS_KEY, 'true');
    setDismissed(true);
  };

  // Wait for mount to avoid hydration mismatch; hide if dismissed or user has saves
  if (dismissed === null || dismissed || insightsSaved > 0) {
    return null;
  }

  return (
    <div className="relative mb-8 rounded-xl border border-teal-500/20 bg-gradient-to-r from-teal-500/10 to-teal-600/5 px-5 py-4">
      {/* Dismiss button */}
      <button
        onClick={handleDismiss}
        aria-label="Dismiss onboarding banner"
        className="absolute right-3 top-3 rounded-md p-1 text-muted-foreground transition-colors hover:bg-teal-500/10 hover:text-foreground"
      >
        <X className="h-4 w-4" />
      </button>

      {/* Header row */}
      <div className="flex flex-wrap items-center gap-2 mb-4 pr-8">
        <Badge
          variant="secondary"
          className="bg-teal-500/15 text-teal-700 dark:text-teal-300 border-teal-500/20"
        >
          Get Started
        </Badge>
        <p className="text-sm font-medium">
          Welcome to StartInsight — here&apos;s how to find your next big idea
        </p>
      </div>

      {/* Steps — horizontal on md+, stacked on mobile */}
      <div className="grid grid-cols-1 gap-3 sm:grid-cols-3 mb-4">
        {STEPS.map((step) => (
          <Link key={step.number} href={step.href} className="group block">
            <div className="flex items-center gap-3 rounded-lg border border-teal-500/15 bg-background/60 px-3 py-2.5 transition-colors hover:border-teal-500/40 hover:bg-teal-500/5">
              {/* Step number circle */}
              <span className="flex h-7 w-7 shrink-0 items-center justify-center rounded-full bg-teal-500 text-xs font-bold text-white">
                {step.number}
              </span>

              {/* Text — hide description on smallest screens to stay compact */}
              <div className="min-w-0 flex-1">
                <p className="text-sm font-medium leading-none group-hover:text-teal-700 dark:group-hover:text-teal-300">
                  {step.label}
                </p>
                <p className="mt-0.5 hidden text-xs text-muted-foreground sm:block truncate">
                  {step.description}
                </p>
              </div>

              {/* Icon */}
              <span className="shrink-0 text-teal-600 dark:text-teal-400 opacity-70 group-hover:opacity-100">
                {step.icon}
              </span>
            </div>
          </Link>
        ))}
      </div>

      {/* CTA row */}
      <div className="flex items-center gap-3">
        <Link href="/insights">
          <Button
            size="sm"
            className="bg-teal-600 text-white hover:bg-teal-700 dark:bg-teal-500 dark:hover:bg-teal-600"
          >
            Explore Insights →
          </Button>
        </Link>
        <button
          onClick={handleDismiss}
          className="text-xs text-muted-foreground hover:text-foreground transition-colors underline underline-offset-2"
        >
          Don&apos;t show again
        </button>
      </div>
    </div>
  );
}
