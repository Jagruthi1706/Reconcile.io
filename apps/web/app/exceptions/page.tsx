'use client';
import { useMemo, useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { PageContainer } from '@/components/shell/page-container';
import { PageHeader } from '@/components/shell/page-header';
import { getExceptions } from '@/lib/api-client';
import type { ExceptionStatus } from '@/lib/api-types';

const statuses: Array<ExceptionStatus | 'all'> = ['all', 'new', 'investigating', 'resolved', 'written_off'];

export default function ExceptionsPage() {
  const [status, setStatus] = useState<ExceptionStatus | 'all'>('all');
  const [search, setSearch] = useState('');
  const { data, isLoading, error } = useQuery({ queryKey: ['exceptions'], queryFn: () => getExceptions() });
  const filtered = useMemo(() => data?.filter((item) => {
    const query = search.toLowerCase();
    return (status === 'all' || item.status === status) && (!query || [item.id, item.line_id, item.run_id, item.reason_code, item.reason_text, item.assignee ?? ''].some((value) => value.toLowerCase().includes(query)));
  }), [data, search, status]);

  return (
    <PageContainer>
      <PageHeader title="Exceptions" question="What needs review?" description="A read-only queue of unresolved items, their machine-readable reasons, and the evidence needed for the next decision." />
      <div className="mt-6 rounded-panel border border-border bg-card shadow-card">
        <div className="flex flex-col gap-3 border-b border-border p-4 md:flex-row md:items-center md:justify-between">
          <input value={search} onChange={(event) => setSearch(event.target.value)} placeholder="Search IDs, reasons, or assignees" aria-label="Search exceptions" className="h-9 rounded-control border border-border bg-background px-3 text-sm outline-none focus:ring-2 focus:ring-ink/30" />
          <div className="flex flex-wrap gap-1" aria-label="Filter by exception status">
            {statuses.map((value) => <button key={value} type="button" aria-pressed={status === value} onClick={() => setStatus(value)} className={`rounded-control px-2.5 py-1.5 text-xs focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ink/30 ${status === value ? 'bg-ink text-parchment' : 'text-foreground/60 hover:bg-muted'}`}>{value === 'all' ? 'All statuses' : value.replace('_', ' ')}</button>)}
          </div>
        </div>
        {isLoading && <div className="p-8 text-sm text-foreground/60">Loading exceptions...</div>}
        {error && <div className="p-8 text-sm text-error">Exception data is unavailable.</div>}
        {!isLoading && !error && !filtered?.length && <div className="p-10 text-center text-sm text-foreground/60">No exceptions match the current filters.</div>}
        {!!filtered?.length && <div className="overflow-x-auto"><table className="w-full min-w-[900px] text-left text-sm"><thead className="border-b border-border text-xs uppercase tracking-[0.12em] text-foreground/50"><tr><th className="px-4 py-3">Exception</th><th className="px-4 py-3">Reason</th><th className="px-4 py-3">Status</th><th className="px-4 py-3">Assignee</th><th className="px-4 py-3">Opened</th><th className="px-4 py-3">Resolved</th></tr></thead><tbody className="divide-y divide-border">{filtered.map((item) => <tr key={item.id} className="hover:bg-background"><td className="px-4 py-3"><div className="font-mono text-xs">{item.id}</div><div className="mt-1 text-xs text-foreground/50">Line {item.line_id} · Run {item.run_id}</div></td><td className="max-w-[280px] px-4 py-3"><div className="font-mono text-xs text-foreground/70">{item.reason_code}</div><div className="mt-1 text-xs text-foreground/60">{item.reason_text}</div></td><td className="px-4 py-3"><span className="rounded-control border border-border px-2 py-1 text-xs">{item.status.replace('_', ' ')}</span></td><td className="px-4 py-3 text-foreground/70">{item.assignee ?? 'Unassigned'}</td><td className="px-4 py-3 text-xs tabular-nums text-foreground/60">{new Date(item.opened_at).toLocaleDateString()}</td><td className="px-4 py-3 text-xs tabular-nums text-foreground/60">{item.resolved_at ? new Date(item.resolved_at).toLocaleDateString() : 'Open'}</td></tr>)}</tbody></table></div>}
      </div>
    </PageContainer>
  );
}
