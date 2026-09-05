import { PageContainer } from '@/components/shell/page-container';
import { PageHeader } from '@/components/shell/page-header';

export default function RazorpayPage() {
  return (
    <PageContainer>
      <PageHeader title="Razorpay" question="Live test-mode integration" description="Connectors and webhook activity are restricted to Razorpay test mode. No live credentials or payment actions are available in this frontend pass." />
      <div className="mt-6 grid gap-6 lg:grid-cols-2"><div className="rounded-panel border border-border bg-card p-5"><p className="label-accent">Connection status</p><p className="mt-3 text-lg font-medium">Not connected</p><p className="mt-2 text-sm text-foreground/60">Credential storage and connection verification await the documented backend contract.</p></div><div className="rounded-panel border border-border bg-card p-5"><p className="label-accent">Safety mode</p><p className="mt-3 text-lg font-medium">TEST MODE only</p><p className="mt-2 text-sm text-foreground/60">Orders, payments, settlements, and webhooks will be shown here after the connector is available.</p></div></div>
    </PageContainer>
  );
}
