'use client';

import Link from 'next/link';
import { useEffect, useState } from 'react';
import type { User, AuthChangeEvent, Session } from '@supabase/supabase-js';
import { Button } from '@/components/ui/button';
import { getSupabaseClient } from '@/lib/supabase/client';
import dynamic from 'next/dynamic';

const ThemeToggle = dynamic(() => import('./theme-toggle').then(mod => ({ default: mod.ThemeToggle })), {
  ssr: false,
  loading: () => <div className="w-10 h-10" />
});

function UserMenu({ user }: { user: User }) {
  const [open, setOpen] = useState(false);
  const supabase = getSupabaseClient();

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
            </div>
            <div className="p-1">
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
    <header className="border-b">
      <div className="container mx-auto px-4 py-4 flex items-center justify-between">
        <Link href="/" className="text-2xl font-bold">
          StartInsight
        </Link>
        <nav className="flex gap-4 items-center">
          <Button variant="ghost" asChild>
            <Link href="/">Home</Link>
          </Button>
          <Button variant="ghost" asChild>
            <Link href="/insights">All Insights</Link>
          </Button>
          <ThemeToggle />

          {!loading && (
            user ? (
              <UserMenu user={user} />
            ) : (
              <Button asChild>
                <Link href="/auth/login">Sign in</Link>
              </Button>
            )
          )}
        </nav>
      </div>
    </header>
  );
}
