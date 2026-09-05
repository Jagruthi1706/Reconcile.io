'use client';

import { useQuery } from '@tanstack/react-query';

import { PageContainer } from '@/components/shell/page-container';
import { PageHeader } from '@/components/shell/page-header';
import { Section } from '@/components/shell/section';
import { getRuns } from '@/lib/api-client';
import { KpiBand, LatestRunInfo } from '@/components/overview/kpi-band';
import { CashSparkline } from '@/components/overview/cash-sparkline';
import { ExceptionsHeatmap } from '@/components/overview/exceptions-heatmap';
import { ActivityFeed } from '@/components/overview/activity-feed';
import { RunReconciliation } from '@/components/overview/run-reconciliation';

export default function OverviewPage() {
  const { data: runs, isLoading: runsLoading, error: runsError } = useQuery({
    queryKey: ['runs'],
    queryFn: () => getRuns(),
  });

  const latestRun = runs?.[0];

  return (
    <PageContainer>
      <PageHeader
        title="Overview"
        question="What is the current financial state?"
        description="Reconciliation position, items requiring attention, cash outlook, and recent system activity."
        actions={<RunReconciliation />}
      />

      <div className="mt-6">
        <LatestRunInfo run={latestRun} loading={runsLoading} error={runsError as Error | null} />
      </div>

      <div className="mt-4">
        <KpiBand latestRun={latestRun} runLoading={runsLoading} runError={runsError as Error | null} />
      </div>

      <div className="mt-6 grid grid-cols-1 gap-6 lg:grid-cols-2">
        <Section>
          <div className="rounded-panel border border-border bg-card p-4">
            <div className="mb-3 flex items-center justify-between">
              <h3 className="text-sm font-medium text-foreground">13-Week Cash Position</h3>
              <span className="label-accent">Projected</span>
            </div>
            <CashSparkline />
          </div>
        </Section>

        <Section>
          <div className="rounded-panel border border-border bg-card p-4">
            <div className="mb-3 flex items-center justify-between">
              <h3 className="text-sm font-medium text-foreground">Exceptions by Source</h3>
              <span className="label-accent">13 weeks</span>
            </div>
            <ExceptionsHeatmap />
          </div>
        </Section>
      </div>

      <div className="mt-6">
        <Section>
          <div className="rounded-panel border border-border bg-card p-4">
            <div className="mb-3 flex items-center justify-between">
              <h3 className="text-sm font-medium text-foreground">Recent Activity</h3>
            </div>
            <ActivityFeed />
          </div>
        </Section>
      </div>
    </PageContainer>
  );
}
