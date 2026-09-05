'use client';

import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { forwardRef } from 'react';
import { PanelLeftClose, PanelLeftOpen } from 'lucide-react';

import { cn } from '@/lib/utils';
import { navRoutes } from '@/lib/navigation';
import { useSidebarStore } from '@/lib/sidebar-store';
import { Tooltip, TooltipContent, TooltipTrigger } from '@/components/ui/tooltip';

export const Sidebar = forwardRef<HTMLElement, React.HTMLAttributes<HTMLElement>>(
  ({ className, ...props }, ref) => {
    const pathname = usePathname();
    const { collapsed, toggle, mobileOpen, setMobileOpen } = useSidebarStore();

    return (
      <>
        {mobileOpen && (
          <div className="fixed inset-0 z-30 bg-ink/40 lg:hidden" onClick={() => setMobileOpen(false)} aria-hidden="true" />
        )}

        <aside
          ref={ref}
          className={cn(
            'fixed inset-y-0 left-0 z-40 overflow-y-auto border-r border-shell-border bg-shell-bg transition-[width,transform] duration-200 ease-out',
            collapsed ? 'w-[var(--sidebar-width-collapsed)]' : 'w-[var(--sidebar-width)]',
            mobileOpen ? 'translate-x-0' : '-translate-x-full lg:translate-x-0',
            className
          )}
          aria-label="Primary navigation"
          {...props}
        >
          <div className="flex h-[var(--topbar-height)] items-center border-b border-shell-border px-3">
            <Link href="/" className="flex items-center gap-2.5" onClick={() => setMobileOpen(false)} aria-label="Reconcile.io home">
              <span className="flex h-7 w-7 items-center justify-center rounded-dense bg-shell-text text-shell-bg">
                <span className="font-accent text-xs font-medium">R</span>
              </span>
              {!collapsed && (
                <span className="font-editorial text-lg leading-none text-shell-text">
                  Reconcile<span className="text-shell-muted">.io</span>
                </span>
              )}
            </Link>
          </div>

          <nav className="px-2 py-3" aria-label="Main navigation">
            <ul className="space-y-0.5">
              {navRoutes.map((route) => {
                const isActive = route.href === '/' ? pathname === '/' : pathname.startsWith(route.href);
                const Icon = route.icon;

                const linkContent = (
                  <Link
                    href={route.href}
                    onClick={() => setMobileOpen(false)}
                    className={cn(
                      'group relative flex items-center gap-3 px-2.5 py-2 text-sm transition-colors duration-150',
                      'focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-shell-text/40 focus-visible:ring-offset-0',
                      isActive ? 'font-medium text-shell-active-text' : 'text-shell-muted hover:bg-shell-hover hover:text-shell-text',
                      collapsed && 'justify-center px-0'
                    )}
                    aria-current={isActive ? 'page' : undefined}
                  >
                    {isActive && !collapsed && <span className="absolute inset-0 bg-shell-active" aria-hidden="true" />}
                    <Icon className="relative h-4 w-4 shrink-0" aria-hidden="true" />
                    {!collapsed && <span className="relative truncate">{route.label}</span>}
                  </Link>
                );

                return (
                  <li key={route.href}>
                    {collapsed ? (
                      <Tooltip>
                        <TooltipTrigger asChild>{linkContent}</TooltipTrigger>
                        <TooltipContent side="right" className="border-shell-border bg-shell-surface text-shell-text">
                          <div className="space-y-0.5">
                            <p className="font-medium">{route.label}</p>
                            <p className="text-xs text-shell-muted">{route.description}</p>
                          </div>
                        </TooltipContent>
                      </Tooltip>
                    ) : (
                      linkContent
                    )}
                  </li>
                );
              })}
            </ul>
          </nav>

          <div className="absolute bottom-0 left-0 right-0 hidden border-t border-shell-border p-2 lg:block">
            <button
              onClick={toggle}
              className={cn(
                'flex w-full items-center gap-3 px-2.5 py-2 text-sm text-shell-muted transition-colors duration-150 hover:bg-shell-hover hover:text-shell-text',
                'focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-shell-text/40',
                collapsed && 'justify-center px-0'
              )}
              aria-label={collapsed ? 'Expand sidebar' : 'Collapse sidebar'}
              aria-expanded={!collapsed}
            >
              {collapsed ? <PanelLeftOpen className="h-4 w-4 shrink-0" aria-hidden="true" /> : <><PanelLeftClose className="h-4 w-4 shrink-0" aria-hidden="true" /><span className="text-xs text-shell-muted">Collapse</span></>}
            </button>
          </div>
        </aside>
      </>
    );
  }
);

Sidebar.displayName = 'Sidebar';
