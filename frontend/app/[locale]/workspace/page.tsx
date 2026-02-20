'use client';

import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import Link from 'next/link';
import { useQuery } from '@tanstack/react-query';
import { Loader2, Bookmark, Star, Rocket, ExternalLink } from 'lucide-react';
import { getSupabaseClient } from '@/lib/supabase/client';
import { fetchWorkspaceStatus, fetchSavedInsights, fetchUserRatings } from '@/lib/api';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import type { SavedInsight, UserRating } from '@/lib/types';

type TabType = 'saved' | 'ratings' | 'building';

export default function WorkspacePage() {
  const router = useRouter();
  const [activeTab, setActiveTab] = useState<TabType>('saved');
  const [accessToken, setAccessToken] = useState<string | null>(null);
  const [isCheckingAuth, setIsCheckingAuth] = useState(true);

  // Check authentication and get access token
  useEffect(() => {
    const checkAuth = async () => {
      const supabase = getSupabaseClient();
      const { data: { session } } = await supabase.auth.getSession();

      if (!session) {
        router.push('/auth/login?redirectTo=/workspace');
        return;
      }

      setAccessToken(session.access_token);
      setIsCheckingAuth(false);
    };

    checkAuth();
  }, [router]);

  // Fetch workspace status
  const { data: status, isLoading: statusLoading } = useQuery({
    queryKey: ['workspace-status', accessToken],
    queryFn: () => fetchWorkspaceStatus(accessToken!),
    enabled: !!accessToken,
  });

  // Fetch saved insights
  const { data: savedInsights, isLoading: savedLoading } = useQuery({
    queryKey: ['saved-insights', accessToken, activeTab],
    queryFn: () => fetchSavedInsights(accessToken!, {
      status: activeTab === 'building' ? 'building' : activeTab === 'saved' ? undefined : undefined,
      limit: 50,
    }),
    enabled: !!accessToken && (activeTab === 'saved' || activeTab === 'building'),
  });

  // Fetch user ratings
  const { data: ratings, isLoading: ratingsLoading } = useQuery({
    queryKey: ['user-ratings', accessToken],
    queryFn: () => fetchUserRatings(accessToken!, { limit: 50 }),
    enabled: !!accessToken && activeTab === 'ratings',
  });

  if (isCheckingAuth) {
    return (
      <div className="min-h-screen bg-background flex items-center justify-center">
        <div className="text-center">
          <Loader2 className="animate-spin h-8 w-8 text-primary mx-auto" />
          <p className="mt-2 text-muted-foreground">Loading workspace...</p>
        </div>
      </div>
    );
  }

  const isLoading = statusLoading || (activeTab === 'ratings' ? ratingsLoading : savedLoading);

  return (
    <div className="min-h-screen bg-background">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Header */}
        <div className="flex justify-between items-center mb-8">
          <div>
            <h1 className="text-3xl font-bold tracking-tight">My Workspace</h1>
            <p className="text-muted-foreground mt-2">
              Your saved insights and research analyses
            </p>
          </div>
          <Link href="/insights">
            <Button>Browse Insights</Button>
          </Link>
        </div>

        {/* Stats Cards */}
        {status && (
          <div className="grid gap-4 md:grid-cols-4 mb-8">
            <Card>
              <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                <CardTitle className="text-sm font-medium">Saved</CardTitle>
                <Bookmark className="h-4 w-4 text-muted-foreground" />
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold">{status.saved_count}</div>
              </CardContent>
            </Card>
            <Card>
              <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                <CardTitle className="text-sm font-medium">Interested</CardTitle>
                <Star className="h-4 w-4 text-muted-foreground" />
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold">{status.interested_count}</div>
              </CardContent>
            </Card>
            <Card>
              <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                <CardTitle className="text-sm font-medium">Building</CardTitle>
                <Rocket className="h-4 w-4 text-muted-foreground" />
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold">{status.building_count}</div>
              </CardContent>
            </Card>
            <Card>
              <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                <CardTitle className="text-sm font-medium">Rated</CardTitle>
                <Star className="h-4 w-4 text-yellow-500" />
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold">{status.ratings_count}</div>
              </CardContent>
            </Card>
          </div>
        )}

        {/* Tabs */}
        <div className="flex gap-4 border-b mb-8">
          <button
            onClick={() => setActiveTab('saved')}
            className={`pb-2 px-1 border-b-2 font-medium transition-colors ${
              activeTab === 'saved'
                ? 'border-primary text-primary'
                : 'border-transparent text-muted-foreground hover:text-foreground'
            }`}
          >
            Saved Insights
          </button>
          <button
            onClick={() => setActiveTab('ratings')}
            className={`pb-2 px-1 border-b-2 font-medium transition-colors ${
              activeTab === 'ratings'
                ? 'border-primary text-primary'
                : 'border-transparent text-muted-foreground hover:text-foreground'
            }`}
          >
            My Ratings
          </button>
          <button
            onClick={() => setActiveTab('building')}
            className={`pb-2 px-1 border-b-2 font-medium transition-colors ${
              activeTab === 'building'
                ? 'border-primary text-primary'
                : 'border-transparent text-muted-foreground hover:text-foreground'
            }`}
          >
            Building
          </button>
        </div>

        {/* Content */}
        {isLoading ? (
          <div className="flex items-center justify-center py-12">
            <Loader2 className="animate-spin h-8 w-8 text-primary" />
          </div>
        ) : activeTab === 'ratings' ? (
          <RatingsContent ratings={ratings?.items || []} />
        ) : (
          <SavedInsightsContent
            insights={savedInsights?.items || []}
            tab={activeTab}
          />
        )}

        {/* Instructions (when empty) */}
        {!isLoading &&
          ((activeTab !== 'ratings' && (!savedInsights?.items || savedInsights.items.length === 0)) ||
           (activeTab === 'ratings' && (!ratings?.items || ratings.items.length === 0))) && (
          <div className="mt-8 grid gap-4 md:grid-cols-3">
            <Card>
              <CardHeader>
                <CardTitle className="text-lg flex items-center gap-2">
                  <span className="bg-primary text-primary-foreground rounded-full w-6 h-6 flex items-center justify-center text-sm">1</span>
                  Browse Insights
                </CardTitle>
              </CardHeader>
              <CardContent>
                <CardDescription>
                  Explore AI-analyzed market opportunities from Reddit, Product Hunt, and Google Trends.
                </CardDescription>
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle className="text-lg flex items-center gap-2">
                  <span className="bg-primary text-primary-foreground rounded-full w-6 h-6 flex items-center justify-center text-sm">2</span>
                  Save &amp; Rate
                </CardTitle>
              </CardHeader>
              <CardContent>
                <CardDescription>
                  Save insights that interest you and rate them to help improve recommendations.
                </CardDescription>
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle className="text-lg flex items-center gap-2">
                  <span className="bg-primary text-primary-foreground rounded-full w-6 h-6 flex items-center justify-center text-sm">3</span>
                  Research &amp; Build
                </CardTitle>
              </CardHeader>
              <CardContent>
                <CardDescription>
                  Run AI research on your ideas and use build tools to create brand assets.
                </CardDescription>
              </CardContent>
            </Card>
          </div>
        )}
      </div>
    </div>
  );
}

function SavedInsightsContent({ insights, tab }: { insights: SavedInsight[]; tab: TabType }) {
  if (insights.length === 0) {
    return (
      <Card>
        <CardContent className="p-12">
          <div className="text-center">
            {tab === 'building' ? (
              <Rocket className="h-16 w-16 mx-auto text-muted-foreground mb-4" />
            ) : (
              <Bookmark className="h-16 w-16 mx-auto text-muted-foreground mb-4" />
            )}
            <h3 className="text-lg font-semibold mb-2">
              {tab === 'building' ? 'No ideas being built yet' : 'No saved insights yet'}
            </h3>
            <p className="text-muted-foreground mb-6 max-w-sm mx-auto">
              {tab === 'building'
                ? 'Claim an insight to mark it as "building" and track your progress.'
                : 'Start building your workspace by saving insights that interest you.'}
            </p>
            <Link href="/insights">
              <Button>Browse Insights</Button>
            </Link>
          </div>
        </CardContent>
      </Card>
    );
  }

  return (
    <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
      {insights.map((saved) => (
        <Card key={saved.id} className="hover:shadow-md transition-shadow">
          <CardHeader>
            <div className="flex justify-between items-start">
              <CardTitle className="text-lg line-clamp-2">
                {saved.insight?.problem_statement || 'Insight'}
              </CardTitle>
              <Badge variant={saved.status === 'building' ? 'default' : 'secondary'}>
                {saved.status}
              </Badge>
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
              <Link href={`/insights/${saved.insight_id}`}>
                <Button variant="ghost" size="sm">
                  <ExternalLink className="h-4 w-4 mr-1" />
                  View
                </Button>
              </Link>
            </div>
            {saved.notes && (
              <p className="mt-2 text-sm text-muted-foreground border-t pt-2">
                {saved.notes}
              </p>
            )}
          </CardContent>
        </Card>
      ))}
    </div>
  );
}

function RatingsContent({ ratings }: { ratings: UserRating[] }) {
  if (ratings.length === 0) {
    return (
      <Card>
        <CardContent className="p-12">
          <div className="text-center">
            <Star className="h-16 w-16 mx-auto text-muted-foreground mb-4" />
            <h3 className="text-lg font-semibold mb-2">No ratings yet</h3>
            <p className="text-muted-foreground mb-6 max-w-sm mx-auto">
              Rate insights to help improve recommendations and track your preferences.
            </p>
            <Link href="/insights">
              <Button>Browse Insights</Button>
            </Link>
          </div>
        </CardContent>
      </Card>
    );
  }

  return (
    <div className="space-y-4">
      {ratings.map((rating) => (
        <Card key={rating.id}>
          <CardHeader className="flex flex-row items-center justify-between space-y-0">
            <div>
              <CardTitle className="text-base">Insight Rating</CardTitle>
              <CardDescription>
                Rated {new Date(rating.rated_at).toLocaleDateString()}
              </CardDescription>
            </div>
            <div className="flex items-center gap-1">
              {[1, 2, 3, 4, 5].map((star) => (
                <Star
                  key={star}
                  className={`h-5 w-5 ${
                    star <= rating.rating
                      ? 'fill-yellow-400 text-yellow-400'
                      : 'text-muted-foreground'
                  }`}
                />
              ))}
            </div>
          </CardHeader>
          {rating.feedback && (
            <CardContent>
              <p className="text-sm text-muted-foreground">{rating.feedback}</p>
            </CardContent>
          )}
          <CardContent className="pt-0">
            <Link href={`/insights/${rating.insight_id}`}>
              <Button variant="ghost" size="sm">
                <ExternalLink className="h-4 w-4 mr-1" />
                View Insight
              </Button>
            </Link>
          </CardContent>
        </Card>
      ))}
    </div>
  );
}
