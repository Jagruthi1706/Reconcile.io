'use client';

import { cn } from '@/lib/utils';
import { useSidebarStore } from '@/lib/sidebar-store';
import { Sidebar } from '@/components/shell/sidebar';
import { TopBar } from '@/components/shell/top-bar';
import { CommandPalette } from '@/components/shell/command-palette';
import { usePathname, useRouter } from 'next/navigation';
import { useEffect } from 'react';
import { getAccessToken } from '@/lib/session';

interface AppShellProps {
  children: React.ReactNode;
  className?: string;
}

export function AppShell({ children, className }: AppShellProps) {
  const collapsed = useSidebarStore((s) => s.collapsed);
  const pathname = usePathname();
  const router = useRouter();

  useEffect(() => {
    if (pathname !== '/login' && !getAccessToken()) router.replace('/login');
  }, [pathname, router]);

  return (
    <div className="min-h-screen bg-background">
      <Sidebar />
      <div
        className={cn(
          'transition-[padding] duration-200 ease-out',
          collapsed ? 'lg:pl-[var(--sidebar-width-collapsed)]' : 'lg:pl-[var(--sidebar-width)]'
        )}
      >
        <TopBar />
        <main className={cn('min-h-[calc(100vh-var(--topbar-height))]', className)}>{children}</main>
      </div>
      <CommandPalette />
    </div>
  );
}
