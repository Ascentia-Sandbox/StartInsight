'use client';

import { useState, useEffect, useCallback } from 'react';
import { useRouter, useSearchParams } from 'next/navigation';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { Suspense } from 'react';
import {
  Loader2,
  Search,
  Pencil,
  Trash2,
  CheckCircle2,
  XCircle,
  Clock,
  Lightbulb,
  Filter,
  Plus,
  X,
  Download,
  FileJson,
  FileSpreadsheet,
} from 'lucide-react';
import { getSupabaseClient } from '@/lib/supabase/client';
import {
  fetchAdminInsights,
  updateInsightAdmin,
  deleteInsightAdmin,
  createInsightAdmin,
  createAuthenticatedClient,
  type InsightAdmin,
  type InsightAdminList,
} from '@/lib/api';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Input } from '@/components/ui/input';
import { Textarea } from '@/components/ui/textarea';
import { Label } from '@/components/ui/label';
import { Checkbox } from '@/components/ui/checkbox';
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table';
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
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog';
import { Slider } from '@/components/ui/slider';
import { toast } from 'sonner';
import { formatDateMYT } from '@/lib/utils';
import { AdminPagination } from '@/components/admin/admin-pagination';

const SCORE_DIMENSIONS = [
  { key: 'opportunity_score', label: 'Opportunity', color: 'bg-blue-500 dark:bg-blue-400' },
  { key: 'problem_score', label: 'Problem', color: 'bg-red-500 dark:bg-red-400' },
  { key: 'feasibility_score', label: 'Feasibility', color: 'bg-green-500 dark:bg-green-400' },
  { key: 'why_now_score', label: 'Why Now', color: 'bg-yellow-500 dark:bg-yellow-400' },
  { key: 'execution_difficulty', label: 'Execution', color: 'bg-purple-500 dark:bg-purple-400' },
  { key: 'go_to_market_score', label: 'GTM', color: 'bg-pink-500 dark:bg-pink-400' },
  { key: 'founder_fit_score', label: 'Founder Fit', color: 'bg-indigo-500 dark:bg-indigo-400' },
] as const;

function StatusBadge({ status }: { status: string | null | undefined }) {
  const s = status || 'approved';
  const variants: Record<string, { variant: 'default' | 'secondary' | 'destructive' | 'outline'; icon: typeof CheckCircle2 }> = {
    approved: { variant: 'default', icon: CheckCircle2 },
    pending: { variant: 'secondary', icon: Clock },
    rejected: { variant: 'destructive', icon: XCircle },
  };
  const v = variants[s] || variants.approved;
  const Icon = v.icon;
  return (
    <Badge variant={v.variant} className="gap-1">
      <Icon className="h-3 w-3" />
      {s}
    </Badge>
  );
}

function ScoreBars({ insight }: { insight: InsightAdmin }) {
  return (
    <div className="flex gap-0.5 items-end h-6">
      {SCORE_DIMENSIONS.map(({ key, label, color }) => {
        const val = insight[key as keyof InsightAdmin] as number | null;
        if (!val) return <div key={key} className="w-2 h-1 bg-muted rounded-sm" title={`${label}: N/A`} />;
        return (
          <div
            key={key}
            className={`w-2 rounded-sm ${color}`}
            style={{ height: `${(val / 10) * 100}%` }}
            title={`${label}: ${val}/10`}
          />
        );
      })}
    </div>
  );
}

export default function AdminInsightsPage() {
  return (
    <Suspense fallback={
      <div className="flex items-center justify-center h-64">
        <Loader2 className="h-6 w-6 animate-spin" />
      </div>
    }>
      <AdminInsightsContent />
    </Suspense>
  );
}

function AdminInsightsContent() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const queryClient = useQueryClient();
  const [accessToken, setAccessToken] = useState<string | null>(null);
  const [search, setSearch] = useState('');
  const [statusFilter, setStatusFilter] = useState<string>('all');
  const [editSheet, setEditSheet] = useState<InsightAdmin | null>(null);
  const [createDialog, setCreateDialog] = useState(false);
  const [deleteDialog, setDeleteDialog] = useState<InsightAdmin | null>(null);
  const [bulkDeleteDialog, setBulkDeleteDialog] = useState(false);
  const [selectedIds, setSelectedIds] = useState<Set<string>>(new Set());
  const [editForm, setEditForm] = useState<Record<string, unknown>>({});
  const [createForm, setCreateForm] = useState<Record<string, unknown>>({
    title: '',
    problem_statement: '',
    proposed_solution: '',
    market_size_estimate: 'Medium',
    relevance_score: 0.8,
    admin_status: 'approved',
    opportunity_score: 5,
    problem_score: 5,
    feasibility_score: 5,
    why_now_score: 5,
    execution_difficulty: 5,
    go_to_market_score: 5,
    founder_fit_score: 5,
    revenue_potential: '$$',
    market_gap_analysis: '',
    why_now_analysis: '',
  });

  const currentPage = Number(searchParams.get('page')) || 1;
  const perPage = Number(searchParams.get('per_page')) || 20;
  const page = currentPage - 1; // 0-indexed for API offset
  const limit = perPage;

  // Auth
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

  // Query
  const { data, isLoading, error } = useQuery({
    queryKey: ['admin-insights', accessToken, search, statusFilter, page],
    queryFn: () =>
      fetchAdminInsights(accessToken!, {
        search: search || undefined,
        status: statusFilter === 'all' ? undefined : statusFilter,
        limit,
        offset: page * limit,
      }),
    enabled: !!accessToken,
    staleTime: 30_000,
  });

  // Mutations
  const updateMutation = useMutation({
    mutationFn: ({ id, payload }: { id: string; payload: Record<string, unknown> }) =>
      updateInsightAdmin(accessToken!, id, payload),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['admin-insights'] });
      setEditSheet(null);
      toast.success('Insight updated');
    },
    onError: (err: Error) => toast.error(`Update failed: ${err.message}`),
  });

  const deleteMutation = useMutation({
    mutationFn: (id: string) => deleteInsightAdmin(accessToken!, id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['admin-insights'] });
      setDeleteDialog(null);
      toast.success('Insight deleted');
    },
    onError: (err: Error) => toast.error(`Delete failed: ${err.message}`),
  });

  const createMutation = useMutation({
    mutationFn: (payload: Record<string, unknown>) =>
      createInsightAdmin(accessToken!, payload),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['admin-insights'] });
      setCreateDialog(false);
      setCreateForm({
        title: '', problem_statement: '', proposed_solution: '',
        market_size_estimate: 'Medium', relevance_score: 0.8, admin_status: 'approved',
        opportunity_score: 5, problem_score: 5, feasibility_score: 5,
        why_now_score: 5, execution_difficulty: 5, go_to_market_score: 5,
        founder_fit_score: 5, revenue_potential: '$$', market_gap_analysis: '', why_now_analysis: '',
      });
      toast.success('Insight created');
    },
    onError: (err: Error) => toast.error(`Create failed: ${err.message}`),
  });

  // Bulk actions
  const handleBulkApprove = async () => {
    const count = selectedIds.size;
    for (const id of selectedIds) {
      await updateInsightAdmin(accessToken!, id, { admin_status: 'approved' });
    }
    queryClient.invalidateQueries({ queryKey: ['admin-insights'] });
    setSelectedIds(new Set());
    toast.success(`${count} insights approved`);
  };

  const handleBulkReject = async () => {
    const count = selectedIds.size;
    for (const id of selectedIds) {
      await updateInsightAdmin(accessToken!, id, { admin_status: 'rejected' });
    }
    queryClient.invalidateQueries({ queryKey: ['admin-insights'] });
    setSelectedIds(new Set());
    toast.success(`${count} insights rejected`);
  };

  // Export handlers
  const handleExport = async (format: 'csv' | 'json') => {
    if (!accessToken) return;
    try {
      const client = createAuthenticatedClient(accessToken);
      const params: Record<string, string> = { format };
      if (statusFilter !== 'all') params.status = statusFilter;
      if (search) params.search = search;

      const { data } = await client.get('/api/admin/insights/export', {
        params,
        responseType: format === 'csv' ? 'blob' : 'json',
      });

      if (format === 'csv') {
        const blob = new Blob([data], { type: 'text/csv' });
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `insights-export-${new Date().toISOString().slice(0, 10)}.csv`;
        document.body.appendChild(a);
        a.click();
        window.URL.revokeObjectURL(url);
        document.body.removeChild(a);
      } else {
        const jsonStr = JSON.stringify(data, null, 2);
        const blob = new Blob([jsonStr], { type: 'application/json' });
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `insights-export-${new Date().toISOString().slice(0, 10)}.json`;
        document.body.appendChild(a);
        a.click();
        window.URL.revokeObjectURL(url);
        document.body.removeChild(a);
      }

      toast.success(`Insights exported as ${format.toUpperCase()}`);
    } catch (err) {
      toast.error(`Export failed: ${err instanceof Error ? err.message : 'Unknown error'}`);
    }
  };

  const handleBulkExport = async (format: 'csv' | 'json') => {
    if (!accessToken || selectedIds.size === 0) return;
    try {
      const client = createAuthenticatedClient(accessToken);
      const ids = Array.from(selectedIds).join(',');
      const { data } = await client.get('/api/admin/insights/export', {
        params: { format, ids },
        responseType: format === 'csv' ? 'blob' : 'json',
      });

      if (format === 'csv') {
        const blob = new Blob([data], { type: 'text/csv' });
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `insights-selected-${selectedIds.size}-${new Date().toISOString().slice(0, 10)}.csv`;
        document.body.appendChild(a);
        a.click();
        window.URL.revokeObjectURL(url);
        document.body.removeChild(a);
      } else {
        const jsonStr = JSON.stringify(data, null, 2);
        const blob = new Blob([jsonStr], { type: 'application/json' });
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `insights-selected-${selectedIds.size}-${new Date().toISOString().slice(0, 10)}.json`;
        document.body.appendChild(a);
        a.click();
        window.URL.revokeObjectURL(url);
        document.body.removeChild(a);
      }

      toast.success(`${selectedIds.size} insights exported as ${format.toUpperCase()}`);
    } catch (err) {
      toast.error(`Export failed: ${err instanceof Error ? err.message : 'Unknown error'}`);
    }
  };

  const handleBulkDelete = async () => {
    if (!accessToken || selectedIds.size === 0) return;
    try {
      const count = selectedIds.size;
      const client = createAuthenticatedClient(accessToken);
      await client.post('/api/admin/insights/bulk-delete', {
        ids: Array.from(selectedIds),
      });
      queryClient.invalidateQueries({ queryKey: ['admin-insights'] });
      toast.success(`${count} insights deleted`);
      setSelectedIds(new Set());
      setBulkDeleteDialog(false);
    } catch (err) {
      toast.error(`Bulk delete failed: ${err instanceof Error ? err.message : 'Unknown error'}`);
    }
  };

  // Open edit sheet
  const openEdit = (insight: InsightAdmin) => {
    setEditForm({
      title: insight.title || '',
      problem_statement: insight.problem_statement,
      proposed_solution: insight.proposed_solution,
      market_size_estimate: insight.market_size_estimate,
      admin_status: insight.admin_status || 'approved',
      admin_notes: insight.admin_notes || '',
      opportunity_score: insight.opportunity_score || 5,
      problem_score: insight.problem_score || 5,
      feasibility_score: insight.feasibility_score || 5,
      why_now_score: insight.why_now_score || 5,
      execution_difficulty: insight.execution_difficulty || 5,
      go_to_market_score: insight.go_to_market_score || 5,
      founder_fit_score: insight.founder_fit_score || 5,
      revenue_potential: insight.revenue_potential || '$$',
      market_gap_analysis: insight.market_gap_analysis || '',
      why_now_analysis: insight.why_now_analysis || '',
    });
    setEditSheet(insight);
  };

  const handleSave = () => {
    if (!editSheet) return;
    updateMutation.mutate({ id: editSheet.id, payload: editForm });
  };

  const toggleSelect = (id: string) => {
    setSelectedIds((prev) => {
      const next = new Set(prev);
      if (next.has(id)) next.delete(id);
      else next.add(id);
      return next;
    });
  };

  const toggleAll = () => {
    if (!data?.items) return;
    if (selectedIds.size === data.items.length) {
      setSelectedIds(new Set());
    } else {
      setSelectedIds(new Set(data.items.map((i) => i.id)));
    }
  };

  if (!accessToken) {
    return (
      <div className="flex items-center justify-center h-64">
        <Loader2 className="h-6 w-6 animate-spin" />
      </div>
    );
  }

  return (
    <div className="p-6 space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold flex items-center gap-2">
            <Lightbulb className="h-6 w-6" />
            Insight Management
          </h1>
          <p className="text-muted-foreground text-sm mt-1">
            Create, edit, approve, and manage all startup insights
          </p>
        </div>
        <div className="flex items-center gap-3">
          {data && (
            <div className="flex gap-2">
              <Badge variant="secondary">{data.pending_count} pending</Badge>
              <Badge variant="default">{data.approved_count} approved</Badge>
              <Badge variant="destructive">{data.rejected_count} rejected</Badge>
            </div>
          )}
          <div className="flex gap-1">
            <Button variant="outline" size="sm" onClick={() => handleExport('csv')}>
              <FileSpreadsheet className="h-4 w-4 mr-1" />
              CSV
            </Button>
            <Button variant="outline" size="sm" onClick={() => handleExport('json')}>
              <FileJson className="h-4 w-4 mr-1" />
              JSON
            </Button>
          </div>
          <Button onClick={() => setCreateDialog(true)}>
            <Plus className="h-4 w-4 mr-2" />
            Create Insight
          </Button>
        </div>
      </div>

      {/* Filters */}
      <Card>
        <CardContent className="pt-4">
          <div className="flex flex-col sm:flex-row gap-3">
            <div className="relative flex-1">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
              <Input
                placeholder="Search by title, problem, or solution..."
                value={search}
                onChange={(e) => {
                  setSearch(e.target.value);
                  const params = new URLSearchParams(searchParams.toString());
                  params.set('page', '1');
                  router.push(`?${params.toString()}`);
                }}
                className="pl-9"
              />
              {search && (
                <Button
                  variant="ghost"
                  size="icon"
                  className="absolute right-1 top-1/2 -translate-y-1/2 h-6 w-6"
                  onClick={() => setSearch('')}
                >
                  <X className="h-3 w-3" />
                </Button>
              )}
            </div>
            <Select value={statusFilter} onValueChange={(v) => {
              setStatusFilter(v);
              const params = new URLSearchParams(searchParams.toString());
              params.set('page', '1');
              router.push(`?${params.toString()}`);
            }}>
              <SelectTrigger className="w-[150px]">
                <Filter className="h-4 w-4 mr-2" />
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">All Status</SelectItem>
                <SelectItem value="pending">Pending</SelectItem>
                <SelectItem value="approved">Approved</SelectItem>
                <SelectItem value="rejected">Rejected</SelectItem>
              </SelectContent>
            </Select>
          </div>
        </CardContent>
      </Card>

      {/* Bulk actions */}
      {selectedIds.size > 0 && (
        <div className="flex items-center gap-3 p-3 bg-primary/5 border rounded-lg">
          <span className="text-sm font-medium">{selectedIds.size} selected</span>
          <div className="h-4 w-px bg-border" />
          <Button size="sm" variant="outline" onClick={handleBulkApprove}>
            <CheckCircle2 className="h-3 w-3 mr-1" /> Approve
          </Button>
          <Button size="sm" variant="outline" onClick={handleBulkReject}>
            <XCircle className="h-3 w-3 mr-1" /> Reject
          </Button>
          <Button size="sm" variant="outline" onClick={() => setBulkDeleteDialog(true)}>
            <Trash2 className="h-3 w-3 mr-1" /> Delete Selected
          </Button>
          <div className="h-4 w-px bg-border" />
          <Button size="sm" variant="outline" onClick={() => handleBulkExport('csv')}>
            <Download className="h-3 w-3 mr-1" /> Export CSV
          </Button>
          <Button size="sm" variant="outline" onClick={() => handleBulkExport('json')}>
            <Download className="h-3 w-3 mr-1" /> Export JSON
          </Button>
          <div className="ml-auto">
            <Button size="sm" variant="ghost" onClick={() => setSelectedIds(new Set())}>
              Clear Selection
            </Button>
          </div>
        </div>
      )}

      {/* Table */}
      <Card>
        <CardContent className="p-0">
          {isLoading ? (
            <div className="flex items-center justify-center h-48">
              <Loader2 className="h-6 w-6 animate-spin" />
            </div>
          ) : error ? (
            <div className="p-6 text-center text-destructive">
              Failed to load insights. Please try again.
            </div>
          ) : (
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead className="w-10">
                    <Checkbox
                      checked={data?.items && data.items.length > 0 && selectedIds.size === data.items.length}
                      onCheckedChange={toggleAll}
                    />
                  </TableHead>
                  <TableHead>Title / Solution</TableHead>
                  <TableHead className="w-20">Score</TableHead>
                  <TableHead className="w-28">Dimensions</TableHead>
                  <TableHead className="w-20">Status</TableHead>
                  <TableHead className="w-20">Source</TableHead>
                  <TableHead className="w-28">Created</TableHead>
                  <TableHead className="w-20">Actions</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {data?.items.map((insight) => (
                  <TableRow
                    key={insight.id}
                    className="cursor-pointer hover:bg-muted/50"
                    onClick={() => openEdit(insight)}
                  >
                    <TableCell onClick={(e) => e.stopPropagation()}>
                      <Checkbox
                        checked={selectedIds.has(insight.id)}
                        onCheckedChange={() => toggleSelect(insight.id)}
                      />
                    </TableCell>
                    <TableCell>
                      <div className="max-w-[300px]">
                        <p className="font-medium truncate">
                          {insight.title || insight.proposed_solution}
                        </p>
                        <p className="text-xs text-muted-foreground truncate">
                          {insight.problem_statement.slice(0, 80)}...
                        </p>
                      </div>
                    </TableCell>
                    <TableCell>
                      <span className="font-mono text-sm font-semibold">
                        {(insight.relevance_score * 100).toFixed(0)}%
                      </span>
                    </TableCell>
                    <TableCell>
                      <ScoreBars insight={insight} />
                    </TableCell>
                    <TableCell>
                      <StatusBadge status={insight.admin_status} />
                    </TableCell>
                    <TableCell>
                      <Badge variant="outline" className="text-xs">
                        {insight.source}
                      </Badge>
                    </TableCell>
                    <TableCell className="text-xs text-muted-foreground">
                      {formatDateMYT(insight.created_at)}
                    </TableCell>
                    <TableCell onClick={(e) => e.stopPropagation()}>
                      <div className="flex gap-1">
                        <Button
                          variant="ghost"
                          size="icon"
                          className="h-7 w-7"
                          onClick={() => openEdit(insight)}
                        >
                          <Pencil className="h-3 w-3" />
                        </Button>
                        <Button
                          variant="ghost"
                          size="icon"
                          className="h-7 w-7 text-destructive"
                          onClick={() => setDeleteDialog(insight)}
                        >
                          <Trash2 className="h-3 w-3" />
                        </Button>
                      </div>
                    </TableCell>
                  </TableRow>
                ))}
                {data?.items.length === 0 && (
                  <TableRow>
                    <TableCell colSpan={8} className="text-center py-12 text-muted-foreground">
                      No insights found
                    </TableCell>
                  </TableRow>
                )}
              </TableBody>
            </Table>
          )}
        </CardContent>
      </Card>

      {/* Pagination */}
      {(data?.total || 0) > 0 && (
        <AdminPagination
          totalItems={data?.total || 0}
          currentPage={currentPage}
          perPage={perPage}
        />
      )}

      {/* Edit Sheet */}
      <Sheet open={!!editSheet} onOpenChange={(open) => !open && setEditSheet(null)}>
        <SheetContent className="sm:max-w-lg overflow-y-auto">
          <SheetHeader>
            <SheetTitle>Edit Insight</SheetTitle>
            <SheetDescription>
              Modify insight content, scores, and status
            </SheetDescription>
          </SheetHeader>

          <div className="space-y-4 py-4">
            {/* Status */}
            <div className="space-y-2">
              <Label>Status</Label>
              <Select
                value={editForm.admin_status as string}
                onValueChange={(v) => setEditForm({ ...editForm, admin_status: v })}
              >
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="approved">Approved</SelectItem>
                  <SelectItem value="pending">Pending</SelectItem>
                  <SelectItem value="rejected">Rejected</SelectItem>
                </SelectContent>
              </Select>
            </div>

            {/* Title */}
            <div className="space-y-2">
              <Label>Title</Label>
              <Input
                value={editForm.title as string}
                onChange={(e) => setEditForm({ ...editForm, title: e.target.value })}
                placeholder="Insight title"
              />
            </div>

            {/* Problem Statement */}
            <div className="space-y-2">
              <Label>Problem Statement</Label>
              <Textarea
                value={editForm.problem_statement as string}
                onChange={(e) => setEditForm({ ...editForm, problem_statement: e.target.value })}
                rows={4}
              />
            </div>

            {/* Proposed Solution */}
            <div className="space-y-2">
              <Label>Proposed Solution</Label>
              <Textarea
                value={editForm.proposed_solution as string}
                onChange={(e) => setEditForm({ ...editForm, proposed_solution: e.target.value })}
                rows={3}
              />
            </div>

            {/* Market Size */}
            <div className="space-y-2">
              <Label>Market Size Estimate</Label>
              <Select
                value={editForm.market_size_estimate as string}
                onValueChange={(v) => setEditForm({ ...editForm, market_size_estimate: v })}
              >
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="Small">Small (&lt;$100M)</SelectItem>
                  <SelectItem value="Medium">Medium ($100M-$1B)</SelectItem>
                  <SelectItem value="Large">Large (&gt;$1B)</SelectItem>
                </SelectContent>
              </Select>
            </div>

            {/* Revenue Potential */}
            <div className="space-y-2">
              <Label>Revenue Potential</Label>
              <Select
                value={editForm.revenue_potential as string}
                onValueChange={(v) => setEditForm({ ...editForm, revenue_potential: v })}
              >
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="$">$ (Low)</SelectItem>
                  <SelectItem value="$$">$$ (Medium)</SelectItem>
                  <SelectItem value="$$$">$$$ (High)</SelectItem>
                  <SelectItem value="$$$$">$$$$ (Very High)</SelectItem>
                </SelectContent>
              </Select>
            </div>

            {/* Score Sliders */}
            <div className="space-y-3">
              <Label className="text-base font-semibold">Dimension Scores (1-10)</Label>
              {SCORE_DIMENSIONS.map(({ key, label }) => (
                <div key={key} className="space-y-1">
                  <div className="flex justify-between text-sm">
                    <span>{label}</span>
                    <span className="font-mono font-semibold">{editForm[key] as number}/10</span>
                  </div>
                  <Slider
                    value={[editForm[key] as number || 5]}
                    onValueChange={([v]) => setEditForm({ ...editForm, [key]: v })}
                    min={1}
                    max={10}
                    step={1}
                  />
                </div>
              ))}
            </div>

            {/* Analysis Text */}
            <div className="space-y-2">
              <Label>Market Gap Analysis</Label>
              <Textarea
                value={editForm.market_gap_analysis as string}
                onChange={(e) => setEditForm({ ...editForm, market_gap_analysis: e.target.value })}
                rows={4}
                placeholder="200-500 word competitor gap analysis"
              />
            </div>

            <div className="space-y-2">
              <Label>Why Now Analysis</Label>
              <Textarea
                value={editForm.why_now_analysis as string}
                onChange={(e) => setEditForm({ ...editForm, why_now_analysis: e.target.value })}
                rows={4}
                placeholder="200-500 word timing analysis"
              />
            </div>

            {/* Admin Notes */}
            <div className="space-y-2">
              <Label>Admin Notes</Label>
              <Textarea
                value={editForm.admin_notes as string}
                onChange={(e) => setEditForm({ ...editForm, admin_notes: e.target.value })}
                rows={2}
                placeholder="Internal notes"
              />
            </div>
          </div>

          <SheetFooter className="flex gap-2">
            <Button variant="outline" onClick={() => setEditSheet(null)}>
              Cancel
            </Button>
            <Button
              onClick={handleSave}
              disabled={updateMutation.isPending}
            >
              {updateMutation.isPending && <Loader2 className="h-4 w-4 mr-2 animate-spin" />}
              Save Changes
            </Button>
          </SheetFooter>
        </SheetContent>
      </Sheet>

      {/* Delete Confirmation Dialog */}
      <Dialog open={!!deleteDialog} onOpenChange={(open) => !open && setDeleteDialog(null)}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Delete Insight</DialogTitle>
            <DialogDescription>
              This will soft-delete the insight by setting its status to rejected.
              The insight data is preserved for audit purposes.
            </DialogDescription>
          </DialogHeader>
          <p className="text-sm">
            <strong>{deleteDialog?.title || deleteDialog?.proposed_solution}</strong>
          </p>
          <DialogFooter>
            <Button variant="outline" onClick={() => setDeleteDialog(null)}>
              Cancel
            </Button>
            <Button
              variant="destructive"
              onClick={() => deleteDialog && deleteMutation.mutate(deleteDialog.id)}
              disabled={deleteMutation.isPending}
            >
              {deleteMutation.isPending && <Loader2 className="h-4 w-4 mr-2 animate-spin" />}
              Delete
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Bulk Delete Confirmation Dialog */}
      <Dialog open={bulkDeleteDialog} onOpenChange={setBulkDeleteDialog}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Delete {selectedIds.size} Insights</DialogTitle>
            <DialogDescription>
              This will soft-delete {selectedIds.size} selected insights by setting their status to rejected.
              All insight data is preserved for audit purposes. This action cannot be easily undone.
            </DialogDescription>
          </DialogHeader>
          <div className="flex items-center gap-2 p-3 bg-destructive/10 border border-destructive/20 rounded-md">
            <Trash2 className="h-4 w-4 text-destructive" />
            <p className="text-sm text-destructive">
              {selectedIds.size} insight{selectedIds.size !== 1 ? 's' : ''} will be marked as rejected.
            </p>
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setBulkDeleteDialog(false)}>
              Cancel
            </Button>
            <Button
              variant="destructive"
              onClick={handleBulkDelete}
            >
              <Trash2 className="h-4 w-4 mr-2" />
              Delete {selectedIds.size} Insights
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Create Insight Dialog */}
      <Sheet open={createDialog} onOpenChange={setCreateDialog}>
        <SheetContent className="sm:max-w-lg overflow-y-auto">
          <SheetHeader>
            <SheetTitle>Create New Insight</SheetTitle>
            <SheetDescription>
              Manually add a new startup insight with scores and analysis
            </SheetDescription>
          </SheetHeader>

          <div className="space-y-4 py-4">
            <div className="space-y-2">
              <Label>Title *</Label>
              <Input
                value={createForm.title as string}
                onChange={(e) => setCreateForm({ ...createForm, title: e.target.value })}
                placeholder="e.g., AI-Powered Legal Document Review"
              />
            </div>

            <div className="space-y-2">
              <Label>Problem Statement *</Label>
              <Textarea
                value={createForm.problem_statement as string}
                onChange={(e) => setCreateForm({ ...createForm, problem_statement: e.target.value })}
                rows={4}
                placeholder="Describe the market problem..."
              />
            </div>

            <div className="space-y-2">
              <Label>Proposed Solution *</Label>
              <Textarea
                value={createForm.proposed_solution as string}
                onChange={(e) => setCreateForm({ ...createForm, proposed_solution: e.target.value })}
                rows={3}
                placeholder="Describe the solution approach..."
              />
            </div>

            <div className="grid gap-3 sm:grid-cols-2">
              <div className="space-y-2">
                <Label>Market Size *</Label>
                <Select
                  value={createForm.market_size_estimate as string}
                  onValueChange={(v) => setCreateForm({ ...createForm, market_size_estimate: v })}
                >
                  <SelectTrigger><SelectValue /></SelectTrigger>
                  <SelectContent>
                    <SelectItem value="Small">Small (&lt;$100M)</SelectItem>
                    <SelectItem value="Medium">Medium ($100M-$1B)</SelectItem>
                    <SelectItem value="Large">Large (&gt;$1B)</SelectItem>
                  </SelectContent>
                </Select>
              </div>
              <div className="space-y-2">
                <Label>Revenue Potential</Label>
                <Select
                  value={createForm.revenue_potential as string}
                  onValueChange={(v) => setCreateForm({ ...createForm, revenue_potential: v })}
                >
                  <SelectTrigger><SelectValue /></SelectTrigger>
                  <SelectContent>
                    <SelectItem value="$">$ (Low)</SelectItem>
                    <SelectItem value="$$">$$ (Medium)</SelectItem>
                    <SelectItem value="$$$">$$$ (High)</SelectItem>
                    <SelectItem value="$$$$">$$$$ (Very High)</SelectItem>
                  </SelectContent>
                </Select>
              </div>
            </div>

            <div className="space-y-2">
              <Label>Status</Label>
              <Select
                value={createForm.admin_status as string}
                onValueChange={(v) => setCreateForm({ ...createForm, admin_status: v })}
              >
                <SelectTrigger><SelectValue /></SelectTrigger>
                <SelectContent>
                  <SelectItem value="approved">Approved</SelectItem>
                  <SelectItem value="pending">Pending</SelectItem>
                </SelectContent>
              </Select>
            </div>

            <div className="space-y-3">
              <Label className="text-base font-semibold">Dimension Scores (1-10)</Label>
              {SCORE_DIMENSIONS.map(({ key, label }) => (
                <div key={key} className="space-y-1">
                  <div className="flex justify-between text-sm">
                    <span>{label}</span>
                    <span className="font-mono font-semibold">{createForm[key] as number}/10</span>
                  </div>
                  <Slider
                    value={[createForm[key] as number || 5]}
                    onValueChange={([v]) => setCreateForm({ ...createForm, [key]: v })}
                    min={1}
                    max={10}
                    step={1}
                  />
                </div>
              ))}
            </div>

            <div className="space-y-2">
              <Label>Market Gap Analysis</Label>
              <Textarea
                value={createForm.market_gap_analysis as string}
                onChange={(e) => setCreateForm({ ...createForm, market_gap_analysis: e.target.value })}
                rows={3}
                placeholder="Competitor gap analysis (optional)"
              />
            </div>

            <div className="space-y-2">
              <Label>Why Now Analysis</Label>
              <Textarea
                value={createForm.why_now_analysis as string}
                onChange={(e) => setCreateForm({ ...createForm, why_now_analysis: e.target.value })}
                rows={3}
                placeholder="Market timing analysis (optional)"
              />
            </div>
          </div>

          <SheetFooter className="flex gap-2">
            <Button variant="outline" onClick={() => setCreateDialog(false)}>
              Cancel
            </Button>
            <Button
              onClick={() => createMutation.mutate(createForm)}
              disabled={
                createMutation.isPending ||
                !(createForm.title as string)?.trim() ||
                !(createForm.problem_statement as string)?.trim() ||
                !(createForm.proposed_solution as string)?.trim()
              }
            >
              {createMutation.isPending && <Loader2 className="h-4 w-4 mr-2 animate-spin" />}
              Create Insight
            </Button>
          </SheetFooter>
        </SheetContent>
      </Sheet>
    </div>
  );
}
