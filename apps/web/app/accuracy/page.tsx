 'use client';
import { useQuery } from '@tanstack/react-query';
import { PageContainer } from '@/components/shell/page-container';
import { PageHeader } from '@/components/shell/page-header';
import { getAccuracyHistory } from '@/lib/api-client';

export default function AccuracyPage() {
  const query = useQuery({ queryKey: ['accuracy-history'], queryFn: getAccuracyHistory });
  const latest = query.data?.[0];
  return (
    <PageContainer>
      <PageHeader title="Accuracy" question="Can I trust the engine?" description="Verified precision, recall, F1, and confusion metrics from the deterministic golden-set benchmark." />
      {query.isLoading && <div className="mt-6 text-sm text-foreground/60">Loading benchmark history...</div>}{query.error && <div className="mt-6 text-sm text-error">Benchmark data is unavailable.</div>}{!query.isLoading && !query.error && !latest && <div className="mt-6 text-sm text-foreground/60">No benchmark has been recorded.</div>}{latest && <div className="mt-6 grid gap-4 sm:grid-cols-4">{[['Precision', latest.precision], ['Recall', latest.recall], ['F1', latest.f1], ['Confusion', `TP ${latest.tp} · FP ${latest.fp} · FN ${latest.fn} · TN ${latest.tn}`]].map(([label, value]) => <div key={String(label)} className="rounded-panel border border-border bg-card p-5"><p className="label-accent">{label}</p><p className="mt-3 text-2xl font-mono">{typeof value === 'number' ? `${(value * 100).toFixed(1)}%` : value}</p></div>)}</div>}
    </PageContainer>
  );
}
