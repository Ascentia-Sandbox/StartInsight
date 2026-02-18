'use client';

import { useEffect, useState, useCallback, useRef } from 'react';
import { useRouter } from 'next/navigation';
import {
  Dialog,
  DialogContent,
  DialogTitle,
} from '@/components/ui/dialog';
import { Input } from '@/components/ui/input';
import {
  LayoutDashboard,
  Users,
  Lightbulb,
  TrendingUp,
  Settings,
  FileText,
  Wrench,
  BarChart3,
  Search,
  Trophy,
  Activity,
  Plug,
  FileCheck,
  ClipboardList,
  Zap,
  FileSearch,
  Command,
} from 'lucide-react';
import { cn } from '@/lib/utils';

interface CommandItem {
  label: string;
  href: string;
  icon: React.ReactNode;
  category: string;
  keywords?: string[];
}

const COMMANDS: CommandItem[] = [
  // Admin Navigation
  { label: 'Dashboard', href: '/admin', icon: <LayoutDashboard className="h-4 w-4" />, category: 'Admin', keywords: ['home', 'overview', 'metrics'] },
  { label: 'Insights', href: '/admin/insights', icon: <Lightbulb className="h-4 w-4" />, category: 'Admin', keywords: ['ideas', 'startup'] },
  { label: 'Users', href: '/admin/users', icon: <Users className="h-4 w-4" />, category: 'Admin', keywords: ['members', 'accounts'] },
  { label: 'AI Agents', href: '/admin/agents', icon: <Zap className="h-4 w-4" />, category: 'Admin', keywords: ['scraper', 'bot', 'automation'] },
  { label: 'Trends', href: '/admin/trends', icon: <TrendingUp className="h-4 w-4" />, category: 'Admin', keywords: ['trending', 'growth'] },
  { label: 'Tools & Affiliates', href: '/admin/tools', icon: <Wrench className="h-4 w-4" />, category: 'Admin', keywords: ['affiliates', 'products'] },
  { label: 'Market Insights', href: '/admin/market-insights', icon: <FileText className="h-4 w-4" />, category: 'Admin', keywords: ['articles', 'reports'] },
  { label: 'Success Stories', href: '/admin/success-stories', icon: <Trophy className="h-4 w-4" />, category: 'Admin', keywords: ['case study'] },
  { label: 'Analytics', href: '/admin/analytics', icon: <BarChart3 className="h-4 w-4" />, category: 'Admin', keywords: ['stats', 'charts', 'data'] },
  { label: 'Pipeline', href: '/admin/pipeline', icon: <Activity className="h-4 w-4" />, category: 'Admin', keywords: ['workflow', 'process'] },
  { label: 'Content Review', href: '/admin/content-review', icon: <FileCheck className="h-4 w-4" />, category: 'Admin', keywords: ['moderation', 'approval'] },
  { label: 'Integrations', href: '/admin/integrations', icon: <Plug className="h-4 w-4" />, category: 'Admin', keywords: ['api', 'webhooks', 'connect'] },
  { label: 'Research Queue', href: '/admin/research-queue', icon: <FileSearch className="h-4 w-4" />, category: 'Admin', keywords: ['requests', 'queue'] },
  { label: 'Audit Logs', href: '/admin/audit-logs', icon: <ClipboardList className="h-4 w-4" />, category: 'Admin', keywords: ['history', 'changes'] },
  // Public Pages
  { label: 'Home', href: '/', icon: <LayoutDashboard className="h-4 w-4" />, category: 'Public Pages', keywords: ['landing'] },
  { label: 'Browse Insights', href: '/insights', icon: <Search className="h-4 w-4" />, category: 'Public Pages', keywords: ['explore', 'discover'] },
  { label: 'Validate Idea', href: '/validate', icon: <Lightbulb className="h-4 w-4" />, category: 'Public Pages', keywords: ['test', 'check', 'research'] },
  // Quick Actions
  { label: 'Settings', href: '/admin/agents', icon: <Settings className="h-4 w-4" />, category: 'Quick Actions', keywords: ['config', 'preferences'] },
];

export function CommandPalette() {
  const [open, setOpen] = useState(false);
  const [query, setQuery] = useState('');
  const [selectedIndex, setSelectedIndex] = useState(0);
  const router = useRouter();
  const inputRef = useRef<HTMLInputElement>(null);
  const listRef = useRef<HTMLDivElement>(null);

  // Filter commands based on search query
  const filteredCommands = query.trim()
    ? COMMANDS.filter((cmd) => {
        const q = query.toLowerCase();
        return (
          cmd.label.toLowerCase().includes(q) ||
          cmd.category.toLowerCase().includes(q) ||
          cmd.keywords?.some((kw) => kw.toLowerCase().includes(q))
        );
      })
    : COMMANDS;

  // Group by category
  const grouped = filteredCommands.reduce<Record<string, CommandItem[]>>(
    (acc, cmd) => {
      if (!acc[cmd.category]) acc[cmd.category] = [];
      acc[cmd.category].push(cmd);
      return acc;
    },
    {}
  );

  const flatItems = Object.values(grouped).flat();

  // Keyboard shortcut to open
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if ((e.metaKey || e.ctrlKey) && e.key === 'k') {
        e.preventDefault();
        setOpen((prev) => !prev);
      }
    };
    document.addEventListener('keydown', handleKeyDown);
    return () => document.removeEventListener('keydown', handleKeyDown);
  }, []);

  // Reset state when opening
  useEffect(() => {
    if (open) {
      setQuery('');
      setSelectedIndex(0);
      // Focus input after dialog animation
      setTimeout(() => inputRef.current?.focus(), 50);
    }
  }, [open]);

  // Scroll selected item into view
  useEffect(() => {
    if (!listRef.current) return;
    const selected = listRef.current.querySelector('[data-selected="true"]');
    if (selected) {
      selected.scrollIntoView({ block: 'nearest' });
    }
  }, [selectedIndex]);

  // Reset selected index when query changes
  useEffect(() => {
    setSelectedIndex(0);
  }, [query]);

  const navigate = useCallback(
    (href: string) => {
      setOpen(false);
      router.push(href);
    },
    [router]
  );

  const handleKeyDown = useCallback(
    (e: React.KeyboardEvent) => {
      switch (e.key) {
        case 'ArrowDown':
          e.preventDefault();
          setSelectedIndex((prev) => (prev + 1) % flatItems.length);
          break;
        case 'ArrowUp':
          e.preventDefault();
          setSelectedIndex((prev) => (prev - 1 + flatItems.length) % flatItems.length);
          break;
        case 'Enter':
          e.preventDefault();
          if (flatItems[selectedIndex]) {
            navigate(flatItems[selectedIndex].href);
          }
          break;
        case 'Escape':
          e.preventDefault();
          setOpen(false);
          break;
      }
    },
    [flatItems, selectedIndex, navigate]
  );

  let itemIndex = -1;

  return (
    <Dialog open={open} onOpenChange={setOpen}>
      <DialogContent
        className="overflow-hidden p-0 shadow-lg max-w-lg"
        onKeyDown={handleKeyDown}
      >
        <DialogTitle className="sr-only">Command Palette</DialogTitle>
        {/* Search input */}
        <div className="flex items-center border-b px-3">
          <Search className="mr-2 h-4 w-4 shrink-0 opacity-50" />
          <Input
            ref={inputRef}
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="Type a command or search..."
            className="h-11 border-0 bg-transparent px-0 shadow-none focus-visible:ring-0 focus-visible:ring-offset-0"
          />
          <kbd className="ml-2 pointer-events-none inline-flex h-5 items-center gap-1 rounded border bg-muted px-1.5 font-mono text-[10px] font-medium text-muted-foreground opacity-100">
            ESC
          </kbd>
        </div>

        {/* Command list */}
        <div ref={listRef} className="max-h-[300px] overflow-y-auto px-1 py-2">
          {flatItems.length === 0 ? (
            <div className="py-6 text-center text-sm text-muted-foreground">
              No results found.
            </div>
          ) : (
            Object.entries(grouped).map(([category, items]) => (
              <div key={category} className="mb-2">
                <div className="px-2 py-1.5 text-xs font-medium text-muted-foreground">
                  {category}
                </div>
                {items.map((cmd) => {
                  itemIndex++;
                  const currentIndex = itemIndex;
                  const isSelected = currentIndex === selectedIndex;

                  return (
                    <button
                      key={cmd.href}
                      data-selected={isSelected}
                      onClick={() => navigate(cmd.href)}
                      onMouseEnter={() => setSelectedIndex(currentIndex)}
                      className={cn(
                        'relative flex w-full cursor-pointer select-none items-center rounded-sm px-2 py-1.5 text-sm outline-none transition-colors',
                        isSelected
                          ? 'bg-accent text-accent-foreground'
                          : 'text-foreground hover:bg-accent/50'
                      )}
                    >
                      <span className="mr-3 flex h-5 w-5 items-center justify-center opacity-70">
                        {cmd.icon}
                      </span>
                      <span>{cmd.label}</span>
                    </button>
                  );
                })}
              </div>
            ))
          )}
        </div>

        {/* Footer hint */}
        <div className="flex items-center justify-between border-t px-3 py-2 text-xs text-muted-foreground">
          <div className="flex items-center gap-2">
            <kbd className="inline-flex h-5 items-center rounded border bg-muted px-1 font-mono text-[10px]">
              <span className="text-xs">&#8593;</span><span className="text-xs">&#8595;</span>
            </kbd>
            <span>Navigate</span>
            <kbd className="inline-flex h-5 items-center rounded border bg-muted px-1 font-mono text-[10px]">
              Enter
            </kbd>
            <span>Select</span>
          </div>
          <div className="flex items-center gap-1">
            <Command className="h-3 w-3" />
            <span>K to toggle</span>
          </div>
        </div>
      </DialogContent>
    </Dialog>
  );
}
