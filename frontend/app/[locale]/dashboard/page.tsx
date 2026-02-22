'use client';

import { useEffect, useState } from 'react';
import { useRouter, useSearchParams } from 'next/navigation';
import Link from 'next/link';
import { useQuery } from '@tanstack/react-query';
import { Loader2, Bookmark, Star, Search, CreditCard, Hammer, Sparkles } from 'lucide-react';
import { getSupabaseClient } from '@/lib/supabase/client';
import { fetchWorkspaceStatus, fetchSubscriptionStatus } from '@/lib/api';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Progress } from '@/components/ui/progress';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Separator } from '@/components/ui/separator';
import { Textarea } from '@/components/ui/textarea';
import { TierBadge } from '@/components/ui/TierBadge';
import { BuilderPlatformGrid, BUILDER_PLATFORMS, type BuilderPlatformId } from '@/components/builder/builder-platform-card';
import { PromptTypeSelector, PROMPT_TYPES, type PromptTypeId } from '@/components/builder/prompt-type-selector';
import { PromptPreviewModal } from '@/components/builder/prompt-preview-modal';
import { OnboardingBanner } from '@/components/onboarding-banner';
import type { User } from '@supabase/supabase-js';

export default function DashboardPage() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const activeTab = searchParams.get('tab') === 'builder' ? 'builder' : 'overview';
  const [user, setUser] = useState<User | null>(null);
  const [accessToken, setAccessToken] = useState<string | null>(null);
  const [isCheckingAuth, setIsCheckingAuth] = useState(true);

  // Builder tab state
  const [selectedPlatform, setSelectedPlatform] = useState<BuilderPlatformId | null>(null);
  const [selectedPromptType, setSelectedPromptType] = useState<PromptTypeId>('landing_page');
  const [ideaDescription, setIdeaDescription] = useState('');
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [generatedPrompt, setGeneratedPrompt] = useState('');

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

  // Fetch subscription status
  const { data: subscription } = useQuery({
    queryKey: ['subscription', accessToken],
    queryFn: () => fetchSubscriptionStatus(accessToken!),
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

  const handleTabChange = (value: string) => {
    const url = value === 'builder' ? '/dashboard?tab=builder' : '/dashboard';
    router.push(url);
  };

  const handleGeneratePrompt = () => {
    if (!selectedPlatform || !ideaDescription.trim()) return;
    const platform = BUILDER_PLATFORMS[selectedPlatform];
    const prompt = `${platform.promptPrefix}\n\n## Idea Description\n${ideaDescription}\n\nBuild a ${PROMPT_TYPES[selectedPromptType].name.toLowerCase()} for this idea. Include:\n- Modern, responsive design\n- Clear value proposition\n- Professional layout\n- Mobile-friendly`;
    setGeneratedPrompt(prompt);
    setIsModalOpen(true);
  };

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

        <Tabs value={activeTab} onValueChange={handleTabChange}>
          <TabsList className="mb-6">
            <TabsTrigger value="overview">Overview</TabsTrigger>
            <TabsTrigger value="builder" className="gap-2">
              <Hammer className="h-4 w-4" />
              Builder
            </TabsTrigger>
          </TabsList>

          {/* Overview Tab */}
          <TabsContent value="overview">
            {/* First-time user onboarding banner — visible until first insight is saved */}
            <OnboardingBanner insightsSaved={Number(status?.saved_count ?? 0)} />

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
                      Number(status?.saved_count ?? 0)
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
                      Number(status?.ratings_count ?? 0)
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
                  <CreditCard className="h-4 w-4 text-muted-foreground" />
                </CardHeader>
                <CardContent>
                  <div className="text-2xl font-bold capitalize">
                    {subscription?.tier || 'Free'}
                  </div>
                  <p className="text-xs text-muted-foreground">
                    <Link href="/billing" className="text-primary hover:underline">
                      {!subscription?.tier || subscription.tier === 'free' ? 'Upgrade for more features' : 'Manage subscription'}
                    </Link>
                  </p>
                </CardContent>
              </Card>
            </div>

            {/* Your Plan — Usage Card */}
            {subscription && (
              <div className="mb-8">
                <Card>
                  <CardHeader className="pb-3">
                    <div className="flex items-center justify-between">
                      <CardTitle className="text-base font-semibold flex items-center gap-2">
                        Your Plan
                        <TierBadge tier={subscription.tier} />
                      </CardTitle>
                      <Link href="/billing" className="text-xs text-primary hover:underline">
                        {subscription.tier === 'free' ? 'Upgrade' : 'Manage'}
                      </Link>
                    </div>
                  </CardHeader>
                  <CardContent className="space-y-4">
                    {/* Insights Today */}
                    {subscription.limits.insights_per_day !== -1 && (
                      <div>
                        <div className="flex items-center justify-between text-sm mb-1">
                          <span className="text-muted-foreground">Insights today</span>
                          <span className="font-medium tabular-nums">
                            {subscription.usage?.insights_today ?? 0} / {subscription.limits.insights_per_day}
                          </span>
                        </div>
                        <Progress
                          value={
                            subscription.limits.insights_per_day > 0
                              ? Math.min(100, Math.round(((subscription.usage?.insights_today ?? 0) / subscription.limits.insights_per_day) * 100))
                              : 0
                          }
                          className={
                            ((subscription.usage?.insights_today ?? 0) / subscription.limits.insights_per_day) >= 0.8
                              ? '[&>div]:bg-red-500'
                              : ''
                          }
                        />
                      </div>
                    )}
                    {subscription.limits.insights_per_day === -1 && (
                      <div className="flex items-center justify-between text-sm">
                        <span className="text-muted-foreground">Insights per day</span>
                        <span className="font-medium text-green-600 dark:text-green-400">Unlimited</span>
                      </div>
                    )}

                    {/* Research Analyses */}
                    {subscription.limits.analyses_per_month !== -1 && (
                      <div>
                        <div className="flex items-center justify-between text-sm mb-1">
                          <span className="text-muted-foreground">Research analyses this month</span>
                          <span className="font-medium tabular-nums">
                            {subscription.usage?.analyses_this_month ?? 0} / {subscription.limits.analyses_per_month}
                          </span>
                        </div>
                        <Progress
                          value={
                            subscription.limits.analyses_per_month > 0
                              ? Math.min(100, Math.round(((subscription.usage?.analyses_this_month ?? 0) / subscription.limits.analyses_per_month) * 100))
                              : 0
                          }
                          className={
                            ((subscription.usage?.analyses_this_month ?? 0) / subscription.limits.analyses_per_month) >= 0.8
                              ? '[&>div]:bg-red-500'
                              : ''
                          }
                        />
                      </div>
                    )}
                    {subscription.limits.analyses_per_month === -1 && (
                      <div className="flex items-center justify-between text-sm">
                        <span className="text-muted-foreground">Research analyses per month</span>
                        <span className="font-medium text-green-600 dark:text-green-400">Unlimited</span>
                      </div>
                    )}
                  </CardContent>
                </Card>
              </div>
            )}

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
                      <p className="mb-3">No recent activity yet. Save insights to see your progress here.</p>
                      <Link
                        href="/insights?sort=top"
                        className="inline-flex items-center gap-2 px-4 py-2 bg-primary text-primary-foreground rounded-md text-sm font-medium hover:opacity-90 transition-opacity"
                      >
                        Browse Today&apos;s Top Ideas →
                      </Link>
                    </div>
                  )}
                </CardContent>
              </Card>
            </div>
          </TabsContent>

          {/* Builder Tab */}
          <TabsContent value="builder">
            <Card>
              <CardHeader>
                <div className="flex items-center gap-2">
                  <Hammer className="h-5 w-5 text-muted-foreground" />
                  <CardTitle className="text-lg">Build Your Idea</CardTitle>
                  <span className="inline-flex items-center rounded-full border px-2.5 py-0.5 text-xs font-semibold bg-secondary text-secondary-foreground ml-2">
                    <Sparkles className="h-3 w-3 mr-1" />
                    AI-Powered
                  </span>
                </div>
                <p className="text-sm text-muted-foreground">
                  Describe your startup idea, pick a builder platform, and generate a ready-to-use prompt.
                </p>
              </CardHeader>
              <CardContent className="space-y-6">
                {/* Step 1: Describe Idea */}
                <div className="space-y-3">
                  <h4 className="text-sm font-medium flex items-center gap-2">
                    <span className="flex items-center justify-center w-5 h-5 rounded-full bg-primary text-primary-foreground text-xs">1</span>
                    Describe Your Idea
                  </h4>
                  <Textarea
                    placeholder="e.g. An app that helps freelancers track invoices and automatically send payment reminders to clients..."
                    value={ideaDescription}
                    onChange={(e) => setIdeaDescription(e.target.value)}
                    rows={4}
                    className="resize-none"
                  />
                </div>

                <Separator />

                {/* Step 2: Select Platform */}
                <div className="space-y-3">
                  <h4 className="text-sm font-medium flex items-center gap-2">
                    <span className="flex items-center justify-center w-5 h-5 rounded-full bg-primary text-primary-foreground text-xs">2</span>
                    Choose Builder Platform
                  </h4>
                  <BuilderPlatformGrid
                    selectedPlatform={selectedPlatform}
                    onSelect={setSelectedPlatform}
                    size="md"
                  />
                </div>

                <Separator />

                {/* Step 3: Select What to Build */}
                <div className="space-y-3">
                  <h4 className="text-sm font-medium flex items-center gap-2">
                    <span className="flex items-center justify-center w-5 h-5 rounded-full bg-primary text-primary-foreground text-xs">3</span>
                    Select What to Build
                  </h4>
                  <PromptTypeSelector
                    value={selectedPromptType}
                    onChange={setSelectedPromptType}
                    className="w-full sm:w-[300px]"
                  />
                </div>

                <Separator />

                {/* Step 4: Generate */}
                <div className="space-y-3">
                  <h4 className="text-sm font-medium flex items-center gap-2">
                    <span className="flex items-center justify-center w-5 h-5 rounded-full bg-primary text-primary-foreground text-xs">4</span>
                    Generate Prompt & Build
                  </h4>
                  <div className="flex flex-wrap items-center gap-3">
                    <Button
                      onClick={handleGeneratePrompt}
                      disabled={!selectedPlatform || !ideaDescription.trim()}
                      className="gap-2"
                    >
                      <Sparkles className="h-4 w-4" />
                      Generate {PROMPT_TYPES[selectedPromptType].name} Prompt
                    </Button>
                    {(!selectedPlatform || !ideaDescription.trim()) && (
                      <span className="text-sm text-muted-foreground">
                        {!ideaDescription.trim() ? 'Describe your idea first' : 'Select a platform first'}
                      </span>
                    )}
                  </div>
                </div>

                {/* Quick Stats */}
                <div className="pt-4 border-t">
                  <div className="grid grid-cols-3 gap-4 text-center">
                    <div>
                      <div className="text-lg font-bold text-primary">5</div>
                      <div className="text-xs text-muted-foreground">Builder Platforms</div>
                    </div>
                    <div>
                      <div className="text-lg font-bold text-primary">4</div>
                      <div className="text-xs text-muted-foreground">Output Types</div>
                    </div>
                    <div>
                      <div className="text-lg font-bold text-primary">1-Click</div>
                      <div className="text-xs text-muted-foreground">To Build</div>
                    </div>
                  </div>
                </div>
              </CardContent>
            </Card>

            {/* Prompt Preview Modal */}
            {selectedPlatform && (
              <PromptPreviewModal
                isOpen={isModalOpen}
                onClose={() => setIsModalOpen(false)}
                prompt={generatedPrompt}
                platformId={selectedPlatform}
                promptType={selectedPromptType}
              />
            )}
          </TabsContent>
        </Tabs>
      </div>
    </div>
  );
}
