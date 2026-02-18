'use client';

import { useState } from 'react';
import { Star } from 'lucide-react';
import { getSupabaseClient } from '@/lib/supabase/client';
import { cn } from '@/lib/utils';

interface RatingComponentProps {
  insightId: string;
  initialRating?: number;
  size?: 'sm' | 'md' | 'lg';
  readonly?: boolean;
  className?: string;
  onRatingChange?: (rating: number) => void;
}

import { config } from '@/lib/env';

const API_URL = config.apiUrl;

export function RatingComponent({
  insightId,
  initialRating = 0,
  size = 'md',
  readonly = false,
  className,
  onRatingChange,
}: RatingComponentProps) {
  const [rating, setRating] = useState(initialRating);
  const [hoveredRating, setHoveredRating] = useState(0);
  const [loading, setLoading] = useState(false);

  const sizeClasses = {
    sm: 'h-4 w-4',
    md: 'h-5 w-5',
    lg: 'h-6 w-6',
  };

  const handleRate = async (newRating: number) => {
    if (readonly) return;

    const supabase = getSupabaseClient();

    // Check if user is authenticated
    const { data: { session } } = await supabase.auth.getSession();
    if (!session) {
      window.location.href = '/auth/login?redirectTo=' + encodeURIComponent(window.location.pathname);
      return;
    }

    setLoading(true);
    try {
      const res = await fetch(`${API_URL}/api/users/insights/${insightId}/rate`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${session.access_token}`,
        },
        body: JSON.stringify({ rating: newRating }),
      });

      if (!res.ok) throw new Error('Failed to rate');

      setRating(newRating);
      onRatingChange?.(newRating);
    } catch (error) {
      console.error('Error rating insight:', error);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className={cn('flex items-center gap-1', className)}>
      {[1, 2, 3, 4, 5].map((star) => {
        const filled = readonly
          ? star <= rating
          : star <= (hoveredRating || rating);

        return (
          <button
            key={star}
            type="button"
            disabled={loading || readonly}
            onClick={() => handleRate(star)}
            onMouseEnter={() => !readonly && setHoveredRating(star)}
            onMouseLeave={() => !readonly && setHoveredRating(0)}
            className={cn(
              'transition-colors',
              readonly ? 'cursor-default' : 'cursor-pointer',
              loading && 'opacity-50 cursor-not-allowed'
            )}
            aria-label={`Rate ${star} stars`}
          >
            <Star
              className={cn(
                sizeClasses[size],
                filled ? 'text-yellow-500' : 'text-muted-foreground'
              )}
              fill={filled ? 'currentColor' : 'none'}
            />
          </button>
        );
      })}
      {!readonly && rating > 0 && (
        <span className="ml-2 text-sm text-muted-foreground">
          {rating}/5
        </span>
      )}
    </div>
  );
}
