'use client';

import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import Link from 'next/link';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { Loader2, Zap, DollarSign, Users, Clock, Play, Pause, RotateCcw, FileText, AlertTriangle } from 'lucide-react';
import { getSupabaseClient } from '@/lib/supabase/client';
import { fetchAdminDashboard, fetchAgentStatus, pauseAgent, resumeAgent, triggerAgent, fetchReviewQueue } from '@/lib/api';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import type { AgentStatus, DashboardMetrics } from '@/lib/types';

export default function AdminDashboard() {
  const router = useRouter();
  const queryClient = useQueryClient();
  const [accessToken, setAccessToken] = useState<string | null>(null);
  const [isCheckingAuth, setIsCheckingAuth] = useState(true);

  // Check authentication
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

  // Fetch dashboard metrics
  const { data: metrics, isLoading: metricsLoading, error: metricsError } = useQuery({
    queryKey: ['admin-dashboard', accessToken],
    queryFn: () => fetchAdminDashboard(accessToken!),
    enabled: !!accessToken,
    refetchInterval: 30000, // Refresh every 30 seconds
  });

  // Fetch agent status
  const { data: agents, isLoading: agentsLoading } = useQuery({
    queryKey: ['admin-agents', accessToken],
    queryFn: () => fetchAgentStatus(accessToken!),
    enabled: !!accessToken,
    refetchInterval: 30000,
  });

  // Agent control mutations
  const pauseMutation = useMutation({
    mutationFn: (agentType: string) => pauseAgent(accessToken!, agentType),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['admin-agents'] });
      queryClient.invalidateQueries({ queryKey: ['admin-dashboard'] });
    },
  });

  const resumeMutation = useMutation({
    mutationFn: (agentType: string) => resumeAgent(accessToken!, agentType),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['admin-agents'] });
      queryClient.invalidateQueries({ queryKey: ['admin-dashboard'] });
    },
  });

  const triggerMutation = useMutation({
    mutationFn: (agentType: string) => triggerAgent(accessToken!, agentType),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['admin-agents'] });
      queryClient.invalidateQueries({ queryKey: ['admin-dashboard'] });
    },
  });

  if (isCheckingAuth) {
    return (
      <div className="min-h-screen bg-background flex items-center justify-center">
        <div className="text-center">
          <Loader2 className="animate-spin h-8 w-8 text-primary mx-auto" />
          <p className="mt-2 text-muted-foreground">Checking admin access...</p>
        </div>
      </div>
    );
  }

  // Handle 403 error (not an admin)
  if (metricsError) {
    return (
      <div className="min-h-screen bg-background flex items-center justify-center">
        <Card className="max-w-md">
          <CardContent className="p-8 text-center">
            <AlertTriangle className="h-12 w-12 text-yellow-500 mx-auto mb-4" />
            <h2 className="text-xl font-semibold mb-2">Access Denied</h2>
            <p className="text-muted-foreground mb-4">
              You do not have admin access. Please contact support if you believe this is an error.
            </p>
            <Link href="/dashboard">
              <Button>Return to Dashboard</Button>
            </Link>
          </CardContent>
        </Card>
      </div>
    );
  }

  const isLoading = metricsLoading || agentsLoading;

  return (
    <div className="min-h-screen bg-background">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Header */}
        <div className="flex justify-between items-center mb-8">
          <div>
            <h1 className="text-3xl font-bold tracking-tight">Admin Dashboard</h1>
            <p className="text-muted-foreground mt-2">
              Monitor system health and manage AI agents
            </p>
          </div>
          <div className="flex gap-2">
            <Link href="/admin/insights">
              <Button variant="outline">
                <FileText className="h-4 w-4 mr-2" />
                Review Queue
              </Button>
            </Link>
          </div>
        </div>

        {isLoading ? (
          <div className="flex items-center justify-center py-12">
            <Loader2 className="animate-spin h-8 w-8 text-primary" />
          </div>
        ) : (
          <>
            {/* System Stats */}
            <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4 mb-8">
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

            {/* Agent Status */}
            <Card className="mb-8">
              <CardHeader>
                <CardTitle>Agent Status</CardTitle>
                <CardDescription>Real-time status of AI processing agents</CardDescription>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  {agents && agents.length > 0 ? (
                    agents.map((agent: AgentStatus) => (
                      <div
                        key={agent.agent_type}
                        className="flex items-center justify-between p-4 border rounded-lg"
                      >
                        <div className="flex items-center gap-4">
                          <div
                            className={`w-3 h-3 rounded-full ${
                              agent.state === 'running'
                                ? 'bg-green-500 animate-pulse'
                                : agent.state === 'paused'
                                ? 'bg-yellow-500'
                                : 'bg-gray-400'
                            }`}
                          />
                          <div>
                            <p className="font-medium capitalize">
                              {agent.agent_type.replace(/_/g, ' ')} Agent
                            </p>
                            <p className="text-sm text-muted-foreground">
                              {agent.last_run
                                ? `Last run: ${new Date(agent.last_run).toLocaleString()}`
                                : 'Never run'}
                            </p>
                          </div>
                        </div>
                        <div className="flex items-center gap-6 text-sm">
                          <div className="text-center">
                            <p className="font-semibold">{agent.items_processed_today}</p>
                            <p className="text-muted-foreground">Items</p>
                          </div>
                          <div className="text-center">
                            <p className="font-semibold text-red-500">{agent.errors_today}</p>
                            <p className="text-muted-foreground">Errors</p>
                          </div>
                          <div className="flex gap-2">
                            {agent.state === 'running' ? (
                              <Button
                                variant="outline"
                                size="sm"
                                onClick={() => pauseMutation.mutate(agent.agent_type)}
                                disabled={pauseMutation.isPending}
                              >
                                <Pause className="h-4 w-4" />
                              </Button>
                            ) : (
                              <Button
                                variant="outline"
                                size="sm"
                                onClick={() => resumeMutation.mutate(agent.agent_type)}
                                disabled={resumeMutation.isPending}
                              >
                                <Play className="h-4 w-4" />
                              </Button>
                            )}
                            <Button
                              variant="outline"
                              size="sm"
                              onClick={() => triggerMutation.mutate(agent.agent_type)}
                              disabled={triggerMutation.isPending}
                            >
                              <RotateCcw className="h-4 w-4" />
                            </Button>
                          </div>
                        </div>
                      </div>
                    ))
                  ) : (
                    <div className="text-center py-8 text-muted-foreground">
                      <Clock className="h-12 w-12 mx-auto mb-4 opacity-50" />
                      <p>No agent data available</p>
                      <p className="text-sm mt-1">Agents will appear here once they start running</p>
                    </div>
                  )}
                </div>
              </CardContent>
            </Card>

            {/* Recent Execution Logs */}
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
                            {log.items_processed} items processed
                          </span>
                        </div>
                        <span className="text-muted-foreground">
                          {new Date(log.started_at).toLocaleTimeString()}
                        </span>
                      </div>
                    ))}
                  </div>
                ) : (
                  <div className="text-center py-8 text-muted-foreground">
                    <p>No recent activity</p>
                  </div>
                )}
              </CardContent>
            </Card>
          </>
        )}
      </div>
    </div>
  );
}
