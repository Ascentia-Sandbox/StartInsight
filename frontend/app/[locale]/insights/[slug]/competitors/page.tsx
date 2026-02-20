'use client';

import { useState, useEffect } from 'react';
import { useParams } from 'next/navigation';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Badge } from '@/components/ui/badge';
import { Loader2, TrendingUp, TrendingDown, Target, Lightbulb, Plus, Trash2 } from 'lucide-react';
import { ScatterChart, Scatter, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Legend, ZAxis } from 'recharts';
import Link from 'next/link';
import { toast } from 'sonner';
import { config } from '@/lib/env';

// ============================================================================
// TYPES
// ============================================================================

interface CompetitorProfile {
  id: string;
  name: string;
  url: string;
  description: string | null;
  value_proposition: string | null;
  target_audience: string | null;
  market_position: string | null;
  metrics: {
    pricing?: Record<string, string>;
    team_size?: string;
    funding?: string;
  } | null;
  features: Record<string, boolean> | null;
  strengths: string[] | null;
  weaknesses: string[] | null;
  positioning_x: number | null;
  positioning_y: number | null;
  last_scraped_at: string | null;
  scrape_status: string | null;
  created_at: string;
  updated_at: string;
}

interface CompetitiveIntelligenceReport {
  insight_id: string;
  total_competitors: number;
  competitor_analyses: Array<{
    competitor_id: string;
    strengths: string[];
    weaknesses: string[];
    market_position: string;
    positioning_x: number;
    positioning_y: number;
    differentiation_strategy: string;
  }>;
  market_gap_analysis: {
    gaps: string[];
    opportunities: string[];
    recommended_positioning: string;
  };
  positioning_matrix_description: string;
  executive_summary: string;
  generated_at: string;
}

// ============================================================================
// MAIN COMPONENT
// ============================================================================

export default function CompetitorsPage() {
  const params = useParams();
  const slugParam = params.slug as string;
  const apiUrl = config.apiUrl;

  const [insightId, setInsightId] = useState<string | null>(null);
  const [competitors, setCompetitors] = useState<CompetitorProfile[]>([]);
  const [report, setReport] = useState<CompetitiveIntelligenceReport | null>(null);
  const [loading, setLoading] = useState(true);
  const [analyzing, setAnalyzing] = useState(false);
  const [scraping, setScraping] = useState(false);
  const [competitorUrls, setCompetitorUrls] = useState<string[]>(['', '', '']);

  // Resolve slug to UUID
  useEffect(() => {
    const isUUID = /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i.test(slugParam);
    if (isUUID) {
      setInsightId(slugParam);
    } else {
      fetch(`${apiUrl}/api/insights/by-slug/${slugParam}`)
        .then(res => res.ok ? res.json() : null)
        .then(data => { if (data?.id) setInsightId(data.id); })
        .catch(() => {});
    }
  }, [slugParam, apiUrl]);

  // Fetch competitors once we have the UUID
  useEffect(() => {
    if (insightId) fetchCompetitors();
  }, [insightId]);

  const fetchCompetitors = async () => {
    try {
      const response = await fetch(`${apiUrl}/api/insights/${insightId}/competitors`);
      if (response.ok) {
        const data = await response.json();
        setCompetitors(data);
      }
    } catch (error) {
      console.error('Error fetching competitors:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleScrapeCompetitors = async () => {
    const validUrls = competitorUrls.filter(url => url.trim() !== '');
    if (validUrls.length === 0) {
      toast.error('Please enter at least one competitor URL');
      return;
    }

    setScraping(true);
    try {
      const response = await fetch(`${apiUrl}/api/insights/${insightId}/competitors/scrape`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(validUrls),
      });

      if (response.ok) {
        const data = await response.json();
        toast.success(`Scraped ${data.success_count} competitors successfully!`);
        await fetchCompetitors();
        setCompetitorUrls(['', '', '']);
      } else {
        toast.error('Failed to scrape competitors', {
          description: 'Please try again later'
        });
      }
    } catch (error) {
      console.error('Error scraping competitors:', error);
      toast.error('Failed to scrape competitors', {
        description: 'Please try again later'
      });
    } finally {
      setScraping(false);
    }
  };

  const handleAnalyzeCompetitors = async () => {
    if (competitors.length === 0) {
      toast.error('Please scrape competitors first before analyzing');
      return;
    }

    setAnalyzing(true);
    try {
      const response = await fetch(`${apiUrl}/api/insights/${insightId}/competitors/analyze`, {
        method: 'POST',
      });

      if (response.ok) {
        const data = await response.json();
        setReport(data);
        await fetchCompetitors(); // Refresh competitors with updated analysis
        toast.success('Competitive analysis complete!');
      } else {
        toast.error('Failed to analyze competitors', {
          description: 'Please try again later'
        });
      }
    } catch (error) {
      console.error('Error analyzing competitors:', error);
      toast.error('Failed to analyze competitors', {
        description: 'Please try again later'
      });
    } finally {
      setAnalyzing(false);
    }
  };

  const handleDeleteCompetitor = async (competitorId: string) => {
    if (!confirm('Are you sure you want to delete this competitor?')) {
      return;
    }

    try {
      const response = await fetch(`${apiUrl}/api/insights/${insightId}/competitors/${competitorId}`, {
        method: 'DELETE',
      });

      if (response.ok) {
        await fetchCompetitors();
        toast.success('Competitor deleted successfully');
      } else {
        toast.error('Failed to delete competitor', {
          description: 'Please try again later'
        });
      }
    } catch (error) {
      console.error('Error deleting competitor:', error);
      toast.error('Failed to delete competitor', {
        description: 'Please try again later'
      });
    }
  };

  // Prepare positioning matrix data
  const positioningData = competitors
    .filter(c => c.positioning_x !== null && c.positioning_y !== null)
    .map(c => ({
      name: c.name,
      x: c.positioning_x,
      y: c.positioning_y,
      position: c.market_position,
    }));

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <Loader2 className="h-8 w-8 animate-spin text-primary" />
      </div>
    );
  }

  return (
    <div className="container mx-auto py-8 space-y-8">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold">Competitive Intelligence</h1>
          <p className="text-muted-foreground mt-2">
            Analyze competitors and identify market gaps
          </p>
        </div>
        <Link href={`/insights/${slugParam}`}>
          <Button variant="outline">Back to Insight</Button>
        </Link>
      </div>

      {/* Scrape Competitors Section */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Plus className="h-5 w-5" />
            Add Competitors
          </CardTitle>
          <CardDescription>
            Enter competitor website URLs to scrape and analyze
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            {competitorUrls.map((url, index) => (
              <Input
                key={index}
                placeholder={`Competitor URL ${index + 1}`}
                value={url}
                onChange={(e) => {
                  const newUrls = [...competitorUrls];
                  newUrls[index] = e.target.value;
                  setCompetitorUrls(newUrls);
                }}
              />
            ))}
          </div>
          <div className="flex gap-2">
            <Button onClick={handleScrapeCompetitors} disabled={scraping || analyzing}>
              {scraping && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
              Scrape Competitors
            </Button>
            <Button
              onClick={handleAnalyzeCompetitors}
              disabled={competitors.length === 0 || scraping || analyzing}
              variant="secondary"
            >
              {analyzing && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
              Analyze with AI
            </Button>
          </div>
        </CardContent>
      </Card>

      {/* Executive Summary (after AI analysis) */}
      {report && (
        <Card className="border-primary">
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Lightbulb className="h-5 w-5 text-yellow-500" />
              Executive Summary
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <p className="text-lg">{report.executive_summary}</p>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6 pt-4 border-t">
              <div>
                <h4 className="font-semibold text-sm text-muted-foreground mb-2">Market Gaps</h4>
                <ul className="space-y-2">
                  {report.market_gap_analysis.gaps.map((gap, index) => (
                    <li key={index} className="flex items-start gap-2">
                      <Target className="h-4 w-4 text-blue-500 mt-1 flex-shrink-0" />
                      <span className="text-sm">{gap}</span>
                    </li>
                  ))}
                </ul>
              </div>
              <div>
                <h4 className="font-semibold text-sm text-muted-foreground mb-2">Opportunities</h4>
                <ul className="space-y-2">
                  {report.market_gap_analysis.opportunities.map((opp, index) => (
                    <li key={index} className="flex items-start gap-2">
                      <TrendingUp className="h-4 w-4 text-green-500 mt-1 flex-shrink-0" />
                      <span className="text-sm">{opp}</span>
                    </li>
                  ))}
                </ul>
              </div>
            </div>
            <div className="pt-4 border-t">
              <h4 className="font-semibold text-sm text-muted-foreground mb-2">Recommended Positioning</h4>
              <p className="text-sm bg-muted p-4 rounded-md">
                {report.market_gap_analysis.recommended_positioning}
              </p>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Positioning Matrix */}
      {positioningData.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle>Market Positioning Matrix</CardTitle>
            <CardDescription>Price vs Features (2x2 Matrix)</CardDescription>
          </CardHeader>
          <CardContent>
            <ResponsiveContainer width="100%" height={400}>
              <ScatterChart margin={{ top: 20, right: 20, bottom: 20, left: 20 }}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis
                  type="number"
                  dataKey="x"
                  name="Price"
                  domain={[0, 10]}
                  label={{ value: 'Price (1=Low, 10=High)', position: 'insideBottom', offset: -5 }}
                />
                <YAxis
                  type="number"
                  dataKey="y"
                  name="Features"
                  domain={[0, 10]}
                  label={{ value: 'Features (1=Few, 10=Many)', angle: -90, position: 'insideLeft' }}
                />
                <ZAxis range={[100, 400]} />
                <Tooltip
                  content={({ active, payload }) => {
                    if (active && payload && payload.length) {
                      const data = payload[0].payload;
                      return (
                        <div className="bg-card border rounded-lg p-3 shadow-lg">
                          <p className="font-semibold">{data.name}</p>
                          <p className="text-sm text-muted-foreground">Price: {data.x}/10</p>
                          <p className="text-sm text-muted-foreground">Features: {data.y}/10</p>
                          <p className="text-sm">
                            <Badge variant="secondary">{data.position}</Badge>
                          </p>
                        </div>
                      );
                    }
                    return null;
                  }}
                />
                <Legend />
                <Scatter name="Competitors" data={positioningData} fill="#6366f1" />
              </ScatterChart>
            </ResponsiveContainer>
            {report && (
              <p className="text-sm text-muted-foreground mt-4 text-center">
                {report.positioning_matrix_description}
              </p>
            )}
          </CardContent>
        </Card>
      )}

      {/* Competitor List */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {competitors.map((competitor) => (
          <Card key={competitor.id} className="hover:shadow-lg transition-shadow">
            <CardHeader>
              <div className="flex items-start justify-between">
                <div className="flex-1">
                  <CardTitle className="text-lg">{competitor.name}</CardTitle>
                  <a
                    href={competitor.url}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="text-sm text-blue-600 hover:underline"
                  >
                    {competitor.url}
                  </a>
                </div>
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={() => handleDeleteCompetitor(competitor.id)}
                >
                  <Trash2 className="h-4 w-4 text-red-500" />
                </Button>
              </div>
              {competitor.market_position && (
                <Badge variant="secondary" className="mt-2">
                  {competitor.market_position}
                </Badge>
              )}
            </CardHeader>
            <CardContent className="space-y-4">
              {competitor.value_proposition && (
                <p className="text-sm text-muted-foreground">
                  {competitor.value_proposition}
                </p>
              )}

              {competitor.metrics?.pricing && (
                <div>
                  <h4 className="font-semibold text-sm mb-2">Pricing</h4>
                  <div className="flex flex-wrap gap-2">
                    {Object.entries(competitor.metrics.pricing).map(([tier, price]) => (
                      <Badge key={tier} variant="outline">
                        {tier}: {price}
                      </Badge>
                    ))}
                  </div>
                </div>
              )}

              {competitor.strengths && competitor.strengths.length > 0 && (
                <div>
                  <h4 className="font-semibold text-sm mb-2 flex items-center gap-1">
                    <TrendingUp className="h-4 w-4 text-green-600" />
                    Strengths
                  </h4>
                  <ul className="space-y-1">
                    {competitor.strengths.map((strength, index) => (
                      <li key={index} className="text-sm text-green-700 dark:text-green-400">
                        • {strength}
                      </li>
                    ))}
                  </ul>
                </div>
              )}

              {competitor.weaknesses && competitor.weaknesses.length > 0 && (
                <div>
                  <h4 className="font-semibold text-sm mb-2 flex items-center gap-1">
                    <TrendingDown className="h-4 w-4 text-red-600" />
                    Weaknesses
                  </h4>
                  <ul className="space-y-1">
                    {competitor.weaknesses.map((weakness, index) => (
                      <li key={index} className="text-sm text-red-700 dark:text-red-400">
                        • {weakness}
                      </li>
                    ))}
                  </ul>
                </div>
              )}

              {competitor.last_scraped_at && (
                <p className="text-xs text-muted-foreground border-t pt-2">
                  Last updated: {new Date(competitor.last_scraped_at).toLocaleDateString()}
                </p>
              )}
            </CardContent>
          </Card>
        ))}
      </div>

      {competitors.length === 0 && (
        <Card>
          <CardContent className="py-12 text-center">
            <p className="text-muted-foreground">
              No competitors added yet. Enter competitor URLs above to get started.
            </p>
          </CardContent>
        </Card>
      )}
    </div>
  );
}
