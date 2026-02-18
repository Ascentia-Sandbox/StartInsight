'use client';

import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { Loader2, AlertTriangle, CheckCircle, XCircle, Clock, ExternalLink } from 'lucide-react';
import { formatDistanceToNow } from 'date-fns';
import { getSupabaseClient } from '@/lib/supabase/client';
import { fetchAdminResearchRequests, updateResearchRequest } from '@/lib/api';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Separator } from '@/components/ui/separator';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog';
import type { ResearchRequestSummary } from '@/lib/types';
import { Breadcrumbs } from '@/components/ui/breadcrumbs';

export default function AdminResearchQueue() {
  const [isMounted, setIsMounted] = useState(false);

  useEffect(() => {
    setIsMounted(true);
  }, []);

  // Show loading spinner until client-side mount
  if (!isMounted) {
    return (
      <div className="min-h-screen bg-background flex items-center justify-center">
        <div className="text-center">
          <Loader2 className="animate-spin h-8 w-8 text-primary mx-auto" />
          <p className="mt-2 text-muted-foreground">Loading research queue...</p>
        </div>
      </div>
    );
  }

  return <ResearchQueueContent />;
}

function ResearchQueueContent() {
  const router = useRouter();
  const queryClient = useQueryClient();
  const [accessToken, setAccessToken] = useState<string | null>(null);
  const [isCheckingAuth, setIsCheckingAuth] = useState(true);
  const [selectedStatus, setSelectedStatus] = useState<'pending' | 'approved' | 'rejected' | 'completed' | undefined>('pending');
  const [reviewDialog, setReviewDialog] = useState<{
    open: boolean;
    request: ResearchRequestSummary | null;
    action: 'approve' | 'reject' | null;
  }>({ open: false, request: null, action: null });

  // Check authentication
  useEffect(() => {
    const checkAuth = async () => {
      const supabase = getSupabaseClient();
      const { data: { session } } = await supabase.auth.getSession();

      if (!session) {
        router.push('/auth/login?redirectTo=/admin/research-queue');
        return;
      }

      setAccessToken(session.access_token);
      setIsCheckingAuth(false);
    };

    checkAuth();
  }, [router]);

  // Fetch research requests
  const { data: requestsData, isLoading, error } = useQuery({
    queryKey: ['admin-research-requests', accessToken, selectedStatus],
    queryFn: () => fetchAdminResearchRequests(accessToken!, { status: selectedStatus, limit: 50 }),
    enabled: !!accessToken,
    refetchInterval: 10000, // Refresh every 10 seconds
  });

  // Update request mutation
  const updateMutation = useMutation({
    mutationFn: ({ requestId, action, notes }: { requestId: string; action: 'approve' | 'reject'; notes?: string }) =>
      updateResearchRequest(accessToken!, requestId, { action, notes }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['admin-research-requests'] });
      setReviewDialog({ open: false, request: null, action: null });
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
  if (error) {
    return (
      <div className="min-h-screen bg-background flex items-center justify-center">
        <Card className="max-w-md">
          <CardContent className="p-8 text-center">
            <AlertTriangle className="h-12 w-12 text-yellow-500 mx-auto mb-4" />
            <h2 className="text-xl font-semibold mb-2">Access Denied</h2>
            <p className="text-muted-foreground mb-4">
              You do not have admin access. Please contact support if you believe this is an error.
            </p>
            <Button onClick={() => router.push('/dashboard')}>
              Back to Dashboard
            </Button>
          </CardContent>
        </Card>
      </div>
    );
  }

  const requests = requestsData?.items || [];
  const pendingCount = requests.filter(r => r.status === 'pending').length;

  const statusConfig = {
    pending: { color: 'bg-yellow-100 text-yellow-800 dark:bg-yellow-900 dark:text-yellow-300', icon: Clock },
    approved: { color: 'bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-300', icon: CheckCircle },
    rejected: { color: 'bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-300', icon: XCircle },
    completed: { color: 'bg-blue-100 text-blue-800 dark:bg-blue-900 dark:text-blue-300', icon: CheckCircle },
  };

  return (
    <div className="min-h-screen bg-background p-6">
      <div className="max-w-7xl mx-auto space-y-6">
        <Breadcrumbs items={[
          { label: 'Admin', href: '/admin' },
          { label: 'Research Queue' },
        ]} />
        {/* Header */}
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-3xl font-bold">Research Request Queue</h1>
            <p className="text-muted-foreground mt-1">
              Review and approve user-submitted research requests
            </p>
          </div>
          <div className="flex items-center gap-2">
            <Badge variant="default" className="text-base px-3 py-1">
              {pendingCount} Pending
            </Badge>
            <Button variant="outline" onClick={() => router.push('/admin')}>
              Back to Admin
            </Button>
          </div>
        </div>

        {/* Status Filter */}
        <Card>
          <CardHeader className="pb-3">
            <CardTitle className="text-sm font-medium">Filter by Status</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="flex gap-2">
              <Button
                variant={selectedStatus === 'pending' ? 'default' : 'outline'}
                size="sm"
                onClick={() => setSelectedStatus('pending')}
              >
                Pending
              </Button>
              <Button
                variant={selectedStatus === 'approved' ? 'default' : 'outline'}
                size="sm"
                onClick={() => setSelectedStatus('approved')}
              >
                Approved
              </Button>
              <Button
                variant={selectedStatus === 'rejected' ? 'default' : 'outline'}
                size="sm"
                onClick={() => setSelectedStatus('rejected')}
              >
                Rejected
              </Button>
              <Button
                variant={selectedStatus === 'completed' ? 'default' : 'outline'}
                size="sm"
                onClick={() => setSelectedStatus('completed')}
              >
                Completed
              </Button>
              <Button
                variant={selectedStatus === undefined ? 'default' : 'outline'}
                size="sm"
                onClick={() => setSelectedStatus(undefined)}
              >
                All
              </Button>
            </div>
          </CardContent>
        </Card>

        {/* Research Requests Table */}
        <Card>
          <CardHeader>
            <CardTitle>Research Requests</CardTitle>
            <CardDescription>
              {requestsData?.total || 0} total request{requestsData?.total !== 1 ? 's' : ''}
              {selectedStatus && ` • Showing ${selectedStatus} requests`}
            </CardDescription>
          </CardHeader>
          <CardContent>
            {isLoading ? (
              <div className="flex items-center justify-center py-12">
                <Loader2 className="animate-spin h-8 w-8 text-primary" />
              </div>
            ) : requests.length === 0 ? (
              <div className="text-center py-12 text-muted-foreground">
                No {selectedStatus || ''} requests found
              </div>
            ) : (
              <div className="space-y-4">
                {requests.map((request) => {
                  const StatusIcon = statusConfig[request.status].icon;
                  return (
                    <Card key={request.id} className="border-2">
                      <CardContent className="p-4">
                        <div className="flex items-start justify-between gap-4">
                          <div className="flex-1 space-y-3">
                            {/* Header */}
                            <div className="flex items-center gap-2">
                              <Badge className={statusConfig[request.status].color}>
                                <StatusIcon className="h-3 w-3 mr-1" />
                                {request.status}
                              </Badge>
                              <span className="text-sm text-muted-foreground">
                                {request.user_email || 'Unknown user'}
                              </span>
                              <span className="text-sm text-muted-foreground">•</span>
                              <span className="text-sm text-muted-foreground">
                                {formatDistanceToNow(new Date(request.created_at), { addSuffix: true })}
                              </span>
                            </div>

                            {/* Idea Description */}
                            <div>
                              <h4 className="font-semibold text-base mb-1">Idea Description</h4>
                              <p className="text-sm text-muted-foreground">
                                {request.idea_description}
                              </p>
                            </div>

                            {/* Target Market */}
                            {request.target_market && (
                              <div>
                                <h4 className="font-semibold text-sm">Target Market</h4>
                                <p className="text-sm text-muted-foreground">
                                  {request.target_market}
                                </p>
                              </div>
                            )}

                            {/* Review Timestamp */}
                            {request.reviewed_at && (
                              <div className="text-xs text-muted-foreground">
                                Reviewed {formatDistanceToNow(new Date(request.reviewed_at), { addSuffix: true })}
                              </div>
                            )}
                          </div>

                          {/* Actions */}
                          {request.status === 'pending' && (
                            <div className="flex flex-col gap-2 min-w-[120px]">
                              <Button
                                size="sm"
                                onClick={() => setReviewDialog({
                                  open: true,
                                  request,
                                  action: 'approve',
                                })}
                                disabled={updateMutation.isPending}
                                className="w-full"
                              >
                                <CheckCircle className="h-4 w-4 mr-1" />
                                Approve
                              </Button>
                              <Button
                                size="sm"
                                variant="destructive"
                                onClick={() => setReviewDialog({
                                  open: true,
                                  request,
                                  action: 'reject',
                                })}
                                disabled={updateMutation.isPending}
                                className="w-full"
                              >
                                <XCircle className="h-4 w-4 mr-1" />
                                Reject
                              </Button>
                            </div>
                          )}
                        </div>
                      </CardContent>
                    </Card>
                  );
                })}
              </div>
            )}
          </CardContent>
        </Card>
      </div>

      {/* Review Confirmation Dialog */}
      <Dialog open={reviewDialog.open} onOpenChange={(open) => !open && setReviewDialog({ open: false, request: null, action: null })}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>
              {reviewDialog.action === 'approve' ? 'Approve' : 'Reject'} Research Request
            </DialogTitle>
            <DialogDescription>
              {reviewDialog.action === 'approve'
                ? 'This will trigger a comprehensive 40-step AI research analysis. The analysis will be linked to the user\'s account.'
                : 'The user will be notified that their request was rejected. Consider providing a brief explanation.'}
            </DialogDescription>
          </DialogHeader>

          {reviewDialog.request && (
            <div className="space-y-3 py-4">
              <div>
                <div className="text-sm font-medium mb-1">User</div>
                <div className="text-sm text-muted-foreground">{reviewDialog.request.user_email}</div>
              </div>
              <div>
                <div className="text-sm font-medium mb-1">Idea</div>
                <div className="text-sm text-muted-foreground line-clamp-3">
                  {reviewDialog.request.idea_description}
                </div>
              </div>
              {reviewDialog.request.target_market && (
                <div>
                  <div className="text-sm font-medium mb-1">Target Market</div>
                  <div className="text-sm text-muted-foreground">
                    {reviewDialog.request.target_market}
                  </div>
                </div>
              )}
            </div>
          )}

          <DialogFooter>
            <Button
              variant="outline"
              onClick={() => setReviewDialog({ open: false, request: null, action: null })}
              disabled={updateMutation.isPending}
            >
              Cancel
            </Button>
            <Button
              variant={reviewDialog.action === 'approve' ? 'default' : 'destructive'}
              onClick={() => {
                if (reviewDialog.request && reviewDialog.action) {
                  updateMutation.mutate({
                    requestId: reviewDialog.request.id,
                    action: reviewDialog.action,
                    notes: reviewDialog.action === 'reject'
                      ? 'Request did not meet quality criteria'
                      : undefined,
                  });
                }
              }}
              disabled={updateMutation.isPending}
            >
              {updateMutation.isPending ? (
                <Loader2 className="animate-spin h-4 w-4 mr-2" />
              ) : reviewDialog.action === 'approve' ? (
                <CheckCircle className="h-4 w-4 mr-2" />
              ) : (
                <XCircle className="h-4 w-4 mr-2" />
              )}
              Confirm {reviewDialog.action === 'approve' ? 'Approval' : 'Rejection'}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}
