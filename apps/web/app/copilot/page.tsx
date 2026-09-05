import { PageContainer } from '@/components/shell/page-container';
import { PageHeader } from '@/components/shell/page-header';

export default function CopilotPage() {
  return (
    <PageContainer>
      <PageHeader title="Copilot" question="Why did this happen?" description="An explanatory layer over retrieved ledger facts. It never decides matches, classifications, or forecast numbers." />
      <div className="mt-6 rounded-panel border border-border bg-card p-5"><div className="flex items-center justify-between border-b border-border pb-4"><span className="label-accent">Structured-only / Claude-enhanced</span><span className="rounded-control border border-border px-2 py-1 text-xs text-foreground/60">Awaiting API</span></div><div className="flex min-h-56 items-center justify-center text-center"><p className="max-w-md text-sm leading-6 text-foreground/60">Ask questions about retrieved records once the Copilot query contract is connected. Answers and citation chips will appear only when validated context is available.</p></div><div className="flex gap-2 border-t border-border pt-4"><input disabled placeholder="Ask about a reconciled record..." aria-label="Copilot question" className="h-10 flex-1 rounded-control border border-border bg-background px-3 text-sm" /><button disabled type="button" className="rounded-control bg-muted px-4 text-sm text-foreground/50">Ask</button></div></div>
    </PageContainer>
  );
}
