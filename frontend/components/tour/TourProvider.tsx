'use client';

import { createContext, useContext, useState, useEffect, ReactNode } from 'react';
import { GuidedTour, TourStep } from './GuidedTour';

// Define tour steps for the homepage
const homepageTourSteps: TourStep[] = [
  {
    target: '[data-tour="logo"]',
    title: 'Welcome to StartInsight!',
    content: 'Your AI-powered platform for discovering validated startup ideas. Let us show you around!',
    placement: 'bottom',
  },
  {
    target: '[data-tour="browse-ideas"]',
    title: 'Browse Ideas',
    content: 'Explore our database of 1000+ validated startup ideas, daily featured opportunities, trending keywords, and market insights.',
    placement: 'bottom',
  },
  {
    target: '[data-tour="tools"]',
    title: 'Powerful Tools',
    content: 'Access our startup toolkit including the AI Research Agent, brand generators, and landing page builders.',
    placement: 'bottom',
  },
  {
    target: '[data-tour="resources"]',
    title: 'Learning Resources',
    content: 'Find success stories, founder guides, and documentation to help you succeed on your entrepreneurial journey.',
    placement: 'bottom',
  },
  {
    target: '[data-tour="theme-toggle"]',
    title: 'Dark Mode',
    content: 'Toggle between light and dark modes for comfortable viewing day or night.',
    placement: 'bottom',
  },
  {
    target: '[data-tour="get-started"]',
    title: 'Get Started',
    content: 'Create your free account to save ideas, access the research agent, and unlock all features.',
    placement: 'left',
  },
  {
    target: '[data-tour="hero-cta"]',
    title: 'Start Exploring',
    content: 'Click "Explore Ideas" to browse our curated database of startup opportunities with 8-dimension scoring.',
    placement: 'top',
  },
];

// Define tour steps for the insights page
const insightsTourSteps: TourStep[] = [
  {
    target: '[data-tour="insights-filters"]',
    title: 'Filter Ideas',
    content: 'Use filters to narrow down ideas by source, score range, or search for specific topics.',
    placement: 'bottom',
  },
  {
    target: '[data-tour="insight-card"]',
    title: 'Insight Cards',
    content: 'Each card shows a startup idea with its relevance score, market category, and key metrics. Click to see full details.',
    placement: 'right',
  },
];

// Define tour steps for insight detail page
const insightDetailTourSteps: TourStep[] = [
  {
    target: '[data-tour="insight-title"]',
    title: 'Idea Overview',
    content: 'This is the main problem statement identified by our AI from real market signals.',
    placement: 'bottom',
  },
  {
    target: '[data-tour="score-radar"]',
    title: '8-Dimension Scoring',
    content: 'Our AI evaluates each idea across 8 dimensions including opportunity, feasibility, timing, and more.',
    placement: 'left',
  },
  {
    target: '[data-tour="community-signals"]',
    title: 'Community Signals',
    content: 'See real engagement data from Reddit, Product Hunt, and other platforms that validate this idea.',
    placement: 'left',
  },
  {
    target: '[data-tour="build-idea"]',
    title: 'Build This Idea',
    content: 'Export this idea directly to AI builders like Lovable, Bolt, or Replit with one click.',
    placement: 'top',
  },
];

interface TourContextType {
  startTour: (tourId?: string) => void;
  closeTour: () => void;
  isOpen: boolean;
  hasCompletedTour: (tourId: string) => boolean;
  resetTour: (tourId?: string) => void;
  currentTourId: string | null;
}

const TourContext = createContext<TourContextType | null>(null);

export function useTourContext() {
  const context = useContext(TourContext);
  if (!context) {
    throw new Error('useTourContext must be used within TourProvider');
  }
  return context;
}

interface TourProviderProps {
  children: ReactNode;
}

export function TourProvider({ children }: TourProviderProps) {
  const [isOpen, setIsOpen] = useState(false);
  const [currentTourId, setCurrentTourId] = useState<string | null>(null);
  const [completedTours, setCompletedTours] = useState<Set<string>>(new Set());

  useEffect(() => {
    // Load completed tours from localStorage
    const saved = localStorage.getItem('startinsight_completed_tours');
    if (saved) {
      try {
        setCompletedTours(new Set(JSON.parse(saved)));
      } catch {
        setCompletedTours(new Set());
      }
    }
  }, []);

  const getTourSteps = (tourId: string): TourStep[] => {
    switch (tourId) {
      case 'homepage':
        return homepageTourSteps;
      case 'insights':
        return insightsTourSteps;
      case 'insight-detail':
        return insightDetailTourSteps;
      default:
        return homepageTourSteps;
    }
  };

  const startTour = (tourId: string = 'homepage') => {
    setCurrentTourId(tourId);
    setIsOpen(true);
  };

  const closeTour = () => {
    setIsOpen(false);
  };

  const markTourComplete = () => {
    if (currentTourId) {
      const newCompleted = new Set(completedTours);
      newCompleted.add(currentTourId);
      setCompletedTours(newCompleted);
      localStorage.setItem('startinsight_completed_tours', JSON.stringify([...newCompleted]));
    }
    closeTour();
  };

  const hasCompletedTour = (tourId: string) => {
    return completedTours.has(tourId);
  };

  const resetTour = (tourId?: string) => {
    if (tourId) {
      const newCompleted = new Set(completedTours);
      newCompleted.delete(tourId);
      setCompletedTours(newCompleted);
      localStorage.setItem('startinsight_completed_tours', JSON.stringify([...newCompleted]));
    } else {
      setCompletedTours(new Set());
      localStorage.removeItem('startinsight_completed_tours');
    }
  };

  const steps = currentTourId ? getTourSteps(currentTourId) : [];

  return (
    <TourContext.Provider
      value={{
        startTour,
        closeTour,
        isOpen,
        hasCompletedTour,
        resetTour,
        currentTourId,
      }}
    >
      {children}
      <GuidedTour
        steps={steps}
        isOpen={isOpen}
        onClose={closeTour}
        onComplete={markTourComplete}
        onSkip={markTourComplete}
      />
    </TourContext.Provider>
  );
}
