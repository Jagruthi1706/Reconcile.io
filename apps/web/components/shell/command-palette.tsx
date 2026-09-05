'use client';

import { useEffect, useMemo, useState } from 'react';
import { useRouter } from 'next/navigation';
import { Search, ArrowUpRight } from 'lucide-react';

import { navRoutes } from '@/lib/navigation';

export function CommandPalette() {
  const [open, setOpen] = useState(false);
  const [query, setQuery] = useState('');
  const router = useRouter();

  useEffect(() => {
    const onKeyDown = (event: KeyboardEvent) => {
      if ((event.metaKey || event.ctrlKey) && event.key.toLowerCase() === 'k') {
        event.preventDefault();
        setOpen(true);
        setQuery('');
      }
      if (event.key === 'Escape') setOpen(false);
    };

    window.addEventListener('keydown', onKeyDown);
    return () => window.removeEventListener('keydown', onKeyDown);
  }, []);

  if (!open) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-start justify-center bg-ink/40 p-6 backdrop-blur-[2px]" role="presentation" onClick={() => setOpen(false)}>
      <div className="w-full max-w-2xl overflow-hidden rounded-panel border border-border bg-card shadow-card" role="dialog" aria-modal="true" aria-label="Command palette" onClick={(e) => e.stopPropagation()}>
        <div className="flex items-center gap-2 border-b border-border px-4 py-3">
          <Search className="h-4 w-4 text-foreground/60" aria-hidden="true" />
          <input
            autoFocus
            value={query}
            onChange={(event) => setQuery(event.target.value)}
            className="w-full bg-transparent text-sm text-foreground outline-none placeholder:text-foreground/50"
            placeholder="Search pages or record IDs"
            aria-label="Search pages or record IDs"
          />
        </div>
        <div className="max-h-[60vh] overflow-auto p-2">
          {navRoutes.filter((route) => `${route.label} ${route.description}`.toLowerCase().includes(query.toLowerCase())).map((route) => (
            <button
              key={route.href}
              type="button"
              className="flex w-full items-center justify-between rounded-control px-3 py-2 text-left hover:bg-muted"
              onClick={() => {
                setOpen(false);
                router.push(route.href);
              }}
            >
              <span className="flex items-center gap-2">
                <route.icon className="h-4 w-4" aria-hidden="true" />
                <span>{route.label}</span>
              </span>
              <ArrowUpRight className="h-3.5 w-3.5 text-foreground/60" aria-hidden="true" />
            </button>
          ))}
          {!navRoutes.some((route) => `${route.label} ${route.description}`.toLowerCase().includes(query.toLowerCase())) && <p className="p-4 text-sm text-foreground/60">No matching pages.</p>}
        </div>
      </div>
    </div>
  );
}
