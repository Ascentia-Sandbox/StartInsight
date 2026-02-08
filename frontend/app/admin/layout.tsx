'use client';

import { useState } from 'react';
import Link from 'next/link';
import { usePathname } from 'next/navigation';
import {
  LayoutDashboard,
  Users,
  Zap,
  Wrench,
  TrendingUp,
  BarChart3,
  Trophy,
  FileSearch,
  ClipboardList,
  ChevronLeft,
  ChevronRight,
  Menu,
  Shield,
  X,
} from 'lucide-react';
import { cn } from '@/lib/utils';
import { Providers } from '../providers';
import { ThemeProvider } from '@/components/theme-provider';
import { Button } from '@/components/ui/button';

const navItems = [
  {
    label: 'Dashboard',
    href: '/admin',
    icon: LayoutDashboard,
  },
  {
    label: 'Users',
    href: '/admin/users',
    icon: Users,
  },
  {
    label: 'AI Agents',
    href: '/admin/agents',
    icon: Zap,
  },
  {
    label: 'Research Queue',
    href: '/admin/research-queue',
    icon: FileSearch,
  },
  {
    label: 'Tools & Affiliates',
    href: '/admin/tools',
    icon: Wrench,
  },
  {
    label: 'Trends',
    href: '/admin/trends',
    icon: TrendingUp,
  },
  {
    label: 'Market Insights',
    href: '/admin/market-insights',
    icon: BarChart3,
  },
  {
    label: 'Success Stories',
    href: '/admin/success-stories',
    icon: Trophy,
  },
  {
    label: 'Audit Logs',
    href: '/admin/audit-logs',
    icon: ClipboardList,
  },
];

function isActive(pathname: string, href: string) {
  if (href === '/admin') return pathname === '/admin';
  return pathname.startsWith(href);
}

export default function AdminLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  const pathname = usePathname();
  const [collapsed, setCollapsed] = useState(false);
  const [mobileOpen, setMobileOpen] = useState(false);

  return (
    <ThemeProvider>
      <Providers>
        <div className="min-h-screen bg-muted/30">
          {/* Mobile header */}
          <div className="lg:hidden flex items-center justify-between border-b bg-background px-4 h-14">
            <Button
              variant="ghost"
              size="icon"
              onClick={() => setMobileOpen(true)}
            >
              <Menu className="h-5 w-5" />
            </Button>
            <div className="flex items-center gap-2">
              <Shield className="h-5 w-5 text-primary" />
              <span className="font-semibold text-sm">Admin Portal</span>
            </div>
            <div className="w-9" />
          </div>

          {/* Mobile overlay */}
          {mobileOpen && (
            <div
              className="lg:hidden fixed inset-0 z-40 bg-black/50"
              onClick={() => setMobileOpen(false)}
            />
          )}

          <div className="flex">
            {/* Sidebar - Desktop */}
            <aside
              className={cn(
                'hidden lg:flex flex-col border-r bg-background h-screen sticky top-0 transition-all duration-200',
                collapsed ? 'w-16' : 'w-60'
              )}
            >
              <SidebarContent
                pathname={pathname}
                collapsed={collapsed}
                onCollapse={() => setCollapsed(!collapsed)}
              />
            </aside>

            {/* Sidebar - Mobile */}
            <aside
              className={cn(
                'lg:hidden fixed inset-y-0 left-0 z-50 flex flex-col border-r bg-background w-60 transition-transform duration-200',
                mobileOpen ? 'translate-x-0' : '-translate-x-full'
              )}
            >
              <div className="flex items-center justify-end p-2">
                <Button
                  variant="ghost"
                  size="icon"
                  onClick={() => setMobileOpen(false)}
                >
                  <X className="h-4 w-4" />
                </Button>
              </div>
              <SidebarContent
                pathname={pathname}
                collapsed={false}
                onCollapse={() => {}}
                onNavigate={() => setMobileOpen(false)}
              />
            </aside>

            {/* Main content */}
            <main className="flex-1 min-h-screen">
              {children}
            </main>
          </div>
        </div>
      </Providers>
    </ThemeProvider>
  );
}

function SidebarContent({
  pathname,
  collapsed,
  onCollapse,
  onNavigate,
}: {
  pathname: string;
  collapsed: boolean;
  onCollapse: () => void;
  onNavigate?: () => void;
}) {
  return (
    <>
      {/* Logo */}
      <div className={cn(
        'flex items-center border-b h-14 px-3',
        collapsed ? 'justify-center' : 'gap-2'
      )}>
        <Shield className="h-5 w-5 text-primary flex-shrink-0" />
        {!collapsed && (
          <span className="font-semibold text-sm truncate">Admin Portal</span>
        )}
      </div>

      {/* Navigation */}
      <nav className="flex-1 py-3 px-2 space-y-1 overflow-y-auto">
        {navItems.map((item) => {
          const active = isActive(pathname, item.href);
          const Icon = item.icon;

          return (
            <Link
              key={item.href}
              href={item.href}
              onClick={onNavigate}
              className={cn(
                'flex items-center gap-3 rounded-md px-3 py-2 text-sm font-medium transition-colors',
                active
                  ? 'bg-primary/10 text-primary'
                  : 'text-muted-foreground hover:bg-muted hover:text-foreground',
                collapsed && 'justify-center px-2'
              )}
              title={collapsed ? item.label : undefined}
            >
              <Icon className="h-4 w-4 flex-shrink-0" />
              {!collapsed && <span className="truncate">{item.label}</span>}
            </Link>
          );
        })}
      </nav>

      {/* Collapse toggle - desktop only */}
      <div className="hidden lg:flex border-t p-2">
        <Button
          variant="ghost"
          size="sm"
          onClick={onCollapse}
          className={cn('w-full', collapsed && 'px-0')}
        >
          {collapsed ? (
            <ChevronRight className="h-4 w-4" />
          ) : (
            <>
              <ChevronLeft className="h-4 w-4 mr-2" />
              <span className="text-xs">Collapse</span>
            </>
          )}
        </Button>
      </div>

      {/* Back to site */}
      <div className="border-t p-2">
        <Link
          href="/"
          onClick={onNavigate}
          className={cn(
            'flex items-center gap-2 rounded-md px-3 py-2 text-xs text-muted-foreground hover:text-foreground transition-colors',
            collapsed && 'justify-center px-2'
          )}
        >
          {!collapsed && 'Back to Site'}
        </Link>
      </div>
    </>
  );
}
