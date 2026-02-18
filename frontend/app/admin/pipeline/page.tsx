'use client';

import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import {
  Loader2, Activity, CheckCircle2, XCircle, Play, Pause, Save, RotateCcw, Settings2,
} from 'lucide-react';
import { getSupabaseClient } from '@/lib/supabase/client';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import {
  Table, TableBody, TableCell, TableHead, TableHeader, TableRow,
} from '@/components/ui/table';
import { toast } from 'sonner';
import { formatDateTimeMYT, formatRelativeTime } from '@/lib/utils';
import { fetchSystemSettings, updateSystemSetting } from '@/lib/api';
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

// Scraper config shape for the Source Configuration tab
interface ScraperConfig {
  label: string;
  prefix: string;
  fields: { key: string; label: string; type: 'text' | 'number' | 'tags'; description: string }[];
}

const SCRAPER_CONFIGS: ScraperConfig[] = [
  {
    label: 'Reddit',
    prefix: 'scraper.reddit',
    fields: [
      { key: 'subreddits', label: 'Subreddits', type: 'tags', description: 'Comma-separated list of subreddits to scrape' },
      { key: 'posts_per_sub', label: 'Posts per Sub', type: 'number', description: 'Max posts to fetch per subreddit per run' },
      { key: 'min_upvotes', label: 'Min Upvotes', type: 'number', description: 'Minimum upvotes threshold' },
    ],
  },
  {
    label: 'Product Hunt',
    prefix: 'scraper.producthunt',
    fields: [
      { key: 'categories', label: 'Categories', type: 'tags', description: 'Comma-separated categories to monitor' },
      { key: 'items_per_run', label: 'Items per Run', type: 'number', description: 'Max products per scrape' },
    ],
  },
  {
    label: 'Hacker News',
    prefix: 'scraper.hackernews',
    fields: [
      { key: 'min_score', label: 'Min Score', type: 'number', description: 'Minimum HN score' },
      { key: 'max_results', label: 'Max Results', type: 'number', description: 'Max stories per run' },
      { key: 'story_types', label: 'Story Types', type: 'tags', description: 'Types: top, best, new, ask, show, job' },
    ],
  },
  {
    label: 'Twitter / X',
    prefix: 'scraper.twitter',
    fields: [
      { key: 'search_queries', label: 'Search Queries', type: 'tags', description: 'Comma-separated search queries' },
    ],
  },
  {
    label: 'Google Trends',
    prefix: 'scraper.google_trends',
    fields: [
      { key: 'regions', label: 'Regions', type: 'tags', description: 'ISO country codes (US, GB, DE, etc.)' },
      { key: 'keywords', label: 'Keywords', type: 'tags', description: 'Comma-separated keywords to track' },
    ],
  },
];

export default function PipelineMonitoringPage() {
  const router = useRouter();
  const queryClient = useQueryClient();
  const [accessToken, setAccessToken] = useState<string | null>(null);
  const [configEdits, setConfigEdits] = useState<Record<string, string | number | string[]>>({});
  const [activeTab, setActiveTab] = useState('monitoring');

  useEffect(() => {
    const supabase = getSupabaseClient();
    supabase.auth.getSession().then(({ data }: { data: { session: { access_token: string } | null } }) => {
      if (data.session?.access_token) setAccessToken(data.session.access_token);
      else router.push('/auth/login?redirectTo=/admin/pipeline');
    });
  }, [router]);

  // Pipeline status + health history
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

  // Scraper settings from system_settings
  const { data: allSettings } = useQuery({
    queryKey: ['system-settings'],
    queryFn: () => fetchSystemSettings(accessToken!),
    enabled: !!accessToken,
  });

  const scraperSettings = allSettings?.settings?.scraper ?? [];

  // Get setting value (from edits or from server)
  function getSettingValue(fullKey: string): string | number | string[] {
    if (fullKey in configEdits) return configEdits[fullKey];
    const found = scraperSettings.find((s: { key: string }) => s.key === fullKey);
    return (found?.value as string | number | string[]) ?? '';
  }

  function setSettingEdit(fullKey: string, value: string | number | string[]) {
    setConfigEdits(prev => ({ ...prev, [fullKey]: value }));
  }

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

  const [savingConfig, setSavingConfig] = useState(false);

  async function saveAllConfigEdits() {
    if (!accessToken || Object.keys(configEdits).length === 0) return;
    setSavingConfig(true);
    try {
      for (const [key, value] of Object.entries(configEdits)) {
        await updateSystemSetting(accessToken, key, value);
      }
      setConfigEdits({});
      queryClient.invalidateQueries({ queryKey: ['system-settings'] });
      toast.success(`Saved ${Object.keys(configEdits).length} setting(s)`);
    } catch (err) {
      toast.error(`Save failed: ${err instanceof Error ? err.message : 'Unknown error'}`);
    } finally {
      setSavingConfig(false);
    }
  }

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

  const dirtyCount = Object.keys(configEdits).length;

  return (
    <div className="p-6 space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold flex items-center gap-2">
            <Activity className="h-6 w-6" />
            Pipeline Monitoring
          </h1>
          <p className="text-muted-foreground text-sm mt-1">
            Monitor scraper health, quotas, and configure data sources
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

      <Tabs value={activeTab} onValueChange={setActiveTab}>
        <TabsList>
          <TabsTrigger value="monitoring">Monitoring</TabsTrigger>
          <TabsTrigger value="config" className="gap-1.5">
            <Settings2 className="h-3.5 w-3.5" />
            Source Config
            {dirtyCount > 0 && (
              <Badge variant="secondary" className="ml-1 h-5 px-1.5 text-xs">{dirtyCount}</Badge>
            )}
          </TabsTrigger>
        </TabsList>

        {/* ========== MONITORING TAB ========== */}
        <TabsContent value="monitoring" className="space-y-6 mt-4">
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
              <div className="overflow-x-auto">
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
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        {/* ========== SOURCE CONFIG TAB ========== */}
        <TabsContent value="config" className="space-y-6 mt-4">
          {dirtyCount > 0 && (
            <div className="flex items-center justify-between p-3 bg-muted/50 rounded-lg border">
              <p className="text-sm text-muted-foreground">
                {dirtyCount} unsaved change{dirtyCount !== 1 ? 's' : ''}
              </p>
              <div className="flex gap-2">
                <Button variant="ghost" size="sm" onClick={() => setConfigEdits({})}>
                  <RotateCcw className="h-3.5 w-3.5 mr-1" /> Reset
                </Button>
                <Button size="sm" onClick={saveAllConfigEdits} disabled={savingConfig}>
                  {savingConfig ? <Loader2 className="h-3.5 w-3.5 mr-1 animate-spin" /> : <Save className="h-3.5 w-3.5 mr-1" />}
                  Save {dirtyCount} Change{dirtyCount !== 1 ? 's' : ''}
                </Button>
              </div>
            </div>
          )}

          <div className="grid gap-4 md:grid-cols-2">
            {SCRAPER_CONFIGS.map((scraper) => (
              <Card key={scraper.prefix}>
                <CardHeader className="pb-3">
                  <CardTitle className="text-base">{scraper.label}</CardTitle>
                  <CardDescription>Configure {scraper.label} data source parameters</CardDescription>
                </CardHeader>
                <CardContent className="space-y-4">
                  {scraper.fields.map((field) => {
                    const fullKey = `${scraper.prefix}.${field.key}`;
                    const currentValue = getSettingValue(fullKey);

                    if (field.type === 'tags') {
                      const tags = Array.isArray(currentValue) ? currentValue : (typeof currentValue === 'string' ? currentValue.split(',').map(s => s.trim()).filter(Boolean) : []);
                      return (
                        <div key={fullKey} className="space-y-1.5">
                          <Label className="text-sm">{field.label}</Label>
                          <Input
                            value={tags.join(', ')}
                            onChange={(e) => {
                              const newTags = e.target.value.split(',').map(s => s.trim()).filter(Boolean);
                              setSettingEdit(fullKey, newTags);
                            }}
                            placeholder={field.description}
                            className="text-sm"
                          />
                          <p className="text-[11px] text-muted-foreground">{field.description}</p>
                        </div>
                      );
                    }

                    return (
                      <div key={fullKey} className="space-y-1.5">
                        <Label className="text-sm">{field.label}</Label>
                        <Input
                          type="number"
                          value={typeof currentValue === 'number' ? currentValue : Number(currentValue) || 0}
                          onChange={(e) => setSettingEdit(fullKey, parseInt(e.target.value) || 0)}
                          className="text-sm"
                        />
                        <p className="text-[11px] text-muted-foreground">{field.description}</p>
                      </div>
                    );
                  })}
                </CardContent>
              </Card>
            ))}
          </div>
        </TabsContent>
      </Tabs>
    </div>
  );
}
