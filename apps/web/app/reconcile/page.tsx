 'use client';
import { useQuery } from '@tanstack/react-query';
import { PageContainer } from '@/components/shell/page-container';
import { PageHeader } from '@/components/shell/page-header';
import { getRunMatches, getRuns } from '@/lib/api-client';

export default function ReconcilePage() {
  const runs = useQuery({ queryKey: ['runs'], queryFn: getRuns });
  const latest = runs.data?.[0];
  const matches = useQuery({ queryKey: ['matches', latest?.id], queryFn: () => getRunMatches(latest!.id), enabled: !!latest });
  return (
    <PageContainer>
      <PageHeader title="Reconcile" question="What matched and what didn’t?" description="Deterministic match tiers, confidence, and the review queue from the latest reconciliation run." />
      <div className="mt-6 rounded-panel border border-border bg-card p-5">
        {runs.isLoading && <p className="text-sm text-foreground/60">Loading runs...</p>}
        {runs.error && <p className="text-sm text-error">Run data is unavailable.</p>}
        {!runs.isLoading && !runs.error && !latest && <p className="text-sm text-foreground/60">No reconciliation runs have been recorded.</p>}
        {latest && <><div className="flex flex-wrap gap-6 text-sm"><span><span className="label-accent">Status</span><br />{latest.status}</span><span><span className="label-accent">Match rate</span><br />{latest.match_rate_count ?? 0}%</span><span><span className="label-accent">Records</span><br />{latest.records_processed ?? 0}</span><span><span className="label-accent">Exceptions</span><br />{latest.exceptions}</span></div><div className="mt-6 overflow-x-auto">{matches.isLoading && <p className="text-sm text-foreground/60">Loading matches...</p>}{matches.error && <p className="text-sm text-error">Match data is unavailable.</p>}{matches.data?.length ? <table className="w-full min-w-[700px] text-left text-sm"><thead className="border-b border-border text-xs uppercase text-foreground/50"><tr><th className="px-3 py-2">Match</th><th className="px-3 py-2">Tier</th><th className="px-3 py-2">Confidence</th><th className="px-3 py-2">Variance</th><th className="px-3 py-2">Status</th></tr></thead><tbody className="divide-y divide-border">{matches.data.map((match) => <tr key={match.id}><td className="px-3 py-2 font-mono text-xs">{match.line_a_id} / {match.line_b_id}</td><td className="px-3 py-2">{match.tier}</td><td className="px-3 py-2">{(match.confidence * 100).toFixed(1)}%</td><td className="px-3 py-2">{match.variance}</td><td className="px-3 py-2">{match.status}</td></tr>)}</tbody></table> : !matches.isLoading && <p className="text-sm text-foreground/60">No matches in this run.</p>}</div></>}
      </div>
    </PageContainer>
  );
}
