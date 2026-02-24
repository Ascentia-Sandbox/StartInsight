'use client';

import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import Link from 'next/link';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { Loader2, Key, Info, Copy, Check } from 'lucide-react';
import { getSupabaseClient } from '@/lib/supabase/client';
import { fetchAPIKeys, createAPIKey, revokeAPIKey } from '@/lib/api';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { toast } from 'sonner';
import type { APIKey } from '@/lib/types';
import { Breadcrumbs } from '@/components/ui/breadcrumbs';
import { FeatureLock } from '@/components/ui/FeatureLock';
import { useSubscription } from '@/hooks/useSubscription';

export default function ApiKeysPage() {
  const router = useRouter();
  const queryClient = useQueryClient();
  const [accessToken, setAccessToken] = useState<string | null>(null);
  const [isCheckingAuth, setIsCheckingAuth] = useState(true);
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [keyName, setKeyName] = useState('');
  const [newKey, setNewKey] = useState<string | null>(null);
  const [copied, setCopied] = useState(false);

  const { tier } = useSubscription();

  // Check authentication
  useEffect(() => {
    const checkAuth = async () => {
      const supabase = getSupabaseClient();
      const { data: { session } } = await supabase.auth.getSession();

      if (!session) {
        router.push('/auth/login?redirectTo=/api-keys');
        return;
      }

      setAccessToken(session.access_token);
      setIsCheckingAuth(false);
    };

    checkAuth();
  }, [router]);

  // Fetch API keys
  const { data: apiKeysData, isLoading } = useQuery({
    queryKey: ['api-keys', accessToken],
    queryFn: () => fetchAPIKeys(accessToken!),
    enabled: !!accessToken,
  });

  // Create API key mutation
  const createKeyMutation = useMutation({
    mutationFn: (data: { name: string }) =>
      createAPIKey(accessToken!, data),
    onSuccess: (data) => {
      setNewKey(data.key);
      queryClient.invalidateQueries({ queryKey: ['api-keys'] });
      toast.success('API key created successfully');
    },
    onError: () => {
      toast.error('Failed to create API key');
    },
  });

  // Revoke API key mutation
  const revokeKeyMutation = useMutation({
    mutationFn: (keyId: string) =>
      revokeAPIKey(accessToken!, keyId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['api-keys'] });
      toast.success('API key revoked');
    },
    onError: () => {
      toast.error('Failed to revoke API key');
    },
  });

  if (isCheckingAuth) {
    return (
      <div className="min-h-screen bg-background flex items-center justify-center">
        <div className="text-center">
          <Loader2 className="animate-spin h-8 w-8 text-primary mx-auto" />
          <p className="mt-2 text-muted-foreground">Loading API keys...</p>
        </div>
      </div>
    );
  }

  const apiKeys = apiKeysData?.keys || [];

  const copyToClipboard = (text: string) => {
    navigator.clipboard.writeText(text);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const handleCreateKey = async (e: React.FormEvent) => {
    e.preventDefault();
    createKeyMutation.mutate({ name: keyName });
  };

  const handleCloseModal = () => {
    setShowCreateModal(false);
    setNewKey(null);
    setKeyName('');
  };

  return (
    <div className="min-h-screen bg-background">
      <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <Breadcrumbs items={[{ label: 'API Keys' }]} />
        {/* Header */}
        <div className="flex justify-between items-center mb-8">
          <div>
            <h1 className="text-3xl font-bold tracking-tight">API Keys</h1>
            <p className="text-muted-foreground mt-2">
              Manage your API keys for programmatic access
            </p>
          </div>
          <Button onClick={() => setShowCreateModal(true)}>Create API Key</Button>
        </div>

        <FeatureLock requiredTier="pro" currentTier={tier} featureName="API Keys">

        {/* Info Banner */}
        <Card className="mb-8 bg-blue-50 dark:bg-blue-900/20 border-blue-200 dark:border-blue-800">
          <CardContent className="pt-6">
            <div className="flex gap-4">
              <Info className="h-6 w-6 text-blue-600 dark:text-blue-400 shrink-0" />
              <div>
                <p className="font-medium text-blue-800 dark:text-blue-200">API Documentation</p>
                <p className="text-sm text-blue-700 dark:text-blue-300 mt-1">
                  Learn how to use the StartInsight API to integrate market insights into your
                  applications.{' '}
                  <Link href="/docs/api" className="underline">
                    View API Docs
                  </Link>
                </p>
              </div>
            </div>
          </CardContent>
        </Card>

        {isLoading ? (
          <div className="flex items-center justify-center py-12">
            <Loader2 className="animate-spin h-8 w-8 text-primary" />
          </div>
        ) : apiKeys.length === 0 ? (
          // Empty State
          <Card>
            <CardContent className="p-12">
              <div className="text-center">
                <Key className="h-16 w-16 mx-auto text-muted-foreground mb-4" />
                <h3 className="text-lg font-semibold mb-2">No API keys yet</h3>
                <p className="text-muted-foreground mb-6 max-w-sm mx-auto">
                  Create an API key to access StartInsight data programmatically.
                </p>
                <Button onClick={() => setShowCreateModal(true)}>Create Your First API Key</Button>
              </div>
            </CardContent>
          </Card>
        ) : (
          // API Keys List
          <div className="space-y-4">
            {apiKeys.map((key: APIKey) => (
              <Card key={key.id}>
                <CardHeader className="flex flex-row items-center justify-between space-y-0">
                  <div>
                    <CardTitle className="text-base">{key.name}</CardTitle>
                    <CardDescription className="font-mono">
                      {key.key_prefix}...
                      <span className="ml-2 text-xs">
                        {key.last_used_at ? `Last used ${new Date(key.last_used_at).toLocaleDateString()}` : 'Never used'}
                      </span>
                    </CardDescription>
                  </div>
                  <div className="flex items-center gap-2">
                    <span
                      className={`px-2 py-1 text-xs rounded-full ${
                        key.is_active
                          ? 'bg-green-100 text-green-800 dark:bg-green-900/30 dark:text-green-400'
                          : 'bg-red-100 text-red-800 dark:bg-red-900/30 dark:text-red-400'
                      }`}
                    >
                      {key.is_active ? 'Active' : 'Revoked'}
                    </span>
                    {key.is_active && (
                      <Button
                        variant="outline"
                        size="sm"
                        onClick={() => revokeKeyMutation.mutate(key.id)}
                        disabled={revokeKeyMutation.isPending}
                      >
                        {revokeKeyMutation.isPending ? (
                          <Loader2 className="animate-spin h-4 w-4" />
                        ) : (
                          'Revoke'
                        )}
                      </Button>
                    )}
                  </div>
                </CardHeader>
              </Card>
            ))}
          </div>
        )}

        {/* Usage Limits */}
        <Card className="mt-8">
          <CardHeader>
            <CardTitle>API Usage</CardTitle>
            <CardDescription>Your current plan limits</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              <div>
                <div className="flex justify-between text-sm mb-1">
                  <span>API Calls (This Month)</span>
                  <span>0 / 1,000</span>
                </div>
                <div className="w-full bg-muted rounded-full h-2">
                  <div className="bg-primary h-2 rounded-full" style={{ width: '0%' }}></div>
                </div>
              </div>
              <p className="text-sm text-muted-foreground">
                Need more API calls?{' '}
                <Link href="/billing" className="text-primary hover:underline">
                  Upgrade your plan
                </Link>
              </p>
            </div>
          </CardContent>
        </Card>

        </FeatureLock>

        {/* Create Key Modal */}
        {showCreateModal && (
          <div className="fixed inset-0 z-50 flex items-center justify-center">
            <div
              className="absolute inset-0 bg-black/50"
              onClick={handleCloseModal}
            />
            <Card className="relative z-10 w-full max-w-md">
              <CardHeader>
                <CardTitle>{newKey ? 'API Key Created' : 'Create API Key'}</CardTitle>
                <CardDescription>
                  {newKey
                    ? 'Make sure to copy your API key now. You will not be able to see it again!'
                    : 'Give your API key a name to identify it'}
                </CardDescription>
              </CardHeader>
              <CardContent>
                {newKey ? (
                  <div className="space-y-4">
                    <div className="p-3 bg-muted rounded-md font-mono text-sm break-all">
                      {newKey}
                    </div>
                    <div className="flex gap-2">
                      <Button
                        className="flex-1"
                        onClick={() => copyToClipboard(newKey)}
                      >
                        {copied ? (
                          <>
                            <Check className="h-4 w-4 mr-2" />
                            Copied!
                          </>
                        ) : (
                          <>
                            <Copy className="h-4 w-4 mr-2" />
                            Copy to Clipboard
                          </>
                        )}
                      </Button>
                      <Button variant="outline" onClick={handleCloseModal}>
                        Done
                      </Button>
                    </div>
                  </div>
                ) : (
                  <form onSubmit={handleCreateKey} className="space-y-4">
                    <div className="space-y-2">
                      <label htmlFor="keyName" className="text-sm font-medium">
                        Key Name
                      </label>
                      <Input
                        id="keyName"
                        value={keyName}
                        onChange={(e) => setKeyName(e.target.value)}
                        placeholder="e.g., Production API Key"
                        required
                      />
                    </div>
                    <div className="flex gap-2 justify-end">
                      <Button
                        type="button"
                        variant="outline"
                        onClick={handleCloseModal}
                      >
                        Cancel
                      </Button>
                      <Button type="submit" disabled={createKeyMutation.isPending}>
                        {createKeyMutation.isPending && (
                          <Loader2 className="animate-spin h-4 w-4 mr-2" />
                        )}
                        Create Key
                      </Button>
                    </div>
                  </form>
                )}
              </CardContent>
            </Card>
          </div>
        )}
      </div>
    </div>
  );
}
