'use client';

import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import {
  Loader2, Plug, Plus, Trash2, Bell, Hash, ExternalLink,
} from 'lucide-react';
import { getSupabaseClient } from '@/lib/supabase/client';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import {
  Table, TableBody, TableCell, TableHead, TableHeader, TableRow,
} from '@/components/ui/table';
import {
  Select, SelectContent, SelectItem, SelectTrigger, SelectValue,
} from '@/components/ui/select';
import {
  Dialog, DialogContent, DialogFooter, DialogHeader, DialogTitle,
} from '@/components/ui/dialog';
import { Switch } from '@/components/ui/switch';
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

interface Integration {
  id: string;
  user_id: string;
  service_type: string;
  service_name: string;
  is_active: boolean;
  config: Record<string, unknown> | null;
  created_at: string;
}

interface BotSubscription {
  id: string;
  integration_id: string;
  channel_id: string;
  channel_name: string | null;
  subscription_type: string;
  keywords: string[] | null;
  min_score: number | null;
  is_active: boolean;
  last_notified_at: string | null;
}

export default function IntegrationsPage() {
  const router = useRouter();
  const queryClient = useQueryClient();
  const [accessToken, setAccessToken] = useState<string | null>(null);
  const [createDialog, setCreateDialog] = useState(false);
  const [createForm, setCreateForm] = useState({
    service_type: 'slack',
    service_name: '',
    webhook_url: '',
  });

  useEffect(() => {
    const supabase = getSupabaseClient();
    supabase.auth.getSession().then(({ data }: { data: { session: { access_token: string } | null } }) => {
      if (data.session?.access_token) setAccessToken(data.session.access_token);
      else router.push('/auth/login?redirectTo=/admin/integrations');
    });
  }, [router]);

  const { data: integrations, isLoading } = useQuery({
    queryKey: ['admin-integrations', accessToken],
    queryFn: async () => {
      const client = createClient(accessToken!);
      const { data } = await client.get('/integrations');
      return data as Integration[];
    },
    enabled: !!accessToken,
  });

  const createMutation = useMutation({
    mutationFn: async (payload: typeof createForm) => {
      const client = createClient(accessToken!);
      await client.post('/integrations', {
        service_type: payload.service_type,
        service_name: payload.service_name || `${payload.service_type} Integration`,
        config: { webhook_url: payload.webhook_url },
      });
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['admin-integrations'] });
      setCreateDialog(false);
      setCreateForm({ service_type: 'slack', service_name: '', webhook_url: '' });
      toast.success('Integration created');
    },
    onError: (err: Error) => toast.error(`Failed: ${err.message}`),
  });

  const deleteMutation = useMutation({
    mutationFn: async (id: string) => {
      const client = createClient(accessToken!);
      await client.delete(`/integrations/${id}`);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['admin-integrations'] });
      toast.success('Integration deleted');
    },
    onError: (err: Error) => toast.error(`Delete failed: ${err.message}`),
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
            <Plug className="h-6 w-6" />
            Integrations
          </h1>
          <p className="text-muted-foreground text-sm mt-1">
            Manage Slack, Discord webhooks and notification subscriptions
          </p>
        </div>
        <Button onClick={() => setCreateDialog(true)}>
          <Plus className="h-4 w-4 mr-2" />
          Add Integration
        </Button>
      </div>

      {/* Integrations List */}
      <div className="grid gap-4 md:grid-cols-2">
        {integrations?.map((integration) => (
          <Card key={integration.id}>
            <CardHeader className="pb-2">
              <div className="flex items-center justify-between">
                <CardTitle className="text-base flex items-center gap-2">
                  {integration.service_type === 'slack' ? (
                    <Hash className="h-4 w-4 text-purple-500" />
                  ) : (
                    <Bell className="h-4 w-4 text-blue-500" />
                  )}
                  {integration.service_name}
                </CardTitle>
                <div className="flex items-center gap-2">
                  <Badge variant={integration.is_active ? 'default' : 'secondary'}>
                    {integration.is_active ? 'Active' : 'Inactive'}
                  </Badge>
                  <Button
                    variant="ghost"
                    size="icon"
                    className="h-7 w-7 text-destructive"
                    onClick={() => deleteMutation.mutate(integration.id)}
                  >
                    <Trash2 className="h-3 w-3" />
                  </Button>
                </div>
              </div>
              <CardDescription>{integration.service_type}</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="text-sm space-y-1">
                <p className="text-muted-foreground">
                  Webhook: <span className="font-mono text-xs">
                    {(integration.config?.webhook_url as string)?.slice(0, 40) || 'Not configured'}...
                  </span>
                </p>
                <p className="text-muted-foreground">
                  Created: {formatDateTimeMYT(integration.created_at)}
                </p>
              </div>
            </CardContent>
          </Card>
        ))}
        {(!integrations || integrations.length === 0) && (
          <Card className="col-span-full">
            <CardContent className="p-12 text-center">
              <Plug className="h-12 w-12 mx-auto mb-3 text-muted-foreground opacity-50" />
              <p className="text-muted-foreground">No integrations configured. Add a Slack or Discord webhook to get started.</p>
            </CardContent>
          </Card>
        )}
      </div>

      {/* Create Dialog */}
      <Dialog open={createDialog} onOpenChange={setCreateDialog}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Add Integration</DialogTitle>
          </DialogHeader>
          <div className="space-y-4">
            <div className="space-y-2">
              <Label>Service Type</Label>
              <Select value={createForm.service_type} onValueChange={(v) => setCreateForm({ ...createForm, service_type: v })}>
                <SelectTrigger><SelectValue /></SelectTrigger>
                <SelectContent>
                  <SelectItem value="slack">Slack</SelectItem>
                  <SelectItem value="discord">Discord</SelectItem>
                </SelectContent>
              </Select>
            </div>
            <div className="space-y-2">
              <Label>Name</Label>
              <Input
                value={createForm.service_name}
                onChange={(e) => setCreateForm({ ...createForm, service_name: e.target.value })}
                placeholder="e.g., #startup-alerts"
              />
            </div>
            <div className="space-y-2">
              <Label>Webhook URL</Label>
              <Input
                value={createForm.webhook_url}
                onChange={(e) => setCreateForm({ ...createForm, webhook_url: e.target.value })}
                placeholder="https://hooks.slack.com/services/..."
                className="font-mono text-sm"
              />
            </div>
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setCreateDialog(false)}>Cancel</Button>
            <Button
              onClick={() => createMutation.mutate(createForm)}
              disabled={createMutation.isPending || !createForm.webhook_url}
            >
              {createMutation.isPending && <Loader2 className="h-4 w-4 mr-2 animate-spin" />}
              Create
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}
