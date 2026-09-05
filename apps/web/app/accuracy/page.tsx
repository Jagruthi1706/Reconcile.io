import { PageContainer } from '@/components/shell/page-container';
import { PageHeader } from '@/components/shell/page-header';

export default function AccuracyPage() {
  return (
    <PageContainer>
      <PageHeader title="Accuracy" question="Can I trust the engine?" description="Benchmark history will appear here once the deterministic engine has produced verified results against the golden set." />
      <div className="mt-6 grid gap-4 sm:grid-cols-4">{['Precision', 'Recall', 'F1', 'Confusion matrix'].map((label) => <div key={label} className="rounded-panel border border-dashed border-border bg-card p-5"><p className="label-accent">{label}</p><p className="mt-3 text-sm text-foreground/60">No benchmark data available</p></div>)}</div>
    </PageContainer>
  );
}
