'use client';

import { useQuery } from '@tanstack/react-query';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Skeleton } from '@/components/ui/skeleton';
import {
  Activity, Radio, TrendingUp, Zap, BarChart3, Globe,
} from 'lucide-react';
import { config } from '@/lib/env';

interface TrendingKeyword {
  keyword: string;
  volume?: string;
  growth?: string;
}

interface PulseData {
  signals_24h: number;
  insights_24h: number;
  total_insights: number;
  trending_keywords: TrendingKeyword[];
  hottest_markets: string[];
  top_sources: Record<string, number>;
  last_updated: string;
}

const sourceColors: Record<string, string> = {
  reddit: 'bg-orange-100 text-orange-700 dark:bg-orange-900/40 dark:text-orange-300',
  product_hunt: 'bg-red-100 text-red-700 dark:bg-red-900/40 dark:text-red-300',
  hacker_news: 'bg-amber-100 text-amber-700 dark:bg-amber-900/40 dark:text-amber-300',
  twitter: 'bg-sky-100 text-sky-700 dark:bg-sky-900/40 dark:text-sky-300',
  google_trends: 'bg-blue-100 text-blue-700 dark:bg-blue-900/40 dark:text-blue-300',
};

export default function PulsePage() {
  const { data, isLoading, error } = useQuery<PulseData>({
    queryKey: ['market-pulse'],
    queryFn: async () => {
      const res = await fetch(`${config.apiUrl}/api/pulse`);
      if (!res.ok) throw new Error('Failed to fetch pulse data');
      return res.json();
    },
    refetchInterval: 60000, // Auto-refresh every 60 seconds
    retry: 2,
  });

  return (
    <div className="min-h-screen">
      {/* Hero */}
      <section className="hero-gradient py-16 px-6">
        <div className="max-w-5xl mx-auto text-center">
          <div className="flex items-center justify-center gap-2 mb-4">
            <Radio className="h-5 w-5 text-green-500 animate-pulse" />
            <span className="text-sm font-medium text-muted-foreground uppercase tracking-wider">Live</span>
          </div>
          <h1 className="text-4xl md:text-5xl font-bold mb-3">Market Pulse</h1>
          <p className="text-lg text-muted-foreground max-w-2xl mx-auto">
            Real-time startup signal intelligence. Updated every 60 seconds from Reddit, Product Hunt, Hacker News, Twitter, and Google Trends.
          </p>
        </div>
      </section>

      <div className="max-w-5xl mx-auto px-6 py-10 space-y-8">
        {isLoading ? (
          <div className="grid gap-4 md:grid-cols-3">
            {[...Array(3)].map((_, i) => (
              <Skeleton key={i} className="h-32" />
            ))}
          </div>
        ) : error ? (
          <Card>
            <CardContent className="p-8 text-center text-muted-foreground">
              <Activity className="h-10 w-10 mx-auto mb-3 opacity-50" />
              <p>Unable to load pulse data. Backend may be starting up.</p>
            </CardContent>
          </Card>
        ) : data ? (
          <>
            {/* Key Metrics */}
            <div className="grid gap-4 md:grid-cols-3">
              <Card>
                <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                  <CardTitle className="text-sm font-medium">Signals (24h)</CardTitle>
                  <Activity className="h-4 w-4 text-muted-foreground" />
                </CardHeader>
                <CardContent>
                  <div className="text-3xl font-bold">{data.signals_24h.toLocaleString()}</div>
                  <p className="text-xs text-muted-foreground mt-1">Raw signals collected from all sources</p>
                </CardContent>
              </Card>
              <Card>
                <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                  <CardTitle className="text-sm font-medium">Insights (24h)</CardTitle>
                  <Zap className="h-4 w-4 text-muted-foreground" />
                </CardHeader>
                <CardContent>
                  <div className="text-3xl font-bold">{data.insights_24h.toLocaleString()}</div>
                  <p className="text-xs text-muted-foreground mt-1">AI-analyzed startup opportunities</p>
                </CardContent>
              </Card>
              <Card>
                <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                  <CardTitle className="text-sm font-medium">Total Insights</CardTitle>
                  <BarChart3 className="h-4 w-4 text-muted-foreground" />
                </CardHeader>
                <CardContent>
                  <div className="text-3xl font-bold">{data.total_insights.toLocaleString()}</div>
                  <p className="text-xs text-muted-foreground mt-1">Cumulative insight database</p>
                </CardContent>
              </Card>
            </div>

            {/* Trending Keywords + Sources */}
            <div className="grid gap-6 md:grid-cols-2">
              {/* Trending Keywords */}
              <Card>
                <CardHeader>
                  <CardTitle className="flex items-center gap-2">
                    <TrendingUp className="h-5 w-5 text-green-600" />
                    Trending Keywords
                  </CardTitle>
                  <CardDescription>Most active search terms from recent insights</CardDescription>
                </CardHeader>
                <CardContent>
                  {data.trending_keywords.length > 0 ? (
                    <div className="space-y-2">
                      {data.trending_keywords.map((kw, idx) => (
                        <div key={idx} className="flex items-center justify-between py-1.5">
                          <span className="text-sm font-medium">{kw.keyword}</span>
                          <div className="flex items-center gap-2">
                            {kw.volume && <span className="text-xs text-muted-foreground">{kw.volume}</span>}
                            {kw.growth && (
                              <Badge variant="outline" className="text-xs text-green-600 border-green-200">
                                {kw.growth}
                              </Badge>
                            )}
                          </div>
                        </div>
                      ))}
                    </div>
                  ) : (
                    <p className="text-sm text-muted-foreground py-4 text-center">No trending keywords yet</p>
                  )}
                </CardContent>
              </Card>

              {/* Signal Sources */}
              <Card>
                <CardHeader>
                  <CardTitle className="flex items-center gap-2">
                    <Globe className="h-5 w-5 text-blue-600" />
                    Signal Sources (24h)
                  </CardTitle>
                  <CardDescription>Signals collected by platform</CardDescription>
                </CardHeader>
                <CardContent>
                  {Object.keys(data.top_sources).length > 0 ? (
                    <div className="space-y-3">
                      {Object.entries(data.top_sources).map(([source, count]) => (
                        <div key={source} className="flex items-center justify-between">
                          <Badge className={sourceColors[source] || 'bg-gray-100 text-gray-700'}>
                            {source.replace('_', ' ')}
                          </Badge>
                          <div className="flex items-center gap-2">
                            <div className="w-24 h-2 bg-muted rounded-full overflow-hidden">
                              <div
                                className="h-full bg-primary rounded-full"
                                style={{ width: `${Math.min(100, (count / Math.max(...Object.values(data.top_sources))) * 100)}%` }}
                              />
                            </div>
                            <span className="text-sm font-medium w-8 text-right">{count}</span>
                          </div>
                        </div>
                      ))}
                    </div>
                  ) : (
                    <p className="text-sm text-muted-foreground py-4 text-center">No signals collected yet</p>
                  )}
                </CardContent>
              </Card>
            </div>

            {/* Last updated */}
            <div className="text-center text-xs text-muted-foreground">
              Last updated: {new Date(data.last_updated).toLocaleString()} — Auto-refreshes every 60s
            </div>
          </>
        ) : null}
      </div>
    </div>
  );
}
