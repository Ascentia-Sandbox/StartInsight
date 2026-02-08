'use client';

import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { Loader2, Check, Building2, Palette, Globe, AlertTriangle, Copy, ExternalLink } from 'lucide-react';
import { getSupabaseClient } from '@/lib/supabase/client';
import {
  fetchCurrentTenant,
  createTenant,
  fetchTenantBranding,
  updateTenantBranding,
  configureTenantDomain,
  verifyTenantDomain,
  removeTenantDomain,
  fetchSubscriptionStatus,
} from '@/lib/api';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Badge } from '@/components/ui/badge';
import { Separator } from '@/components/ui/separator';

export default function TenantSettingsPage() {
  const router = useRouter();
  const queryClient = useQueryClient();
  const [accessToken, setAccessToken] = useState<string | null>(null);
  const [isCheckingAuth, setIsCheckingAuth] = useState(true);

  // Form states
  const [tenantName, setTenantName] = useState('');
  const [subdomain, setSubdomain] = useState('');
  const [appName, setAppName] = useState('');
  const [tagline, setTagline] = useState('');
  const [logoUrl, setLogoUrl] = useState('');
  const [faviconUrl, setFaviconUrl] = useState('');
  const [primaryColor, setPrimaryColor] = useState('#3B82F6');
  const [secondaryColor, setSecondaryColor] = useState('#10B981');
  const [accentColor, setAccentColor] = useState('#F59E0B');
  const [customDomain, setCustomDomain] = useState('');

  // UI states
  const [saveSuccess, setSaveSuccess] = useState(false);
  const [domainVerifying, setDomainVerifying] = useState(false);
  const [copiedDns, setCopiedDns] = useState(false);

  // Check authentication
  useEffect(() => {
    const checkAuth = async () => {
      const supabase = getSupabaseClient();
      const { data: { session } } = await supabase.auth.getSession();

      if (!session) {
        router.push('/auth/login?redirectTo=/tenant-settings');
        return;
      }

      setAccessToken(session.access_token);
      setIsCheckingAuth(false);
    };

    checkAuth();
  }, [router]);

  // Fetch subscription to check if user has enterprise tier
  const { data: subscription } = useQuery({
    queryKey: ['subscription', accessToken],
    queryFn: () => fetchSubscriptionStatus(accessToken!),
    enabled: !!accessToken,
  });

  // Fetch current tenant
  const { data: tenant, isLoading: tenantLoading } = useQuery({
    queryKey: ['current-tenant', accessToken],
    queryFn: () => fetchCurrentTenant(accessToken!),
    enabled: !!accessToken,
  });

  // Fetch tenant branding if tenant exists
  const { data: branding } = useQuery({
    queryKey: ['tenant-branding', accessToken, tenant?.id],
    queryFn: () => fetchTenantBranding(accessToken!, tenant!.id),
    enabled: !!accessToken && !!tenant,
  });

  // Update form when branding loads
  useEffect(() => {
    if (tenant) {
      setTenantName(tenant.name || '');
      setSubdomain(tenant.subdomain || '');
      setCustomDomain(tenant.custom_domain || '');
    }
    if (branding) {
      setAppName(branding.app_name || '');
      setTagline(branding.tagline || '');
      setLogoUrl(branding.logo_url || '');
      setFaviconUrl(branding.favicon_url || '');
      setPrimaryColor(branding.primary_color || '#3B82F6');
      setSecondaryColor(branding.secondary_color || '#10B981');
      setAccentColor(branding.accent_color || '#F59E0B');
    }
  }, [tenant, branding]);

  // Create tenant mutation
  const createMutation = useMutation({
    mutationFn: (data: { name: string; subdomain?: string }) =>
      createTenant(accessToken!, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['current-tenant'] });
      setSaveSuccess(true);
      setTimeout(() => setSaveSuccess(false), 3000);
    },
  });

  // Update branding mutation
  const brandingMutation = useMutation({
    mutationFn: (data: {
      logo_url?: string;
      favicon_url?: string;
      primary_color?: string;
      secondary_color?: string;
      accent_color?: string;
      app_name?: string;
      tagline?: string;
    }) => updateTenantBranding(accessToken!, tenant!.id, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['tenant-branding'] });
      setSaveSuccess(true);
      setTimeout(() => setSaveSuccess(false), 3000);
    },
  });

  // Configure domain mutation
  const domainMutation = useMutation({
    mutationFn: (domain: string) =>
      configureTenantDomain(accessToken!, tenant!.id, domain),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['current-tenant'] });
      setSaveSuccess(true);
      setTimeout(() => setSaveSuccess(false), 3000);
    },
  });

  // Verify domain mutation
  const verifyMutation = useMutation({
    mutationFn: () => verifyTenantDomain(accessToken!, tenant!.id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['current-tenant'] });
      setDomainVerifying(false);
    },
    onError: () => {
      setDomainVerifying(false);
    },
  });

  // Remove domain mutation
  const removeDomainMutation = useMutation({
    mutationFn: () => removeTenantDomain(accessToken!, tenant!.id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['current-tenant'] });
      setCustomDomain('');
    },
  });

  // Handlers
  const handleCreateTenant = () => {
    if (!tenantName.trim()) return;
    createMutation.mutate({
      name: tenantName,
      subdomain: subdomain || undefined,
    });
  };

  const handleSaveBranding = () => {
    brandingMutation.mutate({
      app_name: appName || undefined,
      tagline: tagline || undefined,
      logo_url: logoUrl || undefined,
      favicon_url: faviconUrl || undefined,
      primary_color: primaryColor,
      secondary_color: secondaryColor,
      accent_color: accentColor,
    });
  };

  const handleConfigureDomain = () => {
    if (!customDomain.trim()) return;
    domainMutation.mutate(customDomain);
  };

  const handleVerifyDomain = () => {
    setDomainVerifying(true);
    verifyMutation.mutate();
  };

  const copyDnsRecord = (text: string) => {
    navigator.clipboard.writeText(text);
    setCopiedDns(true);
    setTimeout(() => setCopiedDns(false), 2000);
  };

  // Check if user can access tenant features (enterprise tier)
  const canAccessTenant = subscription?.tier === 'enterprise' || subscription?.tier === 'pro';

  if (isCheckingAuth || tenantLoading) {
    return (
      <div className="min-h-screen bg-background flex items-center justify-center">
        <div className="text-center">
          <Loader2 className="animate-spin h-8 w-8 text-primary mx-auto" />
          <p className="mt-2 text-muted-foreground">Loading tenant settings...</p>
        </div>
      </div>
    );
  }

  // Show upgrade prompt for non-enterprise users
  if (!canAccessTenant) {
    return (
      <div className="min-h-screen bg-background">
        <div className="max-w-3xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
          <Card>
            <CardHeader>
              <div className="flex items-center gap-2">
                <Building2 className="h-6 w-6 text-muted-foreground" />
                <CardTitle>White-Label Settings</CardTitle>
              </div>
              <CardDescription>
                Create your own branded version of StartInsight
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="p-6 bg-gradient-to-r from-primary/10 to-secondary/10 rounded-lg text-center">
                <Building2 className="h-12 w-12 text-primary mx-auto mb-4" />
                <h3 className="text-xl font-semibold mb-2">Enterprise Feature</h3>
                <p className="text-muted-foreground mb-4">
                  White-label and custom domain features are available on Pro and Enterprise plans.
                  Upgrade to create your own branded startup insights platform.
                </p>
                <Button onClick={() => router.push('/billing')}>
                  Upgrade to Pro
                </Button>
              </div>
            </CardContent>
          </Card>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-background">
      <div className="max-w-3xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Header */}
        <div className="mb-8">
          <h1 className="text-3xl font-bold tracking-tight">White-Label Settings</h1>
          <p className="text-muted-foreground mt-2">
            Customize your branded StartInsight instance
          </p>
        </div>

        {/* Success Message */}
        {saveSuccess && (
          <div className="mb-6 p-4 bg-green-50 dark:bg-green-900/20 border border-green-200 dark:border-green-800 rounded-lg flex items-center gap-2 text-green-800 dark:text-green-200">
            <Check className="h-5 w-5" />
            Settings saved successfully
          </div>
        )}

        {/* Create Tenant Section (if no tenant exists) */}
        {!tenant && (
          <Card className="mb-6">
            <CardHeader>
              <div className="flex items-center gap-2">
                <Building2 className="h-5 w-5 text-muted-foreground" />
                <CardTitle>Create Your Tenant</CardTitle>
              </div>
              <CardDescription>
                Set up your white-label instance with a custom subdomain
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="space-y-2">
                <label htmlFor="tenant-name" className="text-sm font-medium">
                  Organization Name
                </label>
                <Input
                  id="tenant-name"
                  type="text"
                  value={tenantName}
                  onChange={(e) => setTenantName(e.target.value)}
                  placeholder="Acme Ventures"
                />
              </div>
              <div className="space-y-2">
                <label htmlFor="subdomain" className="text-sm font-medium">
                  Subdomain
                </label>
                <div className="flex items-center gap-2">
                  <Input
                    id="subdomain"
                    type="text"
                    value={subdomain}
                    onChange={(e) => setSubdomain(e.target.value.toLowerCase().replace(/[^a-z0-9-]/g, ''))}
                    placeholder="acme"
                    className="max-w-[200px]"
                  />
                  <span className="text-muted-foreground">.startinsight.ai</span>
                </div>
                <p className="text-xs text-muted-foreground">
                  Lowercase letters, numbers, and hyphens only
                </p>
              </div>
              <Button onClick={handleCreateTenant} disabled={createMutation.isPending || !tenantName.trim()}>
                {createMutation.isPending && <Loader2 className="animate-spin h-4 w-4 mr-2" />}
                Create Tenant
              </Button>
            </CardContent>
          </Card>
        )}

        {/* Branding Section */}
        {tenant && (
          <>
            <Card className="mb-6">
              <CardHeader>
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <Palette className="h-5 w-5 text-muted-foreground" />
                    <CardTitle>Branding</CardTitle>
                  </div>
                  <Badge variant="outline">{tenant.subdomain}.startinsight.ai</Badge>
                </div>
                <CardDescription>
                  Customize the look and feel of your instance
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-6">
                {/* App Name & Tagline */}
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div className="space-y-2">
                    <label htmlFor="app-name" className="text-sm font-medium">
                      App Name
                    </label>
                    <Input
                      id="app-name"
                      type="text"
                      value={appName}
                      onChange={(e) => setAppName(e.target.value)}
                      placeholder="Acme Insights"
                    />
                  </div>
                  <div className="space-y-2">
                    <label htmlFor="tagline" className="text-sm font-medium">
                      Tagline
                    </label>
                    <Input
                      id="tagline"
                      type="text"
                      value={tagline}
                      onChange={(e) => setTagline(e.target.value)}
                      placeholder="Discover your next venture"
                    />
                  </div>
                </div>

                <Separator />

                {/* Logo & Favicon */}
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div className="space-y-2">
                    <label htmlFor="logo-url" className="text-sm font-medium">
                      Logo URL
                    </label>
                    <Input
                      id="logo-url"
                      type="url"
                      value={logoUrl}
                      onChange={(e) => setLogoUrl(e.target.value)}
                      placeholder="https://example.com/logo.png"
                    />
                    {logoUrl && (
                      <div className="mt-2 p-2 bg-muted rounded">
                        <img src={logoUrl} alt="Logo preview" className="h-8 object-contain" />
                      </div>
                    )}
                  </div>
                  <div className="space-y-2">
                    <label htmlFor="favicon-url" className="text-sm font-medium">
                      Favicon URL
                    </label>
                    <Input
                      id="favicon-url"
                      type="url"
                      value={faviconUrl}
                      onChange={(e) => setFaviconUrl(e.target.value)}
                      placeholder="https://example.com/favicon.ico"
                    />
                  </div>
                </div>

                <Separator />

                {/* Colors */}
                <div className="space-y-3">
                  <h4 className="text-sm font-medium">Brand Colors</h4>
                  <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                    <div className="space-y-2">
                      <label htmlFor="primary-color" className="text-xs text-muted-foreground">
                        Primary Color
                      </label>
                      <div className="flex items-center gap-2">
                        <input
                          type="color"
                          id="primary-color"
                          value={primaryColor}
                          onChange={(e) => setPrimaryColor(e.target.value)}
                          className="w-10 h-10 rounded cursor-pointer"
                        />
                        <Input
                          type="text"
                          value={primaryColor}
                          onChange={(e) => setPrimaryColor(e.target.value)}
                          className="font-mono text-sm"
                          maxLength={7}
                        />
                      </div>
                    </div>
                    <div className="space-y-2">
                      <label htmlFor="secondary-color" className="text-xs text-muted-foreground">
                        Secondary Color
                      </label>
                      <div className="flex items-center gap-2">
                        <input
                          type="color"
                          id="secondary-color"
                          value={secondaryColor}
                          onChange={(e) => setSecondaryColor(e.target.value)}
                          className="w-10 h-10 rounded cursor-pointer"
                        />
                        <Input
                          type="text"
                          value={secondaryColor}
                          onChange={(e) => setSecondaryColor(e.target.value)}
                          className="font-mono text-sm"
                          maxLength={7}
                        />
                      </div>
                    </div>
                    <div className="space-y-2">
                      <label htmlFor="accent-color" className="text-xs text-muted-foreground">
                        Accent Color
                      </label>
                      <div className="flex items-center gap-2">
                        <input
                          type="color"
                          id="accent-color"
                          value={accentColor}
                          onChange={(e) => setAccentColor(e.target.value)}
                          className="w-10 h-10 rounded cursor-pointer"
                        />
                        <Input
                          type="text"
                          value={accentColor}
                          onChange={(e) => setAccentColor(e.target.value)}
                          className="font-mono text-sm"
                          maxLength={7}
                        />
                      </div>
                    </div>
                  </div>
                </div>

                {/* Color Preview */}
                <div className="p-4 rounded-lg border space-y-2">
                  <p className="text-xs text-muted-foreground">Preview</p>
                  <div className="flex items-center gap-3">
                    <div
                      className="w-16 h-8 rounded"
                      style={{ backgroundColor: primaryColor }}
                    />
                    <div
                      className="w-16 h-8 rounded"
                      style={{ backgroundColor: secondaryColor }}
                    />
                    <div
                      className="w-16 h-8 rounded"
                      style={{ backgroundColor: accentColor }}
                    />
                    <span className="text-sm font-medium">{appName || 'Your App'}</span>
                  </div>
                </div>

                <Button onClick={handleSaveBranding} disabled={brandingMutation.isPending}>
                  {brandingMutation.isPending && <Loader2 className="animate-spin h-4 w-4 mr-2" />}
                  Save Branding
                </Button>
              </CardContent>
            </Card>

            {/* Custom Domain Section */}
            <Card className="mb-6">
              <CardHeader>
                <div className="flex items-center gap-2">
                  <Globe className="h-5 w-5 text-muted-foreground" />
                  <CardTitle>Custom Domain</CardTitle>
                </div>
                <CardDescription>
                  Use your own domain instead of {tenant.subdomain}.startinsight.ai
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                {tenant.custom_domain ? (
                  <div className="space-y-4">
                    <div className="p-4 bg-muted rounded-lg">
                      <div className="flex items-center justify-between">
                        <div className="flex items-center gap-2">
                          <Globe className="h-4 w-4" />
                          <span className="font-medium">{tenant.custom_domain}</span>
                        </div>
                        {tenant.custom_domain_verified ? (
                          <Badge variant="default" className="bg-green-600">
                            <Check className="h-3 w-3 mr-1" />
                            Verified
                          </Badge>
                        ) : (
                          <Badge variant="secondary">Pending Verification</Badge>
                        )}
                      </div>
                    </div>

                    {!tenant.custom_domain_verified && (
                      <div className="p-4 bg-amber-50 dark:bg-amber-900/20 rounded-lg border border-amber-200 dark:border-amber-800">
                        <div className="flex items-start gap-2">
                          <AlertTriangle className="h-5 w-5 text-amber-600 mt-0.5" />
                          <div className="space-y-2">
                            <p className="font-medium text-amber-800 dark:text-amber-200">
                              DNS Configuration Required
                            </p>
                            <p className="text-sm text-amber-700 dark:text-amber-300">
                              Add the following CNAME record to your DNS settings:
                            </p>
                            <div className="font-mono text-sm bg-background p-3 rounded border flex items-center justify-between">
                              <span>CNAME @ proxy.startinsight.ai</span>
                              <Button
                                variant="ghost"
                                size="sm"
                                onClick={() => copyDnsRecord('proxy.startinsight.ai')}
                              >
                                {copiedDns ? <Check className="h-4 w-4" /> : <Copy className="h-4 w-4" />}
                              </Button>
                            </div>
                            <Button
                              variant="outline"
                              size="sm"
                              onClick={handleVerifyDomain}
                              disabled={domainVerifying}
                            >
                              {domainVerifying && <Loader2 className="animate-spin h-4 w-4 mr-2" />}
                              Verify Domain
                            </Button>
                          </div>
                        </div>
                      </div>
                    )}

                    <div className="flex items-center gap-2">
                      <Button
                        variant="outline"
                        size="sm"
                        onClick={() => window.open(`https://${tenant.custom_domain}`, '_blank')}
                      >
                        <ExternalLink className="h-4 w-4 mr-2" />
                        Visit Domain
                      </Button>
                      <Button
                        variant="ghost"
                        size="sm"
                        className="text-red-600 hover:text-red-700"
                        onClick={() => removeDomainMutation.mutate()}
                        disabled={removeDomainMutation.isPending}
                      >
                        Remove Domain
                      </Button>
                    </div>
                  </div>
                ) : (
                  <div className="space-y-4">
                    <div className="space-y-2">
                      <label htmlFor="custom-domain" className="text-sm font-medium">
                        Domain Name
                      </label>
                      <Input
                        id="custom-domain"
                        type="text"
                        value={customDomain}
                        onChange={(e) => setCustomDomain(e.target.value.toLowerCase())}
                        placeholder="insights.yourcompany.com"
                      />
                      <p className="text-xs text-muted-foreground">
                        Enter the domain you want to use (e.g., insights.acme.com)
                      </p>
                    </div>
                    <Button
                      onClick={handleConfigureDomain}
                      disabled={domainMutation.isPending || !customDomain.trim()}
                    >
                      {domainMutation.isPending && <Loader2 className="animate-spin h-4 w-4 mr-2" />}
                      Configure Domain
                    </Button>
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
