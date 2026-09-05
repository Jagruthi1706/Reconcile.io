import { PageContainer } from '@/components/shell/page-container';
import { PageHeader } from '@/components/shell/page-header';

export default function ReconcilePage() {
  return (
    <PageContainer>
      <PageHeader title="Reconcile" question="What matched and what didn’t?" description="The workbench will show ledger lines, deterministic match tiers, confidence, and exceptions once the matching read contracts are available." />
      <div className="mt-6 grid gap-4 md:grid-cols-3">{['Ledger lines', 'Match decisions', 'Review queue'].map((label) => <div key={label} className="rounded-panel border border-dashed border-border bg-card p-5"><p className="label-accent">{label}</p><p className="mt-3 text-sm text-foreground/60">Awaiting backend contract</p></div>)}</div>
    </PageContainer>
  );
}
