'use client';

import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import Link from 'next/link';
import { useQuery } from '@tanstack/react-query';
import { Loader2, MessageSquare, ArrowRight, Search } from 'lucide-react';
import { getSupabaseClient } from '@/lib/supabase/client';
import { fetchSavedInsights } from '@/lib/api';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import type { SavedInsight } from '@/lib/types';

export default function ChatHubPage() {
  const router = useRouter();
  const [accessToken, setAccessToken] = useState<string | null>(null);
  const [isCheckingAuth, setIsCheckingAuth] = useState(true);

  useEffect(() => {
    const checkAuth = async () => {
      const supabase = getSupabaseClient();
      const { data: { session } } = await supabase.auth.getSession();

      if (!session) {
        router.push('/auth/login?redirectTo=/chat');
        return;
      }

      setAccessToken(session.access_token);
      setIsCheckingAuth(false);
    };

    checkAuth();
  }, [router]);

  const { data: savedInsights, isLoading, error } = useQuery({
    queryKey: ['chat-hub-insights', accessToken],
    queryFn: () => fetchSavedInsights(accessToken!, { limit: 50 }),
    enabled: !!accessToken,
  });

  if (isCheckingAuth) {
    return (
      <div className="min-h-screen bg-background flex items-center justify-center">
        <div className="text-center">
          <Loader2 className="animate-spin h-8 w-8 text-primary mx-auto" />
          <p className="mt-2 text-muted-foreground">Loading...</p>
        </div>
      </div>
    );
  }

  const insights = savedInsights?.items || [];

  return (
    <div className="min-h-screen bg-background">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Header */}
        <div className="mb-8">
          <h1 className="text-3xl font-bold tracking-tight flex items-center gap-3">
            <MessageSquare className="h-8 w-8 text-primary" />
            Chat &amp; Strategize
          </h1>
          <p className="text-muted-foreground mt-2">
            Pick an insight to discuss with AI — pressure test ideas, plan GTM strategy, explore pricing, and more.
          </p>
        </div>

        {/* Content */}
        {error ? (
          <div className="text-center py-12 text-muted-foreground">
            <p>Failed to load insights. Please try refreshing.</p>
          </div>
        ) : isLoading ? (
          <div className="flex items-center justify-center py-12">
            <Loader2 className="animate-spin h-8 w-8 text-primary" />
          </div>
        ) : insights.length === 0 ? (
          <EmptyState />
        ) : (
          <InsightGrid insights={insights} />
        )}
      </div>
    </div>
  );
}

function InsightGrid({ insights }: { insights: SavedInsight[] }) {
  return (
    <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
      {insights.map((saved) => (
        <Card key={saved.id} className="hover:shadow-md transition-shadow group">
          <CardHeader>
            <div className="flex justify-between items-start">
              <CardTitle className="text-lg line-clamp-2">
                {saved.insight?.problem_statement || 'Insight'}
              </CardTitle>
              <Badge variant="secondary">{saved.status}</Badge>
            </div>
            <CardDescription className="line-clamp-2">
              {saved.insight?.proposed_solution || ''}
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="flex justify-between items-center">
              <span className="text-xs text-muted-foreground">
                Saved {new Date(saved.saved_at).toLocaleDateString()}
              </span>
              <Link href={`/insights/${saved.insight_id}/chat`}>
                <Button size="sm" className="gap-1">
                  <MessageSquare className="h-4 w-4" />
                  Chat
                  <ArrowRight className="h-3 w-3 opacity-0 group-hover:opacity-100 transition-opacity" />
                </Button>
              </Link>
            </div>
          </CardContent>
        </Card>
      ))}
    </div>
  );
}

function EmptyState() {
  return (
    <Card>
      <CardContent className="p-12">
        <div className="text-center">
          <MessageSquare className="h-16 w-16 mx-auto text-muted-foreground mb-4" />
          <h3 className="text-lg font-semibold mb-2">No saved insights yet</h3>
          <p className="text-muted-foreground mb-6 max-w-md mx-auto">
            Save insights you&apos;re interested in, then come back here to chat with AI about strategy, pricing, go-to-market plans, and more.
          </p>
          <Link href="/insights">
            <Button className="gap-2">
              <Search className="h-4 w-4" />
              Browse Insights
            </Button>
          </Link>
        </div>
      </CardContent>
    </Card>
  );
}
