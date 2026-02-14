/**
 * Shared animation constants for framer-motion.
 *
 * Usage:
 *   import { staggerContainer, fadeUpItem } from "@/lib/animations";
 *   <motion.div variants={staggerContainer} initial="hidden" animate="show">
 *     <motion.div variants={fadeUpItem}>...</motion.div>
 *   </motion.div>
 */

import type { Variants, Transition } from "framer-motion";

// ---------------------------------------------------------------------------
// Staggered fade-up reveals for card grids
// ---------------------------------------------------------------------------

export const staggerContainer: Variants = {
  hidden: { opacity: 0 },
  show: {
    opacity: 1,
    transition: { staggerChildren: 0.05 }, // 50ms delay per item
  },
};

export const fadeUpItem: Variants = {
  hidden: { opacity: 0, y: 20 },
  show: {
    opacity: 1,
    y: 0,
    transition: { duration: 0.4, ease: [0.25, 0.46, 0.45, 0.94] },
  },
};

// ---------------------------------------------------------------------------
// Card hover animation — use with whileHover={cardHover}
// ---------------------------------------------------------------------------

export const cardHover = {
  scale: 1.01,
  transition: { duration: 0.2 },
} as const;

// ---------------------------------------------------------------------------
// Score counter animation helper (for animated numbers)
// ---------------------------------------------------------------------------

export const counterAnimation: Transition = {
  duration: 1.5,
  ease: [0.25, 0.46, 0.45, 0.94] as const,
};

// ---------------------------------------------------------------------------
// Page section reveal on scroll — use with whileInView
// ---------------------------------------------------------------------------

export const sectionReveal: Variants = {
  hidden: { opacity: 0, y: 30 },
  visible: {
    opacity: 1,
    y: 0,
    transition: { duration: 0.6, ease: [0.25, 0.46, 0.45, 0.94] },
  },
};

// ---------------------------------------------------------------------------
// Skeleton-to-data morphing — use with AnimatePresence
// ---------------------------------------------------------------------------

export const skeletonToData = {
  initial: { opacity: 0, filter: "blur(4px)" },
  animate: {
    opacity: 1,
    filter: "blur(0px)",
    transition: { duration: 0.4 },
  },
  exit: { opacity: 0, transition: { duration: 0.15 } },
} as const;
