'use client';

import { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import Link from 'next/link';
import { useQuery } from '@tanstack/react-query';
import { Loader2, Bookmark, Star, Search, Calendar } from 'lucide-react';
import { getSupabaseClient } from '@/lib/supabase/client';
import { fetchWorkspaceStatus } from '@/lib/api';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import type { User } from '@supabase/supabase-js';

export default function DashboardPage() {
  const router = useRouter();
  const [user, setUser] = useState<User | null>(null);
  const [accessToken, setAccessToken] = useState<string | null>(null);
  const [isCheckingAuth, setIsCheckingAuth] = useState(true);

  // Check authentication
  useEffect(() => {
    const checkAuth = async () => {
      const supabase = getSupabaseClient();
      const { data: { session } } = await supabase.auth.getSession();

      if (!session) {
        router.push('/auth/login?redirectTo=/dashboard');
        return;
      }

      setUser(session.user);
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

  if (isCheckingAuth) {
    return (
      <div className="min-h-screen bg-background flex items-center justify-center">
        <div className="text-center">
          <Loader2 className="animate-spin h-8 w-8 text-primary mx-auto" />
          <p className="mt-2 text-muted-foreground">Loading dashboard...</p>
        </div>
      </div>
    );
  }

  const userName = user?.user_metadata?.full_name || user?.email?.split('@')[0] || 'User';

  return (
    <div className="min-h-screen bg-background">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Welcome Section */}
        <div className="mb-8">
          <h1 className="text-3xl font-bold tracking-tight">
            Welcome back, {userName}!
          </h1>
          <p className="text-muted-foreground mt-2">
            Here&apos;s an overview of your StartInsight activity.
          </p>
        </div>

        {/* Quick Stats */}
        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4 mb-8">
          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">Saved Insights</CardTitle>
              <Bookmark className="h-4 w-4 text-muted-foreground" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">
                {statusLoading ? (
                  <Loader2 className="animate-spin h-5 w-5" />
                ) : (
                  status?.saved_count || 0
                )}
              </div>
              <p className="text-xs text-muted-foreground">
                {status?.saved_count === 0 ? 'Start saving insights' : 'In your workspace'}
              </p>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">Rated Insights</CardTitle>
              <Star className="h-4 w-4 text-muted-foreground" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">
                {statusLoading ? (
                  <Loader2 className="animate-spin h-5 w-5" />
                ) : (
                  status?.ratings_count || 0
                )}
              </div>
              <p className="text-xs text-muted-foreground">
                {status?.ratings_count === 0 ? 'Rate insights to improve recommendations' : 'Feedback provided'}
              </p>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">Research Analyses</CardTitle>
              <Search className="h-4 w-4 text-muted-foreground" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">0</div>
              <p className="text-xs text-muted-foreground">
                Run AI-powered market research
              </p>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">Plan</CardTitle>
              <Calendar className="h-4 w-4 text-muted-foreground" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">Free</div>
              <p className="text-xs text-muted-foreground">
                <Link href="/billing" className="text-primary hover:underline">
                  Upgrade for more features
                </Link>
              </p>
            </CardContent>
          </Card>
        </div>

        {/* Quick Actions */}
        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
          <Card>
            <CardHeader>
              <CardTitle>Browse Insights</CardTitle>
              <CardDescription>
                Discover the latest AI-analyzed market opportunities
              </CardDescription>
            </CardHeader>
            <CardContent>
              <Link href="/insights">
                <Button className="w-full">View All Insights</Button>
              </Link>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle>My Workspace</CardTitle>
              <CardDescription>
                View and manage your saved insights
              </CardDescription>
            </CardHeader>
            <CardContent>
              <Link href="/workspace">
                <Button variant="outline" className="w-full">Go to Workspace</Button>
              </Link>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle>Research Agent</CardTitle>
              <CardDescription>
                Run AI-powered analysis on your business ideas
              </CardDescription>
            </CardHeader>
            <CardContent>
              <Link href="/research">
                <Button variant="outline" className="w-full">Start Research</Button>
              </Link>
            </CardContent>
          </Card>
        </div>

        {/* Recent Activity */}
        <div className="mt-8">
          <h2 className="text-xl font-semibold mb-4">Recent Activity</h2>
          <Card>
            <CardContent className="p-6">
              {status && (status.saved_count > 0 || status.ratings_count > 0) ? (
                <div className="space-y-4">
                  {status.saved_count > 0 && (
                    <div className="flex items-center gap-3">
                      <Bookmark className="h-5 w-5 text-primary" />
                      <p>You have <strong>{status.saved_count}</strong> saved insights in your workspace.</p>
                    </div>
                  )}
                  {status.ratings_count > 0 && (
                    <div className="flex items-center gap-3">
                      <Star className="h-5 w-5 text-yellow-500" />
                      <p>You&apos;ve rated <strong>{status.ratings_count}</strong> insights.</p>
                    </div>
                  )}
                  {status.building_count > 0 && (
                    <div className="flex items-center gap-3">
                      <Search className="h-5 w-5 text-green-500" />
                      <p>You&apos;re building <strong>{status.building_count}</strong> ideas.</p>
                    </div>
                  )}
                </div>
              ) : (
                <div className="text-center text-muted-foreground py-8">
                  <p>No recent activity yet.</p>
                  <p className="text-sm mt-2">
                    Start by browsing and saving insights, or run a research analysis.
                  </p>
                </div>
              )}
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  );
}
