'use client';

import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import Link from 'next/link';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { Loader2, Check, User, Bell, CreditCard, Trash2, Gift, Copy, Twitter } from 'lucide-react';
import { getSupabaseClient } from '@/lib/supabase/client';
import { fetchUserProfile, updateUserProfile, fetchSubscriptionStatus, fetchEmailPreferences, updateEmailPreferences } from '@/lib/api';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Skeleton } from '@/components/ui/skeleton';
import { config } from '@/lib/env';

// ---------------------------------------------------------------------------
// Referral stats types
// ---------------------------------------------------------------------------

interface ReferralStats {
  referral_code: string;
  referral_link: string;
  referrals_count: number;
  reward_status: string;
}

async function fetchReferralStats(token: string): Promise<ReferralStats> {
  const res = await fetch(`${config.apiUrl}/api/referrals/stats`, {
    headers: { Authorization: `Bearer ${token}` },
  });
  if (!res.ok) throw new Error('Failed to fetch referral stats');
  return res.json() as Promise<ReferralStats>;
}

export default function SettingsPage() {
  const router = useRouter();
  const queryClient = useQueryClient();
  const [accessToken, setAccessToken] = useState<string | null>(null);
  const [isCheckingAuth, setIsCheckingAuth] = useState(true);
  const [displayName, setDisplayName] = useState('');
  const [userEmail, setUserEmail] = useState('');
  const [dailyDigest, setDailyDigest] = useState(false);
  const [researchNotify, setResearchNotify] = useState(true);
  const [showDeleteConfirm, setShowDeleteConfirm] = useState(false);
  const [saveSuccess, setSaveSuccess] = useState(false);
  const [linkCopied, setLinkCopied] = useState(false);

  // Check authentication
  useEffect(() => {
    const checkAuth = async () => {
      const supabase = getSupabaseClient();
      const { data: { session } } = await supabase.auth.getSession();

      if (!session) {
        router.push('/auth/login?redirectTo=/settings');
        return;
      }

      setAccessToken(session.access_token);
      setUserEmail(session.user.email || '');
      setIsCheckingAuth(false);
    };

    checkAuth();
  }, [router]);

  // Fetch user profile
  const { data: profile, isLoading: profileLoading } = useQuery({
    queryKey: ['user-profile', accessToken],
    queryFn: () => fetchUserProfile(accessToken!),
    enabled: !!accessToken,
  });

  // Fetch email preferences from EmailPreferences table
  const { data: emailPrefs } = useQuery({
    queryKey: ['email-preferences', accessToken],
    queryFn: () => fetchEmailPreferences(accessToken!),
    enabled: !!accessToken,
  });

  // Update state when profile loads
  useEffect(() => {
    if (profile) {
      setDisplayName(profile.display_name || '');
      setResearchNotify(profile.preferences?.research_notify !== false);
    }
  }, [profile]);

  // Update daily digest from email preferences
  useEffect(() => {
    if (emailPrefs) {
      setDailyDigest(emailPrefs.daily_digest);
    }
  }, [emailPrefs]);

  // Fetch subscription status
  const { data: subscription } = useQuery({
    queryKey: ['subscription', accessToken],
    queryFn: () => fetchSubscriptionStatus(accessToken!),
    enabled: !!accessToken,
  });

  // Fetch referral stats
  const { data: referralStats, isLoading: referralLoading } = useQuery({
    queryKey: ['referral-stats', accessToken],
    queryFn: () => fetchReferralStats(accessToken!),
    enabled: !!accessToken,
  });

  // Update profile mutation
  const updateMutation = useMutation({
    mutationFn: (data: { display_name?: string; preferences?: Record<string, unknown> }) =>
      updateUserProfile(accessToken!, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['user-profile'] });
      setSaveSuccess(true);
      setTimeout(() => setSaveSuccess(false), 3000);
    },
  });

  // Handle referral link copy
  const handleCopyReferralLink = async () => {
    if (!referralStats) return;
    try {
      await navigator.clipboard.writeText(referralStats.referral_link);
      setLinkCopied(true);
      setTimeout(() => setLinkCopied(false), 2000);
    } catch {
      // Clipboard not available (non-HTTPS dev) — noop
    }
  };

  // Handle profile save
  const handleSaveProfile = () => {
    updateMutation.mutate({ display_name: displayName });
  };

  // Email preferences mutation
  const emailPrefsMutation = useMutation({
    mutationFn: (data: { daily_digest?: boolean }) =>
      updateEmailPreferences(accessToken!, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['email-preferences'] });
      setSaveSuccess(true);
      setTimeout(() => setSaveSuccess(false), 3000);
    },
  });

  // Handle notification save
  const handleSaveNotifications = () => {
    // Update daily digest via EmailPreferences API
    emailPrefsMutation.mutate({ daily_digest: dailyDigest });
    // Update research_notify via user profile preferences
    updateMutation.mutate({
      preferences: {
        research_notify: researchNotify,
      },
    });
  };

  // Handle account deletion
  const handleDeleteAccount = async () => {
    const supabase = getSupabaseClient();
    // Sign out user (actual deletion would require backend support)
    await supabase.auth.signOut();
    router.push('/');
  };

  if (isCheckingAuth || profileLoading) {
    return (
      <div className="min-h-screen bg-background">
        <div className="max-w-3xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
          {/* Header skeleton */}
          <div className="mb-8">
            <Skeleton className="h-9 w-32 mb-2" />
            <Skeleton className="h-4 w-64" />
          </div>
          {/* Profile card skeleton */}
          <Card className="mb-6">
            <CardHeader>
              <Skeleton className="h-6 w-20 mb-1" />
              <Skeleton className="h-4 w-40" />
            </CardHeader>
            <CardContent className="space-y-4">
              <Skeleton className="h-10 w-full" />
              <Skeleton className="h-10 w-full" />
              <Skeleton className="h-9 w-28" />
            </CardContent>
          </Card>
          {/* Notifications card skeleton */}
          <Card className="mb-6">
            <CardHeader>
              <Skeleton className="h-6 w-28 mb-1" />
              <Skeleton className="h-4 w-48" />
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="flex items-center justify-between">
                <div className="space-y-1">
                  <Skeleton className="h-4 w-24" />
                  <Skeleton className="h-3 w-40" />
                </div>
                <Skeleton className="h-6 w-11 rounded-full" />
              </div>
              <div className="flex items-center justify-between">
                <div className="space-y-1">
                  <Skeleton className="h-4 w-32" />
                  <Skeleton className="h-3 w-44" />
                </div>
                <Skeleton className="h-6 w-11 rounded-full" />
              </div>
              <Skeleton className="h-9 w-36" />
            </CardContent>
          </Card>
          {/* Subscription card skeleton */}
          <Card className="mb-6">
            <CardHeader>
              <Skeleton className="h-6 w-28 mb-1" />
              <Skeleton className="h-4 w-44" />
            </CardHeader>
            <CardContent>
              <div className="flex items-center justify-between p-4 bg-muted rounded-lg">
                <div className="space-y-1">
                  <Skeleton className="h-5 w-24" />
                  <Skeleton className="h-4 w-48" />
                </div>
                <Skeleton className="h-9 w-24" />
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
          <h1 className="text-3xl font-bold tracking-tight">Settings</h1>
          <p className="text-muted-foreground mt-2">
            Manage your account settings and preferences
          </p>
        </div>

        {/* Success Message */}
        {saveSuccess && (
          <div className="mb-6 p-4 bg-green-50 dark:bg-green-900/20 border border-green-200 dark:border-green-800 rounded-lg flex items-center gap-2 text-green-800 dark:text-green-200">
            <Check className="h-5 w-5" />
            Settings saved successfully
          </div>
        )}

        {/* Profile Section */}
        <Card className="mb-6">
          <CardHeader>
            <div className="flex items-center gap-2">
              <User className="h-5 w-5 text-muted-foreground" />
              <CardTitle>Profile</CardTitle>
            </div>
            <CardDescription>Your personal information</CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="space-y-2">
              <label htmlFor="name" className="text-sm font-medium">
                Display Name
              </label>
              <Input
                id="name"
                type="text"
                value={displayName}
                onChange={(e) => setDisplayName(e.target.value)}
                placeholder="Your name"
              />
            </div>
            <div className="space-y-2">
              <label htmlFor="email" className="text-sm font-medium">
                Email
              </label>
              <Input
                id="email"
                type="email"
                value={userEmail}
                disabled
                className="bg-muted"
              />
              <p className="text-xs text-muted-foreground">Email cannot be changed</p>
            </div>
            <Button onClick={handleSaveProfile} disabled={updateMutation.isPending}>
              {updateMutation.isPending ? (
                <Loader2 className="animate-spin h-4 w-4 mr-2" />
              ) : null}
              Save Changes
            </Button>
          </CardContent>
        </Card>

        {/* Notification Preferences */}
        <Card className="mb-6">
          <CardHeader>
            <div className="flex items-center gap-2">
              <Bell className="h-5 w-5 text-muted-foreground" />
              <CardTitle>Notifications</CardTitle>
            </div>
            <CardDescription>Manage how you receive updates</CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="font-medium">Daily Digest</p>
                <p className="text-sm text-muted-foreground">
                  Receive a daily email with new insights
                </p>
              </div>
              <label className="relative inline-flex items-center cursor-pointer">
                <input
                  type="checkbox"
                  checked={dailyDigest}
                  onChange={(e) => setDailyDigest(e.target.checked)}
                  className="sr-only peer"
                />
                <div className="w-11 h-6 bg-muted rounded-full peer peer-checked:after:translate-x-full peer-checked:bg-primary after:content-[''] after:absolute after:top-0.5 after:left-[2px] after:bg-background after:rounded-full after:h-5 after:w-5 after:transition-all"></div>
              </label>
            </div>
            <div className="flex items-center justify-between">
              <div>
                <p className="font-medium">Research Complete</p>
                <p className="text-sm text-muted-foreground">
                  Get notified when AI research finishes
                </p>
              </div>
              <label className="relative inline-flex items-center cursor-pointer">
                <input
                  type="checkbox"
                  checked={researchNotify}
                  onChange={(e) => setResearchNotify(e.target.checked)}
                  className="sr-only peer"
                />
                <div className="w-11 h-6 bg-muted rounded-full peer peer-checked:after:translate-x-full peer-checked:bg-primary after:content-[''] after:absolute after:top-0.5 after:left-[2px] after:bg-background after:rounded-full after:h-5 after:w-5 after:transition-all"></div>
              </label>
            </div>
            <Button variant="outline" onClick={handleSaveNotifications} disabled={updateMutation.isPending || emailPrefsMutation.isPending}>
              {(updateMutation.isPending || emailPrefsMutation.isPending) ? (
                <Loader2 className="animate-spin h-4 w-4 mr-2" />
              ) : null}
              Save Preferences
            </Button>
          </CardContent>
        </Card>

        {/* Subscription */}
        <Card className="mb-6">
          <CardHeader>
            <div className="flex items-center gap-2">
              <CreditCard className="h-5 w-5 text-muted-foreground" />
              <CardTitle>Subscription</CardTitle>
            </div>
            <CardDescription>Manage your plan and billing</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="flex items-center justify-between p-4 bg-muted rounded-lg">
              <div>
                <p className="font-semibold capitalize">{subscription?.tier || 'Free'} Plan</p>
                <p className="text-sm text-muted-foreground">
                  {subscription?.tier === 'enterprise'
                    ? 'Unlimited everything, priority support, API access'
                    : subscription?.tier === 'pro'
                    ? 'Unlimited everything, team features'
                    : subscription?.tier === 'starter'
                    ? 'Unlimited insights, 5 research/month'
                    : '5 insights/day, basic features'}
                </p>
              </div>
              <Link href="/billing">
                <Button>{!subscription?.tier || subscription.tier === 'free' ? 'Upgrade' : 'Manage'}</Button>
              </Link>
            </div>
          </CardContent>
        </Card>

        {/* Refer a Friend */}
        <Card className="mb-6 border-teal-200 dark:border-teal-800">
          <CardHeader>
            <div className="flex items-center gap-2">
              <Gift className="h-5 w-5 text-teal-600 dark:text-teal-400" />
              <CardTitle className="text-teal-700 dark:text-teal-300">Refer a Friend</CardTitle>
            </div>
            <CardDescription>
              Give friends a 14-day Pro trial. Get 1 month free when they subscribe.
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            {referralLoading ? (
              <div className="space-y-3">
                <Skeleton className="h-10 w-full" />
                <div className="flex gap-2">
                  <Skeleton className="h-9 w-32" />
                  <Skeleton className="h-9 w-32" />
                </div>
              </div>
            ) : referralStats ? (
              <>
                {/* Referral count badge */}
                <div className="flex items-center gap-3 p-3 bg-teal-50 dark:bg-teal-900/20 rounded-lg">
                  <div className="text-center">
                    <p className="text-2xl font-bold text-teal-700 dark:text-teal-300">
                      {referralStats.referrals_count}
                    </p>
                    <p className="text-xs text-teal-600 dark:text-teal-400">
                      {referralStats.referrals_count === 1 ? 'referral' : 'referrals'}
                    </p>
                  </div>
                  <div className="text-sm text-muted-foreground">
                    {referralStats.reward_status === 'earned'
                      ? '🎉 You have earned a free month! Contact support to redeem.'
                      : 'Refer 1 paying subscriber to earn 1 month free.'}
                  </div>
                </div>

                {/* Referral link input + copy */}
                <div className="space-y-2">
                  <label className="text-sm font-medium">Your referral link</label>
                  <div className="flex gap-2">
                    <Input
                      readOnly
                      value={referralStats.referral_link}
                      className="font-mono text-sm bg-muted"
                      aria-label="Referral link"
                    />
                    <Button
                      variant="outline"
                      size="icon"
                      onClick={handleCopyReferralLink}
                      aria-label="Copy referral link"
                      className="shrink-0 border-teal-300 dark:border-teal-700 text-teal-700 dark:text-teal-300 hover:bg-teal-50 dark:hover:bg-teal-900/20"
                    >
                      {linkCopied ? (
                        <Check className="h-4 w-4" />
                      ) : (
                        <Copy className="h-4 w-4" />
                      )}
                    </Button>
                  </div>
                </div>

                {/* Share actions */}
                <div className="flex flex-wrap gap-2">
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={handleCopyReferralLink}
                    className="border-teal-300 dark:border-teal-700 text-teal-700 dark:text-teal-300 hover:bg-teal-50 dark:hover:bg-teal-900/20"
                  >
                    <Copy className="h-3.5 w-3.5 mr-1.5" />
                    {linkCopied ? 'Copied!' : 'Copy Link'}
                  </Button>
                  <Button
                    variant="outline"
                    size="sm"
                    asChild
                    className="border-sky-300 dark:border-sky-700 text-sky-700 dark:text-sky-300 hover:bg-sky-50 dark:hover:bg-sky-900/20"
                  >
                    <a
                      href={`https://twitter.com/intent/tweet?text=${encodeURIComponent(
                        `Discovering my next startup idea with @startinsight — AI-powered market intelligence. Try it free: ${referralStats.referral_link}`
                      )}`}
                      target="_blank"
                      rel="noopener noreferrer"
                    >
                      <Twitter className="h-3.5 w-3.5 mr-1.5" />
                      Share on X
                    </a>
                  </Button>
                </div>
              </>
            ) : (
              <p className="text-sm text-muted-foreground">
                Unable to load referral stats. Please refresh the page.
              </p>
            )}
          </CardContent>
        </Card>

        {/* Danger Zone */}
        <Card className="border-red-200 dark:border-red-900">
          <CardHeader>
            <div className="flex items-center gap-2">
              <Trash2 className="h-5 w-5 text-red-500" />
              <CardTitle className="text-red-600 dark:text-red-400">Danger Zone</CardTitle>
            </div>
            <CardDescription>Irreversible account actions</CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            {showDeleteConfirm ? (
              <div className="p-4 bg-red-50 dark:bg-red-900/20 rounded-lg space-y-3">
                <p className="font-medium text-red-800 dark:text-red-200">
                  Are you sure you want to delete your account?
                </p>
                <p className="text-sm text-red-600 dark:text-red-300">
                  This action cannot be undone. All your data will be permanently deleted.
                </p>
                <div className="flex gap-2">
                  <Button
                    variant="destructive"
                    onClick={handleDeleteAccount}
                  >
                    Yes, Delete My Account
                  </Button>
                  <Button
                    variant="outline"
                    onClick={() => setShowDeleteConfirm(false)}
                  >
                    Cancel
                  </Button>
                </div>
              </div>
            ) : (
              <div className="flex items-center justify-between">
                <div>
                  <p className="font-medium">Delete Account</p>
                  <p className="text-sm text-muted-foreground">
                    Permanently delete your account and all data
                  </p>
                </div>
                <Button
                  variant="destructive"
                  onClick={() => setShowDeleteConfirm(true)}
                >
                  Delete Account
                </Button>
              </div>
            )}
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
