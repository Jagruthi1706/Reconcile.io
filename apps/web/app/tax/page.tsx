'use client';
import { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { PageContainer } from '@/components/shell/page-container';
import { PageHeader } from '@/components/shell/page-header';
import { getTaxClassifications } from '@/lib/api-client';
import type { TaxClassificationStatus } from '@/lib/api-types';

const statuses: Array<TaxClassificationStatus | 'all'> = ['all', 'auto', 'review', 'confirmed', 'corrected'];

export default function TaxPage() {
  const [status, setStatus] = useState<TaxClassificationStatus | 'all'>('all');
  const query = useQuery({ queryKey: ['tax-classifications', status], queryFn: () => getTaxClassifications(status === 'all' ? undefined : { status }) });
  return (
    <PageContainer>
      <PageHeader title="Tax" question="What requires tax review?" description="Classification confidence and review state, presented directly from the canonical tax record." />
      <div className="mt-6 rounded-panel border border-border bg-card shadow-card">
        <div className="flex flex-wrap gap-1 border-b border-border p-4" aria-label="Filter by classification status">{statuses.map((value) => <button key={value} type="button" aria-pressed={status === value} onClick={() => setStatus(value)} className={`rounded-control px-2.5 py-1.5 text-xs focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ink/30 ${status === value ? 'bg-ink text-parchment' : 'text-foreground/60 hover:bg-muted'}`}>{value === 'all' ? 'All statuses' : value}</button>)}</div>
        {query.isLoading && <div className="p-8 text-sm text-foreground/60">Loading classifications...</div>}
        {query.error && <div className="p-8 text-sm text-error">Classification data is unavailable.</div>}
        {!query.isLoading && !query.error && !query.data?.length && <div className="p-10 text-center text-sm text-foreground/60">No tax classifications are available.</div>}
        {!!query.data?.length && <div className="overflow-x-auto"><table className="w-full min-w-[760px] text-left text-sm"><thead className="border-b border-border text-xs uppercase tracking-[0.12em] text-foreground/50"><tr><th className="px-4 py-3">Classification</th><th className="px-4 py-3">Jurisdiction</th><th className="px-4 py-3">Current label</th><th className="px-4 py-3">Confidence</th><th className="px-4 py-3">Status</th><th className="px-4 py-3">Corrected label</th></tr></thead><tbody className="divide-y divide-border">{query.data.map((item) => <tr key={item.id} className="hover:bg-background"><td className="px-4 py-3"><div className="font-mono text-xs">{item.id}</div><div className="mt-1 text-xs text-foreground/50">GL line {item.gl_line_id}</div></td><td className="px-4 py-3">{item.jurisdiction}</td><td className="px-4 py-3">{item.label}</td><td className="px-4 py-3 font-mono tabular-nums">{(item.confidence * 100).toFixed(1)}%</td><td className="px-4 py-3"><span className="rounded-control border border-border px-2 py-1 text-xs">{item.status}</span></td><td className="px-4 py-3 text-foreground/60">{item.corrected_label ?? 'None recorded'}</td></tr>)}</tbody></table></div>}
      </div>
    </PageContainer>
  );
}
