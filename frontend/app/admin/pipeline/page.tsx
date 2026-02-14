'use client';

import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import {
  Loader2, Activity, CheckCircle2, XCircle, Clock, AlertTriangle,
  Play, Pause, RefreshCw,
} from 'lucide-react';
import { getSupabaseClient } from '@/lib/supabase/client';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import {
  Table, TableBody, TableCell, TableHead, TableHeader, TableRow,
} from '@/components/ui/table';
import { toast } from 'sonner';
import { formatDateTimeMYT, formatRelativeTime } from '@/lib/utils';
import { config } from '@/lib/env';
import axios from 'axios';

const API_URL = config.apiUrl;

function createClient(token: string) {
  return axios.create({
    baseURL: API_URL,
    headers: { Authorization: `Bearer ${token}`, 'Content-Type': 'application/json' },
  });
}

interface ScraperStatus {
  name: string;
  state: string;
  last_success_at: string | null;
  last_error_at: string | null;
  items_scraped_today: number;
  errors_today: number;
  daily_quota: number;
  quota_used: number;
}

interface PipelineStatus {
  scrapers: ScraperStatus[];
  overall_health: string;
  last_full_run: string | null;
}

export default function PipelineMonitoringPage() {
  const router = useRouter();
  const queryClient = useQueryClient();
  const [accessToken, setAccessToken] = useState<string | null>(null);

  useEffect(() => {
    const supabase = getSupabaseClient();
    supabase.auth.getSession().then(({ data }: { data: { session: { access_token: string } | null } }) => {
      if (data.session?.access_token) setAccessToken(data.session.access_token);
      else router.push('/auth/login?redirectTo=/admin/pipeline');
    });
  }, [router]);

  const { data: pipeline, isLoading } = useQuery({
    queryKey: ['pipeline-status', accessToken],
    queryFn: async () => {
      const client = createClient(accessToken!);
      const { data } = await client.get('/admin/pipeline/status');
      return data as PipelineStatus;
    },
    enabled: !!accessToken,
    refetchInterval: 10000,
  });

  const { data: healthHistory } = useQuery({
    queryKey: ['pipeline-health', accessToken],
    queryFn: async () => {
      const client = createClient(accessToken!);
      const { data } = await client.get('/admin/pipeline/health-history?hours=24');
      return data as Array<{
        id: string; scraper_name: string; status: string;
        response_time_ms: number; checked_at: string; error_message: string | null;
      }>;
    },
    enabled: !!accessToken,
  });

  const triggerMutation = useMutation({
    mutationFn: async (name: string) => {
      const client = createClient(accessToken!);
      await client.post(`/admin/pipeline/scrapers/${name}/trigger`);
    },
    onSuccess: (_, name) => {
      queryClient.invalidateQueries({ queryKey: ['pipeline-status'] });
      toast.success(`${name} triggered`);
    },
    onError: (err: Error) => toast.error(`Trigger failed: ${err.message}`),
  });

  const pauseMutation = useMutation({
    mutationFn: async (name: string) => {
      const client = createClient(accessToken!);
      await client.post(`/admin/pipeline/scrapers/${name}/pause`);
    },
    onSuccess: (_, name) => {
      queryClient.invalidateQueries({ queryKey: ['pipeline-status'] });
      toast.success(`${name} paused`);
    },
    onError: (err: Error) => toast.error(`Pause failed: ${err.message}`),
  });

  if (!accessToken || isLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <Loader2 className="h-6 w-6 animate-spin" />
      </div>
    );
  }

  const healthColor = pipeline?.overall_health === 'healthy' ? 'text-green-500'
    : pipeline?.overall_health === 'degraded' ? 'text-yellow-500'
    : 'text-red-500';

  return (
    <div className="p-6 space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold flex items-center gap-2">
            <Activity className="h-6 w-6" />
            Pipeline Monitoring
          </h1>
          <p className="text-muted-foreground text-sm mt-1">
            Monitor scraper health, quotas, and pipeline status
          </p>
        </div>
        <div className="flex items-center gap-3">
          <Badge variant="outline" className={healthColor}>
            {pipeline?.overall_health || 'unknown'}
          </Badge>
          {pipeline?.last_full_run && (
            <span className="text-xs text-muted-foreground">
              Last run: {formatRelativeTime(pipeline.last_full_run)}
            </span>
          )}
        </div>
      </div>

      {/* Scraper Status Cards */}
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
        {pipeline?.scrapers?.map((scraper) => (
          <Card key={scraper.name}>
            <CardHeader className="pb-2">
              <div className="flex items-center justify-between">
                <CardTitle className="text-base capitalize">
                  {scraper.name.replace(/_/g, ' ')}
                </CardTitle>
                <Badge variant={
                  scraper.state === 'active' ? 'default'
                  : scraper.state === 'paused' ? 'secondary'
                  : 'destructive'
                }>
                  {scraper.state}
                </Badge>
              </div>
            </CardHeader>
            <CardContent>
              <div className="grid gap-3 sm:grid-cols-2 text-sm mb-3">
                <div>
                  <p className="text-muted-foreground">Scraped Today</p>
                  <p className="font-semibold">{scraper.items_scraped_today}</p>
                </div>
                <div>
                  <p className="text-muted-foreground">Errors</p>
                  <p className={`font-semibold ${scraper.errors_today > 0 ? 'text-red-500' : ''}`}>
                    {scraper.errors_today}
                  </p>
                </div>
                <div>
                  <p className="text-muted-foreground">Quota</p>
                  <p className="font-semibold">{scraper.quota_used}/{scraper.daily_quota}</p>
                </div>
                <div>
                  <p className="text-muted-foreground">Last Success</p>
                  <p className="font-semibold text-xs">
                    {scraper.last_success_at ? formatRelativeTime(scraper.last_success_at) : 'Never'}
                  </p>
                </div>
              </div>
              {/* Quota bar */}
              <div className="w-full bg-muted rounded-full h-2 mb-3">
                <div
                  className={`h-full rounded-full ${
                    scraper.quota_used / scraper.daily_quota > 0.9 ? 'bg-red-500'
                    : scraper.quota_used / scraper.daily_quota > 0.7 ? 'bg-yellow-500'
                    : 'bg-green-500'
                  }`}
                  style={{ width: `${Math.min((scraper.quota_used / scraper.daily_quota) * 100, 100)}%` }}
                />
              </div>
              <div className="flex gap-2">
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => triggerMutation.mutate(scraper.name)}
                  disabled={triggerMutation.isPending}
                >
                  <Play className="h-3 w-3 mr-1" /> Run
                </Button>
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => pauseMutation.mutate(scraper.name)}
                  disabled={pauseMutation.isPending}
                >
                  <Pause className="h-3 w-3 mr-1" /> Pause
                </Button>
              </div>
            </CardContent>
          </Card>
        ))}
      </div>

      {/* Health History */}
      <Card>
        <CardHeader>
          <CardTitle className="text-base">Health Check History (24h)</CardTitle>
        </CardHeader>
        <CardContent className="p-0">
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Scraper</TableHead>
                <TableHead>Status</TableHead>
                <TableHead>Response Time</TableHead>
                <TableHead>Checked At</TableHead>
                <TableHead>Error</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {healthHistory?.slice(0, 20).map((check) => (
                <TableRow key={check.id}>
                  <TableCell className="capitalize">{check.scraper_name.replace(/_/g, ' ')}</TableCell>
                  <TableCell>
                    {check.status === 'healthy' ? (
                      <Badge variant="default" className="gap-1"><CheckCircle2 className="h-3 w-3" /> Healthy</Badge>
                    ) : (
                      <Badge variant="destructive" className="gap-1"><XCircle className="h-3 w-3" /> Failed</Badge>
                    )}
                  </TableCell>
                  <TableCell>{check.response_time_ms}ms</TableCell>
                  <TableCell className="text-xs">{formatDateTimeMYT(check.checked_at)}</TableCell>
                  <TableCell className="text-xs text-muted-foreground max-w-[200px] truncate">
                    {check.error_message || '-'}
                  </TableCell>
                </TableRow>
              ))}
              {(!healthHistory || healthHistory.length === 0) && (
                <TableRow>
                  <TableCell colSpan={5} className="text-center py-8 text-muted-foreground">
                    No health checks recorded yet.
                  </TableCell>
                </TableRow>
              )}
            </TableBody>
          </Table>
        </CardContent>
      </Card>
    </div>
  );
}
