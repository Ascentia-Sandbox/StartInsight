/**
 * Selectable Card Component - Code simplification Phase 3.
 *
 * Reusable card for selection UIs (research type picker, etc.).
 * Replaces 3 duplicate button patterns in research/page.tsx.
 */

import React from 'react';

interface SelectableCardProps {
  title: string;
  description: string;
  icon?: React.ReactNode;
  selected?: boolean;
  onClick?: () => void;
  className?: string;
}

export function SelectableCard({
  title,
  description,
  icon,
  selected = false,
  onClick,
  className = '',
}: SelectableCardProps) {
  return (
    <button
      onClick={onClick}
      className={`
        p-6 rounded-lg border-2 transition-all text-left w-full
        ${selected
          ? 'border-blue-500 bg-blue-50 dark:bg-blue-950'
          : 'border-gray-200 dark:border-gray-700 hover:border-blue-300'
        }
        ${className}
      `}
    >
      {icon && <div className="mb-3">{icon}</div>}
      <h3 className="font-semibold text-lg mb-2">{title}</h3>
      <p className="text-sm text-gray-600 dark:text-gray-400">{description}</p>
    </button>
  );
}
