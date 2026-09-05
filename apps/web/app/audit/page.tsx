 'use client';
import { useQuery } from '@tanstack/react-query';
import { PageContainer } from '@/components/shell/page-container';
import { PageHeader } from '@/components/shell/page-header';
import { getAudit } from '@/lib/api-client';

export default function AuditPage() {
  const query = useQuery({ queryKey: ['audit'], queryFn: () => getAudit({ limit: 100 }) });
  return (
    <PageContainer>
      <PageHeader title="Audit" question="Can I prove what happened?" description="An immutable, read-only view of recorded state changes and their structured context." />
      <div className="mt-6 rounded-panel border border-border bg-card shadow-card">
        {query.isLoading && <div className="p-8 text-sm text-foreground/60">Loading audit trail...</div>}
        {query.error && <div className="p-8 text-sm text-error">Audit data is unavailable.</div>}
        {!query.isLoading && !query.error && !query.data?.length && <div className="p-10 text-center text-sm text-foreground/60">No audit events have been recorded.</div>}
        {!!query.data?.length && <div className="divide-y divide-border">{query.data.map((entry) => <details key={entry.id} className="px-4 py-4"><summary className="flex cursor-pointer list-none flex-col gap-2 md:flex-row md:items-center md:justify-between"><span><span className="font-medium">{entry.action}</span><span className="ml-2 text-foreground/60">{entry.entity_type} · {entry.entity_id}</span></span><span className="text-xs tabular-nums text-foreground/50">{new Date(entry.created_at).toLocaleString()}</span></summary><div className="mt-3 grid gap-2 border-l-2 border-border pl-3 text-xs text-foreground/60"><span>Actor: {entry.actor}</span><pre className="overflow-auto whitespace-pre-wrap font-mono">{JSON.stringify(entry.payload, null, 2)}</pre></div></details>)}</div>}
      </div>
    </PageContainer>
  );
}
