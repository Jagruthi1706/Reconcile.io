 'use client';
import { useQuery } from '@tanstack/react-query';
import { PageContainer } from '@/components/shell/page-container';
import { PageHeader } from '@/components/shell/page-header';
import { getMatchingRules, getTaxRules } from '@/lib/api-client';

export default function SettingsPage() {
  const matching = useQuery({ queryKey: ['settings-matching'], queryFn: getMatchingRules });
  const tax = useQuery({ queryKey: ['settings-tax'], queryFn: getTaxRules });
  return (
    <PageContainer>
      <PageHeader title="Settings" question="How is the system configured?" description="Read-only configuration framing for matching, tax, access, and the test-mode integration." />
      <div className="mt-6 grid gap-4 md:grid-cols-2"><div className="rounded-panel border border-border bg-card p-5"><p className="label-accent">Workspace access</p><p className="mt-3 text-sm leading-6 text-foreground/60">Authenticated evaluator access is read-only.</p></div><div className="rounded-panel border border-border bg-card p-5"><p className="label-accent">Matching rules</p>{matching.data ? <p className="mt-3 text-sm leading-6 text-foreground/60">Auto-accept {matching.data.match_auto_accept_confidence} · Amount tolerance {matching.data.match_amount_tolerance_pct}% · Date window {matching.data.match_date_window_days} days</p> : <p className="mt-3 text-sm text-error">Matching settings unavailable.</p>}</div><div className="rounded-panel border border-border bg-card p-5"><p className="label-accent">Tax rules</p><p className="mt-3 text-sm leading-6 text-foreground/60">{tax.data?.rules.length ?? 0} configured jurisdiction rules.</p></div><div className="rounded-panel border border-border bg-card p-5"><p className="label-accent">Razorpay</p><p className="mt-3 text-sm leading-6 text-foreground/60">TEST MODE only.</p></div></div>
    </PageContainer>
  );
}
