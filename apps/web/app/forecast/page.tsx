 'use client';
import { useQuery } from '@tanstack/react-query';
import { PageContainer } from '@/components/shell/page-container';
import { PageHeader } from '@/components/shell/page-header';
import { getLatestForecast } from '@/lib/api-client';

function Summary({ label, value }: { label: string; value: string }) { return <div className="rounded-panel border border-border bg-card p-4"><p className="label-accent">{label}</p><p className="mt-2 font-mono text-2xl tabular-nums">{value}</p></div>; }

export default function ForecastPage() {
  const query = useQuery({ queryKey: ['forecast-latest'], queryFn: getLatestForecast });
  return (
    <PageContainer>
            <PageHeader title="Forecast" question="What does this mean for future cash?" description="The latest 13-week snapshot, clearly framed as a projection and calibrated from reconciliation history." />
            <div className="mt-6 flex items-center justify-between border-b border-border pb-3 text-xs text-foreground/60">
              <span>Projected forecast</span>
              {query.data && <span>Generated {new Date(query.data.generated_at).toLocaleString()}</span>}
            </div>
            {query.isLoading && <div className="mt-6 rounded-panel border border-border bg-card p-10 text-sm text-foreground/60">Loading forecast snapshot...</div>}
            {query.error && <div className="mt-6 rounded-panel border border-border bg-card p-10 text-sm text-error">Forecast data is unavailable.</div>}
            {!query.isLoading && !query.error && !query.data && <div className="mt-6 rounded-panel border border-dashed border-border p-10 text-center text-sm text-foreground/60">No forecast snapshot is available.</div>}
            {query.data && <>
              <div className="mt-6 grid gap-4 sm:grid-cols-3">
                <Summary label="Opening cash" value={String(query.data.opening_cash)} />
                <Summary label="Low point week" value={`Week ${query.data.low_point_week}`} />
                <Summary label="Average settlement lag" value={String(query.data.avg_settlement_lag)} />
              </div>
              <div className="mt-6 rounded-panel border border-dashed border-border bg-card p-10 text-center">
                <p className="text-sm font-medium text-foreground">13-week series awaiting finalized contract</p>
                <p className="mx-auto mt-2 max-w-lg text-sm leading-6 text-foreground/60">The snapshot is available, but its <code>weeks</code> JSON shape is not finalized. No chart is rendered until its fields are documented.</p>
              </div>
            </>}
    </PageContainer>
  );
}
