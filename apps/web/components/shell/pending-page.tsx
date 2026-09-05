import { PageHeader } from '@/components/shell/page-header';
import { PageContainer } from '@/components/shell/page-container';

export function PendingPage({ title, question }: { title: string; question: string }) {
  return (
    <PageContainer>
      <PageHeader title={title} question={question} description="This product area is intentionally left as an explicit placeholder during the Phase 0 foundation alignment." />
      <div className="mt-6 rounded-panel border border-dashed border-border bg-card p-6 text-sm text-foreground/70">
        Placeholder implementation — the backend and product flows are intentionally deferred to approved later phases.
      </div>
    </PageContainer>
  );
}
