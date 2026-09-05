'use client';

import Link from 'next/link';
import { Search, Bell, Menu, LogOut } from 'lucide-react';

import { useSidebarStore } from '@/lib/sidebar-store';
import { logout } from '@/lib/api-client';

export function TopBar() {
  const { setMobileOpen } = useSidebarStore();
  const openPalette = () => window.dispatchEvent(new KeyboardEvent('keydown', { key: 'k', metaKey: true }));

  return (
    <header className="sticky top-0 z-20 border-b border-border bg-background/80 backdrop-blur-sm">
      <div className="flex h-[var(--topbar-height)] items-center justify-between gap-3 px-4">
        <div className="flex items-center gap-3">
          <button
            type="button"
            className="inline-flex h-8 w-8 items-center justify-center rounded-control border border-border bg-card text-foreground lg:hidden"
            onClick={() => setMobileOpen(true)}
            aria-label="Open navigation"
          >
            <Menu className="h-4 w-4" aria-hidden="true" />
          </button>
          <button type="button" onClick={openPalette} className="flex items-center gap-2 rounded-control border border-border bg-card px-2.5 py-1.5 text-sm text-foreground/70 hover:bg-muted" aria-label="Open command palette">
            <Search className="h-3.5 w-3.5" aria-hidden="true" />
            <span className="font-medium">⌘K</span>
            <span className="hidden sm:inline">Search</span>
          </button>
        </div>

        <div className="flex items-center gap-2">
          <span className="rounded-control border border-border bg-primary px-2 py-1 text-[10px] uppercase tracking-[0.12em] text-primary-foreground">
            TEST MODE
          </span>
          <button type="button" className="inline-flex h-8 w-8 items-center justify-center rounded-control border border-border bg-card text-foreground" aria-label="Notifications">
            <Bell className="h-4 w-4" aria-hidden="true" />
          </button>
          <Link href="/settings" className="inline-flex items-center rounded-control border border-border bg-card px-2.5 py-1.5 text-sm font-medium text-foreground">
            User
          </Link>
          <button type="button" onClick={logout} className="inline-flex h-8 w-8 items-center justify-center rounded-control border border-border bg-card text-foreground" aria-label="Sign out">
            <LogOut className="h-4 w-4" aria-hidden="true" />
          </button>
        </div>
      </div>
    </header>
  );
}
