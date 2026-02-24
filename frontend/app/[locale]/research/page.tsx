'use client';

import { useState, useEffect } from 'react';
import { useRouter, useSearchParams } from 'next/navigation';
import Link from 'next/link';
import { Lightbulb, Link2, BarChart3, Loader2, CheckCircle, Clock } from 'lucide-react';
import { getSupabaseClient } from '@/lib/supabase/client';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Progress } from '@/components/ui/progress';
import { Textarea } from '@/components/ui/textarea';
import { Input } from '@/components/ui/input';
import { Badge } from '@/components/ui/badge';
import { SelectableCard } from '@/components/ui/SelectableCard';
import { toast } from 'sonner';
import { createResearchRequest, fetchInsightById } from '@/lib/api';
import { useSubscription } from '@/hooks/useSubscription';
import { Breadcrumbs } from '@/components/ui/breadcrumbs';

type InputType = 'idea' | 'url' | 'competitor';

export default function ResearchPage() {
  const router = useRouter();
  const [accessToken, setAccessToken] = useState<string | null>(null);
  const [isCheckingAuth, setIsCheckingAuth] = useState(true);
  const [inputType, setInputType] = useState<InputType>('idea');
  const [content, setContent] = useState('');
  const [targetMarket, setTargetMarket] = useState('');
  const [budgetRange, setBudgetRange] = useState('bootstrap');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState(false);

  const searchParams = useSearchParams();
  const { tier, limits, usage, atLimit, usagePercent } = useSubscription();

  // Check authentication
  useEffect(() => {
    const checkAuth = async () => {
      const supabase = getSupabaseClient();
      const { data: { session } } = await supabase.auth.getSession();

      if (!session) {
        router.push('/auth/login?redirectTo=/research');
        return;
      }

      setAccessToken(session.access_token);
      setIsCheckingAuth(false);
    };

    checkAuth();
  }, [router]);

  // Pre-fill from query params (e.g. from /validate Deep Research button)
  useEffect(() => {
    const idea = searchParams.get('idea');
    const market = searchParams.get('market');
    const insightId = searchParams.get('insight_id');
    if (idea) setContent(idea);
    if (market) setTargetMarket(market);
    // When linked from insight detail page, fetch insight and pre-fill
    if (insightId && !idea) {
      fetchInsightById(insightId)
        .then((insight) => {
          const parts = [
            insight.proposed_solution,
            insight.problem_statement,
          ].filter(Boolean);
          if (parts.length > 0) setContent(parts.join('\n\n'));
        })
        .catch(() => {});
    }
  }, [searchParams]);

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

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!accessToken) {
      setError('Please log in to submit research requests');
      return;
    }

    // Frontend validation matching backend min_length requirements
    if (content.trim().length < 50) {
      setError('Please provide a more detailed description (at least 50 characters).');
      toast.error('Description too short');
      return;
    }

    const market = targetMarket || 'General Market';
    if (market.trim().length < 10) {
      setError('Target market must be at least 10 characters.');
      toast.error('Target market too short');
      return;
    }

    setLoading(true);
    setError(null);
    setSuccess(false);

    try {
      const request = await createResearchRequest(accessToken, {
        idea_description: content,
        target_market: market,
        budget_range: budgetRange,
      });

      // Show success message
      setSuccess(true);
      setContent('');
      setTargetMarket('');
      toast.success('Research request submitted successfully');

      // If auto-approved (paid tiers), redirect to analysis
      if (request.status === 'approved' && request.analysis_id) {
        setTimeout(() => {
          router.push(`/research/${request.analysis_id}`);
        }, 2000);
      }
    } catch (err: any) {
      if (err?.response?.status === 429) {
        setError('Monthly quota exceeded. Upgrade your plan to submit more research requests.');
        toast.error('Monthly quota exceeded');
      } else if (err instanceof Error) {
        setError(err.message);
        toast.error('Failed to submit research request');
      } else {
        setError('An error occurred while submitting your research request');
        toast.error('Failed to submit research request');
      }
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-background">
      <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <Breadcrumbs items={[{ label: 'Research' }]} />
        {/* Header */}
        <div className="mb-8">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-3xl font-bold tracking-tight">AI Research Agent</h1>
              <p className="text-muted-foreground mt-2">
                Get comprehensive market analysis powered by AI
              </p>
            </div>
            <div className="flex flex-col items-end gap-2 min-w-[180px]">
              {tier === 'free' ? (
                <Badge variant="secondary" className="text-sm">
                  <Clock className="h-3 w-3 mr-1" />
                  Manual Approval
                </Badge>
              ) : (
                <Badge variant="default" className="text-sm">
                  <CheckCircle className="h-3 w-3 mr-1" />
                  Auto-Approved
                </Badge>
              )}
              {/* Quota progress bar */}
              {limits.analyses_per_month !== undefined && limits.analyses_per_month !== -1 && (
                <div className="w-full">
                  <div className="flex justify-between text-xs text-muted-foreground mb-1">
                    <span>Monthly quota</span>
                    <span className="tabular-nums">{usage.analyses_this_month} / {limits.analyses_per_month}</span>
                  </div>
                  <Progress
                    value={usagePercent('analyses_this_month')}
                    className={usagePercent('analyses_this_month') >= 80 ? '[&>div]:bg-red-500' : ''}
                  />
                </div>
              )}
              {limits.analyses_per_month === -1 && (
                <span className="text-xs text-green-600 dark:text-green-400 font-medium">Unlimited analyses</span>
              )}
            </div>
          </div>
        </div>

        {/* Input Type Selection */}
        <div className="grid grid-cols-3 gap-4 mb-8">
          <SelectableCard
            title="Business Idea"
            description="Analyze your startup concept"
            icon={<Lightbulb className="h-6 w-6" />}
            selected={inputType === 'idea'}
            onClick={() => setInputType('idea')}
          />
          <SelectableCard
            title="Website URL"
            description="Analyze an existing product"
            icon={<Link2 className="h-6 w-6" />}
            selected={inputType === 'url'}
            onClick={() => setInputType('url')}
          />
          <SelectableCard
            title="Competitor Analysis"
            description="Compare with competitors"
            icon={<BarChart3 className="h-6 w-6" />}
            selected={inputType === 'competitor'}
            onClick={() => setInputType('competitor')}
          />
        </div>

        {/* Research Form */}
        <Card>
          <CardHeader>
            <CardTitle>
              {inputType === 'idea' && 'Describe Your Business Idea'}
              {inputType === 'url' && 'Enter Product URL'}
              {inputType === 'competitor' && 'Enter Competitor Details'}
            </CardTitle>
            <CardDescription>
              {inputType === 'idea' && (
                <>
                  Provide a detailed description of your startup idea for comprehensive analysis.{' '}
                  {tier === 'free' && 'Requires admin approval (1 request/month).'}
                  {tier === 'starter' && 'Auto-approved (3 requests/month).'}
                  {tier === 'pro' && 'Auto-approved (10 requests/month).'}
                  {tier === 'enterprise' && 'Auto-approved (100 requests/month).'}
                </>
              )}
              {inputType === 'url' &&
                'We will scrape and analyze the product page to provide insights'}
              {inputType === 'competitor' &&
                'List your competitors and your product for comparison analysis'}
            </CardDescription>
          </CardHeader>
          <CardContent>
            <form onSubmit={handleSubmit} className="space-y-4">
              {error && (
                <div className="bg-red-50 dark:bg-red-900/20 text-red-600 dark:text-red-400 p-3 rounded-md text-sm">
                  {error}
                </div>
              )}

              {success && (
                <div className="bg-green-50 dark:bg-green-900/20 text-green-600 dark:text-green-400 p-3 rounded-md text-sm">
                  <div className="flex items-center gap-2">
                    <CheckCircle className="h-4 w-4" />
                    <span>
                      {tier === 'free'
                        ? 'Research request submitted! Admin will review shortly (typically within 24 hours).'
                        : 'Research request submitted and auto-approved! Analysis starting now...'}
                    </span>
                  </div>
                </div>
              )}

              <div className="space-y-2">
                <label htmlFor="content" className="text-sm font-medium">
                  {inputType === 'idea' && 'Business Idea Description'}
                  {inputType === 'url' && 'Product URL'}
                  {inputType === 'competitor' && 'Competitor Information'}
                </label>
                {inputType === 'url' ? (
                  <Input
                    id="content"
                    type="url"
                    value={content}
                    onChange={(e) => setContent(e.target.value)}
                    placeholder="https://example.com/product"
                    required
                  />
                ) : (
                  <Textarea
                    id="content"
                    value={content}
                    onChange={(e) => setContent(e.target.value)}
                    placeholder={
                      inputType === 'idea'
                        ? 'Describe your business idea in detail. Include the problem you are solving, your target audience, and how you plan to monetize...'
                        : 'List your competitors (one per line) and describe your own product for comparison...'
                    }
                    rows={6}
                    required
                  />
                )}
                {content.length > 0 && content.length < 50 && (
                  <p className="text-xs text-muted-foreground">{content.length}/50 characters minimum</p>
                )}
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div className="space-y-2">
                  <label htmlFor="targetMarket" className="text-sm font-medium">
                    Target Market
                  </label>
                  <Input
                    id="targetMarket"
                    value={targetMarket}
                    onChange={(e) => setTargetMarket(e.target.value)}
                    placeholder="e.g., Small business owners, B2B SaaS companies (min 10 chars)"
                  />
                </div>

                <div className="space-y-2">
                  <label htmlFor="budgetRange" className="text-sm font-medium">
                    Budget Range
                  </label>
                  <select
                    id="budgetRange"
                    value={budgetRange}
                    onChange={(e) => setBudgetRange(e.target.value)}
                    className="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background file:border-0 file:bg-transparent file:text-sm file:font-medium placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50"
                  >
                    <option value="bootstrap">Bootstrap ($0 - $10k)</option>
                    <option value="10k-50k">Seed ($10k - $50k)</option>
                    <option value="50k-200k">Series A ($50k - $200k)</option>
                    <option value="200k+">Growth ($200k+)</option>
                  </select>
                </div>
              </div>

              {atLimit('analyses_this_month') && (
                <div className="rounded-md border border-amber-200 bg-amber-50 dark:bg-amber-900/20 dark:border-amber-800 p-3 text-sm">
                  <p className="font-medium text-amber-800 dark:text-amber-200">Monthly quota reached</p>
                  <p className="text-amber-700 dark:text-amber-300 mt-0.5">
                    You have used all your research analyses for this month.{' '}
                    <Link href="/billing" className="underline font-medium">
                      Upgrade your plan
                    </Link>{' '}
                    to get more.
                  </p>
                </div>
              )}
              <Button
                type="submit"
                className="w-full"
                disabled={loading || success || atLimit('analyses_this_month')}
              >
                {loading ? (
                  <>
                    <Loader2 className="animate-spin -ml-1 mr-3 h-5 w-5" />
                    Submitting Request...
                  </>
                ) : success ? (
                  <>
                    <CheckCircle className="-ml-1 mr-3 h-5 w-5" />
                    Request Submitted
                  </>
                ) : (
                  'Submit Research Request'
                )}
              </Button>
            </form>
          </CardContent>
        </Card>

        {/* What You Get */}
        <div className="mt-8 grid gap-4 md:grid-cols-3">
          <Card>
            <CardHeader>
              <CardTitle className="text-lg">Market Analysis</CardTitle>
            </CardHeader>
            <CardContent>
              <CardDescription>
                TAM/SAM/SOM estimates, market trends, and growth projections
              </CardDescription>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle className="text-lg">Competitive Landscape</CardTitle>
            </CardHeader>
            <CardContent>
              <CardDescription>
                Detailed competitor analysis with positioning and differentiation opportunities
              </CardDescription>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle className="text-lg">Go-to-Market Strategy</CardTitle>
            </CardHeader>
            <CardContent>
              <CardDescription>
                Recommended channels, pricing strategy, and launch tactics
              </CardDescription>
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  );
}
