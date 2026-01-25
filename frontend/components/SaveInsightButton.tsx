'use client';

import { useState } from 'react';
import { Bookmark } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { getSupabaseClient } from '@/lib/supabase/client';
import { cn } from '@/lib/utils';

interface SaveInsightButtonProps {
  insightId: string;
  initialSaved?: boolean;
  variant?: 'icon' | 'button';
  className?: string;
}

export function SaveInsightButton({
  insightId,
  initialSaved = false,
  variant = 'icon',
  className,
}: SaveInsightButtonProps) {
  const [saved, setSaved] = useState(initialSaved);
  const [loading, setLoading] = useState(false);

  const handleToggle = async () => {
    const supabase = getSupabaseClient();

    // Check if user is authenticated
    const { data: { user } } = await supabase.auth.getUser();
    if (!user) {
      // Redirect to login
      window.location.href = '/auth/login?redirectTo=' + encodeURIComponent(window.location.pathname);
      return;
    }

    setLoading(true);
    try {
      if (saved) {
        // Remove from saved
        const { error } = await supabase
          .from('saved_insights')
          .delete()
          .eq('user_id', user.id)
          .eq('insight_id', insightId);

        if (error) throw error;
        setSaved(false);
      } else {
        // Add to saved
        const { error } = await supabase
          .from('saved_insights')
          .insert({ user_id: user.id, insight_id: insightId });

        if (error) throw error;
        setSaved(true);
      }
    } catch (error) {
      console.error('Error toggling save:', error);
    } finally {
      setLoading(false);
    }
  };

  if (variant === 'icon') {
    return (
      <button
        onClick={handleToggle}
        disabled={loading}
        className={cn(
          'p-2 rounded-full transition-colors',
          saved ? 'text-primary' : 'text-muted-foreground hover:text-foreground',
          loading && 'opacity-50 cursor-not-allowed',
          className
        )}
        aria-label={saved ? 'Remove from saved' : 'Save insight'}
      >
        <Bookmark
          className="h-5 w-5"
          fill={saved ? 'currentColor' : 'none'}
        />
      </button>
    );
  }

  return (
    <Button
      onClick={handleToggle}
      disabled={loading}
      variant={saved ? 'default' : 'outline'}
      size="sm"
      className={className}
    >
      <Bookmark
        className="h-4 w-4 mr-2"
        fill={saved ? 'currentColor' : 'none'}
      />
      {saved ? 'Saved' : 'Save'}
    </Button>
  );
}
