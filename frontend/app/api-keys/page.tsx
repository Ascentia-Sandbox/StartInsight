'use client';

import { useState } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';

interface ApiKey {
  id: string;
  name: string;
  prefix: string;
  createdAt: string;
  lastUsed: string | null;
  isActive: boolean;
}

export default function ApiKeysPage() {
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [keyName, setKeyName] = useState('');
  const [newKey, setNewKey] = useState<string | null>(null);

  // Mock data - would come from API
  const apiKeys: ApiKey[] = [];

  const copyToClipboard = (text: string) => {
    navigator.clipboard.writeText(text);
  };

  return (
    <div className="min-h-screen bg-background">
      <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
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

        {/* Info Banner */}
        <Card className="mb-8 bg-blue-50 dark:bg-blue-900/20 border-blue-200 dark:border-blue-800">
          <CardContent className="pt-6">
            <div className="flex gap-4">
              <svg
                xmlns="http://www.w3.org/2000/svg"
                className="h-6 w-6 text-blue-600 dark:text-blue-400 shrink-0"
                fill="none"
                viewBox="0 0 24 24"
                stroke="currentColor"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"
                />
              </svg>
              <div>
                <p className="font-medium text-blue-800 dark:text-blue-200">API Documentation</p>
                <p className="text-sm text-blue-700 dark:text-blue-300 mt-1">
                  Learn how to use the StartInsight API to integrate market insights into your
                  applications.{' '}
                  <a href="/docs/api" className="underline">
                    View API Docs
                  </a>
                </p>
              </div>
            </div>
          </CardContent>
        </Card>

        {apiKeys.length === 0 ? (
          // Empty State
          <Card>
            <CardContent className="p-12">
              <div className="text-center">
                <svg
                  xmlns="http://www.w3.org/2000/svg"
                  className="h-16 w-16 mx-auto text-muted-foreground mb-4"
                  fill="none"
                  viewBox="0 0 24 24"
                  stroke="currentColor"
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={1.5}
                    d="M15 7a2 2 0 012 2m4 0a6 6 0 01-7.743 5.743L11 17H9v2H7v2H4a1 1 0 01-1-1v-2.586a1 1 0 01.293-.707l5.964-5.964A6 6 0 1121 9z"
                  />
                </svg>
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
            {apiKeys.map((key) => (
              <Card key={key.id}>
                <CardHeader className="flex flex-row items-center justify-between space-y-0">
                  <div>
                    <CardTitle className="text-base">{key.name}</CardTitle>
                    <CardDescription className="font-mono">
                      {key.prefix}...
                      <span className="ml-2 text-xs">
                        {key.lastUsed ? `Last used ${key.lastUsed}` : 'Never used'}
                      </span>
                    </CardDescription>
                  </div>
                  <div className="flex items-center gap-2">
                    <span
                      className={`px-2 py-1 text-xs rounded-full ${
                        key.isActive
                          ? 'bg-green-100 text-green-800 dark:bg-green-900/30 dark:text-green-400'
                          : 'bg-red-100 text-red-800 dark:bg-red-900/30 dark:text-red-400'
                      }`}
                    >
                      {key.isActive ? 'Active' : 'Revoked'}
                    </span>
                    <Button variant="outline" size="sm">
                      Revoke
                    </Button>
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
                <a href="/billing" className="text-primary hover:underline">
                  Upgrade your plan
                </a>
              </p>
            </div>
          </CardContent>
        </Card>

        {/* Create Key Modal */}
        {showCreateModal && (
          <div className="fixed inset-0 z-50 flex items-center justify-center">
            <div
              className="absolute inset-0 bg-black/50"
              onClick={() => {
                setShowCreateModal(false);
                setNewKey(null);
              }}
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
                        Copy to Clipboard
                      </Button>
                      <Button
                        variant="outline"
                        onClick={() => {
                          setShowCreateModal(false);
                          setNewKey(null);
                        }}
                      >
                        Done
                      </Button>
                    </div>
                  </div>
                ) : (
                  <form
                    onSubmit={(e) => {
                      e.preventDefault();
                      // Mock key generation
                      setNewKey('si_live_' + Math.random().toString(36).substring(2, 15));
                    }}
                    className="space-y-4"
                  >
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
                        onClick={() => setShowCreateModal(false)}
                      >
                        Cancel
                      </Button>
                      <Button type="submit">Create Key</Button>
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
