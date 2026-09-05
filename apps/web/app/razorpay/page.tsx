 'use client';
import { useQuery } from '@tanstack/react-query';
import { PageContainer } from '@/components/shell/page-container';
import { PageHeader } from '@/components/shell/page-header';
import { getRazorpayActivity } from '@/lib/api-client';

export default function RazorpayPage() {
  const query = useQuery({ queryKey: ['razorpay-activity'], queryFn: getRazorpayActivity });
  return (
    <PageContainer>
      <PageHeader title="Razorpay" question="Live test-mode integration" description="Connectors and webhook activity are restricted to Razorpay test mode. No live credentials or payment actions are available in this frontend pass." />
      <div className="mt-6 grid gap-6 lg:grid-cols-2"><div className="rounded-panel border border-border bg-card p-5"><p className="label-accent">Connection activity</p><p className="mt-3 text-lg font-medium">{query.data?.length ? 'Connected activity recorded' : 'No activity recorded'}</p><p className="mt-2 text-sm text-foreground/60">{query.error ? 'Activity is unavailable.' : `${query.data?.length ?? 0} test-mode operations recorded.`}</p></div><div className="rounded-panel border border-border bg-card p-5"><p className="label-accent">Safety mode</p><p className="mt-3 text-lg font-medium">TEST MODE only</p><p className="mt-2 text-sm text-foreground/60">Production code rejects non-test Razorpay mode.</p></div></div><div className="mt-6 rounded-panel border border-border bg-card p-5"><p className="label-accent">Recent operations</p>{query.data?.length ? <div className="mt-4 divide-y divide-border">{query.data.slice(0, 10).map((item) => <div key={item.id} className="flex justify-between py-3 text-sm"><span>{item.operation}</span><span className="text-foreground/60">{item.status}</span></div>)}</div> : <p className="mt-3 text-sm text-foreground/60">No Razorpay activity is available yet.</p>}</div>
    </PageContainer>
  );
}
