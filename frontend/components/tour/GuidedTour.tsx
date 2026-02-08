'use client';

import { useState, useEffect, useCallback } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { X, ChevronLeft, ChevronRight, Sparkles } from 'lucide-react';
import { Button } from '@/components/ui/button';

export interface TourStep {
  target: string; // CSS selector for the target element
  title: string;
  content: string;
  placement?: 'top' | 'bottom' | 'left' | 'right';
  spotlightPadding?: number;
}

interface GuidedTourProps {
  steps: TourStep[];
  onComplete?: () => void;
  onSkip?: () => void;
  isOpen: boolean;
  onClose: () => void;
}

export function GuidedTour({ steps, onComplete, onSkip, isOpen, onClose }: GuidedTourProps) {
  const [currentStep, setCurrentStep] = useState(0);
  const [targetRect, setTargetRect] = useState<DOMRect | null>(null);

  const step = steps[currentStep];

  const updateTargetPosition = useCallback(() => {
    if (!step?.target) return;

    const element = document.querySelector(step.target);
    if (element) {
      const rect = element.getBoundingClientRect();
      setTargetRect(rect);

      // Scroll element into view if not visible
      const isInView = rect.top >= 0 && rect.bottom <= window.innerHeight;
      if (!isInView) {
        element.scrollIntoView({ behavior: 'smooth', block: 'center' });
        // Update rect after scroll
        setTimeout(() => {
          setTargetRect(element.getBoundingClientRect());
        }, 500);
      }
    }
  }, [step?.target]);

  useEffect(() => {
    if (isOpen) {
      updateTargetPosition();
      window.addEventListener('resize', updateTargetPosition);
      window.addEventListener('scroll', updateTargetPosition, true);
    }
    return () => {
      window.removeEventListener('resize', updateTargetPosition);
      window.removeEventListener('scroll', updateTargetPosition, true);
    };
  }, [isOpen, currentStep, updateTargetPosition]);

  const handleNext = () => {
    if (currentStep < steps.length - 1) {
      setCurrentStep(currentStep + 1);
    } else {
      handleComplete();
    }
  };

  const handlePrev = () => {
    if (currentStep > 0) {
      setCurrentStep(currentStep - 1);
    }
  };

  const handleComplete = () => {
    localStorage.setItem('startinsight_tour_completed', 'true');
    onComplete?.();
    onClose();
    setCurrentStep(0);
  };

  const handleSkip = () => {
    localStorage.setItem('startinsight_tour_completed', 'true');
    onSkip?.();
    onClose();
    setCurrentStep(0);
  };

  const getTooltipPosition = () => {
    if (!targetRect) {
      return { top: '50%', left: '50%', transform: 'translate(-50%, -50%)' };
    }

    const padding = step?.spotlightPadding || 8;
    const tooltipWidth = 320;
    const tooltipHeight = 200;
    const spacing = 16;

    const placement = step?.placement || 'bottom';

    switch (placement) {
      case 'top':
        return {
          bottom: window.innerHeight - targetRect.top + spacing + padding,
          left: Math.max(16, Math.min(targetRect.left + targetRect.width / 2 - tooltipWidth / 2, window.innerWidth - tooltipWidth - 16)),
        };
      case 'bottom':
        return {
          top: targetRect.bottom + spacing + padding,
          left: Math.max(16, Math.min(targetRect.left + targetRect.width / 2 - tooltipWidth / 2, window.innerWidth - tooltipWidth - 16)),
        };
      case 'left':
        return {
          top: Math.max(16, Math.min(targetRect.top + targetRect.height / 2 - tooltipHeight / 2, window.innerHeight - tooltipHeight - 16)),
          right: window.innerWidth - targetRect.left + spacing + padding,
        };
      case 'right':
        return {
          top: Math.max(16, Math.min(targetRect.top + targetRect.height / 2 - tooltipHeight / 2, window.innerHeight - tooltipHeight - 16)),
          left: targetRect.right + spacing + padding,
        };
      default:
        return {
          top: targetRect.bottom + spacing + padding,
          left: Math.max(16, Math.min(targetRect.left + targetRect.width / 2 - tooltipWidth / 2, window.innerWidth - tooltipWidth - 16)),
        };
    }
  };

  if (!isOpen) return null;

  const padding = step?.spotlightPadding || 8;

  return (
    <AnimatePresence>
      <div className="fixed inset-0 z-[9999]" data-tour-overlay>
        {/* Backdrop with spotlight cutout */}
        <svg className="absolute inset-0 w-full h-full">
          <defs>
            <mask id="spotlight-mask">
              <rect x="0" y="0" width="100%" height="100%" fill="white" />
              {targetRect && (
                <motion.rect
                  initial={{ opacity: 0 }}
                  animate={{ opacity: 1 }}
                  x={targetRect.left - padding}
                  y={targetRect.top - padding}
                  width={targetRect.width + padding * 2}
                  height={targetRect.height + padding * 2}
                  rx="8"
                  fill="black"
                />
              )}
            </mask>
          </defs>
          <rect
            x="0"
            y="0"
            width="100%"
            height="100%"
            fill="rgba(0, 0, 0, 0.75)"
            mask="url(#spotlight-mask)"
          />
        </svg>

        {/* Spotlight border/highlight */}
        {targetRect && (
          <motion.div
            initial={{ opacity: 0, scale: 0.95 }}
            animate={{ opacity: 1, scale: 1 }}
            className="absolute border-2 border-primary rounded-lg pointer-events-none"
            style={{
              left: targetRect.left - padding,
              top: targetRect.top - padding,
              width: targetRect.width + padding * 2,
              height: targetRect.height + padding * 2,
              boxShadow: '0 0 0 4px rgba(99, 102, 241, 0.3)',
            }}
          />
        )}

        {/* Tooltip */}
        <motion.div
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          exit={{ opacity: 0, y: 10 }}
          className="absolute bg-background border rounded-xl shadow-2xl p-5 w-80 z-10"
          style={getTooltipPosition()}
        >
          {/* Close button */}
          <button
            onClick={handleSkip}
            className="absolute top-3 right-3 text-muted-foreground hover:text-foreground transition-colors"
          >
            <X className="h-4 w-4" />
          </button>

          {/* Step indicator */}
          <div className="flex items-center gap-2 mb-3">
            <Sparkles className="h-4 w-4 text-primary" />
            <span className="text-xs font-medium text-muted-foreground">
              Step {currentStep + 1} of {steps.length}
            </span>
          </div>

          {/* Progress bar */}
          <div className="w-full h-1 bg-muted rounded-full mb-4">
            <motion.div
              className="h-full bg-primary rounded-full"
              initial={{ width: 0 }}
              animate={{ width: `${((currentStep + 1) / steps.length) * 100}%` }}
              transition={{ duration: 0.3 }}
            />
          </div>

          {/* Content */}
          <h3 className="text-lg font-semibold mb-2">{step?.title}</h3>
          <p className="text-sm text-muted-foreground mb-4">{step?.content}</p>

          {/* Navigation */}
          <div className="flex items-center justify-between">
            <Button
              variant="ghost"
              size="sm"
              onClick={handleSkip}
              className="text-muted-foreground"
            >
              Skip tour
            </Button>
            <div className="flex gap-2">
              {currentStep > 0 && (
                <Button variant="outline" size="sm" onClick={handlePrev}>
                  <ChevronLeft className="h-4 w-4 mr-1" />
                  Back
                </Button>
              )}
              <Button size="sm" onClick={handleNext}>
                {currentStep === steps.length - 1 ? (
                  'Finish'
                ) : (
                  <>
                    Next
                    <ChevronRight className="h-4 w-4 ml-1" />
                  </>
                )}
              </Button>
            </div>
          </div>
        </motion.div>
      </div>
    </AnimatePresence>
  );
}

// Hook to manage tour state
export function useTour() {
  const [isOpen, setIsOpen] = useState(false);
  const [hasCompletedTour, setHasCompletedTour] = useState(true);

  useEffect(() => {
    const completed = localStorage.getItem('startinsight_tour_completed');
    setHasCompletedTour(completed === 'true');
  }, []);

  const startTour = () => setIsOpen(true);
  const closeTour = () => setIsOpen(false);
  const resetTour = () => {
    localStorage.removeItem('startinsight_tour_completed');
    setHasCompletedTour(false);
  };

  return {
    isOpen,
    startTour,
    closeTour,
    resetTour,
    hasCompletedTour,
  };
}
