'use client';

import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { Lightbulb, Link2, BarChart3, Loader2 } from 'lucide-react';
import { getSupabaseClient } from '@/lib/supabase/client';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Textarea } from '@/components/ui/textarea';
import { Input } from '@/components/ui/input';
import { SelectableCard } from '@/components/ui/SelectableCard';
import { createAuthenticatedClient } from '@/lib/api';

type InputType = 'idea' | 'url' | 'competitor';

export default function ResearchPage() {
  const router = useRouter();
  const [accessToken, setAccessToken] = useState<string | null>(null);
  const [isCheckingAuth, setIsCheckingAuth] = useState(true);
  const [inputType, setInputType] = useState<InputType>('idea');
  const [title, setTitle] = useState('');
  const [content, setContent] = useState('');
  const [targetMarket, setTargetMarket] = useState('');
  const [budgetRange, setBudgetRange] = useState('bootstrap');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

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
      setError('Please log in to run research analyses');
      return;
    }

    setLoading(true);
    setError(null);

    try {
      const client = createAuthenticatedClient(accessToken);
      const response = await client.post('/api/research/analyze', {
        idea_description: content,
        target_market: targetMarket || 'General',
        budget_range: budgetRange,
      });

      // Redirect to analysis result page
      router.push(`/research/${response.data.id}`);
    } catch (err) {
      if (err instanceof Error) {
        setError(err.message);
      } else {
        setError('An error occurred while submitting your research request');
      }
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-background">
      <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Header */}
        <div className="mb-8">
          <h1 className="text-3xl font-bold tracking-tight">AI Research Agent</h1>
          <p className="text-muted-foreground mt-2">
            Get comprehensive market analysis powered by AI
          </p>
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
              {inputType === 'idea' &&
                'Provide a detailed description of your startup idea for comprehensive analysis'}
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
                    placeholder="e.g., Small businesses, B2B SaaS"
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
                    <option value="seed">Seed ($10k - $100k)</option>
                    <option value="series_a">Series A ($100k - $1M)</option>
                    <option value="growth">Growth ($1M+)</option>
                  </select>
                </div>
              </div>

              <Button type="submit" className="w-full" disabled={loading}>
                {loading ? (
                  <>
                    <Loader2 className="animate-spin -ml-1 mr-3 h-5 w-5" />
                    Running AI Analysis...
                  </>
                ) : (
                  'Start Research'
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
