'use client';

import { HelpCircle, Play, RotateCcw } from 'lucide-react';
import { Button } from '@/components/ui/button';
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from '@/components/ui/tooltip';
import { useTourContext } from './TourProvider';

interface StartTourButtonProps {
  tourId?: string;
  variant?: 'default' | 'outline' | 'ghost' | 'secondary';
  size?: 'default' | 'sm' | 'lg' | 'icon';
  showLabel?: boolean;
  className?: string;
}

export function StartTourButton({
  tourId = 'homepage',
  variant = 'outline',
  size = 'default',
  showLabel = true,
  className,
}: StartTourButtonProps) {
  const { startTour, hasCompletedTour, resetTour } = useTourContext();

  const completed = hasCompletedTour(tourId);

  const handleClick = () => {
    if (completed) {
      resetTour(tourId);
    }
    startTour(tourId);
  };

  if (size === 'icon') {
    return (
      <TooltipProvider>
        <Tooltip>
          <TooltipTrigger asChild>
            <Button
              variant={variant}
              size="icon"
              onClick={handleClick}
              className={className}
              data-tour="start-tour-button"
            >
              {completed ? (
                <RotateCcw className="h-4 w-4" />
              ) : (
                <HelpCircle className="h-4 w-4" />
              )}
            </Button>
          </TooltipTrigger>
          <TooltipContent>
            <p>{completed ? 'Replay Tour' : 'Start Tour'}</p>
          </TooltipContent>
        </Tooltip>
      </TooltipProvider>
    );
  }

  return (
    <Button
      variant={variant}
      size={size}
      onClick={handleClick}
      className={className}
      data-tour="start-tour-button"
    >
      {completed ? (
        <>
          <RotateCcw className="h-4 w-4 mr-2" />
          {showLabel && 'Replay Tour'}
        </>
      ) : (
        <>
          <Play className="h-4 w-4 mr-2" />
          {showLabel && 'Start Tour'}
        </>
      )}
    </Button>
  );
}

// Floating tour button that can be added to any page
export function FloatingTourButton({ tourId = 'homepage' }: { tourId?: string }) {
  const { startTour, hasCompletedTour, resetTour } = useTourContext();

  const completed = hasCompletedTour(tourId);

  const handleClick = () => {
    if (completed) {
      resetTour(tourId);
    }
    startTour(tourId);
  };

  return (
    <TooltipProvider>
      <Tooltip>
        <TooltipTrigger asChild>
          <Button
            variant="secondary"
            size="icon"
            onClick={handleClick}
            className="fixed bottom-20 right-6 h-12 w-12 rounded-full shadow-lg z-50 hover:scale-110 transition-transform"
            data-tour="floating-tour-button"
          >
            <HelpCircle className="h-5 w-5" />
          </Button>
        </TooltipTrigger>
        <TooltipContent side="left">
          <p>{completed ? 'Replay Tour' : 'Take a Tour'}</p>
        </TooltipContent>
      </Tooltip>
    </TooltipProvider>
  );
}
