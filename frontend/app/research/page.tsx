'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Textarea } from '@/components/ui/textarea';
import { Input } from '@/components/ui/input';

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
      const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
      const response = await fetch(`${apiUrl}/api/research/analyze`, {
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
          <button
            onClick={() => setInputType('idea')}
            className={`p-4 rounded-lg border-2 text-left transition-colors ${
              inputType === 'idea'
                ? 'border-primary bg-primary/5'
                : 'border-muted hover:border-muted-foreground/50'
            }`}
          >
            <svg
              xmlns="http://www.w3.org/2000/svg"
              className="h-6 w-6 mb-2"
              fill="none"
              viewBox="0 0 24 24"
              stroke="currentColor"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z"
              />
            </svg>
            <p className="font-semibold">Business Idea</p>
            <p className="text-sm text-muted-foreground">Analyze your startup concept</p>
          </button>

          <button
            onClick={() => setInputType('url')}
            className={`p-4 rounded-lg border-2 text-left transition-colors ${
              inputType === 'url'
                ? 'border-primary bg-primary/5'
                : 'border-muted hover:border-muted-foreground/50'
            }`}
          >
            <svg
              xmlns="http://www.w3.org/2000/svg"
              className="h-6 w-6 mb-2"
              fill="none"
              viewBox="0 0 24 24"
              stroke="currentColor"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M13.828 10.172a4 4 0 00-5.656 0l-4 4a4 4 0 105.656 5.656l1.102-1.101m-.758-4.899a4 4 0 005.656 0l4-4a4 4 0 00-5.656-5.656l-1.1 1.1"
              />
            </svg>
            <p className="font-semibold">Website URL</p>
            <p className="text-sm text-muted-foreground">Analyze an existing product</p>
          </button>

          <button
            onClick={() => setInputType('competitor')}
            className={`p-4 rounded-lg border-2 text-left transition-colors ${
              inputType === 'competitor'
                ? 'border-primary bg-primary/5'
                : 'border-muted hover:border-muted-foreground/50'
            }`}
          >
            <svg
              xmlns="http://www.w3.org/2000/svg"
              className="h-6 w-6 mb-2"
              fill="none"
              viewBox="0 0 24 24"
              stroke="currentColor"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z"
              />
            </svg>
            <p className="font-semibold">Competitor Analysis</p>
            <p className="text-sm text-muted-foreground">Compare with competitors</p>
          </button>
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
                    <svg
                      className="animate-spin -ml-1 mr-3 h-5 w-5"
                      xmlns="http://www.w3.org/2000/svg"
                      fill="none"
                      viewBox="0 0 24 24"
                    >
                      <circle
                        className="opacity-25"
                        cx="12"
                        cy="12"
                        r="10"
                        stroke="currentColor"
                        strokeWidth="4"
                      ></circle>
                      <path
                        className="opacity-75"
                        fill="currentColor"
                        d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
                      ></path>
                    </svg>
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
