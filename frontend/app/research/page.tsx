'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import { Lightbulb, Link2, BarChart3, Loader2 } from 'lucide-react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Textarea } from '@/components/ui/textarea';
import { Input } from '@/components/ui/input';
import { SelectableCard } from '@/components/ui/SelectableCard';
import { API_BASE_URL } from '@/lib/api/config';

type InputType = 'idea' | 'url' | 'competitor';

export default function ResearchPage() {
  const [inputType, setInputType] = useState<InputType>('idea');
  const [title, setTitle] = useState('');
  const [content, setContent] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const router = useRouter();

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError(null);

    try {
      const response = await fetch(`${API_BASE_URL}/api/research/analyze`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          title,
          input_type: inputType,
          input_content: content,
        }),
      });

      if (!response.ok) {
        throw new Error('Failed to submit research request');
      }

      const data = await response.json();
      // Redirect to analysis result page
      router.push(`/research/${data.id}`);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'An error occurred');
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
                <label htmlFor="title" className="text-sm font-medium">
                  Analysis Title
                </label>
                <Input
                  id="title"
                  value={title}
                  onChange={(e) => setTitle(e.target.value)}
                  placeholder="e.g., My SaaS Idea Analysis"
                  required
                />
              </div>

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
                    rows={8}
                    required
                  />
                )}
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
