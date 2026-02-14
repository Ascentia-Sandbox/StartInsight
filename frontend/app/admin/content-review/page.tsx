'use client';

import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import {
  Loader2, FileCheck, CheckCircle2, XCircle, Clock, Eye, AlertTriangle,
} from 'lucide-react';
import { getSupabaseClient } from '@/lib/supabase/client';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Textarea } from '@/components/ui/textarea';
import { Label } from '@/components/ui/label';
import {
  Table, TableBody, TableCell, TableHead, TableHeader, TableRow,
} from '@/components/ui/table';
import {
  Select, SelectContent, SelectItem, SelectTrigger, SelectValue,
} from '@/components/ui/select';
import {
  Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle,
} from '@/components/ui/dialog';
import { toast } from 'sonner';
import { formatDateTimeMYT } from '@/lib/utils';
import { config } from '@/lib/env';
import axios from 'axios';

const API_URL = config.apiUrl;

function createClient(token: string) {
  return axios.create({
    baseURL: API_URL,
    headers: { Authorization: `Bearer ${token}`, 'Content-Type': 'application/json' },
  });
}

interface ReviewItem {
  id: string;
  content_type: string;
  content_id: string;
  title: string;
  status: string;
  quality_score: number | null;
  reviewer_notes: string | null;
  submitted_at: string;
  reviewed_at: string | null;
}

interface QueueStats {
  total: number;
  pending: number;
  approved: number;
  rejected: number;
  avg_quality_score: number | null;
}

export default function ContentReviewPage() {
  const router = useRouter();
  const queryClient = useQueryClient();
  const [accessToken, setAccessToken] = useState<string | null>(null);
  const [statusFilter, setStatusFilter] = useState('pending');
  const [reviewDialog, setReviewDialog] = useState<ReviewItem | null>(null);
  const [reviewNotes, setReviewNotes] = useState('');
  const [reviewAction, setReviewAction] = useState<'approve' | 'reject'>('approve');

  useEffect(() => {
    const supabase = getSupabaseClient();
    supabase.auth.getSession().then(({ data }: { data: { session: { access_token: string } | null } }) => {
      if (data.session?.access_token) setAccessToken(data.session.access_token);
      else router.push('/auth/login?redirectTo=/admin/content-review');
    });
  }, [router]);

  const { data: queueData, isLoading } = useQuery({
    queryKey: ['content-review-queue', accessToken, statusFilter],
    queryFn: async () => {
      const client = createClient(accessToken!);
      const { data } = await client.get('/admin/content/review-queue', {
        params: { status: statusFilter === 'all' ? undefined : statusFilter },
      });
      return data as { items: ReviewItem[]; total: number };
    },
    enabled: !!accessToken,
  });

  const { data: stats } = useQuery({
    queryKey: ['content-review-stats', accessToken],
    queryFn: async () => {
      const client = createClient(accessToken!);
      const { data } = await client.get('/admin/content/review-queue/stats');
      return data as QueueStats;
    },
    enabled: !!accessToken,
  });

  const reviewMutation = useMutation({
    mutationFn: async ({ id, action, notes }: { id: string; action: string; notes: string }) => {
      const client = createClient(accessToken!);
      await client.patch(`/admin/content/review-queue/${id}`, { action, reviewer_notes: notes });
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['content-review'] });
      setReviewDialog(null);
      toast.success('Content reviewed');
    },
    onError: (err: Error) => toast.error(`Review failed: ${err.message}`),
  });

  if (!accessToken || isLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <Loader2 className="h-6 w-6 animate-spin" />
      </div>
    );
  }

  return (
    <div className="p-6 space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold flex items-center gap-2">
            <FileCheck className="h-6 w-6" />
            Content Review
          </h1>
          <p className="text-muted-foreground text-sm mt-1">
            Review, approve, and reject AI-generated content
          </p>
        </div>
        {stats && (
          <div className="flex gap-2">
            <Badge variant="secondary">{stats.pending} pending</Badge>
            <Badge variant="default">{stats.approved} approved</Badge>
            <Badge variant="destructive">{stats.rejected} rejected</Badge>
          </div>
        )}
      </div>

      {/* Stats Cards */}
      {stats && (
        <div className="grid gap-4 md:grid-cols-4">
          <Card>
            <CardContent className="pt-4">
              <p className="text-2xl font-bold">{stats.total}</p>
              <p className="text-sm text-muted-foreground">Total Items</p>
            </CardContent>
          </Card>
          <Card>
            <CardContent className="pt-4">
              <p className="text-2xl font-bold text-yellow-500">{stats.pending}</p>
              <p className="text-sm text-muted-foreground">Pending Review</p>
            </CardContent>
          </Card>
          <Card>
            <CardContent className="pt-4">
              <p className="text-2xl font-bold text-green-500">{stats.approved}</p>
              <p className="text-sm text-muted-foreground">Approved</p>
            </CardContent>
          </Card>
          <Card>
            <CardContent className="pt-4">
              <p className="text-2xl font-bold">
                {stats.avg_quality_score ? `${(stats.avg_quality_score * 10).toFixed(1)}/10` : 'N/A'}
              </p>
              <p className="text-sm text-muted-foreground">Avg Quality Score</p>
            </CardContent>
          </Card>
        </div>
      )}

      {/* Filter */}
      <div className="flex gap-3">
        <Select value={statusFilter} onValueChange={setStatusFilter}>
          <SelectTrigger className="w-[150px]">
            <SelectValue />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="all">All</SelectItem>
            <SelectItem value="pending">Pending</SelectItem>
            <SelectItem value="approved">Approved</SelectItem>
            <SelectItem value="rejected">Rejected</SelectItem>
          </SelectContent>
        </Select>
      </div>

      {/* Queue Table */}
      <Card>
        <CardContent className="p-0">
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Title</TableHead>
                <TableHead className="w-24">Type</TableHead>
                <TableHead className="w-20">Quality</TableHead>
                <TableHead className="w-24">Status</TableHead>
                <TableHead className="w-28">Submitted</TableHead>
                <TableHead className="w-24">Actions</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {queueData?.items?.map((item) => (
                <TableRow key={item.id}>
                  <TableCell className="max-w-[300px] truncate font-medium">{item.title}</TableCell>
                  <TableCell>
                    <Badge variant="outline" className="text-xs">{item.content_type}</Badge>
                  </TableCell>
                  <TableCell>
                    {item.quality_score ? (
                      <span className={`font-mono font-semibold ${
                        item.quality_score >= 0.7 ? 'text-green-500' : item.quality_score >= 0.5 ? 'text-yellow-500' : 'text-red-500'
                      }`}>
                        {(item.quality_score * 10).toFixed(1)}
                      </span>
                    ) : '-'}
                  </TableCell>
                  <TableCell>
                    <Badge variant={
                      item.status === 'approved' ? 'default'
                      : item.status === 'rejected' ? 'destructive'
                      : 'secondary'
                    }>
                      {item.status}
                    </Badge>
                  </TableCell>
                  <TableCell className="text-xs text-muted-foreground">
                    {formatDateTimeMYT(item.submitted_at)}
                  </TableCell>
                  <TableCell>
                    <div className="flex gap-1">
                      <Button
                        variant="ghost"
                        size="icon"
                        className="h-7 w-7 text-green-500"
                        onClick={() => { setReviewDialog(item); setReviewAction('approve'); setReviewNotes(''); }}
                      >
                        <CheckCircle2 className="h-3 w-3" />
                      </Button>
                      <Button
                        variant="ghost"
                        size="icon"
                        className="h-7 w-7 text-red-500"
                        onClick={() => { setReviewDialog(item); setReviewAction('reject'); setReviewNotes(''); }}
                      >
                        <XCircle className="h-3 w-3" />
                      </Button>
                    </div>
                  </TableCell>
                </TableRow>
              ))}
              {(!queueData?.items || queueData.items.length === 0) && (
                <TableRow>
                  <TableCell colSpan={6} className="text-center py-12 text-muted-foreground">
                    No items in review queue.
                  </TableCell>
                </TableRow>
              )}
            </TableBody>
          </Table>
        </CardContent>
      </Card>

      {/* Review Dialog */}
      <Dialog open={!!reviewDialog} onOpenChange={(open) => !open && setReviewDialog(null)}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>{reviewAction === 'approve' ? 'Approve' : 'Reject'} Content</DialogTitle>
            <DialogDescription>
              {reviewDialog?.title}
            </DialogDescription>
          </DialogHeader>
          <div className="space-y-3">
            <div className="space-y-2">
              <Label>Reviewer Notes</Label>
              <Textarea
                value={reviewNotes}
                onChange={(e) => setReviewNotes(e.target.value)}
                placeholder="Optional notes about this review decision..."
                rows={3}
              />
            </div>
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setReviewDialog(null)}>Cancel</Button>
            <Button
              variant={reviewAction === 'approve' ? 'default' : 'destructive'}
              onClick={() => reviewDialog && reviewMutation.mutate({
                id: reviewDialog.id,
                action: reviewAction,
                notes: reviewNotes,
              })}
              disabled={reviewMutation.isPending}
            >
              {reviewMutation.isPending && <Loader2 className="h-4 w-4 mr-2 animate-spin" />}
              {reviewAction === 'approve' ? 'Approve' : 'Reject'}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}
