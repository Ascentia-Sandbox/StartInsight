'use client';

import Link from 'next/link';
import { useEffect, useState } from 'react';
import type { User, AuthChangeEvent, Session } from '@supabase/supabase-js';
import { Button } from '@/components/ui/button';
import { TierBadge } from '@/components/ui/TierBadge';
import { getSupabaseClient } from '@/lib/supabase/client';
import { useSubscription } from '@/hooks/useSubscription';
import dynamic from 'next/dynamic';
import { MegaMenu } from '@/components/navigation/mega-menu';
import { MobileMenu } from '@/components/navigation/mobile-menu';
import { Shield } from 'lucide-react';

const ThemeToggle = dynamic(() => import('./theme-toggle').then(mod => ({ default: mod.ThemeToggle })), {
  ssr: false,
  loading: () => <div className="w-10 h-10" />
});

function isAdmin(user: User): boolean {
  return (
    user.app_metadata?.role === 'superadmin' ||
    user.app_metadata?.role === 'admin' ||
    user.user_metadata?.role === 'superadmin' ||
    user.user_metadata?.role === 'admin'
  );
}

function UserMenu({ user }: { user: User }) {
  const [open, setOpen] = useState(false);
  const supabase = getSupabaseClient();
  const showAdmin = isAdmin(user);
  const { tier } = useSubscription();

  const handleSignOut = async () => {
    await supabase.auth.signOut();
    window.location.href = '/';
  };

  const userName = user.user_metadata?.full_name || user.email?.split('@')[0] || 'User';
  const initials = userName
    .split(' ')
    .map((n: string) => n[0])
    .join('')
    .toUpperCase()
    .slice(0, 2);

  return (
    <div className="relative">
      <button
        onClick={() => setOpen(!open)}
        className="flex items-center gap-2 rounded-full bg-primary text-primary-foreground w-9 h-9 items-center justify-center text-sm font-medium hover:opacity-80 transition-opacity"
        aria-label={`User menu — ${tier} plan`}
      >
        {initials}
      </button>

      {open && (
        <>
          <div className="fixed inset-0 z-40" onClick={() => setOpen(false)} />
          <div className="absolute right-0 mt-2 w-56 rounded-md shadow-lg bg-background border z-50">
            <div className="p-3 border-b">
              <p className="text-sm font-medium">{userName}</p>
              <p className="text-xs text-muted-foreground truncate">{user.email}</p>
              <div className="flex items-center gap-1.5 mt-1.5">
                <TierBadge tier={tier} />
                {showAdmin && (
                  <span className="inline-flex items-center gap-1 text-[10px] font-medium text-amber-600 dark:text-amber-400 bg-amber-100 dark:bg-amber-900/30 px-1.5 py-0.5 rounded">
                    <Shield className="h-2.5 w-2.5" />
                    Super Admin
                  </span>
                )}
              </div>
            </div>
            <div className="p-1">
              {showAdmin && (
                <Link
                  href="/admin/agents"
                  className="flex items-center gap-2 px-3 py-2 text-sm rounded-md hover:bg-muted font-medium text-primary"
                  onClick={() => setOpen(false)}
                >
                  <Shield className="h-4 w-4" />
                  Admin Portal
                </Link>
              )}
              <Link
                href="/dashboard"
                className="block px-3 py-2 text-sm rounded-md hover:bg-muted"
                onClick={() => setOpen(false)}
              >
                Dashboard
              </Link>
              <Link
                href="/workspace"
                className="block px-3 py-2 text-sm rounded-md hover:bg-muted"
                onClick={() => setOpen(false)}
              >
                My Workspace
              </Link>
              <Link
                href="/settings"
                className="block px-3 py-2 text-sm rounded-md hover:bg-muted"
                onClick={() => setOpen(false)}
              >
                Settings
              </Link>
              <Link
                href="/billing"
                className="block px-3 py-2 text-sm rounded-md hover:bg-muted"
                onClick={() => setOpen(false)}
              >
                Billing
              </Link>
            </div>
            <div className="border-t p-1">
              <button
                onClick={handleSignOut}
                className="w-full text-left px-3 py-2 text-sm rounded-md hover:bg-muted text-red-600 dark:text-red-400"
              >
                Sign out
              </button>
            </div>
          </div>
        </>
      )}
    </div>
  );
}

export function Header() {
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const supabase = getSupabaseClient();

    // Get initial user
    const getUser = async () => {
      const { data } = await supabase.auth.getUser();
      setUser(data.user);
      setLoading(false);
    };
    getUser();

    // Listen for auth changes
    const { data: { subscription } } = supabase.auth.onAuthStateChange((_event: AuthChangeEvent, session: Session | null) => {
      setUser(session?.user ?? null);
    });

    return () => subscription.unsubscribe();
  }, []);

  return (
    <header className="border-b bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/60 sticky top-0 z-50">
      <div className="container mx-auto px-4 py-3 flex items-center justify-between">
        {/* Logo */}
        <div className="flex items-center gap-6">
          <Link href="/" className="text-xl font-bold text-primary" data-tour="logo">
            StartInsight
          </Link>

          {/* Desktop Navigation */}
          <MegaMenu />
        </div>

        {/* Right Section */}
        <nav className="flex gap-2 items-center">
          <div data-tour="theme-toggle">
            <ThemeToggle />
          </div>

          {!loading && (
            <>
              {/* Mobile Menu */}
              <MobileMenu isAuthenticated={!!user} />

              {/* Desktop Auth */}
              <div className="hidden md:flex items-center gap-2">
                {user ? (
                  <UserMenu user={user} />
                ) : (
                  <>
                    <Button variant="ghost" asChild>
                      <Link href="/auth/login">Sign in</Link>
                    </Button>
                    <Button asChild data-tour="get-started">
                      <Link href="/auth/signup">Get Started</Link>
                    </Button>
                  </>
                )}
              </div>
            </>
          )}
        </nav>
      </div>
    </header>
  );
}
