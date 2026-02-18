'use client';

import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import Link from 'next/link';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import {
  Loader2, Zap, DollarSign, Clock, Play, Pause, RotateCcw,
  FileText, AlertTriangle, Users, Wrench, TrendingUp, BarChart3,
  Trophy, BookOpen, ExternalLink, Eye, Bookmark, Activity,
} from 'lucide-react';
import {
  BarChart, Bar, PieChart, Pie, Cell,
  XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Legend,
} from 'recharts';
import { getSupabaseClient } from '@/lib/supabase/client';
import {
  fetchAdminDashboard, fetchAgentStatus, pauseAgent, resumeAgent,
  triggerAgent, fetchAdminUsers,
  fetchAnalyticsContent, fetchAnalyticsEngagement,
  fetchAnalyticsUsers, fetchAnalyticsHealth,
  fetchAgentCostAnalytics,
} from '@/lib/api';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import type { AgentStatus, DashboardMetrics } from '@/lib/types';
import { formatDateTimeMYT } from '@/lib/utils';
import { toast } from 'sonner';
import { config } from '@/lib/env';

// Chart color palette
const CHART_COLORS = {
  teal: '#0D7377',
  amber: '#D4A017',
  emerald: '#10B981',
  coral: '#E5604E',
  slateBlue: '#4A6FA5',
  purple: '#8B5CF6',
  pink: '#EC4899',
} as const;

const TIER_COLORS: Record<string, string> = {
  free: '#94A3B8',
  starter: '#0D7377',
  pro: '#8B5CF6',
  enterprise: '#D4A017',
};

export default function AdminDashboard() {
  const [isMounted, setIsMounted] = useState(false);

  useEffect(() => {
    setIsMounted(true);
  }, []);

  if (!isMounted) {
    return (
      <div className="flex items-center justify-center min-h-[50vh]">
        <Loader2 className="animate-spin h-8 w-8 text-primary" />
      </div>
    );
  }

  return <AdminContent />;
}

function AdminContent() {
  const router = useRouter();
  const queryClient = useQueryClient();
  const [accessToken, setAccessToken] = useState<string | null>(null);
  const [isCheckingAuth, setIsCheckingAuth] = useState(true);
  const [analyticsDays, setAnalyticsDays] = useState(30);

  useEffect(() => {
    const checkAuth = async () => {
      try {
        const supabase = getSupabaseClient();
        const { data: { session } } = await supabase.auth.getSession();
        if (!session) {
          router.push('/auth/login?redirectTo=/admin');
          return;
        }
        setAccessToken(session.access_token);
      } catch (error) {
        console.error('Admin auth check failed:', error);
      } finally {
        setIsCheckingAuth(false);
      }
    };
    checkAuth();
  }, [router]);

  const { data: metrics, isLoading: metricsLoading, error: metricsError } = useQuery({
    queryKey: ['admin-dashboard', accessToken],
    queryFn: () => fetchAdminDashboard(accessToken!),
    enabled: !!accessToken,
    retry: 1,
    refetchInterval: 15000,
  });

  const { data: agents, isLoading: agentsLoading } = useQuery({
    queryKey: ['admin-agents', accessToken],
    queryFn: () => fetchAgentStatus(accessToken!),
    enabled: !!accessToken,
    retry: 1,
    refetchInterval: 15000,
  });

  // Fetch content counts
  const { data: usersList } = useQuery({
    queryKey: ['admin-users-count', accessToken],
    queryFn: () => fetchAdminUsers(accessToken!, { limit: 100 }),
    enabled: !!accessToken,
  });

  const { data: storiesData } = useQuery({
    queryKey: ['admin-stories-count', accessToken],
    queryFn: async () => {
      const res = await fetch(
        `${config.apiUrl}/api/success-stories?limit=1`,
        { headers: { Authorization: `Bearer ${accessToken}` } }
      );
      if (!res.ok) return 0;
      const data = await res.json();
      return data.total || 0;
    },
    enabled: !!accessToken,
  });

  const { data: articlesData } = useQuery({
    queryKey: ['admin-articles-count', accessToken],
    queryFn: async () => {
      const res = await fetch(
        `${config.apiUrl}/api/market-insights?limit=1`,
        { headers: { Authorization: `Bearer ${accessToken}` } }
      );
      if (!res.ok) return 0;
      const data = await res.json();
      return data.total || 0;
    },
    enabled: !!accessToken,
  });

  const { data: toolsData } = useQuery({
    queryKey: ['admin-tools-count', accessToken],
    queryFn: async () => {
      const res = await fetch(
        `${config.apiUrl}/api/tools?limit=1`,
        { headers: { Authorization: `Bearer ${accessToken}` } }
      );
      if (!res.ok) return 0;
      const data = await res.json();
      return data.total || data.tools?.length || 0;
    },
    enabled: !!accessToken,
  });

  const { data: trendsData } = useQuery({
    queryKey: ['admin-trends-count', accessToken],
    queryFn: async () => {
      const res = await fetch(
        `${config.apiUrl}/api/trends?limit=1`,
        { headers: { Authorization: `Bearer ${accessToken}` } }
      );
      if (!res.ok) return 0;
      const data = await res.json();
      return data.total || 0;
    },
    enabled: !!accessToken,
  });

  // Real analytics data
  const { data: contentData } = useQuery({
    queryKey: ['admin-analytics-content', accessToken, analyticsDays],
    queryFn: () => fetchAnalyticsContent(accessToken!, analyticsDays),
    enabled: !!accessToken,
  });

  const { data: engagementData } = useQuery({
    queryKey: ['admin-analytics-engagement', accessToken, analyticsDays],
    queryFn: () => fetchAnalyticsEngagement(accessToken!, analyticsDays),
    enabled: !!accessToken,
  });

  const { data: userAnalytics } = useQuery({
    queryKey: ['admin-analytics-users', accessToken],
    queryFn: () => fetchAnalyticsUsers(accessToken!),
    enabled: !!accessToken,
  });

  const { data: healthData } = useQuery({
    queryKey: ['admin-analytics-health', accessToken],
    queryFn: () => fetchAnalyticsHealth(accessToken!),
    enabled: !!accessToken,
  });

  const { data: costData } = useQuery({
    queryKey: ['admin-analytics-costs', accessToken],
    queryFn: () => fetchAgentCostAnalytics(accessToken!, '7d'),
    enabled: !!accessToken,
  });

  const pauseMutation = useMutation({
    mutationFn: (agentType: string) => pauseAgent(accessToken!, agentType),
    onSuccess: (_data, agentType) => {
      queryClient.invalidateQueries({ queryKey: ['admin-agents'] });
      queryClient.invalidateQueries({ queryKey: ['admin-dashboard'] });
      toast.success(`${agentType.replace(/_/g, ' ')} paused`);
    },
    onError: () => toast.error('Failed to pause agent'),
  });

  const resumeMutation = useMutation({
    mutationFn: (agentType: string) => resumeAgent(accessToken!, agentType),
    onSuccess: (_data, agentType) => {
      queryClient.invalidateQueries({ queryKey: ['admin-agents'] });
      queryClient.invalidateQueries({ queryKey: ['admin-dashboard'] });
      toast.success(`${agentType.replace(/_/g, ' ')} resumed`);
    },
    onError: () => toast.error('Failed to resume agent'),
  });

  const triggerMutation = useMutation({
    mutationFn: (agentType: string) => triggerAgent(accessToken!, agentType),
    onSuccess: (_data, agentType) => {
      queryClient.invalidateQueries({ queryKey: ['admin-agents'] });
      queryClient.invalidateQueries({ queryKey: ['admin-dashboard'] });
      toast.success(`${agentType.replace(/_/g, ' ')} triggered`);
    },
    onError: (_err, agentType) => toast.error(`Failed to trigger ${agentType?.replace(/_/g, ' ')}`),
  });

  const [pipelineRunning, setPipelineRunning] = useState(false);
  const handleRunPipeline = async () => {
    setPipelineRunning(true);
    try {
      await triggerAgent(accessToken!, 'enhanced_analyzer');
      await triggerAgent(accessToken!, 'quality_reviewer');
      toast.success('Daily pipeline triggered', { description: 'Enhanced analyzer + quality reviewer started' });
      queryClient.invalidateQueries({ queryKey: ['admin-agents'] });
      queryClient.invalidateQueries({ queryKey: ['admin-dashboard'] });
    } catch {
      toast.error('Failed to trigger pipeline');
    } finally {
      setPipelineRunning(false);
    }
  };

  if (isCheckingAuth) {
    return (
      <div className="flex items-center justify-center min-h-[50vh]">
        <Loader2 className="animate-spin h-8 w-8 text-primary" />
      </div>
    );
  }

  if (!accessToken) {
    return (
      <div className="flex items-center justify-center min-h-[50vh]">
        <Card className="max-w-md">
          <CardContent className="p-8 text-center">
            <AlertTriangle className="h-12 w-12 text-yellow-500 mx-auto mb-4" />
            <h2 className="text-xl font-semibold mb-2">Authentication Required</h2>
            <p className="text-muted-foreground mb-4">
              Please sign in to access the admin dashboard.
            </p>
            <Link href="/auth/login?redirectTo=/admin">
              <Button>Sign In</Button>
            </Link>
          </CardContent>
        </Card>
      </div>
    );
  }

  if (metricsError) {
    const isNetworkError = metricsError instanceof TypeError || (metricsError as Error)?.message?.includes('fetch');
    const is403 = (metricsError as { status?: number })?.status === 403;

    return (
      <div className="flex items-center justify-center min-h-[50vh]">
        <Card className="max-w-md">
          <CardContent className="p-8 text-center">
            <AlertTriangle className="h-12 w-12 text-yellow-500 mx-auto mb-4" />
            <h2 className="text-xl font-semibold mb-2">
              {is403 ? 'Access Denied' : isNetworkError ? 'Backend Unavailable' : 'Something Went Wrong'}
            </h2>
            <p className="text-muted-foreground mb-4">
              {is403
                ? 'You do not have admin access.'
                : isNetworkError
                ? 'Cannot connect to the backend server. Please ensure it is running.'
                : (metricsError as Error)?.message || 'An unexpected error occurred.'}
            </p>
            <div className="flex gap-2 justify-center">
              {!is403 && (
                <Button variant="outline" onClick={() => queryClient.invalidateQueries({ queryKey: ['admin-dashboard'] })}>
                  Retry
                </Button>
              )}
              <Link href={is403 ? '/dashboard' : '/admin'}>
                <Button>{is403 ? 'Return to Dashboard' : 'Reload'}</Button>
              </Link>
            </div>
          </CardContent>
        </Card>
      </div>
    );
  }

  const totalUsers = usersList?.length || 0;
  const tierCounts = (usersList || []).reduce((acc: Record<string, number>, u) => {
    acc[u.subscription_tier] = (acc[u.subscription_tier] || 0) + 1;
    return acc;
  }, {});

  const isLoading = metricsLoading || agentsLoading;

  // Transform real data for charts
  const tierChartData = userAnalytics?.by_tier?.map((t) => ({
    name: t.tier.charAt(0).toUpperCase() + t.tier.slice(1),
    value: t.count,
    mrr: t.mrr,
    fill: TIER_COLORS[t.tier] || CHART_COLORS.slateBlue,
  })) || [];

  const costChartData = costData?.daily_breakdown
    ? Object.entries(
        costData.daily_breakdown.reduce((acc: Record<string, Record<string, number>>, item) => {
          if (!acc[item.date]) acc[item.date] = {};
          acc[item.date][item.agent_type] = (acc[item.date][item.agent_type] || 0) + item.cost_usd;
          return acc;
        }, {})
      ).map(([date, agents]) => ({
        date: new Date(date).toLocaleDateString('en-US', { month: 'short', day: 'numeric' }),
        ...agents,
      }))
    : [];

  const agentCostTypes = costData?.cost_by_agent ? Object.keys(costData.cost_by_agent) : [];
  const agentColors = [CHART_COLORS.teal, CHART_COLORS.coral, CHART_COLORS.slateBlue, CHART_COLORS.amber, CHART_COLORS.purple];

  const healthChartData = [
    ...Object.entries(healthData?.agent_success_rates || {}).map(([name, rate]) => ({
      name: name.replace(/_/g, ' '),
      rate,
      fill: rate >= 90 ? CHART_COLORS.emerald : rate >= 70 ? CHART_COLORS.amber : CHART_COLORS.coral,
    })),
    ...Object.entries(healthData?.scraper_success_rates || {}).map(([name, rate]) => ({
      name: name.replace(/_/g, ' '),
      rate,
      fill: rate >= 90 ? CHART_COLORS.emerald : rate >= 70 ? CHART_COLORS.amber : CHART_COLORS.coral,
    })),
  ];

  return (
    <div className="p-6 lg:p-8 max-w-7xl">
      {/* Header */}
      <div className="flex justify-between items-center mb-8">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Admin Dashboard</h1>
          <p className="text-muted-foreground mt-2">
            System overview and content management
          </p>
        </div>
        <div className="flex items-center gap-2">
          <div className="w-2 h-2 rounded-full bg-green-500 animate-pulse" />
          <span className="text-xs text-muted-foreground">Live</span>
        </div>
      </div>

      {isLoading ? (
        <div className="flex items-center justify-center py-12">
          <Loader2 className="animate-spin h-8 w-8 text-primary" />
        </div>
      ) : (
        <>
          {/* AI Processing Stats */}
          <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4 mb-6">
            <Card>
              <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                <CardTitle className="text-sm font-medium">Insights Today</CardTitle>
                <Zap className="h-4 w-4 text-muted-foreground" />
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold">{metrics?.total_insights_today || 0}</div>
                <p className="text-xs text-muted-foreground">Generated by AI agents</p>
              </CardContent>
            </Card>
            <Card>
              <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                <CardTitle className="text-sm font-medium">LLM Cost Today</CardTitle>
                <DollarSign className="h-4 w-4 text-muted-foreground" />
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold">${metrics?.llm_cost_today?.toFixed(2) || '0.00'}</div>
                <p className="text-xs text-muted-foreground">AI processing costs</p>
              </CardContent>
            </Card>
            <Card>
              <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                <CardTitle className="text-sm font-medium">Pending Review</CardTitle>
                <FileText className="h-4 w-4 text-muted-foreground" />
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold">{metrics?.pending_insights || 0}</div>
                <p className="text-xs text-muted-foreground">Insights awaiting approval</p>
              </CardContent>
            </Card>
            <Card>
              <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                <CardTitle className="text-sm font-medium">Errors Today</CardTitle>
                <AlertTriangle className="h-4 w-4 text-muted-foreground" />
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold text-red-500">{metrics?.errors_today || 0}</div>
                <p className="text-xs text-muted-foreground">Processing errors</p>
              </CardContent>
            </Card>
          </div>

          {/* Content & Users Overview */}
          <h2 className="text-lg font-semibold mb-3">Content & Users</h2>
          <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-5 mb-6">
            <Link href="/admin/users">
              <Card className="hover:border-primary/50 transition-colors cursor-pointer">
                <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                  <CardTitle className="text-sm font-medium">Users</CardTitle>
                  <Users className="h-4 w-4 text-muted-foreground" />
                </CardHeader>
                <CardContent>
                  <div className="text-2xl font-bold">{totalUsers}</div>
                  <div className="flex gap-1 mt-1 flex-wrap">
                    {tierCounts.enterprise ? <Badge variant="outline" className="text-[10px] px-1 py-0 bg-amber-50 text-amber-700">{tierCounts.enterprise} enterprise</Badge> : null}
                    {tierCounts.pro ? <Badge variant="outline" className="text-[10px] px-1 py-0 bg-violet-50 text-violet-700">{tierCounts.pro} pro</Badge> : null}
                    {tierCounts.free ? <Badge variant="outline" className="text-[10px] px-1 py-0">{tierCounts.free} free</Badge> : null}
                  </div>
                </CardContent>
              </Card>
            </Link>
            <Link href="/admin/tools">
              <Card className="hover:border-primary/50 transition-colors cursor-pointer">
                <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                  <CardTitle className="text-sm font-medium">Tools</CardTitle>
                  <Wrench className="h-4 w-4 text-muted-foreground" />
                </CardHeader>
                <CardContent>
                  <div className="text-2xl font-bold">{toolsData || 0}</div>
                  <p className="text-xs text-muted-foreground">Affiliate tools</p>
                </CardContent>
              </Card>
            </Link>
            <Link href="/admin/success-stories">
              <Card className="hover:border-primary/50 transition-colors cursor-pointer">
                <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                  <CardTitle className="text-sm font-medium">Stories</CardTitle>
                  <Trophy className="h-4 w-4 text-muted-foreground" />
                </CardHeader>
                <CardContent>
                  <div className="text-2xl font-bold">{storiesData || 0}</div>
                  <p className="text-xs text-muted-foreground">Success stories</p>
                </CardContent>
              </Card>
            </Link>
            <Link href="/admin/market-insights">
              <Card className="hover:border-primary/50 transition-colors cursor-pointer">
                <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                  <CardTitle className="text-sm font-medium">Articles</CardTitle>
                  <BarChart3 className="h-4 w-4 text-muted-foreground" />
                </CardHeader>
                <CardContent>
                  <div className="text-2xl font-bold">{articlesData || 0}</div>
                  <p className="text-xs text-muted-foreground">Market insights</p>
                </CardContent>
              </Card>
            </Link>
            <Link href="/admin/trends">
              <Card className="hover:border-primary/50 transition-colors cursor-pointer">
                <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                  <CardTitle className="text-sm font-medium">Trends</CardTitle>
                  <TrendingUp className="h-4 w-4 text-muted-foreground" />
                </CardHeader>
                <CardContent>
                  <div className="text-2xl font-bold">{trendsData || 0}</div>
                  <p className="text-xs text-muted-foreground">Tracked trends</p>
                </CardContent>
              </Card>
            </Link>
          </div>

          {/* Analytics Charts (2x2 grid) — Real Data */}
          <div className="flex items-center justify-between mb-3">
            <h2 className="text-lg font-semibold">Analytics Overview</h2>
            <div className="flex gap-1">
              {[7, 30, 90].map((d) => (
                <Button
                  key={d}
                  variant={analyticsDays === d ? 'default' : 'ghost'}
                  size="sm"
                  className="text-xs h-7 px-2"
                  onClick={() => setAnalyticsDays(d)}
                >
                  {d}d
                </Button>
              ))}
            </div>
          </div>
          <div className="grid gap-4 md:grid-cols-2 mb-6">
            {/* 1. User Distribution by Tier */}
            <Card>
              <CardHeader className="pb-2">
                <CardTitle className="text-sm font-medium">User Distribution</CardTitle>
                <CardDescription>Users by subscription tier</CardDescription>
              </CardHeader>
              <CardContent>
                {tierChartData.length > 0 ? (
                  <ResponsiveContainer width="100%" height={240}>
                    <PieChart>
                      <Pie
                        data={tierChartData}
                        cx="50%"
                        cy="50%"
                        innerRadius={60}
                        outerRadius={90}
                        paddingAngle={3}
                        dataKey="value"
                        label={({ name, value }) => `${name}: ${value}`}
                      >
                        {tierChartData.map((entry, i) => (
                          <Cell key={i} fill={entry.fill} />
                        ))}
                      </Pie>
                      <Tooltip
                        contentStyle={{ borderRadius: 8, fontSize: 12, border: '1px solid hsl(var(--border))' }}
                        formatter={(value, _name, props) => [
                          `${value} users ($${((props.payload as Record<string, number>)?.mrr || 0).toFixed(0)} MRR)`,
                        ]}
                      />
                      <Legend iconSize={10} wrapperStyle={{ fontSize: 11 }} />
                    </PieChart>
                  </ResponsiveContainer>
                ) : (
                  <div className="flex items-center justify-center h-[240px] text-muted-foreground text-sm">
                    No user data available
                  </div>
                )}
              </CardContent>
            </Card>

            {/* 2. Agent Cost Breakdown */}
            <Card>
              <CardHeader className="pb-2">
                <CardTitle className="text-sm font-medium">Agent Costs (7d)</CardTitle>
                <CardDescription>
                  Daily LLM spend — ${costData?.total_cost_usd?.toFixed(2) || '0.00'} total
                </CardDescription>
              </CardHeader>
              <CardContent>
                {costChartData.length > 0 ? (
                  <ResponsiveContainer width="100%" height={240}>
                    <BarChart data={costChartData} margin={{ top: 4, right: 8, left: -16, bottom: 0 }}>
                      <CartesianGrid strokeDasharray="3 3" className="stroke-muted" />
                      <XAxis dataKey="date" tick={{ fontSize: 11 }} className="text-muted-foreground" />
                      <YAxis tick={{ fontSize: 11 }} className="text-muted-foreground" tickFormatter={(v) => `$${v}`} />
                      <Tooltip
                        contentStyle={{ borderRadius: 8, fontSize: 12, border: '1px solid hsl(var(--border))' }}
                        formatter={(value) => [`$${Number(value).toFixed(4)}`]}
                      />
                      <Legend iconSize={10} wrapperStyle={{ fontSize: 11 }} />
                      {agentCostTypes.map((type, i) => (
                        <Bar
                          key={type}
                          dataKey={type}
                          stackId="a"
                          fill={agentColors[i % agentColors.length]}
                          name={type.replace(/_/g, ' ')}
                          radius={i === agentCostTypes.length - 1 ? [2, 2, 0, 0] : [0, 0, 0, 0]}
                        />
                      ))}
                    </BarChart>
                  </ResponsiveContainer>
                ) : (
                  <div className="flex items-center justify-center h-[240px] text-muted-foreground text-sm">
                    No cost data available yet
                  </div>
                )}
              </CardContent>
            </Card>

            {/* 3. Content Performance */}
            <Card>
              <CardHeader className="pb-2">
                <CardTitle className="text-sm font-medium">Content Performance</CardTitle>
                <CardDescription>Views, saves & engagement ({analyticsDays}d)</CardDescription>
              </CardHeader>
              <CardContent>
                <div className="grid grid-cols-3 gap-4 mb-4">
                  <div className="text-center">
                    <div className="flex items-center justify-center gap-1 mb-1">
                      <Eye className="h-3.5 w-3.5 text-muted-foreground" />
                    </div>
                    <div className="text-xl font-bold">{contentData?.total_insight_views || 0}</div>
                    <p className="text-[10px] text-muted-foreground">Insight Views</p>
                  </div>
                  <div className="text-center">
                    <div className="flex items-center justify-center gap-1 mb-1">
                      <Bookmark className="h-3.5 w-3.5 text-muted-foreground" />
                    </div>
                    <div className="text-xl font-bold">{contentData?.total_insight_saves || 0}</div>
                    <p className="text-[10px] text-muted-foreground">Insight Saves</p>
                  </div>
                  <div className="text-center">
                    <div className="flex items-center justify-center gap-1 mb-1">
                      <BookOpen className="h-3.5 w-3.5 text-muted-foreground" />
                    </div>
                    <div className="text-xl font-bold">{contentData?.total_article_views || 0}</div>
                    <p className="text-[10px] text-muted-foreground">Article Views</p>
                  </div>
                </div>
                {contentData?.top_insights && contentData.top_insights.length > 0 ? (
                  <div className="space-y-2">
                    <p className="text-xs font-medium text-muted-foreground">Top Insights</p>
                    {contentData.top_insights.slice(0, 5).map((insight) => (
                      <div key={insight.id} className="flex items-center justify-between text-xs">
                        <span className="truncate max-w-[200px]">{insight.title}</span>
                        <div className="flex items-center gap-2">
                          <Badge variant="outline" className="text-[10px] px-1.5 py-0">
                            {insight.interactions} interactions
                          </Badge>
                          <span className="text-muted-foreground">{insight.score?.toFixed(1)}</span>
                        </div>
                      </div>
                    ))}
                  </div>
                ) : (
                  <div className="text-center py-4 text-muted-foreground text-sm">
                    No content interaction data
                  </div>
                )}
              </CardContent>
            </Card>

            {/* 4. System Health — Success Rates */}
            <Card>
              <CardHeader className="pb-2">
                <CardTitle className="text-sm font-medium">System Health</CardTitle>
                <CardDescription>
                  Agent & scraper success rates — {healthData?.recent_errors || 0} errors
                </CardDescription>
              </CardHeader>
              <CardContent>
                {healthChartData.length > 0 ? (
                  <ResponsiveContainer width="100%" height={240}>
                    <BarChart data={healthChartData} layout="vertical" margin={{ top: 4, right: 8, left: 8, bottom: 0 }}>
                      <CartesianGrid strokeDasharray="3 3" className="stroke-muted" />
                      <XAxis type="number" domain={[0, 100]} tick={{ fontSize: 11 }} tickFormatter={(v) => `${v}%`} />
                      <YAxis dataKey="name" type="category" width={100} tick={{ fontSize: 10 }} className="text-muted-foreground" />
                      <Tooltip
                        contentStyle={{ borderRadius: 8, fontSize: 12, border: '1px solid hsl(var(--border))' }}
                        formatter={(value) => [`${value}%`, 'Success Rate']}
                      />
                      <Bar dataKey="rate" radius={[0, 4, 4, 0]}>
                        {healthChartData.map((entry, i) => (
                          <Cell key={i} fill={entry.fill} />
                        ))}
                      </Bar>
                    </BarChart>
                  </ResponsiveContainer>
                ) : (
                  <div className="flex items-center justify-center h-[240px]">
                    <div className="text-center text-muted-foreground">
                      <Activity className="h-8 w-8 mx-auto mb-2 opacity-50" />
                      <p className="text-sm">No health data available</p>
                    </div>
                  </div>
                )}
              </CardContent>
            </Card>
          </div>

          {/* Engagement Summary */}
          {engagementData && (
            <div className="grid gap-4 md:grid-cols-4 mb-6">
              <Card>
                <CardHeader className="pb-2">
                  <CardTitle className="text-xs font-medium text-muted-foreground">DAU</CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="text-2xl font-bold">{engagementData.dau}</div>
                  <p className="text-xs text-muted-foreground">Daily active users</p>
                </CardContent>
              </Card>
              <Card>
                <CardHeader className="pb-2">
                  <CardTitle className="text-xs font-medium text-muted-foreground">MAU</CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="text-2xl font-bold">{engagementData.mau}</div>
                  <p className="text-xs text-muted-foreground">Monthly active users</p>
                </CardContent>
              </Card>
              <Card>
                <CardHeader className="pb-2">
                  <CardTitle className="text-xs font-medium text-muted-foreground">Stickiness</CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="text-2xl font-bold">{(engagementData.dau_mau_ratio * 100).toFixed(1)}%</div>
                  <p className="text-xs text-muted-foreground">DAU/MAU ratio</p>
                </CardContent>
              </Card>
              <Card>
                <CardHeader className="pb-2">
                  <CardTitle className="text-xs font-medium text-muted-foreground">Avg Session</CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="text-2xl font-bold">
                    {engagementData.avg_session_duration_sec > 60
                      ? `${(engagementData.avg_session_duration_sec / 60).toFixed(1)}m`
                      : `${Math.round(engagementData.avg_session_duration_sec)}s`}
                  </div>
                  <p className="text-xs text-muted-foreground">Session duration</p>
                </CardContent>
              </Card>
            </div>
          )}

          {/* Quick Actions */}
          <h2 className="text-lg font-semibold mb-3">Quick Actions</h2>
          <div className="grid gap-3 md:grid-cols-2 lg:grid-cols-4 mb-8">
            <Link href="/admin/success-stories">
              <Button variant="outline" className="w-full justify-start h-auto py-3">
                <Trophy className="h-4 w-4 mr-2 text-amber-500" />
                <div className="text-left">
                  <div className="font-medium text-sm">Add Success Story</div>
                  <div className="text-xs text-muted-foreground">Create founder case study</div>
                </div>
              </Button>
            </Link>
            <Link href="/admin/market-insights">
              <Button variant="outline" className="w-full justify-start h-auto py-3">
                <BookOpen className="h-4 w-4 mr-2 text-blue-500" />
                <div className="text-left">
                  <div className="font-medium text-sm">Write Article</div>
                  <div className="text-xs text-muted-foreground">Publish market insight</div>
                </div>
              </Button>
            </Link>
            <Link href="/admin/tools">
              <Button variant="outline" className="w-full justify-start h-auto py-3">
                <Wrench className="h-4 w-4 mr-2 text-green-500" />
                <div className="text-left">
                  <div className="font-medium text-sm">Add Tool</div>
                  <div className="text-xs text-muted-foreground">New affiliate tool</div>
                </div>
              </Button>
            </Link>
            <Link href="/admin/research-queue">
              <Button variant="outline" className="w-full justify-start h-auto py-3">
                <FileText className="h-4 w-4 mr-2 text-violet-500" />
                <div className="text-left">
                  <div className="font-medium text-sm">Review Queue</div>
                  <div className="text-xs text-muted-foreground">Pending research requests</div>
                </div>
              </Button>
            </Link>
          </div>

          {/* Public Site Links */}
          <h2 className="text-lg font-semibold mb-3">View Public Pages</h2>
          <div className="flex flex-wrap gap-2 mb-8">
            {[
              { label: 'Success Stories', href: '/success-stories' },
              { label: 'Market Insights', href: '/market-insights' },
              { label: 'Tools', href: '/tools' },
              { label: 'Trends', href: '/trends' },
              { label: 'Features', href: '/features' },
              { label: 'Insights', href: '/insights' },
            ].map((link) => (
              <Link key={link.href} href={link.href} target="_blank">
                <Badge variant="outline" className="cursor-pointer hover:bg-muted py-1.5 px-3 text-xs">
                  {link.label}
                  <ExternalLink className="h-3 w-3 ml-1" />
                </Badge>
              </Link>
            ))}
          </div>

          {/* Agent Status */}
          <Card className="mb-8">
            <CardHeader>
              <div className="flex items-center justify-between">
                <div>
                  <CardTitle>Agent Status</CardTitle>
                  <CardDescription>AI processing agents</CardDescription>
                </div>
                <div className="flex gap-2">
                  <Button variant="outline" size="sm"
                    onClick={handleRunPipeline}
                    disabled={pipelineRunning}>
                    {pipelineRunning ? <Loader2 className="h-3 w-3 mr-1 animate-spin" /> : <Play className="h-3 w-3 mr-1" />}
                    Run Pipeline
                  </Button>
                  <Link href="/admin/agents">
                    <Button variant="outline" size="sm">
                      <Zap className="h-3 w-3 mr-1" />
                      Full Control
                    </Button>
                  </Link>
                </div>
              </div>
            </CardHeader>
            <CardContent>
              <div className="space-y-3">
                {agents && agents.length > 0 ? (
                  agents.map((agent: AgentStatus) => (
                    <div
                      key={agent.agent_type}
                      className="flex items-center justify-between p-3 border rounded-lg"
                    >
                      <div className="flex items-center gap-3">
                        <div
                          className={`w-2.5 h-2.5 rounded-full ${
                            agent.state === 'running'
                              ? 'bg-green-500 animate-pulse'
                              : agent.state === 'paused'
                              ? 'bg-yellow-500'
                              : 'bg-gray-400'
                          }`}
                        />
                        <div>
                          <p className="font-medium text-sm capitalize">
                            {agent.agent_type.replace(/_/g, ' ')}
                          </p>
                          <p className="text-xs text-muted-foreground">
                            {agent.last_run
                              ? `Last: ${formatDateTimeMYT(agent.last_run)}`
                              : 'Never run'}
                          </p>
                        </div>
                      </div>
                      <div className="flex items-center gap-4 text-sm">
                        <span className="text-muted-foreground text-xs">
                          {agent.items_processed_today} items
                        </span>
                        {agent.errors_today > 0 && (
                          <span className="text-red-500 text-xs">{agent.errors_today} errors</span>
                        )}
                        <div className="flex gap-1">
                          {agent.state === 'running' ? (
                            <Button
                              variant="ghost" size="icon" className="h-7 w-7"
                              onClick={() => pauseMutation.mutate(agent.agent_type)}
                              disabled={pauseMutation.isPending}
                            >
                              <Pause className="h-3 w-3" />
                            </Button>
                          ) : (
                            <Button
                              variant="ghost" size="icon" className="h-7 w-7"
                              onClick={() => resumeMutation.mutate(agent.agent_type)}
                              disabled={resumeMutation.isPending}
                            >
                              <Play className="h-3 w-3" />
                            </Button>
                          )}
                          <Button
                            variant="ghost" size="icon" className="h-7 w-7"
                            onClick={() => triggerMutation.mutate(agent.agent_type)}
                            disabled={triggerMutation.isPending}
                          >
                            <RotateCcw className="h-3 w-3" />
                          </Button>
                        </div>
                      </div>
                    </div>
                  ))
                ) : (
                  <div className="text-center py-6 text-muted-foreground">
                    <Clock className="h-10 w-10 mx-auto mb-3 opacity-50" />
                    <p className="text-sm">No agent data available</p>
                  </div>
                )}
              </div>
            </CardContent>
          </Card>

          {/* Recent Activity */}
          <Card>
            <CardHeader>
              <CardTitle>Recent Activity</CardTitle>
              <CardDescription>Latest agent execution logs</CardDescription>
            </CardHeader>
            <CardContent>
              {metrics?.recent_logs && metrics.recent_logs.length > 0 ? (
                <div className="space-y-2">
                  {metrics.recent_logs.slice(0, 5).map((log) => (
                    <div
                      key={log.id}
                      className="flex items-center justify-between p-3 border rounded-md text-sm"
                    >
                      <div className="flex items-center gap-3">
                        <div
                          className={`w-2 h-2 rounded-full ${
                            log.status === 'completed'
                              ? 'bg-green-500'
                              : log.status === 'failed'
                              ? 'bg-red-500'
                              : log.status === 'running'
                              ? 'bg-blue-500 animate-pulse'
                              : 'bg-gray-400'
                          }`}
                        />
                        <span className="font-medium capitalize">
                          {log.agent_type.replace(/_/g, ' ')}
                        </span>
                        <span className="text-muted-foreground">
                          {log.items_processed} items
                        </span>
                      </div>
                      <span className="text-muted-foreground">
                        {formatDateTimeMYT(log.started_at)}
                      </span>
                    </div>
                  ))}
                </div>
              ) : (
                <div className="text-center py-6 text-muted-foreground">
                  <p className="text-sm">No recent activity</p>
                </div>
              )}
            </CardContent>
          </Card>
        </>
      )}
    </div>
  );
}
