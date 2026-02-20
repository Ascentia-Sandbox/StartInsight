'use client';

import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { useQuery } from '@tanstack/react-query';
import {
  Loader2,
  Users,
  DollarSign,
  TrendingUp,
  Activity,
  Eye,
  Bookmark,
  FileText,
  CheckCircle2,
  XCircle,
  AlertTriangle,
} from 'lucide-react';
import { getSupabaseClient } from '@/lib/supabase/client';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Progress } from '@/components/ui/progress';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import { config } from '@/lib/env';
import axios from 'axios';

const API_URL = config.apiUrl;

function createClient(token: string) {
  return axios.create({
    baseURL: API_URL,
    headers: { Authorization: `Bearer ${token}`, 'Content-Type': 'application/json' },
    timeout: 10000,
  });
}

function MetricCard({
  title,
  value,
  subtitle,
  icon: Icon,
  trend,
}: {
  title: string;
  value: string | number;
  subtitle?: string;
  icon: typeof Users;
  trend?: { value: number; label: string };
}) {
  return (
    <Card>
      <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
        <CardTitle className="text-sm font-medium">{title}</CardTitle>
        <Icon className="h-4 w-4 text-muted-foreground" />
      </CardHeader>
      <CardContent>
        <div className="text-2xl font-bold">{value}</div>
        {subtitle && <p className="text-xs text-muted-foreground">{subtitle}</p>}
        {trend && (
          <div className="flex items-center gap-1 mt-1">
            <TrendingUp className={`h-3 w-3 ${trend.value >= 0 ? 'text-green-500 dark:text-green-400' : 'text-red-500 dark:text-red-400'}`} />
            <span className={`text-xs ${trend.value >= 0 ? 'text-green-500 dark:text-green-400' : 'text-red-500 dark:text-red-400'}`}>
              {trend.value >= 0 ? '+' : ''}{trend.value}% {trend.label}
            </span>
          </div>
        )}
      </CardContent>
    </Card>
  );
}

function HealthIndicator({ label, rate }: { label: string; rate: number }) {
  const color = rate >= 90 ? 'text-green-500 dark:text-green-400' : rate >= 70 ? 'text-yellow-500 dark:text-yellow-400' : 'text-red-500 dark:text-red-400';
  const Icon = rate >= 90 ? CheckCircle2 : rate >= 70 ? AlertTriangle : XCircle;

  return (
    <div className="flex items-center justify-between py-2">
      <div className="flex items-center gap-2">
        <Icon className={`h-4 w-4 ${color}`} />
        <span className="text-sm">{label}</span>
      </div>
      <div className="flex items-center gap-2 w-32">
        <Progress value={rate} className="h-2" />
        <span className={`text-xs font-mono ${color}`}>{rate.toFixed(0)}%</span>
      </div>
    </div>
  );
}

export default function AnalyticsDashboard() {
  const router = useRouter();
  const [accessToken, setAccessToken] = useState<string | null>(null);
  const [period, setPeriod] = useState<number>(30);

  useEffect(() => {
    const supabase = getSupabaseClient();
    supabase.auth.getSession().then(({ data }: { data: { session: { access_token: string } | null } }) => {
      if (data.session?.access_token) {
        setAccessToken(data.session.access_token);
      } else {
        router.push('/login');
      }
    });
  }, [router]);

  const { data: revenue, isLoading: revLoading } = useQuery({
    queryKey: ['analytics-revenue', accessToken, period],
    queryFn: async () => {
      const client = createClient(accessToken!);
      const { data } = await client.get(`/admin/analytics/revenue?days=${period}`);
      return data;
    },
    enabled: !!accessToken,
    staleTime: 60_000,
  });

  const { data: engagement, isLoading: engLoading } = useQuery({
    queryKey: ['analytics-engagement', accessToken, period],
    queryFn: async () => {
      const client = createClient(accessToken!);
      const { data } = await client.get(`/admin/analytics/engagement?days=${period}`);
      return data;
    },
    enabled: !!accessToken,
    staleTime: 60_000,
  });

  const { data: content, isLoading: contLoading } = useQuery({
    queryKey: ['analytics-content', accessToken, period],
    queryFn: async () => {
      const client = createClient(accessToken!);
      const { data } = await client.get(`/admin/analytics/content?days=${period}`);
      return data;
    },
    enabled: !!accessToken,
    staleTime: 60_000,
  });

  const { data: health, isLoading: healthLoading } = useQuery({
    queryKey: ['analytics-health', accessToken, period],
    queryFn: async () => {
      const client = createClient(accessToken!);
      const { data } = await client.get(`/admin/analytics/health?days=${period}`);
      return data;
    },
    enabled: !!accessToken,
    staleTime: 30_000,
  });

  if (!accessToken) {
    return (
      <div className="flex items-center justify-center h-64">
        <Loader2 className="h-6 w-6 animate-spin" />
      </div>
    );
  }

  const loading = revLoading || engLoading || contLoading || healthLoading;

  return (
    <div className="p-6 space-y-6">
      <div className="flex items-start justify-between">
        <div>
          <h1 className="text-2xl font-bold flex items-center gap-2">
            <Activity className="h-6 w-6" />
            Analytics Dashboard
          </h1>
          <p className="text-muted-foreground text-sm mt-1">
            Revenue, engagement, content performance, and system health
          </p>
        </div>
        <Select value={String(period)} onValueChange={(v) => setPeriod(Number(v))}>
          <SelectTrigger className="w-[140px]">
            <SelectValue />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="7">Last 7 days</SelectItem>
            <SelectItem value="30">Last 30 days</SelectItem>
            <SelectItem value="90">Last 90 days</SelectItem>
          </SelectContent>
        </Select>
      </div>

      {loading && (
        <div className="flex items-center gap-2 text-muted-foreground">
          <Loader2 className="h-4 w-4 animate-spin" /> Loading analytics...
        </div>
      )}

      <Tabs defaultValue="overview">
        <TabsList>
          <TabsTrigger value="overview">Overview</TabsTrigger>
          <TabsTrigger value="engagement">Engagement</TabsTrigger>
          <TabsTrigger value="content">Content</TabsTrigger>
          <TabsTrigger value="health">System Health</TabsTrigger>
        </TabsList>

        {/* Overview Tab */}
        <TabsContent value="overview" className="space-y-4">
          <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
            <MetricCard
              title="Monthly Recurring Revenue"
              value={`$${(revenue?.mrr || 0).toLocaleString()}`}
              subtitle={`ARR: $${(revenue?.arr || 0).toLocaleString()}`}
              icon={DollarSign}
              trend={revenue?.mrr_growth_mom !== undefined ? {
                value: revenue.mrr_growth_mom,
                label: 'MoM growth',
              } : undefined}
            />
            <MetricCard
              title="Active Subscriptions"
              value={revenue?.active_subscriptions || 0}
              subtitle={revenue?.churn_rate > 0 ? `${revenue.churn_rate}% churn` : 'No churn'}
              icon={Users}
            />
            <MetricCard
              title="Daily Active Users"
              value={engagement?.dau || 0}
              subtitle={`MAU: ${engagement?.mau || 0}`}
              icon={Activity}
            />
            <MetricCard
              title="DAU/MAU Ratio"
              value={`${((engagement?.dau_mau_ratio || 0) * 100).toFixed(1)}%`}
              subtitle="Stickiness"
              icon={TrendingUp}
            />
          </div>

          <div className="grid gap-4 md:grid-cols-2">
            <Card>
              <CardHeader>
                <CardTitle className="text-base">Content Performance</CardTitle>
              </CardHeader>
              <CardContent className="space-y-3">
                <div className="flex justify-between">
                  <span className="text-sm flex items-center gap-2">
                    <Eye className="h-4 w-4" /> Insight Views
                  </span>
                  <span className="font-mono">{content?.total_insight_views || 0}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-sm flex items-center gap-2">
                    <Bookmark className="h-4 w-4" /> Insight Saves
                  </span>
                  <span className="font-mono">{content?.total_insight_saves || 0}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-sm flex items-center gap-2">
                    <FileText className="h-4 w-4" /> Article Views
                  </span>
                  <span className="font-mono">{content?.total_article_views || 0}</span>
                </div>
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle className="text-base">System Health</CardTitle>
              </CardHeader>
              <CardContent>
                {health ? (
                  <div className="space-y-1">
                    {Object.entries(health.scraper_success_rates || {}).map(([name, rate]) => (
                      <HealthIndicator key={name} label={name} rate={rate as number} />
                    ))}
                    {Object.entries(health.agent_success_rates || {}).map(([name, rate]) => (
                      <HealthIndicator key={name} label={name} rate={rate as number} />
                    ))}
                    {health.recent_errors > 0 && (
                      <div className="pt-2 border-t">
                        <Badge variant="destructive">{health.recent_errors} errors this week</Badge>
                      </div>
                    )}
                  </div>
                ) : (
                  <p className="text-sm text-muted-foreground">Loading...</p>
                )}
              </CardContent>
            </Card>
          </div>
        </TabsContent>

        {/* Engagement Tab */}
        <TabsContent value="engagement" className="space-y-4">
          <div className="grid gap-4 md:grid-cols-3">
            <MetricCard title="DAU" value={engagement?.dau || 0} icon={Users} />
            <MetricCard title="MAU" value={engagement?.mau || 0} icon={Users} />
            <MetricCard
              title="Avg Session"
              value={`${Math.round(engagement?.avg_session_duration_sec || 0)}s`}
              icon={Activity}
            />
          </div>

          <Card>
            <CardHeader>
              <CardTitle className="text-base">Feature Usage (Last 30 Days)</CardTitle>
            </CardHeader>
            <CardContent>
              {engagement?.feature_usage && Object.keys(engagement.feature_usage).length > 0 ? (
                <div className="space-y-2">
                  {Object.entries(engagement.feature_usage)
                    .sort(([, a], [, b]) => (b as number) - (a as number))
                    .map(([feature, count]) => {
                      const max = Math.max(...Object.values(engagement.feature_usage).map(Number));
                      return (
                        <div key={feature} className="flex items-center gap-3">
                          <span className="text-sm w-40 truncate">{feature}</span>
                          <div className="flex-1">
                            <Progress value={((count as number) / max) * 100} className="h-2" />
                          </div>
                          <span className="text-xs font-mono w-12 text-right">{(count as number).toLocaleString()}</span>
                        </div>
                      );
                    })}
                </div>
              ) : (
                <p className="text-sm text-muted-foreground">No feature usage data yet</p>
              )}
            </CardContent>
          </Card>
        </TabsContent>

        {/* Content Tab */}
        <TabsContent value="content" className="space-y-4">
          <div className="grid gap-4 md:grid-cols-2">
            <Card>
              <CardHeader>
                <CardTitle className="text-base">Top Insights by Engagement</CardTitle>
              </CardHeader>
              <CardContent>
                {content?.top_insights?.length > 0 ? (
                  <div className="space-y-3">
                    {content.top_insights.slice(0, 5).map((insight: { id: string; title: string; score: number; interactions: number }, i: number) => (
                      <div key={insight.id} className="flex items-center gap-3">
                        <span className="text-xs text-muted-foreground w-4">{i + 1}</span>
                        <div className="flex-1 min-w-0">
                          <p className="text-sm font-medium truncate">{insight.title}</p>
                          <p className="text-xs text-muted-foreground">
                            Score: {((insight.score || 0) * 100).toFixed(0)}%
                          </p>
                        </div>
                        <Badge variant="secondary">{insight.interactions}</Badge>
                      </div>
                    ))}
                  </div>
                ) : (
                  <p className="text-sm text-muted-foreground">No interaction data yet</p>
                )}
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle className="text-base">Top Articles by Views</CardTitle>
              </CardHeader>
              <CardContent>
                {content?.top_articles?.length > 0 ? (
                  <div className="space-y-3">
                    {content.top_articles.slice(0, 5).map((article: { id: string; title: string; views: number }, i: number) => (
                      <div key={article.id} className="flex items-center gap-3">
                        <span className="text-xs text-muted-foreground w-4">{i + 1}</span>
                        <p className="flex-1 text-sm font-medium truncate">{article.title}</p>
                        <div className="flex items-center gap-1">
                          <Eye className="h-3 w-3 text-muted-foreground" />
                          <span className="text-xs font-mono">{article.views}</span>
                        </div>
                      </div>
                    ))}
                  </div>
                ) : (
                  <p className="text-sm text-muted-foreground">No articles published yet</p>
                )}
              </CardContent>
            </Card>
          </div>
        </TabsContent>

        {/* Health Tab */}
        <TabsContent value="health" className="space-y-4">
          <div className="grid gap-4 md:grid-cols-2">
            <Card>
              <CardHeader>
                <CardTitle className="text-base">Scraper Success Rates (7 days)</CardTitle>
              </CardHeader>
              <CardContent>
                {health?.scraper_success_rates && Object.keys(health.scraper_success_rates).length > 0 ? (
                  <div className="space-y-1">
                    {Object.entries(health.scraper_success_rates).map(([name, rate]) => (
                      <HealthIndicator key={name} label={name} rate={rate as number} />
                    ))}
                  </div>
                ) : (
                  <p className="text-sm text-muted-foreground">No scraper data yet</p>
                )}
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle className="text-base">Agent Success Rates (7 days)</CardTitle>
              </CardHeader>
              <CardContent>
                {health?.agent_success_rates && Object.keys(health.agent_success_rates).length > 0 ? (
                  <div className="space-y-1">
                    {Object.entries(health.agent_success_rates).map(([name, rate]) => (
                      <HealthIndicator key={name} label={name} rate={rate as number} />
                    ))}
                  </div>
                ) : (
                  <p className="text-sm text-muted-foreground">No agent data yet</p>
                )}
              </CardContent>
            </Card>
          </div>

          {health?.recent_errors !== undefined && (
            <Card>
              <CardHeader>
                <CardTitle className="text-base">Error Summary</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="flex items-center gap-3">
                  {health.recent_errors === 0 ? (
                    <>
                      <CheckCircle2 className="h-5 w-5 text-green-500" />
                      <span className="text-sm">No errors in the last 7 days</span>
                    </>
                  ) : (
                    <>
                      <AlertTriangle className="h-5 w-5 text-yellow-500" />
                      <span className="text-sm">
                        <strong>{health.recent_errors}</strong> errors in the last 7 days
                      </span>
                    </>
                  )}
                </div>
              </CardContent>
            </Card>
          )}
        </TabsContent>
      </Tabs>
    </div>
  );
}
