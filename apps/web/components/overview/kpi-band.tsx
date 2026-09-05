'use client';

import Link from 'next/link';
import { useQuery } from '@tanstack/react-query';

import { getRuns, getExceptions, getTaxClassifications, getLatestForecast } from '@/lib/api-client';
import type { ReconciliationRunSummary } from '@/lib/api-types';
import { RecordId } from '@/components/shell/record-id';
import { Percentage } from '@/components/shell/amount';

interface KpiBandProps {
  latestRun: ReconciliationRunSummary | undefined;
  runLoading: boolean;
  runError: Error | null;
}

interface KpiCellProps {
  label: string;
  href?: string;
  children: React.ReactNode;
  loading?: boolean;
  error?: Error | null;
  isEmpty?: boolean;
  emptyMessage?: string;
}

function KpiCell({ label, href, children, loading, error, isEmpty, emptyMessage }: KpiCellProps) {
  const content = (
    <div className="min-w-0 flex-1 px-5 py-4">
      <p className="label-accent mb-2">{label}</p>
      {loading ? (
        <div className="h-7 w-24 animate-pulse rounded-dense bg-muted" />
      ) : error ? (
        <p className="text-sm text-error">Unable to load</p>
      ) : isEmpty ? (
        <p className="text-sm text-foreground/60">{emptyMessage ?? 'No data'}</p>
      ) : (
        children
      )}
    </div>
  );

  if (href && !loading && !error && !isEmpty) {
    return <Link href={href} className="block transition-colors hover:bg-accent/50">{content}</Link>;
  }
  return content;
}

export function KpiBand({ latestRun, runLoading, runError }: KpiBandProps) {
  const { data: exceptionsData, isLoading: excLoading, error: excError } = useQuery({
    queryKey: ['exceptions'],
    queryFn: () => getExceptions(),
  });

  const { data: taxData, isLoading: taxLoading, error: taxError } = useQuery({
    queryKey: ['tax-classifications'],
    queryFn: () => getTaxClassifications(),
  });

  const { data: forecastData, isLoading: fcLoading, error: fcError } = useQuery({
    queryKey: ['forecast-latest'],
    queryFn: () => getLatestForecast(),
  });

  const openExceptions = exceptionsData?.filter((e) => e.status === 'new' || e.status === 'investigating').length ?? 0;
  const taxReviewQueue = taxData?.filter((t) => t.status === 'review').length ?? 0;
  const hasRun = !!latestRun && latestRun.status === 'done';

  return (
    <div className="flex flex-wrap items-stretch divide-x divide-border overflow-hidden rounded-panel border border-border bg-card" role="region" aria-label="Key performance indicators">
      <KpiCell label="Match Rate · Count" href="/reconcile" loading={runLoading} error={runError} isEmpty={!hasRun} emptyMessage="No finished run">
        {latestRun && <Percentage value={latestRun.match_rate_count} className="text-2xl font-medium text-foreground" />}
      </KpiCell>

      <KpiCell label="Match Rate · Value" href="/reconcile" loading={runLoading} error={runError} isEmpty={!hasRun} emptyMessage="No finished run">
        {latestRun && <Percentage value={latestRun.match_rate_dollar} className="text-2xl font-medium text-foreground" />}
      </KpiCell>

      <KpiCell label="Open Exceptions" href="/exceptions" loading={excLoading} error={excError} isEmpty={openExceptions === 0 && !excLoading} emptyMessage="No open exceptions">
        <span className="text-2xl font-medium text-foreground">{openExceptions}</span>
      </KpiCell>

      <KpiCell label="Cash Low-Point" href="/forecast" loading={fcLoading} error={fcError} isEmpty={!forecastData} emptyMessage="No forecast">
        <span className="text-2xl font-medium text-foreground">{forecastData ? `Week ${forecastData.low_point_week}` : ''}</span>
        <span className="ml-1.5 text-sm text-foreground/60">of 13</span>
      </KpiCell>

      <KpiCell label="Tax Review Queue" href="/tax" loading={taxLoading} error={taxError} isEmpty={taxReviewQueue === 0 && !taxLoading} emptyMessage="Queue empty">
        <span className="text-2xl font-medium text-foreground">{taxReviewQueue}</span>
      </KpiCell>
    </div>
  );
}

export function LatestRunInfo({ run, loading, error }: { run: ReconciliationRunSummary | undefined; loading: boolean; error: Error | null }) {
  if (loading) {
    return (
      <div className="flex items-center gap-2">
        <span className="label-accent">Latest Run</span>
        <div className="h-4 w-20 animate-pulse rounded-dense bg-muted" />
      </div>
    );
  }

  if (error || !run) {
    return (
      <div className="flex items-center gap-2">
        <span className="label-accent">Latest Run</span>
        <span className="text-sm text-foreground/60">No finished run</span>
      </div>
    );
  }

  return (
    <div className="flex items-center gap-2">
      <span className="label-accent">Latest Run</span>
      <RecordId id={run.id} />
      <span className="text-xs text-foreground/60">{run.records_processed} records · {run.auto_matched} auto-matched</span>
    </div>
  );
}
