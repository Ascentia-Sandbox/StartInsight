'use client';

import { useEffect, useState } from 'react';
import { useParams } from 'next/navigation';
import Link from 'next/link';
import { ArrowLeft, TrendingUp, TrendingDown, Zap } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Card, CardContent } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Skeleton } from '@/components/ui/skeleton';
import { config } from '@/lib/env';
import { TrendChart } from '@/components/trend-chart';

interface TrendDetail {
  id: string;
  keyword: string;
  category: string;
  search_volume: number;
  growth_percentage: number;
  business_implications: string;
  trend_data: { dates?: string[]; values?: number[]; source?: string } | null;
  source: string;
  is_featured: boolean;
  created_at: string;
}

export default function TrendDetailPage() {
  const params = useParams();
  const trendId = params.id as string;

  const [trend, setTrend] = useState<TrendDetail | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(false);

  useEffect(() => {
    if (!trendId) return;
    fetch(`${config.apiUrl}/api/trends/${trendId}`)
      .then((res) => {
        if (!res.ok) throw new Error('Not found');
        return res.json();
      })
      .then((data) => setTrend(data))
      .catch(() => setError(true))
      .finally(() => setLoading(false));
  }, [trendId]);

  if (loading) {
    return (
      <div className="min-h-screen bg-background">
        <div className="max-w-4xl mx-auto px-4 py-12 space-y-6">
          <Skeleton className="h-8 w-48" />
          <Skeleton className="h-12 w-full" />
          <Skeleton className="h-64 w-full" />
          <Skeleton className="h-32 w-full" />
        </div>
      </div>
    );
  }

  if (error || !trend) {
    return (
      <div className="min-h-screen bg-background flex items-center justify-center">
        <div className="text-center">
          <h2 className="text-2xl font-bold mb-2">Trend not found</h2>
          <p className="text-muted-foreground mb-6">This trend does not exist or has been removed.</p>
          <Button asChild variant="outline">
            <Link href="/trends"><ArrowLeft className="h-4 w-4 mr-2" /> Back to Trends</Link>
          </Button>
        </div>
      </div>
    );
  }

  const isPositive = trend.growth_percentage >= 0;

  // Build chart data from trend_data
  const chartData =
    trend.trend_data?.dates && trend.trend_data?.values
      ? trend.trend_data.dates.map((date, i) => ({
          date,
          value: trend.trend_data!.values![i] ?? 0,
        }))
      : null;

  const formatVolume = (volume: number) => {
    if (volume >= 1000000) return `${(volume / 1000000).toFixed(1)}M`;
    if (volume >= 1000) return `${(volume / 1000).toFixed(0)}K`;
    return volume.toString();
  };

  return (
    <div className="min-h-screen bg-background">
      <div className="max-w-4xl mx-auto px-4 py-12">
        {/* Back link */}
        <Button asChild variant="ghost" size="sm" className="mb-6">
          <Link href="/trends"><ArrowLeft className="h-4 w-4 mr-2" /> Back to Trends</Link>
        </Button>

        {/* Header */}
        <div className="mb-8">
          <div className="flex items-center gap-3 mb-3">
            <Badge variant="outline">{trend.category}</Badge>
            {trend.is_featured && <Badge variant="secondary">Hot</Badge>}
          </div>
          <h1 className="text-4xl font-bold mb-4">{trend.keyword}</h1>
        </div>

        {/* Stats cards */}
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 mb-8">
          <Card>
            <CardContent className="p-5 text-center">
              <div className="text-xs text-muted-foreground uppercase tracking-wider mb-1">Search Volume</div>
              <div className="text-3xl font-bold">{formatVolume(trend.search_volume)}</div>
              <div className="text-xs text-muted-foreground">monthly searches</div>
            </CardContent>
          </Card>
          <Card>
            <CardContent className="p-5 text-center">
              <div className="text-xs text-muted-foreground uppercase tracking-wider mb-1">Growth</div>
              <div className={`text-3xl font-bold flex items-center justify-center gap-1 ${isPositive ? 'text-green-600' : 'text-red-500'}`}>
                {isPositive ? <TrendingUp className="h-6 w-6" /> : <TrendingDown className="h-6 w-6" />}
                {isPositive ? '+' : ''}{trend.growth_percentage.toFixed(0)}%
              </div>
            </CardContent>
          </Card>
          <Card>
            <CardContent className="p-5 text-center">
              <div className="text-xs text-muted-foreground uppercase tracking-wider mb-1">Source</div>
              <div className="text-lg font-semibold capitalize">{trend.source?.replace('_', ' ') || 'Various'}</div>
            </CardContent>
          </Card>
        </div>

        {/* Trend chart */}
        <Card className="mb-8">
          <CardContent className="p-6">
            <TrendChart
              data={chartData ?? undefined}
              keyword={trend.keyword}
              volume={formatVolume(trend.search_volume)}
              growth={`${isPositive ? '+' : ''}${trend.growth_percentage.toFixed(0)}%`}
            />
            {trend.trend_data?.source && (
              <p className="text-xs text-muted-foreground text-right mt-2">
                {trend.trend_data.source === 'estimated'
                  ? 'Estimated trend data'
                  : 'Source: Google Trends'}
              </p>
            )}
          </CardContent>
        </Card>

        {/* Business implications */}
        {trend.business_implications && (
          <Card className="mb-8">
            <CardContent className="p-6">
              <h2 className="text-lg font-semibold mb-3">Business Implications</h2>
              <p className="text-muted-foreground leading-relaxed">{trend.business_implications}</p>
            </CardContent>
          </Card>
        )}

        {/* CTA */}
        <div className="flex gap-3">
          <Button asChild size="lg">
            <Link href={`/validate?idea=${encodeURIComponent(trend.keyword)}`}>
              <Zap className="h-4 w-4 mr-2" /> Validate this idea
            </Link>
          </Button>
          <Button asChild variant="outline" size="lg">
            <Link href="/trends">
              <ArrowLeft className="h-4 w-4 mr-2" /> Back to Trends
            </Link>
          </Button>
        </div>
      </div>
    </div>
  );
}
