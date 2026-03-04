// GuidedTour is lazy-loaded via TourProvider — do NOT re-export here
// as it would pull framer-motion (219 KB) into the main bundle.
export type { TourStep } from './GuidedTour';
export { TourProvider, useTourContext } from './TourProvider';
export { StartTourButton, FloatingTourButton } from './StartTourButton';
