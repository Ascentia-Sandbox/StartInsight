'use client';

import { useState, useEffect, useRef, useCallback } from 'react';
import { useRouter } from 'next/navigation';
import Link from 'next/link';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import {
  Loader2,
  Bot,
  Play,
  Pause,
  RotateCcw,
  Settings2,
  AlertTriangle,
  ArrowLeft,
  CheckCircle2,
  XCircle,
  Clock,
  Zap,
  Shield,
  Plus,
  Pencil,
  Trash2,
  Eye,
  FileText,
  BookOpen,
  Star,
  Sparkles,
  BarChart3,
  Lightbulb,
  Search,
  Maximize2,
  Minimize2,
  ScrollText,
  X,
  DollarSign,
  Radio,
} from 'lucide-react';
import { getSupabaseClient } from '@/lib/supabase/client';
import {
  fetchAgentConfigurations,
  updateAgentConfiguration,
  createAgentConfiguration,
  deleteAgentConfiguration,
  toggleAgentEnabled,
  fetchAgentExecutionStats,
  fetchAgentCostAnalytics,
  updateAgentSchedule,
  fetchAgentStatus,
  fetchAgentLogs,
  pauseAgent,
  resumeAgent,
  triggerAgent,
  type AgentConfig,
  type AgentStats,
  type AgentExecutionLog,
  type CostAnalytics,
} from '@/lib/api';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Switch } from '@/components/ui/switch';
import { Input } from '@/components/ui/input';
import { Textarea } from '@/components/ui/textarea';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog';
import {
  Sheet,
  SheetContent,
  SheetDescription,
  SheetHeader,
  SheetTitle,
  SheetFooter,
} from '@/components/ui/sheet';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import { Label } from '@/components/ui/label';
import { Checkbox } from '@/components/ui/checkbox';
import type { AgentStatus } from '@/lib/types';
import { toast } from 'sonner';
import { formatDateTimeMYT, formatDateMYT, formatRelativeTime } from '@/lib/utils';
import { config } from '@/lib/env';

const API_URL = config.apiUrl;

// ============================================================================
// Market Insights Types & Helpers
// ============================================================================

interface MarketInsight {
  id: string;
  title: string;
  slug: string;
  summary: string;
  content: string;
  category: string;
  author_name: string;
  author_avatar_url: string | null;
  cover_image_url: string | null;
  reading_time_minutes: number;
  view_count: number;
  is_featured: boolean;
  is_published: boolean;
  published_at: string | null;
  created_at: string;
}

interface InsightItem {
  id: string;
  slug?: string;
  proposed_solution: string;
  problem_statement: string;
  relevance_score: number;
  opportunity_score: number | null;
  feasibility_score: number | null;
  founder_fit_score: number | null;
  market_size_estimate: string | null;
  created_at: string;
}

const MI_CATEGORIES = ['Trends', 'Analysis', 'Guides', 'Case Studies'];
const AI_MODELS = [
  'gemini-1.5-flash',
  'gemini-1.5-pro',
  'claude-3-5-sonnet-20250122',
  'claude-3-haiku-20241022',
  'gpt-4o',
  'gpt-4o-mini',
];

function generateSlug(title: string): string {
  return title
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, '-')
    .replace(/(^-|-$)/g, '')
    .slice(0, 200);
}


// ============================================================================
// Main Page Component
// ============================================================================

export default function AgentCommandCenter() {
  const router = useRouter();
  const queryClient = useQueryClient();
  const [accessToken, setAccessToken] = useState<string | null>(null);
  const [isCheckingAuth, setIsCheckingAuth] = useState(true);

  // Agent editing state
  const [editingAgent, setEditingAgent] = useState<AgentConfig | null>(null);
  const [isFullView, setIsFullView] = useState(false);
  const [agentEditForm, setAgentEditForm] = useState({
    model_name: '',
    temperature: 0.7,
    max_tokens: 4096,
    rate_limit_per_hour: 100,
    cost_limit_daily_usd: 50,
    system_prompt: '',
    description: '',
    schedule: '',
    schedule_type: 'manual' as string,
    schedule_cron: '',
    schedule_interval_hours: 6,
  });
  const [costPeriod, setCostPeriod] = useState<'7d' | '30d' | '90d'>('7d');

  // Agent create state
  const [createDialogOpen, setCreateDialogOpen] = useState(false);
  const [createForm, setCreateForm] = useState({
    agent_name: '',
    model_name: 'gemini-1.5-flash',
    temperature: 0.7,
    max_tokens: 4096,
    rate_limit_per_hour: 100,
    cost_limit_daily_usd: 50,
    description: '',
    schedule: '',
  });

  // Agent delete state
  const [deleteDialogOpen, setDeleteDialogOpen] = useState(false);
  const [deletingAgent, setDeletingAgent] = useState<AgentConfig | null>(null);

  // Agent logs state
  const [logsAgent, setLogsAgent] = useState<string | null>(null);
  const [liveStream, setLiveStream] = useState(false);
  const [streamLogs, setStreamLogs] = useState<Array<{ id: string; status: string; started_at: string; duration_ms?: number; items_processed: number; error_message?: string; source?: string }>>([]);
  const [streamPaused, setStreamPaused] = useState(false);
  const streamRef = useRef<AbortController | null>(null);
  const terminalRef = useRef<HTMLDivElement>(null);

  // Market Insights state
  const [miDialogOpen, setMiDialogOpen] = useState(false);
  const [miFullView, setMiFullView] = useState(false);
  const [miDeleteDialogOpen, setMiDeleteDialogOpen] = useState(false);
  const [editingMi, setEditingMi] = useState<MarketInsight | null>(null);
  const [deletingMi, setDeletingMi] = useState<MarketInsight | null>(null);
  const [miForm, setMiForm] = useState({
    title: '',
    slug: '',
    summary: '',
    content: '',
    category: '',
    author_name: 'StartInsight AI',
    reading_time_minutes: 5,
    is_featured: false,
    is_published: true,
  });
  const [miSearchQuery, setMiSearchQuery] = useState('');

  // Insight management state
  const [insightDeleteDialogOpen, setInsightDeleteDialogOpen] = useState(false);
  const [deletingInsight, setDeletingInsight] = useState<InsightItem | null>(null);
  const [insightSearchQuery, setInsightSearchQuery] = useState('');

  // Log filter state
  const [logStatusFilter, setLogStatusFilter] = useState<string>('all');
  const [logSearchQuery, setLogSearchQuery] = useState('');

  // Auth check
  useEffect(() => {
    const checkAuth = async () => {
      const supabase = getSupabaseClient();
      const { data: { session } } = await supabase.auth.getSession();
      if (!session) {
        router.push('/auth/login?redirectTo=/admin/agents');
        return;
      }
      setAccessToken(session.access_token);
      setIsCheckingAuth(false);
    };
    checkAuth();
  }, [router]);

  // ========== AGENT TRIGGER POLLING ==========
  const [pollingAgent, setPollingAgent] = useState<string | null>(null);
  const pollTimerRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  const pollForResult = useCallback((agentType: string, attempt = 0) => {
    if (attempt >= 10 || !accessToken) {
      setPollingAgent(null);
      toast.info(`${agentType.replace(/_/g, ' ')} is still running — check logs for result`);
      return;
    }
    pollTimerRef.current = setTimeout(async () => {
      try {
        const result = await fetchAgentLogs(accessToken, agentType, 1, 0);
        const latest = result.items[0];
        if (latest?.status === 'completed') {
          setPollingAgent(null);
          const duration = latest.duration_ms ? `${(latest.duration_ms / 1000).toFixed(1)}s` : '';
          toast.success(`${agentType.replace(/_/g, ' ')} completed`, {
            description: `${latest.items_processed} items processed${duration ? ` in ${duration}` : ''}`,
          });
          queryClient.invalidateQueries({ queryKey: ['admin-agents'] });
          return;
        }
        if (latest?.status === 'failed') {
          setPollingAgent(null);
          toast.error(`${agentType.replace(/_/g, ' ')} failed`, {
            description: latest.error_message?.slice(0, 100) || 'Unknown error',
          });
          return;
        }
        pollForResult(agentType, attempt + 1);
      } catch {
        pollForResult(agentType, attempt + 1);
      }
    }, 3000);
  }, [accessToken, queryClient]);

  useEffect(() => {
    return () => {
      if (pollTimerRef.current) clearTimeout(pollTimerRef.current);
    };
  }, []);

  // ========== AGENT QUERIES ==========
  const { data: configs, isLoading: configsLoading, error: configsError } = useQuery({
    queryKey: ['agent-configs', accessToken],
    queryFn: () => fetchAgentConfigurations(accessToken!),
    enabled: !!accessToken,
    refetchInterval: 10000,
  });

  const { data: agentStatuses } = useQuery({
    queryKey: ['admin-agents', accessToken],
    queryFn: () => fetchAgentStatus(accessToken!),
    enabled: !!accessToken,
    refetchInterval: 10000,
  });

  const { data: stats } = useQuery({
    queryKey: ['agent-stats', accessToken],
    queryFn: () => fetchAgentExecutionStats(accessToken!),
    enabled: !!accessToken,
    refetchInterval: 15000,
  });

  const { data: costData } = useQuery({
    queryKey: ['agent-costs', accessToken, costPeriod],
    queryFn: () => fetchAgentCostAnalytics(accessToken!, costPeriod),
    enabled: !!accessToken,
  });

  // ========== AGENT LOGS QUERY ==========
  const { data: logsData, isLoading: logsLoading } = useQuery({
    queryKey: ['agent-logs', logsAgent, accessToken],
    queryFn: () => fetchAgentLogs(accessToken!, logsAgent!, 50),
    enabled: !!accessToken && !!logsAgent,
  });

  // ========== MARKET INSIGHTS QUERIES ==========
  const { data: miData, isLoading: miLoading } = useQuery({
    queryKey: ['admin-market-insights', accessToken],
    queryFn: async () => {
      const res = await fetch(`${API_URL}/api/market-insights?limit=50`);
      const data = await res.json();
      return (data.articles || []) as MarketInsight[];
    },
    enabled: !!accessToken,
  });

  // ========== INSIGHTS QUERIES ==========
  const { data: insightsData, isLoading: insightsLoading } = useQuery({
    queryKey: ['admin-insights-list', accessToken],
    queryFn: async () => {
      const res = await fetch(`${API_URL}/api/insights?limit=100`);
      const data = await res.json();
      return (data.insights || []) as InsightItem[];
    },
    enabled: !!accessToken,
  });

  // ========== LIVE LOG STREAMING ==========
  useEffect(() => {
    if (!liveStream || !logsAgent || !accessToken) return;

    const controller = new AbortController();
    streamRef.current = controller;
    setStreamLogs([]);

    const connect = async () => {
      try {
        const res = await fetch(`${API_URL}/admin/agents/${logsAgent}/logs/stream`, {
          headers: { Authorization: `Bearer ${accessToken}` },
          signal: controller.signal,
        });
        if (!res.body) return;
        const reader = res.body.getReader();
        const decoder = new TextDecoder();
        let buffer = '';

        while (true) {
          const { done, value } = await reader.read();
          if (done) break;
          buffer += decoder.decode(value, { stream: true });
          const lines = buffer.split('\n');
          buffer = lines.pop() || '';

          for (const line of lines) {
            if (line.startsWith('data:') && !streamPaused) {
              const raw = line.slice(5).trim();
              if (!raw) continue;
              try {
                const entry = JSON.parse(raw);
                if (entry.id) {
                  setStreamLogs((prev) => {
                    const exists = prev.some((l) => l.id === entry.id);
                    if (exists) return prev;
                    const next = [...prev, entry].slice(-100);
                    return next;
                  });
                }
              } catch { /* skip non-JSON */ }
            }
          }
        }
      } catch (err: unknown) {
        if (err instanceof Error && err.name !== 'AbortError') {
          console.error('SSE stream error:', err);
        }
      }
    };
    connect();

    return () => { controller.abort(); streamRef.current = null; };
  }, [liveStream, logsAgent, accessToken, streamPaused]);

  // Auto-scroll terminal
  useEffect(() => {
    if (terminalRef.current && !streamPaused) {
      terminalRef.current.scrollTop = terminalRef.current.scrollHeight;
    }
  }, [streamLogs, streamPaused]);

  // ========== AGENT MUTATIONS ==========
  const toggleMutation = useMutation({
    mutationFn: (agentName: string) => toggleAgentEnabled(accessToken!, agentName),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['agent-configs'] });
      queryClient.invalidateQueries({ queryKey: ['admin-agents'] });
    },
  });

  const updateMutation = useMutation({
    mutationFn: ({ name, data }: { name: string; data: Record<string, unknown> }) =>
      updateAgentConfiguration(accessToken!, name, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['agent-configs'] });
      setEditingAgent(null);
      setIsFullView(false);
      toast.success('Agent configuration updated');
    },
    onError: () => toast.error('Failed to update agent'),
  });

  const createMutation = useMutation({
    mutationFn: (payload: Parameters<typeof createAgentConfiguration>[1]) =>
      createAgentConfiguration(accessToken!, payload),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['agent-configs'] });
      setCreateDialogOpen(false);
      toast.success('Agent created');
    },
    onError: (err: Error & { response?: { data?: { detail?: string } } }) =>
      toast.error(err.response?.data?.detail || 'Failed to create agent'),
  });

  const deleteMutation = useMutation({
    mutationFn: (agentName: string) => deleteAgentConfiguration(accessToken!, agentName),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['agent-configs'] });
      setDeleteDialogOpen(false);
      setDeletingAgent(null);
      toast.success('Agent deleted');
    },
    onError: () => toast.error('Failed to delete agent'),
  });

  const pauseMutation = useMutation({
    mutationFn: (agentType: string) => pauseAgent(accessToken!, agentType),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['admin-agents'] });
      toast.success('Agent paused');
    },
    onError: () => toast.error('Failed to pause agent'),
  });

  const resumeMutation = useMutation({
    mutationFn: (agentType: string) => resumeAgent(accessToken!, agentType),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['admin-agents'] });
      toast.success('Agent resumed');
    },
    onError: () => toast.error('Failed to resume agent'),
  });

  const triggerMutation = useMutation({
    mutationFn: (agentType: string) => triggerAgent(accessToken!, agentType),
    onSuccess: (_data, agentType) => {
      queryClient.invalidateQueries({ queryKey: ['admin-agents'] });
      queryClient.invalidateQueries({ queryKey: ['agent-logs', agentType] });
      toast.success(`${agentType.replace(/_/g, ' ')} triggered — polling for result...`);
      setPollingAgent(agentType);
      pollForResult(agentType);
    },
    onError: (err: Error, agentType) => toast.error(`Failed to trigger "${agentType.replace(/_/g, ' ')}"`, {
      description: err.message,
    }),
  });

  // ========== AGENT HELPERS ==========
  const getAgentRuntime = (agentName: string): AgentStatus | undefined => {
    return agentStatuses?.find((a: AgentStatus) => a.agent_type === agentName);
  };

  const getAgentStats = (agentName: string): AgentStats | undefined => {
    return stats?.find((s: AgentStats) => s.agent_name === agentName);
  };

  const scheduleMutation = useMutation({
    mutationFn: ({ name, payload }: { name: string; payload: { schedule_type: string; schedule_cron?: string; schedule_interval_hours?: number } }) =>
      updateAgentSchedule(accessToken!, name, payload),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['agent-configs'] });
      toast.success('Schedule updated');
    },
    onError: (err: Error) => toast.error(`Schedule update failed: ${err.message}`),
  });

  const openAgentEditDialog = (agent: AgentConfig) => {
    setEditingAgent(agent);
    setAgentEditForm({
      model_name: agent.model_name,
      temperature: agent.temperature,
      max_tokens: agent.max_tokens,
      rate_limit_per_hour: agent.rate_limit_per_hour,
      cost_limit_daily_usd: agent.cost_limit_daily_usd,
      system_prompt: typeof agent.custom_prompts?.system_prompt === 'string' ? agent.custom_prompts.system_prompt : '',
      description: typeof agent.custom_prompts?.description === 'string' ? agent.custom_prompts.description : '',
      schedule: typeof agent.custom_prompts?.schedule === 'string' ? agent.custom_prompts.schedule : '',
      schedule_type: agent.schedule_type || 'manual',
      schedule_cron: agent.schedule_cron || '',
      schedule_interval_hours: agent.schedule_interval_hours || 6,
    });
  };

  const handleSaveAgent = () => {
    if (!editingAgent) return;
    updateMutation.mutate({
      name: editingAgent.agent_name,
      data: {
        model_name: agentEditForm.model_name,
        temperature: agentEditForm.temperature,
        max_tokens: agentEditForm.max_tokens,
        rate_limit_per_hour: agentEditForm.rate_limit_per_hour,
        cost_limit_daily_usd: agentEditForm.cost_limit_daily_usd,
        custom_prompts: {
          ...editingAgent.custom_prompts,
          system_prompt: agentEditForm.system_prompt || undefined,
          description: agentEditForm.description || undefined,
          schedule: agentEditForm.schedule || undefined,
        },
      },
    });
  };

  const handleCreateAgent = () => {
    createMutation.mutate({
      agent_name: createForm.agent_name.toLowerCase().replace(/\s+/g, '_'),
      model_name: createForm.model_name,
      temperature: createForm.temperature,
      max_tokens: createForm.max_tokens,
      rate_limit_per_hour: createForm.rate_limit_per_hour,
      cost_limit_daily_usd: createForm.cost_limit_daily_usd,
      custom_prompts: {
        description: createForm.description || undefined,
        schedule: createForm.schedule || undefined,
      },
    });
  };

  // ========== MARKET INSIGHTS CRUD ==========
  const handleMiCreate = () => {
    setEditingMi(null);
    setMiForm({
      title: '',
      slug: '',
      summary: '',
      content: '',
      category: '',
      author_name: 'StartInsight AI',
      reading_time_minutes: 5,
      is_featured: false,
      is_published: true,
    });
    setMiDialogOpen(true);
  };

  const handleMiEdit = (article: MarketInsight) => {
    setEditingMi(article);
    setMiForm({
      title: article.title,
      slug: article.slug,
      summary: article.summary,
      content: article.content,
      category: article.category,
      author_name: article.author_name,
      reading_time_minutes: article.reading_time_minutes,
      is_featured: article.is_featured,
      is_published: article.is_published,
    });
    setMiDialogOpen(true);
  };

  const handleMiSubmit = async () => {
    try {
      const url = editingMi
        ? `${API_URL}/api/market-insights/${editingMi.id}`
        : `${API_URL}/api/market-insights`;
      const method = editingMi ? 'PATCH' : 'POST';

      const res = await fetch(url, {
        method,
        headers: { 'Content-Type': 'application/json', Authorization: `Bearer ${accessToken}` },
        body: JSON.stringify({
          ...miForm,
          slug: miForm.slug || generateSlug(miForm.title),
        }),
      });

      if (res.ok) {
        toast.success(editingMi ? 'Article updated' : 'Article created');
        setMiDialogOpen(false);
        setMiFullView(false);
        queryClient.invalidateQueries({ queryKey: ['admin-market-insights'] });
      } else {
        const err = await res.json();
        toast.error(err.detail || 'Failed to save article');
      }
    } catch {
      toast.error('Failed to save article');
    }
  };

  const handleMiDelete = async () => {
    if (!deletingMi) return;
    try {
      const res = await fetch(`${API_URL}/api/market-insights/${deletingMi.id}`, {
        method: 'DELETE',
        headers: { Authorization: `Bearer ${accessToken}` },
      });
      if (res.ok || res.status === 204) {
        toast.success('Article deleted');
        queryClient.invalidateQueries({ queryKey: ['admin-market-insights'] });
      } else {
        toast.error('Failed to delete article');
      }
    } catch {
      toast.error('Failed to delete article');
    } finally {
      setMiDeleteDialogOpen(false);
      setDeletingMi(null);
    }
  };

  // ========== INSIGHT DELETE ==========
  const handleInsightDelete = async () => {
    if (!deletingInsight || !accessToken) return;
    try {
      const res = await fetch(`${API_URL}/api/admin/insights/${deletingInsight.id}`, {
        method: 'DELETE',
        headers: { Authorization: `Bearer ${accessToken}` },
      });
      if (res.ok || res.status === 204) {
        toast.success('Insight deleted');
        queryClient.invalidateQueries({ queryKey: ['admin-insights-list'] });
      } else {
        toast.error('Failed to delete insight');
      }
    } catch {
      toast.error('Failed to delete insight');
    } finally {
      setInsightDeleteDialogOpen(false);
      setDeletingInsight(null);
    }
  };

  // ========== FILTERED DATA ==========
  const filteredMi = (miData || []).filter((a) =>
    !miSearchQuery || a.title.toLowerCase().includes(miSearchQuery.toLowerCase())
  );

  const filteredInsights = (insightsData || []).filter((i) =>
    !insightSearchQuery || i.proposed_solution?.toLowerCase().includes(insightSearchQuery.toLowerCase())
  );

  // ========== AGENT EDIT FORM CONTENT (shared between Dialog and Sheet) ==========
  const AgentEditFormContent = () => (
    <Tabs defaultValue="general" className="w-full">
      <TabsList className="mb-4 w-full grid grid-cols-3">
        <TabsTrigger value="general">General</TabsTrigger>
        <TabsTrigger value="prompts">Prompts</TabsTrigger>
        <TabsTrigger value="limits">Limits</TabsTrigger>
      </TabsList>

      <TabsContent value="general" className="space-y-4">
        <div className="space-y-2">
          <Label>Description</Label>
          <Input
            value={agentEditForm.description}
            onChange={(e) => setAgentEditForm({ ...agentEditForm, description: e.target.value })}
            placeholder="What does this agent do?"
          />
        </div>
        <div className="space-y-2">
          <Label>Schedule Type</Label>
          <Select value={agentEditForm.schedule_type} onValueChange={(v) => setAgentEditForm({ ...agentEditForm, schedule_type: v })}>
            <SelectTrigger><SelectValue /></SelectTrigger>
            <SelectContent>
              <SelectItem value="manual">Manual Only</SelectItem>
              <SelectItem value="interval">Interval (every N hours)</SelectItem>
              <SelectItem value="cron">Custom Cron</SelectItem>
            </SelectContent>
          </Select>
        </div>
        {agentEditForm.schedule_type === 'interval' && (
          <div className="space-y-2">
            <Label>Run Every (hours)</Label>
            <Select value={String(agentEditForm.schedule_interval_hours)} onValueChange={(v) => setAgentEditForm({ ...agentEditForm, schedule_interval_hours: parseInt(v) })}>
              <SelectTrigger><SelectValue /></SelectTrigger>
              <SelectContent>
                <SelectItem value="1">Every 1 hour</SelectItem>
                <SelectItem value="3">Every 3 hours</SelectItem>
                <SelectItem value="6">Every 6 hours</SelectItem>
                <SelectItem value="12">Every 12 hours</SelectItem>
                <SelectItem value="24">Daily (24h)</SelectItem>
                <SelectItem value="72">Every 3 days</SelectItem>
                <SelectItem value="168">Weekly</SelectItem>
              </SelectContent>
            </Select>
          </div>
        )}
        {agentEditForm.schedule_type === 'cron' && (
          <div className="space-y-2">
            <Label>Cron Expression</Label>
            <Input
              value={agentEditForm.schedule_cron}
              onChange={(e) => setAgentEditForm({ ...agentEditForm, schedule_cron: e.target.value })}
              placeholder="0 8 * * * (daily at 8am UTC)"
              className="font-mono"
            />
            <p className="text-xs text-muted-foreground">Format: minute hour day month weekday</p>
          </div>
        )}
        {editingAgent && (
          <Button
            variant="outline"
            size="sm"
            onClick={() => scheduleMutation.mutate({
              name: editingAgent.agent_name,
              payload: {
                schedule_type: agentEditForm.schedule_type,
                ...(agentEditForm.schedule_type === 'cron' ? { schedule_cron: agentEditForm.schedule_cron } : {}),
                ...(agentEditForm.schedule_type === 'interval' ? { schedule_interval_hours: agentEditForm.schedule_interval_hours } : {}),
              },
            })}
            disabled={scheduleMutation.isPending}
          >
            {scheduleMutation.isPending ? <Loader2 className="h-3 w-3 mr-1 animate-spin" /> : <Clock className="h-3 w-3 mr-1" />}
            Save Schedule
          </Button>
        )}
        {editingAgent?.next_run_at && (
          <p className="text-xs text-muted-foreground">Next run: {formatDateTimeMYT(editingAgent.next_run_at)}</p>
        )}
        {editingAgent?.last_run_at && (
          <p className="text-xs text-muted-foreground">Last run: {formatDateTimeMYT(editingAgent.last_run_at)}</p>
        )}
        <div className="space-y-2">
          <Label>AI Model (API)</Label>
          <Select value={agentEditForm.model_name} onValueChange={(v) => setAgentEditForm({ ...agentEditForm, model_name: v })}>
            <SelectTrigger>
              <SelectValue placeholder="Select model" />
            </SelectTrigger>
            <SelectContent>
              {AI_MODELS.map((m) => (
                <SelectItem key={m} value={m}>{m}</SelectItem>
              ))}
            </SelectContent>
          </Select>
        </div>
        <div className="grid gap-4 sm:grid-cols-2">
          <div className="space-y-2">
            <Label>Temperature</Label>
            <Input type="number" step="0.1" min="0" max="2"
              value={agentEditForm.temperature}
              onChange={(e) => setAgentEditForm({ ...agentEditForm, temperature: parseFloat(e.target.value) || 0 })}
            />
          </div>
          <div className="space-y-2">
            <Label>Max Tokens</Label>
            <Input type="number" min="100" max="32000"
              value={agentEditForm.max_tokens}
              onChange={(e) => setAgentEditForm({ ...agentEditForm, max_tokens: parseInt(e.target.value) || 4096 })}
            />
          </div>
        </div>
      </TabsContent>

      <TabsContent value="prompts" className="space-y-4">
        <div className="space-y-2">
          <Label>System Prompt</Label>
          <Textarea
            value={agentEditForm.system_prompt}
            onChange={(e) => setAgentEditForm({ ...agentEditForm, system_prompt: e.target.value })}
            placeholder="Enter the system prompt that guides this agent's behavior..."
            rows={isFullView ? 20 : 12}
            className="font-mono text-sm leading-relaxed"
          />
          <div className="flex items-center justify-between">
            <p className="text-xs text-muted-foreground">
              Leave empty to use the default built-in prompt.
            </p>
            <p className="text-xs text-muted-foreground">
              {agentEditForm.system_prompt.length} characters
            </p>
          </div>
        </div>
      </TabsContent>

      <TabsContent value="limits" className="space-y-4">
        <div className="grid gap-4 sm:grid-cols-2">
          <div className="space-y-2">
            <Label>Rate Limit (per hour)</Label>
            <Input type="number" min="1" max="1000"
              value={agentEditForm.rate_limit_per_hour}
              onChange={(e) => setAgentEditForm({ ...agentEditForm, rate_limit_per_hour: parseInt(e.target.value) || 10 })}
            />
          </div>
          <div className="space-y-2">
            <Label>Cost Limit ($/day)</Label>
            <Input type="number" min="1" max="1000"
              value={agentEditForm.cost_limit_daily_usd}
              onChange={(e) => setAgentEditForm({ ...agentEditForm, cost_limit_daily_usd: parseFloat(e.target.value) || 10 })}
            />
          </div>
        </div>
      </TabsContent>
    </Tabs>
  );

  // ========== MI EDIT FORM CONTENT (shared between Dialog and Sheet) ==========
  const MiEditFormContent = () => (
    <Tabs defaultValue="content" className="w-full">
      <TabsList className="mb-4">
        <TabsTrigger value="content">Content</TabsTrigger>
        <TabsTrigger value="meta">Meta & Settings</TabsTrigger>
      </TabsList>

      <TabsContent value="content" className="space-y-4">
        <div className="space-y-2">
          <Label>Title</Label>
          <Input value={miForm.title}
            onChange={(e) => setMiForm({ ...miForm, title: e.target.value, slug: miForm.slug || generateSlug(e.target.value) })}
            placeholder="AI Code Review Market Hits $2.3B"
          />
        </div>
        <div className="space-y-2">
          <Label>Summary</Label>
          <Textarea value={miForm.summary}
            onChange={(e) => setMiForm({ ...miForm, summary: e.target.value })}
            placeholder="Brief article summary..."
            rows={2}
          />
        </div>
        <div className="space-y-2">
          <Label>Content (Markdown)</Label>
          <Textarea value={miForm.content}
            onChange={(e) => setMiForm({ ...miForm, content: e.target.value })}
            placeholder="## Introduction&#10;&#10;Write your article..."
            rows={miFullView ? 30 : 16}
            className="font-mono text-sm"
          />
        </div>
      </TabsContent>

      <TabsContent value="meta" className="space-y-4">
        <div className="grid gap-4 sm:grid-cols-2">
          <div className="space-y-2">
            <Label>URL Slug</Label>
            <Input value={miForm.slug}
              onChange={(e) => setMiForm({ ...miForm, slug: e.target.value })}
            />
          </div>
          <div className="space-y-2">
            <Label>Category</Label>
            <Select value={miForm.category} onValueChange={(v) => setMiForm({ ...miForm, category: v })}>
              <SelectTrigger><SelectValue placeholder="Select category" /></SelectTrigger>
              <SelectContent>
                {MI_CATEGORIES.map((c) => <SelectItem key={c} value={c}>{c}</SelectItem>)}
              </SelectContent>
            </Select>
          </div>
        </div>
        <div className="grid gap-4 sm:grid-cols-2">
          <div className="space-y-2">
            <Label>Author Name</Label>
            <Input value={miForm.author_name}
              onChange={(e) => setMiForm({ ...miForm, author_name: e.target.value })}
            />
          </div>
          <div className="space-y-2">
            <Label>Reading Time (min)</Label>
            <Input type="number" value={miForm.reading_time_minutes}
              onChange={(e) => setMiForm({ ...miForm, reading_time_minutes: parseInt(e.target.value) || 5 })}
            />
          </div>
        </div>
        <div className="flex gap-6">
          <div className="flex items-center space-x-2">
            <Checkbox id="mi-featured" checked={miForm.is_featured}
              onCheckedChange={(c) => setMiForm({ ...miForm, is_featured: c as boolean })}
            />
            <Label htmlFor="mi-featured">Featured</Label>
          </div>
          <div className="flex items-center space-x-2">
            <Checkbox id="mi-published" checked={miForm.is_published}
              onCheckedChange={(c) => setMiForm({ ...miForm, is_published: c as boolean })}
            />
            <Label htmlFor="mi-published">Published</Label>
          </div>
        </div>
      </TabsContent>
    </Tabs>
  );

  // ========== LOADING / ERROR STATES ==========
  if (isCheckingAuth || configsLoading) {
    return (
      <div className="min-h-screen bg-background flex items-center justify-center">
        <div className="text-center">
          <Loader2 className="animate-spin h-8 w-8 text-primary mx-auto" />
          <p className="mt-2 text-muted-foreground">Loading command center...</p>
        </div>
      </div>
    );
  }

  if (configsError) {
    return (
      <div className="min-h-screen bg-background flex items-center justify-center">
        <Card className="max-w-md">
          <CardContent className="p-8 text-center">
            <Shield className="h-12 w-12 text-red-500 dark:text-red-400 mx-auto mb-4" />
            <h2 className="text-xl font-semibold mb-2">Access Denied</h2>
            <p className="text-muted-foreground mb-4">
              Only superadmins can access the command center.
            </p>
            <Link href="/">
              <Button>Return Home</Button>
            </Link>
          </CardContent>
        </Card>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-background">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Header */}
        <div className="flex items-center gap-4 mb-8">
          <Link href="/admin">
            <Button variant="outline" size="sm">
              <ArrowLeft className="h-4 w-4 mr-1" />
              Admin
            </Button>
          </Link>
          <div className="flex-1">
            <h1 className="text-3xl font-bold tracking-tight flex items-center gap-3">
              <Bot className="h-8 w-8 text-primary" />
              AI Command Center
            </h1>
            <p className="text-muted-foreground mt-1">
              Manage AI agents, market insights, and startup insights. Superadmin only.
            </p>
          </div>
          <Badge variant="outline" className="text-xs">
            <div className="w-2 h-2 rounded-full bg-green-500 animate-pulse mr-1" />
            Live
          </Badge>
        </div>

        <Tabs defaultValue="agents" className="space-y-6">
          <TabsList className="grid w-full grid-cols-4">
            <TabsTrigger value="agents" className="flex items-center gap-1.5">
              <Bot className="h-4 w-4" />
              <span className="hidden sm:inline">Agents</span>
              <Badge variant="secondary" className="text-[10px] px-1.5 py-0 ml-1">
                {configs?.length || 0}
              </Badge>
            </TabsTrigger>
            <TabsTrigger value="market-insights" className="flex items-center gap-1.5">
              <BookOpen className="h-4 w-4" />
              <span className="hidden sm:inline">Market Insights</span>
              <Badge variant="secondary" className="text-[10px] px-1.5 py-0 ml-1">
                {miData?.length || 0}
              </Badge>
            </TabsTrigger>
            <TabsTrigger value="insights" className="flex items-center gap-1.5">
              <Lightbulb className="h-4 w-4" />
              <span className="hidden sm:inline">Insights</span>
              <Badge variant="secondary" className="text-[10px] px-1.5 py-0 ml-1">
                {insightsData?.length || 0}
              </Badge>
            </TabsTrigger>
            <TabsTrigger value="statistics" className="flex items-center gap-1.5">
              <BarChart3 className="h-4 w-4" />
              <span className="hidden sm:inline">Statistics</span>
            </TabsTrigger>
          </TabsList>

          {/* ============================================================ */}
          {/* TAB 1: AGENTS */}
          {/* ============================================================ */}
          <TabsContent value="agents">
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-lg font-semibold">Agent Configurations</h2>
              <Button onClick={() => {
                setCreateForm({
                  agent_name: '',
                  model_name: 'gemini-1.5-flash',
                  temperature: 0.7,
                  max_tokens: 4096,
                  rate_limit_per_hour: 100,
                  cost_limit_daily_usd: 50,
                  description: '',
                  schedule: '',
                });
                setCreateDialogOpen(true);
              }}>
                <Plus className="h-4 w-4 mr-2" />
                Create Agent
              </Button>
            </div>

            {/* Summary Stats Bar */}
            {configs && configs.length > 0 && (
              <div className="grid gap-3 grid-cols-2 md:grid-cols-4 mb-4">
                <Card>
                  <CardContent className="p-4 flex items-center gap-3">
                    <div className="p-2 rounded-md bg-green-100 dark:bg-green-900">
                      <Bot className="h-4 w-4 text-green-600 dark:text-green-400" />
                    </div>
                    <div>
                      <p className="text-2xl font-bold">{configs.filter((a: AgentConfig) => a.is_enabled).length}</p>
                      <p className="text-xs text-muted-foreground">Active Agents</p>
                    </div>
                  </CardContent>
                </Card>
                <Card>
                  <CardContent className="p-4 flex items-center gap-3">
                    <div className="p-2 rounded-md bg-gray-100 dark:bg-gray-800">
                      <Bot className="h-4 w-4 text-gray-500" />
                    </div>
                    <div>
                      <p className="text-2xl font-bold">{configs.filter((a: AgentConfig) => !a.is_enabled).length}</p>
                      <p className="text-xs text-muted-foreground">Disabled Agents</p>
                    </div>
                  </CardContent>
                </Card>
                <Card>
                  <CardContent className="p-4 flex items-center gap-3">
                    <div className="p-2 rounded-md bg-blue-100 dark:bg-blue-900">
                      <Zap className="h-4 w-4 text-blue-600 dark:text-blue-400" />
                    </div>
                    <div>
                      <p className="text-2xl font-bold">
                        {stats ? stats.reduce((sum: number, s: AgentStats) => sum + s.tokens_used_24h, 0).toLocaleString() : '—'}
                      </p>
                      <p className="text-xs text-muted-foreground">Tokens (24h)</p>
                    </div>
                  </CardContent>
                </Card>
                <Card>
                  <CardContent className="p-4 flex items-center gap-3">
                    <div className="p-2 rounded-md bg-amber-100 dark:bg-amber-900">
                      <DollarSign className="h-4 w-4 text-amber-600 dark:text-amber-400" />
                    </div>
                    <div>
                      <p className="text-2xl font-bold">
                        ${stats ? stats.reduce((sum: number, s: AgentStats) => sum + s.cost_24h_usd, 0).toFixed(2) : '0.00'}
                      </p>
                      <p className="text-xs text-muted-foreground">Cost (24h)</p>
                    </div>
                  </CardContent>
                </Card>
              </div>
            )}

            <div className="space-y-4">
              {configs && configs.length > 0 ? (
                configs.map((agent: AgentConfig) => {
                  const runtime = getAgentRuntime(agent.agent_name);
                  const agentStats = getAgentStats(agent.agent_name);
                  const isTriggering = triggerMutation.isPending && triggerMutation.variables === agent.agent_name;
                  const isPolling = pollingAgent === agent.agent_name;
                  const isAgentBusy = isTriggering || isPolling;
                  const isPausing = pauseMutation.isPending && pauseMutation.variables === agent.agent_name;
                  const isResuming = resumeMutation.isPending && resumeMutation.variables === agent.agent_name;

                  return (
                    <Card key={agent.id} className={`${!agent.is_enabled ? 'opacity-60' : ''} ${isAgentBusy ? 'ring-2 ring-primary/30' : ''}`}>
                      <CardContent className="p-6">
                        {isAgentBusy && (
                          <div className="flex items-center gap-2 mb-3 p-2 rounded-md bg-primary/5 text-sm text-primary">
                            <Loader2 className="h-4 w-4 animate-spin" />
                            <span>{isPolling ? 'Agent running — waiting for result...' : 'Triggering agent...'}</span>
                          </div>
                        )}
                        <div className="flex items-start justify-between">
                          <div className="flex items-start gap-4 flex-1">
                            <div className={`mt-1 w-3 h-3 rounded-full shrink-0 ${
                              !agent.is_enabled ? 'bg-gray-400'
                                : runtime?.state === 'running' ? 'bg-green-500 animate-pulse'
                                : runtime?.state === 'paused' ? 'bg-yellow-500'
                                : runtime?.state === 'error' ? 'bg-red-500'
                                : 'bg-blue-500'
                            }`} />
                            <div className="flex-1 min-w-0">
                              <div className="flex items-center gap-2 mb-1">
                                <h3 className="font-semibold text-lg capitalize">
                                  {agent.agent_name.replace(/_/g, ' ')}
                                </h3>
                                <Badge variant={agent.is_enabled ? 'default' : 'secondary'}>
                                  {agent.is_enabled ? 'Active' : 'Disabled'}
                                </Badge>
                                {runtime?.state === 'running' && (
                                  <Badge variant="outline" className="text-green-600 dark:text-green-400 border-green-300 dark:border-green-700">Running</Badge>
                                )}
                                {runtime?.state === 'paused' && (
                                  <Badge variant="outline" className="text-yellow-600 dark:text-yellow-400 border-yellow-300 dark:border-yellow-700">Paused</Badge>
                                )}
                                {runtime?.state === 'error' && (
                                  <Badge variant="outline" className="text-red-600 dark:text-red-400 border-red-300 dark:border-red-700">Error</Badge>
                                )}
                              </div>

                              {typeof agent.custom_prompts?.description === 'string' && (
                                <p className="text-sm text-muted-foreground mt-1">{agent.custom_prompts.description}</p>
                              )}
                              {(agent.schedule_type || typeof agent.custom_prompts?.schedule === 'string') && (
                                <div className="flex items-center gap-2 text-xs text-muted-foreground mt-0.5">
                                  <Clock className="h-3 w-3" />
                                  {agent.schedule_type === 'cron' ? `Cron: ${agent.schedule_cron}`
                                    : agent.schedule_type === 'interval' ? `Every ${agent.schedule_interval_hours}h`
                                    : agent.schedule_type === 'manual' ? 'Manual only'
                                    : typeof agent.custom_prompts?.schedule === 'string' ? agent.custom_prompts.schedule : ''}
                                  {agent.next_run_at && (
                                    <span className="text-primary">Next: {formatRelativeTime(agent.next_run_at)}</span>
                                  )}
                                  {agent.last_run_at && (
                                    <span>Last: {formatRelativeTime(agent.last_run_at)}</span>
                                  )}
                                </div>
                              )}

                              <div className="flex flex-wrap gap-x-4 gap-y-1 text-sm text-muted-foreground mt-2">
                                <span>Model: <span className="text-foreground font-medium">{agent.model_name}</span></span>
                                <span>Temp: <span className="text-foreground font-medium">{agent.temperature}</span></span>
                                <span>Tokens: <span className="text-foreground font-medium">{agent.max_tokens.toLocaleString()}</span></span>
                                <span>Rate: <span className="text-foreground font-medium">{agent.rate_limit_per_hour}/hr</span></span>
                                <span>Cost: <span className="text-foreground font-medium">${agent.cost_limit_daily_usd}/day</span></span>
                              </div>

                              {runtime && (
                                <div className="flex gap-4 mt-2 text-sm">
                                  <span className="flex items-center gap-1"><Zap className="h-3 w-3" />{runtime.items_processed_today} today</span>
                                  {runtime.errors_today > 0 && (
                                    <span className="flex items-center gap-1 text-red-500 dark:text-red-400"><XCircle className="h-3 w-3" />{runtime.errors_today} errors</span>
                                  )}
                                  {runtime.last_run && (
                                    <span className="flex items-center gap-1 text-muted-foreground"><Clock className="h-3 w-3" />Last: {formatDateTimeMYT(runtime.last_run)}</span>
                                  )}
                                </div>
                              )}

                              {agentStats && agentStats.executions_24h > 0 && (
                                <div className="flex items-center gap-4 mt-1 text-sm text-muted-foreground">
                                  <span>{agentStats.executions_24h} runs (24h)</span>
                                  <span>Success: {(agentStats.success_rate * 100).toFixed(0)}%</span>
                                  <span>Avg: {agentStats.avg_duration_ms.toFixed(0)}ms</span>
                                  <Badge variant="outline" className={
                                    agentStats.cost_24h_usd > 0.50 ? 'text-red-600 dark:text-red-400 border-red-300 dark:border-red-700 bg-red-50 dark:bg-red-950' :
                                    agentStats.cost_24h_usd > 0.10 ? 'text-yellow-600 dark:text-yellow-400 border-yellow-300 dark:border-yellow-700 bg-yellow-50 dark:bg-yellow-950' :
                                    'text-green-600 dark:text-green-400 border-green-300 dark:border-green-700 bg-green-50 dark:bg-green-950'
                                  }>
                                    <DollarSign className="h-3 w-3 mr-0.5" />{agentStats.cost_24h_usd.toFixed(2)}/day
                                  </Badge>
                                </div>
                              )}

                              <p className="text-xs text-muted-foreground mt-2" title={formatDateTimeMYT(agent.updated_at)}>
                                Updated: {formatRelativeTime(agent.updated_at)}
                              </p>
                            </div>
                          </div>

                          <div className="flex items-center gap-3 ml-4">
                            <div className="flex flex-col items-center gap-1">
                              <Switch
                                checked={agent.is_enabled}
                                onCheckedChange={() => toggleMutation.mutate(agent.agent_name)}
                                disabled={toggleMutation.isPending}
                              />
                              <span className="text-[10px] text-muted-foreground">
                                {agent.is_enabled ? 'On' : 'Off'}
                              </span>
                            </div>
                            <div className="flex gap-1">
                              {runtime?.state === 'running' ? (
                                <Button variant="outline" size="sm"
                                  onClick={() => pauseMutation.mutate(agent.agent_name)}
                                  disabled={pauseMutation.isPending || !agent.is_enabled}
                                  title="Pause agent">
                                  {isPausing ? <Loader2 className="h-4 w-4 animate-spin" /> : <Pause className="h-4 w-4" />}
                                </Button>
                              ) : (
                                <Button variant="outline" size="sm"
                                  onClick={() => resumeMutation.mutate(agent.agent_name)}
                                  disabled={resumeMutation.isPending || !agent.is_enabled}
                                  title="Resume agent">
                                  {isResuming ? <Loader2 className="h-4 w-4 animate-spin" /> : <Play className="h-4 w-4" />}
                                </Button>
                              )}
                              <Button variant="outline" size="sm"
                                onClick={() => triggerMutation.mutate(agent.agent_name)}
                                disabled={isAgentBusy || !agent.is_enabled}
                                title={isPolling ? 'Running...' : 'Trigger now'}>
                                {isAgentBusy ? <Loader2 className="h-4 w-4 animate-spin" /> : <RotateCcw className="h-4 w-4" />}
                              </Button>
                              <Button variant="outline" size="sm"
                                onClick={() => setLogsAgent(agent.agent_name)}
                                title="View logs"><ScrollText className="h-4 w-4" /></Button>
                              <Button variant="outline" size="sm"
                                onClick={() => openAgentEditDialog(agent)}
                                title="Edit configuration"><Settings2 className="h-4 w-4" /></Button>
                              <Button variant="outline" size="sm"
                                onClick={() => { setDeletingAgent(agent); setDeleteDialogOpen(true); }}
                                title="Delete agent"><Trash2 className="h-4 w-4 text-red-500 dark:text-red-400" /></Button>
                            </div>
                          </div>
                        </div>
                      </CardContent>
                    </Card>
                  );
                })
              ) : (
                <Card>
                  <CardContent className="p-12 text-center">
                    <Bot className="h-16 w-16 mx-auto mb-4 text-muted-foreground opacity-50" />
                    <h3 className="text-lg font-medium mb-2">No Agents Configured</h3>
                    <p className="text-muted-foreground mb-4">Create your first agent or run seed_agent_configs.py.</p>
                    <Button onClick={() => setCreateDialogOpen(true)}>
                      <Plus className="h-4 w-4 mr-2" />
                      Create Agent
                    </Button>
                  </CardContent>
                </Card>
              )}
            </div>
          </TabsContent>

          {/* ============================================================ */}
          {/* TAB 2: MARKET INSIGHTS */}
          {/* ============================================================ */}
          <TabsContent value="market-insights">
            <Card>
              <CardHeader className="flex flex-row items-center justify-between pb-4">
                <div>
                  <CardTitle>Market Insight Articles</CardTitle>
                  <CardDescription>Create manually or generate with AI agent</CardDescription>
                </div>
                <div className="flex gap-2">
                  <Button variant="outline" onClick={handleMiCreate}>
                    <Plus className="h-4 w-4 mr-2" />
                    Manual Create
                  </Button>
                  <Button
                    onClick={() => {
                      triggerMutation.mutate('market_insight_publisher');
                      toast.success('Market Insight Publisher agent triggered.');
                    }}
                    disabled={triggerMutation.isPending}
                  >
                    <Sparkles className="h-4 w-4 mr-2" />
                    Generate with AI
                  </Button>
                </div>
              </CardHeader>
              <CardContent>
                <div className="mb-4">
                  <div className="relative">
                    <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
                    <Input
                      placeholder="Search articles..."
                      value={miSearchQuery}
                      onChange={(e) => setMiSearchQuery(e.target.value)}
                      className="pl-9"
                    />
                  </div>
                </div>

                {miLoading ? (
                  <div className="flex justify-center py-8"><Loader2 className="animate-spin h-6 w-6" /></div>
                ) : filteredMi.length === 0 ? (
                  <div className="text-center py-12">
                    <BookOpen className="h-12 w-12 mx-auto mb-3 text-muted-foreground opacity-50" />
                    <p className="text-muted-foreground mb-4">No market insight articles yet.</p>
                    <div className="flex gap-2 justify-center">
                      <Button variant="outline" onClick={handleMiCreate}>
                        <Plus className="h-4 w-4 mr-1" />Create Manually
                      </Button>
                    </div>
                  </div>
                ) : (
                  <Table>
                    <TableHeader>
                      <TableRow>
                        <TableHead className="w-[400px]">Title</TableHead>
                        <TableHead>Category</TableHead>
                        <TableHead>Author</TableHead>
                        <TableHead className="text-center">Views</TableHead>
                        <TableHead>Status</TableHead>
                        <TableHead className="text-right">Actions</TableHead>
                      </TableRow>
                    </TableHeader>
                    <TableBody>
                      {filteredMi.map((article) => (
                        <TableRow key={article.id}>
                          <TableCell>
                            <div>
                              <p className="font-medium line-clamp-1">{article.title}</p>
                              <p className="text-xs text-muted-foreground">
                                {formatDateMYT(article.published_at)} &middot; {article.reading_time_minutes} min
                              </p>
                            </div>
                          </TableCell>
                          <TableCell><Badge variant="outline">{article.category}</Badge></TableCell>
                          <TableCell className="text-sm">{article.author_name}</TableCell>
                          <TableCell className="text-center">{article.view_count}</TableCell>
                          <TableCell>
                            <div className="flex gap-1 items-center">
                              {article.is_featured && <Star className="h-3.5 w-3.5 text-yellow-500 dark:text-yellow-400 fill-yellow-500 dark:fill-yellow-400" />}
                              <Badge variant={article.is_published ? 'default' : 'secondary'}>
                                {article.is_published ? 'Published' : 'Draft'}
                              </Badge>
                            </div>
                          </TableCell>
                          <TableCell className="text-right">
                            <div className="flex justify-end gap-1">
                              <Button variant="ghost" size="icon"
                                onClick={() => window.open(`/market-insights/${article.slug}`, '_blank')}
                                title="Preview"><Eye className="h-4 w-4" /></Button>
                              <Button variant="ghost" size="icon"
                                onClick={() => handleMiEdit(article)}
                                title="Edit"><Pencil className="h-4 w-4" /></Button>
                              <Button variant="ghost" size="icon"
                                onClick={() => { setDeletingMi(article); setMiDeleteDialogOpen(true); }}
                                title="Delete"><Trash2 className="h-4 w-4 text-red-500 dark:text-red-400" /></Button>
                            </div>
                          </TableCell>
                        </TableRow>
                      ))}
                    </TableBody>
                  </Table>
                )}
              </CardContent>
            </Card>
          </TabsContent>

          {/* ============================================================ */}
          {/* TAB 3: INSIGHTS */}
          {/* ============================================================ */}
          <TabsContent value="insights">
            <Card>
              <CardHeader className="flex flex-row items-center justify-between pb-4">
                <div>
                  <CardTitle>Startup Insights</CardTitle>
                  <CardDescription>Review, manage, and quality-check AI-generated insights</CardDescription>
                </div>
                <div className="flex gap-2">
                  <Button variant="outline"
                    onClick={() => {
                      triggerMutation.mutate('insight_quality_reviewer');
                      toast.success('Insight Quality Reviewer triggered.');
                    }}
                    disabled={triggerMutation.isPending}
                  >
                    <CheckCircle2 className="h-4 w-4 mr-2" />
                    Run Quality Audit
                  </Button>
                  <Button
                    onClick={() => {
                      triggerMutation.mutate('enhanced_analyzer');
                      toast.success('Enhanced Analyzer triggered.');
                    }}
                    disabled={triggerMutation.isPending}
                  >
                    <Sparkles className="h-4 w-4 mr-2" />
                    Analyze New Signals
                  </Button>
                </div>
              </CardHeader>
              <CardContent>
                <div className="mb-4">
                  <div className="relative">
                    <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
                    <Input
                      placeholder="Search insights..."
                      value={insightSearchQuery}
                      onChange={(e) => setInsightSearchQuery(e.target.value)}
                      className="pl-9"
                    />
                  </div>
                </div>

                {insightsLoading ? (
                  <div className="flex justify-center py-8"><Loader2 className="animate-spin h-6 w-6" /></div>
                ) : filteredInsights.length === 0 ? (
                  <div className="text-center py-12">
                    <Lightbulb className="h-12 w-12 mx-auto mb-3 text-muted-foreground opacity-50" />
                    <p className="text-muted-foreground">No insights found.</p>
                  </div>
                ) : (
                  <Table>
                    <TableHeader>
                      <TableRow>
                        <TableHead className="w-[350px]">Proposed Solution</TableHead>
                        <TableHead className="text-center">Relevance</TableHead>
                        <TableHead className="text-center">Opportunity</TableHead>
                        <TableHead className="text-center">Feasibility</TableHead>
                        <TableHead className="text-center">Founder Fit</TableHead>
                        <TableHead>Market Size</TableHead>
                        <TableHead>Date</TableHead>
                        <TableHead className="text-right">Actions</TableHead>
                      </TableRow>
                    </TableHeader>
                    <TableBody>
                      {filteredInsights.map((insight) => (
                        <TableRow key={insight.id}>
                          <TableCell>
                            <p className="font-medium line-clamp-2 text-sm">{insight.proposed_solution}</p>
                          </TableCell>
                          <TableCell className="text-center">
                            <Badge variant={insight.relevance_score >= 0.85 ? 'default' : 'outline'}>
                              {(insight.relevance_score * 100).toFixed(0)}%
                            </Badge>
                          </TableCell>
                          <TableCell className="text-center text-sm">{insight.opportunity_score ?? '-'}</TableCell>
                          <TableCell className="text-center text-sm">{insight.feasibility_score ?? '-'}</TableCell>
                          <TableCell className="text-center text-sm">{insight.founder_fit_score ?? '-'}</TableCell>
                          <TableCell className="text-sm">{insight.market_size_estimate || '-'}</TableCell>
                          <TableCell className="text-xs text-muted-foreground">{formatDateMYT(insight.created_at)}</TableCell>
                          <TableCell className="text-right">
                            <div className="flex justify-end gap-1">
                              <Button variant="ghost" size="icon"
                                onClick={() => window.open(`/insights/${insight.slug || insight.id}`, '_blank')}
                                title="View"><Eye className="h-4 w-4" /></Button>
                              <Button variant="ghost" size="icon"
                                onClick={() => { setDeletingInsight(insight); setInsightDeleteDialogOpen(true); }}
                                title="Delete"><Trash2 className="h-4 w-4 text-red-500 dark:text-red-400" /></Button>
                            </div>
                          </TableCell>
                        </TableRow>
                      ))}
                    </TableBody>
                  </Table>
                )}
              </CardContent>
            </Card>
          </TabsContent>

          {/* ============================================================ */}
          {/* TAB 4: STATISTICS */}
          {/* ============================================================ */}
          <TabsContent value="statistics">
            <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
              {stats && stats.length > 0 ? (
                stats.map((s: AgentStats) => (
                  <Card key={s.agent_name}>
                    <CardHeader className="pb-2">
                      <CardTitle className="text-base capitalize">{s.agent_name.replace(/_/g, ' ')}</CardTitle>
                      <CardDescription>Last 24 hours</CardDescription>
                    </CardHeader>
                    <CardContent>
                      <div className="grid gap-4 sm:grid-cols-2">
                        <div>
                          <p className="text-2xl font-bold">{s.executions_24h}</p>
                          <p className="text-xs text-muted-foreground">Executions</p>
                        </div>
                        <div>
                          <p className="text-2xl font-bold flex items-center gap-1">
                            {(s.success_rate * 100).toFixed(0)}%
                            {s.success_rate >= 0.95 ? <CheckCircle2 className="h-4 w-4 text-green-500 dark:text-green-400" />
                              : s.success_rate >= 0.8 ? <AlertTriangle className="h-4 w-4 text-yellow-500 dark:text-yellow-400" />
                              : <XCircle className="h-4 w-4 text-red-500 dark:text-red-400" />}
                          </p>
                          <p className="text-xs text-muted-foreground">Success Rate</p>
                        </div>
                        <div>
                          <p className="text-2xl font-bold">{s.avg_duration_ms.toFixed(0)}</p>
                          <p className="text-xs text-muted-foreground">Avg Duration (ms)</p>
                        </div>
                        <div>
                          <p className="text-2xl font-bold">${s.cost_24h_usd.toFixed(2)}</p>
                          <p className="text-xs text-muted-foreground">Cost (24h)</p>
                        </div>
                      </div>
                    </CardContent>
                  </Card>
                ))
              ) : (
                <Card className="col-span-full">
                  <CardContent className="p-12 text-center">
                    <BarChart3 className="h-16 w-16 mx-auto mb-4 text-muted-foreground opacity-50" />
                    <h3 className="text-lg font-medium mb-2">No Statistics Yet</h3>
                    <p className="text-muted-foreground">Agent execution statistics will appear after agents run.</p>
                  </CardContent>
                </Card>
              )}
            </div>

            {/* Cost Analytics Chart */}
            <Card className="mt-6">
              <CardHeader className="pb-3">
                <div className="flex items-center justify-between">
                  <CardTitle className="text-base flex items-center gap-2">
                    <DollarSign className="h-4 w-4" />
                    Cost Analytics
                  </CardTitle>
                  <div className="flex gap-1">
                    {(['7d', '30d', '90d'] as const).map((p) => (
                      <Button
                        key={p}
                        variant={costPeriod === p ? 'default' : 'outline'}
                        size="sm"
                        className="h-7 text-xs"
                        onClick={() => setCostPeriod(p)}
                      >
                        {p}
                      </Button>
                    ))}
                  </div>
                </div>
                {costData && (
                  <div className="flex gap-6 mt-2 text-sm">
                    <span>Total: <strong>${costData.total_cost_usd.toFixed(2)}</strong></span>
                    <span>Tokens: <strong>{costData.total_tokens.toLocaleString()}</strong></span>
                    <span>Executions: <strong>{costData.total_executions}</strong></span>
                  </div>
                )}
              </CardHeader>
              <CardContent>
                {costData && costData.cost_by_agent && Object.keys(costData.cost_by_agent).length > 0 ? (
                  <div className="space-y-2">
                    {Object.entries(costData.cost_by_agent)
                      .sort(([, a], [, b]) => (b as number) - (a as number))
                      .map(([agent, cost]) => {
                        const maxCost = Math.max(...Object.values(costData.cost_by_agent).map(Number));
                        const pct = maxCost > 0 ? ((cost as number) / maxCost) * 100 : 0;
                        return (
                          <div key={agent} className="flex items-center gap-3">
                            <span className="text-sm w-40 truncate capitalize">{agent.replace(/_/g, ' ')}</span>
                            <div className="flex-1 bg-muted rounded-full h-3 overflow-hidden">
                              <div className="h-full bg-primary rounded-full transition-all" style={{ width: `${pct}%` }} />
                            </div>
                            <span className="text-sm font-mono w-16 text-right">${(cost as number).toFixed(2)}</span>
                          </div>
                        );
                      })}
                  </div>
                ) : (
                  <p className="text-sm text-muted-foreground text-center py-6">No cost data available for this period.</p>
                )}
              </CardContent>
            </Card>
          </TabsContent>
        </Tabs>

        {/* ============================================================ */}
        {/* DIALOG/SHEET: Edit Agent Configuration */}
        {/* ============================================================ */}
        {isFullView ? (
          <Sheet open={!!editingAgent} onOpenChange={(open) => { if (!open) { setEditingAgent(null); setIsFullView(false); } }}>
            <SheetContent side="right" className="w-full sm:max-w-[95vw] overflow-y-auto p-0">
              {(() => {
                const runtime = editingAgent ? getAgentRuntime(editingAgent.agent_name) : undefined;
                const agentSt = editingAgent ? getAgentStats(editingAgent.agent_name) : undefined;
                const isAgentTriggering = triggerMutation.isPending && triggerMutation.variables === editingAgent?.agent_name;
                return (
                  <>
                    {/* Full-view Header */}
                    <div className="sticky top-0 z-10 bg-background border-b px-6 py-4">
                      <div className="flex items-center justify-between">
                        <div className="flex items-center gap-3">
                          <div className={`w-3 h-3 rounded-full ${
                            !editingAgent?.is_enabled ? 'bg-gray-400'
                              : runtime?.state === 'running' ? 'bg-green-500 animate-pulse'
                              : runtime?.state === 'paused' ? 'bg-yellow-500'
                              : runtime?.state === 'error' ? 'bg-red-500'
                              : 'bg-blue-500'
                          }`} />
                          <h2 className="text-xl font-bold capitalize">
                            {editingAgent?.agent_name.replace(/_/g, ' ')}
                          </h2>
                          <Badge variant={editingAgent?.is_enabled ? 'default' : 'secondary'}>
                            {editingAgent?.is_enabled ? 'Active' : 'Disabled'}
                          </Badge>
                          {runtime?.state && (
                            <Badge variant="outline" className={
                              runtime.state === 'running' ? 'text-green-600 dark:text-green-400 border-green-300 dark:border-green-700' :
                              runtime.state === 'paused' ? 'text-yellow-600 dark:text-yellow-400 border-yellow-300 dark:border-yellow-700' :
                              runtime.state === 'error' ? 'text-red-600 dark:text-red-400 border-red-300 dark:border-red-700' : ''
                            }>{runtime.state}</Badge>
                          )}
                        </div>
                        <div className="flex items-center gap-2">
                          <Button onClick={handleSaveAgent} disabled={updateMutation.isPending}>
                            {updateMutation.isPending && <Loader2 className="animate-spin h-4 w-4 mr-2" />}
                            Save Configuration
                          </Button>
                          <Button variant="outline" onClick={() => { setEditingAgent(null); setIsFullView(false); }}>Cancel</Button>
                          <Button variant="ghost" size="icon" onClick={() => setIsFullView(false)} title="Compact view">
                            <Minimize2 className="h-4 w-4" />
                          </Button>
                        </div>
                      </div>
                    </div>

                    {/* Full-view Body: 2-column layout */}
                    <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 p-6">
                      {/* Left Column: Configuration (2/3 width) */}
                      <div className="lg:col-span-2 space-y-6">
                        {/* Identity Section */}
                        <Card>
                          <CardHeader className="pb-3">
                            <CardTitle className="text-base flex items-center gap-2">
                              <Bot className="h-4 w-4" />
                              Agent Identity
                            </CardTitle>
                          </CardHeader>
                          <CardContent className="space-y-4">
                            <div className="grid gap-4 sm:grid-cols-2">
                              <div className="space-y-2">
                                <Label>Description</Label>
                                <Input
                                  value={agentEditForm.description}
                                  onChange={(e) => setAgentEditForm({ ...agentEditForm, description: e.target.value })}
                                  placeholder="What does this agent do?"
                                />
                              </div>
                              <div className="space-y-2">
                                <Label>Schedule Type</Label>
                                <Select value={agentEditForm.schedule_type} onValueChange={(v) => setAgentEditForm({ ...agentEditForm, schedule_type: v })}>
                                  <SelectTrigger><SelectValue /></SelectTrigger>
                                  <SelectContent>
                                    <SelectItem value="manual">Manual Only</SelectItem>
                                    <SelectItem value="interval">Interval</SelectItem>
                                    <SelectItem value="cron">Custom Cron</SelectItem>
                                  </SelectContent>
                                </Select>
                              </div>
                              {agentEditForm.schedule_type === 'interval' && (
                                <div className="space-y-2">
                                  <Label>Every (hours)</Label>
                                  <Select value={String(agentEditForm.schedule_interval_hours)} onValueChange={(v) => setAgentEditForm({ ...agentEditForm, schedule_interval_hours: parseInt(v) })}>
                                    <SelectTrigger><SelectValue /></SelectTrigger>
                                    <SelectContent>
                                      <SelectItem value="1">1h</SelectItem>
                                      <SelectItem value="3">3h</SelectItem>
                                      <SelectItem value="6">6h</SelectItem>
                                      <SelectItem value="12">12h</SelectItem>
                                      <SelectItem value="24">Daily</SelectItem>
                                      <SelectItem value="72">3 days</SelectItem>
                                      <SelectItem value="168">Weekly</SelectItem>
                                    </SelectContent>
                                  </Select>
                                </div>
                              )}
                              {agentEditForm.schedule_type === 'cron' && (
                                <div className="space-y-2">
                                  <Label>Cron Expression</Label>
                                  <Input value={agentEditForm.schedule_cron} onChange={(e) => setAgentEditForm({ ...agentEditForm, schedule_cron: e.target.value })} placeholder="0 8 * * *" className="font-mono" />
                                </div>
                              )}
                              <div className="flex items-end">
                                <Button variant="outline" size="sm" onClick={() => editingAgent && scheduleMutation.mutate({ name: editingAgent.agent_name, payload: { schedule_type: agentEditForm.schedule_type, ...(agentEditForm.schedule_type === 'cron' ? { schedule_cron: agentEditForm.schedule_cron } : {}), ...(agentEditForm.schedule_type === 'interval' ? { schedule_interval_hours: agentEditForm.schedule_interval_hours } : {}) } })} disabled={scheduleMutation.isPending}>
                                  {scheduleMutation.isPending ? <Loader2 className="h-3 w-3 mr-1 animate-spin" /> : <Clock className="h-3 w-3 mr-1" />} Save Schedule
                                </Button>
                              </div>
                            </div>
                          </CardContent>
                        </Card>

                        {/* Model Configuration */}
                        <Card>
                          <CardHeader className="pb-3">
                            <CardTitle className="text-base flex items-center gap-2">
                              <Zap className="h-4 w-4" />
                              Model Configuration
                            </CardTitle>
                          </CardHeader>
                          <CardContent>
                            <div className="grid grid-cols-3 gap-4">
                              <div className="space-y-2">
                                <Label>AI Model</Label>
                                <Select value={agentEditForm.model_name} onValueChange={(v) => setAgentEditForm({ ...agentEditForm, model_name: v })}>
                                  <SelectTrigger><SelectValue placeholder="Select model" /></SelectTrigger>
                                  <SelectContent>
                                    {AI_MODELS.map((m) => <SelectItem key={m} value={m}>{m}</SelectItem>)}
                                  </SelectContent>
                                </Select>
                              </div>
                              <div className="space-y-2">
                                <Label>Temperature</Label>
                                <Input type="number" step="0.1" min="0" max="2"
                                  value={agentEditForm.temperature}
                                  onChange={(e) => setAgentEditForm({ ...agentEditForm, temperature: parseFloat(e.target.value) || 0 })}
                                />
                                <p className="text-[10px] text-muted-foreground">0 = deterministic, 2 = creative</p>
                              </div>
                              <div className="space-y-2">
                                <Label>Max Tokens</Label>
                                <Input type="number" min="100" max="32000"
                                  value={agentEditForm.max_tokens}
                                  onChange={(e) => setAgentEditForm({ ...agentEditForm, max_tokens: parseInt(e.target.value) || 4096 })}
                                />
                              </div>
                            </div>
                          </CardContent>
                        </Card>

                        {/* System Prompt */}
                        <Card>
                          <CardHeader className="pb-3">
                            <CardTitle className="text-base flex items-center gap-2">
                              <FileText className="h-4 w-4" />
                              System Prompt
                            </CardTitle>
                            <CardDescription>The prompt that defines this agent&apos;s behavior and output format.</CardDescription>
                          </CardHeader>
                          <CardContent>
                            <Textarea
                              value={agentEditForm.system_prompt}
                              onChange={(e) => setAgentEditForm({ ...agentEditForm, system_prompt: e.target.value })}
                              placeholder="Enter the system prompt that guides this agent's behavior..."
                              rows={18}
                              className="font-mono text-sm leading-relaxed"
                            />
                            <div className="flex items-center justify-between mt-2">
                              <p className="text-xs text-muted-foreground">
                                Leave empty to use the default built-in prompt.
                              </p>
                              <p className="text-xs text-muted-foreground">
                                {agentEditForm.system_prompt.length} characters
                              </p>
                            </div>
                          </CardContent>
                        </Card>

                        {/* Rate & Cost Limits */}
                        <Card>
                          <CardHeader className="pb-3">
                            <CardTitle className="text-base flex items-center gap-2">
                              <Shield className="h-4 w-4" />
                              Rate &amp; Cost Limits
                            </CardTitle>
                          </CardHeader>
                          <CardContent>
                            <div className="grid gap-4 sm:grid-cols-2">
                              <div className="space-y-2">
                                <Label>Rate Limit (per hour)</Label>
                                <Input type="number" min="1" max="1000"
                                  value={agentEditForm.rate_limit_per_hour}
                                  onChange={(e) => setAgentEditForm({ ...agentEditForm, rate_limit_per_hour: parseInt(e.target.value) || 10 })}
                                />
                                <p className="text-[10px] text-muted-foreground">Max API calls this agent can make per hour</p>
                              </div>
                              <div className="space-y-2">
                                <Label>Cost Limit ($/day)</Label>
                                <Input type="number" min="1" max="1000"
                                  value={agentEditForm.cost_limit_daily_usd}
                                  onChange={(e) => setAgentEditForm({ ...agentEditForm, cost_limit_daily_usd: parseFloat(e.target.value) || 10 })}
                                />
                                <p className="text-[10px] text-muted-foreground">Max daily spend for this agent</p>
                              </div>
                            </div>
                          </CardContent>
                        </Card>
                      </div>

                      {/* Right Column: Status & Actions (1/3 width) */}
                      <div className="space-y-6">
                        {/* Quick Actions */}
                        <Card>
                          <CardHeader className="pb-3">
                            <CardTitle className="text-base">Quick Actions</CardTitle>
                          </CardHeader>
                          <CardContent className="space-y-2">
                            {isAgentTriggering && (
                              <div className="flex items-center gap-2 p-2 rounded-md bg-primary/5 text-sm text-primary mb-2">
                                <Loader2 className="h-4 w-4 animate-spin" />
                                <span>Running agent...</span>
                              </div>
                            )}
                            <Button className="w-full justify-start" variant="outline"
                              onClick={() => editingAgent && triggerMutation.mutate(editingAgent.agent_name)}
                              disabled={triggerMutation.isPending || !editingAgent?.is_enabled}>
                              {isAgentTriggering ? <Loader2 className="h-4 w-4 mr-2 animate-spin" /> : <RotateCcw className="h-4 w-4 mr-2" />}
                              Trigger Now
                            </Button>
                            {runtime?.state === 'running' ? (
                              <Button className="w-full justify-start" variant="outline"
                                onClick={() => editingAgent && pauseMutation.mutate(editingAgent.agent_name)}
                                disabled={pauseMutation.isPending}>
                                <Pause className="h-4 w-4 mr-2" />
                                Pause Agent
                              </Button>
                            ) : (
                              <Button className="w-full justify-start" variant="outline"
                                onClick={() => editingAgent && resumeMutation.mutate(editingAgent.agent_name)}
                                disabled={resumeMutation.isPending || !editingAgent?.is_enabled}>
                                <Play className="h-4 w-4 mr-2" />
                                Resume Agent
                              </Button>
                            )}
                            <Button className="w-full justify-start" variant="outline"
                              onClick={() => editingAgent && setLogsAgent(editingAgent.agent_name)}>
                              <ScrollText className="h-4 w-4 mr-2" />
                              View Full Logs
                            </Button>
                            <div className="flex items-center justify-between pt-2 border-t mt-2">
                              <span className="text-sm font-medium">Enabled</span>
                              <Switch
                                checked={editingAgent?.is_enabled ?? false}
                                onCheckedChange={() => editingAgent && toggleMutation.mutate(editingAgent.agent_name)}
                                disabled={toggleMutation.isPending}
                              />
                            </div>
                          </CardContent>
                        </Card>

                        {/* Live Status */}
                        <Card>
                          <CardHeader className="pb-3">
                            <CardTitle className="text-base flex items-center gap-2">
                              <BarChart3 className="h-4 w-4" />
                              Live Status
                            </CardTitle>
                          </CardHeader>
                          <CardContent>
                            {runtime ? (
                              <div className="space-y-3">
                                <div className="flex justify-between text-sm">
                                  <span className="text-muted-foreground">State</span>
                                  <Badge variant="outline" className={
                                    runtime.state === 'running' ? 'text-green-600 dark:text-green-400 border-green-300 dark:border-green-700' :
                                    runtime.state === 'paused' ? 'text-yellow-600 dark:text-yellow-400 border-yellow-300 dark:border-yellow-700' :
                                    runtime.state === 'error' ? 'text-red-600 dark:text-red-400 border-red-300 dark:border-red-700' : ''
                                  }>{runtime.state}</Badge>
                                </div>
                                <div className="flex justify-between text-sm">
                                  <span className="text-muted-foreground">Items Today</span>
                                  <span className="font-medium">{runtime.items_processed_today}</span>
                                </div>
                                {runtime.errors_today > 0 && (
                                  <div className="flex justify-between text-sm">
                                    <span className="text-muted-foreground">Errors Today</span>
                                    <span className="font-medium text-red-500 dark:text-red-400">{runtime.errors_today}</span>
                                  </div>
                                )}
                                {runtime.last_run && (
                                  <div className="flex justify-between text-sm">
                                    <span className="text-muted-foreground">Last Run</span>
                                    <span className="font-medium text-xs">{formatDateTimeMYT(runtime.last_run)}</span>
                                  </div>
                                )}
                              </div>
                            ) : (
                              <p className="text-sm text-muted-foreground text-center py-4">No runtime data available</p>
                            )}
                          </CardContent>
                        </Card>

                        {/* Statistics */}
                        <Card>
                          <CardHeader className="pb-3">
                            <CardTitle className="text-base flex items-center gap-2">
                              <Zap className="h-4 w-4" />
                              Statistics (24h)
                            </CardTitle>
                          </CardHeader>
                          <CardContent>
                            {agentSt && agentSt.executions_24h > 0 ? (
                              <div className="space-y-3">
                                <div className="flex justify-between text-sm">
                                  <span className="text-muted-foreground">Executions</span>
                                  <span className="font-bold text-lg">{agentSt.executions_24h}</span>
                                </div>
                                <div className="flex justify-between text-sm">
                                  <span className="text-muted-foreground">Success Rate</span>
                                  <span className="font-medium flex items-center gap-1">
                                    {(agentSt.success_rate * 100).toFixed(0)}%
                                    {agentSt.success_rate >= 0.95 ? <CheckCircle2 className="h-3 w-3 text-green-500 dark:text-green-400" />
                                      : agentSt.success_rate >= 0.8 ? <AlertTriangle className="h-3 w-3 text-yellow-500 dark:text-yellow-400" />
                                      : <XCircle className="h-3 w-3 text-red-500 dark:text-red-400" />}
                                  </span>
                                </div>
                                <div className="flex justify-between text-sm">
                                  <span className="text-muted-foreground">Avg Duration</span>
                                  <span className="font-medium">{agentSt.avg_duration_ms.toFixed(0)}ms</span>
                                </div>
                                <div className="flex justify-between text-sm">
                                  <span className="text-muted-foreground">Cost</span>
                                  <span className="font-medium">${agentSt.cost_24h_usd.toFixed(2)}</span>
                                </div>
                              </div>
                            ) : (
                              <p className="text-sm text-muted-foreground text-center py-4">No executions in the last 24 hours</p>
                            )}
                          </CardContent>
                        </Card>

                        {/* Meta Info */}
                        <Card>
                          <CardHeader className="pb-3">
                            <CardTitle className="text-base">Configuration Info</CardTitle>
                          </CardHeader>
                          <CardContent className="space-y-2 text-sm">
                            <div className="flex justify-between">
                              <span className="text-muted-foreground">Agent ID</span>
                              <span className="font-mono text-xs">{editingAgent?.id.slice(0, 8)}...</span>
                            </div>
                            <div className="flex justify-between">
                              <span className="text-muted-foreground">Name</span>
                              <span className="font-mono text-xs">{editingAgent?.agent_name}</span>
                            </div>
                            <div className="flex justify-between">
                              <span className="text-muted-foreground">Last Updated</span>
                              <span className="text-xs">{editingAgent && formatDateTimeMYT(editingAgent.updated_at)}</span>
                            </div>
                          </CardContent>
                        </Card>
                      </div>
                    </div>
                  </>
                );
              })()}
            </SheetContent>
          </Sheet>
        ) : (
          <Dialog open={!!editingAgent} onOpenChange={(open) => !open && setEditingAgent(null)}>
            <DialogContent className="sm:max-w-2xl max-h-[90vh] overflow-y-auto">
              <DialogHeader>
                <div className="flex items-center justify-between pr-8">
                  <DialogTitle className="capitalize flex items-center gap-2">
                    <Settings2 className="h-5 w-5" />
                    Configure: {editingAgent?.agent_name.replace(/_/g, ' ')}
                  </DialogTitle>
                  <Button variant="ghost" size="icon" onClick={() => setIsFullView(true)} title="Full view">
                    <Maximize2 className="h-4 w-4" />
                  </Button>
                </div>
                <DialogDescription>
                  Modify agent behavior, model, prompts, and limits.
                </DialogDescription>
              </DialogHeader>
              <AgentEditFormContent />
              <DialogFooter>
                <Button variant="outline" onClick={() => setEditingAgent(null)}>Cancel</Button>
                <Button onClick={handleSaveAgent} disabled={updateMutation.isPending}>
                  {updateMutation.isPending && <Loader2 className="animate-spin h-4 w-4 mr-2" />}
                  Save Configuration
                </Button>
              </DialogFooter>
            </DialogContent>
          </Dialog>
        )}

        {/* ============================================================ */}
        {/* DIALOG: Create Agent */}
        {/* ============================================================ */}
        <Dialog open={createDialogOpen} onOpenChange={setCreateDialogOpen}>
          <DialogContent className="sm:max-w-2xl max-h-[90vh] overflow-y-auto">
            <DialogHeader>
              <DialogTitle className="flex items-center gap-2">
                <Plus className="h-5 w-5" />
                Create New Agent
              </DialogTitle>
              <DialogDescription>
                Register a new AI agent. It will appear in the command center.
              </DialogDescription>
            </DialogHeader>
            <div className="space-y-4 py-4">
              <div className="space-y-2">
                <Label>Agent Name (snake_case)</Label>
                <Input
                  value={createForm.agent_name}
                  onChange={(e) => setCreateForm({ ...createForm, agent_name: e.target.value })}
                  placeholder="e.g., content_analyzer"
                />
                <p className="text-xs text-muted-foreground">Must be unique. Will be converted to snake_case.</p>
              </div>
              <div className="space-y-2">
                <Label>Description</Label>
                <Input
                  value={createForm.description}
                  onChange={(e) => setCreateForm({ ...createForm, description: e.target.value })}
                  placeholder="What does this agent do?"
                />
              </div>
              <div className="space-y-2">
                <Label>Schedule</Label>
                <Input
                  value={createForm.schedule}
                  onChange={(e) => setCreateForm({ ...createForm, schedule: e.target.value })}
                  placeholder="e.g., Every 6 hours"
                />
              </div>
              <div className="grid gap-4 sm:grid-cols-2">
                <div className="space-y-2">
                  <Label>AI Model</Label>
                  <Select value={createForm.model_name} onValueChange={(v) => setCreateForm({ ...createForm, model_name: v })}>
                    <SelectTrigger><SelectValue /></SelectTrigger>
                    <SelectContent>
                      {AI_MODELS.map((m) => <SelectItem key={m} value={m}>{m}</SelectItem>)}
                    </SelectContent>
                  </Select>
                </div>
                <div className="space-y-2">
                  <Label>Temperature</Label>
                  <Input type="number" step="0.1" min="0" max="2"
                    value={createForm.temperature}
                    onChange={(e) => setCreateForm({ ...createForm, temperature: parseFloat(e.target.value) || 0.7 })}
                  />
                </div>
              </div>
              <div className="grid gap-4 sm:grid-cols-2">
                <div className="space-y-2">
                  <Label>Rate Limit (/hr)</Label>
                  <Input type="number" min="1" max="1000"
                    value={createForm.rate_limit_per_hour}
                    onChange={(e) => setCreateForm({ ...createForm, rate_limit_per_hour: parseInt(e.target.value) || 100 })}
                  />
                </div>
                <div className="space-y-2">
                  <Label>Cost Limit ($/day)</Label>
                  <Input type="number" min="1" max="1000"
                    value={createForm.cost_limit_daily_usd}
                    onChange={(e) => setCreateForm({ ...createForm, cost_limit_daily_usd: parseFloat(e.target.value) || 50 })}
                  />
                </div>
              </div>
            </div>
            <DialogFooter>
              <Button variant="outline" onClick={() => setCreateDialogOpen(false)}>Cancel</Button>
              <Button onClick={handleCreateAgent} disabled={createMutation.isPending || !createForm.agent_name}>
                {createMutation.isPending && <Loader2 className="animate-spin h-4 w-4 mr-2" />}
                Create Agent
              </Button>
            </DialogFooter>
          </DialogContent>
        </Dialog>

        {/* ============================================================ */}
        {/* DIALOG: Delete Agent */}
        {/* ============================================================ */}
        <Dialog open={deleteDialogOpen} onOpenChange={setDeleteDialogOpen}>
          <DialogContent>
            <DialogHeader>
              <DialogTitle>Delete Agent</DialogTitle>
              <DialogDescription>
                Are you sure you want to delete &ldquo;{deletingAgent?.agent_name.replace(/_/g, ' ')}&rdquo;? This will remove the configuration permanently.
              </DialogDescription>
            </DialogHeader>
            <DialogFooter>
              <Button variant="outline" onClick={() => setDeleteDialogOpen(false)}>Cancel</Button>
              <Button variant="destructive" onClick={() => deletingAgent && deleteMutation.mutate(deletingAgent.agent_name)}
                disabled={deleteMutation.isPending}>
                {deleteMutation.isPending && <Loader2 className="animate-spin h-4 w-4 mr-2" />}
                Delete
              </Button>
            </DialogFooter>
          </DialogContent>
        </Dialog>

        {/* ============================================================ */}
        {/* SHEET: Agent Execution Logs */}
        {/* ============================================================ */}
        <Sheet open={!!logsAgent} onOpenChange={(open) => { if (!open) { setLogsAgent(null); setLogStatusFilter('all'); setLogSearchQuery(''); } }}>
          <SheetContent side="right" className="w-full sm:max-w-3xl overflow-y-auto">
            <SheetHeader>
              <SheetTitle className="capitalize flex items-center gap-2">
                <ScrollText className="h-5 w-5" />
                Logs: {logsAgent?.replace(/_/g, ' ')}
              </SheetTitle>
              <SheetDescription className="flex items-center justify-between">
                <span>Recent execution logs for this agent.</span>
                <Button
                  variant={liveStream ? 'default' : 'outline'}
                  size="sm"
                  onClick={() => { setLiveStream(!liveStream); if (liveStream) { streamRef.current?.abort(); } }}
                  className="gap-1.5"
                >
                  <Radio className={`h-3.5 w-3.5 ${liveStream ? 'animate-pulse' : ''}`} />
                  {liveStream ? 'Stop Stream' : 'Live Stream'}
                </Button>
              </SheetDescription>
            </SheetHeader>
            <div className="py-4">
              {logsLoading ? (
                <div className="flex justify-center py-8"><Loader2 className="animate-spin h-6 w-6" /></div>
              ) : !logsData || logsData.items.length === 0 ? (
                <div className="text-center py-12">
                  <ScrollText className="h-12 w-12 mx-auto mb-3 text-muted-foreground opacity-50" />
                  <p className="text-muted-foreground">No execution logs found for this agent.</p>
                </div>
              ) : (() => {
                const filteredLogs = logsData.items.filter((log: AgentExecutionLog) => {
                  if (logStatusFilter !== 'all' && log.status !== logStatusFilter) return false;
                  if (logSearchQuery) {
                    const q = logSearchQuery.toLowerCase();
                    return (log.error_message?.toLowerCase().includes(q) || log.source?.toLowerCase().includes(q));
                  }
                  return true;
                });
                return (
                  <div className="space-y-3">
                    {/* Filter Controls */}
                    <div className="flex flex-col sm:flex-row gap-2">
                      <Select value={logStatusFilter} onValueChange={setLogStatusFilter}>
                        <SelectTrigger className="w-[140px] h-8 text-sm">
                          <SelectValue placeholder="Status" />
                        </SelectTrigger>
                        <SelectContent>
                          <SelectItem value="all">All Status</SelectItem>
                          <SelectItem value="completed">Completed</SelectItem>
                          <SelectItem value="failed">Failed</SelectItem>
                          <SelectItem value="running">Running</SelectItem>
                        </SelectContent>
                      </Select>
                      <div className="relative flex-1">
                        <Search className="absolute left-2 top-1/2 -translate-y-1/2 h-3.5 w-3.5 text-muted-foreground" />
                        <Input
                          placeholder="Search errors..."
                          value={logSearchQuery}
                          onChange={(e) => setLogSearchQuery(e.target.value)}
                          className="pl-7 h-8 text-sm"
                        />
                      </div>
                    </div>
                    <p className="text-sm text-muted-foreground">
                      Showing {filteredLogs.length} of {logsData.total} logs
                    </p>
                    <Table>
                      <TableHeader>
                        <TableRow>
                          <TableHead>Time</TableHead>
                          <TableHead>Status</TableHead>
                          <TableHead className="text-center">Items</TableHead>
                          <TableHead className="text-center">Errors</TableHead>
                          <TableHead>Duration</TableHead>
                          <TableHead>Details</TableHead>
                        </TableRow>
                      </TableHeader>
                      <TableBody>
                        {filteredLogs.map((log: AgentExecutionLog) => (
                          <TableRow key={log.id} className={log.status === 'failed' ? 'border-l-2 border-l-red-500' : ''}>
                            <TableCell className="text-xs whitespace-nowrap">
                              {formatDateTimeMYT(log.started_at)}
                            </TableCell>
                            <TableCell>
                              <Badge variant={
                                log.status === 'completed' ? 'default'
                                : log.status === 'running' ? 'outline'
                                : log.status === 'failed' ? 'destructive'
                                : 'secondary'
                              }>
                                {log.status}
                              </Badge>
                            </TableCell>
                            <TableCell className="text-center">{log.items_processed}</TableCell>
                            <TableCell className="text-center">
                              {log.items_failed > 0 ? (
                                <span className="text-red-500 dark:text-red-400">{log.items_failed}</span>
                              ) : (
                                <span className="text-muted-foreground">0</span>
                              )}
                            </TableCell>
                            <TableCell className="text-sm">
                              {log.duration_ms ? `${(log.duration_ms / 1000).toFixed(1)}s` : '-'}
                            </TableCell>
                            <TableCell className="text-xs max-w-[200px]">
                              {log.error_message ? (
                                <span className="text-red-500 dark:text-red-400 line-clamp-2" title={log.error_message}>{log.error_message}</span>
                              ) : log.source ? (
                                <span className="text-muted-foreground">{log.source}</span>
                              ) : '-'}
                            </TableCell>
                          </TableRow>
                        ))}
                        {filteredLogs.length === 0 && (
                          <TableRow>
                            <TableCell colSpan={6} className="text-center py-8 text-muted-foreground">
                              No logs match the current filters.
                            </TableCell>
                          </TableRow>
                        )}
                      </TableBody>
                    </Table>
                  </div>
                );
              })()}

              {/* Live Stream Terminal */}
              {liveStream && (
                <div className="mt-6 border-t pt-4">
                  <div className="flex items-center justify-between mb-2">
                    <h4 className="text-sm font-medium flex items-center gap-2">
                      <Radio className="h-3.5 w-3.5 text-green-500 dark:text-green-400 animate-pulse" />
                      Live Stream
                    </h4>
                    <div className="flex items-center gap-2">
                      <Button variant="ghost" size="sm" onClick={() => setStreamPaused(!streamPaused)}>
                        {streamPaused ? <Play className="h-3.5 w-3.5" /> : <Pause className="h-3.5 w-3.5" />}
                        {streamPaused ? 'Resume' : 'Pause'}
                      </Button>
                      <Button variant="ghost" size="sm" onClick={() => setStreamLogs([])}>
                        <RotateCcw className="h-3.5 w-3.5" />
                        Clear
                      </Button>
                    </div>
                  </div>
                  <div
                    ref={terminalRef}
                    className="bg-zinc-950 dark:bg-black rounded-lg p-3 font-mono text-xs h-[300px] overflow-y-auto border border-zinc-800"
                  >
                    {streamLogs.length === 0 ? (
                      <p className="text-zinc-500">Waiting for log entries...</p>
                    ) : (
                      streamLogs.map((entry) => (
                        <div
                          key={entry.id}
                          className={`py-0.5 border-b border-zinc-900 last:border-0 ${
                            entry.status === 'failed' ? 'text-red-400' :
                            entry.status === 'completed' ? 'text-green-400' :
                            entry.status === 'running' ? 'text-blue-400' : 'text-zinc-400'
                          }`}
                        >
                          <span className="text-zinc-600">[{entry.started_at ? new Date(entry.started_at).toLocaleTimeString() : '--'}]</span>
                          {' '}
                          <span className="font-semibold">{entry.status.toUpperCase()}</span>
                          {entry.items_processed > 0 && <span className="text-zinc-500"> items={entry.items_processed}</span>}
                          {entry.duration_ms && <span className="text-zinc-500"> {(entry.duration_ms / 1000).toFixed(1)}s</span>}
                          {entry.source && <span className="text-zinc-500"> src={entry.source}</span>}
                          {entry.error_message && <span className="text-red-400 block pl-4">  {entry.error_message}</span>}
                        </div>
                      ))
                    )}
                    {streamPaused && <p className="text-yellow-500 mt-2">-- PAUSED --</p>}
                  </div>
                </div>
              )}
            </div>
          </SheetContent>
        </Sheet>

        {/* ============================================================ */}
        {/* DIALOG/SHEET: Create/Edit Market Insight */}
        {/* ============================================================ */}
        {miFullView ? (
          <Sheet open={miDialogOpen} onOpenChange={(open) => { if (!open) { setMiDialogOpen(false); setMiFullView(false); } }}>
            <SheetContent side="right" className="w-full sm:max-w-3xl overflow-y-auto">
              <SheetHeader>
                <div className="flex items-center justify-between pr-8">
                  <SheetTitle>{editingMi ? 'Edit Article' : 'Create Market Insight'}</SheetTitle>
                  <Button variant="ghost" size="icon" onClick={() => setMiFullView(false)} title="Exit full view">
                    <Minimize2 className="h-4 w-4" />
                  </Button>
                </div>
                <SheetDescription>
                  {editingMi ? 'Update the article in full view.' : 'Write a new market insight article.'}
                </SheetDescription>
              </SheetHeader>
              <div className="py-4">
                <MiEditFormContent />
              </div>
              <SheetFooter>
                <Button variant="outline" onClick={() => { setMiDialogOpen(false); setMiFullView(false); }}>Cancel</Button>
                <Button onClick={handleMiSubmit}>
                  {editingMi ? 'Update Article' : 'Create Article'}
                </Button>
              </SheetFooter>
            </SheetContent>
          </Sheet>
        ) : (
          <Dialog open={miDialogOpen} onOpenChange={setMiDialogOpen}>
            <DialogContent className="max-w-4xl max-h-[90vh] overflow-y-auto">
              <DialogHeader>
                <div className="flex items-center justify-between pr-8">
                  <DialogTitle>{editingMi ? 'Edit Article' : 'Create Market Insight'}</DialogTitle>
                  <Button variant="ghost" size="icon" onClick={() => setMiFullView(true)} title="Full view">
                    <Maximize2 className="h-4 w-4" />
                  </Button>
                </div>
                <DialogDescription>
                  {editingMi ? 'Update the article.' : 'Write a new market insight article. Supports Markdown.'}
                </DialogDescription>
              </DialogHeader>
              <MiEditFormContent />
              <DialogFooter>
                <Button variant="outline" onClick={() => setMiDialogOpen(false)}>Cancel</Button>
                <Button onClick={handleMiSubmit}>
                  {editingMi ? 'Update Article' : 'Create Article'}
                </Button>
              </DialogFooter>
            </DialogContent>
          </Dialog>
        )}

        {/* DIALOG: Delete Market Insight */}
        <Dialog open={miDeleteDialogOpen} onOpenChange={setMiDeleteDialogOpen}>
          <DialogContent>
            <DialogHeader>
              <DialogTitle>Delete Article</DialogTitle>
              <DialogDescription>
                Are you sure you want to delete &ldquo;{deletingMi?.title}&rdquo;? This cannot be undone.
              </DialogDescription>
            </DialogHeader>
            <DialogFooter>
              <Button variant="outline" onClick={() => setMiDeleteDialogOpen(false)}>Cancel</Button>
              <Button variant="destructive" onClick={handleMiDelete}>Delete</Button>
            </DialogFooter>
          </DialogContent>
        </Dialog>

        {/* DIALOG: Delete Insight */}
        <Dialog open={insightDeleteDialogOpen} onOpenChange={setInsightDeleteDialogOpen}>
          <DialogContent>
            <DialogHeader>
              <DialogTitle>Delete Insight</DialogTitle>
              <DialogDescription>
                Are you sure you want to delete &ldquo;{deletingInsight?.proposed_solution}&rdquo;? This cannot be undone.
              </DialogDescription>
            </DialogHeader>
            <DialogFooter>
              <Button variant="outline" onClick={() => setInsightDeleteDialogOpen(false)}>Cancel</Button>
              <Button variant="destructive" onClick={handleInsightDelete}>Delete</Button>
            </DialogFooter>
          </DialogContent>
        </Dialog>
      </div>
    </div>
  );
}
