import { PageContainer } from '@/components/shell/page-container';
import { PageHeader } from '@/components/shell/page-header';

export default function SettingsPage() {
  return (
    <PageContainer>
      <PageHeader title="Settings" question="How is the system configured?" description="Read-only configuration framing for matching, tax, access, and the test-mode integration." />
      <div className="mt-6 grid gap-4 md:grid-cols-2">{[['Workspace access', 'User and role information will appear when authentication is connected.'], ['Matching rules', 'Tolerance thresholds are managed by the documented settings API.'], ['Tax rules', 'Jurisdiction rule tables are managed by the documented settings API.'], ['Razorpay', 'The integration is restricted to test mode.']].map(([title, text]) => <div key={title} className="rounded-panel border border-border bg-card p-5"><p className="label-accent">{title}</p><p className="mt-3 text-sm leading-6 text-foreground/60">{text}</p><span className="mt-5 inline-flex rounded-control border border-dashed border-border px-2 py-1 text-xs text-foreground/50">Read-only / awaiting API</span></div>)}</div>
    </PageContainer>
  );
}
