'use client';

import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import Link from 'next/link';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import {
  Loader2, Zap, DollarSign, Clock, Play, Pause, RotateCcw,
  FileText, AlertTriangle, Users, Wrench, TrendingUp, BarChart3,
  Trophy, BookOpen, ExternalLink,
} from 'lucide-react';
import { getSupabaseClient } from '@/lib/supabase/client';
import {
  fetchAdminDashboard, fetchAgentStatus, pauseAgent, resumeAgent,
  triggerAgent, fetchAdminUsers,
} from '@/lib/api';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import type { AgentStatus, DashboardMetrics } from '@/lib/types';
import { formatDateTimeMYT } from '@/lib/utils';
import { toast } from 'sonner';
import { config } from '@/lib/env';

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

  useEffect(() => {
    const checkAuth = async () => {
      const supabase = getSupabaseClient();
      const { data: { session } } = await supabase.auth.getSession();
      if (!session) {
        router.push('/auth/login?redirectTo=/admin');
        return;
      }
      setAccessToken(session.access_token);
      setIsCheckingAuth(false);
    };
    checkAuth();
  }, [router]);

  const { data: metrics, isLoading: metricsLoading, error: metricsError } = useQuery({
    queryKey: ['admin-dashboard', accessToken],
    queryFn: () => fetchAdminDashboard(accessToken!),
    enabled: !!accessToken,
    refetchInterval: 15000,
  });

  const { data: agents, isLoading: agentsLoading } = useQuery({
    queryKey: ['admin-agents', accessToken],
    queryFn: () => fetchAgentStatus(accessToken!),
    enabled: !!accessToken,
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

  if (metricsError) {
    return (
      <div className="flex items-center justify-center min-h-[50vh]">
        <Card className="max-w-md">
          <CardContent className="p-8 text-center">
            <AlertTriangle className="h-12 w-12 text-yellow-500 mx-auto mb-4" />
            <h2 className="text-xl font-semibold mb-2">Access Denied</h2>
            <p className="text-muted-foreground mb-4">
              You do not have admin access.
            </p>
            <Link href="/dashboard">
              <Button>Return to Dashboard</Button>
            </Link>
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
